"""Locate the project root by walking up for ``manifest.toml`` (R8)."""

from __future__ import annotations

from pathlib import Path

from .errors import ProjectNotFoundError

MANIFEST_NAME = "manifest.toml"


def find_project_root(start: Path | None = None) -> Path:
    """Return the nearest ancestor of ``start`` (default cwd) holding ``manifest.toml``.

    Raises :class:`ProjectNotFoundError` when no ancestor contains one (R8).
    """
    origin = (start or Path.cwd()).resolve()
    for candidate in (origin, *origin.parents):
        if (candidate / MANIFEST_NAME).is_file():
            return candidate
    raise ProjectNotFoundError(str(origin))
