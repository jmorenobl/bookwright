"""Shared fixtures for the GOLEM domain-model suite.

The canonical project base used across the user-story examples (spec US1). Per
-concept sample entities are introduced by the phases that add those classes.
"""

from __future__ import annotations

import pytest

B = "https://example.org/my-book/"
"""Canonical project URI base (absolute http(s), trailing slash)."""


@pytest.fixture
def uri_base() -> str:
    """The project namespace base used by every construction example."""
    return B
