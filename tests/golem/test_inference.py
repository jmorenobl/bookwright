"""AttributeAssignment: verbatim source, optional premise, uuid7 ordering.

FR-009/013, SC-006.
"""

from __future__ import annotations

import re

from pydantic import ValidationError
from rdflib.namespace import XSD
from rdflib.term import Literal

from bookwright.golem import AttributeAssignment, Character
from bookwright.golem import namespaces as ns
from tests.golem.conftest import B

_UUID7 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def _target() -> Character:
    return Character(uri_base=B, name="Aparici")


def _attribute() -> Character:
    return Character(uri_base=B, name="Peña")


def test_source_preserved_verbatim_with_line_locator() -> None:
    note = AttributeAssignment(
        uri_base=B, target=_target(), attribute=_attribute(), source="manuscript/cap-04.md:42"
    )
    triples = list(note.to_triples())
    source_objs = [o for _, p, o in triples if p == ns.USED_SPECIFIC_OBJECT]
    assert source_objs == [Literal("manuscript/cap-04.md:42", datatype=XSD.string)]


def test_target_and_attribute_triples_present() -> None:
    target, attribute = _target(), _attribute()
    note = AttributeAssignment(
        uri_base=B, target=target, attribute=attribute, source="bible/characters/aparici.md"
    )
    triples = set(note.to_triples())
    assert (note.uri, ns.ASSIGNED_ATTRIBUTE_TO, target.uri) in triples
    assert (note.uri, ns.ASSIGNED, attribute.uri) in triples


def test_premise_omitted_when_none() -> None:
    note = AttributeAssignment(
        uri_base=B, target=_target(), attribute=_attribute(), source="bible/x.md", premise=None
    )
    assert ns.REFERS_TO not in {p for _, p, _ in note.to_triples()}


def test_premise_linked_when_present() -> None:
    first = AttributeAssignment(
        uri_base=B, target=_target(), attribute=_attribute(), source="bible/x.md"
    )
    second = AttributeAssignment(
        uri_base=B, target=_target(), attribute=_attribute(), source="bible/y.md", premise=first
    )
    assert (second.uri, ns.REFERS_TO, first.uri) in set(second.to_triples())


def test_assertion_token_is_uuid7() -> None:
    note = AttributeAssignment(
        uri_base=B, target=_target(), attribute=_attribute(), source="bible/x.md"
    )
    assert str(note.uri).startswith(f"{B}assertion/")
    token = str(note.uri).rsplit("/", 1)[-1]
    assert _UUID7.match(token)


def test_sequential_assignments_are_distinct_and_creation_ordered() -> None:
    notes = [
        AttributeAssignment(
            uri_base=B, target=_target(), attribute=_attribute(), source=f"bible/{i}.md"
        )
        for i in range(5)
    ]
    uris = [str(n.uri) for n in notes]
    assert len(set(uris)) == len(uris)  # distinct
    assert uris == sorted(uris)  # uuid7 sorts in creation order


def test_assignment_is_frozen() -> None:
    note = AttributeAssignment(
        uri_base=B, target=_target(), attribute=_attribute(), source="bible/x.md"
    )
    original = note.uri
    try:
        note.source = "other"
    except ValidationError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("AttributeAssignment must be frozen")
    assert note.uri == original
