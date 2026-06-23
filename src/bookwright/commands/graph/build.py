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
from bookwright.errors import BookwrightError
from bookwright.io.errors import ProjectNotFoundError, SlugCollisionError
from bookwright.io.project import find_project_root
from bookwright.io.report import BuildReport
from bookwright.io.vocabularies import load_vocabulary

from .._envelope import EXIT_COLLISION, EXIT_CONFIG, emit_error, emit_json, invalid_manifest_payload
from .._graph import PIPELINE_CONFIG_FAULTS, build_project_graph
from . import app

#: build's exit-2 faults: project resolution plus the shared pipeline roster (D4).
_CONFIG_FAULTS: tuple[type[BookwrightError], ...] = (
    ProjectNotFoundError,
    *PIPELINE_CONFIG_FAULTS,
)


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
    except _CONFIG_FAULTS as exc:
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
    """Run the build, returning the report. Raises the fault-model exceptions.

    The pipeline body lives in :func:`bookwright.commands._graph.build_project_graph`
    (shared with ``bookwright status``, 020 research D1); this wrapper owns only
    project/manifest resolution.
    """
    project_root = find_project_root()
    manifest = Manifest.load(project_root / "manifest.toml")
    return build_project_graph(project_root, manifest).report


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
    if report.unresolved_references:
        console.print(f"{len(report.unresolved_references)} unresolved reference(s)")
    if report.sources or report.findings or report.anchors:
        console.print(
            f"research: {report.sources} source(s), "
            f"{report.findings} finding(s), {report.anchors} anchor(s)"
        )
    if report.research_warnings:
        console.print(f"{len(report.research_warnings)} unresolved research target(s):")
        for warning in report.research_warnings:
            console.print(f"  - {warning.path}: {warning.field} '{warning.name}' not in bible")
    _print_untyped_vocab_terms(console, report)


def _print_untyped_vocab_terms(console: Console, report: BuildReport) -> None:
    """Append the unrecognized-vocabulary-term block to the human summary (FR-002/006).

    One ``- {path}: {field} '{term}' is not a {vocabulary} term`` line per entry in
    envelope order, then one ``valid {vocabulary} terms: …`` enumeration **per distinct
    vocabulary** (not per entry), derived at render time from
    ``load_vocabulary(vocabulary).terms`` — never denormalized into the record. The
    enumeration is pre-sorted (``VocabularyIndex.terms``), so two builds render
    byte-identically (FR-016).
    """
    if not report.untyped_vocab_terms:
        return
    console.print(f"{len(report.untyped_vocab_terms)} unrecognized vocabulary term(s):")
    for warning in report.untyped_vocab_terms:
        console.print(
            f"  - {warning.path}: {warning.field} '{warning.term}' "
            f"is not a {warning.vocabulary} term"
        )
    seen: list[str] = []
    for warning in report.untyped_vocab_terms:
        if warning.vocabulary not in seen:
            seen.append(warning.vocabulary)
    for vocabulary in seen:
        terms = ", ".join(load_vocabulary(vocabulary).terms)
        console.print(f"  valid {vocabulary} terms: {terms}")
