"""Provenance enumeration: ``GolemEntity.derived_assertions`` (FR-011, SC-006).

The source-agnostic seam the iteration-6 indexer consumes: every entity yields
one :class:`~bookwright.golem.base.DerivedAssertion` per derived assertion — the
identity assertion plus each feature, role, and participation — tagged with the
frontmatter field it came from (never a file path). The indexer resolves that
field to a ``file:line`` locator and mints the ``crm:E13`` assignments.
"""

from __future__ import annotations

from rdflib.term import URIRef

from bookwright.golem import (
    Character,
    DerivedAssertion,
    NarrativeEvent,
    NarrativeFunction,
    NarrativeSequence,
    NarrativeUnit,
    SocialRelationship,
)
from bookwright.golem import namespaces as ns
from bookwright.io._bible_builders import MappedEntity
from bookwright.io.bible import build_provenance
from tests.golem.conftest import B


def _attributed() -> Character:
    return Character(
        uri_base=B,
        name="Aparici",
        born=1828,
        died=1900,
        features=("ingeniero químico", "barba"),
        narrative_roles=("protagonist",),
    )


def test_identity_assertion_is_first_and_file_level() -> None:
    """FR-011: the identity assertion comes first and carries file-level
    provenance — target == attribute == the entity, source_field None."""
    c = Character(uri_base=B, name="Aparici")
    assertions = list(c.derived_assertions())
    assert assertions[0] == DerivedAssertion(c.uri, c.uri, None)


def test_attribute_free_character_emits_only_identity() -> None:
    """A bare Character makes exactly one derived assertion: its identity."""
    c = Character(uri_base=B, name="Aparici")
    assert list(c.derived_assertions()) == [DerivedAssertion(c.uri, c.uri, None)]


def test_born_and_died_tagged_with_their_frontmatter_keys() -> None:
    """FR-011/SC-006: each biographical feature is tagged ``born`` / ``died`` so
    the indexer resolves the locator to the originating frontmatter line."""
    c = Character(uri_base=B, name="Aparici", born=1828, died=1900)
    by_attr = {a.attribute: a.source_field for a in c.derived_assertions()}
    assert by_attr[URIRef(f"{c.uri}/feature/bio/birth")] == "born"
    assert by_attr[URIRef(f"{c.uri}/feature/bio/death")] == "died"


def test_free_text_features_tagged_features() -> None:
    """Free-text features all trace back to the single ``features`` key."""
    c = Character(uri_base=B, name="Aparici", features=("barba", "alto"))
    fields = {a.source_field for a in c.derived_assertions() if a.attribute != c.uri}
    assert fields == {"features"}


def test_roles_tagged_narrative_roles() -> None:
    """Roles trace back to the ``narrative_roles`` key."""
    c = Character(uri_base=B, name="Aparici", narrative_roles=("protagonist",))
    role = [a for a in c.derived_assertions() if a.attribute != c.uri]
    expected = URIRef(f"{c.uri}/role/protagonist")
    assert role == [DerivedAssertion(c.uri, expected, "narrative_roles")]


def test_one_assertion_per_materialized_feature_and_role() -> None:
    """SC-006: every materialized feature/role node has exactly one assertion —
    the attribute set of derived_assertions() equals the HAS_FEATURE/PLAYS edge
    targets of to_triples(), so no derived node is left without provenance."""
    c = _attributed()
    edge_targets = {o for s, p, o in c.to_triples() if p in (ns.HAS_FEATURE, ns.PLAYS)}
    assertion_targets = {a.attribute for a in c.derived_assertions() if a.attribute != c.uri}
    assert assertion_targets == edge_targets


def test_event_participants_via_declarative_default() -> None:
    """NarrativeEvent needs no override: its ``participants`` field name already
    equals its frontmatter key, so the base default tags each participation."""
    hero = Character(uri_base=B, name="Aparici")
    villain = Character(uri_base=B, name="Peña")
    event = NarrativeEvent(uri_base=B, name="the duel", participants=(hero, villain))
    assert list(event.derived_assertions()) == [
        DerivedAssertion(event.uri, event.uri, None),
        DerivedAssertion(event.uri, hero.uri, "participants"),
        DerivedAssertion(event.uri, villain.uri, "participants"),
    ]


