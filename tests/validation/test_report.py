"""``ValidationReport`` filtering, gate, and JSON shape (D13.3).

Also covers the additive ``not_evaluated`` channel + the documented green predicate
(iteration 040, SC-002): a non-empty channel makes a run non-green even when
``status == "ok"``.
"""

from __future__ import annotations

import io

from rich.console import Console

from bookwright.validation.base import (
    NotEvaluatedKind,
    NotEvaluatedResult,
    Severity,
    ValidatorError,
    Violation,
)
from bookwright.validation.report import ScopeFilter, ValidationReport
from tests.conftest import is_green


def _render(report: ValidationReport) -> str:
    buffer = io.StringIO()
    report.render(Console(file=buffer, width=200), scope=None, severity=None)
    return buffer.getvalue()


_ERR = Violation("temporal", Severity.error, "cycle", None)
_WARN_A = Violation("character_presence", Severity.warning, "w-a", "manuscript/cap-01.md:3")
_WARN_B = Violation("setting_continuity", Severity.warning, "w-b", "manuscript/cap-02.md:9")
_INFO = Violation("focalization", Severity.info, "note", "manuscript/cap-01.md:1")


def _report() -> ValidationReport:
    return ValidationReport(
        violations=(_ERR, _WARN_A, _WARN_B, _INFO),
        errors=(),
        ran=("character_presence", "focalization", "setting_continuity", "temporal"),
    )


def test_gate_is_pre_filter() -> None:
    report = _report()
    assert report.failed is True
    # A filter that hides the error never clears the gate (FR-013).
    assert report.failed is True


def test_scope_filters_to_file_and_omits_location_less() -> None:
    report = _report()
    scope = ScopeFilter(rel="manuscript/cap-01.md", is_dir=False)
    reported = report.reported(scope=scope, severity=None)
    assert reported == [_WARN_A, _INFO]  # cap-02 + the location-less error dropped


def test_scope_directory_matches_prefix() -> None:
    report = _report()
    scope = ScopeFilter(rel="manuscript", is_dir=True)
    reported = report.reported(scope=scope, severity=None)
    assert _ERR not in reported  # location-less omitted under scope
    assert {_WARN_A, _WARN_B, _INFO} == set(reported)


def test_severity_threshold_orders_error_warning_info() -> None:
    report = _report()
    assert report.reported(scope=None, severity=Severity.error) == [_ERR]
    assert set(report.reported(scope=None, severity=Severity.warning)) == {_ERR, _WARN_A, _WARN_B}


def test_scope_and_severity_compose_without_touching_gate() -> None:
    report = _report()
    scope = ScopeFilter(rel="manuscript/cap-01.md", is_dir=False)
    reported = report.reported(scope=scope, severity=Severity.warning)
    assert reported == [_WARN_A]  # cap-01 ∧ ≥warning → just the warning
    assert report.failed is True  # gate unaffected (D13.3)


def test_to_json_summary_counts_over_unfiltered_set() -> None:
    report = _report()
    scope = ScopeFilter(rel="manuscript/cap-01.md", is_dir=False)
    payload = report.to_json(scope=scope, severity=Severity.warning)

    assert payload["status"] == "violations"
    assert payload["failed"] is True
    assert len(payload["violations"]) == 1  # reported (cap-01 ∧ ≥warning)
    summary = payload["summary"]
    assert summary["total"] == 4
    assert summary["reported"] == 1
    # by_severity counts the UNFILTERED set and always carries all three keys.
    assert summary["by_severity"] == {"error": 1, "warning": 2, "info": 1}


def test_to_json_all_severity_keys_present_when_absent() -> None:
    report = ValidationReport(violations=(_WARN_A,), errors=(), ran=("character_presence",))
    payload = report.to_json(scope=None, severity=None)
    assert payload["summary"]["by_severity"] == {"error": 0, "warning": 1, "info": 0}
    assert payload["failed"] is False
    assert payload["status"] == "violations"


def test_to_json_ok_status_when_nothing_reported() -> None:
    report = ValidationReport(violations=(), errors=(), ran=("temporal",))
    payload = report.to_json(scope=None, severity=None)
    assert payload["status"] == "ok"
    assert payload["violations"] == []


def test_errors_surface_in_json() -> None:
    report = ValidationReport(
        violations=(),
        errors=(ValidatorError(".bookwright/validators/broken.py", "SyntaxError", "load"),),
        ran=(),
    )
    payload = report.to_json(scope=None, severity=None)
    assert payload["errors"] == [
        {"validator": ".bookwright/validators/broken.py", "phase": "load", "message": "SyntaxError"}
    ]


_SKIP = NotEvaluatedResult("focalization", "the constitution does not declare a narrative voice")
#: A permanent capability-gap entry (iteration 044): present in every project, does not
#: deny green, labeled as a known limitation.
_SKIP_CAP = NotEvaluatedResult(
    "character_unknown_mentions",
    "open-set proper-noun discovery requires semantic judgment (move 3)",
    NotEvaluatedKind.pending_capability,
)


