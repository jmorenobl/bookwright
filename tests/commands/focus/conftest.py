"""Shared fixtures for the ``focus`` command tests.

Scaffolds a minimal valid Bookwright project (a directory holding a
``manifest.toml`` with the three required blocks) and ``chdir``s into it, so the
``focus`` subcommands' ``find_project_root()`` resolves it. The manifest literal
is single-sourced in :mod:`tests.fixtures.manifests` — the graph suite's
``tiny_novel`` carries a full bible the focus commands never touch.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from tests.fixtures.manifests import MINIMAL_MANIFEST, with_focus


@pytest.fixture()
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A minimal project (no ``[focus]``) with cwd set to its root."""
    root = tmp_path / "my-novel"
    root.mkdir()
    (root / "manifest.toml").write_text(MINIMAL_MANIFEST, encoding="utf-8")
    monkeypatch.chdir(root)
    return root


@pytest.fixture()
def project_with_focus(project: Path) -> Callable[[str], Path]:
    """Append a ``[focus]`` block to the project's manifest and return its root."""

    def _make(block: str) -> Path:
        manifest = project / "manifest.toml"
        manifest.write_text(
            with_focus(block, base=manifest.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        return project

    return _make
