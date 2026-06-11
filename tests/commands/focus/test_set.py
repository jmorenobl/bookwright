"""Integration tests for ``bookwright focus set``.

Covers create/update, the partial-``notes`` rule (FR-007), the ``updated_at``
stamp (FR-006), empty-``--target`` rejection leaving the manifest unchanged
(FR-008), channel discipline (Principle IX, FR-013), and the shared
project/manifest fault boundary.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

import bookwright.commands.focus.set_ as set_module
from bookwright.cli import app
from bookwright.core import Manifest

_FIXED_DATE = "2026-06-11"


@pytest.fixture(autouse=True)
def _freeze_today(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stamp a deterministic ``updated_at`` instead of the real system clock."""
    monkeypatch.setattr(set_module, "_today", lambda: _FIXED_DATE)


# --- create -------------------------------------------------------------------


def test_create_with_target_only_defaults_notes_empty(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["focus", "set", "--target", "cap-04"])
    assert result.exit_code == 0
    focus = Manifest.load(project / "manifest.toml").focus
    assert focus is not None
    assert focus.target == "cap-04"
    assert focus.notes == ""
    assert focus.updated_at == _FIXED_DATE


def test_create_human_confirmation_to_stderr_stdout_empty(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["focus", "set", "--target", "cap-04"])
    assert result.exit_code == 0
    assert result.stdout == ""  # human mode writes nothing to stdout
    assert "cap-04" in result.stderr


def test_create_json_emits_single_ok_document(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["focus", "set", "--target", "cap-04", "--notes", "x", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "status": "ok",
        "focus": {"target": "cap-04", "notes": "x", "updated_at": _FIXED_DATE},
    }


# --- partial-notes rule on update (FR-007) -----------------------------------


def test_update_target_only_preserves_existing_notes(
    project_with_focus: Callable[[str], Path], runner: CliRunner
) -> None:
    root = project_with_focus('target = "old"\nnotes = "keep me"\nupdated_at = "2026-01-01"\n')
    result = runner.invoke(app, ["focus", "set", "--target", "new"])
    assert result.exit_code == 0
    focus = Manifest.load(root / "manifest.toml").focus
    assert focus is not None
    assert focus.target == "new"
    assert focus.notes == "keep me"  # preserved
    assert focus.updated_at == _FIXED_DATE  # refreshed


def test_update_notes_set(project_with_focus: Callable[[str], Path], runner: CliRunner) -> None:
    root = project_with_focus('target = "old"\nnotes = "old note"\nupdated_at = "2026-01-01"\n')
    runner.invoke(app, ["focus", "set", "--target", "new", "--notes", "fresh"])
    focus = Manifest.load(root / "manifest.toml").focus
    assert focus is not None and focus.notes == "fresh"


def test_update_notes_cleared_with_empty_string(
    project_with_focus: Callable[[str], Path], runner: CliRunner
) -> None:
    root = project_with_focus('target = "old"\nnotes = "old note"\nupdated_at = "2026-01-01"\n')
    runner.invoke(app, ["focus", "set", "--target", "new", "--notes", ""])
    focus = Manifest.load(root / "manifest.toml").focus
    assert focus is not None and focus.notes == ""


# --- empty-target rejection (FR-008) -----------------------------------------


@pytest.mark.parametrize("bad", ["   ", ""])
def test_empty_target_rejected_manifest_unchanged(
    project: Path, runner: CliRunner, bad: str
) -> None:
    before = (project / "manifest.toml").read_text(encoding="utf-8")
    result = runner.invoke(app, ["focus", "set", "--target", bad, "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "focus_target_empty"
    # FR-008: the manifest is left byte-for-byte unchanged.
    assert (project / "manifest.toml").read_text(encoding="utf-8") == before


def test_empty_target_human_mode_error_to_stderr(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["focus", "set", "--target", "   "])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr.startswith("bookwright: error:")


# --- author text is never rich markup (channel discipline) --------------------


def test_confirmation_echoes_bracketed_target_literally(project: Path, runner: CliRunner) -> None:
    # Square brackets are ordinary narrative shorthand; the confirmation must
    # echo them verbatim, not parse (or crash on) them as rich markup tags.
    target = "cerrar fin[/] de [cap 4]"
    result = runner.invoke(app, ["focus", "set", "--target", target])
    assert result.exit_code == 0
    assert target in result.stderr
