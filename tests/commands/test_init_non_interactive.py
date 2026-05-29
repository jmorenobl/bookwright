"""FR-029 — `--here` in non-empty + non-interactive refuses."""

from __future__ import annotations

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from bookwright.cli import app

from .conftest import dirhash


def test_non_interactive_here_refuses(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    non_interactive_io: None,
) -> None:
    subdir = scaffold_in_tmp / "non-empty"
    subdir.mkdir()
    (subdir / "user-file.md").write_text("hi", encoding="utf-8")
    os.chdir(subdir)

    snapshot = dirhash(subdir)

    result = runner.invoke(app, ["init", "--here", "--json"])
    assert result.exit_code == 4, result.stdout

    payload = json.loads(result.stdout)
    assert payload["code"] == "non_interactive_here"
    assert payload["details"]["modern"] == "--force"

    assert dirhash(subdir) == snapshot
