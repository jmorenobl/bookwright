"""Inference module: provenance for inferred attributes (CIDOC-CRM E13)."""

from __future__ import annotations

from typing import ClassVar

import uuid_utils
from pydantic import PrivateAttr
from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, GolemEntity
from bookwright.golem.namespaces import (
    ASSIGNED,
    ASSIGNED_ATTRIBUTE_TO,
    CLASS_IRI,
    REFERS_TO,
    USED_SPECIFIC_OBJECT,
)


class AttributeAssignment(GolemEntity):
    """A provenance record for an inferred attribute (``crm:E13_Attribute_Assignment``).

    Constructed without a ``name``: its identity token is a time-ordered
    ``uuid_utils.uuid7()`` generated once at construction and frozen, so two
    assignments created in sequence sort in creation order (FR-013, D3). The
    ``source`` path is stored and emitted verbatim as an ``xsd:string`` literal
    (FR-009, D7); ``premise`` is omitted from the triples when ``None``.
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["AttributeAssignment"]
    path_segment: ClassVar[str] = "assertion"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (
        CrossRef("target", ASSIGNED_ATTRIBUTE_TO),
        CrossRef("attribute", ASSIGNED),
        CrossRef("source", USED_SPECIFIC_OBJECT, literal=True),
        CrossRef("premise", REFERS_TO),
    )

    target: GolemEntity | URIRef
    attribute: GolemEntity | URIRef
    source: str
    premise: GolemEntity | URIRef | None = None

    _token: str = PrivateAttr()

    def model_post_init(self, __context: object) -> None:
        self._token = str(uuid_utils.uuid7())
        super().model_post_init(__context)

    def _build_token(self) -> str:
        return self._token
