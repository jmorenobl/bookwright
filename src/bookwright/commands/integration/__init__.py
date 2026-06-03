"""The ``bookwright integration`` Typer sub-app.

Manages a project's active agent integration. ``use`` lives in its own module
(Principle IV) and registers its callback here. Wired into the root CLI in
:mod:`bookwright.cli` via ``app.add_typer(integration.app, name="integration")``.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="integration",
    help="Manage the project's agent integration (re-materialize skills).",
    no_args_is_help=True,
    add_completion=False,
)

# `use` registers its callback on `app` at import time; importing it here keeps
# the sub-app self-contained. The `as` redirect marks the import as an
# intentional re-export (registration side effect).
from . import use as use  # noqa: E402
