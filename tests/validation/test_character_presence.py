"""``character_presence`` — orphan(error) + unknown-mention(warning) + dedup."""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.indexers import RdflibIndexer
from bookwright.io.prose import prose_view
from bookwright.validation.base import NotEvaluated, Severity, Violation
from bookwright.validation.validators.character_presence import CharacterPresence
from tests.validation.conftest import load_context, write_project


def _run(root: Path) -> list[Violation]:
    return CharacterPresence().validate(load_context(root), RdflibIndexer())


def test_no_prose_and_empty_roster_is_not_evaluated(project_root: Path) -> None:
    # Both inputs empty (no manuscript prose AND no bible roster) → not-evaluated:
    # there is nothing to cross-check in either direction (FR-009).
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
    # (FR-004/FR-012). This is NOT not-evaluated.
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


def test_leading_dialogue_dash_opening_word_is_not_flagged(project_root: Path) -> None:
    # FR-002 / SC-001: a Spanish dialogue line opens with a leading em dash glued
    # to the first spoken word (`—Esto`). The SEAM strips that leading dash with NO
    # validator-code change, so `Esto` lands at offset 0 and inherits the existing
    # sentence-initial exemption — exactly the mechanism the heading/blockquote tests use.
    # First, the seam itself strips the marker (so the word lands at offset 0):
    assert prose_view("—Esto es el porvenir")[0].normalized == "Esto es el porvenir"
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici habló.\n—Esto es el porvenir.\n"},
    )
    findings = _run(project_root)
    # `Esto` opens the dialogue line after the dash is stripped → exempt; no finding.
    assert all("Esto" not in f.message for f in findings)


def test_mid_line_name_in_dialogue_is_still_flagged(project_root: Path) -> None:
    # FR-009 / SC-002: the other direction of the both-directions guarantee. Only
    # the LEADING marker is neutralized — a genuine off-roster name later in the dialogue
    # line still fires. `Quirón` sits mid-line after `—Pregúntale a`, so it is non-initial
    # and flagged exactly once; the opening word `Pregúntale` is exempt.
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici asintió.\n—Pregúntale a Quirón —dijo.\n"},
    )
    findings = _run(project_root)
    warnings = [f for f in findings if f.severity == Severity.warning]
    quiron = [f for f in warnings if "Quirón" in f.message]
    assert len(quiron) == 1
    assert quiron[0].source == "manuscript/cap-01.md:2"
    # The opening word is NOT flagged — only the leading dash was neutralized.
    assert all("Pregúntale" not in f.message for f in findings)


def test_declared_setting_tokens_are_not_flagged(project_root: Path) -> None:
    # Story 1 / FR-002/FR-003 / SC-001: the capitalized tokens of a declared multi-word
    # SETTING ("la Real Fábrica de Paños") named in the manuscript produce NO
    # unknown-mention warning — the regression DEBT-010 closes.
    write_project(
        project_root,
        characters=["Aparici"],
        settings=["la Real Fábrica de Paños"],
        manuscript={"cap-01.md": "Aparici visitó la Real Fábrica de Paños esa tarde.\n"},
    )
    findings = _run(project_root)
    warnings = [f for f in findings if f.severity == Severity.warning]
    assert all(token not in f.message for f in warnings for token in ("Real", "Fábrica", "Paños"))
    assert warnings == []


def test_declared_location_tokens_are_not_flagged(project_root: Path) -> None:
    # Story 1 (location arm) / FR-002/FR-015: a declared LOCATION (G13) named in the
    # manuscript — full phrase and any ≥3-letter token — produces no unknown-mention warning.
    write_project(
        project_root,
        characters=["Aparici"],
        locations=["Casa del Reloj"],
        manuscript={"cap-01.md": "Aparici entró en la Casa del Reloj al amanecer.\n"},
    )
    warnings = [f for f in _run(project_root) if f.severity == Severity.warning]
    assert all(token not in f.message for f in warnings for token in ("Casa", "Reloj"))
    assert warnings == []


def test_declared_object_tokens_are_not_flagged(project_root: Path) -> None:
    # Story 1 (object arm) / FR-002/FR-015: a declared OBJECT (G16) named in the
    # manuscript — full phrase and any ≥3-letter token — produces no unknown-mention warning.
    write_project(
        project_root,
        characters=["Aparici"],
        objects=["Espada del Rey"],
        manuscript={"cap-01.md": "Aparici empuñó la Espada del Rey en silencio.\n"},
    )
    warnings = [f for f in _run(project_root) if f.severity == Severity.warning]
    assert all(token not in f.message for f in warnings for token in ("Espada", "Rey"))
    assert warnings == []


def test_off_bible_name_still_fires_with_wider_roster(project_root: Path) -> None:
    # Story 2 / FR-005 / SC-004: the wider roster suppresses only false positives. A proper
    # noun absent from characters, settings, locations AND objects still produces exactly
    # one warning with the same message/severity and first-occurrence locator.
    write_project(
        project_root,
        characters=["Aparici"],
        settings=["Ayelo"],
        locations=["Onteniente"],
        objects=["Telar"],
        manuscript={"cap-01.md": "Aparici saludó al señor Garcia.\nLuego Garcia se fue.\n"},
    )
    warnings = [f for f in _run(project_root) if f.severity == Severity.warning]
    garcia = [f for f in warnings if "Garcia" in f.message]
    assert len(garcia) == 1
    assert garcia[0].source == "manuscript/cap-01.md:1"
    assert "no bible entry" in garcia[0].message


def test_unmentioned_setting_location_object_yield_no_finding(project_root: Path) -> None:
    # Story 3 / FR-004 / SC-003: a declared setting/location/object NEVER named in the
    # manuscript produces neither an orphan `error` (that rule is character-only) nor any
    # absence `warning`. Only the character roster is mentioned → the project is clean.
    write_project(
        project_root,
        characters=["Aparici"],
        settings=["la Real Fábrica de Paños"],
        locations=["Casa del Reloj"],
        objects=["Espada del Rey"],
        manuscript={"cap-01.md": "Aparici caminó solo.\n"},
    )
    assert _run(project_root) == []


def test_not_evaluated_guard_unchanged_by_declared_environments(project_root: Path) -> None:
    # Story 4 / FR-007 / SC-005: the iteration-040 abstain stays clavado on
    # `not character_roster and not files` — declared settings/locations/objects do NOT
    # make it evaluable, and the reason string is byte-identical.
    write_project(
        project_root,
        characters=[],
        settings=["Ayelo"],
        locations=["Onteniente"],
        objects=["Telar"],
        manuscript={},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == (
        "there is no manuscript prose and no bible character roster to cross-check"
    )


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
