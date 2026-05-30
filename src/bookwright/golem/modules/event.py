"""Event module: narrative events and the psychological states they touch."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import GolemEntity, SluggedEntity, Triple, ref_uri
from bookwright.golem.namespaces import CLASS_IRI, GENERICALLY_DEPENDENT_ON, PARTICIPANT


class NarrativeEvent(SluggedEntity):
    """A narrative event (``golem:G5_Narrative_Event``).

    Each participant is linked by one ``dlp:participant`` triple (FR-015).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeEvent"]
    path_segment: ClassVar[str] = "event"

    participants: tuple[GolemEntity | URIRef, ...] = ()

    def to_triples(self) -> Iterable[Triple]:
        yield from super().to_triples()
        for participant in self.participants:
            yield (self.uri, PARTICIPANT, ref_uri(participant))


class PsychologicalState(SluggedEntity):
    """A psychological state (``golem:G3_Psychological_State``).

    When set, the state is ``dlp:generically-dependent-on`` its bearer (FR-015).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["PsychologicalState"]
    path_segment: ClassVar[str] = "psychological-state"

    bearer: GolemEntity | URIRef | None = None

    def to_triples(self) -> Iterable[Triple]:
        yield from super().to_triples()
        if self.bearer is not None:
            yield (self.uri, GENERICALLY_DEPENDENT_ON, ref_uri(self.bearer))
