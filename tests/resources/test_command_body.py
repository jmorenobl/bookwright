"""FR-007..FR-014 / FR-016a / FR-017 — the command-source body contract.

Body non-empty + Spanish, the eight required sections detectable by ES
heading-keyword, the generative marker/update-in-place rule, the report-only
"no escribe nada" statement, and the inline ``graph build`` for the two commands
that need the project graph. Data-driven by ``helpers`` classification so it
covers all 10 files (US1 + US2) uniformly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.io.frontmatter import parse_frontmatter

from .helpers import (
    GENERATIVE_COMMANDS,
    REPORT_ONLY_COMMANDS,
    command_files,
    looks_spanish,
    read_text,
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
    body = parse_frontmatter(read_text(path)).body
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
    body = parse_frontmatter(read_text(path)).body
    lowered = body.lower()
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
    lowered = parse_frontmatter(read_text(path)).body.lower()
    # FR-012: an explicit report-only / "writes nothing" statement.
    assert "no escribe nada" in lowered or "solo lectura" in lowered, (
        f"{path.name}: no report-only statement"
    )


@pytest.mark.parametrize("name", ["bookwright-constitution", "bookwright-continuity"])
def test_graph_build_is_inline(name: str) -> None:
    # FR-017: the two graph-consuming commands write the CLI call inline.
    path = next(p for p in command_files() if p.stem == name)
    body = parse_frontmatter(read_text(path)).body
    assert "bookwright graph build --json" in body, f"{name}: missing inline graph build"
