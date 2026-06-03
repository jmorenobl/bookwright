"""C2 / FR-007 — every materialized SKILL.md satisfies agentskills.io (Principle VII).

A fresh ``init`` for both shipped integrations (``claude`` → ``.claude/skills/``,
``generic`` → ``.agents/skills/``) must materialize exactly the 10 source commands
as ``<skills_dir>/<name>/SKILL.md``, each passing the *shipped* linter
``bookwright.integrations.lint.lint_skill_md``. The test reuses that linter rather
than re-encoding the 64/1024 bounds, so there is a single source of truth for the
agentskills.io limits (Amendment A). A negative assertion guards Principle VI: the
toolkit never writes a legacy ``*/commands/`` directory.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.integrations.lint import lint_skill_md
from bookwright.integrations.materialize import iter_command_sources

#: (integration key, skills dir relative to the project root).
INTEGRATIONS = [("claude", ".claude/skills"), ("generic", ".agents/skills")]

#: The number of source commands shipped — derived, never hard-coded (Amendment A).
EXPECTED_SKILL_COUNT = len(iter_command_sources())


def _skill_dirs(skills_root: Path) -> list[Path]:
    """Every materialized skill directory (one ``SKILL.md`` each) under ``skills_root``."""
    return sorted(p.parent for p in skills_root.rglob("SKILL.md"))


@pytest.mark.parametrize(("integration", "skills_rel"), INTEGRATIONS)
def test_materialized_skills_pass_the_shipped_linter(
    cli: CliRunner, workdir: Path, integration: str, skills_rel: str
) -> None:
    """Each generated SKILL.md passes ``lint_skill_md`` and the count == source commands."""
    result = cli.invoke(app, ["init", "libro", "--integration", integration, "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout

    project = workdir / "libro"
    skills_root = project / skills_rel
    assert skills_root.is_dir(), f"{integration}: expected skills under {skills_rel}"

    skill_dirs = _skill_dirs(skills_root)
    assert len(skill_dirs) == EXPECTED_SKILL_COUNT

    for skill_dir in skill_dirs:
        # Reuses the production agentskills.io gate; raises SkillLintError on violation.
        lint_skill_md(skill_dir)


@pytest.mark.parametrize("integration", ["claude", "generic"])
def test_no_legacy_commands_directory(cli: CliRunner, workdir: Path, integration: str) -> None:
    """Principle VI: a ``*/commands/`` directory is never created by ``init``."""
    result = cli.invoke(app, ["init", "libro", "--integration", integration, "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    project = workdir / "libro"
    assert not list(project.rglob("commands")), "a legacy commands/ dir was materialized"
