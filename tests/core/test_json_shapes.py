"""FR-024: JSON shapes for exceptions and warnings (contracts/manifest_api.md)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from bookwright.core import (
    Manifest,
    ManifestNotFoundError,
    ManifestOverwriteError,
    ManifestSyntaxError,
    ManifestValidationError,
    ManifestWarning,
)

from .conftest import load_fixture


def _roundtrip(obj: dict[str, Any]) -> dict[str, Any]:
    """JSON-serialize and reload to confirm the shape is JSON-clean."""

    return cast(dict[str, Any], json.loads(json.dumps(obj)))


def test_manifest_validation_error_json_shape() -> None:
    """`ManifestValidationError.to_json()` matches the contract."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("invalid_multi_error.toml"))
    payload = _roundtrip(exc_info.value.to_json())

    assert payload["status"] == "error"
    assert payload["code"] == "manifest_validation"
    # The one error that gains a top-level message under normalization (the
    # existing summary string) — required by the canonical envelope.
    assert isinstance(payload["message"], str) and payload["message"]
    failures = payload["details"]["failures"]
    assert isinstance(failures, list)
    assert len(failures) >= 1
    for failure in failures:
        assert set(failure.keys()) == {"field", "value", "rule", "message"}
        assert isinstance(failure["field"], str)
        assert isinstance(failure["rule"], str)
        assert isinstance(failure["message"], str)


def test_manifest_warning_json_shape() -> None:
    """`ManifestWarning.to_json()` matches the contract."""

    warning = ManifestWarning(
        rule_id="manifest_version.unknown_future",
        field_path="bookwright.manifest_version",
        offending_value="9",
        message="manifest_version 9 is newer than this CLI knows about",
    )
    payload = _roundtrip(warning.to_json())
    assert payload == {
        "rule": "manifest_version.unknown_future",
        "field": "bookwright.manifest_version",
        "value": "9",
        "message": "manifest_version 9 is newer than this CLI knows about",
    }


def test_manifest_syntax_error_json_shape(tmp_path: Path) -> None:
    """`ManifestSyntaxError.to_json()` matches the contract."""

    bad = tmp_path / "broken.toml"
    bad.write_text("= = not toml", encoding="utf-8")
    with pytest.raises(ManifestSyntaxError) as exc_info:
        Manifest.load(bad)
    payload = _roundtrip(exc_info.value.to_json())
    assert payload["status"] == "error"
    assert payload["code"] == "manifest_syntax"
    assert payload["message"]
    details = payload["details"]
    assert details["field"].startswith("bookwright.")
    # line/column may be int or null per the contract.
    assert details["line"] is None or isinstance(details["line"], int)
    assert details["column"] is None or isinstance(details["column"], int)


def test_manifest_not_found_error_json_shape(tmp_path: Path) -> None:
    """`ManifestNotFoundError.to_json()` matches the contract."""

    target = tmp_path / "missing.toml"
    with pytest.raises(ManifestNotFoundError) as exc_info:
        Manifest.load(target)
    payload = _roundtrip(exc_info.value.to_json())
    assert payload["status"] == "error"
    assert payload["code"] == "manifest_not_found"
    assert payload["details"]["path"].endswith("missing.toml")
    assert payload["message"]


def test_manifest_overwrite_error_json_shape(tmp_path: Path) -> None:
    """`ManifestOverwriteError.to_json()` matches the contract."""

    target = tmp_path / "manifest.toml"
    target.write_text("# preexisting\n", encoding="utf-8")
    m = Manifest.build(
        title="X",
        authors=["A"],
        integration_key="claude",
        uri_base="https://example.org/x/",
    )
    with pytest.raises(ManifestOverwriteError) as exc_info:
        m.dump(target)
    payload = _roundtrip(exc_info.value.to_json())
    assert payload["status"] == "error"
    assert payload["code"] == "manifest_overwrite_refused"
    assert payload["details"]["path"].endswith("manifest.toml")
    assert "refuse to overwrite" in payload["message"]
