"""Discover ``bible/research/`` files and map their front-matter to provenance entities.

The research analogue of :mod:`bookwright.io.bible` (design § 20.5/§ 20.7). It reads
``sources.md`` (the Source registry), every ``<topic>.md`` (findings + anchors) and
``_index.md`` (global open questions), and turns their YAML front-matter into the
frozen :class:`~bookwright.golem.modules.provenance.Source` /
:class:`~bookwright.golem.modules.provenance.Finding` /
:class:`~bookwright.golem.modules.provenance.Anchor` entities ``graph build`` then
serializes.

Fault model (deliberately **stricter** than the bible mapper — research D7): a
vocabulary violation, a missing required Source facet, a non-open finding without a
``claim``/``sources``, an ``anchors[].promotes`` naming an unknown finding, a
translation-rule violation, or malformed YAML raises
:class:`~bookwright.io.errors.ResearchError` and aborts the build with no graph. An
unresolved ``bears_on``/``constrains`` *narrative* target is the one **soft** miss
(D12): the link triple is omitted and a :class:`ResearchWarning` is recorded, the
build still succeeding — existence/kind checking is the iteration-15 validator's job.
An **absent or empty** ``bible/research/`` yields zero entities and never raises
(FR-015, SC-005).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from rdflib.term import URIRef

from bookwright.golem import Anchor, Finding, Source
from bookwright.golem.base import GolemEntity
from bookwright.golem.namespaces import RELIABILITY_IRI, SOURCE_TYPE_IRI
from bookwright.golem.slug import make_slug

from .errors import ResearchError
from .frontmatter import parse_frontmatter

SOURCES_FILE = "sources.md"
INDEX_FILE = "_index.md"

# Every facet a Source declares (research-format.md). ``translation`` is governed by
# the language rule (§ D6), not listed as plainly required here.
_SOURCE_FACETS = (
    "name",
    "reference",
    "author",
    "original_language",
    "type",
    "reliability",
    "reliability_justification",
    "access_date",
    "original_quote",
)


@dataclass(frozen=True)
class ResearchWarning:
    """A soft, unresolved ``bears_on``/``constrains`` narrative target (research D12).

    The link triple was omitted; the build still succeeds. ``field`` is
    ``"bears_on"`` or ``"constrains"``; ``name`` is the target that did not resolve
    in the bible ``entity_index``.
    """

    relpath: str
    field: str
    name: str


@dataclass(frozen=True)
class ResearchResult:
    """The outcome of mapping a project's ``bible/research/`` to provenance entities."""

    sources: tuple[Source, ...] = ()
    findings: tuple[Finding, ...] = ()
    anchors: tuple[Anchor, ...] = ()
    files_processed: int = 0
    warnings: tuple[ResearchWarning, ...] = ()

    @property
    def entities(self) -> tuple[GolemEntity, ...]:
        return (*self.sources, *self.findings, *self.anchors)


@dataclass
class _Accumulator:
    """Mutable state threaded through the mapping passes."""

    project_root: Path
    uri_base: str
    book_language: str
    bible_index: Mapping[str, URIRef]
    timeline_uri: URIRef
    sources: list[Source] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    anchors: list[Anchor] = field(default_factory=list)
    warnings: list[ResearchWarning] = field(default_factory=list)
    files_processed: int = 0
    source_index: dict[str, URIRef] = field(default_factory=dict)

    def result(self) -> ResearchResult:
        return ResearchResult(
            sources=tuple(self.sources),
            findings=tuple(self.findings),
            anchors=tuple(self.anchors),
            files_processed=self.files_processed,
            warnings=tuple(self.warnings),
        )


def map_research(  # noqa: PLR0913 — the six parameters are the fixed contract surface (research-io.md)
    project_root: Path,
    research_dir: Path,
    uri_base: str,
    book_language: str,
    bible_index: Mapping[str, URIRef],
    timeline_uri: URIRef,
) -> ResearchResult:
    """Map ``research_dir`` to provenance entities (see module docstring).

    Files are processed in a deterministic order: ``sources.md`` first (so finding
    source references resolve in one pass), then the topic files in sorted order,
    then ``_index.md`` (global open questions).
    """
    acc = _Accumulator(
        project_root=project_root,
        uri_base=uri_base,
        book_language=book_language,
        bible_index=bible_index,
        timeline_uri=timeline_uri,
    )
    if not research_dir.is_dir():
        return acc.result()

    sources_path = research_dir / SOURCES_FILE
    if sources_path.is_file():
        _map_sources(acc, sources_path)

    for path in sorted(research_dir.glob("*.md")):
        if path.name in {SOURCES_FILE, INDEX_FILE}:
            continue
        _map_topic(acc, path)

    index_path = research_dir / INDEX_FILE
    if index_path.is_file():
        _map_index(acc, index_path)

    return acc.result()


