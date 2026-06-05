"""`--ai`, `--ai-skills`, `--ai-commands-dir`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app

from .conftest import dirhash


def test_ai_alias_warns_and_succeeds(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    """FR-003 — `--ai claude` works with a deprecation warning."""

    result = runner.invoke(app, ["init", "mi-libro", "--ai", "claude", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    expected_warning = "bookwright: warning: --ai is deprecated; use --integration instead"
    assert expected_warning in payload["warnings"]

    options_payload = json.loads(
        (scaffold_in_tmp / "mi-libro" / ".bookwright" / "init-options.json").read_text()
    )
    assert options_payload["options"]["deprecated_flags_seen"] == ["--ai"]


def test_ai_alias_routes_value_when_integration_default(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    """If --ai is set and --integration is the default, --ai's value wins."""

    result = runner.invoke(app, ["init", "mi-libro", "--ai", "generic", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["integration"]["key"] == "generic"


def test_integration_wins_when_both_set(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    """If both --ai and --integration are set, --integration wins."""

    result = runner.invoke(
        app,
        [
            "init",
            "mi-libro",
            "--ai",
            "generic",
            "--integration",
            "claude",
            "--no-git",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["integration"]["key"] == "claude"


@pytest.mark.parametrize(
    "argv",
    [
        ["init", "mi-libro", "--ai-skills", "--no-git", "--json"],
        ["init", "mi-libro", "--ai-commands-dir", "x", "--no-git", "--json"],
    ],
)
def test_removed_flags_fail_with_structured_error(
    runner: CliRunner, scaffold_in_tmp: Path, argv: list[str]
) -> None:
    """FR-004 / FR-031 — removed flags fail and write nothing."""

    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, argv)
    assert result.exit_code == 2, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "removed_flag"
    assert "details" in payload
    assert payload["details"]["flag"].startswith("--ai-")

    assert dirhash(scaffold_in_tmp) == snapshot


def test_removed_flag_wins_over_mutex(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    """`--removed-flag` is reported, NOT `mutually_exclusive`, when both apply."""

    result = runner.invoke(
        app,
        ["init", "mi-libro", "--here", "--ai-skills", "--no-git", "--json"],
    )
    assert result.exit_code == 2, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "removed_flag"
