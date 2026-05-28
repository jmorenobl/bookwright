"""US2 - Acceptance Scenarios 1-9 (FR-002, FR-004 through FR-011, FR-013 parse failure)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from bookwright.core import (
    Manifest,
    ManifestNotFoundError,
    ManifestSyntaxError,
    ManifestValidationError,
)
from bookwright.core.errors import _FieldFailure

from .conftest import load_fixture


def _rule_ids(exc: ManifestValidationError) -> list[str]:
    return [f.rule_id for f in exc.failures]


def _failure_for(exc: ManifestValidationError, field_path: str) -> _FieldFailure:
    matches = [f for f in exc.failures if f.field_path == field_path]
    if not matches:
        raise AssertionError(f"expected a failure at {field_path}; got {_rule_ids(exc)}")
    return matches[0]


@pytest.mark.parametrize(
    ("fixture", "field_path", "rule_id"),
    [
        ("invalid_book_title_missing.toml", "book.title", "book.title.missing"),
        ("invalid_book_type_bad.toml", "book.type", "book.type.not_in_enum"),
        ("invalid_book_language_klingon.toml", "book.language", "book.language.not_iso_639_1"),
        ("invalid_book_authors_empty.toml", "book.authors", "book.authors.empty"),
        (
            "invalid_book_authors_blank_entry.toml",
            "book.authors[1]",
            "book.authors.entry.empty",
        ),
        ("invalid_book_status_wip.toml", "book.status", "book.status.not_in_enum"),
        (
            "invalid_uri_base_no_scheme.toml",
            "bookwright.uri_base",
            "bookwright.uri_base.wrong_scheme",
        ),
        (
            "invalid_uri_base_no_trailing_slash.toml",
            "bookwright.uri_base",
            "bookwright.uri_base.no_trailing_slash",
        ),
        (
            "invalid_uri_base_has_query.toml",
            "bookwright.uri_base",
            "bookwright.uri_base.has_query",
        ),
        (
            "invalid_uri_base_has_fragment.toml",
            "bookwright.uri_base",
            "bookwright.uri_base.has_fragment",
        ),
        (
            "invalid_uri_base_malformed_ipv6.toml",
            "bookwright.uri_base",
            "bookwright.uri_base.invalid_uri",
        ),
        (
            "invalid_uri_base_empty_host.toml",
            "bookwright.uri_base",
            "bookwright.uri_base.empty_host",
        ),
        (
            "invalid_bookwright_schema_version_empty.toml",
            "bookwright.schema_version",
            "bookwright.schema_version.empty",
        ),
        (
            "invalid_cli_version_min_v1.toml",
            "bookwright.cli_version_min",
            "bookwright.cli_version_min.not_pep440",
        ),
        (
            "invalid_manifest_version_dotted.toml",
            "bookwright.manifest_version",
            "bookwright.manifest_version.not_positive_integer_string",
        ),
        (
            "invalid_manifest_version_zero.toml",
            "bookwright.manifest_version",
            "bookwright.manifest_version.not_positive_integer_string",
        ),
    ],
)
def test_single_rule_fixtures(fixture: str, field_path: str, rule_id: str) -> None:
    """Each invalid fixture raises with the expected field path and rule id."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture(fixture))
    failure = _failure_for(exc_info.value, field_path)
    assert failure.rule_id == rule_id


@pytest.mark.parametrize(
    ("fixture", "field_path"),
    [
        ("invalid_bookwright_missing_uri_base.toml", "bookwright.uri_base"),
        ("invalid_bookwright_missing_schema_version.toml", "bookwright.schema_version"),
        (
            "invalid_bookwright_missing_manifest_version.toml",
            "bookwright.manifest_version",
        ),
        (
            "invalid_bookwright_missing_cli_version_min.toml",
            "bookwright.cli_version_min",
        ),
    ],
)
def test_missing_required_bookwright_fields(fixture: str, field_path: str) -> None:
    """FR-010: every required `[bookwright]` key reports its own missing failure."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture(fixture))
    failure = _failure_for(exc_info.value, field_path)
    assert failure.rule_id.endswith(".missing")


def test_multi_error_surfaces_all_failures() -> None:
    """FR-011 / SC-007: independent failures accumulate in one raise."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("invalid_multi_error.toml"))
    rule_ids = _rule_ids(exc_info.value)
    # At least three independent failures from different fields.
    assert len(rule_ids) >= 3  # noqa: PLR2004
    assert {f.field_path for f in exc_info.value.failures} >= {
        "book.title",
        "book.language",
        "bookwright.uri_base",
    }


def test_missing_file_raises_not_found(tmp_path: Path) -> None:
    """FR-002: a missing manifest raises `ManifestNotFoundError`."""

    target = tmp_path / "does-not-exist.toml"
    with pytest.raises(ManifestNotFoundError) as exc_info:
        Manifest.load(target)
    assert exc_info.value.path.name == "does-not-exist.toml"


def test_syntax_error_raises_syntax_error(
    tmp_manifest: Callable[[str], Path],
) -> None:
    """FR-002: invalid TOML raises `ManifestSyntaxError`."""

    body = "this is = = not = toml"
    path = tmp_manifest(body)
    with pytest.raises(ManifestSyntaxError) as exc_info:
        Manifest.load(path)
    assert exc_info.value.message  # non-empty
