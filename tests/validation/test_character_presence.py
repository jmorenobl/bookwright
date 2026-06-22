"""``character_presence`` — orphan(error) + unknown-mention(warning) + dedup."""

from __future__ import annotations

from pathlib import Path

from bookwright.indexers import RdflibIndexer
from bookwright.io.prose import prose_view
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


def test_heading_first_word_is_not_flagged(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={
            "cap-01.md": (
                "# Capítulo 1\n"
                "\n"
                "Aparici llegó al muelle.\n"
                "\n"
                "## Escena en el faro\n"
                "\n"
                "Allí esperó.\n"
                "\n"
                "###### El faro\n"
                "\n"
                "Volvió.\n"
            )
        },
    )
    # Multi-depth headings + roster-only prose → the leading ATX marker is stripped,
    # so each title's first word is line-initial and exempt: zero findings (FR-006).
    assert _run(project_root) == []


def test_name_in_heading_body_is_still_flagged(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "# La caída de Elena\nAparici la recordó.\n"},
    )
    findings = _run(project_root)
    warnings = [f for f in findings if f.severity == Severity.warning]
    elena = [f for f in warnings if "Elena" in f.message]
    # Only the marker is stripped: "La" opens the title (exempt) but "Elena" sits
    # mid-line and still fires exactly once, citing the heading's relpath:line (FR-002).
    assert len(elena) == 1
    assert elena[0].source == "manuscript/cap-01.md:1"
    # Prose validator — no graph, no triples on the emitted finding (FR-009 / Principle X).
    assert elena[0].triples == ()


def test_blockquote_off_roster_mention_is_not_flagged(project_root: Path) -> None:
    # Story 2 / FR-011 / SC-003: the class-closure proof. A `> blockquote` off-roster
    # mention is handled by the SEAM's existing `[-*+>]` recognizer with NO
    # validator-code change — `Quevedo` is line-initial after the `> ` strip and so
    # inherits the sentence-initial exemption.
    # First, the seam itself strips the marker (so the name lands at offset 0):
    assert prose_view("> Quevedo lo dijo")[0].normalized == "Quevedo lo dijo"
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici escuchó.\n> Quevedo lo dijo, sentenció.\n"},
    )
    findings = _run(project_root)
    # `Quevedo` opens the blockquote line → exempt; only the roster `Aparici` appears,
    # so there is no unknown mention. Contrast with the raw `> Quevedo …`, where
    # `Quevedo` would be non-initial (after `> `) and would fire.
    assert all("Quevedo" not in f.message for f in findings)


def test_locator_is_source_line_not_match_offset(project_root: Path) -> None:
    # Story 3 / FR-010 / SC-004: a finding on a marker-bearing line reports the line's
    # 1-based source number, never the offset of the match within the stripped text.
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici miró.\n\n## La sombra de Quevedo\n"},
    )
    findings = _run(project_root)
    quevedo = [f for f in findings if "Quevedo" in f.message]
    assert len(quevedo) == 1
    # `Quevedo` sits mid-heading on source line 3 → cited as `:3` (not the offset 0
    # the stripped "La sombra de Quevedo" would imply for the line's first word).
    assert quevedo[0].source == "manuscript/cap-01.md:3"
