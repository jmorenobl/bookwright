"""End-to-end subprocess test for `bookwright version --json`.

CliRunner does NOT exercise the `[project.scripts].bookwright` entry point or
`__main__.py` wiring, so this is the only test that proves an external agent
invoking the CLI sees a pure-JSON stdout (Principio IX, FR-009a).
"""

import json
import subprocess
import sys

import bookwright


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
                "golem_schema_version": "unknown",
            },
            separators=(",", ":"),
        )
        + "\n"
    )
    assert result.returncode == 0, f"stderr was: {result.stderr!r}"
    assert result.stdout == expected_stdout
    assert result.stderr == ""
