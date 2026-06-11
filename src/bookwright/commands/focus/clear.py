"""``bookwright focus clear [--json]``.

Remove the ``[focus]`` block, preserving the rest of the manifest. Absent block ⇒
a successful no-op (FR-010). Under ``--json`` emit
``{"status":"ok","cleared":<bool>}`` — the boolean discriminator lets an agent
tell a real removal from a no-op without a second read; both exit 0. Human prose
goes to stderr (Principle IX).
"""

from __future__ import annotations

import typer
from rich.console import Console

from .._envelope import emit_json
from .._project import load_manifest_or_exit
from . import app


@app.command("clear")
def run(
    json_output: bool = typer.Option(
        False, "--json", help="Emit the result as one JSON document on stdout."
    ),
) -> None:
    """Clear the authored focus state (no-op when none is set)."""
    path, manifest = load_manifest_or_exit(json_output)
    had_focus = manifest.focus is not None

    manifest.clear_focus()
    # Only rewrite when something actually changed — a no-op leaves the bytes
    # untouched rather than re-serializing an unchanged manifest.
    if had_focus:
        manifest.dump(path, overwrite=True)

    if json_output:
        emit_json({"status": "ok", "cleared": had_focus})
    else:
        message = "focus cleared" if had_focus else "no focus to clear"
        Console(stderr=True, highlight=False).print(message)
