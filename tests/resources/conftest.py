"""Shared fixtures for the iteration-7 template validation suite.

Stamps a fresh project with the **real** iter-4 scaffold (``bookwright init``)
and exposes a helper that runs the **real** iter-6 bible mapper over it. Imports
only already-shipped iter-4/iter-6 modules — this iteration writes no production
code (FR-023). The validation tests therefore assert against the live contracts,
never a re-implementation.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.core.manifest import Manifest
from bookwright.io.bible import MapResult, map_bible

# A representative project title; ``init`` resolves the remaining four scaffold
# context keys (slug, author, language, integration_key) from it (W2).
PROJECT_TITLE = "qt-book"


@pytest.fixture()
def stamped_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Stamp a fresh project into ``tmp_path`` via the real ``bookwright init``.

    ``--no-git`` keeps the fixture independent of a git binary; the scaffold
    walker (``.j2`` rendered under ``StrictUndefined`` / every other file
    byte-copied) runs exactly as in production. Returns the stamped project root.
    """
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["init", PROJECT_TITLE, "--json", "--no-git"])
    assert result.exit_code == 0, result.stdout
    project_root = tmp_path / PROJECT_TITLE
    assert project_root.is_dir()
    return project_root


@pytest.fixture()
def map_stamped_bible(stamped_project: Path) -> Callable[[], MapResult]:
    """Return a helper running ``map_bible`` over the stamped project.

    Reads the stamped manifest for the same ``uri_base`` and bible path the real
    ``graph build`` uses, so callers can inspect ``skipped`` / ``unknown_keys`` /
    ``unresolved_references`` from the live mapper.
    """

    def _run() -> MapResult:
        manifest = Manifest.load(stamped_project / "manifest.toml")
        bible_dir = stamped_project / manifest.paths.bible
        return map_bible(stamped_project, bible_dir, manifest.bookwright.uri_base)

    return _run
