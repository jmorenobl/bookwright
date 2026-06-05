"""manifest_version gate — FR-012, SC-003."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from bookwright.core import Manifest, ManifestValidationError

from .conftest import load_fixture


def test_installed_too_old_is_rejected(installed_version: Callable[[str], None]) -> None:
    """FR-012: an underpowered CLI refuses to load a future-cli_version_min manifest."""

    installed_version("0.0.1")
    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("future_cli_version.toml"))
    failure = exc_info.value.failures[0]
    assert failure.field_path == "bookwright.cli_version_min"
    assert failure.rule_id == "bookwright.cli_version_min.installed_too_old"
    assert "0.0.1" in failure.message
    assert "9999.0.0" in failure.message


def test_installed_at_or_above_required_loads(
    installed_version: Callable[[str], None],
) -> None:
    """FR-012: when installed >= required, validation continues normally."""

    installed_version("9999.0.0")
    m = Manifest.load(load_fixture("future_cli_version.toml"))
    assert m.bookwright.cli_version_min == "9999.0.0"
    assert m.book.title == "Future CLI"


def test_installed_strictly_higher_loads(
    installed_version: Callable[[str], None],
) -> None:
    """Installed > required also loads cleanly."""

    installed_version("9999.0.1")
    m = Manifest.load(load_fixture("future_cli_version.toml"))
    assert m.book.title == "Future CLI"


def test_installed_not_pep440_is_rejected(installed_version: Callable[[str], None]) -> None:
    """FR-012: non-PEP-440 installed version surfaces as a model-level failure."""

    installed_version("not-a-version")
    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.load(load_fixture("valid_minimal.toml"))
    failure = exc_info.value.failures[0]
    assert failure.field_path == "bookwright.cli_version_min"
    assert failure.rule_id == "bookwright.cli_version_min.installed_not_pep440"
    assert "not-a-version" in failure.message
