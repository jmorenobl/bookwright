"""The tri-valued validation flow proven end to end (iteration 040, dormant focalization).

Walks ``graph build`` → ``validate --json`` over the source-only
``tiny-undeclared-voice`` fixture — a project whose constitution still carries the
``- **Voz narrativa**: [PENDING: …]`` placeholder a fresh ``bookwright init`` emits.
In-process via ``typer.testing.CliRunner``, the same harness the other E2E tests use
(``copy_fixture`` + ``monkeypatch.chdir``).

The assertion surface is the ``validate --json`` envelope only (SC-001/SC-002):

* ``focalization`` appears in ``not_evaluated[]`` with a legible reason;
* it is **absent** from ``errors[]`` (it did not crash — FR-005);
* the documented green predicate ``status == "ok" AND not_evaluated == []`` is
  **False** (the run is not clean) even though ``violations`` may be empty;
* the gate is not tripped (exit 0): not-evaluated is not a finding (Edge Case "the gate").
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from tests.conftest import copy_fixture

FIXTURE = "tiny-undeclared-voice"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copy the source-only fixture into ``tmp_path`` and ``chdir`` into the copy."""
    root = copy_fixture(FIXTURE, tmp_path)
    monkeypatch.chdir(root)
    return root


def _is_green(payload: dict[str, object]) -> bool:
    """The single documented green predicate (SC-002)."""
    return payload["status"] == "ok" and payload["not_evaluated"] == []


def test_dormant_focalization_is_not_evaluated_not_green(project: Path, cli: CliRunner) -> None:
    assert cli.invoke(app, ["graph", "build", "--json"]).exit_code == 0

    result = cli.invoke(app, ["validate", "--json"])
    assert result.exit_code == 0, result.stdout  # not-evaluated never gates (FR-004)
    payload = json.loads(result.stdout)

    skipped = {r["validator"]: r["reason"] for r in payload["not_evaluated"]}
    assert "focalization" in skipped  # SC-001: the dormant validator declares itself
    assert skipped["focalization"]  # a legible, non-empty reason
    assert "focalization" not in {e["validator"] for e in payload["errors"]}  # FR-005
    assert _is_green(payload) is False  # SC-002: not-evaluated ⇒ not clean
