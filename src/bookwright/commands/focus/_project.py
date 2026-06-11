"""Shared project-load + ``--json`` fault boundary for the ``focus`` subcommands.

All three subcommands (``show``/``set``/``clear``) locate the project and load the
manifest the same way and remap the same two faults to exit 2 (research D10).
Factoring it here keeps each command body to its own logic — ``set`` keeps its own
``FocusTargetEmptyError`` rejection, the one per-command fault, visible in
``set.py``.
"""

from __future__ import annotations

from pathlib import Path

import typer

from bookwright.core.errors import ManifestError
from bookwright.core.manifest import Manifest
from bookwright.io.errors import ProjectNotFoundError
from bookwright.io.project import find_project_root

from .._envelope import emit_error, invalid_manifest_payload

EXIT_CONFIG = 2


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
