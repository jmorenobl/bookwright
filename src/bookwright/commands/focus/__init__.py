"""The ``bookwright focus`` Typer sub-app.

``show``, ``set``, and ``clear`` live in their own modules (Principle IV) and
register their callbacks here. The app is wired into the root CLI in
:mod:`bookwright.cli` via ``app.add_typer(focus.app, name="focus")``.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="focus",
    help="Record, view, and clear the authored focus state.",
    no_args_is_help=True,
    add_completion=False,
)

# Each subcommand registers its callback on `app` at import time; the per-story
# `from . import …` lines are appended below as the modules land. The `as`
# redirect marks the import as an intentional re-export (registration side effect).
from . import clear as clear  # noqa: E402
from . import set as set  # noqa: E402
from . import show as show  # noqa: E402
