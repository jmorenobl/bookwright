"""Narrative module: units, their functions/roles, and ordered sequences."""

from __future__ import annotations

from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, GolemEntity, SluggedEntity
from bookwright.golem.namespaces import CLASS_IRI, PROPER_PART, REFERS_TO


class NarrativeUnit(SluggedEntity):
    """A narrative unit (``golem:G9_Narrative_Unit``).

    Refers to each of its narrative functions and roles (``crm:P67_refers_to``).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeUnit"]
    path_segment: ClassVar[str] = "narrative-unit"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (
        CrossRef("functions", REFERS_TO, multi=True),
        CrossRef("roles", REFERS_TO, multi=True),
    )

    functions: tuple[GolemEntity | URIRef, ...] = ()
    roles: tuple[GolemEntity | URIRef, ...] = ()


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
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (CrossRef("units", PROPER_PART, multi=True),)

    units: tuple[GolemEntity | URIRef, ...] = ()
