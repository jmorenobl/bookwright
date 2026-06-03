"""``ValidationReport`` filtering, gate, and JSON shape (T031, D13.3)."""

from __future__ import annotations

from bookwright.validation.base import Severity, ValidatorError, Violation
from bookwright.validation.report import ScopeFilter, ValidationReport

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
