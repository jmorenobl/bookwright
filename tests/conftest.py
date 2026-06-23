"""Shared pytest fixtures and the E2E harness for the bookwright test suite.

The harness (D1/D2) is two pieces both consumed by the fixture-validity
tests (``tests/fixtures/``) and the E2E suite (``tests/e2e/``):

* :func:`copy_fixture` — copy a committed fixture project into a test's
  ``tmp_path`` with ``shutil.copytree`` so the real CLI can ``graph build`` the
  derived ``bible/graph.ttl`` in a throwaway copy, never mutating the committed
  source tree (Principle I / D2 / R1).
* the :func:`cli` fixture — a fresh ``typer.testing.CliRunner`` for driving
  ``bookwright.cli:app`` **in-process**, so every assertion contributes to the
  ``--cov`` measurement (FR-009 / D1).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

#: Root of the committed fixture projects (``tests/fixtures/<name>/``).
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def runner() -> CliRunner:
    """Return a fresh Typer CliRunner instance for each test."""
    return CliRunner()


@pytest.fixture()
def cli() -> CliRunner:
    """A fresh CliRunner for driving ``bookwright.cli:app`` in-process (D1).

    The new fixture/E2E tests invoke as ``cli.invoke(app, [...])`` — the same
    in-process path the ``bookwright`` console-script uses, so coverage is faithful
    (FR-009). The CLI commands resolve the project from the working directory, so a
    caller sets ``cwd`` (e.g. ``monkeypatch.chdir(project)``) before invoking.
    """
    return CliRunner()


def is_green(payload: dict[str, object]) -> bool:
    """The single documented green predicate, refined by kind (SC-002, iteration 044).

    Green ⟺ ``status == "ok"`` AND no ``not_evaluated`` entry is a ``missing_input``
    gap. A ``pending_capability`` entry stays listed but does **not** deny green
    (FR-004). Canonical here so the two consumers (the ``report`` unit suite and the
    tri-valued E2E suite) cannot drift — it is a test helper, not a code property, the
    same shape iteration 040 shipped.
    """
    not_evaluated = payload["not_evaluated"]
    assert isinstance(not_evaluated, list)
    return payload["status"] == "ok" and not any(
        r["kind"] == "missing_input" for r in not_evaluated
    )


def copy_fixture(name: str, dest_parent: Path) -> Path:
    """Copy the committed fixture ``name`` into ``dest_parent``; return the copy.

    Uses ``shutil.copytree`` so the committed fixture is never mutated and the
    derived ``bible/graph.ttl`` is materialized only in this throwaway copy
    (D2 / R1). ``dest_parent`` must be a test's ``tmp_path`` (or a child of it);
    the helper writes only under it. Raises ``FileNotFoundError`` for an unknown
    fixture so a typo fails loudly rather than silently testing nothing.
    """
    source = FIXTURES_DIR / name
    if not source.is_dir():
        raise FileNotFoundError(f"unknown fixture {name!r} under {FIXTURES_DIR}")
    destination = dest_parent / name
    shutil.copytree(source, destination)
    return destination
