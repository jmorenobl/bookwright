"""Unit/integration tests for ``bookwright integration use`` (the swap command).

Covers the happy swap (claude → generic and back), idempotency, the residue
policy (old skills dir untouched), the structured fault model, and the manifest
round-trip (comments preserved, still loadable).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.core.manifest import Manifest
from bookwright.integrations import base
from bookwright.integrations.errors import SkillMaterializationError
from bookwright.integrations.lint import lint_skill_md
from bookwright.integrations.materialize import iter_command_sources

EXPECTED_SKILL_COUNT = len(iter_command_sources())


def _skill_dirs(skills_root: Path) -> list[Path]:
    return sorted(p.parent for p in skills_root.rglob("SKILL.md"))


@pytest.fixture()
def claude_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> Path:
    """Init a fresh ``claude`` project under ``tmp_path`` and ``chdir`` into it."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "libro", "--integration", "claude", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    project = tmp_path / "libro"
    monkeypatch.chdir(project)
    return project


def test_swap_to_generic_materializes_and_updates_manifest(
    claude_project: Path, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["integration", "use", "generic", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["integration"] == "generic"
    assert payload["skills_dir"] == ".agents/skills"
    assert payload["count"] == EXPECTED_SKILL_COUNT

    agents = _skill_dirs(claude_project / ".agents" / "skills")
    assert len(agents) == EXPECTED_SKILL_COUNT
    for skill_dir in agents:
        lint_skill_md(skill_dir)  # production agentskills.io gate; raises on violation

    manifest = Manifest.load(claude_project / "manifest.toml")
    assert manifest.integration.key == "generic"
    assert manifest.integration.skills_dir == ".agents/skills"


def test_swap_leaves_old_skills_untouched(claude_project: Path, runner: CliRunner) -> None:
    """Residue policy: the previous .claude/skills/ is left in place (no cleanup)."""
    before = _skill_dirs(claude_project / ".claude" / "skills")
    assert runner.invoke(app, ["integration", "use", "generic", "--json"]).exit_code == 0
    after = _skill_dirs(claude_project / ".claude" / "skills")
    assert after == before


def test_swap_is_idempotent(claude_project: Path, runner: CliRunner) -> None:
    assert runner.invoke(app, ["integration", "use", "generic", "--json"]).exit_code == 0
    second = runner.invoke(app, ["integration", "use", "generic", "--json"])
    assert second.exit_code == 0
    assert json.loads(second.stdout)["count"] == EXPECTED_SKILL_COUNT


def test_swap_round_trips_back_to_claude(claude_project: Path, runner: CliRunner) -> None:
    assert runner.invoke(app, ["integration", "use", "generic", "--json"]).exit_code == 0
    back = runner.invoke(app, ["integration", "use", "claude", "--json"])
    assert back.exit_code == 0
    payload = json.loads(back.stdout)
    assert payload["skills_dir"] == ".claude/skills"
    assert Manifest.load(claude_project / "manifest.toml").integration.key == "claude"


def test_manifest_comments_survive_the_swap(claude_project: Path, runner: CliRunner) -> None:
    """The TOML round-trip preserves comments and unrelated keys (FR-020)."""
    manifest_text = (claude_project / "manifest.toml").read_text(encoding="utf-8")
    assert runner.invoke(app, ["integration", "use", "generic", "--json"]).exit_code == 0
    after = (claude_project / "manifest.toml").read_text(encoding="utf-8")
    # A representative comment from the [integration] block is still present.
    assert "Recorded integration metadata" in after
    assert "Recorded integration metadata" in manifest_text


def test_unknown_integration_key_is_exit_2(claude_project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["integration", "use", "nope", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["code"] == "unknown_integration"


def test_outside_project_is_exit_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["integration", "use", "generic", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "not_a_project"


def test_human_output_goes_to_stderr_not_stdout(claude_project: Path, runner: CliRunner) -> None:
    """Without --json, stdout stays empty and the summary lands on stderr (Principle IX)."""
    result = runner.invoke(app, ["integration", "use", "generic"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "switched integration to 'generic'" in result.stderr


def test_unknown_key_human_error_on_stderr(claude_project: Path, runner: CliRunner) -> None:
    """Without --json, an error writes a single line to stderr and nothing to stdout."""
    result = runner.invoke(app, ["integration", "use", "nope"])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "bookwright: error:" in result.stderr


def test_invalid_manifest_is_exit_2(claude_project: Path, runner: CliRunner) -> None:
    """An unparseable manifest surfaces the config envelope, not a traceback."""
    (claude_project / "manifest.toml").write_text("this = = invalid", encoding="utf-8")
    result = runner.invoke(app, ["integration", "use", "generic", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "invalid_manifest"


def test_materialization_failure_rolls_back(
    claude_project: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure mid-materialization leaves the project byte-identical (atomicity)."""

    def _boom(*args: object, **kwargs: object) -> None:
        raise SkillMaterializationError(skill="bookwright-bible", rule="residual_token", detail="x")

    monkeypatch.setattr(base, "generate_skill_md", _boom)
    result = runner.invoke(app, ["integration", "use", "generic", "--json"])
    assert result.exit_code == 3
    assert json.loads(result.stdout)["code"] == "skill_materialization_failed"
    # Rolled back: no generic skills dir was left behind, manifest unchanged.
    assert not (claude_project / ".agents" / "skills").exists()
    assert Manifest.load(claude_project / "manifest.toml").integration.key == "claude"
