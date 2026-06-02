"""Manifest writer + template walker + orchestration for ``bookwright init``.

The atomic-or-nothing rollback ledger and the tracked fs primitives now live in
the shared :mod:`bookwright.io.fs` module (extracted in iteration 9 so the skills
materializer can record through the same ledger). They are re-exported here for
backward compatibility with the ``init`` package's importers. The template walker
drives Jinja2 over packaged resources (research §R9).
"""

from __future__ import annotations

import sys
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import jinja2

from bookwright import integrations as _integrations
from bookwright.core.manifest import Manifest
from bookwright.io.fs import (
    BackupCreationError,
    BackupEntry,
    BackupLedger,
    TargetOutsideProjectRootError,
    _register_target,
    mkdir_tracked,
    write_bytes_atomic,
)

from . import envelope, git

if TYPE_CHECKING:
    from .envelope import ResolvedInvocation

# Re-exported from io.fs for the init package's importers (envelope, git,
# conflict) and the resource-render tests. Listed in __all__ so linters do not
# flag the re-exports as unused.
__all__ = [
    "COMMIT_MESSAGE",
    "GIT_EXISTING_WARNING",
    "GIT_MISSING_WARNING",
    "BackupCreationError",
    "BackupEntry",
    "BackupLedger",
    "TargetOutsideProjectRootError",
    "copy_resource_file",
    "dump_manifest_tracked",
    "mkdir_tracked",
    "render_resource_tree",
    "run_scaffold_steps",
    "write_bytes_atomic",
]

COMMIT_MESSAGE = "Initial commit from bookwright init"

GIT_MISSING_WARNING = (
    "bookwright: warning: git not found on PATH; project created without a repository"
)
GIT_EXISTING_WARNING = "bookwright: warning: existing .git/ detected; skipped git init and commit"


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
    integration: _integrations.SkillsIntegration,
    parsed_options: dict[str, str | bool],
    ledger: BackupLedger,
    warnings: list[str],
    author_name: str,
) -> None:
    """All filesystem mutations + integration setup + git step.

    The orchestrator behind ``bookwright init``'s success path: renders
    the packaged template tree, dumps the manifest, copies vocabularies,
    runs the integration's ``setup()`` and finally ``git init + commit``
    when applicable. The ``git_status`` on ``resolved`` is settled by
    ``main.run`` before this function is called.
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

    # 4) Wire the integration's setup() through the ledger. The materializer
    # records every directory and file it creates via this live BackupLedger, so
    # a failed init unwinds all materialized skills — including over a pre-existing
    # skills_dir (FR-019/SC-008). setup() resolves + mkdir_tracked's the target.
    integration.setup(project_root, manifest, parsed_options, ledger=ledger)

    # 5) Write the init-options record (git_status already settled by main.run).
    record = envelope.build_options_record(resolved)
    options_payload = envelope.serialize_options_record(record)
    write_bytes_atomic(
        project_root / ".bookwright" / "init-options.json",
        options_payload,
        ledger,
    )

    # 6) Run git init + commit if applicable. Warnings go to stderr regardless
    # of ``--json`` (contract §5); the JSON envelope mirrors them via the
    # ``warnings`` list on the success path.
    if resolved.git_status == "initialized":
        git.init_and_commit(project_root, COMMIT_MESSAGE, author_name, ledger)
    elif resolved.git_status == "skipped_existing_repo":
        warnings.append(GIT_EXISTING_WARNING)
        sys.stderr.write(GIT_EXISTING_WARNING + "\n")
    elif resolved.git_status == "skipped_no_binary":
        warnings.append(GIT_MISSING_WARNING)
        sys.stderr.write(GIT_MISSING_WARNING + "\n")
