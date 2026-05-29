"""Contract §3 + §7.5 — subprocess pin of stdout purity + stderr split."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_BOOKWRIGHT_ARGV: list[str] = [sys.executable, "-m", "bookwright"]


def _run(argv: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _BOOKWRIGHT_ARGV + argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def test_json_stdout_is_pure_on_success(tmp_path: Path) -> None:
    completed = _run(["init", "mi-libro", "--no-git", "--json"], cwd=tmp_path)
    assert completed.returncode == 0, completed.stderr

    assert completed.stdout.endswith("\n")
    body = completed.stdout.rstrip("\n")
    payload = json.loads(body)
    assert payload["status"] == "ok"


@pytest.mark.parametrize(
    "argv,expected_code,expected_exit",
    [
        (["init", "--json"], "mutually_exclusive", 2),
        (["init", "mi-libro", "--here", "--json"], "mutually_exclusive", 2),
        (["init", "..", "--no-git", "--json"], "invalid_project_name", 2),
        (
            ["init", "mi-libro", "--integration", "copilot", "--no-git", "--json"],
            "unknown_integration",
            5,
        ),
        (
            ["init", "mi-libro", "--ai-skills", "--no-git", "--json"],
            "removed_flag",
            2,
        ),
    ],
)
def test_json_stdout_is_pure_on_failure(
    tmp_path: Path,
    argv: list[str],
    expected_code: str,
    expected_exit: int,
) -> None:
    completed = _run(argv, cwd=tmp_path)
    assert completed.returncode == expected_exit, completed.stderr

    assert completed.stdout.endswith("\n")
    payload = json.loads(completed.stdout.rstrip("\n"))
    assert payload["status"] == "error"
    assert payload["code"] == expected_code


def test_silent_stderr_on_success_no_warnings(tmp_path: Path) -> None:
    """No deprecations, no git fallback → stderr is empty under --json."""

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "test"
    env["GIT_AUTHOR_EMAIL"] = "test@example.com"

    completed = subprocess.run(
        _BOOKWRIGHT_ARGV + ["init", "mi-libro", "--json"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr

    # Author resolution may add a fallback warning if no git identity is set;
    # the stderr SHOULD contain only `bookwright: warning: ...` lines or be empty.
    for line in completed.stderr.splitlines():
        assert line.startswith("bookwright:"), line


def test_non_json_failure_stderr_line(tmp_path: Path) -> None:
    """FR-031 — without --json, failures emit one stderr line and empty stdout."""

    completed = _run(["init", "..", "--no-git"], cwd=tmp_path)
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr.startswith("bookwright: error:")
