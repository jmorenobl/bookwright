"""Narrative module: units, their functions/roles, and ordered sequences."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import GolemEntity, SluggedEntity, Triple, ref_uri
from bookwright.golem.namespaces import CLASS_IRI, PROPER_PART, REFERS_TO


class NarrativeUnit(SluggedEntity):
    """A narrative unit (``golem:G9_Narrative_Unit``).

    Refers to each of its narrative functions and roles (``crm:P67_refers_to``).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeUnit"]
    path_segment: ClassVar[str] = "narrative-unit"

    functions: tuple[GolemEntity | URIRef, ...] = ()
    roles: tuple[GolemEntity | URIRef, ...] = ()

    def to_triples(self) -> Iterable[Triple]:
        yield from super().to_triples()
        for function in self.functions:
            yield (self.uri, REFERS_TO, ref_uri(function))
        for role in self.roles:
            yield (self.uri, REFERS_TO, ref_uri(role))


class NarrativeFunction(SluggedEntity):
    """A narrative function (``golem:G10_Narrative_Function``). Identity only."""

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeFunction"]
    path_segment: ClassVar[str] = "narrative-function"


class NarrativeRole(SluggedEntity):
    """A narrative role (``golem:G11_Narrative_Role``). Identity only."""

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeRole"]
    path_segment: ClassVar[str] = "narrative-role"


class NarrativeSequence(SluggedEntity):
    """A narrative sequence (``golem:G7_Narrative_Sequence``).

    Emits one ``dlp:proper-part`` triple per member unit, in declared order
    (FR-015). RDF is unordered; the ordering is the caller's tuple order.
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeSequence"]
    path_segment: ClassVar[str] = "narrative-sequence"

    units: tuple[GolemEntity | URIRef, ...] = ()

    def to_triples(self) -> Iterable[Triple]:
        yield from super().to_triples()
        for unit in self.units:
            yield (self.uri, PROPER_PART, ref_uri(unit))
