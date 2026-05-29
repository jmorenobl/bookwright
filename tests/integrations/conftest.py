"""Shared fixtures for ``tests/integrations/``."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from bookwright.core import Manifest
from bookwright.integrations import INTEGRATION_REGISTRY


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Return a fresh, empty project root inside the test's ``tmp_path``."""

    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def minimal_manifest() -> Manifest:
    """Build the smallest valid Manifest the integrations layer's signatures accept.

    The integrations layer treats the ``manifest`` argument as opaque in v0
    (the v0 ``setup()`` body never reads it). Using the iteration-2
    ``Manifest.build`` keeps the fixture honest — it returns the real type.
    """

    return Manifest.build(
        title="Fixture Book",
        authors=["Fixture Author"],
        integration_key="claude",
        uri_base="https://example.org/fixture/",
        language="en",
        type="novel",
        status="idea",
    )


@pytest.fixture
def registry_snapshot() -> Iterator[dict[str, Any]]:
    """Snapshot ``INTEGRATION_REGISTRY`` and restore it on teardown.

    Lets US5 tests safely mutate the registry (insert ``FakeIntegration``)
    without bleeding into other tests in the suite.
    """

    snapshot = dict(INTEGRATION_REGISTRY)
    try:
        yield snapshot
    finally:
        INTEGRATION_REGISTRY.clear()
        INTEGRATION_REGISTRY.update(snapshot)
