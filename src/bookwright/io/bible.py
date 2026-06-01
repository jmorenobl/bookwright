"""Discover bible source files and map their frontmatter to GOLEM entities.

Type is determined by **location** (R2 / bible-format.md). The mapper passes
frontmatter values straight to the iteration-5 constructors — it never builds
feature/role/dimension nodes itself (data-model § 0/§ 3). It collects soft
warnings (``unknown_keys``, ``unresolved_participants``), skips files whose
frontmatter is unusable (FR-013), and raises on a slug collision (FR-014).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from rdflib.term import URIRef

from bookwright.golem import (
    AttributeAssignment,
    Character,
    EmptySlugError,
    NarrativeEvent,
    Setting,
    SocialRelationship,
)
from bookwright.golem.base import GolemEntity
from bookwright.golem.slug import make_slug

from .errors import InvalidFrontmatterError, SlugCollisionError
from .frontmatter import Frontmatter, parse_frontmatter
from .report import SkippedFile, UnknownKey, UnresolvedParticipant

CHARACTER_KEYS = frozenset({"name", "born", "died", "features", "narrative_roles"})
SETTING_KEYS = frozenset({"name"})
ITEM_KEYS = frozenset({"name", "participants"})
TIMELINE_TOP_KEYS = frozenset({"events"})
RELATIONSHIPS_TOP_KEYS = frozenset({"relationships"})

# A directory builder maps ``(frontmatter, relpath) → entity``; a collection
# factory maps ``(name, participants) → entity``. Typed so ``mypy --strict``
# checks every call site (rather than the previous ``Any`` escape hatch).
_Builder = Callable[[dict[str, Any], str], GolemEntity]
_Factory = Callable[[str, tuple[URIRef, ...]], GolemEntity]


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
    unresolved_participants: list[UnresolvedParticipant] = field(default_factory=list)

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
    tracker, and the ``slug → URI`` index into one object keeps each helper's
    signature small — the four used to be threaded positionally through every
    function.
    """

    project_root: Path
    result: MapResult
    collisions: _Collisions
    slug_index: dict[str, URIRef]


@dataclass(frozen=True)
class _DirSpec:
    """Per-concept config for a one-entity-per-file directory (characters/settings)."""

    directory: Path
    concept: str
    builder: _Builder
    allowed_keys: frozenset[str]
    index: bool  # whether built entities feed the participant-resolution index


@dataclass(frozen=True)
class _CollectionSpec:
    """Per-concept config for a single collection file (timeline/relationships)."""

    path: Path
    concept: str
    top_keys: frozenset[str]
    container: str
    factory: _Factory


def map_bible(project_root: Path, bible_dir: Path, uri_base: str) -> MapResult:
    """Map every recognised bible file under ``bible_dir`` to GOLEM entities.

    Characters and settings are one-entity-per-file; ``timeline.md`` /
    ``relationships.md`` are single collection files. Characters are constructed
    first so ``events:`` / ``relationships:`` participants resolve against a
    ``slug → URI`` index in a single pass.
    """
    ctx = _MapContext(
        project_root=project_root,
        result=MapResult(),
        collisions=_Collisions(),
        slug_index={},
    )

    _map_single_dir(
        ctx,
        _DirSpec(
            directory=bible_dir / "characters",
            concept="Character",
            builder=lambda meta, rp: _build_character(uri_base, meta),
            allowed_keys=CHARACTER_KEYS,
            index=True,
        ),
    )
    _map_single_dir(
        ctx,
        _DirSpec(
            directory=bible_dir / "settings",
            concept="Setting",
            builder=lambda meta, rp: Setting(uri_base=uri_base, name=_require_name(meta)),
            allowed_keys=SETTING_KEYS,
            index=False,
        ),
    )
    _map_collection(
        ctx,
        _CollectionSpec(
            path=bible_dir / "timeline.md",
            concept="NarrativeEvent",
            top_keys=TIMELINE_TOP_KEYS,
            container="events",
            factory=lambda name, participants: NarrativeEvent(
                uri_base=uri_base, name=name, participants=participants
            ),
        ),
    )
    _map_collection(
        ctx,
        _CollectionSpec(
            path=bible_dir / "relationships.md",
            concept="SocialRelationship",
            top_keys=RELATIONSHIPS_TOP_KEYS,
            container="relationships",
            factory=lambda name, participants: SocialRelationship(
                uri_base=uri_base, name=name, participants=participants
            ),
        ),
    )
    return ctx.result


def build_provenance(mapped: MappedEntity, uri_base: str) -> Iterable[AttributeAssignment]:
    """Mint one ``crm:E13_Attribute_Assignment`` per derived assertion (R6, FR-011).

    The identity assertion carries file-level provenance; an attribute whose
    originating frontmatter key is locatable carries a ``relpath:line`` source.
    """
    for assertion in mapped.entity.derived_assertions():
        line = mapped.key_lines.get(assertion.source_field) if assertion.source_field else None
        source = f"{mapped.relpath}:{line}" if line is not None else mapped.relpath
        yield AttributeAssignment(
            uri_base=uri_base,
            target=assertion.target,
            attribute=assertion.attribute,
            source=source,
        )


# --- internals --------------------------------------------------------------


def _relpath(path: Path, project_root: Path) -> str:
    return path.relative_to(project_root).as_posix()


