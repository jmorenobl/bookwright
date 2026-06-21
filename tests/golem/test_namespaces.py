"""Prefix binding and class-IRI closure backstop (FR-010, SC-003)."""

from __future__ import annotations

from rdflib import Graph

from bookwright.golem import namespaces as ns


def test_bind_prefixes_binds_exactly_the_short_prefixes() -> None:
    graph = Graph()
    ns.bind_prefixes(graph)
    bound = {prefix: str(uri) for prefix, uri in graph.namespaces()}
    assert bound["golem"] == "https://w3id.org/golem/ontology#"
    assert bound["crm"] == "http://www.cidoc-crm.org/cidoc-crm/"
    assert bound["dlp"] == "http://www.ontologydesignpatterns.org/ont/dlp/DOLCE-Lite.owl#"
    # ExtendedDnS, bound distinct from the DOLCE-Lite dlp (FR-018).
    assert bound["edns"] == "http://www.ontologydesignpatterns.org/ont/dlp/ExtendedDnS.owl#"
    assert bound["edns"] != bound["dlp"]
    assert bound["rdf"] == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    assert bound["rdfs"] == "http://www.w3.org/2000/01/rdf-schema#"
    assert bound["xsd"] == "http://www.w3.org/2001/XMLSchema#"


def test_class_iris_are_in_frozen_terms() -> None:
    frozen = ns.frozen_terms()
    for name, iri in ns.CLASS_IRI.items():
        assert iri in frozen, f"{name} → {iri} absent from frozen ontology"


def test_cross_reference_predicates_are_in_frozen_terms() -> None:
    frozen = ns.frozen_terms()
    predicates = [
        ns.PARTICIPANT,
        ns.PROPER_PART,
        ns.GENERICALLY_DEPENDENT_ON,
        ns.GENERIC_LOCATION,
        ns.REFERS_TO,
        ns.ASSIGNED_ATTRIBUTE_TO,
        ns.ASSIGNED,
        ns.USED_SPECIFIC_OBJECT,
        # Attribute-carrier predicates (FR-020).
        ns.HAS_FEATURE,
        ns.PLAYS,
        ns.HAS_TYPE,
        ns.HAS_DIMENSION,
        ns.HAS_VALUE,
    ]
    for predicate in predicates:
        assert predicate in frozen, f"{predicate} absent from frozen ontology"


def test_attribute_carrier_class_iris_present() -> None:
    """FR-020: the character-attribute carrier classes are mapped and frozen."""
    for name in ("CharacterFeature", "Dimension", "Type"):
        assert name in ns.CLASS_IRI


def test_class_iri_maps_twelve_concepts_plus_attribute_carriers() -> None:
    """The 12 narrative concepts (the SC-001 guarantee, also pinned in the
    CONCEPTS registry) plus the character-scoped carrier-only classes — G17 /
    E54 / E55, the temporal ``TimeInterval`` (DOLCE-Lite, added by the validation
    system's interval model, research D11), and ``G11_Narrative_Role`` (whose only
    materialization is the non-``CONCEPTS`` ``CharacterRole`` carrier) — 17 class
    IRIs in all. G11's IRI lives in the carrier bucket, not the concept bucket:
    no top-level role concept exists, yet the frozen 17-IRI closure is unchanged."""
    concepts = {
        "Character",
        "Object",
        "SocialRelationship",
        "RelationshipRole",
        "NarrativeEvent",
        "PsychologicalState",
        "Setting",
        "NarrativeLocation",
        "NarrativeUnit",
        "NarrativeFunction",
        "NarrativeSequence",
        "AttributeAssignment",
    }
    carriers = {"CharacterFeature", "Dimension", "Type", "TimeInterval", "NarrativeRole"}
    assert concepts <= set(ns.CLASS_IRI)
    assert carriers <= set(ns.CLASS_IRI)
    assert len(ns.CLASS_IRI) == len(concepts) + len(carriers) == 17
