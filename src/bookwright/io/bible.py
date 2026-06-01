"""Discover bible source files and map their frontmatter to GOLEM entities.

Type is determined by **location** (R2 / bible-format.md). The mapper passes
frontmatter values straight to the iteration-5 constructors — it never builds
feature/role/dimension nodes itself (data-model § 0/§ 3). It collects soft
warnings (``unknown_keys``, ``unresolved_participants``), skips files whose
frontmatter is unusable (FR-013), and raises on a slug collision (FR-014).
"""

from __future__ import annotations

from collections.abc import Iterable
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
from .frontmatter import parse_frontmatter
from .report import SkippedFile, UnknownKey, UnresolvedParticipant

CHARACTER_KEYS = frozenset({"name", "born", "died", "features", "narrative_roles"})
SETTING_KEYS = frozenset({"name"})
ITEM_KEYS = frozenset({"name", "participants"})
TIMELINE_TOP_KEYS = frozenset({"events"})
RELATIONSHIPS_TOP_KEYS = frozenset({"relationships"})


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


def map_bible(project_root: Path, bible_dir: Path, uri_base: str) -> MapResult:
    """Map every recognised bible file under ``bible_dir`` to GOLEM entities.

    Characters and settings are one-entity-per-file; ``timeline.md`` /
    ``relationships.md`` are single collection files. Characters are constructed
    first so ``events:`` / ``relationships:`` participants resolve against a
    ``slug → URI`` index in a single pass.
    """
    result = MapResult()
    collisions = _Collisions()
    slug_to_uri: dict[str, URIRef] = {}

    _map_single_dir(
        bible_dir / "characters",
        project_root,
        result,
        collisions,
        concept="Character",
        builder=lambda meta, rp: _build_character(uri_base, meta, rp, result),
        slug_index=slug_to_uri,
    )
    _map_single_dir(
        bible_dir / "settings",
        project_root,
        result,
        collisions,
        concept="Setting",
        builder=lambda meta, rp: Setting(uri_base=uri_base, name=_require_name(meta)),
        slug_index=None,
    )
    _map_collection(
        bible_dir / "timeline.md",
        project_root,
        result,
        collisions,
        concept="NarrativeEvent",
        top_keys=TIMELINE_TOP_KEYS,
        container="events",
        factory=lambda name, participants: NarrativeEvent(
            uri_base=uri_base, name=name, participants=participants
        ),
        slug_index=slug_to_uri,
    )
    _map_collection(
        bible_dir / "relationships.md",
        project_root,
        result,
        collisions,
        concept="SocialRelationship",
        top_keys=RELATIONSHIPS_TOP_KEYS,
        container="relationships",
        factory=lambda name, participants: SocialRelationship(
            uri_base=uri_base, name=name, participants=participants
        ),
        slug_index=slug_to_uri,
    )
    return result


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
    metadata: dict[str, Any], allowed: frozenset[str], relpath: str, result: MapResult
) -> None:
    for key in metadata:
        if key not in allowed:
            result.unknown_keys.append(UnknownKey(path=relpath, key=key))


def _build_character(
    uri_base: str, metadata: dict[str, Any], relpath: str, result: MapResult
) -> Character:
    name = _require_name(metadata)
    born = _coerce_year(metadata.get("born"), "born")
    died = _coerce_year(metadata.get("died"), "died")
    features = _coerce_str_list(metadata.get("features"), "features")
    roles = _coerce_str_list(metadata.get("narrative_roles"), "narrative_roles")
    _record_unknown_keys(metadata, CHARACTER_KEYS, relpath, result)
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


