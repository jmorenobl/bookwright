"""E2E — ``bookwright init`` materializes lint-clean skills (SC-001/002/007/008)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.integrations import materialize as materialize_module
from bookwright.integrations.errors import SkillLintError
from bookwright.integrations.lint import lint_skill_md
from bookwright.integrations.materialize import iter_command_sources

_ROSTER = {Path(node.name).stem for node in iter_command_sources()}


@pytest.mark.parametrize(
    "argv,skills_rel",
    [
        (["init", "proj", "--integration", "claude", "--no-git"], ".claude/skills"),
        (["init", "proj", "--integration", "generic", "--no-git"], ".agents/skills"),
        (
            [
                "init",
                "proj",
                "--integration",
                "generic",
                "--integration-options",
                "--skills-dir .cursor/skills",
                "--no-git",
            ],
            ".cursor/skills",
        ),
    ],
)
def test_init_materializes_lint_clean_skills(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    argv: list[str],
    skills_rel: str,
) -> None:
    result = runner.invoke(app, argv)
    assert result.exit_code == 0, result.stdout

    skills_dir = scaffold_in_tmp / "proj" / skills_rel
    materialized = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    assert materialized == _ROSTER

    for name in _ROSTER:
        skill_dir = skills_dir / name
        assert (skill_dir / "SKILL.md").is_file()
        lint_skill_md(skill_dir)  # SC-002 — every generated skill lints clean
        # SC-007 — nothing the materializer wrote escapes the skills_dir.
        for path in skill_dir.rglob("*"):
            assert path.is_relative_to(skills_dir)

    assert not (skills_dir / ".bookwright-skills-placeholder").exists()


def test_init_scaffolds_outline_units_dir(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    """FR-012/A2 — a fresh init contains `outline/units/` (mirrors bible/settings)."""
    result = runner.invoke(app, ["init", "proj", "--no-git"])
    assert result.exit_code == 0, result.stdout
    assert (scaffold_in_tmp / "proj" / "outline" / "units").is_dir()


def test_forced_lint_failure_aborts_with_envelope(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-016 — a lint failure yields a skill_lint_failed envelope, no invalid SKILL.md."""

    def boom(skill_dir: Path) -> None:
        raise SkillLintError(skill=skill_dir.name, rule="description_too_long", detail="len=1102")

    monkeypatch.setattr(materialize_module, "lint_skill_md", boom)

    result = runner.invoke(app, ["init", "proj", "--no-git", "--json"])
    assert result.exit_code != 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "skill_lint_failed"
    assert payload["details"]["rule"] == "description_too_long"
    assert payload["rolled_back"] is True

    # The aborted init left no project skills behind (rollback + self-cleanup).
    assert not (scaffold_in_tmp / "proj" / ".claude" / "skills" / "bookwright-analyze").exists()


def test_orphan_rollback_preserves_preexisting_skills_dir(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SC-008/FR-019 — a mid-roster failure over a pre-existing skills_dir leaves
    zero materialized bookwright-* dirs and the user's file untouched."""

    project = scaffold_in_tmp / "proj"
    skills_dir = project / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    user_file = skills_dir / "my-notes.md"
    user_file.write_text("USER CONTENT\n", encoding="utf-8")

    real_lint = lint_skill_md

    def flaky(skill_dir: Path) -> None:
        if skill_dir.name == "bookwright-bible":
            raise SkillLintError(skill=skill_dir.name, rule="body_over_budget", detail="forced")
        real_lint(skill_dir)

    monkeypatch.setattr(materialize_module, "lint_skill_md", flaky)

    result = runner.invoke(app, ["init", "proj", "--force", "--no-git", "--json"])
    assert result.exit_code != 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "skill_lint_failed"

    # Zero materialized bookwright-* skill dirs remain ...
    remaining = {
        p.name for p in skills_dir.iterdir() if p.is_dir() and p.name.startswith("bookwright-")
    }
    assert remaining == set()
    # ... and the user's pre-existing file is intact.
    assert user_file.read_text(encoding="utf-8") == "USER CONTENT\n"
