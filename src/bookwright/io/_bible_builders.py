"""Concrete builders, coercers, and the mapper's context/result records.

A behavior-preserving extraction from :mod:`bookwright.io.bible` (iteration 025):
``bible.py`` keeps the orchestration — discovering files and wiring per-concept
passes — while this module holds the leaf builders that turn one frontmatter
mapping into a GOLEM entity, the value coercers they share, and the mutable
context / immutable result records threaded through the whole map.

The dependency is **one-way**: ``bible.py`` imports these names; this module
imports nothing from ``bible.py`` (no cycle — Principle IX). It depends only on
``golem``, ``io.errors``, ``io.report``, and the stdlib.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rdflib.term import URIRef

from bookwright.golem import Character, EmptySlugError, NarrativeEvent, NarrativeLocation
from bookwright.golem.base import GolemEntity
from bookwright.golem.namespaces import TEMPORAL_RELATIONS
from bookwright.golem.slug import make_slug

from .errors import InvalidFrontmatterError, SlugCollisionError
from .report import SkippedFile, UnknownKey, UnresolvedReference

# The five qualitative temporal relations an event may declare (each a list of
# event names resolved against the timeline's own event index — research D11).
# Derived from the single source of truth so the keys never drift from the model;
# ``bible.py`` imports it to assemble ``EVENT_ITEM_KEYS``.
RELATION_KEYS: tuple[str, ...] = tuple(rel.name for rel in TEMPORAL_RELATIONS)

# A directory builder maps ``(frontmatter, relpath) → entity``; a collection
# builder maps an ``_ItemContext`` (name, resolved participants, the raw item, and
# the collection's own name→URI index) → entity. Typed so ``mypy --strict`` checks
# every call site (rather than the previous ``Any`` escape hatch).
_Builder = Callable[[dict[str, Any], str], GolemEntity]
_ItemBuilder = Callable[["_ItemContext"], GolemEntity]


@dataclass(frozen=True)
class MappedEntity:
    """One constructed entity paired with the source needed for provenance (R6)."""

    entity: GolemEntity
    relpath: str
    key_lines: dict[str, int]


@dataclass
class MapResult:
    """The outcome of mapping a project's bible to GOLEM entities."""

    mapped: list[MappedEntity] = field(default_factory=list)
    files_processed: int = 0
    skipped: list[SkippedFile] = field(default_factory=list)
    unknown_keys: list[UnknownKey] = field(default_factory=list)
    unresolved_references: list[UnresolvedReference] = field(default_factory=list)
    # ``make_slug(name) → URI`` for every character, setting, event and location — the
    # research ``bears_on``/``constrains`` targets (D11), distinct from participant
    # ``slug_index``.
    entity_index: dict[str, URIRef] = field(default_factory=dict)

    @property
    def entities(self) -> list[GolemEntity]:
        return [m.entity for m in self.mapped]


class _Collisions:
    """Tracks ``(concept, slug) → relpath`` to detect identifier collisions (FR-014)."""

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], str] = {}

    def record(self, concept: str, slug: str, relpath: str) -> None:
        prior = self._seen.get((concept, slug))
        if prior is not None and prior != relpath:
            raise SlugCollisionError(slug, prior, relpath)
        self._seen[(concept, slug)] = relpath


@dataclass
class _MapContext:
    """The mutable state every mapping helper shares (R3).

    Bundling ``project_root``, the accumulating ``result``, the collision
    tracker, and the resolution indices into one object keeps each helper's
    signature small — the four used to be threaded positionally through every
    function. ``settings_index`` is the settings-scoped name→URI index a
    location's ``setting:`` resolves against (iteration 025), kept separate from
    the character-scoped ``slug_index`` and the research ``entity_index``.
    """

    project_root: Path
    result: MapResult
    collisions: _Collisions
    slug_index: dict[str, URIRef]
    settings_index: dict[str, URIRef] = field(default_factory=dict)


@dataclass(frozen=True)
class _ItemContext:
    """Everything a collection builder needs for one item (R3)."""

    ctx: _MapContext
    item: dict[str, Any]
    name: str
    participants: tuple[URIRef, ...]
    relpath: str
    item_index: dict[str, URIRef]


def _require_name(metadata: dict[str, Any]) -> str:
    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        raise InvalidFrontmatterError("", "missing or empty `name`")
    return name


