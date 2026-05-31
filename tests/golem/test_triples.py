"""Triple emission: rdf:type, cross-references, term closure.

FR-008/015, SC-003.
"""

from __future__ import annotations

from rdflib.namespace import RDF
from rdflib.term import Literal, URIRef

from bookwright.golem import (
    AttributeAssignment,
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
from bookwright.golem import namespaces as ns
from bookwright.golem.base import GolemEntity
from tests.golem.conftest import B


def _sample_entities() -> list[GolemEntity]:
    aparici = Character(uri_base=B, name="Aparici")
    pena = Character(uri_base=B, name="Peña")
    obj = Object(uri_base=B, name="El cuchillo")
    setting = Setting(uri_base=B, name="El pueblo")
    location = NarrativeLocation(uri_base=B, name="El faro", setting=setting)
    rel = SocialRelationship(uri_base=B, name="Aparici y Peña", participants=(aparici, pena))
    role = RelationshipRole(uri_base=B, name="Rival", relationship=rel)
    event = NarrativeEvent(uri_base=B, name="La caída", participants=(aparici, obj))
    state = PsychologicalState(uri_base=B, name="Miedo", bearer=aparici)
    func = NarrativeFunction(uri_base=B, name="Villanía")
    nrole = NarrativeRole(uri_base=B, name="Héroe")
    unit = NarrativeUnit(uri_base=B, name="Apertura", functions=(func,), roles=(nrole,))
    seq = NarrativeSequence(uri_base=B, name="Acto I", units=(unit,))
    note = AttributeAssignment(uri_base=B, target=aparici, attribute=func, source="bible/x.md:1")
    # +US5: an attributed Character drags G17/E54/E55/GP0_has_feature/edns:plays/
    # P2_has_type/P43_has_dimension/P90_has_value/rdfs:label into the closure loop.
    attributed = Character(
        uri_base=B,
        name="Don Atributo",
        born=1828,
        died=1900,
        features=("ingeniero químico",),
        narrative_roles=("protagonist",),
    )
    return [
        attributed,
        aparici,
        pena,
        obj,
        setting,
        location,
        rel,
        role,
        event,
        state,
        func,
        nrole,
        unit,
        seq,
        note,
    ]


def test_every_entity_emits_its_rdf_type() -> None:
    for entity in _sample_entities():
        triples = list(entity.to_triples())
        type_triple = (entity.uri, RDF.type, entity.golem_class)
        assert type_triple in triples
        # The type assertion is always emitted first.
        assert triples[0] == type_triple


def test_cross_reference_triples_link_by_uri() -> None:
    aparici = Character(uri_base=B, name="Aparici")
    pena = Character(uri_base=B, name="Peña")
    rel = SocialRelationship(uri_base=B, name="Aparici y Peña", participants=(aparici, pena))
    triples = set(rel.to_triples())
    assert (rel.uri, ns.PARTICIPANT, aparici.uri) in triples
    assert (rel.uri, ns.PARTICIPANT, pena.uri) in triples

    setting = Setting(uri_base=B, name="El pueblo")
    location = NarrativeLocation(uri_base=B, name="El faro", setting=setting)
    assert (location.uri, ns.GENERIC_LOCATION, setting.uri) in set(location.to_triples())

    state = PsychologicalState(uri_base=B, name="Miedo", bearer=aparici)
    assert (state.uri, ns.GENERICALLY_DEPENDENT_ON, aparici.uri) in set(state.to_triples())

    unit = NarrativeUnit(uri_base=B, name="U")
    seq = NarrativeSequence(uri_base=B, name="S", units=(unit,))
    assert (seq.uri, ns.PROPER_PART, unit.uri) in set(seq.to_triples())


def test_cross_reference_accepts_bare_uriref() -> None:
    external = URIRef("https://example.org/other/character/foo")
    rel = SocialRelationship(uri_base=B, name="R", participants=(external,))
    assert (rel.uri, ns.PARTICIPANT, external) in set(rel.to_triples())


def test_optional_reference_omitted_when_none() -> None:
    role = RelationshipRole(uri_base=B, name="Rival")
    assert ns.REFERS_TO not in {p for _, p, _ in role.to_triples()}

    state = PsychologicalState(uri_base=B, name="Miedo")
    assert ns.GENERICALLY_DEPENDENT_ON not in {p for _, p, _ in state.to_triples()}

    location = NarrativeLocation(uri_base=B, name="El faro")
    assert ns.GENERIC_LOCATION not in {p for _, p, _ in location.to_triples()}


def test_term_closure_over_frozen_ontology() -> None:
    frozen = ns.frozen_terms()
    for entity in _sample_entities():
        for subject, predicate, obj in entity.to_triples():
            assert predicate == RDF.type or predicate in frozen, f"predicate {predicate} not frozen"
            if predicate == RDF.type:
                assert obj in frozen, f"class {obj} not frozen"
            # Literals (verbatim source paths) are exempt from class closure.
            assert isinstance(obj, URIRef | Literal)
            assert isinstance(subject, URIRef)
