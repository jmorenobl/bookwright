"""The ``bookwright graph`` Typer sub-app.

``build`` and ``query`` live in their own modules (Principle IV) and register
their callbacks here. The app is wired into the root CLI in
:mod:`bookwright.cli` via ``app.add_typer(graph.app, name="graph")``.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="graph",
    help="Build and query the project's GOLEM graph.",
    no_args_is_help=True,
    add_completion=False,
)

# `build` and `query` register their callbacks on `app` at import
# time; importing them here keeps the sub-app self-contained. The `as` redirect
# marks the imports as intentional re-exports (registration side effect).
from . import build as build  # noqa: E402
from . import query as query  # noqa: E402
