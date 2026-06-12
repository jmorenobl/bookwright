"""``bookwright status`` — derived project state + deterministic next actions.

Rebuilds the graph from the corpus via the shared pipeline (recomputation IS the
freshness mechanism, 020 research D1), aggregates the state facts into a
:class:`~bookwright.status.model.StatusState`, maps them through the pure rule
table, and emits the report: a readable summary in human mode, exactly one
``{"status":"ok","focus":…,"state":…,"next_actions":…}`` document under
``--json``. Every successful run regenerates ``.bookwright/cache/status.json``
with the byte-identical document — one serialization, two sinks (research D6).

Fault model (research D4/D5, contracts/cli-status.md): *absent* information
degrades to a successful exit-0 report; *corrupt* corpora fail exactly as
``graph build`` on the same corpus — config faults exit 2, a slug collision
exit 3, skipped bible files exit 4 (``skipped_sources``: a facts report over a
knowingly partial corpus would be a lie, so build's partial success hardens
into a full error here while the exit code stays aligned per-corpus).
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, TypeVar

import typer
from rich.console import Console

from bookwright.core.errors import ManifestError
from bookwright.core.manifest import Manifest
from bookwright.errors import BookwrightError
from bookwright.indexers import UnknownIndexerError
from bookwright.io.errors import (
    MissingDirectoryError,
    ProjectNotFoundError,
    ResearchError,
    SlugCollisionError,
)
from bookwright.io.manuscript import manuscript_present
from bookwright.io.project import find_project_root
from bookwright.status.model import (
    AnchorGap,
    GraphFacts,
    LowReliabilityFinding,
    OpenQuestion,
    StatusState,
    ValidationSummary,
)
from bookwright.status.queries import (
    anchor_gaps,
    low_reliability_findings,
    open_questions,
    validation_summary,
)
from bookwright.status.rules import Action, next_actions
from bookwright.validation.base import UnknownValidatorError

from ._envelope import EXIT_CONFIG, emit_error, invalid_manifest_payload, ok_payload
from ._graph import build_project_graph

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from bookwright.io.report import SkippedFile

EXIT_COLLISION = 3
EXIT_SKIPPED = 4

_CACHE_SUBPATH = (".bookwright", "cache", "status.json")

#: The exit-2 pipeline/config faults, mirrored from ``graph build`` (D4) plus
#: ``UnknownValidatorError`` — the one fault the validation leg adds, exiting 2
#: with its own envelope exactly as ``bookwright validate`` does.
_CONFIG_FAULTS = (
    MissingDirectoryError,
    UnknownIndexerError,
    ResearchError,
    UnknownValidatorError,
)

_T = TypeVar("_T")


class _NoProjectError(BookwrightError):
    """A caught ``ProjectNotFoundError`` re-coded to the contract's ``no_project``.

    Mirrors ``commands.validate._UsageError("no_project", …)``: the remap is a
    ``BookwrightError`` whose canonical ``to_json()`` builds the envelope.
    """

    code = "no_project"


class _SkippedSourcesError(BookwrightError):
    """≥ 1 bible file was skipped — a corrupt corpus for a facts report (D4)."""

    code = "skipped_sources"

    def __init__(self, skipped: tuple[SkippedFile, ...]) -> None:
        super().__init__(
            f"{len(skipped)} bible file(s) skipped (unusable front-matter); "
            "status will not report facts computed from a partial corpus",
            {"skipped": [{"path": s.path, "reason": s.reason} for s in skipped]},
        )


def run(
    json_output: bool = typer.Option(
        False, "--json", help="Emit the status report as one JSON document on stdout."
    ),
) -> None:
    """Report the project's derived state and deterministic next actions."""
    try:
        root = find_project_root()
    except ProjectNotFoundError as exc:
        emit_error(_NoProjectError(str(exc), {"start": exc.start}).to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    try:
        manifest = Manifest.load(root / "manifest.toml")
    except ManifestError as exc:
        emit_error(invalid_manifest_payload(exc), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc

    try:
        state = _aggregate(root, manifest)
    except _CONFIG_FAULTS as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except SlugCollisionError as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_COLLISION) from exc
    except _SkippedSourcesError as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_SKIPPED) from exc

    actions = next_actions(state)
    document = _render_document(manifest, state, actions)
    _write_cache(root, document)

    if json_output:
        sys.stdout.write(document)  # the cache's exact bytes (research D6)
    else:
        _print_report(manifest, state, actions)


