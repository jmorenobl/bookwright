"""Manuscript presence check (FR-012).

v0 does **no** prose mining — extraction is bible-frontmatter-driven. This module
only confirms the manuscript directory exists so ``graph build`` can fail fast on
a malformed project layout.

Both ``manuscript/`` and ``outline/`` are **author-only** in v0.3: the scaffold
creates them, but the engine never ingests their contents — there is no
``outline/`` reader at all, and ``manuscript_present`` only checks existence.
Their inertness is deliberate (see the deferral rationale in
``bookwright.golem.deferrals`` and ``docs/authoring.md``), not an oversight.
"""

from __future__ import annotations

from pathlib import Path


def manuscript_present(manuscript_dir: Path) -> bool:
    """Return whether the manuscript directory exists."""
    return manuscript_dir.is_dir()
