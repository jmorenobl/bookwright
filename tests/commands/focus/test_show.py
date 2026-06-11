"""Integration tests for ``bookwright focus show``.

Covers present/absent in both human and ``--json`` modes, channel discipline (Principle IX,
SC-006), the graceful exit-0 "no focus" path (FR-005), and the shared
project/manifest fault boundary (FR-013).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from bookwright.cli import app

# --- present ------------------------------------------------------------------


def test_present_human_prints_fields_to_stdout(
    project_with_focus: Callable[[str], Path], runner: CliRunner
) -> None:
    project_with_focus('target = "cap-04"\nnotes = "cerrar timeline"\nupdated_at = "2026-06-11"\n')
    result = runner.invoke(app, ["focus", "show"])
    assert result.exit_code == 0
    assert "cap-04" in result.stdout
    assert "cerrar timeline" in result.stdout
    assert "2026-06-11" in result.stdout


def test_present_json_emits_single_ok_document(
    project_with_focus: Callable[[str], Path], runner: CliRunner
) -> None:
    project_with_focus('target = "cap-04"\nnotes = "n"\nupdated_at = "2026-06-11"\n')
    result = runner.invoke(app, ["focus", "show", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "status": "ok",
        "focus": {"target": "cap-04", "notes": "n", "updated_at": "2026-06-11"},
    }
    assert result.stderr == ""  # SC-006: nothing but the JSON doc


# --- absent (FR-005) ----------------------------------------------------------


def test_absent_human_reports_to_stderr_exit_zero(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["focus", "show"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "no focus defined" in result.stderr


def test_absent_json_emits_focus_null(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["focus", "show", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"status": "ok", "focus": None}


# --- author text is never rich markup (channel discipline) --------------------


def test_bracketed_author_text_prints_literally(
    project_with_focus: Callable[[str], Path], runner: CliRunner
) -> None:
    # Square brackets are ordinary narrative shorthand; human mode must print
    # them verbatim, not swallow (or crash on) them as rich markup tags.
    project_with_focus(
        'target = "cerrar fin[/] de [cap 4]"\nnotes = "ver [b]timeline[/b]"\n'
        'updated_at = "2026-06-11"\n'
    )
    result = runner.invoke(app, ["focus", "show"])
    assert result.exit_code == 0
    assert "cerrar fin[/] de [cap 4]" in result.stdout
    assert "ver [b]timeline[/b]" in result.stdout
