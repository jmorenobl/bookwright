"""``setting_continuity`` — cross-file contradicting descriptors."""

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


def test_block_prefixed_lines_keep_findings_and_line_numbers(project_root: Path) -> None:
    # FR-009 / Story 1: leading bullet/blockquote markers on the descriptor lines do not
    # move the findings or their line numbers — the per-line scan reads RAW, so the
    # `\bterm\b` matching (and `.number` locator) is identical to the bare form.
    write_project(
        project_root,
        settings=["Ayelo"],
        manuscript={
            "cap-01.md": "# Capítulo 1\n> Ayelo es una villa coastal y luminosa.\n",
            "cap-02.md": "- Ayelo, inland y polvorienta, dormía.\n",
        },
    )
    findings = _run(project_root)
    assert len(findings) == 1
    finding = findings[0]
    assert "coastal" in finding.message and "inland" in finding.message
    # `coastal` is on line 2 of cap-01 (after the heading), `inland` on line 1 of cap-02.
    assert finding.source == "manuscript/cap-01.md:2"
    assert "cap-01.md:2" in finding.message and "cap-02.md:1" in finding.message
