"""Shared fixtures for the ``focus`` command tests.

Scaffolds a minimal valid Bookwright project (a directory holding a
``manifest.toml`` with the three required blocks) and ``chdir``s into it, so the
``focus`` subcommands' ``find_project_root()`` resolves it. Kept local to the
focus suite — the graph suite's ``tiny_novel`` carries a full bible the focus
commands never touch.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

_BASE_MANIFEST = """\
# authored comment
[bookwright]
cli_version_min = "0.0.1"
schema_version = "golem-1.1"
manifest_version = "1"
uri_base = "https://example.org/focus/"

[book]
title = "Focus Book"
type = "novel"
language = "es"
authors = ["Solo Author"]

[integration]
key = "generic"
skills_dir = ".agents/skills"
"""


@pytest.fixture()
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A minimal project (no ``[focus]``) with cwd set to its root."""
    root = tmp_path / "my-novel"
    root.mkdir()
    (root / "manifest.toml").write_text(_BASE_MANIFEST, encoding="utf-8")
    monkeypatch.chdir(root)
    return root


@pytest.fixture()
def project_with_focus(project: Path) -> Callable[[str], Path]:
    """Append a ``[focus]`` block to the project's manifest and return its root."""

    def _make(block: str) -> Path:
        manifest = project / "manifest.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8") + f"\n[focus]\n{block}",
            encoding="utf-8",
        )
        return project

    return _make
