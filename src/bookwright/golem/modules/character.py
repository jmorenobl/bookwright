"""Character module: agents and objects of the storyworld (GOLEM § character)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import ClassVar, TypeVar

from pydantic import Field, PrivateAttr
from rdflib.term import URIRef

from bookwright.golem.base import CrossRef, DerivedAssertion, GolemEntity, SluggedEntity
from bookwright.golem.modules.feature import BioKind, CharacterFeature, CharacterRole
from bookwright.golem.namespaces import CLASS_IRI, HAS_FEATURE, PLAYS
from bookwright.golem.slug import make_slug

_Node = TypeVar("_Node", bound=GolemEntity)


def _dedup_nodes(texts: Iterable[str], factory: Callable[[str], _Node]) -> tuple[_Node, ...]:
    """Materialize one node per text, dropping later duplicates by URI (FR-021)."""
    nodes: list[_Node] = []
    seen: set[URIRef] = set()
    for text in texts:
        node = factory(text)
        if node.uri not in seen:
            seen.add(node.uri)
            nodes.append(node)
    return tuple(nodes)


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
        CrossRef("_feature_nodes", HAS_FEATURE, multi=True, owned=True),
        CrossRef("_role_nodes", PLAYS, multi=True, owned=True),
    )

    born: int | None = None
    died: int | None = None
    features: tuple[str, ...] = ()
    narrative_roles: tuple[str, ...] = ()
    # role-slug → Greimas actant term, supplied by the IO builder when Greimas is
    # active (iteration 030). Construction input only — it emits no triples itself;
    # it just lets each materialized role node carry its matched type. Empty ⇒ the
    # graph is byte-for-byte the pre-feature output (FR-008/SC-003).
    role_types: dict[str, URIRef] = Field(default_factory=dict)

    _feature_nodes: tuple[CharacterFeature, ...] = PrivateAttr(default=())
    _role_nodes: tuple[CharacterRole, ...] = PrivateAttr(default=())

    def model_post_init(self, __context: object) -> None:
        super().model_post_init(__context)  # fixes slug + identity URI first

        # Biographical features live under `feature/bio/…`, structurally apart
        # from the free-text slug space, so they never collide with free-text
        # values and only the free-text values need URI dedup (FR-021).
        biographical: list[CharacterFeature] = []
        if self.born is not None:
            biographical.append(self._biographical("birth", self.born))
        if self.died is not None:
            biographical.append(self._biographical("death", self.died))
        free_text = _dedup_nodes(
            self.features,
            lambda text: CharacterFeature(
                uri_base=self.uri_base, character_uri=self.uri, label=text
            ),
        )
        self._feature_nodes = (*biographical, *free_text)
        self._role_nodes = _dedup_nodes(
            self.narrative_roles,
            lambda text: CharacterRole(
                uri_base=self.uri_base,
                character_uri=self.uri,
                label=text,
                type_uri=self.role_types.get(make_slug(text)),
            ),
        )

    def _biographical(self, kind: BioKind, year: int) -> CharacterFeature:
        return CharacterFeature(
            uri_base=self.uri_base, character_uri=self.uri, kind=kind, year=year
        )

    @property
    def role_nodes(self) -> tuple[CharacterRole, ...]:
        """The character-scoped role nodes (``edns:plays`` targets), deduped by URI.

        Public read-only view of the materialized roles so callers outside this
        module (the outline units pass indexes them by slug) need not reach into
        the private attribute or recompute the ``{uri}/role/{slug}`` scheme."""
        return self._role_nodes

    def derived_assertions(self) -> Iterable[DerivedAssertion]:
        """One :class:`DerivedAssertion` per derived assertion, each tagged with
        the frontmatter key it came from so the indexer can resolve a source line:
        biographical features → ``born`` / ``died``, free-text → ``features``,
        roles → ``narrative_roles``. The identity assertion is file-level
        (``source_field`` ``None``).

        Overrides the declarative base because ``cross_refs`` cannot express this
        fan-out: a single ``_feature_nodes`` tuple carries three distinct origins
        (``born`` / ``died`` / ``features``), which only this class can untangle —
        a biographical node is recognised by its ``kind``."""
        yield DerivedAssertion(self.uri, self.uri, None)
        for feature in self._feature_nodes:
            field = {"birth": "born", "death": "died"}.get(feature.kind or "", "features")
            yield DerivedAssertion(self.uri, feature.uri, field)
        for role in self._role_nodes:
            yield DerivedAssertion(self.uri, role.uri, "narrative_roles")
            # A typed role gets a second assertion: the role node → its Greimas
            # term, so the typing link is reified as a ``crm:E13`` carrying the
            # character card's ``narrative_roles:`` locator (iteration 030, D4).
            if role.type_uri is not None:
                yield DerivedAssertion(role.uri, role.type_uri, "narrative_roles")


class Object(SluggedEntity):
    """A storyworld object (``golem:G16_Object``). Identity only in v0."""

    golem_class: ClassVar[URIRef] = CLASS_IRI["Object"]
    path_segment: ClassVar[str] = "object"
