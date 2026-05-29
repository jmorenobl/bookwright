"""Backup ledger + atomic writer + template walker for ``bookwright init``.

The ledger is the FR-030 / SC-005 atomic-or-nothing primitive: every
filesystem mutation `init` performs is recorded here BEFORE the bytes hit
disk; on success the backups are unlinked, on any exception the ledger is
replayed in reverse to restore the project root to byte-for-byte its
pre-invocation state. The writer goes through ``os.replace`` for local
atomicity (research §R6); the walker drives Jinja2 over packaged
resources (research §R9).
"""

from __future__ import annotations

import contextlib
import os
import secrets
import shutil
import sys
import tempfile
from dataclasses import dataclass
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import jinja2

from bookwright import integrations as _integrations
from bookwright.commands import _init_envelope, _init_git
from bookwright.core.manifest import Manifest

if TYPE_CHECKING:
    from bookwright.commands._init_envelope import ResolvedInvocation

_BACKUP_SUBDIR = Path(".bookwright/cache/backup")

COMMIT_MESSAGE = "Initial commit from bookwright init"

GIT_MISSING_WARNING = (
    "bookwright: warning: git not found on PATH; project created without a repository"
)
GIT_EXISTING_WARNING = "bookwright: warning: existing .git/ detected; skipped git init and commit"


class BackupCreationError(Exception):
    """Raised when a pre-overwrite backup copy could not be created (FR-030 last sentence)."""

    code = "backup_creation_error"

    def __init__(self, *, target: Path, reason: str) -> None:
        self.target = target
        self.reason = reason
        super().__init__(f"could not create backup for {target}: {reason}")


class TargetOutsideProjectRootError(Exception):
    """Raised when a writer would touch a path outside ``project_root`` (FR-014)."""

    def __init__(self, *, target: Path, project_root: Path) -> None:
        self.target = target
        self.project_root = project_root
        super().__init__(f"target {target} is outside project root {project_root}")


@dataclass(frozen=True)
class BackupEntry:
    """One ledger entry (data-model §3)."""

    target: Path
    backup_path: Path | None
    was_directory: bool


