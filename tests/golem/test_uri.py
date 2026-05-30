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
