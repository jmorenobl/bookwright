"""US5 - Acceptance Scenarios 1-3 (FR-013, FR-014, SC-006)."""

from __future__ import annotations

import pytest

from bookwright.core import Manifest, ManifestValidationError

from .conftest import load_fixture


def test_future_manifest_version_attaches_one_warning(capsys: pytest.CaptureFixture[str]) -> None:
    """FR-013 + AS1: a future `manifest_version` yields exactly one warning."""

    m = Manifest.load(load_fixture("future_manifest_version.toml"))
    assert len(m.warnings) == 1
    warning = m.warnings[0]
    assert warning.rule_id == "manifest_version.unknown_future"
    assert warning.field_path == "bookwright.manifest_version"
    assert warning.offending_value == "9"
    assert "9" in warning.message
    assert "max known: 1" in warning.message

    # Every recognised field is still populated (best-effort load).
    assert m.book.title == "Future Manifest"
    assert m.book.authors == ["Forward Thinker"]
    assert m.bookwright.uri_base == "https://example.org/future-mv/"

    # SC-006: the model layer must not write to stdout/stderr.
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_known_manifest_version_has_no_warning() -> None:
    """FR-014 + AS2: known `manifest_version` loads with no warning."""

    m = Manifest.load(load_fixture("valid_minimal.toml"))
    assert m.warnings == ()


def test_missing_manifest_version_raises_validation_error() -> None:
    """AS3 / regression guard: a missing manifest_version still fails (US2 path)."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("invalid_bookwright_missing_manifest_version.toml"))
    assert any(
        f.field_path == "bookwright.manifest_version" and f.rule_id.endswith(".missing")
        for f in exc_info.value.failures
    )


def test_malformed_manifest_version_raises_validation_error() -> None:
    """A malformed manifest_version (e.g. '1.0') still fails (US2 path)."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("invalid_manifest_version_dotted.toml"))
    assert any(
        f.field_path == "bookwright.manifest_version"
        and f.rule_id == "bookwright.manifest_version.not_positive_integer_string"
        for f in exc_info.value.failures
    )
