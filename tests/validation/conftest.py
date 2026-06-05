"""Shared fixtures + scaffolding for the validation suite.

A project-scaffold builder plus per-validator violation/clean helpers. Importable
by the test modules (``from tests.validation.conftest import ...``) so each story's
tests stay self-contained while sharing one realistic project shape.
"""

from __future__ import annotations

import textwrap
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest
from rdflib.namespace import RDF
from rdflib.term import Literal as RdfLiteral
from rdflib.term import URIRef

from bookwright.core.manifest import Manifest
from bookwright.golem.modules.event import NarrativeEvent
from bookwright.golem.modules.feature import gyear_literal
from bookwright.golem.namespaces import (
    BEGIN_OF_BEGIN,
    BW_ACCESS_DATE,
    BW_AUTHOR,
    BW_CONSTRAINS,
    BW_ORIGINAL_LANGUAGE,
    BW_ORIGINAL_QUOTE,
    BW_PROMOTES,
    BW_REFERENCE,
    BW_RELIABILITY,
    BW_RELIABILITY_JUSTIFICATION,
    BW_SUPPORTED_BY,
    BW_TRANSLATION,
    CLASS_IRI,
    E52_TIME_SPAN,
    END_OF_END,
    HAS_TIME_SPAN,
    HAS_TYPE,
    RELIABILITY_IRI,
    SOURCE_TYPE_IRI,
)
from bookwright.indexers import RdflibIndexer
from bookwright.io.bible import build_provenance, map_bible
from bookwright.validation.base import ValidationContext

URI_BASE = "https://example.org/novel/"

_MANIFEST = """\
[bookwright]
cli_version_min = "0.0.1"
schema_version = "1.1"
manifest_version = "1"
uri_base = "{uri_base}"

[book]
title = "Novel"
type = "novel"
language = "es"
authors = ["Autora"]

[integration]
key = "claude"
skills_dir = ".claude/skills/"
"""


def _validators_block(
    enabled: Iterable[str] | None,
    disabled: Iterable[str] | None,
    custom: Iterable[str] | None,
) -> str:
    if enabled is None and disabled is None and custom is None:
        return ""

    def _arr(values: Iterable[str] | None) -> str:
        items = ", ".join(f'"{v}"' for v in (values or ()))
        return f"[{items}]"

    return (
        "\n[validators]\n"
        f"enabled = {_arr(enabled)}\n"
        f"disabled = {_arr(disabled)}\n"
        f"custom = {_arr(custom)}\n"
    )


def write_project(  # noqa: PLR0913 — a flexible scaffold helper; keyword-only knobs
    root: Path,
    *,
    characters: Iterable[str] = (),
    settings: Iterable[str] = (),
    timeline: str | None = None,
    relationships: str | None = None,
    manuscript: Mapping[str, str] | None = None,
    constitution: str | None = None,
    enabled: Iterable[str] | None = None,
    disabled: Iterable[str] | None = None,
    custom: Iterable[str] | None = None,
) -> Path:
    """Create a project tree under ``root`` and return it.

    ``characters`` / ``settings`` are names (one bible file each); ``timeline`` /
    ``relationships`` / ``constitution`` are raw file bodies; ``manuscript`` maps a
    relpath (under ``manuscript/``) to its text. The ``manuscript/`` directory always
    exists so the layout is valid.
    """
    root.mkdir(parents=True, exist_ok=True)
    block = _validators_block(enabled, disabled, custom)
    (root / "manifest.toml").write_text(
        _MANIFEST.format(uri_base=URI_BASE) + block, encoding="utf-8"
    )

    manuscript_dir = root / "manuscript"
    manuscript_dir.mkdir(exist_ok=True)
    for relpath, text in (manuscript or {}).items():
        target = manuscript_dir / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(text), encoding="utf-8")

    bible = root / "bible"
    (bible / "characters").mkdir(parents=True, exist_ok=True)
    (bible / "settings").mkdir(parents=True, exist_ok=True)
    for name in characters:
        slug = name.lower().replace(" ", "-")
        (bible / "characters" / f"{slug}.md").write_text(
            f'---\nname: "{name}"\n---\n', encoding="utf-8"
        )
    for name in settings:
        slug = name.lower().replace(" ", "-")
        (bible / "settings" / f"{slug}.md").write_text(
            f'---\nname: "{name}"\n---\n', encoding="utf-8"
        )
    if timeline is not None:
        (bible / "timeline.md").write_text(textwrap.dedent(timeline), encoding="utf-8")
    if relationships is not None:
        (bible / "relationships.md").write_text(textwrap.dedent(relationships), encoding="utf-8")
    if constitution is not None:
        (bible / "constitution.md").write_text(textwrap.dedent(constitution), encoding="utf-8")

    return root