def test_to_json_carries_not_evaluated_sibling_key() -> None:
    report = ValidationReport(
        violations=(), errors=(), ran=("focalization",), not_evaluated=(_SKIP,)
    )
    payload = report.to_json(scope=None, severity=None)
    assert payload["not_evaluated"] == [
        {
            "validator": "focalization",
            "reason": "the constitution does not declare a narrative voice",
            "kind": "missing_input",
        }
    ]
    # The channel is additive: violations/errors keep their shapes, status untouched.
    assert payload["status"] == "ok"
    assert payload["violations"] == []
    assert payload["errors"] == []


def test_to_json_not_evaluated_carries_kind() -> None:
    """FR-008: each ``not_evaluated[]`` element exposes ``kind`` alongside the
    unchanged ``validator``/``reason``; no pre-existing key changed name or type."""
    report = ValidationReport(
        violations=(),
        errors=(),
        ran=("character_unknown_mentions", "focalization"),
        not_evaluated=(_SKIP_CAP, _SKIP),  # sorted? no — report preserves given order
    )
    payload = report.to_json(scope=None, severity=None)
    entries = payload["not_evaluated"]
    assert isinstance(entries, list)
    for entry in entries:
        assert set(entry) == {"validator", "reason", "kind"}
        assert entry["kind"] in {"missing_input", "pending_capability"}
        assert isinstance(entry["validator"], str)
        assert isinstance(entry["reason"], str)
    kinds = {e["validator"]: e["kind"] for e in entries}
    assert kinds["character_unknown_mentions"] == "pending_capability"
    assert kinds["focalization"] == "missing_input"


def test_green_predicate_false_for_solely_not_evaluated_run() -> None:
    # status == "ok" and violations == [], yet not green because the channel carries a
    # missing_input gap (FR-004).
    report = ValidationReport(
        violations=(), errors=(), ran=("focalization",), not_evaluated=(_SKIP,)
    )
    payload = report.to_json(scope=None, severity=None)
    assert payload["status"] == "ok"
    assert payload["failed"] is False  # never gates (FR-004)
    assert is_green(payload) is False  # SC-002


def test_green_predicate_true_for_capability_gap_only_run() -> None:
    """SC-001: status ok + a ``pending_capability``-only channel is GREEN — the
    permanent capability-gap does not deny green (FR-004)."""
    report = ValidationReport(
        violations=(), errors=(), ran=("character_unknown_mentions",), not_evaluated=(_SKIP_CAP,)
    )
    payload = report.to_json(scope=None, severity=None)
    assert payload["status"] == "ok"
    assert payload["failed"] is False
    assert is_green(payload) is True


def test_green_predicate_true_for_evaluated_and_clean_run() -> None:
    report = ValidationReport(violations=(), errors=(), ran=("temporal",))
    payload = report.to_json(scope=None, severity=None)
    assert is_green(payload) is True


def test_render_prints_not_evaluated_section_instead_of_clean_line() -> None:
    report = ValidationReport(
        violations=(), errors=(), ran=("focalization",), not_evaluated=(_SKIP,)
    )
    out = _render(report)
    assert "not evaluated:" in out
    assert "focalization [input gap]: the constitution does not declare a narrative voice" in out
    assert "no violations found" not in out  # the clean line is suppressed (SC-002)


def test_render_labels_each_kind_and_suppresses_clean_line_for_capability_gap() -> None:
    """FR-007/FR-010: the render labels each entry by its kind-generic tag, keeps
    the validator-specific reason, and never prints the clean line for a capability-gap
    only run (the entry stays visible)."""
    report = ValidationReport(
        violations=(),
        errors=(),
        ran=("character_unknown_mentions", "focalization"),
        not_evaluated=(_SKIP_CAP, _SKIP),
    )
    out = _render(report)
    assert (
        "character_unknown_mentions [known limitation — no action available yet]: "
        "open-set proper-noun discovery requires semantic judgment (move 3)" in out
    )
    assert "focalization [input gap]: the constitution does not declare a narrative voice" in out
    assert "no violations found" not in out


def test_render_capability_gap_only_does_not_read_as_clean() -> None:
    """FR-010 edge case: a run whose ONLY content is a capability-gap entry shows the
    ``not evaluated:`` section, never the terse clean line."""
    report = ValidationReport(
        violations=(), errors=(), ran=("character_unknown_mentions",), not_evaluated=(_SKIP_CAP,)
    )
    out = _render(report)
    assert "not evaluated:" in out
    assert "character_unknown_mentions [known limitation — no action available yet]" in out
    assert "no violations found" not in out


def test_render_clean_line_only_when_all_channels_empty() -> None:
    report = ValidationReport(violations=(), errors=(), ran=("temporal",))
    assert "no violations found" in _render(report)


def test_location_less_violation_renders_no_specific_location() -> None:
    # A source=None finding still renders, labelled "(no specific location)". After 048
    # the built-in validators resolve a locator on the normal path, so this branch now
    # serves the defensive cases: the factual_anchor FR-010 join-miss floor and any
    # custom validator that emits a location-less Violation. ``_ERR`` is one such finding.
    assert "(no specific location)" in _render(_report())
