"""FR-030 / SC-005 — atomic-or-nothing rollback grid."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app

from .conftest import dirhash

# Cases that fail BEFORE any byte hits disk (validation / CLI parsing).
_VALIDATION_FAILURES: list[tuple[list[str], str, int]] = [
    (["init", "..", "--no-git", "--json"], "invalid_project_name", 2),
    (
        ["init", "mi-libro", "--here", "--no-git", "--json"],
        "mutually_exclusive",
        2,
    ),
    (
        ["init", "mi-libro", "--integration", "copilot", "--no-git", "--json"],
        "unknown_integration",
        5,
    ),
    (
        [
            "init",
            "mi-libro",
            "--integration",
            "generic",
            "--integration-options",
            "--cursor-dir x",
            "--no-git",
            "--json",
        ],
        "unknown_option",
        5,
    ),
    (
        [
            "init",
            "mi-libro",
            "--integration",
            "generic",
            "--integration-options",
            "--skills-dir",
            "--no-git",
            "--json",
        ],
        "malformed_option",
        5,
    ),
    # B1 regression (round-4 audit): absolute --skills-dir tripped the
    # ResolvedInvocation field validator post-mkdir, leaking an orphan
    # project dir AND escaping the structured-error envelope (FR-030).
    (
        [
            "init",
            "mi-libro",
            "--integration",
            "generic",
            "--integration-options",
            "--skills-dir /tmp/foo",
            "--no-git",
            "--json",
        ],
        "malformed_option",
        5,
    ),
    (
        ["init", "mi-libro", "--ai-skills", "--no-git", "--json"],
        "removed_flag",
        2,
    ),
]


@pytest.mark.parametrize("argv,expected_code,expected_exit", _VALIDATION_FAILURES)
def test_pre_scaffold_failure_leaves_tree_unchanged(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    argv: list[str],
    expected_code: str,
    expected_exit: int,
) -> None:
    (scaffold_in_tmp / "decoy.md").write_text("sibling", encoding="utf-8")
    snapshot_before = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, argv)
    assert result.exit_code == expected_exit, result.stdout

    payload = json.loads(result.stdout)
    assert payload["code"] == expected_code
    assert payload["rolled_back"] is False

    assert dirhash(scaffold_in_tmp) == snapshot_before


def test_target_not_empty_failure_leaves_tree_unchanged(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    target = scaffold_in_tmp / "mi-libro"
    target.mkdir()
    (target / "existing.txt").write_text("pre", encoding="utf-8")

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 4, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "target_not_empty"

    assert dirhash(scaffold_in_tmp) == snapshot


def test_already_initialized_failure_leaves_tree_unchanged(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    subdir = scaffold_in_tmp / "existing-project"
    (subdir / ".bookwright").mkdir(parents=True)
    os.chdir(subdir)

    snapshot = dirhash(subdir)

    result = runner.invoke(app, ["init", "--here", "--no-git", "--json"])
    assert result.exit_code == 3, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "already_initialized"

    assert dirhash(subdir) == snapshot


def test_filesystem_error_rolls_back(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulated OSError mid-scaffold via monkeypatched os.replace → ledger rollback."""

    real_replace = os.replace
    fail_after = {"count": 0}

    def flaky_replace(src: str, dst: str) -> None:
        fail_after["count"] += 1
        if fail_after["count"] >= 3:
            raise OSError(28, "fake no space")
        real_replace(src, dst)

    monkeypatch.setattr("bookwright.io.fs.os.replace", flaky_replace)

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 6, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "filesystem_error"
    assert payload["rolled_back"] is True

    assert dirhash(scaffold_in_tmp) == snapshot


