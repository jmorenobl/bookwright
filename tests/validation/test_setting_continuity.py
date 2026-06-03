"""``setting_continuity`` — cross-file contradicting descriptors (T022)."""

from __future__ import annotations

from pathlib import Path

from bookwright.indexers import RdflibIndexer
from bookwright.validation.base import Severity, Violation
from bookwright.validation.validators.setting_continuity import SettingContinuity
from tests.validation.conftest import load_context, write_project


def _run(root: Path) -> list[Violation]:
    return SettingContinuity().validate(load_context(root), RdflibIndexer())


def test_contradicting_descriptors_warn_citing_both(project_root: Path) -> None:
    write_project(
        project_root,
        settings=["Ayelo"],
        manuscript={
            "cap-01.md": "Ayelo es una villa coastal y luminosa.\n",
            "cap-02.md": "Ayelo, inland y polvorienta, dormía.\n",
        },
    )
    findings = _run(project_root)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity == Severity.warning
    assert "coastal" in finding.message and "inland" in finding.message
    assert "cap-01.md" in finding.message and "cap-02.md" in finding.message


def test_consistent_setting_has_no_findings(project_root: Path) -> None:
    write_project(
        project_root,
        settings=["Ayelo"],
        manuscript={
            "cap-01.md": "Ayelo, coastal, brillaba.\n",
            "cap-02.md": "Ayelo seguía coastal al amanecer.\n",
        },
    )
    assert _run(project_root) == []


def test_same_file_two_terms_does_not_warn(project_root: Path) -> None:
    # The clash must be *across* files; one file holding both is not a continuity break.
    write_project(
        project_root,
        settings=["Ayelo"],
        manuscript={"cap-01.md": "Ayelo era coastal, casi inland.\n"},
    )
    assert _run(project_root) == []
