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
    DLP,
    GOLEM,
    TEMPORAL_RELATIONS,
    TR,
    USED_SPECIFIC_OBJECT,
)
from bookwright.indexers import Indexer
from bookwright.validation.base import split_source

__all__ = [
    "EventInterval",
    "intervals_disjoint",
    "load_intervals",
    "load_orphan_units",
    "load_relations",
    "parse_gyear",
    "resolve_source",
    "timeline_bounds",
]

_PREFIXES = "\n".join(
    f"PREFIX {prefix}: <{uri}>"
    for prefix, uri in (
        ("golem", str(GOLEM)),
        ("crm", str(CRM)),
        ("tr", str(TR)),
        ("csm", str(CSM)),
        ("dlp", str(DLP)),
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


def parse_gyear(raw: str) -> int | None:
    """Coerce an ``xsd:gYear`` lexical (``"1885"``, ``"0800"``, ``"-0044"``) to int.

    The single ``gYear`` parser for the ``temporal`` and ``factual_anchor``
    validators: ``temporal`` reads event boundary years through it (via
    :func:`load_intervals`) and ``factual_anchor`` reads anchor time-span years
    through it (via ``anchor_queries.load_anchors``), so both coerce identically.
    """
    text = raw.strip()
    negative = text.startswith("-")
    digits = text[1:] if negative else text
    if not digits.isdigit():
        return None
    value = int(digits)
    return -value if negative else value


def intervals_disjoint(a: EventInterval, b: EventInterval) -> bool:
    """True when two closed year ranges provably do not overlap (FR-011, research D1).

    The **single source of truth** for "two intervals contradict": both the
    ``temporal`` validator (overlap-disjoint rule) and ``factual_anchor`` (the
    anachronism rule) decide disjointness here and nowhere else. An open bound
    (``None``) is unbounded on that side, so it can never force disjointness — an
    open-ended interval cannot be *proven* disjoint from anything.
    """
    return (a.end is not None and b.begin is not None and a.end < b.begin) or (
        b.end is not None and a.begin is not None and b.end < a.begin
    )


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
        event, btype, year = row["event"], row["btype"], parse_gyear(row["year"])
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


def timeline_bounds(intervals: dict[str, EventInterval]) -> EventInterval:
    """The timeline's overall ``(min begin, max end)`` across the given events (D3).

    A **pure** reduction over an already-loaded :func:`load_intervals` result — it
    adds **no** new interval reasoning — used by ``factual_anchor`` when an anchor
    constrains the timeline as a whole. Both bounds are ``None`` when no event carries
    a year. The ``uri`` is a sentinel label (the timeline has no single typed node,
    research D10). It takes the loaded dict (not the indexer) so the caller reuses one
    :func:`load_intervals` pass rather than querying the graph a second time.
    """
    begins = [iv.begin for iv in intervals.values() if iv.begin is not None]
    ends = [iv.end for iv in intervals.values() if iv.end is not None]
    return EventInterval(
        uri="timeline",
        begin=min(begins) if begins else None,
        end=max(ends) if ends else None,
    )


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


def load_orphan_units(indexer: Indexer) -> list[tuple[str, str | None]]:
    """``(uri, label)`` for every ``G9`` unit that is a member of no ``G7`` sequence (FR-005).

    A unit is orphaned ⇔ no ``G7_Narrative_Sequence`` has a ``dlp:proper-part`` edge
    to it (the membership edge :class:`NarrativeSequence` emits per member). The
    ``NOT EXISTS`` states that declaratively over the derived graph. The unit's human
    ``rdfs:label`` (emitted per ``G9`` since iteration 035) rides the same query via an
    ``OPTIONAL`` so the orphan rule can name the unit by its authored name without a
    second round trip (FR-003); ``label`` is ``None`` when the graph carries none. Each
    ``G9`` emits exactly one ``rdfs:label`` (iteration 035), so the ``OPTIONAL`` yields
    exactly one row per orphan URI — sorting by that unique URI is byte-stable (research
    D3/D9), no per-URI dedup needed. A graph with no ``G9`` units returns ``[]`` so the
    orphan rule stays inert (FR-009).
    """
    rows = _q(
        indexer,
        """
        SELECT ?unit ?label WHERE {
          ?unit a golem:G9_Narrative_Unit .
          FILTER NOT EXISTS {
            ?seq a golem:G7_Narrative_Sequence .
            ?seq dlp:proper-part ?unit .
          }
          OPTIONAL { ?unit rdfs:label ?label }
        }
        """,
    )
    return sorted(((row["unit"], row.get("label")) for row in rows), key=lambda pair: pair[0])


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
