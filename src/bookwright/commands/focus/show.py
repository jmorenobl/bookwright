"""``bookwright focus show [--json]``.

Read-only. Under ``--json`` emit exactly one
``{"status":"ok","focus":{…}|null}`` document on stdout; in human mode print the
three fields legibly to stdout when present, or ``no focus defined`` to stderr
when absent (FR-005). Either way exit 0 — an absent block is not an error
(Principle IX, channel discipline research D8).
"""

from __future__ import annotations

import typer
from rich.console import Console

from .._envelope import emit_json
from .._project import load_manifest_or_exit
from . import app


@app.command("show")
def run(
    json_output: bool = typer.Option(
        False, "--json", help="Emit the focus state as one JSON document on stdout."
    ),
) -> None:
    """Display the current authored focus state."""
    _, manifest = load_manifest_or_exit(json_output)
    focus = manifest.focus

    if focus is None:
        if json_output:
            emit_json({"status": "ok", "focus": None})
        else:
            Console(stderr=True, highlight=False).print("no focus defined")
        return

    if json_output:
        emit_json({"status": "ok", "focus": focus.model_dump()})
    else:
        # markup=False: `target`/`notes` are author text — bracketed words must
        # echo literally, not be parsed (or crash) as rich markup tags.
        console = Console(highlight=False, markup=False)
        console.print(f"target:     {focus.target}")
        console.print(f"notes:      {focus.notes}")
        console.print(f"updated_at: {focus.updated_at}")
