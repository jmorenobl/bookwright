"""Unit tests for query error/empty behaviour on the engine (FR-016, R8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from rdflib.term import URIRef

from bookwright.indexers import GraphLoadError, InvalidQueryError, RdflibIndexer

CHARACTER = URIRef("https://w3id.org/golem/ontology#G1_Character")
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")


def test_malformed_sparql_raises_invalid_query() -> None:
    engine = RdflibIndexer()
    with pytest.raises(InvalidQueryError):
        engine.query("SELECT ?c WHERE { this is not sparql")


def test_malformed_sparql_yields_no_partial_rows() -> None:
    engine = RdflibIndexer()
    engine.add_triple(URIRef("https://example.org/c"), RDF_TYPE, CHARACTER)
    try:
        engine.query("SELECT ?c WHERE {{{")
    except InvalidQueryError:
        pass
    else:  # pragma: no cover - the query above is malformed
        pytest.fail("expected InvalidQueryError")


def test_zero_match_query_returns_empty_iterable() -> None:
    engine = RdflibIndexer()
    rows = list(engine.query(f"SELECT ?c WHERE {{ ?c a <{CHARACTER}> }}"))
    assert rows == []


def test_load_malformed_turtle_raises_graph_load_error(tmp_path: Path) -> None:
    bad = tmp_path / "graph.ttl"
    bad.write_text("this is not @@@ valid turtle", encoding="utf-8")
    engine = RdflibIndexer()
    with pytest.raises(GraphLoadError) as excinfo:
        engine.load(bad)
    assert excinfo.value.to_json()["code"] == "graph_load_failed"
