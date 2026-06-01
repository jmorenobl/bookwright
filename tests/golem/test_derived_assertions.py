"""Provenance enumeration: ``GolemEntity.derived_assertions`` (FR-011, SC-006).

The source-agnostic seam the iteration-6 indexer consumes: every entity yields
one :class:`~bookwright.golem.base.DerivedAssertion` per derived assertion — the
identity assertion plus each feature, role, and participation — tagged with the
frontmatter field it came from (never a file path). The indexer resolves that
field to a ``file:line`` locator and mints the ``crm:E13`` assignments.
"""

from __future__ import annotations

from rdflib.term import URIRef

from bookwright.golem import Character, DerivedAssertion, NarrativeEvent, SocialRelationship
from bookwright.golem import namespaces as ns
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
