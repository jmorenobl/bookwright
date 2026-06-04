"""Unit tests for the shared interval helpers in ``queries`` (T012).

``intervals_disjoint`` is the single source of truth for "two year ranges provably
do not overlap" (FR-011); ``load_timeline_bounds`` is the thin reduction over
``load_intervals`` the anchor anachronism rule uses for a timeline target (D3).
"""

from __future__ import annotations

from bookwright.validation.queries import (
    EventInterval,
    intervals_disjoint,
    load_timeline_bounds,
)
from tests.validation.conftest import add_event, research_graph


def _iv(begin: int | None, end: int | None) -> EventInterval:
    return EventInterval(uri="x", begin=begin, end=end)


def test_disjoint_in_each_direction() -> None:
    assert intervals_disjoint(_iv(1900, 1910), _iv(1920, 1930)) is True
    assert intervals_disjoint(_iv(1920, 1930), _iv(1900, 1910)) is True


def test_overlapping_and_touching_are_not_disjoint() -> None:
    assert intervals_disjoint(_iv(1900, 1925), _iv(1920, 1930)) is False
    # touching at a single year (end == begin) is contact, not a provable gap.
    assert intervals_disjoint(_iv(1900, 1920), _iv(1920, 1930)) is False


def test_open_bound_never_forces_disjointness() -> None:
    # When the bound that WOULD prove the gap is open, disjointness is unprovable:
    # a runs 1900→∞, so it may reach into b — not disjoint despite b being "later".
    assert intervals_disjoint(_iv(1900, None), _iv(1920, 1930)) is False
    # symmetric: b's end is open, so b may reach back into a.
    assert intervals_disjoint(_iv(1920, 1930), _iv(1900, None)) is False
    assert intervals_disjoint(_iv(None, None), _iv(1920, 1930)) is False


def test_open_bound_on_irrelevant_side_still_disjoint() -> None:
    # a ends 1910 (bounded) before b begins 1920 — a's open START does not matter.
    assert intervals_disjoint(_iv(None, 1910), _iv(1920, 1930)) is True


def test_load_timeline_bounds_spans_all_events() -> None:
    engine = research_graph()
    add_event(engine, "early", begin=1900, end=1905)
    add_event(engine, "late", begin=1950, end=1960)
    bounds = load_timeline_bounds(engine)
    assert bounds.begin == 1900
    assert bounds.end == 1960


def test_load_timeline_bounds_none_when_no_years() -> None:
    engine = research_graph()
    add_event(engine, "vague", begin=None, end=None)
    bounds = load_timeline_bounds(engine)
    assert bounds.begin is None
    assert bounds.end is None
