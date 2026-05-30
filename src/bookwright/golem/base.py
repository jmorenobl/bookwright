"""The frozen-entity base: deterministic identity + the rdf:type triple.

Every GOLEM concept is an immutable Pydantic v2 model (research D1). Identity is
computed once, in ``model_post_init`` — which runs *after* validation, so an
:class:`~bookwright.golem.errors.EmptySlugError` raised while slugging a name
propagates unwrapped (not folded into a ``pydantic.ValidationError``).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, PrivateAttr
from rdflib.namespace import RDF
from rdflib.term import Literal, URIRef

from bookwright.golem.slug import make_slug

Triple = tuple[URIRef, URIRef, URIRef | Literal]
"""An rdflib triple emitted by :meth:`GolemEntity.to_triples`."""

EntityRef = "GolemEntity | URIRef"


def ref_uri(ref: GolemEntity | URIRef) -> URIRef:
    """Resolve a cross-reference target to the URIRef used in a linking triple."""
    return ref.uri if isinstance(ref, GolemEntity) else ref


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
        """Yield this entity's triples, always including the rdf:type assertion.

        Subclasses extend (call ``super().to_triples()``), never replace, the
        base type triple (FR-008).
        """
        yield (self.uri, RDF.type, self.golem_class)


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
