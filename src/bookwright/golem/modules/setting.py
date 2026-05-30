"""Setting module: settings and the narrative locations placed within them."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import GolemEntity, SluggedEntity, Triple, ref_uri
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

    setting: GolemEntity | URIRef | None = None

    def to_triples(self) -> Iterable[Triple]:
        yield from super().to_triples()
        if self.setting is not None:
            yield (self.uri, GENERIC_LOCATION, ref_uri(self.setting))
