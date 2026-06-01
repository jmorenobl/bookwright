"""Character module: agents and objects of the storyworld (GOLEM § character)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from pydantic import PrivateAttr
from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, SluggedEntity, Triple
from bookwright.golem.modules.feature import BioKind, CharacterFeature, CharacterRole
from bookwright.golem.namespaces import CLASS_IRI, HAS_FEATURE, PLAYS


class Character(SluggedEntity):
    """A character (``golem:G1_Character``).

    Besides its identity, a character may carry the documented frontmatter:
    ``born`` / ``died`` years, free-text ``features``, and
    ``narrative_roles``. Each is materialized — once, deterministically, at
    construction — as a character-scoped node under
    :mod:`bookwright.golem.modules.feature`, linked by a frozen predicate
    (``golem:GP0_has_feature`` for features, ``edns:plays`` for roles). A
    character built with none of the four attributes has empty node tuples and
    therefore emits only its ``rdf:type`` assertion.
    """

    golem_class: ClassVar[URIRef] = CLASS_IRI["Character"]
    path_segment: ClassVar[str] = "character"
    cross_refs: ClassVar[tuple[CrossRef, ...]] = (
        CrossRef("_feature_nodes", HAS_FEATURE, multi=True),
        CrossRef("_role_nodes", PLAYS, multi=True),
    )

    born: int | None = None
    died: int | None = None
    features: tuple[str, ...] = ()
    narrative_roles: tuple[str, ...] = ()

    _feature_nodes: tuple[CharacterFeature, ...] = PrivateAttr(default=())
    _role_nodes: tuple[CharacterRole, ...] = PrivateAttr(default=())

    def model_post_init(self, __context: object) -> None:
        super().model_post_init(__context)  # fixes slug + identity URI first

        feature_nodes: list[CharacterFeature] = []
        if self.born is not None:
            feature_nodes.append(self._biographical("birth", self.born))
        if self.died is not None:
            feature_nodes.append(self._biographical("death", self.died))
        # Biographical features live under `feature/bio/…`, structurally apart
        # from the free-text slug space, so the only dedup needed here is between
        # identical free-text values (FR-021).
        seen: set[URIRef] = set()
        for text in self.features:
            node = CharacterFeature(uri_base=self.uri_base, character_uri=self.uri, label=text)
            if node.uri not in seen:  # dedup identical feature values (FR-021)
                seen.add(node.uri)
                feature_nodes.append(node)
        self._feature_nodes = tuple(feature_nodes)

        role_nodes: list[CharacterRole] = []
        seen_roles: set[URIRef] = set()
        for text in self.narrative_roles:
            role = CharacterRole(uri_base=self.uri_base, character_uri=self.uri, label=text)
            if role.uri not in seen_roles:  # dedup identical roles (FR-021)
                seen_roles.add(role.uri)
                role_nodes.append(role)
        self._role_nodes = tuple(role_nodes)

    def _biographical(self, kind: BioKind, year: int) -> CharacterFeature:
        return CharacterFeature(
            uri_base=self.uri_base, character_uri=self.uri, kind=kind, year=year
        )

    def to_triples(self) -> Iterable[Triple]:
        # The rdf:type assertion + the GP0_has_feature / edns:plays edges (via
        # cross_refs), then each nested node's own triples.
        yield from super().to_triples()
        for feature in self._feature_nodes:
            yield from feature.to_triples()
        for role in self._role_nodes:
            yield from role.to_triples()


class Object(SluggedEntity):
    """A storyworld object (``golem:G16_Object``). Identity only in v0."""

    golem_class: ClassVar[URIRef] = CLASS_IRI["Object"]
    path_segment: ClassVar[str] = "object"
