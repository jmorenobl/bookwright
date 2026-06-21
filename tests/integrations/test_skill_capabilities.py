"""capability-aware output + the FR-013 injection invariant (SC-006)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.integrations.errors import SkillLintError
from bookwright.integrations.lint import lint_skill_md


def _write_skill(skill_dir: Path, body: str) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {skill_dir.name}\n"
        "description: trigger text\n"
        "license: EUPL-1.2\n"
        "metadata:\n"
        "  author: bookwright\n"
        "  version: 0.0.1\n"
        "---\n" + body,
        encoding="utf-8",
    )


# ---------- Rule 5: forbidden_injection allowlist (FR-013) ----------


def test_injection_to_absent_wrapper_is_rejected(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    _write_skill(skill_dir, "Run !`/usr/local/bin/wrapper` now.\n")
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "forbidden_injection"


def test_injection_reading_project_file_passes(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    _write_skill(skill_dir, "Context: !`cat bible/constitution.md`\n")
    lint_skill_md(skill_dir)  # must not raise


def test_injection_invoking_bookwright_passes(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    _write_skill(skill_dir, "Graph: !`bookwright graph build --json`\n")
    lint_skill_md(skill_dir)  # must not raise


def test_injection_read_command_with_absolute_path_is_rejected(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    _write_skill(skill_dir, "Leak: !`cat /etc/passwd`\n")
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "forbidden_injection"


def test_empty_injection_is_rejected(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    _write_skill(skill_dir, "Broken: !`` here.\n")
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "forbidden_injection"


def test_injection_with_unbalanced_quotes_is_rejected(tmp_path: Path) -> None:
    # shlex.split would raise ValueError; it must surface as a structured
    # SkillLintError, not escape the JSON envelope (Principle IX).
    skill_dir = tmp_path / "bookwright-x"
    _write_skill(skill_dir, 'Broken: !`cat "unterminated` here.\n')
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "forbidden_injection"


def test_injection_read_command_with_home_path_is_rejected(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bookwright-x"
    _write_skill(skill_dir, "Leak: !`cat ~/secrets`\n")
    with pytest.raises(SkillLintError) as exc:
        lint_skill_md(skill_dir)
    assert exc.value.rule == "forbidden_injection"
