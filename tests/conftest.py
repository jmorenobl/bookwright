"""Shared pytest fixtures for the bookwright test suite."""

import pytest
from typer.testing import CliRunner


@pytest.fixture()
def runner() -> CliRunner:
    """Return a fresh Typer CliRunner instance for each test."""
    return CliRunner()
