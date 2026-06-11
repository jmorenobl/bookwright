"""Integration tests for ``bookwright focus clear``.

Covers present (real removal) and absent (no-op success), both human and ``--json``, the
``cleared`` boolean discriminator (FR-010), channel discipline (Principle IX),
and the shared project/manifest fault boundary (FR-013).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.core import Manifest

# --- present: real removal ----------------------------------------------------


def test_present_human_removes_block_reports_to_stderr(
    project_with_focus: Callable[[str], Path], runner: CliRunner
) -> None:
    root = project_with_focus('target = "cap-04"\nupdated_at = "2026-06-11"\n')
    result = runner.invoke(app, ["focus", "clear"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "focus cleared" in result.stderr
    assert Manifest.load(root / "manifest.toml").focus is None
    assert "[focus]" not in (root / "manifest.toml").read_text(encoding="utf-8")


def test_present_json_reports_cleared_true(
    project_with_focus: Callable[[str], Path], runner: CliRunner
) -> None:
    project_with_focus('target = "cap-04"\nupdated_at = "2026-06-11"\n')
    result = runner.invoke(app, ["focus", "clear", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"status": "ok", "cleared": True}


# --- absent: no-op success (FR-010) ------------------------------------------


def test_absent_human_reports_nothing_to_clear(project: Path, runner: CliRunner) -> None:
    before = (project / "manifest.toml").read_text(encoding="utf-8")
    result = runner.invoke(app, ["focus", "clear"])
    assert result.exit_code == 0
    assert "no focus to clear" in result.stderr
    # No-op leaves the manifest byte-for-byte untouched (no pointless rewrite).
    assert (project / "manifest.toml").read_text(encoding="utf-8") == before


def test_absent_json_reports_cleared_false(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["focus", "clear", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"status": "ok", "cleared": False}


# --- shared fault boundary ----------------------------------------------------


def test_outside_project(outside_project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["focus", "clear", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "not_a_project"


def test_invalid_manifest(project: Path, runner: CliRunner) -> None:
    (project / "manifest.toml").write_text("this = = invalid toml", encoding="utf-8")
    result = runner.invoke(app, ["focus", "clear", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "invalid_manifest"
