"""``bookwright validate`` — run the active validators and report violations.

Binding: contracts/cli-validate.md, FR-008..014, Principle IX. The CI gate (exit 1)
is computed from the **unfiltered** error-severity set, so ``--scope`` / ``--severity``
(display filters) can never hide an error. Under ``--json`` exactly one JSON document
goes to stdout; all prose goes to stderr.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

from bookwright.core.errors import ManifestError
from bookwright.core.manifest import Manifest
from bookwright.errors import BookwrightError
from bookwright.indexers import GraphLoadError, UnknownIndexerError, resolve_indexer
from bookwright.io.errors import ProjectNotFoundError
from bookwright.io.project import find_project_root
from bookwright.validation import (
    ScopeFilter,
    Severity,
    UnknownValidatorError,
    ValidationContext,
    ValidationReport,
    discover_validators,
    resolve_active,
    run_validators,
)

from ._envelope import EXIT_CONFIG, INVALID_MANIFEST_CODE, emit_error, emit_json

EXIT_OK = 0
EXIT_GATE = 1

_CUSTOM_SUBPATH = (".bookwright", "validators")


class _UsageError(BookwrightError):
    """An exit-2 config/usage failure carrying a contract error envelope.

    A single class whose ``code`` is set per instance (``no_project`` /
    ``invalid_manifest`` / ``unknown_validator`` / ``empty_scope``) — hence the
    per-instance ``self.code`` override the base supports (research Decision 2).
    """

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        super().__init__(message, details)


def run(
    scope: Annotated[
        Path | None,
        typer.Option("--scope", help="Limit the reported violations to this file or directory."),
    ] = None,
    severity: Annotated[
        Severity,
        typer.Option("--severity", help="Report this level and above (error>warning>info)."),
    ] = Severity.info,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit one JSON document on stdout and nothing else.")
    ] = False,
) -> None:
    """Validate the project and report coherence violations (exit 1 gates on errors)."""
    try:
        report, scope_filter = _validate(scope)
    except _UsageError as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc

    if json_output:
        emit_json(report.to_json(scope=scope_filter, severity=severity))
    else:
        report.render(Console(), scope=scope_filter, severity=severity)

    raise typer.Exit(EXIT_GATE if report.failed else EXIT_OK)


def _validate(scope: Path | None) -> tuple[ValidationReport, ScopeFilter | None]:
    """Run the pipeline, raising :class:`_UsageError` for every exit-2 condition."""
    try:
        root = find_project_root()
    except ProjectNotFoundError as exc:
        raise _UsageError("no_project", str(exc), {"start": exc.start}) from exc

    try:
        manifest = Manifest.load(root / "manifest.toml")
    except ManifestError as exc:
        raise _UsageError(INVALID_MANIFEST_CODE, str(exc)) from exc

    indexer = _load_indexer(manifest, root)
    project = ValidationContext(root=root, manifest=manifest)

    builtins, customs, load_errors = discover_validators(root.joinpath(*_CUSTOM_SUBPATH))
    try:
        active = resolve_active(builtins, customs, manifest.validators)
    except UnknownValidatorError as exc:
        # UnknownValidatorError is itself a BookwrightError carrying the exact
        # ``unknown_validator`` envelope; re-thread its code/message/details into
        # the exit-2 funnel rather than rebuilding them by hand.
        raise _UsageError(exc.code, exc.message, exc.details) from exc

    scope_filter = _resolve_scope(scope, root)

    violations, run_errors, ran = run_validators(active, project, indexer)
    report = ValidationReport(
        violations=tuple(violations),
        errors=(*load_errors, *run_errors),
        ran=tuple(ran),
    )
    return report, scope_filter


def _load_indexer(manifest: Manifest, root: Path) -> Any:
    """The manifest-selected engine, with ``graph.ttl`` loaded when it exists."""
    try:
        engine_cls = resolve_indexer(manifest.bookwright.indexer)
    except UnknownIndexerError as exc:
        raise _UsageError(INVALID_MANIFEST_CODE, str(exc)) from exc
    engine = engine_cls()
    graph_path = root / manifest.paths.graph
    if graph_path.is_file():
        try:
            engine.load(graph_path)
        except GraphLoadError as exc:
            raise _UsageError(INVALID_MANIFEST_CODE, str(exc)) from exc
    return engine


def _resolve_scope(scope: Path | None, root: Path) -> ScopeFilter | None:
    """Resolve ``--scope`` under the project root, or exit 2 ``empty_scope`` (D10)."""
    if scope is None:
        return None
    resolved = scope if scope.is_absolute() else (Path.cwd() / scope)
    resolved = resolved.resolve()
    if not resolved.exists():
        raise _UsageError("empty_scope", f"scope path does not exist: {scope}")
    try:
        rel = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise _UsageError("empty_scope", f"scope path is outside the project: {scope}") from exc
    return ScopeFilter(rel=rel, is_dir=resolved.is_dir())