def _aggregate(root: Path, manifest: Manifest) -> StatusState:
    """Build the graph and aggregate every derived fact (FR-001..FR-007).

    The degraded path (research D5): when the build *prerequisites* are absent —
    no bible directory, no manuscript signal — there is nothing to reason over
    and "nothing here yet" is a fact, not a failure. An empty-but-present bible
    builds normally (zero entities) and is likewise degraded, not an error.
    """
    bible_dir = root / manifest.paths.bible
    manuscript_dir = root / manifest.paths.manuscript
    if not bible_dir.is_dir() or not manuscript_present(manuscript_dir):
        return StatusState(
            phase=manifest.book.status,
            focus_defined=manifest.focus is not None,
            graph=GraphFacts(available=False, entities=0, triples=0),
            open_questions=(),
            unresolved_anchors=(),
            low_reliability_findings=(),
            validation=ValidationSummary(counts={}, ran=()),
        )

    outcome = build_project_graph(root, manifest)  # refreshes bible/graph.ttl (D1)
    if outcome.report.skipped:
        raise _SkippedSourcesError(outcome.report.skipped)

    engine = outcome.engine
    research = outcome.research
    minimum = manifest.research.min_reliability_for_anchor
    uri_base = manifest.bookwright.uri_base
    return StatusState(
        phase=manifest.book.status,
        focus_defined=manifest.focus is not None,
        graph=GraphFacts(
            available=True, entities=outcome.report.entities, triples=outcome.report.triples
        ),
        open_questions=open_questions(engine, research.finding_identities),
        unresolved_anchors=anchor_gaps(engine, research.anchor_identities, minimum, uri_base),
        low_reliability_findings=low_reliability_findings(
            engine, research.finding_identities, minimum
        ),
        validation=validation_summary(root, manifest, engine),
    )


def _render_document(manifest: Manifest, state: StatusState, actions: list[Action]) -> str:
    """Serialize the success document once — stdout and cache share these bytes."""
    payload = ok_payload(
        focus=manifest.focus.model_dump() if manifest.focus is not None else None,
        state=state.to_payload(),
        next_actions=[action.to_payload() for action in actions],
    )
    return json.dumps(payload, separators=(",", ":")) + "\n"


def _write_cache(root: Path, document: str) -> None:
    """Regenerate ``.bookwright/cache/status.json`` (every successful run, FR-012).

    Write-only output: never read back, never an input. A regenerated-per-run
    cache needs no ledger/atomicity machinery — plain ``write_text`` (D6).
    """
    cache_path = root.joinpath(*_CACHE_SUBPATH)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(document, encoding="utf-8")


def _print_report(manifest: Manifest, state: StatusState, actions: list[Action]) -> None:
    """The human-readable report on stdout (FR-011).

    ``markup=False``: phases, focus targets, claims, and prompts are author text
    — bracketed words must echo literally, not parse as rich markup.
    """
    console = Console(highlight=False, markup=False)
    console.print(f"phase: {state.phase}")
    focus = manifest.focus
    if focus is None:
        console.print("focus: (none)")
    else:
        console.print(f"focus: {focus.target} (updated {focus.updated_at})")
    if state.graph.available:
        console.print(f"graph: {state.graph.entities} entities, {state.graph.triples} triples")
    else:
        console.print("graph: unavailable (nothing to build from yet)")

    _print_items(console, "open questions", state.open_questions, _question_line)
    _print_items(console, "unresolved anchors", state.unresolved_anchors, _anchor_line)
    _print_items(console, "low-reliability findings", state.low_reliability_findings, _finding_line)

    counts = state.validation.to_payload()["counts"]
    console.print(
        f"validation: {counts['error']} error(s), {counts['warning']} warning(s), "
        f"{counts['info']} info — ran {len(state.validation.ran)} validator(s)"
    )

    if not actions:
        console.print("next actions: none — nothing to recommend")
        return
    console.print("next actions:")
    for index, action in enumerate(actions, start=1):
        console.print(f"  {index}. [{action.skill}] {action.reason}")
        console.print(f"     prompt: {action.prompt}")


def _print_items(
    console: Console, label: str, items: tuple[_T, ...], line: Callable[[_T], str]
) -> None:
    console.print(f"{label} ({len(items)}):" if items else f"{label}: none")
    for item in items:
        console.print(f"  - {line(item)}")


def _question_line(question: OpenQuestion) -> str:
    text = f": {question.text}" if question.text is not None else ""
    return f"{question.id}{text} ({question.file})"


def _anchor_line(gap: AnchorGap) -> str:
    target = f" -> {gap.constrains}" if gap.constrains is not None else ""
    return f"{gap.promotes}{target}: {', '.join(gap.problems)} ({gap.file})"


def _finding_line(finding: LowReliabilityFinding) -> str:
    best = finding.best_reliability if finding.best_reliability is not None else "unrated"
    return f"{finding.id}: best support {best} ({finding.file})"
