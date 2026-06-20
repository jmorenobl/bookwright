"""Feature module: character-scoped attribute carriers.

These typed nodes hang off a :class:`~bookwright.golem.modules.character.Character`
and carry the documented frontmatter that the identity-only model could not:
free-text features, biographical years (``born`` / ``died``), and narrative
roles. They are **not** narrative concepts — they are excluded from the
``CONCEPTS`` registry (SC-001) — but they emit only frozen GOLEM / CIDOC-CRM /
DOLCE terms (FR-020), and every node carries a deterministic, character-scoped
URI built from its owner's URI plus a fixed suffix (never a blank node, FR-021).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar, Literal

from pydantic import model_validator
from rdflib.namespace import RDF, RDFS, XSD
from rdflib.term import Literal as RdfLiteral
from rdflib.term import URIRef

from bookwright.golem.base import GolemEntity, Triple
from bookwright.golem.namespaces import (
    CLASS_IRI,
    HAS_DIMENSION,
    HAS_TYPE,
    HAS_VALUE,
)
from bookwright.golem.slug import make_slug

BioKind = Literal["birth", "death"]
"""The two biographical feature kinds; each maps to a shared E55_Type individual."""


def gyear_literal(year: int) -> RdfLiteral:
    """Format an integer year as a lexically valid ``xsd:gYear`` literal (FR-019).

    XSD requires the year part to be at least four digits, with an optional
    leading ``-`` for BCE years. Plain ``str(year)`` is invalid for years < 1000
    or BCE (e.g. ``"800"``, ``"-44"``), which the iteration-10 temporal queries —
    the whole reason for ``gYear`` over a plain string — would then reject. Pad
    the magnitude to four digits and preserve the sign instead, so ``800`` →
    ``"0800"`` and ``-44`` → ``"-0044"`` while ``1828`` stays ``"1828"``.
    """
    sign = "-" if year < 0 else ""
    return RdfLiteral(f"{sign}{abs(year):04d}", datatype=XSD.gYear)


class Dimension(GolemEntity):
    """A measurement (``crm:E54_Dimension``) carrying a biographical year.

    URI is ``{feature.uri}/dimension``; the year is emitted as an ``xsd:gYear``
    literal (never ``xsd:integer`` or an untyped string — FR-019), which is what
    makes iteration-10's temporal queries answerable.
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["Dimension"]

    feature_uri: URIRef
    year: int

    def model_post_init(self, __context: object) -> None:
        self._uri = URIRef(f"{self.feature_uri}/dimension")

    def to_triples(self) -> Iterable[Triple]:
        yield (self.uri, RDF.type, self.golem_class)
        yield (self.uri, HAS_VALUE, gyear_literal(self.year))


class CharacterFeature(GolemEntity):
    """A character feature (``golem:G17_Character_Feature``), one of two variants.

    - **free-text** — supply ``label``; URI ``{character.uri}/feature/{slug(label)}``,
      emits the type assertion + ``rdfs:label``.
    - **biographical** — supply ``kind`` (``"birth"``/``"death"``) and ``year``;
      URI ``{character.uri}/feature/bio/{kind}`` (the ``bio/`` sub-segment keeps
      the birth/death token out of the free-text slug space, so the two variants
      can never collide on one character), emits the type assertion, a
      ``crm:P2_has_type`` link to the shared ``{uri_base}type/{kind}`` E55_Type
      individual, and a ``crm:P43_has_dimension`` link to its :class:`Dimension`.

    Exactly one variant must be supplied. A free-text ``label`` that slugs to
    empty raises :class:`~bookwright.golem.errors.EmptySlugError` (FR-021).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["CharacterFeature"]

    character_uri: URIRef
    label: str | None = None
    kind: BioKind | None = None
    year: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _exactly_one_variant(cls, data: dict[str, object]) -> dict[str, object]:
        # Runs *before* identity construction in ``model_post_init`` (which
        # builds the URI from the chosen variant), so the variant invariant is
        # enforced by a real ``ValidationError`` rather than the type-narrowing
        # assert at the bottom of this class. That assert is then never the line
        # that rejects bad input, so it stays correct under ``python -O``. ``data``
        # is always the raw kwargs dict: this frozen model is only ever built via
        # ``CharacterFeature(...)``, never re-validated from an existing instance.
        kind, label, year = data.get("kind"), data.get("label"), data.get("year")
        if kind is not None:
            # Biographical: a year is mandatory, a free-text label is forbidden.
            if label is not None:
                raise ValueError("biographical CharacterFeature must not also carry a `label`")
            if year is None:
                raise ValueError("biographical CharacterFeature requires a `year`")
        else:
            # Free-text: a label is mandatory; a stray `year` is forbidden rather
            # than silently dropped, since only the biographical variant emits it.
            if label is None:
                raise ValueError("CharacterFeature requires either `label` or (`kind` + `year`)")
            if year is not None:
                raise ValueError("free-text CharacterFeature must not carry a `year`")
        return data

    def model_post_init(self, __context: object) -> None:
        if self.kind is not None:
            # Biographical features live under a `bio/` sub-segment: a free-text
            # slug never contains `/`, so it can never collide with the
            # birth/death token on the same character (FR-021).
            self._uri = URIRef(f"{self.character_uri}/feature/bio/{self.kind}")
        else:
            assert self.label is not None  # guaranteed by _exactly_one_variant
            self._uri = URIRef(f"{self.character_uri}/feature/{make_slug(self.label)}")

    def to_triples(self) -> Iterable[Triple]:
        yield (self.uri, RDF.type, self.golem_class)
        if self.kind is not None:
            type_uri = URIRef(f"{self.uri_base}type/{self.kind}")
            yield (self.uri, HAS_TYPE, type_uri)
            yield (type_uri, RDF.type, CLASS_IRI["Type"])
            assert self.year is not None  # guaranteed by _exactly_one_variant
            dimension = Dimension(uri_base=self.uri_base, feature_uri=self.uri, year=self.year)
            yield (self.uri, HAS_DIMENSION, dimension.uri)
            yield from dimension.to_triples()
        else:
            yield (self.uri, RDFS.label, RdfLiteral(self.label))


class CharacterRole(GolemEntity):
    """A character-scoped narrative role (``golem:G11_Narrative_Role``).

    URI is ``{character.uri}/role/{slug(label)}``; emits the type assertion and
    the role text on ``rdfs:label``. Distinct from the top-level ``NarrativeRole``
    concept: this node is inlined under a character and is not in ``CONCEPTS``.

    When ``type_uri`` is set (iteration 030 — the role name matched a Greimas
    actant), it also emits a ``crm:P2_has_type`` link to that ``crm:E55_Type``
    term, the same typing shape the biographical feature variant uses. Its type
    provenance E13 is emitted by its owning :class:`Character`, not here, because
    only the character is a top-level mapped entity (research D4).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["NarrativeRole"]

    character_uri: URIRef
    label: str
    type_uri: URIRef | None = None

    def model_post_init(self, __context: object) -> None:
        self._uri = URIRef(f"{self.character_uri}/role/{make_slug(self.label)}")

    def to_triples(self) -> Iterable[Triple]:
        yield (self.uri, RDF.type, self.golem_class)
        yield (self.uri, RDFS.label, RdfLiteral(self.label))
        if self.type_uri is not None:
            yield (self.uri, HAS_TYPE, self.type_uri)
            yield (self.type_uri, RDF.type, CLASS_IRI["Type"])
