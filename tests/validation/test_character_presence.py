"""``character_presence`` — orphan(error) rule + the not-evaluated guard.

The unknown-mention (``warning``) rule moved out to ``character_unknown_mentions``
(issue #1, track A): this validator now keeps only the deterministic orphan direction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.indexers import RdflibIndexer
from bookwright.validation.base import NotEvaluated, Severity, Violation
from bookwright.validation.validators.character_presence import CharacterPresence
from tests.validation.conftest import load_context, write_project


def _run(root: Path) -> list[Violation]:
    return CharacterPresence().validate(load_context(root), RdflibIndexer())


def test_no_prose_and_empty_roster_is_not_evaluated(project_root: Path) -> None:
    # Both inputs empty (no manuscript prose AND no bible roster) → not-evaluated:
    # there is nothing to cross-check in either direction (FR-004).
    write_project(project_root, characters=[], manuscript={})
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == (
        "there is no manuscript prose and no bible character roster to cross-check"
    )


def test_empty_manuscript_with_roster_stays_evaluated_and_emits_orphans(
    project_root: Path,
) -> None:
    # An empty manuscript with a NON-EMPTY roster MUST stay evaluated and still emit the
    # error-level orphan findings byte-for-byte — the rule that protects the gate
    # (FR-003/FR-004). This is NOT not-evaluated.
    write_project(project_root, characters=["Aparici", "Peña"], manuscript={})
    findings = _run(project_root)  # does not raise
    orphans = [f for f in findings if f.severity == Severity.error]
    assert {f.source for f in orphans} == {
        "bible/characters/aparici.md",
        "bible/characters/peña.md",
    }
    assert all("never mentioned in the manuscript" in f.message for f in orphans)


def test_orphan_bible_character_is_error(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici", "Peña"],
        manuscript={"cap-01.md": "Aparici saludó al señor.\n"},
    )
    findings = _run(project_root)
    orphans = [f for f in findings if f.severity == Severity.error]
    assert len(orphans) == 1
    assert "Peña" in orphans[0].message
    assert orphans[0].source == "bible/characters/peña.md"
    # Prose validator — no graph, no triples on the emitted finding (Principle X).
    assert orphans[0].triples == ()


def test_clean_project_has_no_findings(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici saludó.\n"},
    )
    assert _run(project_root) == []
