"""Unit-level coverage for the `_init_*` helpers.

Drives the validators, the locale/git resolve helpers, the envelope
encoders, and the scaffold primitives directly to cover the branches the
end-to-end CLI tests don't reach.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookwright.commands import (
    _init_envelope,
    _init_git,
    _init_resolve,
    _init_scaffold,
    _init_validate,
)
from bookwright.commands._init_envelope import (
    InitOptionsRecord,
    ResolvedInvocation,
    build_options_record,
    error_envelope,
    success_envelope,
)
from bookwright.commands._init_scaffold import (
    BackupCreationError,
    BackupLedger,
    TargetOutsideProjectRootError,
)

# ---------- _init_validate ----------


def test_check_slug_not_reserved_empty() -> None:
    with pytest.raises(_init_validate.InvalidProjectNameError) as exc:
        _init_validate.check_slug_not_reserved("")
    assert exc.value.rule == "empty"


def test_check_slug_not_reserved_reserved() -> None:
    with pytest.raises(_init_validate.InvalidProjectNameError) as exc:
        _init_validate.check_slug_not_reserved("con")
    assert exc.value.rule == "reserved_name"


# ---------- _init_resolve ----------


def test_resolve_authors_falls_back_to_user_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_init_resolve, "_git_config_user_name", lambda _cwd: None)
    monkeypatch.setenv("USER", "alice")
    authors, fellback = _init_resolve.resolve_authors(tmp_path)
    assert authors == ["alice"]
    assert fellback is False


def test_resolve_authors_falls_back_to_sentinel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_init_resolve, "_git_config_user_name", lambda _cwd: None)
    monkeypatch.delenv("USER", raising=False)
    authors, fellback = _init_resolve.resolve_authors(tmp_path)
    assert authors == [_init_resolve.AUTHOR_SENTINEL]
    assert fellback is True


def test_git_config_handles_missing_binary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise FileNotFoundError

    monkeypatch.setattr("bookwright.commands._init_resolve.subprocess.run", boom)
    assert _init_resolve._git_config_user_name(tmp_path) is None


def test_git_config_handles_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCompleted:
        returncode = 1
        stdout = ""

    monkeypatch.setattr(
        "bookwright.commands._init_resolve.subprocess.run",
        lambda *a, **kw: FakeCompleted(),
    )
    assert _init_resolve._git_config_user_name(tmp_path) is None


@pytest.mark.parametrize(
    "locale_value,expected",
    [
        ((None, None), "es"),
        (("", ""), "es"),
        (("es_ES", "UTF-8"), "es"),
        (("EN_US", "UTF-8"), "en"),
        (("xx_YY", "UTF-8"), "es"),  # unknown prefix → fallback
    ],
)
def test_resolve_language_locale_paths(
    monkeypatch: pytest.MonkeyPatch,
    locale_value: tuple[str | None, str | None],
    expected: str,
) -> None:
    monkeypatch.setattr(
        "bookwright.commands._init_resolve.locale.getlocale",
        lambda *a, **k: locale_value,
    )
    assert _init_resolve.resolve_language() == expected


def test_resolve_language_handles_typeerror(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a, **_kw):  # type: ignore[no-untyped-def]
        raise TypeError

    monkeypatch.setattr("bookwright.commands._init_resolve.locale.getlocale", boom)
    assert _init_resolve.resolve_language() == "es"


def test_derive_slug_empty_after_slugify() -> None:
    with pytest.raises(_init_validate.InvalidProjectNameError) as exc:
        _init_resolve.derive_slug("***")
    assert exc.value.rule == "empty"


def test_is_interactive_default(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys as _sys  # noqa: PLC0415

    monkeypatch.setattr(_sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(_sys.stdout, "isatty", lambda: True)
    assert _init_resolve.is_interactive() is True
    monkeypatch.setattr(_sys.stdin, "isatty", lambda: False)
    assert _init_resolve.is_interactive() is False


# ---------- _init_envelope ----------


def _make_resolved(**overrides: object) -> ResolvedInvocation:
    base: dict[str, object] = {
        "mode": "named",
        "project_name": "mi-libro",
        "project_slug": "mi-libro",
        "project_root": "/abs/mi-libro",
        "title": "mi-libro",
        "authors": ["Alice"],
        "language": "es",
        "integration_key": "claude",
        "integration_skills_dir": ".claude/skills",
        "integration_options": {},
        "no_git": False,
        "force": False,
        "json_output": False,
        "git_status": "initialized",
        "deprecated_flags_seen": [],
    }
    base.update(overrides)
    return ResolvedInvocation(**base)  # type: ignore[arg-type]


def test_resolved_invocation_rejects_invalid_language() -> None:
    with pytest.raises(ValueError, match="ISO 639-1"):
        _make_resolved(language="xx")


def test_resolved_invocation_rejects_empty_authors() -> None:
    with pytest.raises(ValueError, match="authors"):
        _make_resolved(authors=[])


def test_resolved_invocation_rejects_absolute_skills_dir() -> None:
    with pytest.raises(ValueError, match="relative"):
        _make_resolved(integration_skills_dir="/abs/path")


def test_resolved_invocation_rejects_skills_dir_with_dotdot() -> None:
    with pytest.raises(ValueError, match="\\.\\."):
        _make_resolved(integration_skills_dir="../escape")


def test_init_options_record_rejects_wrong_schema_version() -> None:
    resolved = _make_resolved()
    with pytest.raises(ValueError, match="schema_version"):
        InitOptionsRecord(
            schema_version=2,
            created_at="2026-05-29T12:00:00Z",
            bookwright_version="0.0.1",
            options=resolved,
        )


def test_init_options_record_rejects_invalid_timestamp() -> None:
    resolved = _make_resolved()
    with pytest.raises(ValueError, match="created_at"):
        InitOptionsRecord(
            schema_version=1,
            created_at="not-an-iso-stamp",
            bookwright_version="0.0.1",
            options=resolved,
        )


def test_success_envelope_shape() -> None:
    resolved = _make_resolved()
    envelope = success_envelope(resolved, warnings=["w"])
    assert envelope["status"] == "ok"
    assert envelope["warnings"] == ["w"]


def test_error_envelope_shape() -> None:
    envelope = error_envelope("boom", "x", {"k": "v"}, rolled_back=True)
    assert envelope["status"] == "error"
    assert envelope["rolled_back"] is True
    assert envelope["details"] == {"k": "v"}


def test_dump_success_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    _init_envelope.dump_success_to_stdout({"status": "ok"})
    captured = capsys.readouterr()
    assert json.loads(captured.out.rstrip("\n")) == {"status": "ok"}


def test_dump_error_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    _init_envelope.dump_error_to_stdout({"status": "error"})
    captured = capsys.readouterr()
    assert json.loads(captured.out.rstrip("\n")) == {"status": "error"}


def test_serialize_options_record_uses_indent_2() -> None:
    record = build_options_record(_make_resolved())
    payload = _init_envelope.serialize_options_record(record)
    decoded = payload.decode("utf-8")
    assert decoded.endswith("\n")
    assert "  " in decoded


# ---------- _init_scaffold ----------


def test_ledger_refuses_writes_outside_root(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    with pytest.raises(TargetOutsideProjectRootError):
        ledger.record_new_file(tmp_path.parent / "outside.txt")


def test_ledger_rollback_unlinks_new_file(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    target = tmp_path / "newfile.txt"
    _init_scaffold.write_bytes_atomic(target, b"hi", ledger)
    assert target.read_text() == "hi"

    ledger.rollback()
    assert not target.exists()


def test_ledger_rollback_restores_overwritten_file(tmp_path: Path) -> None:
    target = tmp_path / "pre.txt"
    target.write_text("ORIGINAL", encoding="utf-8")

    ledger = BackupLedger(tmp_path)
    _init_scaffold.write_bytes_atomic(target, b"NEW", ledger)
    assert target.read_text() == "NEW"

    ledger.rollback()
    assert target.read_text() == "ORIGINAL"


def test_ledger_rollback_restores_directory(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    new_dir = tmp_path / "dir" / "sub"
    _init_scaffold.mkdir_tracked(new_dir, ledger)
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

    monkeypatch.setattr("bookwright.commands._init_scaffold.shutil.copy2", boom)
    ledger = BackupLedger(tmp_path)
    with pytest.raises(BackupCreationError):
        ledger.record_overwrite(target)


def test_ledger_commit_prunes_cache(tmp_path: Path) -> None:
    target = tmp_path / "pre.txt"
    target.write_text("ORIGINAL", encoding="utf-8")

    ledger = BackupLedger(tmp_path)
    _init_scaffold.write_bytes_atomic(target, b"NEW", ledger)
    ledger.commit()

    cache = tmp_path / ".bookwright" / "cache"
    assert not cache.exists() or not any(cache.rglob("*"))


def test_mkdir_tracked_noop_when_exists(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    existing = tmp_path / "already-here"
    existing.mkdir()
    _init_scaffold.mkdir_tracked(existing, ledger)
    assert ledger.entries == ()


# ---------- _init_git ----------


def test_git_available_returns_bool() -> None:
    assert isinstance(_init_git.git_available(), bool)


def test_is_inside_existing_repo(tmp_path: Path) -> None:
    inner = tmp_path / "inner"
    inner.mkdir()
    assert _init_git.is_inside_existing_repo(inner) is False

    (tmp_path / ".git").mkdir()
    assert _init_git.is_inside_existing_repo(inner) is True


def test_init_and_commit_raises_git_init_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeCompleted:
        returncode = 1
        stderr = "fatal: cannot do that"
        stdout = ""

    monkeypatch.setattr(
        "bookwright.commands._init_git.subprocess.run", lambda *a, **k: FakeCompleted()
    )

    ledger = BackupLedger(tmp_path)
    with pytest.raises(_init_git.GitInitError) as exc:
        _init_git.init_and_commit(tmp_path, "msg", "Author", ledger)
    assert "fatal" in exc.value.stderr