def _coerce_year(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidFrontmatterError("", f"`{field_name}` must be an integer year")
    return value


def _coerce_str_list(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise InvalidFrontmatterError("", f"`{field_name}` must be a list of strings")
    return tuple(value)


def _build_character(uri_base: str, metadata: dict[str, Any]) -> Character:
    name = _require_name(metadata)
    born = _coerce_year(metadata.get("born"), "born")
    died = _coerce_year(metadata.get("died"), "died")
    features = _coerce_str_list(metadata.get("features"), "features")
    roles = _coerce_str_list(metadata.get("narrative_roles"), "narrative_roles")
    return Character(
        uri_base=uri_base,
        name=name,
        born=born,
        died=died,
        features=features,
        narrative_roles=roles,
    )


def _build_event(uri_base: str, ic: _ItemContext) -> NarrativeEvent:
    """Construct a ``NarrativeEvent`` from a timeline item: interval + relations."""
    begin, end = _resolve_interval(ic)
    relations = {
        key: _resolve_refs(ic.ctx, ic.item.get(key), ic.item_index, ic.name, ic.relpath)
        for key in RELATION_KEYS
    }
    return NarrativeEvent(
        uri_base=uri_base,
        name=ic.name,
        participants=ic.participants,
        begin=begin,
        end=end,
        **relations,
    )


def _resolve_interval(ic: _ItemContext) -> tuple[int | None, int | None]:
    """Coerce ``begin`` / ``end`` / ``date`` to int years, enforcing exclusivity.

    ``date`` is a single-year shorthand (``begin == end``). Supplying ``date``
    alongside ``begin``/``end`` is a soft warning (``date`` ignored), like an
    unknown key — never an abort.
    """
    begin = _coerce_year(ic.item.get("begin"), "begin")
    end = _coerce_year(ic.item.get("end"), "end")
    date = _coerce_year(ic.item.get("date"), "date")
    if date is not None:
        if begin is not None or end is not None:
            # Mutually exclusive: keep begin/end, drop date, flag it softly.
            ic.ctx.result.unknown_keys.append(UnknownKey(path=ic.relpath, key="date"))
        else:
            return date, date
    return begin, end


def _resolve_refs(
    ctx: _MapContext,
    raw: Any,
    index: dict[str, URIRef],
    entity_name: str,
    relpath: str,
) -> tuple[URIRef, ...]:
    """Resolve a list of names against ``index`` (characters or sibling events).

    A non-list value, or a name absent from the index, is surfaced as an
    ``UnresolvedReference`` soft warning (no abort); the owning entity is built.
    """
    if raw is None:
        return ()
    if not isinstance(raw, list):
        ctx.result.unresolved_references.append(
            UnresolvedReference(path=relpath, entity=entity_name, name=str(raw))
        )
        return ()
    resolved: list[URIRef] = []
    for ref in raw:
        if not isinstance(ref, str):
            continue
        uri = index.get(make_slug(ref))
        if uri is None:
            ctx.result.unresolved_references.append(
                UnresolvedReference(path=relpath, entity=entity_name, name=ref)
            )
            continue
        resolved.append(uri)
    return tuple(resolved)


def _resolve_setting(
    ctx: _MapContext, metadata: dict[str, Any], entity_name: str, relpath: str
) -> URIRef | None:
    """Resolve an optional ``setting:`` against the settings-scoped index (FR-003/004).

    Absent / ``None`` / blank-or-whitespace → no edge. A non-string is unusable
    frontmatter (``InvalidFrontmatterError`` → the file is skipped). A present name
    that resolves yields the setting's URI (the ``dlp:generic-location`` target); a
    present name that does not resolve — including one that slugs to nothing — is a
    soft miss recorded as an ``UnresolvedReference`` (the location is still built,
    no edge, no abort).
    """
    value = metadata.get("setting")
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidFrontmatterError("", "`setting` must be a string")
    if not value.strip():
        return None
    try:
        slug = make_slug(value)
    except EmptySlugError:
        slug = None
    uri = ctx.settings_index.get(slug) if slug is not None else None
    if uri is None:
        ctx.result.unresolved_references.append(
            UnresolvedReference(path=relpath, entity=entity_name, name=value)
        )
        return None
    return uri


def _build_location(
    uri_base: str, ctx: _MapContext, metadata: dict[str, Any], relpath: str
) -> NarrativeLocation:
    """Build a ``NarrativeLocation`` (G13) from ``name`` + optional ``setting`` (FR-001/002)."""
    name = _require_name(metadata)
    # Validate the name slugs *before* resolving ``setting:``, so an unsluggable name
    # aborts (→ the file is skipped) without ``_resolve_setting`` first recording a
    # stray unresolved-reference warning for a file that produces no entity. Keeps
    # the invariant that a skipped file appears only under ``skipped``.
    make_slug(name)
    setting = _resolve_setting(ctx, metadata, name, relpath)
    return NarrativeLocation(uri_base=uri_base, name=name, setting=setting)
