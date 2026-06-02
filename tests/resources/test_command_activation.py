"""SC-003 backstop — descriptions carry bilingual triggers + sibling disambiguation.

A keyword presence test, not the authoritative SC-003 check (that is the hand-run
A/B battery recorded in the spec). Asserts each ``description`` has an ES and an EN
trigger, and that the four documented sibling pairs each carry the keyword that
repels the sibling.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.io.frontmatter import parse_frontmatter

from .helpers import command_files, looks_spanish, read_text

#: Lightweight English-presence markers (descriptions are bilingual ES+EN).
_EN_MARKERS: tuple[str, ...] = (
    " the ",
    " and ",
    " before ",
    " after ",
    " is ",
    " of ",
    " into ",
    " your ",
    " whether ",
)


def _descriptions() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in command_files():
        out[path.stem] = parse_frontmatter(read_text(path)).metadata["description"]
    return out


@pytest.mark.parametrize("path", command_files(), ids=lambda p: p.name)
def test_description_is_bilingual(path: Path) -> None:
    description = parse_frontmatter(read_text(path)).metadata["description"]
    assert looks_spanish(description), f"{path.name}: description lacks ES trigger"
    lowered = f" {description.lower()} "
    assert any(m in lowered for m in _EN_MARKERS), f"{path.name}: description lacks EN trigger"


def test_sibling_disambiguation_keywords() -> None:
    d = {name: desc.lower() for name, desc in _descriptions().items()}

    # constitution <-> bible: phase (antes/before vs después/after) + names sibling.
    assert "antes" in d["bookwright-constitution"] and "before" in d["bookwright-constitution"]
    assert "bookwright-bible" in d["bookwright-constitution"]  # bible-not-premature signal
    assert "después" in d["bookwright-bible"] and "after" in d["bookwright-bible"]
    assert "bookwright-constitution" in d["bookwright-bible"]

    # analyze <-> continuity: pre-draft vs post-draft.
    assert "pre-draft" in d["bookwright-analyze"]
    assert "post-draft" in d["bookwright-continuity"]

    # clarify <-> checklist: dudas (open questions) vs completitud (artifact completeness).
    assert "dudas" in d["bookwright-clarify"]
    assert "completitud" in d["bookwright-checklist"]
