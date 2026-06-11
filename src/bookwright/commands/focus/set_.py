"""``bookwright focus set --target <text> [--notes <text>] [--json]``.

Create or update the ``[focus]`` block: stamp ``updated_at`` with today's date,
apply the partial-``notes`` rule (FR-007), reject an empty ``--target`` *before*
touching the manifest (FR-008), and preserve every other byte (FR-009). Under
``--json`` exactly one ``{"status":"ok","focus":{…}}`` document on stdout;
otherwise a confirmation to stderr (Principle IX).
"""

from __future__ import annotations

from datetime import date

import typer
from rich.console import Console

from bookwright.core.manifest import Manifest

from .._envelope import EXIT_CONFIG, emit_error, emit_json
from .._project import load_manifest_or_exit
from . import app
from .errors import FocusTargetEmptyError


def _today() -> str:
    """Today's local date as ``YYYY-MM-DD``. A test seam (research D5)."""
    return date.today().isoformat()


@app.command("set")
def run(
    target: str = typer.Option(..., "--target", help="What you are working on now."),
    notes: str | None = typer.Option(
        None, "--notes", help="Open threads / pending decisions. Omit to keep; '' to clear."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit the result as one JSON document on stdout."
    ),
) -> None:
    """Record or update the authored focus state."""
    path, manifest = load_manifest_or_exit(json_output)

    if not target.strip():
        exc = FocusTargetEmptyError()
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc

    resolved_notes = _resolve_notes(notes, manifest)
    # `target` is stored verbatim, not stripped (data-model write-shape decision 2).
    block = manifest.set_focus(target=target, notes=resolved_notes, updated_at=_today())
    manifest.dump(path, overwrite=True)

    if json_output:
        emit_json({"status": "ok", "focus": block.model_dump()})
    else:
        # markup=False: `target` is author text — bracketed words must echo
        # literally, not be parsed (or crash) as rich markup tags.
        Console(stderr=True, highlight=False, markup=False).print(
            f'focus set: target="{block.target}", updated_at={block.updated_at}'
        )


def _resolve_notes(notes: str | None, manifest: Manifest) -> str:
    """Apply the partial-``notes`` rule (FR-007, research D4).

    ``--notes`` omitted (``None``) ⇒ keep the existing notes (or ``""`` on create);
    ``--notes "X"`` ⇒ set; ``--notes ""`` ⇒ clear.
    """
    if notes is not None:
        return notes
    return manifest.focus.notes if manifest.focus is not None else ""
