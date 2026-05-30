"""Collection-level Turtle serialization (research D8, FR-012)."""

from __future__ import annotations

from collections.abc import Iterable

from rdflib import Graph

from bookwright.golem.base import GolemEntity
from bookwright.golem.namespaces import bind_prefixes


def to_turtle(entities: Iterable[GolemEntity]) -> str:
    """Serialize ``entities`` to a single prefixed Turtle document.

    Builds a fresh graph, binds the short prefixes (FR-010), adds every triple
    each entity yields, and serializes. The output parses back through rdflib
    and round-trips isomorphically (SC-004).
    """
    graph = Graph()
    bind_prefixes(graph)
    for entity in entities:
        for triple in entity.to_triples():
            graph.add(triple)
    return graph.serialize(format="turtle")
