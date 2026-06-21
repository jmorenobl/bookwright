"""Narrative module: units, their functions/roles, and ordered sequences."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from rdflib.namespace import RDF, RDFS, XSD
from rdflib.term import Literal, URIRef

from bookwright.golem.base import (
    CrossRef,
    DerivedAssertion,
    GolemEntity,
    SluggedEntity,
    Triple,
    ref_uri,
)
from bookwright.golem.namespaces import (
    BW_SEQUENCE_ORDINAL,
    CLASS_IRI,
    HAS_TYPE,
    PROPER_PART,
    REFERS_TO,
)


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

    def to_triples(self) -> Iterable[Triple]:
        # The single ``rdfs:label`` triple carrying the authored ``name`` verbatim,
        # reusing the ``CharacterRole``/``CharacterFeature`` one-triple label shape so
        # a beat is queryable by its human name (FR-001). It rides the entity's
        # identity assertion — no new E13 (FR-006).
        yield from super().to_triples()
        yield (self.uri, RDFS.label, Literal(self.name))


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
        # The single ``rdfs:label`` triple carrying the authored ``name`` verbatim
        # (FR-002); rides the identity assertion like the unit's, no new E13. The
        # function is minted once per slug, so exactly one label triple exists even
        # when several fiches name it (C2 dedup invariant).
        yield (self.uri, RDFS.label, Literal(self.name))
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


class NarrativeSequence(SluggedEntity):
    """A narrative sequence (``golem:G7_Narrative_Sequence``).

    Emits one ``dlp:proper-part`` triple per member unit, in declared order
    (FR-015). RDF is unordered; the ordering is the caller's tuple order.
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeSequence"]
    path_segment: ClassVar[str] = "narrative-sequence"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (CrossRef("units", PROPER_PART, multi=True),)

    units: tuple[GolemEntity | URIRef, ...] = ()

    def to_triples(self) -> Iterable[Triple]:
        # After the type + ``dlp:proper-part`` edges, materialize each member's
        # resolved position as a queryable per-unit ordinal so the sequence is
        # ``ORDER BY``-able under unordered RDF (FR-003). ``units`` is already sorted
        # by ``_member_sort_key`` at assembly time, so the 1-based index ``i`` is the
        # member's contiguous rank in that total order (FR-004) — the subject is the
        # **unit** URI, one hop from the sequence.
        yield from super().to_triples()
        for i, unit in enumerate(self.units, start=1):
            yield (ref_uri(unit), BW_SEQUENCE_ORDINAL, Literal(i, datatype=XSD.integer))

    def derived_assertions(self) -> Iterable[DerivedAssertion]:
        # The base yields the identity assertion plus one proper-part membership E13
        # per member. Each ordinal is a *relational* attribution (a property of the
        # assembled membership, not intrinsic to the unit), so — unlike the label —
        # it gets its own file-level E13: target the unit, attribute the sequence,
        # keyed to ``order`` (no ``:line`` since the rank emerges across cards) (FR-006).
        yield from super().derived_assertions()
        for unit in self.units:
            yield DerivedAssertion(ref_uri(unit), self.uri, "order")
