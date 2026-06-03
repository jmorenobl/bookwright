"""E2E package harness — re-exports the root helpers and adds an empty workdir.

The ``cli`` and ``runner`` fixtures and :func:`copy_fixture` live in the root
``tests/conftest.py`` (T004) and are already visible here; this module re-exports
``copy_fixture``/``FIXTURES_DIR`` so an E2E module can import them by name, and adds
the ``workdir`` fixture used by the init-from-scratch tests (C1/C2/C3).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import FIXTURES_DIR, copy_fixture

__all__ = ["FIXTURES_DIR", "copy_fixture", "workdir"]


@pytest.fixture()
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty directory set as cwd — the starting point for a fresh ``init``.

    The E2E tests that drive ``init <name>`` (rather than a committed fixture)
    need an empty, writable cwd; this provides one inside the test's ``tmp_path``
    and ``chdir``s into it so ``find_project_root`` resolves the created project.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path
