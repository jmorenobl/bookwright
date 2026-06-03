"""Event module: narrative events and the psychological states they touch."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from rdflib.namespace import RDF
from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, GolemEntity, SluggedEntity, Triple
from bookwright.golem.modules.feature import Dimension
from bookwright.golem.namespaces import (
    CLASS_IRI,
    DURATION,
    FOLLOWS,
    GENERICALLY_DEPENDENT_ON,
    HAS_DIMENSION,
    HAS_TYPE,
    PARTICIPANT,
    PRECEDES,
    TEMPORAL_LOCATION,
    TEMPORALLY_INCLUDED_IN,
    TEMPORALLY_INCLUDES,
    TEMPORALLY_OVERLAPS,
)

# boundary kind → the begin/end year field it draws from (interval emission order).
_BOUNDARIES: tuple[str, ...] = ("begin", "end")


class NarrativeEvent(SluggedEntity):
    """A narrative event (``golem:G5_Narrative_Event``).

    Each participant is linked by one ``dlp:participant`` triple (FR-015). An event
    may additionally carry a multi-year time **interval** (``begin`` / ``end`` years)
    and any of the five qualitative temporal relations to other events, which the
    ``temporal`` validator (iteration 11) reasons over. The relations are ordinary
    ``cross_refs`` (one frozen ``TR:*`` predicate each); the interval needs a custom
    ``to_triples`` override because its typed-boundary + dimension shape is outside
    what ``cross_refs`` can express (research D11). An event with no interval and no
    relations behaves exactly as before — only its ``rdf:type`` and any participants.
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeEvent"]
    path_segment: ClassVar[str] = "event"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (
        CrossRef("participants", PARTICIPANT, multi=True),
        CrossRef("follows", FOLLOWS, multi=True),
        CrossRef("precedes", PRECEDES, multi=True),
        CrossRef("overlaps", TEMPORALLY_OVERLAPS, multi=True),
        CrossRef("includes", TEMPORALLY_INCLUDES, multi=True),
        CrossRef("included_in", TEMPORALLY_INCLUDED_IN, multi=True),
    )

    participants: tuple[GolemEntity | URIRef, ...] = ()
    begin: int | None = None
    end: int | None = None
    follows: tuple[GolemEntity | URIRef, ...] = ()
    precedes: tuple[GolemEntity | URIRef, ...] = ()
    overlaps: tuple[GolemEntity | URIRef, ...] = ()
    includes: tuple[GolemEntity | URIRef, ...] = ()
    included_in: tuple[GolemEntity | URIRef, ...] = ()

    def to_triples(self) -> Iterable[Triple]:
        """The base emission (type + participants + the five relation edges) followed
        by the closure-safe interval triples for any present begin/end boundary."""
        yield from super().to_triples()
        yield from self._interval_triples()

    def _interval_triples(self) -> Iterable[Triple]:
        if self.begin is None and self.end is None:
            return
        span_uri = URIRef(f"{self.uri}/time-span")
        time_interval = CLASS_IRI["TimeInterval"]
        yield (self.uri, DURATION, span_uri)
        yield (span_uri, RDF.type, time_interval)
        for kind in _BOUNDARIES:
            year = self.begin if kind == "begin" else self.end
            if year is None:
                continue
            boundary_uri = URIRef(f"{span_uri}/{kind}")
            type_uri = URIRef(f"{self.uri_base}type/{kind}")
            dimension = Dimension(uri_base=self.uri_base, feature_uri=boundary_uri, year=year)
            yield (span_uri, TEMPORAL_LOCATION, boundary_uri)
            yield (boundary_uri, RDF.type, time_interval)
            yield (boundary_uri, HAS_TYPE, type_uri)
            yield (type_uri, RDF.type, CLASS_IRI["Type"])
            yield (boundary_uri, HAS_DIMENSION, dimension.uri)
            yield from dimension.to_triples()


class PsychologicalState(SluggedEntity):
    """A psychological state (``golem:G3_Psychological_State``).

    When set, the state is ``dlp:generically-dependent-on`` its bearer (FR-015).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["PsychologicalState"]
    path_segment: ClassVar[str] = "psychological-state"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (CrossRef("bearer", GENERICALLY_DEPENDENT_ON),)

    bearer: GolemEntity | URIRef | None = None
