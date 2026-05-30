"""End-to-end subprocess tests for `bookwright … --json`.

CliRunner does NOT exercise the `[project.scripts].bookwright` entry point or
`__main__.py` wiring, so these are the only tests that prove an external agent
invoking the CLI sees a pure-JSON stdout (Principio IX, FR-009a).
"""

import json
import subprocess
import sys

import bookwright
from bookwright.commands.check import RUNTIME_MODULES


def test_version_json_subprocess_stdout_pure() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "bookwright", "version", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    expected_stdout = (
        json.dumps(
            {
                "package_version": bookwright.__version__,
                "golem_schema_version": "golem-1.1",
            },
            separators=(",", ":"),
        )
        + "\n"
    )
    assert result.returncode == 0, f"stderr was: {result.stderr!r}"
    assert result.stdout == expected_stdout
    assert result.stderr == ""


def test_check_json_subprocess_stdout_pure() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "bookwright", "check", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    found_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    expected_checks: list[dict[str, str]] = [
        {"name": "python_version", "status": "ok", "detail": found_version},
    ]
    expected_checks.extend({"name": f"dependency:{m}", "status": "ok"} for m in RUNTIME_MODULES)
    expected_stdout = (
        json.dumps({"ok": True, "checks": expected_checks}, separators=(",", ":")) + "\n"
    )
    assert result.returncode == 0, f"stderr was: {result.stderr!r}"
    assert result.stdout == expected_stdout
    assert result.stderr == ""