def test_integration_setup_failure_rolls_back(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SkillsIntegration.setup() crash → rollback unwinds the partial scaffold."""

    from bookwright.integrations.claude import ClaudeIntegration  # noqa: PLC0415

    def boom(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("integration crashed")

    monkeypatch.setattr(ClaudeIntegration, "setup", boom)

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 6, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "filesystem_error"
    assert payload["rolled_back"] is True

    assert dirhash(scaffold_in_tmp) == snapshot


def test_backup_creation_error_rolls_back(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forced shutil.copy2 failure → backup_creation_error + clean rollback."""

    def flaky_copy(src: str, dst: str) -> None:
        raise PermissionError("backup forbidden")

    monkeypatch.setattr("bookwright.io.fs.shutil.copy2", flaky_copy)

    target = scaffold_in_tmp / "mi-libro"
    target.mkdir()
    (target / "manifest.toml").write_text("# existing", encoding="utf-8")
    (target / "untouched.txt").write_text("keep me", encoding="utf-8")

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", "mi-libro", "--force", "--no-git", "--json"])
    assert result.exit_code == 6, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "backup_creation_error"

    # The restoration may differ ONLY in that the very file we tried to overwrite
    # is still its original; everything else is byte-for-byte unchanged.
    after = dirhash(scaffold_in_tmp)
    # Filter out the .bookwright/cache/backup hierarchy and any token dirs we may
    # have produced; the ledger's rollback should leave the cache empty.
    cache_root = (target / ".bookwright" / "cache").as_posix()

    def _filter(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return [(r, h) for r, h in entries if cache_root not in r]

    assert _filter(after) == _filter(snapshot)


def test_keyboard_interrupt_propagates_after_rollback(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R2 regression — KeyboardInterrupt mid-scaffold rolls back, then re-raises.

    The interrupt must NOT be funnelled through ``classify_filesystem_failure``
    (which would mis-stamp it as ``filesystem_error`` exit 6) and must NOT
    produce a JSON envelope on stdout. Typer's outer shell converts the
    propagated ``KeyboardInterrupt`` into the conventional SIGINT exit
    code 130 — the user-visible signal — but only after our handler has
    rolled back the partial scaffold.
    """

    def boom(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("bookwright.commands.init.scaffold.render_resource_tree", boom)

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])

    # Convention: SIGINT exits 130, NOT 6 (which would be filesystem_error).
    assert result.exit_code == 130, result.stdout
    # No error envelope: stdout must not look like an envelope, and stderr
    # must not contain the human-readable error prefix.
    assert result.stdout.strip() == ""
    assert "bookwright: error:" not in result.stderr
    # Rollback + project_root cleanup leave the parent tree byte-identical.
    assert dirhash(scaffold_in_tmp) == snapshot


def test_system_exit_propagates_after_rollback(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R2 regression — bare ``SystemExit`` mid-scaffold also bypasses the envelope path.

    Only ``typer.Exit`` (which already carries the structured envelope) and
    ``Exception`` subclasses should hit ``classify_filesystem_failure``. A
    bare ``SystemExit`` raised from arbitrary code must roll back and
    re-raise, preserving the original exit code.
    """

    def boom(*args: object, **kwargs: object) -> None:
        raise SystemExit(42)

    monkeypatch.setattr("bookwright.commands.init.scaffold.render_resource_tree", boom)

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])

    assert result.exit_code == 42, result.stdout
    assert result.stdout.strip() == ""
    assert "bookwright: error:" not in result.stderr
    assert dirhash(scaffold_in_tmp) == snapshot


def test_skills_dir_resolves_to_project_root_rolls_back(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    """B3 regression (round-4 audit): setup-time MalformedOptionError used to be
    misclassified as ``filesystem_error`` exit 6 with empty details, hiding the
    real rule (``resolves_to_project_root``). After the fix it surfaces with the
    same shape as parse-time MalformedOptionError, and the rollback removes the
    project dir that the scaffold had already partially populated.
    """

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(
        app,
        [
            "init",
            "x",
            "--integration",
            "generic",
            "--integration-options",
            "--skills-dir .",
            "--no-git",
            "--json",
        ],
    )
    assert result.exit_code == 5, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "malformed_option"
    assert payload["details"]["rule"] == "resolves_to_project_root"
    assert payload["details"]["value"] == "."
    assert payload["rolled_back"] is True

    assert dirhash(scaffold_in_tmp) == snapshot


def test_git_error_rolls_back(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_available: None,
) -> None:
    """Forced git failure → git_error + clean rollback."""

    from bookwright.commands.init import git  # noqa: PLC0415

    def boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise git.GitInitError(stderr="fake git failure")

    monkeypatch.setattr(git, "init_and_commit", boom)

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", "mi-libro", "--json"])
    assert result.exit_code == 7, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "git_error"
    assert payload["rolled_back"] is True

    assert dirhash(scaffold_in_tmp) == snapshot
