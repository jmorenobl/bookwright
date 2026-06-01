"""Unit tests for :class:`RdflibIndexer` (contracts/indexer.md invariants)."""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph
from rdflib.term import Literal, URIRef

from bookwright.indexers import RdflibIndexer

B = "https://example.org/my-book/"
CHARACTER = URIRef("https://w3id.org/golem/ontology#G1_Character")
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")


def test_empty_on_construction() -> None:
    assert RdflibIndexer().count() == 0


def test_add_triple_and_count() -> None:
    engine = RdflibIndexer()
    engine.add_triple(URIRef(f"{B}character/aparici"), RDF_TYPE, CHARACTER)
    assert engine.count() == 1


def test_add_triple_coerces_iri_strings() -> None:
    engine = RdflibIndexer()
    engine.add_triple(f"{B}character/aparici", str(RDF_TYPE), CHARACTER)
    rows = list(engine.query(f"SELECT ?s WHERE {{ ?s a <{CHARACTER}> }}"))
    assert rows == [{"s": f"{B}character/aparici"}]


def test_add_triple_scalar_object_becomes_literal() -> None:
    engine = RdflibIndexer()
    engine.add_triple(f"{B}c", "https://example.org/p", 1828)
    triples = list(engine._graph)
    assert triples[0][2] == Literal(1828)


def test_save_load_roundtrip_isomorphic(tmp_path: Path) -> None:
    engine = RdflibIndexer()
    engine.add_triple(URIRef(f"{B}character/aparici"), RDF_TYPE, CHARACTER)
    out = tmp_path / "nested" / "graph.ttl"
    engine.save(out)
    assert out.exists()  # parent dirs created

    reloaded = RdflibIndexer()
    reloaded.load(out)
    assert reloaded.count() == engine.count()

    a, b = Graph(), Graph()
    a.parse(str(out), format="turtle")
    b.add((URIRef(f"{B}character/aparici"), RDF_TYPE, CHARACTER))
    assert a.isomorphic(b)


def test_saved_turtle_uses_short_prefixes(tmp_path: Path) -> None:
    engine = RdflibIndexer()
    engine.add_triple(URIRef(f"{B}character/aparici"), RDF_TYPE, CHARACTER)
    out = tmp_path / "graph.ttl"
    engine.save(out)
    text = out.read_text(encoding="utf-8")
    assert "@prefix golem:" in text
    assert "golem:G1_Character" in text


def test_construct_returns_populated_engine() -> None:
    engine = RdflibIndexer()
    engine.add_triple(URIRef(f"{B}character/aparici"), RDF_TYPE, CHARACTER)
    sub = engine.construct(f"CONSTRUCT {{ ?s a <{CHARACTER}> }} WHERE {{ ?s a <{CHARACTER}> }}")
    assert isinstance(sub, RdflibIndexer)
    assert sub.count() == 1
