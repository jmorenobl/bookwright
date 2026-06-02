"""Shared ``setup()`` materialization contract (FR-001, FR-016, FR-017, FR-019, SC-008)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.core import Manifest
from bookwright.integrations import (
    SKILL_PLACEHOLDER_MARKER_NAME,
    ClaudeIntegration,
    GenericIntegration,
    MalformedOptionError,
)
from bookwright.integrations import base as base_module
from bookwright.integrations import materialize as materialize_module
from bookwright.integrations.errors import SkillLintError
from bookwright.integrations.lint import lint_skill_md as real_lint_skill_md
from bookwright.integrations.materialize import iter_command_sources
from bookwright.io.fs import BackupLedger

_ROSTER = {Path(node.name).stem for node in iter_command_sources()}


# ---------- materialization (no marker) ----------


@pytest.mark.parametrize(
    "integration_cls,skills_rel",
    [
        (ClaudeIntegration, ".claude/skills"),
        (GenericIntegration, ".agents/skills"),
    ],
)
def test_setup_materializes_one_skill_per_command(
    integration_cls: type[ClaudeIntegration | GenericIntegration],
    skills_rel: str,
    tmp_project: Path,
    minimal_manifest: Manifest,
) -> None:
    integration_cls().setup(tmp_project, minimal_manifest, None)
    skills_dir = tmp_project / skills_rel
    assert skills_dir.is_dir()

    materialized = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    assert materialized == _ROSTER
    for name in _ROSTER:
        assert (skills_dir / name / "SKILL.md").is_file()

    # No placeholder marker is written any more.
    assert not (skills_dir / SKILL_PLACEHOLDER_MARKER_NAME).exists()


def test_setup_generic_with_parsed_options_overrides_dir(
    tmp_project: Path, minimal_manifest: Manifest
) -> None:
    GenericIntegration().setup(tmp_project, minimal_manifest, {"skills_dir": ".cursor/skills"})
    assert (tmp_project / ".cursor/skills" / "bookwright-bible" / "SKILL.md").is_file()
    assert (tmp_project / ".agents/skills").exists() is False


# ---------- containment guards (iteration-3, still raise) ----------


@pytest.mark.parametrize("escape_value", ["../escape/skills", "../../etc/foo", "a/../../escape"])
def test_setup_rejects_skills_dir_escaping_project_root(
    escape_value: str, tmp_project: Path, minimal_manifest: Manifest
) -> None:
    with pytest.raises(MalformedOptionError) as exc:
        GenericIntegration().setup(tmp_project, minimal_manifest, {"skills_dir": escape_value})
    assert exc.value.to_dict()["rule"] == "escapes_project_root"
    assert (tmp_project / ".agents/skills").exists() is False


@pytest.mark.parametrize(
    "collapse_value,expected_value",
    [("", "."), (".", "."), ("./", "."), ("foo/..", "foo/..")],
)
def test_setup_rejects_skills_dir_that_resolves_to_project_root(
    collapse_value: str, expected_value: str, tmp_project: Path, minimal_manifest: Manifest
) -> None:
    with pytest.raises(MalformedOptionError) as exc:
        GenericIntegration().setup(tmp_project, minimal_manifest, {"skills_dir": collapse_value})
    payload = exc.value.to_dict()
    assert payload["rule"] == "resolves_to_project_root"
    assert payload["value"] == expected_value


# ---------- ledger contract ----------


def test_setup_defaults_to_null_ledger_when_omitted(
    tmp_project: Path, minimal_manifest: Manifest
) -> None:
    """Standalone-callable: omitting `ledger` still materializes (NullLedger default)."""

    ClaudeIntegration().setup(tmp_project, minimal_manifest, None)
    assert (tmp_project / ".claude/skills" / "bookwright-bible" / "SKILL.md").is_file()


def test_setup_records_every_materialized_path_with_backup_ledger(
    tmp_project: Path, minimal_manifest: Manifest
) -> None:
    ledger = BackupLedger(tmp_project)
    ClaudeIntegration().setup(tmp_project, minimal_manifest, None, ledger=ledger)

    recorded = {entry.target for entry in ledger.entries}
    skills_dir = (tmp_project / ".claude/skills").resolve()
    for name in _ROSTER:
        assert (skills_dir / name / "SKILL.md").resolve() in recorded


def test_setup_does_not_read_manifest(tmp_project: Path) -> None:
    class SentinelManifest:
        def __getattr__(self, item: str) -> object:  # pragma: no cover - guard only
            raise AssertionError(f"setup() must NOT read manifest attributes (touched {item!r})")

    GenericIntegration().setup(tmp_project, SentinelManifest(), None)  # type: ignore[arg-type]
    assert (tmp_project / ".agents/skills" / "bookwright-bible" / "SKILL.md").is_file()


# ---------- orphan rollback over a pre-existing skills_dir (SC-008, FR-019) ----------


def test_orphan_rollback_over_preexisting_skills_dir(
    tmp_project: Path,
    minimal_manifest: Manifest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mid-roster lint failure → ledger rollback removes ALL materialized skills,
    leaving the user's pre-existing skills_dir content untouched."""

    skills_dir = tmp_project / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    user_file = skills_dir / "my-notes.md"
    user_file.write_text("USER CONTENT\n", encoding="utf-8")

    def flaky_lint(skill_dir: Path) -> None:
        if skill_dir.name == "bookwright-bible":
            raise SkillLintError(skill="bookwright-bible", rule="body_over_budget", detail="forced")
        real_lint_skill_md(skill_dir)

    monkeypatch.setattr(materialize_module, "lint_skill_md", flaky_lint)

    ledger = BackupLedger(tmp_project)
    with pytest.raises(SkillLintError):
        ClaudeIntegration().setup(tmp_project, minimal_manifest, None, ledger=ledger)

    ledger.rollback()

    # No materialized skill dirs remain ...
    remaining = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    assert remaining == set()
    # ... and the user's pre-existing file is byte-for-byte intact.
    assert user_file.read_text(encoding="utf-8") == "USER CONTENT\n"


def test_empty_roster_writes_no_skill_dirs(
    tmp_project: Path, minimal_manifest: Manifest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Edge case — an empty roster creates the skills_dir but no skill subdirs."""

    monkeypatch.setattr(base_module, "iter_command_sources", lambda: [])
    ClaudeIntegration().setup(tmp_project, minimal_manifest, None)
    skills_dir = tmp_project / ".claude/skills"
    assert skills_dir.is_dir()
    assert list(skills_dir.iterdir()) == []