class BackupLedger:
    """In-memory rollback record for one ``init`` invocation."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root.resolve()
        self._entries: list[BackupEntry] = []

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def entries(self) -> tuple[BackupEntry, ...]:
        return tuple(self._entries)

    def _ensure_under_root(self, target: Path) -> Path:
        resolved = target.resolve() if target.exists() else (target.parent.resolve() / target.name)
        if not resolved.is_relative_to(self._project_root):
            raise TargetOutsideProjectRootError(target=resolved, project_root=self._project_root)
        return resolved

    def record_new_file(self, target: Path) -> None:
        resolved = self._ensure_under_root(target)
        self._entries.append(BackupEntry(target=resolved, backup_path=None, was_directory=False))

    def record_new_directory(self, target: Path) -> None:
        resolved = self._ensure_under_root(target)
        self._entries.append(BackupEntry(target=resolved, backup_path=None, was_directory=True))

    def record_overwrite(self, target: Path) -> Path:
        """Copy ``target`` into the cache before allowing the overwrite.

        Raises ``BackupCreationError`` on copy failure — caller must abort
        before any byte hits the target (FR-030 last sentence).
        """

        resolved = self._ensure_under_root(target)
        token = secrets.token_hex(6)
        relative = resolved.relative_to(self._project_root)
        backup_path = self._project_root / _BACKUP_SUBDIR / token / relative
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resolved, backup_path)
        except OSError as exc:
            raise BackupCreationError(target=resolved, reason=str(exc)) from exc
        self._entries.append(
            BackupEntry(target=resolved, backup_path=backup_path, was_directory=False)
        )
        return backup_path

    def commit(self) -> None:
        """Success path — delete every backup file and prune empty parents."""

        for entry in self._entries:
            if entry.backup_path is not None:
                with contextlib.suppress(OSError):
                    entry.backup_path.unlink()
        # Prune the per-invocation backup root if it ended up empty.
        backup_root = self._project_root / _BACKUP_SUBDIR
        if backup_root.exists():
            with contextlib.suppress(OSError):
                shutil.rmtree(backup_root)

    def rollback(self) -> None:
        """Failure path — walk in reverse, restore overwrites, unlink new entries."""

        for entry in reversed(self._entries):
            if entry.backup_path is not None:
                with contextlib.suppress(OSError):
                    shutil.move(str(entry.backup_path), str(entry.target))
                continue
            if entry.was_directory:
                if entry.target.exists():
                    with contextlib.suppress(OSError):
                        shutil.rmtree(entry.target)
                continue
            if entry.target.exists():
                with contextlib.suppress(OSError):
                    entry.target.unlink()
        # Always try to clear the backup cache directory itself.
        backup_root = self._project_root / _BACKUP_SUBDIR
        if backup_root.exists():
            with contextlib.suppress(OSError):
                shutil.rmtree(backup_root)


def _register_target(target: Path, ledger: BackupLedger) -> None:
    """Record ``target`` with the ledger: new file or overwrite."""

    if target.exists():
        ledger.record_overwrite(target)
    else:
        ledger.record_new_file(target)


def write_bytes_atomic(target: Path, payload: bytes, ledger: BackupLedger) -> None:
    """Atomic file write via ``tempfile.mkstemp`` + ``os.fsync`` + ``os.replace``.

    Registers the target with the ledger BEFORE any byte hits disk
    (so a copy failure during overwrite-backup aborts cleanly).
    """

    _register_target(target, ledger)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(target.parent),
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(tmp_fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


def mkdir_tracked(target: Path, ledger: BackupLedger) -> None:
    """``mkdir(parents=True, exist_ok=True)`` while recording the new directory."""

    if target.exists():
        return
    # Walk up to find the first non-existent parent — every newly created
    # directory must be registered so rollback can prune them in reverse.
    to_create: list[Path] = []
    cursor = target
    while not cursor.exists():
        to_create.append(cursor)
        cursor = cursor.parent
    for path in reversed(to_create):
        ledger.record_new_directory(path)
        path.mkdir(exist_ok=True)


def dump_manifest_tracked(manifest: Manifest, target: Path, ledger: BackupLedger) -> None:
    """Register ``target`` with the ledger, then delegate to ``Manifest.dump``.

    Keeps ``Manifest.dump`` as the sole TOML writer (FR-015) while still
    participating the write in the backup ledger (FR-030).
    """

    _register_target(target, ledger)
    manifest.dump(target, overwrite=target.exists())


_J2_SUFFIX = ".j2"
_RESOURCE_PACKAGE = "bookwright.resources.project"


def _iter_resource_files(root: Traversable) -> list[tuple[str, Traversable]]:
    """Walk a ``Traversable`` resource tree, yielding ``(rel_posix, node)``.

    ``rel_posix`` uses ``/`` separators and is relative to ``root``. The
    ``__init__.py`` marker file is filtered out — it is implementation
    detail of the package layout, not part of the project template.
    """

    results: list[tuple[str, Traversable]] = []

    def _walk(node: Traversable, prefix: str) -> None:
        for child in node.iterdir():
            name = child.name
            if name == "__pycache__":
                continue
            if prefix == "" and name == "__init__.py":
                continue
            rel = f"{prefix}{name}" if prefix == "" else f"{prefix}/{name}"
            if child.is_dir():
                _walk(child, rel)
            else:
                results.append((rel, child))

    _walk(root, "")
    return results


def _target_relpath(rel: str) -> Path:
    """Drop the ``.j2`` suffix when present; preserve directory layout."""

    return Path(rel[: -len(_J2_SUFFIX)]) if rel.endswith(_J2_SUFFIX) else Path(rel)


def render_resource_tree(
    target_root: Path,
    context: dict[str, Any],
    ledger: BackupLedger,
) -> None:
    """Walk ``bookwright.resources.project`` and render it into ``target_root``.

    ``.j2`` files go through one shared Jinja2 environment with strict
    undefined; everything else is byte-copied. Empty directories are
    preserved via ``.gitkeep`` resources.
    """

    env = jinja2.Environment(
        loader=jinja2.PackageLoader(_RESOURCE_PACKAGE, ""),
        autoescape=False,
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )

    package_root = files(_RESOURCE_PACKAGE)
    entries = _iter_resource_files(package_root)

    for rel, node in sorted(entries, key=lambda item: item[0]):
        target = target_root / _target_relpath(rel)
        mkdir_tracked(target.parent, ledger)

        if rel.endswith(_J2_SUFFIX):
            template = env.get_template(rel)
            rendered = template.render(**context)
            write_bytes_atomic(target, rendered.encode("utf-8"), ledger)
            continue

        with as_file(node) as src:
            payload = Path(src).read_bytes()
        write_bytes_atomic(target, payload, ledger)


def copy_resource_file(
    package: str,
    name: str,
    target: Path,
    ledger: BackupLedger,
) -> None:
    """Copy a single packaged resource file to ``target`` through the ledger."""

    node = files(package).joinpath(name)
    with as_file(node) as src:
        payload = Path(src).read_bytes()
    write_bytes_atomic(target, payload, ledger)


def run_scaffold_steps(  # noqa: PLR0913 — orchestrator: gathers every previously-resolved input in one call
    *,
    resolved: ResolvedInvocation,
    integration_cls: type[_integrations.SkillsIntegration],
    parsed_options: dict[str, str | bool],
    ledger: BackupLedger,
    json_output: bool,
    warnings: list[str],
    no_git: bool,
    author_name: str,
    use_git: bool,
) -> ResolvedInvocation:
    """All filesystem mutations + integration setup + git step.

    The orchestrator behind ``bookwright init``'s success path: renders
    the packaged template tree, dumps the manifest, copies vocabularies,
    runs the integration's ``setup()`` and finally ``git init + commit``
    when applicable. Returns ``resolved`` with ``git_status`` filled in.
    """

    project_root = Path(resolved.project_root)

    template_context = {
        "title": resolved.title,
        "project_slug": resolved.project_slug,
        "author": resolved.authors[0],
        "language": resolved.language,
        "integration_key": resolved.integration_key,
    }

    # 1) Render the packaged template tree.
    render_resource_tree(project_root, template_context, ledger)

    # 2) Build and dump the manifest.
    manifest = Manifest.build(
        title=resolved.title,
        authors=list(resolved.authors),
        integration_key=resolved.integration_key,
        integration_skills_dir=resolved.integration_skills_dir,
        integration_options=dict(parsed_options),
        language=resolved.language,
        type="novel",
        status="idea",
        uri_base=f"https://example.org/{resolved.project_slug}/",
    )
    dump_manifest_tracked(manifest, project_root / "manifest.toml", ledger)

    # 3) Copy bundled vocabularies into .bookwright/vocabularies/.
    vocab_target = project_root / ".bookwright" / "vocabularies"
    mkdir_tracked(vocab_target, ledger)
    for vocab in ("propp.ttl", "greimas.ttl"):
        copy_resource_file(
            "bookwright.resources.vocabularies",
            vocab,
            vocab_target / vocab,
            ledger,
        )

    # 4) Wire the integration's setup() through the ledger.
    skills_target = project_root / integration_cls().resolve_skills_dir(parsed_options)
    mkdir_tracked(skills_target, ledger)
    marker = skills_target / _integrations.SKILL_PLACEHOLDER_MARKER_NAME
    if not marker.exists():
        ledger.record_new_file(marker)
    integration_cls().setup(project_root, manifest, parsed_options)

    # 5) Write the init-options record. The git_status is filled in below.
    if no_git:
        resolved = resolved.model_copy(update={"git_status": "skipped_by_flag"})
    elif not use_git:
        resolved = resolved.model_copy(update={"git_status": "skipped_no_binary"})
    elif _init_git.is_inside_existing_repo(project_root):
        resolved = resolved.model_copy(update={"git_status": "skipped_existing_repo"})
    else:
        resolved = resolved.model_copy(update={"git_status": "initialized"})

    record = _init_envelope.build_options_record(resolved)
    options_payload = _init_envelope.serialize_options_record(record)
    write_bytes_atomic(
        project_root / ".bookwright" / "init-options.json",
        options_payload,
        ledger,
    )

    # 6) Run git init + commit if applicable.
    if resolved.git_status == "initialized":
        _init_git.init_and_commit(project_root, COMMIT_MESSAGE, author_name, ledger)
    elif resolved.git_status == "skipped_existing_repo":
        warnings.append(GIT_EXISTING_WARNING)
        if not json_output:
            sys.stderr.write(GIT_EXISTING_WARNING + "\n")
    elif resolved.git_status == "skipped_no_binary":
        warnings.append(GIT_MISSING_WARNING)
        if not json_output:
            sys.stderr.write(GIT_MISSING_WARNING + "\n")

    return resolved
