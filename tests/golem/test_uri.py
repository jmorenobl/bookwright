"""URI / identity: per-concept segments, determinism, immutability.

FR-003/004/007, US1 worked examples, SC-002.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from rdflib.term import URIRef

from bookwright.golem import (
    Character,
    NarrativeEvent,
    NarrativeFunction,
    NarrativeLocation,
    NarrativeRole,
    NarrativeSequence,
    NarrativeUnit,
    Object,
    PsychologicalState,
    RelationshipRole,
    Setting,
    SocialRelationship,
)
from tests.golem.conftest import B

# (class, expected FR-004 segment) for all 12 slugged concepts.
SEGMENTS = [
    (Character, "character"),
    (Object, "object"),
    (SocialRelationship, "relationship"),
    (RelationshipRole, "relationship-role"),
    (NarrativeEvent, "event"),
    (PsychologicalState, "psychological-state"),
    (Setting, "setting"),
    (NarrativeLocation, "location"),
    (NarrativeUnit, "narrative-unit"),
    (NarrativeFunction, "narrative-function"),
    (NarrativeRole, "narrative-role"),
    (NarrativeSequence, "narrative-sequence"),
]


@pytest.mark.parametrize(("cls", "segment"), SEGMENTS)
def test_segment_table(cls: type, segment: str) -> None:
    entity = cls(uri_base=B, name="Some Name")
    assert entity.uri == URIRef(f"{B}{segment}/some-name")
    assert isinstance(entity.uri, URIRef)


@pytest.mark.parametrize(
    ("cls", "name", "expected"),
    [
        (Character, "Aparici", f"{B}character/aparici"),
        (NarrativeEvent, "La caída del puente", f"{B}event/la-caida-del-puente"),
        (NarrativeLocation, "El faro", f"{B}location/el-faro"),
    ],
)
def test_us1_worked_examples(cls: type, name: str, expected: str) -> None:
    assert cls(uri_base=B, name=name).uri == URIRef(expected)


def test_byte_identical_reconstruction() -> None:
    first = Character(uri_base=B, name="José Peña")
    second = Character(uri_base=B, name="José Peña")
    assert str(first.uri) == str(second.uri)
    assert first.uri == second.uri


def test_frozen_name_reassignment_rejected() -> None:
    aparici = Character(uri_base=B, name="Aparici")
    original = aparici.uri
    with pytest.raises(ValidationError):
        aparici.name = "Otro"
    assert aparici.uri == original


def test_slug_exposed_on_named_entity() -> None:
    assert Character(uri_base=B, name="José Peña").slug == "jose-pena"


# --- +US5: nested character-scoped attribute-node URIs (FR-021, SC-007) ------


def test_character_scoped_node_uri_patterns() -> None:
    c = Character(
        uri_base=B,
        name="Aparici",
        born=1828,
        died=1900,
        features=("ingeniero químico",),
        narrative_roles=("protagonist",),
    )
    subjects = {s for s, _, _ in c.to_triples()}
    assert URIRef(f"{c.uri}/feature/birth") in subjects
    assert URIRef(f"{c.uri}/feature/death") in subjects
    assert URIRef(f"{c.uri}/feature/ingeniero-quimico") in subjects
    assert URIRef(f"{c.uri}/feature/birth/dimension") in subjects
    assert URIRef(f"{c.uri}/role/protagonist") in subjects


def test_birth_death_type_individuals_are_project_scoped_and_shared() -> None:
    """FR-019: the birth/death E55_Type individuals carry stable project-scoped
    URIs ({uri_base}type/birth|death) and are shared (deduped) across characters."""
    aparici = Character(uri_base=B, name="Aparici", born=1828)
    pena = Character(uri_base=B, name="Peña", born=1830)
    birth_type = URIRef(f"{B}type/birth")
    assert birth_type in {o for _, _, o in aparici.to_triples()}
    assert birth_type in {o for _, _, o in pena.to_triples()}
    # The type individual is NOT character-scoped (no character segment).
    assert "character" not in str(birth_type)


def test_attributed_character_uris_are_immutable() -> None:
    c = Character(uri_base=B, name="Aparici", born=1828, features=("barba",))
    original = {s for s, _, _ in c.to_triples()}
    with pytest.raises(ValidationError):
        c.born = 1900
    assert {s for s, _, _ in c.to_triples()} == original