def _require_name(metadata: dict[str, Any]) -> str:
    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        raise InvalidFrontmatterError("", "missing or empty `name`")
    return name


def _record_unknown_keys(
    ctx: _MapContext, metadata: dict[str, Any], allowed: frozenset[str], relpath: str
) -> None:
    for key in metadata:
        if key not in allowed:
            ctx.result.unknown_keys.append(UnknownKey(path=relpath, key=key))


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


def _map_single_dir(ctx: _MapContext, spec: _DirSpec) -> None:
    if not spec.directory.is_dir():
        return
    for path in sorted(spec.directory.glob("*.md")):
        relpath = _relpath(path, ctx.project_root)
        ctx.result.files_processed += 1
        frontmatter = _safe_parse(ctx, path, relpath)
        if frontmatter is None:
            continue
        try:
            entity = spec.builder(frontmatter.metadata, relpath)
            ctx.collisions.record(spec.concept, _slug_of(entity), relpath)
        except InvalidFrontmatterError as exc:
            ctx.result.skipped.append(SkippedFile(path=relpath, reason=exc.reason))
            continue
        except EmptySlugError as exc:
            ctx.result.skipped.append(SkippedFile(path=relpath, reason=exc.message))
            continue
        # Only record soft warnings once the file actually produced an entity, so a
        # subsequently skipped file never contributes `unknown_keys` (report stays
        # consistent: a skipped file shows up only under `skipped`).
        _record_unknown_keys(ctx, frontmatter.metadata, spec.allowed_keys, relpath)
        if spec.index:
            ctx.slug_index[_slug_of(entity)] = entity.uri
        ctx.result.mapped.append(
            MappedEntity(entity=entity, relpath=relpath, key_lines=frontmatter.key_lines)
        )


def _map_collection(ctx: _MapContext, spec: _CollectionSpec) -> None:
    if not spec.path.is_file():
        return
    relpath = _relpath(spec.path, ctx.project_root)
    ctx.result.files_processed += 1
    frontmatter = _safe_parse(ctx, spec.path, relpath)
    if frontmatter is None:
        return
    _record_unknown_keys(ctx, frontmatter.metadata, spec.top_keys, relpath)
    items = frontmatter.metadata.get(spec.container, [])
    if not isinstance(items, list):
        ctx.result.skipped.append(
            SkippedFile(path=relpath, reason=f"`{spec.container}` must be a list")
        )
        return
    for item in items:
        if not isinstance(item, dict):
            ctx.result.skipped.append(
                SkippedFile(path=relpath, reason=f"each `{spec.container}` item must be a mapping")
            )
            continue
        _map_collection_item(ctx, spec, item, relpath, frontmatter)


def _map_collection_item(
    ctx: _MapContext,
    spec: _CollectionSpec,
    item: dict[str, Any],
    relpath: str,
    frontmatter: Frontmatter,
) -> None:
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        ctx.result.skipped.append(
            SkippedFile(path=relpath, reason=f"a `{spec.container}` item is missing `name`")
        )
        return
    participants = _resolve_participants(ctx, item, name, relpath)
    try:
        entity = spec.factory(name, participants)
        ctx.collisions.record(spec.concept, make_slug(name), relpath)
    except EmptySlugError as exc:
        ctx.result.skipped.append(SkippedFile(path=relpath, reason=exc.message))
        return
    # Record soft warnings only after the item produced an entity (see _map_single_dir).
    _record_unknown_keys(ctx, item, ITEM_KEYS, relpath)
    ctx.result.mapped.append(
        MappedEntity(entity=entity, relpath=relpath, key_lines=frontmatter.key_lines)
    )


def _resolve_participants(
    ctx: _MapContext,
    item: dict[str, Any],
    entity_name: str,
    relpath: str,
) -> tuple[URIRef, ...]:
    raw = item.get("participants")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        # A scalar/mapping where a list was expected can't resolve to characters;
        # surface it as an unresolved reference (soft warning) instead of dropping
        # it silently. The owning event/relationship is still built.
        ctx.result.unresolved_participants.append(
            UnresolvedParticipant(path=relpath, entity=entity_name, name=str(raw))
        )
        return ()
    resolved: list[URIRef] = []
    for ref in raw:
        if not isinstance(ref, str):
            continue
        uri = ctx.slug_index.get(make_slug(ref))
        if uri is None:
            ctx.result.unresolved_participants.append(
                UnresolvedParticipant(path=relpath, entity=entity_name, name=ref)
            )
            continue
        resolved.append(uri)
    return tuple(resolved)


def _safe_parse(ctx: _MapContext, path: Path, relpath: str) -> Frontmatter | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # A non-UTF-8 or unreadable file is "unusable frontmatter" (FR-013): skip
        # it and keep building, exactly like a YAML error — never abort the build.
        ctx.result.skipped.append(SkippedFile(path=relpath, reason=f"unreadable file: {exc}"))
        return None
    try:
        return parse_frontmatter(text)
    except yaml.YAMLError as exc:
        ctx.result.skipped.append(
            SkippedFile(path=relpath, reason=f"malformed YAML frontmatter: {exc}")
        )
        return None


def _slug_of(entity: GolemEntity) -> str:
    slug = getattr(entity, "slug", None)
    return slug if isinstance(slug, str) else str(entity.uri)