# --- sources.md -------------------------------------------------------------


def _map_sources(acc: _Accumulator, path: Path) -> None:
    relpath = _relpath(acc, path)
    acc.files_processed += 1
    metadata = _load(acc, path, relpath)
    raw_sources = metadata.get("sources", [])
    if not isinstance(raw_sources, list):
        raise ResearchError(relpath, f"`sources` must be a list in {relpath}")
    for raw in raw_sources:
        if not isinstance(raw, dict):
            raise ResearchError(relpath, f"each `sources` item must be a mapping in {relpath}")
        source = _build_source(acc, raw, relpath)
        slug = make_slug(source.name)
        acc.source_index[slug] = source.uri
        acc.sources.append(source)


def _build_source(acc: _Accumulator, raw: dict[str, Any], relpath: str) -> Source:
    """Validate one source mapping and build the frozen :class:`Source` (D4/D6)."""
    for facet in _SOURCE_FACETS:
        if facet not in raw:
            raise ResearchError(
                relpath, f"source is missing required `{facet}` in {relpath}", facet
            )
    _reject_unknown_vocab(raw, relpath)
    try:
        source = Source(uri_base=acc.uri_base, **{k: raw[k] for k in raw})
    except ValidationError as exc:
        raise ResearchError(relpath, f"invalid source in {relpath}: {_first_error(exc)}") from exc
    return _apply_translation_rule(acc, source, relpath)


def _reject_unknown_vocab(raw: dict[str, Any], relpath: str) -> None:
    """Name the offending value for an out-of-vocabulary ``type``/``reliability``."""
    type_value = raw.get("type")
    if type_value not in SOURCE_TYPE_IRI:
        raise ResearchError(
            relpath, f"unknown source type {type_value!r} in {relpath}", str(type_value)
        )
    reliability = raw.get("reliability")
    if reliability not in RELIABILITY_IRI:
        raise ResearchError(
            relpath, f"unknown reliability {reliability!r} in {relpath}", str(reliability)
        )


def _apply_translation_rule(acc: _Accumulator, source: Source, relpath: str) -> Source:
    """Enforce the language-driven translation rule (research D6, SC-004).

    When the source language differs from the book's, ``translation`` is required;
    when they match, any supplied translation is dropped (never emitted).
    """
    if source.original_language != acc.book_language:
        if source.translation is None or not source.translation.strip():
            raise ResearchError(
                relpath,
                f"source {source.name!r} needs a `translation` (language "
                f"{source.original_language!r} ≠ book {acc.book_language!r}) in {relpath}",
                source.name,
            )
        return source
    if source.translation is not None:
        return source.model_copy(update={"translation": None})
    return source


# --- <topic>.md & _index.md -------------------------------------------------


def _map_topic(acc: _Accumulator, path: Path) -> None:
    relpath = _relpath(acc, path)
    acc.files_processed += 1
    metadata = _load(acc, path, relpath)
    finding_ids = _map_findings(acc, metadata.get("findings"), relpath, open_only=False)
    _map_anchors(acc, metadata.get("anchors"), relpath, finding_ids)


def _map_index(acc: _Accumulator, path: Path) -> None:
    relpath = _relpath(acc, path)
    acc.files_processed += 1
    metadata = _load(acc, path, relpath)
    _map_findings(acc, metadata.get("open_questions"), relpath, open_only=True)


def _map_findings(
    acc: _Accumulator, raw_findings: Any, relpath: str, *, open_only: bool
) -> dict[str, URIRef]:
    """Build the findings in one file; return its in-file ``id`` → URI map."""
    finding_ids: dict[str, URIRef] = {}
    if raw_findings is None:
        return finding_ids
    if not isinstance(raw_findings, list):
        raise ResearchError(relpath, f"`findings` must be a list in {relpath}")
    for raw in raw_findings:
        if not isinstance(raw, dict):
            raise ResearchError(relpath, f"each finding must be a mapping in {relpath}")
        identifier, finding = _build_finding(acc, raw, relpath, open_only=open_only)
        finding_ids[identifier] = finding.uri
        acc.findings.append(finding)
    return finding_ids


def _build_finding(
    acc: _Accumulator, raw: dict[str, Any], relpath: str, *, open_only: bool
) -> tuple[str, Finding]:
    identifier = raw.get("id")
    if not isinstance(identifier, str) or not identifier.strip():
        raise ResearchError(relpath, f"a finding is missing its `id` in {relpath}")
    is_open = bool(raw.get("open", False)) or open_only
    claim = raw.get("claim")
    sources = _resolve_sources(acc, raw.get("sources"), relpath)
    if not is_open and (not isinstance(claim, str) or not claim.strip() or not sources):
        raise ResearchError(
            relpath,
            f"finding {identifier!r} needs a `claim` and at least one `source` in {relpath}",
            identifier,
        )
    bears_on = _resolve_narrative(acc, raw.get("bears_on"), "bears_on", relpath)
    finding = Finding(
        uri_base=acc.uri_base,
        claim=claim if isinstance(claim, str) and claim.strip() else None,
        asserted_by=str(raw.get("asserted_by", "author")),
        bears_on=bears_on,
        sources=sources,
        open=is_open,
    )
    return identifier, finding