def load_context(root: Path) -> ValidationContext:
    """A :class:`ValidationContext` over a scaffolded project."""
    return ValidationContext(root=root, manifest=Manifest.load(root / "manifest.toml"))


def build_indexer(root: Path) -> RdflibIndexer:
    """Map the bible to GOLEM entities + provenance into a fresh in-memory engine."""
    manifest = Manifest.load(root / "manifest.toml")
    uri_base = manifest.bookwright.uri_base
    result = map_bible(root, root / manifest.paths.bible, uri_base)
    engine = RdflibIndexer()
    for mapped in result.mapped:
        for triple in mapped.entity.to_triples():
            engine.add_triple(*triple)
        for assignment in build_provenance(mapped, uri_base):
            for triple in assignment.to_triples():
                engine.add_triple(*triple)
    return engine


def build_and_save_graph(root: Path) -> Path:
    """Build the graph and serialize it to ``bible/graph.ttl`` (for command tests)."""
    manifest = Manifest.load(root / "manifest.toml")
    graph_path = root / manifest.paths.graph
    build_indexer(root).save(graph_path)
    return graph_path


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    """An empty directory to scaffold a project into."""
    return tmp_path / "novel"


# --- Research-aware graph builder (factual_anchor suite) ---------------------
#
# A hand-built ``bw:``/``crm:`` graph (defense-in-depth: it never round-trips
# through the iteration-12 reader, so the validator is exercised against graphs
# the reader could not produce, e.g. an incomplete source). Predicates come from
# the ``golem.namespaces`` constants — never hardcoded IRI strings — so the
# scaffold tracks the vocabulary the same way production code does.


def graph_uri(suffix: str) -> str:
    """The absolute project URI for a relative ``suffix`` (``"anchor/a1"`` …)."""
    return f"{URI_BASE}{suffix}"


# Facet key → its source predicate. ``translation`` is conditional (emitted only
# when the source language differs from the book language), so it is **not** in
# :data:`CORE_FACETS`; a well-formed same-language source carries the eight core
# facets and no translation.
_FACET_PREDICATE: dict[str, URIRef] = {
    "reference": BW_REFERENCE,
    "author": BW_AUTHOR,
    "original_language": BW_ORIGINAL_LANGUAGE,
    "type": HAS_TYPE,
    "reliability": BW_RELIABILITY,
    "reliability_justification": BW_RELIABILITY_JUSTIFICATION,
    "access_date": BW_ACCESS_DATE,
    "original_quote": BW_ORIGINAL_QUOTE,
    "translation": BW_TRANSLATION,
}
CORE_FACETS: tuple[str, ...] = tuple(f for f in _FACET_PREDICATE if f != "translation")
ALL_FACETS: tuple[str, ...] = tuple(_FACET_PREDICATE)


@dataclass(frozen=True)
class SourceSpec:
    """One supporting source, hand-built with a selectable subset of facets.

    ``facets`` is which facet predicates to emit (default: the eight core facets,
    i.e. a well-formed same-language source). ``reliability`` is the rating value
    emitted only when ``"reliability"`` is among ``facets`` (``None`` ⇒ unrated even
    if present — used to test the no-double-label rule); ``original_language`` is the
    value of the ``bw:originalLanguage`` facet (drives translation conditionality).
    """

    suffix: str = "source/s1"
    facets: tuple[str, ...] = CORE_FACETS
    reliability: str | None = "alta"
    original_language: str = "es"


@dataclass(frozen=True)
class AnchorSpec:
    """One anchor and its promoted finding, hand-built into the graph.

    ``finding_present`` controls whether the promoted finding node exists (a node
    with no describing triple is *absent* from the graph — the R4/R1 interplay).
    ``constrains`` is the absolute target URI, or ``None`` for a dropped link (no
    ``bw:constrains`` triple). ``span`` is the optional ``(begin, end)`` time-span.
    """

    suffix: str = "anchor/a1"
    finding_suffix: str = "finding/f1"
    finding_present: bool = True
    sources: tuple[SourceSpec, ...] = ()
    constrains: str | None = None
    span: tuple[int | None, int | None] | None = None