def test_relationship_participants_via_declarative_default() -> None:
    """SocialRelationship participations are tagged identically by the default."""
    a = Character(uri_base=B, name="Aparici")
    b = Character(uri_base=B, name="Peña")
    rel = SocialRelationship(uri_base=B, name="rivalry", participants=(a, b))
    fields = {x.source_field for x in rel.derived_assertions() if x.attribute != rel.uri}
    assert fields == {"participants"}


def test_participantless_event_emits_only_identity() -> None:
    """An event with no participants makes only its identity assertion."""
    event = NarrativeEvent(uri_base=B, name="the storm")
    assert list(event.derived_assertions()) == [DerivedAssertion(event.uri, event.uri, None)]


# --- iteration 030: vocabulary typing yields a provenanced assertion ---------


def test_typed_function_yields_extra_assertion_tagged_functions() -> None:
    """A typed ``NarrativeFunction`` yields its identity assertion plus a type
    assertion (function → term) tagged ``functions`` so the indexer reifies it."""
    term = URIRef("https://bookwright.dev/vocab/propp#function/departure")
    func = NarrativeFunction(uri_base=B, name="Departure", type_uri=term)
    assert list(func.derived_assertions()) == [
        DerivedAssertion(func.uri, func.uri, None),
        DerivedAssertion(func.uri, term, "functions"),
    ]


def test_untyped_function_yields_only_identity() -> None:
    """An untyped function makes exactly its identity assertion (no type E13)."""
    func = NarrativeFunction(uri_base=B, name="Departure")
    assert list(func.derived_assertions()) == [DerivedAssertion(func.uri, func.uri, None)]


def test_sequence_member_ordinal_reified_as_own_file_level_e13() -> None:
    """C5/D6: each member ordinal is its own assertion (target=unit, attribute=sequence,
    tagged ``order``), distinct from the proper-part membership E13, reified with
    file-level provenance (``key_lines={}`` → no ``:line``)."""
    a = NarrativeUnit(uri_base=B, name="Beat A")
    b = NarrativeUnit(uri_base=B, name="Beat B")
    seq = NarrativeSequence(uri_base=B, name="Quest", units=(a, b))

    assertions = list(seq.derived_assertions())
    # The base still yields identity + one proper-part membership per member …
    assert DerivedAssertion(seq.uri, seq.uri, None) in assertions
    assert DerivedAssertion(seq.uri, a.uri, "units") in assertions
    # … and the override adds one ordinal assertion per member: unit → sequence.
    assert DerivedAssertion(a.uri, seq.uri, "order") in assertions
    assert DerivedAssertion(b.uri, seq.uri, "order") in assertions

    # Reified through the standard provenance path with file-level provenance.
    mapped = MappedEntity(entity=seq, relpath="outline/units/a.md", key_lines={})
    ordinal_e13 = [
        e for e in build_provenance(mapped, B) if e.attribute == seq.uri and e.target != seq.uri
    ]
    assert {e.target for e in ordinal_e13} == {a.uri, b.uri}
    assert all(e.source == "outline/units/a.md" for e in ordinal_e13)  # file-level, no :line


def test_typed_role_assertion_emitted_by_owning_character() -> None:
    """A typed role's type E13 is owned by the Character: the role node → its term,
    tagged ``narrative_roles`` so the locator resolves to that card line (D4)."""
    term = URIRef("https://bookwright.dev/vocab/greimas#actant/subject")
    char = Character(
        uri_base=B, name="Ada", narrative_roles=("sujeto",), role_types={"sujeto": term}
    )
    (role,) = char.role_nodes
    assert DerivedAssertion(role.uri, term, "narrative_roles") in list(char.derived_assertions())
