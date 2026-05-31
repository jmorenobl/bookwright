"""GOLEM domain model: typed, frozen entities with deterministic RDF identity.

Public surface: the thirteen GOLEM concept classes, the two
character-scoped attribute carriers (``CharacterFeature`` / ``Dimension`` —
exported for iteration-10 introspection but deliberately **not** in
``CONCEPTS``), the ``GolemError`` / ``EmptySlugError`` types, the ``CONCEPTS``
name→class registry, and ``to_turtle``. See
specs/005-golem-domain-model/contracts/golem_api.md for the stable contract.
"""

from __future__ import annotations

from bookwright.golem.errors import EmptySlugError, GolemError
from bookwright.golem.modules.character import Character, Object
from bookwright.golem.modules.event import NarrativeEvent, PsychologicalState
from bookwright.golem.modules.feature import CharacterFeature, Dimension
from bookwright.golem.modules.inference import AttributeAssignment
from bookwright.golem.modules.narrative import (
    NarrativeFunction,
    NarrativeRole,
    NarrativeSequence,
    NarrativeUnit,
)
from bookwright.golem.modules.relationship import RelationshipRole, SocialRelationship
from bookwright.golem.modules.setting import NarrativeLocation, Setting
from bookwright.golem.serialize import to_turtle

CONCEPTS: dict[str, type] = {
    "Character": Character,
    "Object": Object,
    "SocialRelationship": SocialRelationship,
    "RelationshipRole": RelationshipRole,
    "NarrativeEvent": NarrativeEvent,
    "PsychologicalState": PsychologicalState,
    "Setting": Setting,
    "NarrativeLocation": NarrativeLocation,
    "NarrativeUnit": NarrativeUnit,
    "NarrativeFunction": NarrativeFunction,
    "NarrativeRole": NarrativeRole,
    "NarrativeSequence": NarrativeSequence,
    "AttributeAssignment": AttributeAssignment,
}
"""Concept name → class, for downstream introspection (contract § surface)."""

__all__ = [
    "CONCEPTS",
    "AttributeAssignment",
    "Character",
    "CharacterFeature",
    "Dimension",
    "EmptySlugError",
    "GolemError",
    "NarrativeEvent",
    "NarrativeFunction",
    "NarrativeLocation",
    "NarrativeRole",
    "NarrativeSequence",
    "NarrativeUnit",
    "Object",
    "PsychologicalState",
    "RelationshipRole",
    "Setting",
    "SocialRelationship",
    "to_turtle",
]
