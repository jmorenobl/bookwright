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
    ]
    for predicate in predicates:
        assert predicate in frozen, f"{predicate} absent from frozen ontology"


def test_all_thirteen_concepts_mapped() -> None:
    assert len(ns.CLASS_IRI) == 13
