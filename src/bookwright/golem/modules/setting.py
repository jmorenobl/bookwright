"""Setting module: settings and the narrative locations placed within them."""

from __future__ import annotations

from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, GolemEntity, SluggedEntity
from bookwright.golem.namespaces import CLASS_IRI, GENERIC_LOCATION


class Setting(SluggedEntity):
    """A setting (``golem:G12_Setting``). Identity only in v0."""

    golem_class: ClassVar[URIRef] = CLASS_IRI["Setting"]
    path_segment: ClassVar[str] = "setting"


class NarrativeLocation(SluggedEntity):
    """A narrative location (``golem:G13_Narrative_Location``).

    When set, the location is ``dlp:generic-location`` of its setting (FR-015).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeLocation"]
    path_segment: ClassVar[str] = "location"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (CrossRef("setting", GENERIC_LOCATION),)

    setting: GolemEntity | URIRef | None = None
