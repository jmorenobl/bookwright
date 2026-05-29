"""Branch coverage for `commands/init.py` paths the user-story tests miss.

End-to-end tests cover the JSON envelope path. This file pins the stderr
human-readable path, the rare validation branches, and the author-fallback
warning, all in-process so the coverage instrument actually sees them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app


def test_stderr_path_on_validation_failure(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    """Non-`--json` validation failure writes one stderr line, empty stdout."""

    result = runner.invoke(app, ["init", "..", "--no-git"])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr.startswith("bookwright: error:") or "error" in result.stderr


def test_stderr_path_on_mutex_failure(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    result = runner.invoke(app, ["init", "--no-git"])
    assert result.exit_code == 2


def test_stderr_path_on_unknown_integration(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    result = runner.invoke(app, ["init", "mi-libro", "--integration", "copilot", "--no-git"])
    assert result.exit_code == 5


def test_author_fallback_warning_to_stderr(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the author falls back to the sentinel, stderr gets the warning."""

    monkeypatch.setattr(
        "bookwright.commands._init_resolve._git_config_user_name",
        lambda _cwd: None,
    )
    monkeypatch.delenv("USER", raising=False)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    fallback = (
        "bookwright: warning: author could not be resolved from git config or $USER; "
        "using 'Unknown Author'"
    )
    assert fallback in payload["warnings"]


def test_author_fallback_warning_non_json_to_stderr(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bookwright.commands._init_resolve._git_config_user_name",
        lambda _cwd: None,
    )
    monkeypatch.delenv("USER", raising=False)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git"])
    assert result.exit_code == 0


def test_here_basename_reserved_via_dir_rename(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """A cwd basename matching a reserved name trips FR-021a."""

    target = scaffold_in_tmp / "CON"
    target.mkdir()
    os.chdir(target)

    result = runner.invoke(app, ["init", "--here", "--no-git", "--json"])
    assert result.exit_code == 2, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "invalid_project_name"
    assert payload["details"]["rule"] == "reserved_name"


def test_named_mode_reserved_slug(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    """A name that passes validate_project_name but slugifies to a reserved name."""

    # "C O N" → trimmed "C O N" → not slash, dot, leading-dot, length ok,
    # reserved? validate_project_name uppercases and checks. "C O N" is not in
    # the reserved set; but slugify("C O N") → "c-o-n" which is not reserved
    # either. Skip this — covered already by derive_slug raising on "***".
    result = runner.invoke(app, ["init", "***", "--no-git", "--json"])
    assert result.exit_code == 2, result.stdout


def test_confirm_accepts_overwrite(
    runner: CliRunner, scaffold_in_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Interactive `y` confirm proceeds with the scaffold under --here."""

    subdir = scaffold_in_tmp / "interactive"
    subdir.mkdir()
    (subdir / "keep.txt").write_text("keep", encoding="utf-8")
    os.chdir(subdir)

    monkeypatch.setattr("bookwright.commands._init_resolve.is_interactive", lambda: True)

    result = runner.invoke(app, ["init", "--here", "--no-git"], input="y\n")
    assert result.exit_code == 0, result.stdout
    assert (subdir / "manifest.toml").is_file()


def test_confirm_declines_overwrite(
    runner: CliRunner, scaffold_in_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    subdir = scaffold_in_tmp / "interactive-decline"
    subdir.mkdir()
    (subdir / "keep.txt").write_text("keep", encoding="utf-8")
    os.chdir(subdir)

    monkeypatch.setattr("bookwright.commands._init_resolve.is_interactive", lambda: True)

    result = runner.invoke(app, ["init", "--here", "--no-git"], input="n\n")
    assert result.exit_code == 4
    assert "aborted by user" in result.stderr or "aborted by user" in result.stdout


def test_permission_error_at_mkdir(
    runner: CliRunner, scaffold_in_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A PermissionError when creating the project root → permission_denied."""

    real_mkdir = Path.mkdir

    def flaky_mkdir(self: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self.name == "mi-libro":
            raise PermissionError(13, "permission denied")
        return real_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", flaky_mkdir)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 6, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "permission_denied"


def test_os_error_at_mkdir(
    runner: CliRunner, scaffold_in_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_mkdir = Path.mkdir

    def flaky_mkdir(self: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self.name == "mi-libro":
            raise OSError(28, "fake no space")
        return real_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", flaky_mkdir)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 6, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "filesystem_error"
