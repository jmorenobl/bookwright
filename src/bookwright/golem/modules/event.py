"""Event module: narrative events and the psychological states they touch."""

from __future__ import annotations

from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, GolemEntity, SluggedEntity
from bookwright.golem.namespaces import CLASS_IRI, GENERICALLY_DEPENDENT_ON, PARTICIPANT


class NarrativeEvent(SluggedEntity):
    """A narrative event (``golem:G5_Narrative_Event``).

    Each participant is linked by one ``dlp:participant`` triple (FR-015).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeEvent"]
    path_segment: ClassVar[str] = "event"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (
        CrossRef("participants", PARTICIPANT, multi=True),
    )

    participants: tuple[GolemEntity | URIRef, ...] = ()


class PsychologicalState(SluggedEntity):
    """A psychological state (``golem:G3_Psychological_State``).

    When set, the state is ``dlp:generically-dependent-on`` its bearer (FR-015).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["PsychologicalState"]
    path_segment: ClassVar[str] = "psychological-state"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (CrossRef("bearer", GENERICALLY_DEPENDENT_ON),)

    bearer: GolemEntity | URIRef | None = None
