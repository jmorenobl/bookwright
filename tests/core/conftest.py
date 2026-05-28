"""Shared fixtures for `tests/core/`."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

import bookwright.core.manifest as manifest_module

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_manifest(tmp_path: Path) -> Callable[[str], Path]:
    """Return a helper that writes the given TOML body to a temp manifest file."""

    def _write(body: str, name: str = "manifest.toml") -> Path:
        target = tmp_path / name
        target.write_text(body, encoding="utf-8")
        return target

    return _write


@pytest.fixture
def installed_version(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str], None]]:
    """Monkey-patch `_installed_version()` to a caller-supplied PEP 440 string."""

    def _set(version: str) -> None:
        monkeypatch.setattr(manifest_module, "_installed_version", lambda: version)

    yield _set


def load_fixture(name: str) -> Path:
    """Resolve a path under `tests/core/fixtures/`."""

    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"missing fixture: {path}")
    return path
