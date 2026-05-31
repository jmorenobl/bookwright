"""Turtle serialization round-trips isomorphically with short prefixes.

FR-012, SC-004.
"""

from __future__ import annotations

from rdflib import Graph
from rdflib.compare import isomorphic

from bookwright.golem import (
    AttributeAssignment,
    Character,
    NarrativeLocation,
    Setting,
    SocialRelationship,
    to_turtle,
)
from bookwright.golem.base import GolemEntity
from tests.golem.conftest import B


def _populated_graph_entities() -> list[GolemEntity]:
    aparici = Character(uri_base=B, name="Aparici")
    pena = Character(uri_base=B, name="José Peña")
    setting = Setting(uri_base=B, name="El pueblo")
    location = NarrativeLocation(uri_base=B, name="El faro", setting=setting)
    rel = SocialRelationship(uri_base=B, name="Aparici y Peña", participants=(aparici, pena))
    note = AttributeAssignment(
        uri_base=B, target=aparici, attribute=pena, source="manuscript/cap-04.md:42"
    )
    attributed = Character(
        uri_base=B,
        name="Don Atributo",
        born=1828,
        died=1900,
        features=("ingeniero químico",),
        narrative_roles=("protagonist",),
    )
    return [aparici, pena, setting, location, rel, note, attributed]


def test_roundtrip_is_isomorphic() -> None:
    entities = _populated_graph_entities()
    ttl = to_turtle(entities)

    parsed = Graph()
    parsed.parse(data=ttl, format="turtle")

    source = Graph()
    for entity in entities:
        for triple in entity.to_triples():
            source.add(triple)

    assert isomorphic(parsed, source)


def test_output_uses_short_prefixes_not_expanded_iris() -> None:
    ttl = to_turtle(_populated_graph_entities())
    assert "@prefix golem:" in ttl
    assert "@prefix crm:" in ttl
    assert "@prefix dlp:" in ttl
    assert "a golem:G1_Character" in ttl
    assert "dlp:participant" in ttl
    # The GOLEM class IRI must not appear expanded as a full <...> term.
    assert "<https://w3id.org/golem/ontology#G1_Character>" not in ttl


def test_parses_without_malformed_triples() -> None:
    ttl = to_turtle(_populated_graph_entities())
    parsed = Graph()
    parsed.parse(data=ttl, format="turtle")
    assert len(parsed) > 0


def test_verbatim_source_literal_preserved() -> None:
    note = AttributeAssignment(
        uri_base=B,
        target=Character(uri_base=B, name="Aparici"),
        attribute=Character(uri_base=B, name="Peña"),
        source="manuscript/cap-04.md:42",
    )
    ttl = to_turtle([note])
    parsed = Graph()
    parsed.parse(data=ttl, format="turtle")
    literals = [str(o) for o in parsed.objects() if str(o) == "manuscript/cap-04.md:42"]
    assert literals == ["manuscript/cap-04.md:42"]
