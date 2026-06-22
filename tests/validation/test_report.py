"""``ValidationReport`` filtering, gate, and JSON shape (D13.3).

Also covers the additive ``not_evaluated`` channel + the documented green predicate
(iteration 040, SC-002): a non-empty channel makes a run non-green even when
``status == "ok"``.
"""

from __future__ import annotations

import io

from rich.console import Console

from bookwright.validation.base import (
    NotEvaluatedResult,
    Severity,
    ValidatorError,
    Violation,
)
from bookwright.validation.report import ScopeFilter, ValidationReport


def _is_green(payload: dict[str, object]) -> bool:
    """The single documented predicate (SC-002): ok AND nothing not-evaluated."""
    return payload["status"] == "ok" and payload["not_evaluated"] == []


def _render(report: ValidationReport) -> str:
    console = Console(file=io.StringIO(), width=200)
    report.render(console, scope=None, severity=None)
    return console.file.getvalue()  # type: ignore[attr-defined]

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


def test_to_json_carries_not_evaluated_sibling_key() -> None:
    report = ValidationReport(violations=(), errors=(), ran=("focalization",), not_evaluated=(_SKIP,))
    payload = report.to_json(scope=None, severity=None)
    assert payload["not_evaluated"] == [
        {"validator": "focalization", "reason": "the constitution does not declare a narrative voice"}
    ]
    # The channel is additive: violations/errors keep their shapes, status untouched.
    assert payload["status"] == "ok"
    assert payload["violations"] == []
    assert payload["errors"] == []


def test_green_predicate_false_for_solely_not_evaluated_run() -> None:
    # status == "ok" and violations == [], yet not green because the channel is non-empty.
    report = ValidationReport(violations=(), errors=(), ran=("focalization",), not_evaluated=(_SKIP,))
    payload = report.to_json(scope=None, severity=None)
    assert payload["status"] == "ok"
    assert payload["failed"] is False  # never gates (FR-004)
    assert _is_green(payload) is False  # SC-002


def test_green_predicate_true_for_evaluated_and_clean_run() -> None:
    report = ValidationReport(violations=(), errors=(), ran=("temporal",))
    payload = report.to_json(scope=None, severity=None)
    assert _is_green(payload) is True


def test_render_prints_not_evaluated_section_instead_of_clean_line() -> None:
    report = ValidationReport(violations=(), errors=(), ran=("focalization",), not_evaluated=(_SKIP,))
    out = _render(report)
    assert "not evaluated:" in out
    assert "focalization: the constitution does not declare a narrative voice" in out
    assert "no violations found" not in out  # the clean line is suppressed (SC-002)


def test_render_clean_line_only_when_all_channels_empty() -> None:
    report = ValidationReport(violations=(), errors=(), ran=("temporal",))
    assert "no violations found" in _render(report)
