"""The shared project/manifest fault boundary, once for all three subcommands.

``show``/``set``/``clear`` all enter through ``commands._project.load_manifest_or_exit``
(FR-013, research D7/D10); parametrizing over the three invocations pins the one
contract — exit 2, structured ``code`` in the envelope — in one place instead of
a copy per command module.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app

_INVOCATIONS = [
    pytest.param(["focus", "show", "--json"], id="show"),
    pytest.param(["focus", "set", "--target", "cap-04", "--json"], id="set"),
    pytest.param(["focus", "clear", "--json"], id="clear"),
]


@pytest.mark.parametrize("argv", _INVOCATIONS)
def test_outside_project(outside_project: Path, runner: CliRunner, argv: list[str]) -> None:
    result = runner.invoke(app, argv)
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "not_a_project"


@pytest.mark.parametrize("argv", _INVOCATIONS)
def test_invalid_manifest(project: Path, runner: CliRunner, argv: list[str]) -> None:
    (project / "manifest.toml").write_text("this = = invalid toml", encoding="utf-8")
    result = runner.invoke(app, argv)
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "invalid_manifest"
