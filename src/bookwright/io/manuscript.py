"""Manuscript presence check (FR-012).

v0 does **no** prose mining — extraction is bible-frontmatter-driven. This module
only confirms the manuscript directory exists so ``graph build`` can fail fast on
a malformed project layout.
"""

from __future__ import annotations

from pathlib import Path


def manuscript_present(manuscript_dir: Path) -> bool:
    """Return whether the manuscript directory exists."""
    return manuscript_dir.is_dir()
