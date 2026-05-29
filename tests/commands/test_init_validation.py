"""FR-021a — PROJECT_NAME validation grid."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app

from .conftest import dirhash


@pytest.mark.parametrize(
    "raw_name,rule",
    [
        ("", "empty"),
        ("   ", "empty"),
        ("foo/bar", "path_separator"),
        ("foo\\bar", "path_separator"),
        (".", "dot_or_dotdot"),
        ("..", "dot_or_dotdot"),
        (".hidden", "leading_dot"),
        ("x" * 101, "too_long"),
        ("CON", "reserved_name"),
        ("PRN", "reserved_name"),
        ("COM1", "reserved_name"),
        ("LPT9", "reserved_name"),
    ],
)
def test_invalid_project_name_grid(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    raw_name: str,
    rule: str,
) -> None:
    snapshot_before = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", raw_name, "--json", "--no-git"])

    assert result.exit_code == 2, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["code"] == "invalid_project_name"
    assert payload["details"]["rule"] == rule

    snapshot_after = dirhash(scaffold_in_tmp)
    assert snapshot_after == snapshot_before


@pytest.mark.parametrize(
    "raw_name,expected_slug",
    [
        ("mi-libro", "mi-libro"),
        ("Mi Libro", "mi-libro"),
        ("Café-Society", "cafe-society"),
        ("librö-ñ", "libro-n"),
    ],
)
def test_positive_project_names(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    raw_name: str,
    expected_slug: str,
) -> None:
    result = runner.invoke(app, ["init", raw_name, "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["project_slug"] == expected_slug
    assert (scaffold_in_tmp / expected_slug / "manifest.toml").is_file()
