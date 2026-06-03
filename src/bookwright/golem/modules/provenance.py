"""Provenance module: research entities (Source / Finding / Anchor).

The three research concepts of iteration 012 (design § 20). They reuse the GOLEM
machinery — frozen Pydantic identity, deterministic URIs, ``to_triples()`` — but
introduce **no new GOLEM/ontology class** (Constitution X, FR-001):

- :class:`Source` is typed purely via ``crm:E55_Type`` (``crm:P2_has_type`` →
  a ``sources.ttl`` individual); it emits **no** ``rdf:type`` (research D2).
- :class:`Finding` and :class:`Anchor` reify on ``crm:E13_Attribute_Assignment``
  (the same class the Inference module uses), staying distinguishable from inferred
  assertions by their URI segment and their ``bw:`` predicates (FR-018, research D9).

All Bookwright (``bw:``) predicates and the source-type / reliability individuals
are declared in ``resources/vocabularies/sources.ttl``, never in the frozen
``golem.ttl``.
"""

from __future__ import annotations

import datetime
from collections.abc import Iterable
from typing import ClassVar, Literal

from pydantic import field_validator
from rdflib.namespace import RDF, XSD
from rdflib.term import Literal as RdfLiteral
from rdflib.term import URIRef

from bookwright.golem.base import MintedEntity, SluggedEntity, Triple
from bookwright.golem.modules.feature import gyear_literal
from bookwright.golem.namespaces import (
    ASSIGNED_ATTRIBUTE_TO,
    BEGIN_OF_BEGIN,
    BW_ACCESS_DATE,
    BW_ASSERTED_BY,
    BW_AUTHOR,
    BW_CLAIM,
    BW_CONSTRAINS,
    BW_OPEN,
    BW_ORIGINAL_LANGUAGE,
    BW_ORIGINAL_QUOTE,
    BW_PROMOTES,
    BW_REFERENCE,
    BW_RELIABILITY,
    BW_RELIABILITY_JUSTIFICATION,
    BW_SUPPORTED_BY,
    BW_TRANSLATION,
    CLASS_IRI,
    E52_TIME_SPAN,
    END_OF_END,
    HAS_TIME_SPAN,
    HAS_TYPE,
    RELIABILITY_IRI,
    SOURCE_TYPE_IRI,
)

SourceType = Literal[
    "primaria", "secundaria", "oficial", "académica", "periodística", "testimonial"
]
"""The six controlled source-type values (FR-003). The `Literal` is the enforcement
point — an out-of-vocabulary value raises a `ValidationError` (research D4)."""

Reliability = Literal["alta", "media", "baja"]
"""The three controlled reliability values (FR-004)."""


def _string(value: str) -> RdfLiteral:
    """An ``xsd:string`` literal (the default datatype for every prose facet)."""
    return RdfLiteral(value, datatype=XSD.string)


