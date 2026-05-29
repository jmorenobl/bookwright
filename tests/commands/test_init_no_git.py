"""US4 — `--no-git` and git-missing warning."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app


def test_no_git_skips_repo(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["git_status"] == "skipped_by_flag"

    project_root = scaffold_in_tmp / "mi-libro"
    assert not (project_root / ".git").exists()


def test_fake_git_missing_warns_and_succeeds(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    fake_git_missing: None,
) -> None:
    result = runner.invoke(app, ["init", "mi-libro", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["git_status"] == "skipped_no_binary"
    expected_warning = (
        "bookwright: warning: git not found on PATH; project created without a repository"
    )
    assert expected_warning in payload["warnings"]

    project_root = scaffold_in_tmp / "mi-libro"
    assert not (project_root / ".git").exists()


@pytest.mark.usefixtures("git_available")
def test_no_git_inside_existing_repo_leaves_it_alone(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    """An already-initialised parent repo stays untouched."""

    parent = scaffold_in_tmp / "outer"
    parent.mkdir()
    subprocess.run(["git", "init"], cwd=str(parent), capture_output=True, check=True)
    head_before_file = parent / "sentinel.txt"
    head_before_file.write_text("seed", encoding="utf-8")
    subprocess.run(["git", "add", "sentinel.txt"], cwd=str(parent), capture_output=True, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=T", "commit", "-m", "seed"],
        cwd=str(parent),
        capture_output=True,
        check=True,
    )
    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(parent),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    os.chdir(parent)
    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["git_status"] == "skipped_by_flag"

    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(parent),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert head_before == head_after


@pytest.mark.usefixtures("git_available")
def test_commit_author_email_fallback(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When no user-level git identity is present, the fallback email is used."""

    fake_home = scaffold_in_tmp / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("HOME", str(fake_home))

    result = runner.invoke(app, ["init", "mi-libro", "--json"])
    assert result.exit_code == 0, result.stdout

    completed = subprocess.run(
        ["git", "log", "-1", "--format=%ae"],
        cwd=str(scaffold_in_tmp / "mi-libro"),
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == "author@bookwright.local"
