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
