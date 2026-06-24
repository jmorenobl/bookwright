"""The shared graph-build pipeline (`graph build` + `status`, 020 research D1).

The pipeline body extracted from ``commands/graph/build.py``: map the bible to
GOLEM entities (with CIDOC provenance), map ``bible/research/``, feed every
triple into one manifest-selected engine, and refresh the derived
``bible/graph.ttl`` cache. Both verbs consume this one implementation so the
graph they reason over can never diverge.

The fault model is the pipeline's own — :class:`MissingDirectoryError` for
absent prerequisites, ``UnknownIndexerError`` from engine resolution,
``SlugCollisionError`` / ``ResearchError`` from the mappers. Callers own
project/manifest resolution and the exit-code mapping (`graph build` per
cli-graph.md R7; `status` per 020 research D4/D5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bookwright.golem.namespaces import timeline_uri
from bookwright.indexers import Indexer, UnknownIndexerError, resolve_indexer
from bookwright.io.bible import feed_graph, map_bible
from bookwright.io.errors import MissingDirectoryError, ResearchError
from bookwright.io.manuscript import manuscript_present
from bookwright.io.outline import map_outline
from bookwright.io.report import BuildReport, ResearchTargetWarning
from bookwright.io.research import ResearchResult, map_research
from bookwright.io.vocabularies import load_active_vocabularies

if TYPE_CHECKING:
    from pathlib import Path

    from bookwright.core.manifest import Manifest
    from bookwright.errors import BookwrightError

#: The pipeline's own exit-2 fault classes, single-sourced beside the pipeline
#: that raises them so the two consuming except-ladders (`graph build`,
#: `status`) cannot drift apart on the same corpus (020 research D4).
PIPELINE_CONFIG_FAULTS: tuple[type[BookwrightError], ...] = (
    MissingDirectoryError,
    UnknownIndexerError,
    ResearchError,
)


def missing_prerequisite(root: Path, manifest: Manifest) -> tuple[str, Path] | None:
    """The first absent build prerequisite as ``(label, path)``, or ``None``.

    The single statement of "can this corpus build?": :func:`build_project_graph`
    raises ``MissingDirectoryError`` from it, and ``status`` branches to its
    degraded report on it (020 research D5) — one predicate, no drift.
    """
    bible_dir = root / manifest.paths.bible
    if not bible_dir.is_dir():
        return ("bible", bible_dir)
    manuscript_dir = root / manifest.paths.manuscript
    if not manuscript_present(manuscript_dir):
        return ("manuscript", manuscript_dir)
    return None


@dataclass(frozen=True)
class BuildOutcome:
    """Everything one pipeline run yields (data-model 020 § 5).

    ``report`` is what `graph build` emits; ``engine`` (already populated and
    saved) and ``research`` (carrying the authored identities, research D2) are
    what ``status`` aggregates over.
    """

    engine: Indexer
    report: BuildReport
    research: ResearchResult


def build_project_graph(root: Path, manifest: Manifest) -> BuildOutcome:
    """Build the project graph from the bible and write ``manifest.paths.graph``.

    Raises the fault-model exceptions documented in the module docstring; on
    success the returned engine holds the full graph and the Turtle cache on
    disk matches it.
    """
    missing = missing_prerequisite(root, manifest)
    if missing is not None:
        label, path = missing
        raise MissingDirectoryError(label, str(path))

    bible_dir = root / manifest.paths.bible
    engine_cls = resolve_indexer(manifest.bookwright.indexer)
    engine = engine_cls()

    uri_base = manifest.bookwright.uri_base
    # Load the active controlled vocabularies once (iteration 030): Greimas types
    # character roles in the bible pass, Propp types narrative functions in the
    # outline pass. With no vocabulary active both are ``None`` ⇒ no typing
    # (FR-008/SC-003).
    vocabs = load_active_vocabularies(manifest.vocabularies.active)
    result = map_bible(root, bible_dir, uri_base, greimas=vocabs.greimas)
    # Append the outline/units pass into the same MapResult (research D1): one result
    # to iterate, no merge, BuildReport counters aggregate the additions for free.
    map_outline(root, root / manifest.paths.outline, uri_base, result, propp=vocabs.propp)

    # Research pass: map bible/research/ then feed the whole corpus into the engine
    # via the shared assembly (one graph, one save — research D8). ``feed_graph`` is
    # the single triple-feeding both this verb and the validation corpus share, so the
    # two graphs cannot drift (048).
    research = map_research(
        root,
        bible_dir / "research",
        uri_base,
        manifest.book.language,
        result.entity_index,
        timeline_uri(uri_base),
    )
    feed_graph(engine, result, research, uri_base)

    graph_rel = manifest.paths.graph
    engine.save(root / graph_rel)

    report = BuildReport(
        files_processed=result.files_processed + research.files_processed,
        entities=len(result.entities) + len(research.entities),
        triples=engine.count(),
        graph_path=graph_rel,
        skipped=tuple(result.skipped),
        unknown_keys=tuple(result.unknown_keys),
        unresolved_references=tuple(result.unresolved_references),
        untyped_vocab_terms=tuple(result.untyped_vocab_terms),
        sources=len(research.sources),
        findings=len(research.findings),
        anchors=len(research.anchors),
        research_warnings=tuple(
            ResearchTargetWarning(path=w.relpath, field=w.field, name=w.name)
            for w in research.warnings
        ),
    )
    return BuildOutcome(engine=engine, report=report, research=research)
