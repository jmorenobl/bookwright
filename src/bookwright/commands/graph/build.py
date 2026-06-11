"""`bookwright graph build` — read the bible, build the graph, write Turtle.

Locates the project, resolves the manifest-selected engine, maps every
recognised bible file to GOLEM entities (with CIDOC provenance), and serializes
to ``bible/graph.ttl``. Fault model (R7, cli-graph.md): missing project /
directory / unknown engine → exit 2; slug collision → exit 3 (no graph); ≥ 1
skipped file → exit 4 (graph still written); clean build → exit 0.
"""

from __future__ import annotations

import typer
from rich.console import Console

from bookwright.core.errors import ManifestError
from bookwright.core.manifest import Manifest
from bookwright.golem.namespaces import timeline_uri
from bookwright.indexers import UnknownIndexerError, resolve_indexer
from bookwright.io.bible import build_provenance, map_bible
from bookwright.io.errors import (
    MissingDirectoryError,
    ProjectNotFoundError,
    ResearchError,
    SlugCollisionError,
)
from bookwright.io.manuscript import manuscript_present
from bookwright.io.project import find_project_root
from bookwright.io.report import BuildReport, ResearchTargetWarning
from bookwright.io.research import map_research

from .._envelope import emit_error, emit_json, invalid_manifest_payload
from . import app

EXIT_CONFIG = 2
EXIT_COLLISION = 3


@app.command("build")
def run(
    force: bool = typer.Option(
        False, "--force", help="Rebuild from scratch, ignoring any cache (v0: no-op)."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit the build report as one JSON document on stdout."
    ),
) -> None:
    """Build the project graph from the bible and write ``bible/graph.ttl``."""
    console = Console(stderr=True)
    try:
        report = _build()
    except ManifestError as exc:
        emit_error(invalid_manifest_payload(exc), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except (
        ProjectNotFoundError,
        MissingDirectoryError,
        UnknownIndexerError,
        ResearchError,
    ) as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except SlugCollisionError as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_COLLISION) from exc

    if json_output:
        emit_json(report.to_json())
    else:
        _print_summary(console, report)
    raise typer.Exit(report.exit_code)


def _build() -> BuildReport:
    """Run the build, returning the report. Raises the fault-model exceptions."""
    project_root = find_project_root()
    manifest = Manifest.load(project_root / "manifest.toml")

    bible_dir = project_root / manifest.paths.bible
    manuscript_dir = project_root / manifest.paths.manuscript
    if not bible_dir.is_dir():
        raise MissingDirectoryError("bible", str(bible_dir))
    if not manuscript_present(manuscript_dir):
        raise MissingDirectoryError("manuscript", str(manuscript_dir))

    engine_cls = resolve_indexer(manifest.bookwright.indexer)
    engine = engine_cls()

    uri_base = manifest.bookwright.uri_base
    result = map_bible(project_root, bible_dir, uri_base)

    for mapped in result.mapped:
        for triple in mapped.entity.to_triples():
            engine.add_triple(*triple)
        for assignment in build_provenance(mapped, uri_base):
            for triple in assignment.to_triples():
                engine.add_triple(*triple)

    # Research pass: map bible/research/ and feed its triples into the same engine
    # (one graph, one save — research D8). Research entities are already E13
    # reifications, so they are NOT routed through build_provenance.
    research = map_research(
        project_root,
        bible_dir / "research",
        uri_base,
        manifest.book.language,
        result.entity_index,
        timeline_uri(uri_base),
    )
    for entity in research.entities:
        for triple in entity.to_triples():
            engine.add_triple(*triple)

    graph_rel = manifest.paths.graph
    engine.save(project_root / graph_rel)

    return BuildReport(
        files_processed=result.files_processed + research.files_processed,
        entities=len(result.entities) + len(research.entities),
        triples=engine.count(),
        graph_path=graph_rel,
        skipped=tuple(result.skipped),
        unknown_keys=tuple(result.unknown_keys),
        unresolved_participants=tuple(result.unresolved_participants),
        sources=len(research.sources),
        findings=len(research.findings),
        anchors=len(research.anchors),
        research_warnings=tuple(
            ResearchTargetWarning(path=w.relpath, field=w.field, name=w.name)
            for w in research.warnings
        ),
    )


def _print_summary(console: Console, report: BuildReport) -> None:
    """Write the human build summary to stderr (one line per metric)."""
    console.print(
        f"processed {report.files_processed} files, "
        f"{report.entities} entities, {report.triples} triples → {report.graph_path}"
    )
    if report.skipped:
        console.print(f"skipped {len(report.skipped)} file(s):")
        for item in report.skipped:
            console.print(f"  - {item.path}: {item.reason}")
    if report.unknown_keys:
        console.print(f"{len(report.unknown_keys)} unknown frontmatter key(s) ignored")
    if report.unresolved_participants:
        console.print(f"{len(report.unresolved_participants)} unresolved participant reference(s)")
    if report.sources or report.findings or report.anchors:
        console.print(
            f"research: {report.sources} source(s), "
            f"{report.findings} finding(s), {report.anchors} anchor(s)"
        )
    if report.research_warnings:
        console.print(f"{len(report.research_warnings)} unresolved research target(s):")
        for warning in report.research_warnings:
            console.print(f"  - {warning.path}: {warning.field} '{warning.name}' not in bible")
