"""``character_presence`` — orphan(error) + unknown-mention(warning) + dedup."""

from __future__ import annotations

from pathlib import Path

from bookwright.indexers import RdflibIndexer
from bookwright.validation.base import Severity, Violation
from bookwright.validation.validators.character_presence import CharacterPresence
from tests.validation.conftest import load_context, write_project


def _run(root: Path) -> list[Violation]:
    return CharacterPresence().validate(load_context(root), RdflibIndexer())


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


def test_unknown_mention_is_warning_deduped_per_name(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={
            "cap-01.md": (
                "Aparici saludó al señor Garcia.\n"
                "Más tarde, Garcia se marchó.\n"
                "El viejo Garcia desapareció.\n"
            )
        },
    )
    findings = _run(project_root)
    warnings = [f for f in findings if f.severity == Severity.warning]
    garcia = [f for f in warnings if "Garcia" in f.message]
    # Exactly one finding for the name, citing the first occurrence (not per mention).
    assert len(garcia) == 1
    assert garcia[0].source == "manuscript/cap-01.md:1"


def test_clean_project_has_no_findings(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici saludó.\n"},
    )
    assert _run(project_root) == []


def test_sentence_initial_capital_is_not_flagged(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici llegó.\nLuego todo cambió.\n"},
    )
    # "Luego" opens a sentence → grammatical capital, never an unknown mention.
    assert all("Luego" not in f.message for f in _run(project_root))