def _resolve_sources(acc: _Accumulator, raw_sources: Any, relpath: str) -> tuple[URIRef, ...]:
    if raw_sources is None:
        return ()
    if not isinstance(raw_sources, list):
        raise ResearchError(relpath, f"`sources` must be a list of source names in {relpath}")
    resolved: list[URIRef] = []
    for name in raw_sources:
        uri = acc.source_index.get(make_slug(str(name)))
        if uri is None:
            raise ResearchError(relpath, f"unknown source {name!r} in {relpath}", str(name))
        resolved.append(uri)
    return tuple(resolved)


def _map_anchors(
    acc: _Accumulator, raw_anchors: Any, relpath: str, finding_ids: Mapping[str, URIRef]
) -> None:
    if raw_anchors is None:
        return
    if not isinstance(raw_anchors, list):
        raise ResearchError(relpath, f"`anchors` must be a list in {relpath}")
    for raw in raw_anchors:
        if not isinstance(raw, dict):
            raise ResearchError(relpath, f"each anchor must be a mapping in {relpath}")
        acc.anchors.append(_build_anchor(acc, raw, relpath, finding_ids))


def _build_anchor(
    acc: _Accumulator, raw: dict[str, Any], relpath: str, finding_ids: Mapping[str, URIRef]
) -> Anchor:
    promotes_id = raw.get("promotes")
    if not isinstance(promotes_id, str) or promotes_id not in finding_ids:
        raise ResearchError(
            relpath,
            f"anchor `promotes` an unknown finding {promotes_id!r} in {relpath}",
            str(promotes_id),
        )
    if "constrains" not in raw:
        raise ResearchError(relpath, f"anchor is missing required `constrains` in {relpath}")
    constrains = _resolve_constrains(acc, raw.get("constrains"), relpath)
    begin, end = _resolve_span(raw, relpath)
    return Anchor(
        uri_base=acc.uri_base,
        promotes=finding_ids[promotes_id],
        constrains=constrains,
        begin=begin,
        end=end,
    )


def _resolve_constrains(acc: _Accumulator, raw: Any, relpath: str) -> URIRef | None:
    if isinstance(raw, str) and raw.strip() == "timeline":
        return acc.timeline_uri
    return _resolve_narrative(acc, raw, "constrains", relpath)


def _resolve_narrative(acc: _Accumulator, raw: Any, field_name: str, relpath: str) -> URIRef | None:
    """Resolve a narrative target via the bible index; a miss is a soft warning (D12)."""
    if raw is None:
        return None
    name = str(raw)
    uri = acc.bible_index.get(make_slug(name))
    if uri is None:
        acc.warnings.append(ResearchWarning(relpath=relpath, field=field_name, name=name))
        return None
    return uri


def _resolve_span(raw: dict[str, Any], relpath: str) -> tuple[int | None, int | None]:
    """Coerce ``begin``/``end``/``date`` to year ints (``date`` is begin == end)."""
    begin = _coerce_year(raw.get("begin"), "begin", relpath)
    end = _coerce_year(raw.get("end"), "end", relpath)
    date = _coerce_year(raw.get("date"), "date", relpath)
    if date is not None:
        if begin is not None or end is not None:
            raise ResearchError(
                relpath, f"anchor `date` is mutually exclusive with `begin`/`end` in {relpath}"
            )
        return date, date
    return begin, end


def _coerce_year(value: Any, key: str, relpath: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ResearchError(
            relpath, f"anchor `{key}` must be an integer year in {relpath}", str(value)
        )
    return value


# --- shared -----------------------------------------------------------------


def _relpath(acc: _Accumulator, path: Path) -> str:
    return path.relative_to(acc.project_root).as_posix()


def _load(acc: _Accumulator, path: Path, relpath: str) -> dict[str, Any]:
    """Read and parse a research file's front-matter; malformed YAML is fatal (D7)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ResearchError(relpath, f"cannot read {relpath}: {exc}") from exc
    try:
        return parse_frontmatter(text).metadata
    except yaml.YAMLError as exc:
        raise ResearchError(relpath, f"malformed YAML front-matter in {relpath}: {exc}") from exc


def _first_error(exc: ValidationError) -> str:
    """A compact, value-naming summary of the first pydantic validation error."""
    errors = exc.errors()
    if not errors:  # pragma: no cover — a pydantic ValidationError always carries ≥1 error
        return str(exc)
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    return f"{location}: {first.get('msg', '')}".strip(": ")