def _facet_object(facet: str, source: SourceSpec) -> URIRef | RdfLiteral:
    """The object emitted for ``facet`` — typed where the rule reads the value."""
    if facet == "reliability":
        assert source.reliability is not None  # only emitted when rated
        return RELIABILITY_IRI[source.reliability]
    if facet == "type":
        return SOURCE_TYPE_IRI["primaria"]
    if facet == "original_language":
        return RdfLiteral(source.original_language)
    return RdfLiteral(f"{facet}-value")


def _add_source(engine: RdflibIndexer, finding_uri: str, source: SourceSpec) -> None:
    # IRI-valued objects MUST be ``URIRef`` — a plain ``str`` object coerces to a
    # ``Literal`` (see ``RdflibIndexer.add_triple``) and would break every join.
    # Only the requested facet predicates are emitted: a source with ``facets=()``
    # carries no describing triple at all (the dangling-supportedBy edge case).
    source_uri = graph_uri(source.suffix)
    engine.add_triple(finding_uri, str(BW_SUPPORTED_BY), URIRef(source_uri))
    for facet in source.facets:
        if facet == "reliability" and source.reliability is None:
            continue  # an "unrated" source: predicate omitted on purpose
        engine.add_triple(source_uri, str(_FACET_PREDICATE[facet]), _facet_object(facet, source))


def add_anchor(engine: RdflibIndexer, anchor: AnchorSpec) -> str:
    """Hand-build one :class:`AnchorSpec` into ``engine``; return the anchor URI."""
    anchor_uri = graph_uri(anchor.suffix)
    finding_uri = graph_uri(anchor.finding_suffix)
    engine.add_triple(anchor_uri, str(RDF.type), CLASS_IRI["AttributeAssignment"])
    engine.add_triple(anchor_uri, str(BW_PROMOTES), URIRef(finding_uri))
    if anchor.finding_present:
        engine.add_triple(finding_uri, str(RDF.type), CLASS_IRI["AttributeAssignment"])
        for source in anchor.sources:
            _add_source(engine, finding_uri, source)
    if anchor.constrains is not None:
        engine.add_triple(anchor_uri, str(BW_CONSTRAINS), URIRef(anchor.constrains))
    if anchor.span is not None:
        begin, end = anchor.span
        span_uri = f"{anchor_uri}/time-span"
        engine.add_triple(anchor_uri, str(HAS_TIME_SPAN), URIRef(span_uri))
        engine.add_triple(span_uri, str(RDF.type), E52_TIME_SPAN)
        if begin is not None:
            engine.add_triple(span_uri, str(BEGIN_OF_BEGIN), gyear_literal(begin))
        if end is not None:
            engine.add_triple(span_uri, str(END_OF_END), gyear_literal(end))
    return anchor_uri


def add_event(engine: RdflibIndexer, name: str, begin: int | None, end: int | None) -> str:
    """Add a ``G5_Narrative_Event`` with an interval; return its URI.

    Reuses the real :class:`NarrativeEvent` serialization so the event carries the
    exact typed-boundary shape ``load_intervals`` reads (no duplicated interval
    plumbing in the test harness).
    """
    event = NarrativeEvent(uri_base=URI_BASE, name=name, begin=begin, end=end)
    for triple in event.to_triples():
        engine.add_triple(*triple)
    return str(event.uri)


def add_present_entity(engine: RdflibIndexer, suffix: str) -> str:
    """Add a bare present narrative entity (one describing triple); return its URI."""
    entity_uri = graph_uri(suffix)
    engine.add_triple(entity_uri, str(RDF.type), CLASS_IRI["Character"])
    return entity_uri


def research_graph(*anchors: AnchorSpec) -> RdflibIndexer:
    """A fresh in-memory engine with ``anchors`` hand-built into it."""
    engine = RdflibIndexer()
    for anchor in anchors:
        add_anchor(engine, anchor)
    return engine


def research_context(root: Path, *, enabled: bool = True, min_reliability: str = "media") -> Path:
    """Scaffold a project whose ``[research]`` block sets ``enabled`` / threshold."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "manuscript").mkdir(exist_ok=True)
    block = (
        "\n[research]\n"
        f"enabled = {str(enabled).lower()}\n"
        f'min_reliability_for_anchor = "{min_reliability}"\n'
    )
    (root / "manifest.toml").write_text(
        _MANIFEST.format(uri_base=URI_BASE) + block, encoding="utf-8"
    )
    return root
