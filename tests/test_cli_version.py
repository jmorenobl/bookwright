"""CliRunner-based coverage of `bookwright version` in human and --json modes."""

import json

from typer.testing import CliRunner

import bookwright
from bookwright.cli import app


def test_version_human(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert bookwright.__version__ in result.stdout
    assert "unknown" in result.stdout


def test_version_json_byte_exact(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version", "--json"])
    assert result.exit_code == 0
    expected = (
        json.dumps(
            {
                "package_version": bookwright.__version__,
                "golem_schema_version": "unknown",
            },
            separators=(",", ":"),
        )
        + "\n"
    )
    assert result.stdout == expected
