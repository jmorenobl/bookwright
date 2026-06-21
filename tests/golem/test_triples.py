"""Triple emission: rdf:type, cross-references, term closure.

FR-008/015, SC-003.
"""

from __future__ import annotations

from rdflib.namespace import RDF, RDFS, XSD
from rdflib.term import Literal, URIRef

from bookwright.golem import (
    AttributeAssignment,
    Character,
    NarrativeEvent,
    NarrativeFunction,
    NarrativeLocation,
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
from bookwright.golem.modules.feature import CharacterRole
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
    # G11 is materialized solely by the character-scoped ``CharacterRole`` carrier
    # (there is no top-level role concept); the unit's role cross-ref links to that
    # node by bare URI.
    crole = CharacterRole(uri_base=B, character_uri=aparici.uri, label="Héroe")
    unit = NarrativeUnit(uri_base=B, name="Apertura", functions=(func,), roles=(crole.uri,))
    seq = NarrativeSequence(uri_base=B, name="Acto I", units=(unit,))
    note = AttributeAssignment(uri_base=B, target=aparici, attribute=func, source="bible/x.md:1")
    # An attributed Character drags G17/E54/E55/GP0_has_feature/edns:plays/
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
        crole,
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


def test_narrative_event_interval_and_relation_triples() -> None:
    """A NarrativeEvent with begin/end + a follows ref emits the typed-boundary
    interval (gYear via a Dimension) and the frozen ``TR:follows`` edge (D11)."""
    other = URIRef(f"{B}event/otro")
    event = NarrativeEvent(uri_base=B, name="Quiebra", begin=1884, end=1884, follows=(other,))
    triples = set(event.to_triples())

    # The relation edge.
    assert (event.uri, ns.FOLLOWS, other) in triples

    # The interval carrier + a typed begin boundary carrying a gYear via its Dimension.
    span = URIRef(f"{event.uri}/time-span")
    assert (event.uri, ns.DURATION, span) in triples
    assert (span, RDF.type, ns.CLASS_IRI["TimeInterval"]) in triples
    begin_boundary = URIRef(f"{span}/begin")
    assert (span, ns.TEMPORAL_LOCATION, begin_boundary) in triples
    assert (begin_boundary, ns.HAS_TYPE, URIRef(f"{B}type/begin")) in triples
    dimension = URIRef(f"{begin_boundary}/dimension")
    assert (begin_boundary, ns.HAS_DIMENSION, dimension) in triples
    assert (dimension, ns.HAS_VALUE, Literal("1884", datatype=XSD.gYear)) in triples


def test_open_interval_emits_only_known_boundary() -> None:
    """A begin-only (open) interval emits the begin boundary and no end boundary."""
    event = NarrativeEvent(uri_base=B, name="Apertura", begin=1900)
    span = URIRef(f"{event.uri}/time-span")
    triples = set(event.to_triples())
    assert (span, ns.TEMPORAL_LOCATION, URIRef(f"{span}/begin")) in triples
    assert (span, ns.TEMPORAL_LOCATION, URIRef(f"{span}/end")) not in triples


def test_interval_terms_are_in_frozen_closure() -> None:
    """Every predicate/class an interval event emits is frozen (D11, SC-003)."""
    frozen = ns.frozen_terms()
    other = URIRef(f"{B}event/otro")
    event = NarrativeEvent(
        uri_base=B, name="E", begin=1, end=2, follows=(other,), overlaps=(other,)
    )
    for _, predicate, obj in event.to_triples():
        assert predicate == RDF.type or predicate in frozen, f"predicate {predicate} not frozen"
        if predicate == RDF.type:
            assert obj in frozen, f"class {obj} not frozen"


def test_narrative_unit_emits_single_label(uri_base: str) -> None:
    """FR-001: a ``NarrativeUnit`` emits exactly one ``rdfs:label`` carrying its
    authored name byte-for-byte (accents/casing/spacing preserved)."""
    unit = NarrativeUnit(uri_base=B, name="La traición del senescal")
    labels = [o for _, p, o in unit.to_triples() if p == RDFS.label]
    assert labels == [Literal("La traición del senescal")]


def test_narrative_function_emits_single_label_alongside_typing(uri_base: str) -> None:
    """FR-002: a function emits exactly one ``rdfs:label`` with its name, coexisting
    with the ``crm:P2_has_type``/``rdf:type`` typing pair when ``type_uri`` is set."""
    term = URIRef("https://bookwright.dev/vocab/propp#function/interdiction")
    func = NarrativeFunction(uri_base=B, name="Interdicción", type_uri=term)
    triples = list(func.to_triples())
    assert [o for _, p, o in triples if p == RDFS.label] == [Literal("Interdicción")]
    assert (func.uri, ns.HAS_TYPE, term) in triples
    assert (term, RDF.type, ns.CLASS_IRI["Type"]) in triples


def test_typed_narrative_function_emits_p2_has_type_and_e55(uri_base: str) -> None:
    """C6 (golem layer): a ``NarrativeFunction`` with ``type_uri`` set emits both
    the ``crm:P2_has_type`` link and the term's ``rdf:type crm:E55_Type``."""
    term = URIRef("https://bookwright.dev/vocab/propp#function/departure")
    func = NarrativeFunction(uri_base=B, name="Departure", type_uri=term)
    triples = set(func.to_triples())
    assert (func.uri, ns.HAS_TYPE, term) in triples
    assert (term, RDF.type, ns.CLASS_IRI["Type"]) in triples


def test_untyped_narrative_function_emits_no_typing(uri_base: str) -> None:
    """``type_uri=None`` (the default) emits neither typing triple — unchanged G10."""
    func = NarrativeFunction(uri_base=B, name="Departure")
    predicates = {p for _, p, _ in func.to_triples()}
    assert ns.HAS_TYPE not in predicates


def test_typed_character_role_emits_p2_has_type_and_e55(uri_base: str) -> None:
    """C9 (golem layer): a typed ``CharacterRole`` (built via its owning Character)
    emits the ``crm:P2_has_type`` link and the term's ``rdf:type crm:E55_Type``."""
    term = URIRef("https://bookwright.dev/vocab/greimas#actant/subject")
    char = Character(
        uri_base=B, name="Ada", narrative_roles=("sujeto",), role_types={"sujeto": term}
    )
    (role,) = char.role_nodes
    triples = set(role.to_triples())
    assert (role.uri, ns.HAS_TYPE, term) in triples
    assert (term, RDF.type, ns.CLASS_IRI["Type"]) in triples


def test_untyped_character_role_emits_no_typing(uri_base: str) -> None:
    """A role with no matching term (empty ``role_types``) emits no typing triple."""
    char = Character(uri_base=B, name="Ada", narrative_roles=("custom",))
    (role,) = char.role_nodes
    assert ns.HAS_TYPE not in {p for _, p, _ in role.to_triples()}


def test_term_closure_over_frozen_ontology() -> None:
    frozen = ns.frozen_terms()
    for entity in _sample_entities():
        for subject, predicate, obj in entity.to_triples():
            # ``bw:`` is Bookwright's own vocabulary, declared in ``sources.ttl`` and
            # intentionally outside the frozen GOLEM closure — the same status the
            # ``bw:reference`` family has (which is why research entities are excluded
            # from ``_sample_entities``). ``NarrativeSequence`` now emits a ``bw:`` term
            # (``bw:sequenceOrdinal``), so the closure check exempts that namespace.
            assert (
                predicate == RDF.type
                or predicate in frozen
                or str(predicate).startswith(str(ns.BW))
            ), f"predicate {predicate} not frozen"
            if predicate == RDF.type:
                assert obj in frozen, f"class {obj} not frozen"
            # Literals (verbatim source paths) are exempt from class closure.
            assert isinstance(obj, URIRef | Literal)
            assert isinstance(subject, URIRef)
