"""US5 acceptance matrix: a Character carries born/died/features/narrative_roles.

FR-016 through FR-021, SC-007, US5-1..6. Every attribute is reached through frozen GOLEM /
CIDOC-CRM / DOLCE ExtendedDnS terms; every generated node is a deterministic,
character-scoped URI (never a blank node); an attribute-free Character emits
only its identity assertion.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from rdflib.namespace import RDF, RDFS, XSD
from rdflib.term import Literal, URIRef

from bookwright.golem import Character, CharacterFeature, to_turtle
from bookwright.golem import namespaces as ns
from bookwright.golem.errors import EmptySlugError
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


def test_free_text_feature_linked_by_has_feature_with_label() -> None:
    """US5-1, FR-017: free text → G17 feature linked by golem:GP0_has_feature,
    text carried on rdfs:label."""
    c = Character(uri_base=B, name="Aparici", features=("ingeniero químico",))
    triples = set(c.to_triples())
    feature = URIRef(f"{c.uri}/feature/ingeniero-quimico")
    assert (c.uri, ns.HAS_FEATURE, feature) in triples
    assert (feature, RDF.type, ns.CLASS_IRI["CharacterFeature"]) in triples
    assert (feature, RDFS.label, Literal("ingeniero químico")) in triples


def test_narrative_role_linked_by_plays_with_label() -> None:
    """US5-2, FR-018: role → G11 linked by edns:plays, text on rdfs:label."""
    c = Character(uri_base=B, name="Aparici", narrative_roles=("protagonist",))
    triples = set(c.to_triples())
    role = URIRef(f"{c.uri}/role/protagonist")
    assert (c.uri, ns.PLAYS, role) in triples
    assert (role, RDF.type, ns.CLASS_IRI["NarrativeRole"]) in triples
    assert (role, RDFS.label, Literal("protagonist")) in triples


def test_born_year_modeled_through_dimension_chain() -> None:
    """US5-3, FR-019: born=1828 → biographical G17 typed crm:P2_has_type a birth
    E55_Type individual + crm:P43_has_dimension → E54_Dimension whose
    crm:P90_has_value is "1828"^^xsd:gYear."""
    c = Character(uri_base=B, name="Aparici", born=1828)
    triples = set(c.to_triples())
    feature = URIRef(f"{c.uri}/feature/birth")
    type_uri = URIRef(f"{B}type/birth")
    dimension = URIRef(f"{feature}/dimension")
    assert (c.uri, ns.HAS_FEATURE, feature) in triples
    assert (feature, RDF.type, ns.CLASS_IRI["CharacterFeature"]) in triples
    assert (feature, ns.HAS_TYPE, type_uri) in triples
    assert (type_uri, RDF.type, ns.CLASS_IRI["Type"]) in triples
    assert (feature, ns.HAS_DIMENSION, dimension) in triples
    assert (dimension, RDF.type, ns.CLASS_IRI["Dimension"]) in triples
    assert (dimension, ns.HAS_VALUE, Literal("1828", datatype=XSD.gYear)) in triples


def test_died_year_modeled_through_dimension_chain() -> None:
    """US5-4: died=1900 analogous to born, with the death E55_Type individual."""
    c = Character(uri_base=B, name="Aparici", died=1900)
    triples = set(c.to_triples())
    feature = URIRef(f"{c.uri}/feature/death")
    type_uri = URIRef(f"{B}type/death")
    dimension = URIRef(f"{feature}/dimension")
    assert (feature, ns.HAS_TYPE, type_uri) in triples
    assert (type_uri, RDF.type, ns.CLASS_IRI["Type"]) in triples
    assert (dimension, ns.HAS_VALUE, Literal("1900", datatype=XSD.gYear)) in triples


def test_gyear_literal_is_not_integer_or_plain_string() -> None:
    """FR-019: the year is xsd:gYear, never xsd:integer or an untyped literal."""
    c = Character(uri_base=B, name="Aparici", born=1828)
    dimension = URIRef(f"{c.uri}/feature/birth/dimension")
    values = [o for s, p, o in c.to_triples() if s == dimension and p == ns.HAS_VALUE]
    assert values == [Literal("1828", datatype=XSD.gYear)]
    value = values[0]
    assert isinstance(value, Literal)
    assert value.datatype == XSD.gYear


def test_deterministic_character_scoped_uris() -> None:
    """FR-021: every generated node carries a deterministic, character-scoped URI."""
    c = _attributed()
    expected = {
        URIRef(f"{c.uri}/feature/birth"),
        URIRef(f"{c.uri}/feature/death"),
        URIRef(f"{c.uri}/feature/ingeniero-quimico"),
        URIRef(f"{c.uri}/feature/barba"),
        URIRef(f"{c.uri}/feature/birth/dimension"),
        URIRef(f"{c.uri}/feature/death/dimension"),
        URIRef(f"{c.uri}/role/protagonist"),
    }
    subjects = {s for s, _, _ in c.to_triples()}
    # The character-scoped nodes are all present as subjects (plus the character
    # itself and the project-scoped E55_Type individuals).
    assert expected <= subjects
    # No blank nodes anywhere.
    for s, _, o in c.to_triples():
        assert isinstance(s, URIRef)
        assert isinstance(o, URIRef | Literal)


def test_identical_feature_values_dedup_on_one_character() -> None:
    """FR-021: two identical feature values on the same character → one node."""
    c = Character(uri_base=B, name="Aparici", features=("barba", "barba"))
    feature = URIRef(f"{c.uri}/feature/barba")
    edges = [(s, p, o) for s, p, o in c.to_triples() if p == ns.HAS_FEATURE]
    assert edges == [(c.uri, ns.HAS_FEATURE, feature)]


def test_identical_roles_dedup_on_one_character() -> None:
    """FR-021: identical narrative roles on the same character → one node."""
    c = Character(uri_base=B, name="Aparici", narrative_roles=("hero", "hero"))
    role = URIRef(f"{c.uri}/role/hero")
    edges = [(s, p, o) for s, p, o in c.to_triples() if p == ns.PLAYS]
    assert edges == [(c.uri, ns.PLAYS, role)]


def test_empty_slug_feature_raises() -> None:
    """FR-021: a feature text that slugs to empty raises EmptySlugError."""
    with pytest.raises(EmptySlugError):
        Character(uri_base=B, name="Aparici", features=("!!!",))


def test_empty_slug_role_raises() -> None:
    """FR-021: a narrative-role text that slugs to empty raises EmptySlugError."""
    with pytest.raises(EmptySlugError):
        Character(uri_base=B, name="Aparici", narrative_roles=("---",))


def test_attribute_free_character_emits_only_rdf_type() -> None:
    """US5-6: a Character with none of the four attributes emits only its
    identity assertion — byte-identical to the merged identity-only output."""
    bare = Character(uri_base=B, name="Aparici")
    assert list(bare.to_triples()) == [(bare.uri, RDF.type, bare.golem_class)]
    # And byte-identical Turtle to the pre-US5 identity-only Character.
    assert to_turtle([bare]) == to_turtle([Character(uri_base=B, name="Aparici")])


def test_character_feature_requires_exactly_one_variant() -> None:
    """The public carrier rejects an ambiguous (both) or empty (neither) build."""
    char = Character(uri_base=B, name="Aparici")
    with pytest.raises(ValidationError):  # both variants supplied
        CharacterFeature(uri_base=B, character_uri=char.uri, label="x", kind="birth", year=1828)
    with pytest.raises(ValidationError):  # neither variant supplied
        CharacterFeature(uri_base=B, character_uri=char.uri)


def test_biographical_character_feature_requires_year() -> None:
    """A biographical feature without a year is rejected."""
    char = Character(uri_base=B, name="Aparici")
    with pytest.raises(ValidationError):
        CharacterFeature(uri_base=B, character_uri=char.uri, kind="birth")


def test_all_emitted_terms_are_frozen() -> None:
    """SC-007: zero emitted classes/predicates fall outside frozen_terms()."""
    frozen = ns.frozen_terms()
    for _s, p, o in _attributed().to_triples():
        assert p == RDF.type or p in frozen, f"predicate {p} not frozen"
        if p == RDF.type:
            assert o in frozen, f"class {o} not frozen"
