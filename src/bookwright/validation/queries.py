"""Read-only graph projections for the ``temporal`` validator (data-model, D11/D12).

These helpers turn the interval graph the timeline indexer emits into plain
in-memory shapes (``EventInterval`` + relation edge sets) the validator reasons
over, so ``temporal`` never touches rdflib directly. SPARQL is run through the
``Indexer`` seam (``indexer.query``); every traversal is insensitive to whether a
year sits on a boundary directly or on its ``Dimension`` sub-node.
"""

from __future__ import annotations

from dataclasses import dataclass

from rdflib.namespace import RDF, RDFS, XSD

from bookwright.golem.namespaces import (
    ASSIGNED_ATTRIBUTE_TO,
    CRM,
    CSM,
    GOLEM,
    TEMPORAL_RELATIONS,
    TR,
    USED_SPECIFIC_OBJECT,
)
from bookwright.indexers import Indexer
from bookwright.validation.base import split_source

__all__ = ["EventInterval", "load_intervals", "load_relations", "resolve_source"]

_PREFIXES = "\n".join(
    f"PREFIX {prefix}: <{uri}>"
    for prefix, uri in (
        ("golem", str(GOLEM)),
        ("crm", str(CRM)),
        ("tr", str(TR)),
        ("csm", str(CSM)),
        ("rdf", str(RDF)),
        ("rdfs", str(RDFS)),
        ("xsd", str(XSD)),
    )
)


@dataclass(frozen=True)
class EventInterval:
    """One event's begin/end years (either may be ``None`` for an open interval)."""

    uri: str
    begin: int | None
    end: int | None


def _q(indexer: Indexer, body: str) -> list[dict[str, str]]:
    return list(indexer.query(f"{_PREFIXES}\n{body}"))


def _parse_year(raw: str) -> int | None:
    """Coerce an ``xsd:gYear`` lexical (``"1885"``, ``"0800"``, ``"-0044"``) to int."""
    text = raw.strip()
    negative = text.startswith("-")
    digits = text[1:] if negative else text
    if not digits.isdigit():
        return None
    value = int(digits)
    return -value if negative else value


def load_intervals(indexer: Indexer) -> dict[str, EventInterval]:
    """One :class:`EventInterval` per ``G5_Narrative_Event`` in the graph.

    The year is reached via ``(csm:duration|tr:temporal-location)/tr:temporal-location``
    to a boundary whose ``crm:P2_has_type`` localname is ``begin`` / ``end``, then
    ``(crm:P90_has_value | crm:P43_has_dimension/crm:P90_has_value)`` — so it is
    insensitive to the carrier-node shape (D12). Events without an interval still
    appear, with both bounds ``None``.
    """
    intervals: dict[str, list[int | None]] = {
        row["event"]: [None, None]
        for row in _q(indexer, "SELECT ?event WHERE { ?event a golem:G5_Narrative_Event . }")
    }
    rows = _q(
        indexer,
        """
        SELECT ?event ?btype ?year WHERE {
          ?event a golem:G5_Narrative_Event .
          ?event (csm:duration|tr:temporal-location)/tr:temporal-location ?boundary .
          ?boundary crm:P2_has_type ?btype .
          ?boundary (crm:P90_has_value | crm:P43_has_dimension/crm:P90_has_value) ?year .
        }
        """,
    )
    for row in rows:
        event, btype, year = row["event"], row["btype"], _parse_year(row["year"])
        if event not in intervals or year is None:
            continue
        if btype.endswith("/begin"):
            intervals[event][0] = year
        elif btype.endswith("/end"):
            intervals[event][1] = year
    return {
        event: EventInterval(uri=event, begin=bounds[0], end=bounds[1])
        for event, bounds in intervals.items()
    }


def load_relations(indexer: Indexer) -> dict[str, set[tuple[str, str]]]:
    """The five ``TR:*`` edge sets, keyed by canonical relation name (D11).

    Keys are :data:`TEMPORAL_RELATIONS` names (``follows`` … ``included_in``). Each
    set holds ``(subject, object)`` event-URI pairs. Only edges between two narrative
    events are kept, so a stray edge never leaks into the reasoning.
    """
    relations: dict[str, set[tuple[str, str]]] = {}
    for relation in TEMPORAL_RELATIONS:
        rows = _q(
            indexer,
            f"""
            SELECT ?a ?b WHERE {{
              ?a a golem:G5_Narrative_Event .
              ?b a golem:G5_Narrative_Event .
              ?a <{relation.predicate}> ?b .
            }}
            """,
        )
        relations[relation.name] = {(row["a"], row["b"]) for row in rows}
    return relations


def resolve_source(indexer: Indexer, uri: str) -> str | None:
    """Recover the ``relpath[:line]`` provenance string for a graph entity (D6).

    Reads the CIDOC provenance edge: an ``E13_Attribute_Assignment`` whose
    ``P140_assigned_attribute_to`` is ``uri`` carries the source on
    ``P16_used_specific_object``. When several exist, prefer one with a ``:line``
    suffix, then the lexicographically smallest, for a deterministic result.
    """
    rows = _q(
        indexer,
        f"""
        SELECT ?source WHERE {{
          ?assertion <{ASSIGNED_ATTRIBUTE_TO}> <{uri}> .
          ?assertion <{USED_SPECIFIC_OBJECT}> ?source .
        }}
        """,
    )
    sources = sorted({row["source"] for row in rows})
    if not sources:
        return None
    located = [s for s in sources if split_source(s)[1] is not None]
    return located[0] if located else sources[0]
