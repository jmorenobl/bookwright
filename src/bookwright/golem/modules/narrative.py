"""Narrative module: units, their functions/roles, and ordered sequences."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from rdflib.namespace import RDF
from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, DerivedAssertion, GolemEntity, SluggedEntity, Triple
from bookwright.golem.namespaces import CLASS_IRI, HAS_TYPE, PROPER_PART, REFERS_TO


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
    """A narrative function (``golem:G10_Narrative_Function``).

    Identity only unless ``type_uri`` is set (iteration 030): when an authored
    function name matched a canonical Propp term, the function carries a
    ``crm:P2_has_type`` link to that ``crm:E55_Type`` term — the same two-triple
    typing shape ``Source`` and ``CharacterFeature``'s biographical variant use,
    adding no class to the frozen ontology. ``None`` ⇒ unchanged behaviour.
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeFunction"]
    path_segment: ClassVar[str] = "narrative-function"

    type_uri: URIRef | None = None

    def to_triples(self) -> Iterable[Triple]:
        yield from super().to_triples()
        if self.type_uri is not None:
            yield (self.uri, HAS_TYPE, self.type_uri)
            yield (self.type_uri, RDF.type, CLASS_IRI["Type"])

    def derived_assertions(self) -> Iterable[DerivedAssertion]:
        # The base yields the file-level identity assertion (no cross_refs here);
        # delegate so the identity shape stays single-sourced, mirroring to_triples.
        yield from super().derived_assertions()
        if self.type_uri is not None:
            # Reify the typing link through the standard provenance path so it gets
            # a ``crm:E13_Attribute_Assignment`` like every other GOLEM assertion;
            # ``"functions"`` is the front-matter key the type derived from (D4).
            yield DerivedAssertion(self.uri, self.type_uri, "functions")


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
