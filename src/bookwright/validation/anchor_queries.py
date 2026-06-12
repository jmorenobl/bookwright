"""Read-only graph projections for the ``factual_anchor`` validator (research D9).

Turns the research-anchor sub-graph iterations 012/013 emit into the plain
in-memory shapes the validator reasons over, so ``factual_anchor`` never touches
rdflib directly — exactly how ``queries`` serves ``temporal``. Every traversal is
run through the :class:`~bookwright.indexers.Indexer` seam; the predicate IRIs come
from :mod:`bookwright.golem.namespaces`, never hardcoded.

An *anchor* is the subject of a ``bw:promotes`` triple (the one predicate that
distinguishes an anchor's ``crm:E13_Attribute_Assignment`` node from a finding's).
The interval model and the ``gYear`` parser are reused from :mod:`.queries` so the
anchor span and an event boundary coerce identically (research D2).
"""

from __future__ import annotations

from dataclasses import dataclass

from rdflib.term import URIRef

from bookwright.golem.namespaces import (
    BEGIN_OF_BEGIN,
    BW_ACCESS_DATE,
    BW_AUTHOR,
    BW_CONSTRAINS,
    BW_ORIGINAL_LANGUAGE,
    BW_ORIGINAL_QUOTE,
    BW_PROMOTES,
    BW_REFERENCE,
    BW_RELIABILITY,
    BW_RELIABILITY_JUSTIFICATION,
    BW_SUPPORTED_BY,
    BW_TRANSLATION,
    END_OF_END,
    HAS_TIME_SPAN,
    HAS_TYPE,
    RELIABILITY_IRI,
    timeline_uri,
)
from bookwright.indexers import Indexer
from bookwright.validation.queries import EventInterval, parse_gyear

__all__ = [
    "FACETS",
    "RELIABILITY_NAME",
    "AnchorRecord",
    "Facet",
    "SourceRecord",
    "entity_present",
    "load_anchors",
    "load_sources_by_anchor",
]


@dataclass(frozen=True)
class AnchorRecord:
    """One research anchor projected from the graph (the validator's working unit).

    ``constrains`` is ``None`` when the anchor carries no ``bw:constrains`` triple
    (the reader dropped an unresolved link); ``span`` is ``EventInterval(uri, None,
    None)`` when the anchor declares no time-span.
    """

    uri: str
    promotes: str
    constrains: str | None
    span: EventInterval


def load_anchors(indexer: Indexer) -> list[AnchorRecord]:
    """One :class:`AnchorRecord` per anchor node, in sorted-URI order.

    The optional ``bw:constrains`` target and the optional ``crm:E52_Time-Span``
    (``P82a``/``P82b`` → years via :func:`~bookwright.validation.queries.parse_gyear`)
    are read in a single projection; an absent optional is simply unbound. SPARQL
    only — no reasoning happens here.
    """
    rows = indexer.query(
        f"""
        SELECT ?anchor ?finding ?constrains ?begin ?end WHERE {{
          ?anchor <{BW_PROMOTES}> ?finding .
          OPTIONAL {{ ?anchor <{BW_CONSTRAINS}> ?constrains . }}
          OPTIONAL {{
            ?anchor <{HAS_TIME_SPAN}> ?ts .
            OPTIONAL {{ ?ts <{BEGIN_OF_BEGIN}> ?begin . }}
            OPTIONAL {{ ?ts <{END_OF_END}> ?end . }}
          }}
        }}
        """
    )
    records: dict[str, AnchorRecord] = {}
    for row in rows:
        anchor = row["anchor"]
        if anchor in records:  # defensive: one anchor → one record (first wins, sorted)
            continue
        begin = parse_gyear(row["begin"]) if "begin" in row else None
        end = parse_gyear(row["end"]) if "end" in row else None
        records[anchor] = AnchorRecord(
            uri=anchor,
            promotes=row["finding"],
            constrains=row.get("constrains"),
            span=EventInterval(uri=anchor, begin=begin, end=end),
        )
    return [records[uri] for uri in sorted(records)]


# --- Source provenance / reliability projections (R2/R3, research D5/D6) -----


@dataclass(frozen=True)
class Facet:
    """One mandatory provenance facet of a :class:`Source` (research D5).

    ``label`` is the author-facing name a violation message uses; ``predicate`` is
    the source predicate whose presence in the graph proves the facet is recorded.
    ``foreign_only`` marks ``translation`` — mandatory only when the source's
    original language differs from the book language (the reader's D6 rule).
    """

    label: str
    predicate: URIRef
    foreign_only: bool = False