class Source(SluggedEntity):
    """A research source, typed via ``crm:E55_Type`` — **no** ``rdf:type`` (D2).

    Its identity token is the ASCII slug of ``name`` (segment ``source``), like
    :class:`~bookwright.golem.modules.character.Character`. ``type`` and
    ``reliability`` are controlled vocabularies enforced by ``Literal`` fields;
    an out-of-vocabulary value is a ``ValidationError`` the reader turns into a
    build-aborting :class:`~bookwright.io.errors.ResearchError` (FR-016).

    ``translation`` is set by the reader **only** when the source's
    ``original_language`` differs from the book language (research D6); the entity
    itself is language-context-free.
    """

    # A documented, *unemitted* placeholder: Source overrides ``to_triples`` and
    # yields no ``(uri, rdf:type, golem_class)`` triple. Identity in the graph is
    # ``?s crm:P2_has_type ?t . ?t a crm:E55_Type`` (research D2).
    golem_class: ClassVar[URIRef] = CLASS_IRI["Type"]
    path_segment: ClassVar[str] = "source"

    reference: str
    author: str
    original_language: str
    type: SourceType
    reliability: Reliability
    reliability_justification: str
    access_date: datetime.date
    original_quote: str
    translation: str | None = None

    @field_validator("reliability_justification")
    @classmethod
    def _non_empty_justification(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("`reliability_justification` must not be empty")
        return value

    def to_triples(self) -> Iterable[Triple]:
        """Emit the source's provenance facets — typed via E55, never ``rdf:type``."""
        yield (self.uri, HAS_TYPE, SOURCE_TYPE_IRI[self.type])
        yield (self.uri, BW_RELIABILITY, RELIABILITY_IRI[self.reliability])
        yield (self.uri, BW_RELIABILITY_JUSTIFICATION, _string(self.reliability_justification))
        yield (self.uri, BW_REFERENCE, _string(self.reference))
        yield (self.uri, BW_AUTHOR, _string(self.author))
        yield (self.uri, BW_ORIGINAL_LANGUAGE, _string(self.original_language))
        yield (self.uri, BW_ACCESS_DATE, RdfLiteral(self.access_date, datatype=XSD.date))
        yield (self.uri, BW_ORIGINAL_QUOTE, _string(self.original_quote))
        if self.translation is not None:
            yield (self.uri, BW_TRANSLATION, _string(self.translation))


class Finding(MintedEntity):
    """A research finding, reified on ``crm:E13_Attribute_Assignment`` (FR-006).

    Its identity token is the time-ordered uuid7 minted once by
    :class:`~bookwright.golem.base.MintedEntity` (segment ``finding``). A **closed**
    finding records a ``claim``, who asserts
    it (``asserted_by``, default ``"author"``), the narrative entity it
    ``bears_on`` (reusing the Inference module's ``crm:P140_assigned_attribute_to``)
    and one or more supporting ``sources``. An **open** finding (FR-008) is an
    unresolved question: ``claim``/``bears_on``/``sources`` may all be empty and the
    entity is still valid, emitting just ``rdf:type`` + ``bw:open true``.

    ``bw:assertedBy`` is emitted only alongside a ``claim`` — an open question with
    no claim asserts nothing, so it carries no asserter (research D9).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["AttributeAssignment"]
    path_segment: ClassVar[str] = "finding"

    claim: str | None = None
    asserted_by: str = "author"
    bears_on: URIRef | None = None
    sources: tuple[URIRef, ...] = ()
    open: bool = False

    def to_triples(self) -> Iterable[Triple]:
        yield (self.uri, RDF.type, self.golem_class)
        if self.claim is not None:
            yield (self.uri, BW_CLAIM, _string(self.claim))
            yield (self.uri, BW_ASSERTED_BY, _string(self.asserted_by))
        if self.bears_on is not None:
            yield (self.uri, ASSIGNED_ATTRIBUTE_TO, self.bears_on)
        for source in self.sources:
            yield (self.uri, BW_SUPPORTED_BY, source)
        if self.open:
            yield (self.uri, BW_OPEN, RdfLiteral(True))


class Anchor(MintedEntity):
    """A binding constraint promoting a :class:`Finding`, reified on E13 (FR-009).

    Its identity token is the uuid7 minted by
    :class:`~bookwright.golem.base.MintedEntity` (segment ``anchor``). It
    ``promotes`` the finding it derives from and ``constrains`` a narrative entity
    (or the well-known untyped timeline IRI, research D10). When the named target
    does not resolve in the bible, the reader builds the anchor with
    ``constrains=None`` and surfaces a warning — the ``bw:constrains`` triple is
    simply omitted, the build still succeeds (research D12).

    An optional time-span (``begin``/``end`` years, research D5) is emitted as a
    ``crm:E52_Time-Span`` sub-node under ``crm:P4_has_time-span``; an anchor with
    neither bound emits no time-span (FR-010).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["AttributeAssignment"]
    path_segment: ClassVar[str] = "anchor"

    promotes: URIRef
    constrains: URIRef | None = None
    begin: int | None = None
    end: int | None = None

    def to_triples(self) -> Iterable[Triple]:
        yield (self.uri, RDF.type, self.golem_class)
        yield (self.uri, BW_PROMOTES, self.promotes)
        if self.constrains is not None:
            yield (self.uri, BW_CONSTRAINS, self.constrains)
        if self.begin is not None or self.end is not None:
            time_span = URIRef(f"{self.uri}/time-span")
            yield (self.uri, HAS_TIME_SPAN, time_span)
            yield (time_span, RDF.type, E52_TIME_SPAN)
            if self.begin is not None:
                yield (time_span, BEGIN_OF_BEGIN, gyear_literal(self.begin))
            if self.end is not None:
                yield (time_span, END_OF_END, gyear_literal(self.end))
