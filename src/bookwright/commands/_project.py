"""Shared project-load + ``--json`` fault boundary for the command layer.

Every manifest-reading subcommand locates the project and loads the manifest the
same way and remaps the same two faults to exit 2 (research D10). Factoring it
here — next to the envelope helpers in :mod:`bookwright.commands._envelope` —
keeps each command body to its own logic and gives later iterations (e.g. the
020 ``bookwright status`` read path) the boundary without reaching into a
sibling command package.
"""

from __future__ import annotations

from pathlib import Path

import typer

from bookwright.core.errors import ManifestError
from bookwright.core.manifest import Manifest
from bookwright.io.errors import ProjectNotFoundError
from bookwright.io.project import find_project_root

from ._envelope import EXIT_CONFIG, emit_error, invalid_manifest_payload


def load_manifest_or_exit(json_output: bool) -> tuple[Path, Manifest]:
    """Return ``(manifest_path, manifest)`` or emit the fault envelope and exit 2.

    A caught ``ManifestError`` collapses to the contract's ``invalid_manifest``
    code; ``ProjectNotFoundError`` carries its own ``not_a_project`` code. Both
    exit 2 — the structured distinction lives in the envelope ``code`` (research
    D7), never the exit status.
    """

    try:
        root = find_project_root()
        path = root / "manifest.toml"
        manifest = Manifest.load(path)
    except ManifestError as exc:
        emit_error(invalid_manifest_payload(exc), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except ProjectNotFoundError as exc:
        emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    return path, manifest