def _map_single_dir(  # noqa: PLR0913 - one cohesive mapping step; splitting hurts clarity
    directory: Path,
    project_root: Path,
    result: MapResult,
    collisions: _Collisions,
    *,
    concept: str,
    builder: Any,
    slug_index: dict[str, URIRef] | None,
) -> None:
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.md")):
        relpath = _relpath(path, project_root)
        result.files_processed += 1
        frontmatter = _safe_parse(path, relpath, result)
        if frontmatter is None:
            continue
        try:
            entity = builder(frontmatter.metadata, relpath)
            collisions.record(concept, _slug_of(entity), relpath)
        except InvalidFrontmatterError as exc:
            result.skipped.append(SkippedFile(path=relpath, reason=exc.reason))
            continue
        except EmptySlugError as exc:
            result.skipped.append(SkippedFile(path=relpath, reason=exc.message))
            continue
        if slug_index is not None:
            slug_index[_slug_of(entity)] = entity.uri
        result.mapped.append(
            MappedEntity(entity=entity, relpath=relpath, key_lines=frontmatter.key_lines)
        )


def _map_collection(  # noqa: PLR0913 - one cohesive mapping step; splitting hurts clarity
    path: Path,
    project_root: Path,
    result: MapResult,
    collisions: _Collisions,
    *,
    concept: str,
    top_keys: frozenset[str],
    container: str,
    factory: Any,
    slug_index: dict[str, URIRef],
) -> None:
    if not path.is_file():
        return
    relpath = _relpath(path, project_root)
    result.files_processed += 1
    frontmatter = _safe_parse(path, relpath, result)
    if frontmatter is None:
        return
    _record_unknown_keys(frontmatter.metadata, top_keys, relpath, result)
    items = frontmatter.metadata.get(container, [])
    if not isinstance(items, list):
        result.skipped.append(SkippedFile(path=relpath, reason=f"`{container}` must be a list"))
        return
    for item in items:
        if not isinstance(item, dict):
            result.skipped.append(
                SkippedFile(path=relpath, reason=f"each `{container}` item must be a mapping")
            )
            continue
        _map_collection_item(
            item, relpath, result, collisions, concept, container, factory, slug_index, frontmatter
        )


def _map_collection_item(  # noqa: PLR0913 - threads the shared mapping state
    item: dict[str, Any],
    relpath: str,
    result: MapResult,
    collisions: _Collisions,
    concept: str,
    container: str,
    factory: Any,
    slug_index: dict[str, URIRef],
    frontmatter: Any,
) -> None:
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        result.skipped.append(
            SkippedFile(path=relpath, reason=f"a `{container}` item is missing `name`")
        )
        return
    _record_unknown_keys(item, ITEM_KEYS, relpath, result)
    participants = _resolve_participants(item, name, relpath, result, slug_index)
    try:
        entity = factory(name, participants)
        collisions.record(concept, make_slug(name), relpath)
    except EmptySlugError as exc:
        result.skipped.append(SkippedFile(path=relpath, reason=exc.message))
        return
    result.mapped.append(
        MappedEntity(entity=entity, relpath=relpath, key_lines=frontmatter.key_lines)
    )


def _resolve_participants(
    item: dict[str, Any],
    entity_name: str,
    relpath: str,
    result: MapResult,
    slug_index: dict[str, URIRef],
) -> tuple[URIRef, ...]:
    raw = item.get("participants", [])
    if not isinstance(raw, list):
        return ()
    resolved: list[URIRef] = []
    for ref in raw:
        if not isinstance(ref, str):
            continue
        uri = slug_index.get(make_slug(ref))
        if uri is None:
            result.unresolved_participants.append(
                UnresolvedParticipant(path=relpath, entity=entity_name, name=ref)
            )
            continue
        resolved.append(uri)
    return tuple(resolved)


def _safe_parse(path: Path, relpath: str, result: MapResult) -> Any:
    try:
        return parse_frontmatter(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        result.skipped.append(
            SkippedFile(path=relpath, reason=f"malformed YAML frontmatter: {exc}")
        )
        return None


def _slug_of(entity: GolemEntity) -> str:
    slug = getattr(entity, "slug", None)
    return slug if isinstance(slug, str) else str(entity.uri)
