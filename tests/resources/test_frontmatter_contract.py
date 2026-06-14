"""C6 / SC-002 / SC-003 / FR-020 — templates honor the frozen iter-6 mapper contract.

(1) Every shipped template parses through ``parse_frontmatter`` without raising.
(2) A freshly-``init``-ed project round-trips through ``map_bible`` with zero
    skips, zero ``unknown_keys`` and zero ``unresolved_references`` (SC-002).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from bookwright.io.bible import MapResult
from bookwright.io.frontmatter import parse_frontmatter

from .helpers import PROJECT_DIR, authored_templates, read_text


@pytest.mark.parametrize("path", authored_templates(), ids=lambda p: p.name)
def test_template_parses_without_raising(path: Path) -> None:
    # SC-003: every authored template is readable by the iter-6 reader.
    parse_frontmatter(read_text(path))


def test_fresh_project_round_trips_clean(
    map_stamped_bible: Callable[[], MapResult],
) -> None:
    result = map_stamped_bible()
    assert result.skipped == [], f"unexpected skips: {result.skipped}"
    assert result.unknown_keys == [], f"unexpected unknown keys: {result.unknown_keys}"
    assert result.unresolved_references == [], (
        f"unexpected unresolved references: {result.unresolved_references}"
    )


def test_indexed_collections_have_exactly_one_top_key() -> None:
    # C2/C4: timeline.md / relationships.md must carry ONLY their container key.
    cases = {
        PROJECT_DIR / "bible" / "timeline.md": "events",
        PROJECT_DIR / "bible" / "relationships.md": "relationships",
    }
    for path, container in cases.items():
        fm = parse_frontmatter(read_text(path))
        assert set(fm.metadata) == {container}, f"{path} top-level keys: {set(fm.metadata)}"
        assert fm.metadata[container] == [], f"{path} ships a non-empty {container}"
