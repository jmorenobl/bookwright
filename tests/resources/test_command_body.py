"""FR-007..FR-014 / FR-016a / FR-017 — the command-source body contract.

Body non-empty + Spanish, the eight required sections detectable by ES
heading-keyword, the generative marker/update-in-place rule, the report-only
"no escribe nada" statement, and the inline ``graph build`` for the two commands
that need the project graph. Data-driven by ``helpers`` classification so it
covers all 12 files uniformly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import (
    GENERATIVE_COMMANDS,
    REPORT_ONLY_COMMANDS,
    command_body,
    command_files,
    looks_spanish,
)

#: (FR-007..FR-014) one ES heading-keyword per required section; presence required.
REQUIRED_SECTION_KEYWORDS: tuple[str, ...] = (
    "rol",  # FR-007 Rol / contexto
    "input",  # FR-008 Input esperado
    "procedimiento",  # FR-009 Procedimiento
    "output",  # FR-010 Output esperado
    "leer",  # FR-011 Archivos a leer
    "escribir",  # FR-012 Archivos a escribir (o report-only)
    "faltante",  # FR-013 Información faltante
    "no hacer",  # FR-014 Qué NO hacer
)


def _headings(body: str) -> list[str]:
    return [line.lower() for line in body.splitlines() if line.lstrip().startswith("#")]


@pytest.mark.parametrize("path", command_files(), ids=lambda p: p.name)
def test_body_required_sections_and_language(path: Path) -> None:
    body = command_body(path)
    assert body.strip(), f"{path.name}: empty body"
    assert looks_spanish(body), f"{path.name}: body does not look Spanish"

    headings = _headings(body)
    for keyword in REQUIRED_SECTION_KEYWORDS:
        assert any(keyword in h for h in headings), (
            f"{path.name}: no heading matches required section '{keyword}'"
        )


@pytest.mark.parametrize(
    "path",
    [p for p in command_files() if p.stem in GENERATIVE_COMMANDS],
    ids=lambda p: p.name,
)
def test_generative_marker_and_update_in_place(path: Path) -> None:
    lowered = command_body(path).lower()
    # FR-016a: update-in-place rule stated.
    assert "actualización en sitio" in lowered, f"{path.name}: no update-in-place rule"
    # FR-016/FR-013: the [PENDING: token guidance, or a link to the shared protocol.
    assert "[pending:" in lowered or "pending-protocol.md" in lowered, (
        f"{path.name}: no [PENDING:] guidance nor pending-protocol link"
    )


@pytest.mark.parametrize(
    "path",
    [p for p in command_files() if p.stem in REPORT_ONLY_COMMANDS],
    ids=lambda p: p.name,
)
def test_report_only_states_no_writes(path: Path) -> None:
    lowered = command_body(path).lower()
    # FR-012: an explicit report-only / "writes nothing" statement.
    assert "no escribe nada" in lowered or "solo lectura" in lowered, (
        f"{path.name}: no report-only statement"
    )


@pytest.mark.parametrize(
    "name", ["bookwright-constitution", "bookwright-continuity", "bookwright-verify"]
)
def test_graph_build_is_inline(name: str) -> None:
    # FR-017: the graph-consuming commands write the CLI call inline.
    path = next(p for p in command_files() if p.stem == name)
    body = command_body(path)
    assert "bookwright graph build --json" in body, f"{name}: missing inline graph build"


def _continuity_body() -> str:
    path = next(p for p in command_files() if p.stem == "bookwright-continuity")
    return command_body(path)


def test_continuity_carries_the_fourth_undeclared_character_axis() -> None:
    # Iteration 051 (move 3, first slice): the 4th axis rides inside
    # `## Procedimiento`/`## Output` — no new required heading, the section gate above
    # still passes. The axis names the open-set / undeclared-character judgment, reads
    # the person roster from the SHEETS (`name:`, not a graph label), and reports each
    # undeclared person as one more deviation.
    body = _continuity_body()
    lowered = body.lower()
    # The axis itself, in the procedure.
    assert "cuarto eje" in lowered, "continuity: no fourth axis in the procedure"
    assert "sin declarar" in lowered or "sin ficha" in lowered, (
        "continuity: 4th axis does not name undeclared / sheet-less characters"
    )
    # Grounding: the roster comes from the character sheets' `name:`, not from a graph
    # label — `G1_Character` has no `rdfs:label` (cites references/golem-character.md).
    assert "name:" in body and "rdfs:label" in body, (
        "continuity: 4th axis does not ground the roster in the sheets' name: field"
    )
    assert "references/golem-character.md" in body, (
        "continuity: 4th axis does not cite references/golem-character.md"
    )
    # Output report shape: the exact 'no entry in `bible/characters/`' phrasing.
    assert "no entry in `bible/characters/`" in body, (
        "continuity: ## Output does not report the undeclared mention as a deviation"
    )


def test_continuity_carries_the_fifth_head_hopping_axis() -> None:
    # Iteration 052 (move 3, second slice): the 5th axis ("head-hopping / broken
    # focalization") rides inside `## Procedimiento`/`## Output` — no new required
    # heading, the section gate still passes. The LLM judgment quality is NOT asserted
    # (FR-013, § 20.6.2 decision 4); only the body contract C1-C5.
    body = _continuity_body()
    lowered = body.lower()
    # C1 — the axis itself, in the procedure, named for head-hopping / POV breaks.
    assert "quinto eje" in lowered, "continuity: no fifth axis in the procedure"
    assert "head-hopping" in lowered, "continuity: 5th axis does not name head-hopping"
    # C1(a) — scoped to third-person limited; omniscient/first-person → nothing.
    assert "tercera persona limitada" in lowered, "continuity: 5th axis not scoped to limited-third"
    assert "omnisciente" in lowered and "primera persona" in lowered, (
        "continuity: 5th axis does not exclude omniscient / first person"
    )
    # C2 — grounding cited: voice + POV calendar + roster.
    assert "voz narrativa" in lowered, "continuity: 5th axis does not cite the declared voice"
    assert "bible/pov-structure.md" in body, "continuity: 5th axis does not cite the POV calendar"
    assert "calendario de pov" in lowered, "continuity: 5th axis does not name the POV calendar"
    assert "roster" in lowered, "continuity: 5th axis does not cite the roster"
    # C1(e) — grounding-gap clause: absent / [PENDING] calendar → report the gap, no guess.
    assert "[pending:" in lowered, "continuity: 5th axis does not handle a [PENDING] POV calendar"
    assert "no adivines" in lowered or "no adivina" in lowered, (
        "continuity: 5th axis does not document 'do not guess' on a missing anchor"
    )
    # C3 — ## Output reports each head-hop as one more deviation (judgment, not error).
    assert "interiority of" in body and "POV of" in body, (
        "continuity: ## Output does not report the head-hop deviation phrasing"
    )
    assert "una desviación\nmás" in body or "una desviación más" in body, (
        "continuity: ## Output does not frame the head-hop as one more deviation"
    )


def test_continuity_carries_the_sixth_first_person_axis() -> None:
    # Iteration 054 (move 3, third dimension, judgment half): the 6th axis ("1st-person
    # break / voice slip") rides inside `## Procedimiento`/`## Output` — no new required
    # heading, the section gate still passes. The LLM judgment quality is NOT asserted
    # (FR-017, § 20.6.2 decision 4); only the body contract C1-C3.
    body = _continuity_body()
    lowered = body.lower()
    # C1 — the axis itself, in the procedure, named for the first-person / voice slip.
    assert "sexto eje" in lowered, "continuity: no sixth axis in the procedure"
    assert "primera persona" in lowered, "continuity: 6th axis does not name the first-person slip"
    # C1 — scope DIFFERS from the 5th axis: applies under third person LIMITED OR NOT.
    assert "limitada o no limitada" in lowered, (
        "continuity: 6th axis not scoped to third person limited OR non-limited"
    )
    # C1(c) — judges the pro-drop verbal morphology the explicit-pronoun check cannot see.
    assert "pro-drop" in lowered, "continuity: 6th axis does not name pro-drop morphology"
    assert "Caminé" in body and "Me senté" in body, (
        "continuity: 6th axis does not give the pro-drop examples the deterministic check misses"
    )
    # C1 — grounding is the DECLARED VOICE ONLY (no roster, no POV calendar).
    assert "voz narrativa" in lowered, "continuity: 6th axis does not cite the declared voice"
    assert "bible/constitution.md" in body, (
        "continuity: 6th axis does not ground in bible/constitution.md"
    )
    assert "solo la voz declarada" in lowered, (
        "continuity: 6th axis does not state the declared voice is its only grounding"
    )
    assert "persona gramatical" in lowered, (
        "continuity: 6th axis does not justify why it needs neither roster nor POV calendar"
    )
    # C1(d) — grounding-gap clause: absent / [PENDING] voice → report the gap, no guess.
    assert "[pending:" in lowered, "continuity: 6th axis does not handle a [PENDING] voice"
    assert "no adivines" in lowered or "no adivina" in lowered, (
        "continuity: 6th axis does not document 'do not guess' on a missing declared voice"
    )
    # C1 — ADDS the morphological recall on top of, never suppresses, the explicit-pronoun
    # `warning`s of `focalization`.
    assert "suprime" in lowered, (
        "continuity: 6th axis does not state it never suppresses the explicit-pronoun warnings"
    )
    # C2 — ## Output reports each first-person slip as one more deviation (judgment, not error).
    assert "first-person voice under a narration declared in third person" in body, (
        "continuity: ## Output does not carry the exact first-person deviation phrasing"
    )
    assert "ruptura de 1ª persona" in lowered, (
        "continuity: ## Output axis enumeration does not include the first-person break"
    )
