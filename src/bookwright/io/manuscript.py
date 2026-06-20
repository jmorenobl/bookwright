"""Manuscript presence check (FR-012).

v0 does **no** prose mining — extraction is bible-frontmatter-driven. This module
only confirms the manuscript directory exists so ``graph build`` can fail fast on
a malformed project layout.

``manuscript/`` is **author-only**: the scaffold creates it, but the engine
never ingests its contents — ``manuscript_present`` only checks existence.
``outline/`` is **partially ingested** since iteration 028: ``outline/units/``
cards feed ``NarrativeUnit`` / ``NarrativeFunction`` entities and — since
iteration 029, via their ``sequence``/``order`` keys — assemble
``NarrativeSequence`` (G7) entities (all via ``bookwright.io.outline``), while
``arcs``/``structure``/``synopsis``/``scenes`` remain author-only prose. This
inertness is deliberate (see the deferral
rationale in ``bookwright.golem.deferrals`` and ``docs/authoring.md``), not an
oversight.
"""

from __future__ import annotations

from pathlib import Path


def manuscript_present(manuscript_dir: Path) -> bool:
    """Return whether the manuscript directory exists."""
    return manuscript_dir.is_dir()
