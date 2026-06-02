"""Shared transactional-filesystem layer (extracted from ``init/scaffold.py``).

The :class:`BackupLedger` is the atomic-or-nothing primitive: every filesystem
mutation a caller performs is recorded here BEFORE the bytes hit disk; on success
the backups are unlinked, on any exception the ledger is replayed in reverse to
restore the tree to byte-for-byte its pre-mutation state. The writer goes through
``os.replace`` for local atomicity.

Two consumers depend on this module: ``bookwright.commands.init`` (the original
home) and ``bookwright.integrations`` (the iteration-9 skills materializer). To
keep them decoupled from the concrete ledger, this module also defines the narrow
:class:`FileLedger` ``Protocol`` (structurally satisfied by :class:`BackupLedger`)
and a no-op :class:`NullLedger` for standalone callers.

Dependency direction is acyclic by design: this module imports **only** stdlib —
it imports neither ``commands`` nor ``integrations``.
"""

from __future__ import annotations

import contextlib
import os
import secrets
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

_BACKUP_SUBDIR = Path(".bookwright/cache/backup")


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


@runtime_checkable
class FileLedger(Protocol):
    """Narrow rollback-recording surface the materializer depends on.

    Structurally satisfied by :class:`BackupLedger` (and any future ledger).
    The integrations layer depends on this Protocol, never on the concrete
    ledger, so it stays decoupled from ``init`` internals (Principle V).
    """

    def record_new_file(self, target: Path) -> None: ...

    def record_new_directory(self, target: Path) -> None: ...

    def record_overwrite(self, target: Path) -> Path: ...


class NullLedger:
    """No-op :class:`FileLedger` for standalone callers (no rollback needed)."""

    def record_new_file(self, target: Path) -> None:
        del target

    def record_new_directory(self, target: Path) -> None:
        del target

    def record_overwrite(self, target: Path) -> Path:
        return target


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


def _register_target(target: Path, ledger: FileLedger) -> None:
    """Record ``target`` with the ledger: new file or overwrite."""

    if target.exists():
        ledger.record_overwrite(target)
    else:
        ledger.record_new_file(target)


def write_bytes_atomic(target: Path, payload: bytes, ledger: FileLedger) -> None:
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


def mkdir_tracked(target: Path, ledger: FileLedger) -> None:
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
