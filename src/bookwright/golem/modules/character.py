"""Character module: agents and objects of the storyworld (GOLEM § character)."""

from __future__ import annotations

from typing import ClassVar

from rdflib.term import URIRef

from bookwright.golem.base import SluggedEntity
from bookwright.golem.namespaces import CLASS_IRI


class Character(SluggedEntity):
    """A character (``golem:G1_Character``). Identity only in v0."""

    golem_class: ClassVar[URIRef] = CLASS_IRI["Character"]
    path_segment: ClassVar[str] = "character"


class Object(SluggedEntity):
    """A storyworld object (``golem:G16_Object``). Identity only in v0."""

    golem_class: ClassVar[URIRef] = CLASS_IRI["Object"]
    path_segment: ClassVar[str] = "object"
