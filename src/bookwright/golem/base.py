"""The frozen-entity base: deterministic identity + the rdf:type triple.

Every GOLEM concept is an immutable Pydantic v2 model (research D1). Identity is
computed once, in ``model_post_init`` — which runs *after* validation, so an
:class:`~bookwright.golem.errors.EmptySlugError` raised while slugging a name
propagates unwrapped (not folded into a ``pydantic.ValidationError``).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar, NamedTuple

from pydantic import BaseModel, ConfigDict, PrivateAttr
from rdflib.namespace import RDF, XSD
from rdflib.term import Literal, URIRef

from bookwright.golem.slug import make_slug

Triple = tuple[URIRef, URIRef, URIRef | Literal]
"""An rdflib triple emitted by :meth:`GolemEntity.to_triples`."""


def ref_uri(ref: GolemEntity | URIRef) -> URIRef:
    """Resolve a cross-reference target to the URIRef used in a linking triple."""
    return ref.uri if isinstance(ref, GolemEntity) else ref


class CrossRef(NamedTuple):
    """A declarative cross-reference edge: one field → its linking predicate (FR-015).

    Concepts list these in :attr:`GolemEntity.cross_refs` instead of hand-rolling
    a ``to_triples`` override, so the base emits every edge uniformly and a new
    concept can never forget to chain the ``rdf:type`` assertion.

    - ``multi``: the field is a tuple; emit one triple per item, in tuple order.
    - ``literal``: emit the field value verbatim as an ``xsd:string`` (e.g. a
      source path), not a resolved reference.
    - ``owned``: the targets are sub-nodes this entity owns rather than peer
      entities serialized in their own right; after each link triple, chain the
      target's own ``to_triples()`` so the whole sub-tree is emitted here. (Used
      with ``multi`` — a character owns its feature / role nodes.)
    - otherwise the field is a single optional reference, omitted when ``None``.
    """

    attr: str
    predicate: URIRef
    multi: bool = False
    literal: bool = False
    owned: bool = False


class GolemEntity(BaseModel):
    """Abstract base for every GOLEM concept.

    Subclasses set the class-level ``golem_class`` (rdf:type target) and
    ``path_segment`` (FR-004), and provide a token via ``_build_token``.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        arbitrary_types_allowed=True,
    )

    uri_base: str

    golem_class: ClassVar[URIRef]
    path_segment: ClassVar[str]
    cross_refs: ClassVar[tuple[CrossRef, ...]] = ()

    _uri: URIRef = PrivateAttr()

    def model_post_init(self, __context: object) -> None:
        self._uri = URIRef(f"{self.uri_base}{self.path_segment}/{self._build_token()}")

    def _build_token(self) -> str:  # pragma: no cover - overridden by every concrete class
        raise NotImplementedError

    @property
    def uri(self) -> URIRef:
        """The deterministic, immutable identifier (FR-003/004/007)."""
        return self._uri

    def to_triples(self) -> Iterable[Triple]:
        """Yield this entity's triples: the ``rdf:type`` assertion (FR-008, always
        first) followed by every edge declared in :attr:`cross_refs` (FR-015) —
        and, for an ``owned`` edge, the target sub-node's own triples chained
        immediately after its link triple.

        Concepts customize emission declaratively via ``cross_refs`` only when
        their edges are URIRef references or ``xsd:string`` literals — the two
        shapes this method knows how to emit. Concepts whose emission falls
        outside that path override ``to_triples`` deliberately: ``CharacterFeature``
        and ``CharacterRole`` emit an ``rdfs:label`` plain literal (and the former
        a discriminator-keyed sub-tree), and ``Dimension`` emits a typed
        ``xsd:gYear`` literal — none of which ``cross_refs`` can express.
        """
        yield (self.uri, RDF.type, self.golem_class)
        for ref in self.cross_refs:
            value = getattr(self, ref.attr)
            if ref.multi:
                for item in value:
                    yield (self.uri, ref.predicate, ref_uri(item))
                    if ref.owned:
                        yield from item.to_triples()
            elif ref.literal:
                yield (self.uri, ref.predicate, Literal(value, datatype=XSD.string))
            elif value is not None:
                yield (self.uri, ref.predicate, ref_uri(value))


class SluggedEntity(GolemEntity):
    """A named concept whose identity token is the ASCII slug of its name."""

    name: str

    _slug: str = PrivateAttr()

    def model_post_init(self, __context: object) -> None:
        self._slug = make_slug(self.name)
        super().model_post_init(__context)

    def _build_token(self) -> str:
        return self._slug

    @property
    def slug(self) -> str:
        """The slugged token of :attr:`name` (FR-005)."""
        return self._slug
