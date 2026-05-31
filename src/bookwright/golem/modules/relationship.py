"""Relationship module: social relationships and the roles within them."""

from __future__ import annotations

from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, GolemEntity, SluggedEntity
from bookwright.golem.namespaces import CLASS_IRI, PARTICIPANT, REFERS_TO


class SocialRelationship(SluggedEntity):
    """A social relationship (``golem:G4_Social_Relationship``).

    Each participant is linked by one ``dlp:participant`` triple (FR-015).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["SocialRelationship"]
    path_segment: ClassVar[str] = "relationship"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (
        CrossRef("participants", PARTICIPANT, multi=True),
    )

    participants: tuple[GolemEntity | URIRef, ...] = ()


class RelationshipRole(SluggedEntity):
    """A relationship role (``golem:G6_Relationship_Role``).

    When set, the role refers to its owning relationship (``crm:P67_refers_to``).
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["RelationshipRole"]
    path_segment: ClassVar[str] = "relationship-role"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (CrossRef("relationship", REFERS_TO),)

    relationship: GolemEntity | URIRef | None = None
