"""Authoritative description table contract (FR-004, SC-002, SC-009)."""

from __future__ import annotations

from pathlib import Path

import bookwright
from bookwright.integrations.constants import SKILL_DESCRIPTION_MAX_LENGTH
from bookwright.integrations.descriptions import SKILL_DESCRIPTIONS, get_description
from bookwright.io.frontmatter import parse_frontmatter

_COMMANDS_DIR = Path(bookwright.__file__).resolve().parent / "resources" / "commands"

_ROSTER: tuple[str, ...] = (
    "bookwright-constitution",
    "bookwright-bible",
    "bookwright-outline",
    "bookwright-scenes",
    "bookwright-draft",
    "bookwright-synopsis",
    "bookwright-clarify",
    "bookwright-analyze",
    "bookwright-continuity",
    "bookwright-checklist",
    "bookwright-research",
)


def test_all_roster_keys_present() -> None:
    assert set(SKILL_DESCRIPTIONS) == set(_ROSTER)


def test_every_description_under_cap() -> None:
    for name, description in SKILL_DESCRIPTIONS.items():
        assert 0 < len(description) < SKILL_DESCRIPTION_MAX_LENGTH, name


def test_get_description_returns_table_value_when_keyed() -> None:
    for name in _ROSTER:
        assert get_description(name, "FALLBACK") == SKILL_DESCRIPTIONS[name]


def test_get_description_falls_back_for_missing_key() -> None:
    assert get_description("bookwright-unknown", "the fallback") == "the fallback"


def test_v0_equality_gate_mirrors_source_frontmatter() -> None:
    """SC-009 — in v0 the dict mirrors each source frontmatter description verbatim.

    Accidental drift fails CI; a deliberate divergence is an explicit, reviewed
    edit to this expectation.
    """

    for name in _ROSTER:
        source = parse_frontmatter((_COMMANDS_DIR / f"{name}.md").read_text(encoding="utf-8"))
        assert SKILL_DESCRIPTIONS[name] == source.metadata["description"], name
