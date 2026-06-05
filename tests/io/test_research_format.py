"""Format-conformance of the shared **rich** research fixture (SC-004/005).

The iteration-14 ``bookwright-research`` skill instructs the agent to emit
``bible/research/*`` files in exactly the shape ``map_research()`` parses. This
test pins that the *shared* rich fixture (``tests/fixtures/research.py``, the same
content the skill's reference doc describes) round-trips with **zero**
``ResearchError`` and carries the provenance the success criteria require:

* **SC-005** — the conflicting pair maps to two distinct findings, each with its
  own (different) source; no silent collapse.
* **SC-004** — every source carries an ``original_quote``; every foreign-language
  source (``original_language`` ≠ book ``es``) carries a ``translation``.

Contract IDs: contracts/research-file-format.md. The fixture content lives in one
place; this test imports it and defines none of its own.
"""

from __future__ import annotations

from pathlib import Path

from rdflib.term import URIRef

from bookwright.golem.slug import make_slug
from bookwright.io.research import ResearchResult, map_research
from tests.fixtures.research import (
    BAJA_CLAIM,
    CONFLICT_CLAIM_A,
    CONFLICT_CLAIM_B,
    CONSTRAINED_ENTITY,
    PROMOTED_CLAIM,
    write_research_fixture,
)

_URI_BASE = "https://example.org/conformance/"
_BOOK_LANGUAGE = "es"


def _map(tmp_path: Path) -> ResearchResult:
    """Write the rich fixture under ``tmp_path`` and map it (constrained entity resolvable)."""
    research_dir = tmp_path / "bible" / "research"
    write_research_fixture(research_dir)
    entity_slug = make_slug(CONSTRAINED_ENTITY)
    bible_index = {entity_slug: URIRef(f"{_URI_BASE}character/{entity_slug}")}
    return map_research(
        project_root=tmp_path,
        research_dir=research_dir,
        uri_base=_URI_BASE,
        book_language=_BOOK_LANGUAGE,
        bible_index=bible_index,
        timeline_uri=URIRef(f"{_URI_BASE}timeline"),
    )


def test_rich_fixture_maps_without_research_error(tmp_path: Path) -> None:
    # The whole tree is conformant: map_research raises nothing and the
    # constrained entity resolves, so no soft warnings either (SC-003 link is real).
    result = _map(tmp_path)
    assert len(result.sources) == 4
    assert result.warnings == ()
    # The promoted finding and its anchor are present, plus the open question.
    claims = {f.claim for f in result.findings if f.claim is not None}
    assert PROMOTED_CLAIM in claims
    assert any(f.open for f in result.findings)
    assert len(result.anchors) == 1


def test_conflicting_pair_yields_two_findings_each_with_own_source(tmp_path: Path) -> None:
    # SC-005 — the two divergent accounts of the 1944 event do NOT collapse: two
    # distinct findings, each carrying exactly one source, and the sources differ.
    result = _map(tmp_path)
    conflict = [f for f in result.findings if f.claim in {CONFLICT_CLAIM_A, CONFLICT_CLAIM_B}]
    assert {f.claim for f in conflict} == {CONFLICT_CLAIM_A, CONFLICT_CLAIM_B}
    assert all(len(f.sources) == 1 for f in conflict)
    assert conflict[0].sources[0] != conflict[1].sources[0]


def test_every_source_has_quote_and_foreign_sources_have_translation(tmp_path: Path) -> None:
    # SC-004 — full provenance: an original-language quotation on every source, and
    # a translation on each source whose language differs from the book's.
    result = _map(tmp_path)
    for source in result.sources:
        assert source.original_quote.strip(), source.name
        if source.original_language != _BOOK_LANGUAGE:
            assert source.translation and source.translation.strip(), source.name
        else:
            # The reader drops a translation when the languages match (research D6).
            assert source.translation is None, source.name


def test_baja_finding_is_present_and_unanchored(tmp_path: Path) -> None:
    # SC-006 (reader side) — the baja-reliability finding exists as a finding and no
    # anchor promotes it; the reader builds only the anchors the file declares.
    result = _map(tmp_path)
    baja = next(f for f in result.findings if f.claim == BAJA_CLAIM)
    assert all(anchor.promotes != baja.uri for anchor in result.anchors)