# The mandatory facets, in serialization order. Their predicate SET is the single
# membership emitted by a fully-populated ``provenance.Source.to_triples()`` (D5),
# pinned by a drift-guard test — it is NOT ``io/research._SOURCE_FACETS`` (which
# lists Pydantic field NAMES: it includes ``name``, which has no predicate, and
# omits ``translation``). The IRIs come from the ``golem.namespaces`` constants.
FACETS: tuple[Facet, ...] = (
    Facet("type", HAS_TYPE),
    Facet("reliability", BW_RELIABILITY),
    Facet("reliability justification", BW_RELIABILITY_JUSTIFICATION),
    Facet("reference", BW_REFERENCE),
    Facet("author", BW_AUTHOR),
    Facet("original language", BW_ORIGINAL_LANGUAGE),
    Facet("access date", BW_ACCESS_DATE),
    Facet("original quote", BW_ORIGINAL_QUOTE),
    Facet("translation", BW_TRANSLATION, foreign_only=True),
)

# Reliability rank name ← its E55 individual IRI, inverted from the single
# vocabulary source (``RELIABILITY_IRI``) so the scale never re-spells it (D6).
# Public alongside the projections (020): ``status`` aggregation joins ratings
# back to names through this same map, never a re-derived copy.
RELIABILITY_NAME: dict[str, str] = {str(iri): name for name, iri in RELIABILITY_IRI.items()}


@dataclass(frozen=True)
class SourceRecord:
    """One source backing an anchor's promoted finding (R2/R3 working unit).

    ``present_predicates`` is the set of facet-predicate IRI strings the source
    actually carries (R2 reads it to find gaps); ``original_language`` drives the
    translation conditionality; ``reliability`` is the rating *name*
    (``alta``/``media``/``baja``) or ``None`` when the source is unrated.
    """

    uri: str
    present_predicates: frozenset[str]
    original_language: str | None
    reliability: str | None


@dataclass
class _SourceAccum:
    """Mutable accumulator while folding a source's triples (one per ``?p``)."""

    predicates: set[str]
    language: str | None = None
    reliability_iri: str | None = None


def load_sources_by_anchor(indexer: Indexer) -> dict[str, list[SourceRecord]]:
    """Supporting sources per anchor, reached ``anchor→finding→source`` (D5).

    A source with no describing triple (a dangling ``bw:supportedBy``) still
    appears — with an empty facet set — so R2 can flag every missing facet. Sources
    are returned in sorted-URI order per anchor for byte-stable output.
    """
    rows = indexer.query(
        f"""
        SELECT ?anchor ?source ?p ?o WHERE {{
          ?anchor <{BW_PROMOTES}> ?finding .
          ?finding <{BW_SUPPORTED_BY}> ?source .
          OPTIONAL {{ ?source ?p ?o . }}
        }}
        """
    )
    by_anchor: dict[str, dict[str, _SourceAccum]] = {}
    for row in rows:
        sources = by_anchor.setdefault(row["anchor"], {})
        acc = sources.setdefault(row["source"], _SourceAccum(predicates=set()))
        predicate = row.get("p")
        if predicate is None:
            continue
        acc.predicates.add(predicate)
        if predicate == str(BW_ORIGINAL_LANGUAGE):
            acc.language = row.get("o")
        elif predicate == str(BW_RELIABILITY):
            acc.reliability_iri = row.get("o")
    return {
        anchor: [
            SourceRecord(
                uri=source,
                present_predicates=frozenset(acc.predicates),
                original_language=acc.language,
                reliability=RELIABILITY_NAME.get(acc.reliability_iri or ""),
            )
            for source, acc in sorted(sources.items())
        ]
        for anchor, sources in by_anchor.items()
    }


def entity_present(indexer: Indexer, uri: str, uri_base: str) -> bool:
    """Whether ``uri`` denotes a present graph entity (R4 presence test, D4).

    True when the URI is the subject of at least one triple, or when it is the
    well-known (untyped) timeline IRI — a legitimate ``bw:constrains`` target that
    carries no describing triple of its own.
    """
    if uri == str(timeline_uri(uri_base)):
        return True
    rows = list(indexer.query(f"SELECT ?p WHERE {{ <{uri}> ?p ?o . }} LIMIT 1"))
    return bool(rows)
