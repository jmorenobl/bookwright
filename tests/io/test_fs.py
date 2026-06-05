"""Unit coverage for the shared transactional-fs layer (``bookwright.io.fs``).

Relocated from ``tests/commands/test_init_helpers.py`` when the ledger + tracked
writers were extracted out of ``init/scaffold.py`` (iteration 9). Adds a
``NullLedger`` no-op contract test (FR-019, standalone callers).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.io.fs import (
    BackupCreationError,
    BackupLedger,
    NullLedger,
    TargetOutsideProjectRootError,
    mkdir_tracked,
    write_bytes_atomic,
)


def test_ledger_refuses_writes_outside_root(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    with pytest.raises(TargetOutsideProjectRootError):
        ledger.record_new_file(tmp_path.parent / "outside.txt")


def test_ledger_rollback_unlinks_new_file(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    target = tmp_path / "newfile.txt"
    write_bytes_atomic(target, b"hi", ledger)
    assert target.read_text() == "hi"

    ledger.rollback()
    assert not target.exists()


def test_ledger_rollback_restores_overwritten_file(tmp_path: Path) -> None:
    target = tmp_path / "pre.txt"
    target.write_text("ORIGINAL", encoding="utf-8")

    ledger = BackupLedger(tmp_path)
    write_bytes_atomic(target, b"NEW", ledger)
    assert target.read_text() == "NEW"

    ledger.rollback()
    assert target.read_text() == "ORIGINAL"


def test_ledger_rollback_restores_directory(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    new_dir = tmp_path / "dir" / "sub"
    mkdir_tracked(new_dir, ledger)
    assert new_dir.exists()

    ledger.rollback()
    assert not new_dir.exists()
    assert not (tmp_path / "dir").exists()


def test_ledger_record_overwrite_on_failure_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "exists.txt"
    target.write_text("hi", encoding="utf-8")

    def boom(*_a, **_kw):  # type: ignore[no-untyped-def]
        raise PermissionError("forbidden")

    monkeypatch.setattr("bookwright.io.fs.shutil.copy2", boom)
    ledger = BackupLedger(tmp_path)
    with pytest.raises(BackupCreationError):
        ledger.record_overwrite(target)


def test_ledger_commit_prunes_cache(tmp_path: Path) -> None:
    target = tmp_path / "pre.txt"
    target.write_text("ORIGINAL", encoding="utf-8")

    ledger = BackupLedger(tmp_path)
    write_bytes_atomic(target, b"NEW", ledger)
    ledger.commit()

    cache = tmp_path / ".bookwright" / "cache"
    assert not cache.exists() or not any(cache.rglob("*"))


def test_mkdir_tracked_noop_when_exists(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    existing = tmp_path / "already-here"
    existing.mkdir()
    mkdir_tracked(existing, ledger)
    assert ledger.entries == ()


# ---------- NullLedger no-op contract (FR-019, standalone callers) ----------


def test_null_ledger_records_nothing_but_writes_happen(tmp_path: Path) -> None:
    """NullLedger no-ops every record call; the actual fs mutations still occur."""

    ledger = NullLedger()
    target = tmp_path / "a" / "b" / "file.txt"
    mkdir_tracked(target.parent, ledger)
    write_bytes_atomic(target, b"payload", ledger)

    assert target.read_text(encoding="utf-8") == "payload"
    # record_overwrite is a no-op that simply echoes the target back; the other
    # two record calls are no-ops that mutate nothing (exercised for coverage).
    assert ledger.record_overwrite(target) == target
    ledger.record_new_file(target)
    ledger.record_new_directory(target.parent)
