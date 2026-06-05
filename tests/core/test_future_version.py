"""Future manifest_version handling — FR-013, FR-014, SC-006."""

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
    """AS3 / regression guard: a missing manifest_version still fails."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("invalid_bookwright_missing_manifest_version.toml"))
    assert any(
        f.field_path == "bookwright.manifest_version" and f.rule_id.endswith(".missing")
        for f in exc_info.value.failures
    )


def test_malformed_manifest_version_raises_validation_error() -> None:
    """A malformed manifest_version (e.g. '1.0') still fails."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("invalid_manifest_version_dotted.toml"))
    assert any(
        f.field_path == "bookwright.manifest_version"
        and f.rule_id == "bookwright.manifest_version.not_positive_integer_string"
        for f in exc_info.value.failures
    )


def test_unknown_key_in_bookwright_still_raises() -> None:
    """Contract: forward-compat is `manifest_version`-deep only.

    A future `manifest_version` paired with an unknown key inside a
    known block (`[bookwright]`) MUST raise `ManifestValidationError`
    with rule `bookwright.<key>.unknown_key` — the `extra="forbid"`
    barrier fires *before* `_classify_manifest_version_warnings` runs,
    so the documented "best-effort" forward-compat warning never
    surfaces in this case. Pins the boundary documented in
    `contracts/manifest_api.md` §`Manifest.load`/Forward-compat.
    """

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("future_manifest_version_unknown_key.toml"))
    failures_by_path = {f.field_path: f for f in exc_info.value.failures}
    assert "bookwright.lock_file" in failures_by_path
    assert failures_by_path["bookwright.lock_file"].rule_id == ("bookwright.lock_file.unknown_key")
    # Sanity: the model never reaches `_classify_manifest_version_warnings`,
    # so no forward-compat warning rule sneaks in alongside the hard failure.
    assert not any(
        f.rule_id.startswith("manifest_version.unknown_future") for f in exc_info.value.failures
    )
