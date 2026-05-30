"""Relationship module: social relationships and the roles within them."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import GolemEntity, SluggedEntity, Triple, ref_uri
from bookwright.golem.namespaces import CLASS_IRI, PARTICIPANT, REFERS_TO


class SocialRelationship(SluggedEntity):
    """A social relationship (``golem:G4_Social_Relationship``).

    Each participant is linked by one ``dlp:participant`` triple (FR-015).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["SocialRelationship"]
    path_segment: ClassVar[str] = "relationship"

    participants: tuple[GolemEntity | URIRef, ...] = ()

    def to_triples(self) -> Iterable[Triple]:
        yield from super().to_triples()
        for participant in self.participants:
            yield (self.uri, PARTICIPANT, ref_uri(participant))


class RelationshipRole(SluggedEntity):
    """A relationship role (``golem:G6_Relationship_Role``).

    When set, the role refers to its owning relationship (``crm:P67_refers_to``).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["RelationshipRole"]
    path_segment: ClassVar[str] = "relationship-role"

    relationship: GolemEntity | URIRef | None = None

    def to_triples(self) -> Iterable[Triple]:
        yield from super().to_triples()
        if self.relationship is not None:
            yield (self.uri, REFERS_TO, ref_uri(self.relationship))
