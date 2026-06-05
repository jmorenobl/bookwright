"""``temporal`` validator -- FR-015 rules a-d, each pinned to SC-009.

One fixture per rule → exactly one ``error`` finding carrying the implicated relation
edge in ``triples``; a clean timeline → zero; an open interval; and an end-to-end
(timeline.md → graph → validate) with a source location.
"""

from __future__ import annotations

from pathlib import Path

from bookwright.validation.base import Severity, Violation
from bookwright.validation.queries import load_intervals
from bookwright.validation.validators.temporal import Temporal
from tests.validation.conftest import build_indexer, load_context, write_project


def _run(root: Path) -> list[Violation]:
    return Temporal().validate(load_context(root), build_indexer(root))


def _only_error(findings: list[Violation]) -> Violation:
    errors = [f for f in findings if f.severity == Severity.error]
    assert len(errors) == 1, [f.message for f in findings]
    return errors[0]


def test_rule_a_cycle(project_root: Path) -> None:
    write_project(
        project_root,
        timeline="""\
        ---
        events:
          - name: "A"
            follows: ["B"]
          - name: "B"
            follows: ["A"]
        ---
        """,
    )
    finding = _only_error(_run(project_root))
    assert "cycle" in finding.message.lower()
    assert finding.triples  # carries the implicated follows edges


def test_rule_b_order_and_overlap(project_root: Path) -> None:
    write_project(
        project_root,
        timeline="""\
        ---
        events:
          - name: "A"
            precedes: ["B"]
            overlaps: ["B"]
          - name: "B"
        ---
        """,
    )
    finding = _only_error(_run(project_root))
    assert "overlap" in finding.message.lower()
    assert any("temporally-overlaps" in p for _, p, _ in finding.triples)


def test_rule_c_containment_vs_order(project_root: Path) -> None:
    write_project(
        project_root,
        timeline="""\
        ---
        events:
          - name: "A"
            includes: ["B"]
            precedes: ["B"]
          - name: "B"
        ---
        """,
    )
    finding = _only_error(_run(project_root))
    assert "containment" in finding.message.lower()
    assert any("temporally-includes" in p for _, p, _ in finding.triples)


def test_rule_d_numeric_contradiction(project_root: Path) -> None:
    write_project(
        project_root,
        timeline="""\
        ---
        events:
          - name: "Fundación"
            begin: 1885
            end: 1912
          - name: "Quiebra"
            date: 1884
            follows: ["Fundación"]
        ---
        """,
    )
    finding = _only_error(_run(project_root))
    assert "follow" in finding.message.lower()
    assert any("TemporalRelations.owl#follows" in p for _, p, _ in finding.triples)
    # Numeric findings carry the event's source location (D6).
    assert finding.source == "bible/timeline.md"


def test_rule_d_overlap_but_years_are_disjoint(project_root: Path) -> None:
    # Declared overlap, yet the year ranges are provably disjoint (FR-011). This pins
    # the "ends X / begins Y" message branch byte-for-byte after the intervals_disjoint
    # rewire; its sibling direction is covered by the other overlap fixtures.
    write_project(
        project_root,
        timeline="""\
        ---
        events:
          - name: "alfa"
            begin: 1900
            end: 1910
            overlaps: ["beta"]
          - name: "beta"
            begin: 1920
            end: 1930
        ---
        """,
    )
    finding = _only_error(_run(project_root))
    assert "(ends 1910)" in finding.message
    assert "(begins 1920)" in finding.message
    assert "disjoint" in finding.message


def test_rule_d_overlap_disjoint_reverse_direction(project_root: Path) -> None:
    # The canonical-first event sits AFTER the second → the "begins X / ends Y"
    # message branch (the other side of the same shared disjointness decision).
    write_project(
        project_root,
        timeline="""\
        ---
        events:
          - name: "alfa"
            begin: 1920
            end: 1930
            overlaps: ["beta"]
          - name: "beta"
            begin: 1900
            end: 1910
        ---
        """,
    )
    finding = _only_error(_run(project_root))
    assert "(begins 1920)" in finding.message
    assert "(ends 1910)" in finding.message
    assert "disjoint" in finding.message


def test_clean_timeline_has_no_findings(project_root: Path) -> None:
    write_project(
        project_root,
        timeline="""\
        ---
        events:
          - name: "A"
            begin: 1880
            end: 1884
          - name: "B"
            begin: 1885
            end: 1890
            follows: ["A"]
        ---
        """,
    )
    assert _run(project_root) == []


def test_open_interval_is_handled(project_root: Path) -> None:
    write_project(
        project_root,
        timeline="""\
        ---
        events:
          - name: "A"
            begin: 1900
        ---
        """,
    )
    indexer = build_indexer(project_root)
    intervals = load_intervals(indexer)
    (interval,) = intervals.values()
    assert interval.begin == 1900
    assert interval.end is None
    assert Temporal().validate(load_context(project_root), indexer) == []


def test_no_events_no_findings(project_root: Path) -> None:
    write_project(project_root, characters=["A"], manuscript={"c.md": "A"})
    assert _run(project_root) == []
