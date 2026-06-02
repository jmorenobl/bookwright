"""Ad-hoc agentskills.io linter invariants - rules 1-4 (FR-015, SC-002).

Rule 5 (``forbidden_injection``) is covered in ``test_skill_capabilities.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.integrations import ClaudeIntegration
from bookwright.integrations.constants import SKILL_DESCRIPTION_MAX_LENGTH
from bookwright.integrations.errors import SkillLintError
from bookwright.integrations.lint import approx_tokens, lint_skill_md
from bookwright.integrations.materialize import generate_skill_md, iter_command_sources
from bookwright.io.fs import NullLedger


def _write_skill(skill_dir: Path, *, name: str, description: str, body: str) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = (
        "---\n"
        f"name: {name}\n"
        f"description: {description!r}\n"
        "license: Apache-2.0\n"
        "metadata:\n"
        "  author: bookwright\n"
        "  version: 0.0.1\n"
        "---\n"
    )
    (skill_dir / "SKILL.md").write_text(frontmatter + body, encoding="utf-8")


def test_every_materialized_source_lints_clean(tmp_path: Path) -> None:
    """SC-002 — all 10 materialized sources lint clean (100%)."""

    integration = ClaudeIntegration()
    for source in iter_command_sources():
        result = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
        assert result is not None
        lint_skill_md(result.parent)  # must not raise


def test_rule_invalid_frontmatter_missing_file(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    skill_dir.mkdir()
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "invalid_frontmatter"


def test_rule_invalid_frontmatter_empty_metadata(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("no fence at all\n", encoding="utf-8")
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "invalid_frontmatter"


def test_rule_name_mismatch(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    _write_skill(skill_dir, name="bookwright-other", description="hi", body="# body\n")
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "name_mismatch"


def test_rule_description_too_long(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    over_cap = "a" * (SKILL_DESCRIPTION_MAX_LENGTH + 1)
    _write_skill(skill_dir, name="bookwright-x", description=over_cap, body="# body\n")
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "description_too_long"


def test_rule_body_over_budget(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    # approx_tokens uses ceil(len/4) (or tiktoken); make a body well over 5000 tokens.
    huge_body = "palabra " * 6000
    assert approx_tokens(huge_body) >= 5000
    _write_skill(skill_dir, name="bookwright-x", description="hi", body=huge_body)
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "body_over_budget"
