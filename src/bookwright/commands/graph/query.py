"""`bookwright graph query` — load ``bible/graph.ttl`` and run a SPARQL query.

Read-only. Renders a ``rich`` table for humans (stdout) or, under ``--json``, a
single ``{"status":"ok","results":[...],"count":N}`` document (Principle IX).
Fault model (cli-graph.md): missing project / graph / unknown engine → exit 2;
malformed SPARQL → exit 3 with no partial rows.
"""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from bookwright.core.errors import ManifestError
from bookwright.core.manifest import Manifest
from bookwright.indexers import (
    GraphLoadError,
    GraphNotBuiltError,
    InvalidQueryError,
    UnknownIndexerError,
    resolve_indexer,
)
from bookwright.io.errors import ProjectNotFoundError
from bookwright.io.project import find_project_root

from . import app
from .envelope import emit_error, emit_json, error_payload

EXIT_CONFIG = 2
EXIT_INVALID_QUERY = 3


@app.command("query")
def run(
    sparql: str = typer.Argument(..., help="The SPARQL query to run against the graph."),
    json_output: bool = typer.Option(
        False, "--json", help="Emit results as one JSON document on stdout."
    ),
) -> None:
    """Run ``sparql`` against the project graph and print the rows."""
    try:
        rows = _query(sparql)
    except ManifestError as exc:
        emit_error(error_payload("invalid_manifest", str(exc)), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except (
        ProjectNotFoundError,
        GraphNotBuiltError,
        GraphLoadError,
        UnknownIndexerError,
    ) as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except InvalidQueryError as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_INVALID_QUERY) from exc

    if json_output:
        emit_json({"status": "ok", "results": rows, "count": len(rows)})
    else:
        _render_table(rows)


def _query(sparql: str) -> list[dict[str, Any]]:
    """Load the graph and run the query, returning fully materialized rows."""
    project_root = find_project_root()
    manifest = Manifest.load(project_root / "manifest.toml")

    engine_cls = resolve_indexer(manifest.bookwright.indexer)
    engine = engine_cls()

    graph_path = project_root / manifest.paths.graph
    if not graph_path.is_file():
        raise GraphNotBuiltError(manifest.paths.graph)
    engine.load(graph_path)

    return list(engine.query(sparql))


def _render_table(rows: list[dict[str, Any]]) -> None:
    """Render rows as a ``rich`` table on stdout (an empty note when no matches)."""
    console = Console()
    if not rows:
        Console(stderr=True).print("(no results)")
        return
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    table = Table(*columns)
    for row in rows:
        table.add_row(*(row.get(column, "") for column in columns))
    console.print(table)
