"""The two demonstrative SPARQL queries (FR-007/FR-008/SC-003).

Builds a graph from sample entities through :class:`RdflibIndexer` and proves both
recall axes the dogfooding exercise measured as broken: resolving a narrative unit
by its authored name (Q1, FR-007) and listing a sequence's members in their declared
order via the materialized ordinal (Q2, FR-008). Queries use full IRIs (no PREFIX
reliance), matching ``contracts/narrative-label-order.md``.
"""

from __future__ import annotations

from rdflib.term import URIRef

from bookwright.golem import NarrativeSequence, NarrativeUnit
from bookwright.golem.base import GolemEntity
from bookwright.indexers.rdflib_indexer import RdflibIndexer
from tests.golem.conftest import B

_G9 = "https://w3id.org/golem/ontology#G9_Narrative_Unit"
_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
_PROPER_PART = "http://www.ontologydesignpatterns.org/ont/dlp/DOLCE-Lite.owl#proper-part"
_ORDINAL = "https://bookwright.dev/vocab/bw#sequenceOrdinal"


def _build(*entities: GolemEntity) -> RdflibIndexer:
    """Feed every entity's triples into a fresh engine (the build pipeline in miniature)."""
    engine = RdflibIndexer()
    for entity in entities:
        for triple in entity.to_triples():
            engine.add_triple(*triple)
    return engine


# --- Q1: resolve a unit by name (FR-007) ------------------------------------


def test_find_unit_by_label_returns_its_uri() -> None:
    """Q1: a SPARQL match on ``rdfs:label`` resolves the unit's URI (SC-001)."""
    unit = NarrativeUnit(uri_base=B, name="La traición del senescal")
    other = NarrativeUnit(uri_base=B, name="El cuchillo")
    engine = _build(unit, other)
    rows = list(
        engine.query(f'SELECT ?u WHERE {{ ?u a <{_G9}> ; <{_LABEL}> "La traición del senescal" }}')
    )
    assert [r["u"] for r in rows] == [str(unit.uri)]


def test_find_unit_by_absent_name_returns_no_rows() -> None:
    """Q1: a name present in no fiche returns the empty result."""
    engine = _build(NarrativeUnit(uri_base=B, name="La traición del senescal"))
    rows = list(
        engine.query(
            f'SELECT ?u WHERE {{ ?u a <{_G9}> ; <{_LABEL}> "Ningún beat con este nombre" }}'
        )
    )
    assert rows == []


# --- Q2: list a sequence's units in declared order (FR-008) -----------------


def _ordered(engine: RdflibIndexer, seq_uri: URIRef) -> list[str]:
    """The member URIs of ``seq_uri`` sorted by their materialized ordinal (Q2)."""
    rows = list(
        engine.query(
            f"SELECT ?u ?n WHERE {{ <{seq_uri}> <{_PROPER_PART}> ?u . "
            f"?u <{_ORDINAL}> ?n }} ORDER BY ?n"
        )
    )
    return [r["u"] for r in rows]


def test_list_sequence_in_declared_order() -> None:
    """Q2: ``ORDER BY`` the ordinal yields the declared order; a second sequence
    returns only its own members in its own order (C3/C4/SC-002)."""
    a = NarrativeUnit(uri_base=B, name="Beat A")
    b = NarrativeUnit(uri_base=B, name="Beat B")
    c = NarrativeUnit(uri_base=B, name="Beat C")
    quest = NarrativeSequence(uri_base=B, name="Quest", units=(a, b, c))
    # A second sequence whose tuple order differs, to prove the query isolates one line.
    x = NarrativeUnit(uri_base=B, name="Beat X")
    y = NarrativeUnit(uri_base=B, name="Beat Y")
    coda = NarrativeSequence(uri_base=B, name="Coda", units=(y, x))
    engine = _build(a, b, c, x, y, quest, coda)

    assert _ordered(engine, quest.uri) == [str(a.uri), str(b.uri), str(c.uri)]
    assert _ordered(engine, coda.uri) == [str(y.uri), str(x.uri)]
