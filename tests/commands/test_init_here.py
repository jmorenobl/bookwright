"""`bookwright init --here`."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app

from .conftest import dirhash

pytestmark = pytest.mark.usefixtures("git_available")


def test_here_in_empty_cwd(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """Acceptance Scenario 1 — empty cwd scaffolds directly."""

    subdir = scaffold_in_tmp / "my-here-project"
    subdir.mkdir()
    os.chdir(subdir)

    result = runner.invoke(app, ["init", "--here", "--json"])
    assert result.exit_code == 0, result.stdout

    assert (subdir / "manifest.toml").is_file()
    assert (subdir / ".bookwright").is_dir()
    assert (subdir / ".git").is_dir()

    completed = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=str(subdir),
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Initial commit from bookwright init" in completed.stdout


def test_here_already_initialized_refusal(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """FR-028 — `.bookwright/` present → refuse even with --force."""

    subdir = scaffold_in_tmp / "existing"
    (subdir / ".bookwright").mkdir(parents=True)
    os.chdir(subdir)

    snapshot = dirhash(subdir)

    for argv in (["init", "--here", "--json"], ["init", "--here", "--force", "--json"]):
        result = runner.invoke(app, argv)
        assert result.exit_code == 3, result.stdout
        payload = json.loads(result.stdout)
        assert payload["code"] == "already_initialized"

    assert dirhash(subdir) == snapshot


def test_here_force_overrides_prompt(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """FR-026 — `--force` skips the confirm prompt in --here mode."""

    subdir = scaffold_in_tmp / "my-here-project"
    subdir.mkdir()
    (subdir / "notes.txt").write_text("USER NOTES", encoding="utf-8")
    os.chdir(subdir)

    result = runner.invoke(app, ["init", "--here", "--force", "--json"])
    assert result.exit_code == 0, result.stdout

    assert (subdir / "notes.txt").read_text(encoding="utf-8") == "USER NOTES"
    assert (subdir / "manifest.toml").is_file()


def test_here_with_project_name_mutex(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """FR-002 — `init mi-libro --here` is rejected."""

    result = runner.invoke(app, ["init", "mi-libro", "--here", "--json"])
    assert result.exit_code == 2, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "mutually_exclusive"


def test_here_inside_existing_repo_skips_git(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """FR-025 — existing .git/ is preserved; no new init / commit."""

    subdir = scaffold_in_tmp / "existing-repo"
    subdir.mkdir()
    subprocess.run(["git", "init"], cwd=str(subdir), capture_output=True, check=True)
    sentinel = subdir / "sentinel.txt"
    sentinel.write_text("preserved", encoding="utf-8")
    subprocess.run(["git", "add", "sentinel.txt"], cwd=str(subdir), capture_output=True, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=T", "commit", "-m", "seed"],
        cwd=str(subdir),
        capture_output=True,
        check=True,
    )
    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(subdir),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    os.chdir(subdir)

    result = runner.invoke(app, ["init", "--here", "--force", "--json"])
    assert result.exit_code == 0, result.stdout

    payload = json.loads(result.stdout)
    assert payload["git_status"] == "skipped_existing_repo"
    expected_warning = "bookwright: warning: existing .git/ detected; skipped git init and commit"
    assert expected_warning in payload["warnings"]

    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(subdir),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert head_before == head_after

    payload_on_disk = json.loads(
        (subdir / ".bookwright" / "init-options.json").read_text(encoding="utf-8")
    )
    assert payload_on_disk["options"]["git_status"] == "skipped_existing_repo"
