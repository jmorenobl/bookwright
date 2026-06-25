"""The tri-valued validation flow proven end to end (iteration 040, dormant focalization).

Walks ``graph build`` → ``validate --json`` over the source-only
``tiny-undeclared-voice`` fixture — a project whose constitution still carries the
``- **Voz narrativa**: [PENDING: …]`` placeholder a fresh ``bookwright init`` emits.
In-process via ``typer.testing.CliRunner``, the same harness the other E2E tests use
(``copy_fixture`` + ``monkeypatch.chdir``).

The assertion surface is the ``validate --json`` envelope only (SC-001/SC-002):

* ``focalization`` appears in ``not_evaluated[]`` with a legible reason;
* it is **absent** from ``errors[]`` (it did not crash — FR-005);
* the refined green predicate (``status == "ok" AND no not_evaluated entry has
  kind == "missing_input"``, iteration 044) is **False** here — ``focalization``'s gap is
  ``missing_input`` — even though ``violations`` may be empty; a clean fixture, by
  contrast, reads green despite carrying the ``pending_capability`` abstainer entry;
* the gate is not tripped (exit 0): not-evaluated is not a finding (Edge Case "the gate").
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from tests.conftest import copy_fixture, is_green

FIXTURE = "tiny-undeclared-voice"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copy the source-only fixture into ``tmp_path`` and ``chdir`` into the copy."""
    root = copy_fixture(FIXTURE, tmp_path)
    monkeypatch.chdir(root)
    return root


def test_dormant_focalization_is_not_evaluated_not_green(project: Path, cli: CliRunner) -> None:
    assert cli.invoke(app, ["graph", "build", "--json"]).exit_code == 0

    result = cli.invoke(app, ["validate", "--json"])
    assert result.exit_code == 0, result.stdout  # not-evaluated never gates (FR-004)
    payload = json.loads(result.stdout)

    skipped = {r["validator"]: r for r in payload["not_evaluated"]}
    assert "focalization" in skipped  # SC-001: the dormant validator declares itself
    assert skipped["focalization"]["reason"]  # a legible, non-empty reason
    # focalization's gap is input-conditional — a missing voice declaration (FR-002).
    assert skipped["focalization"]["kind"] == "missing_input"
    assert "focalization" not in {e["validator"] for e in payload["errors"]}  # FR-005
    # The capability-gap abstainer is present but is pending_capability (it does not deny green).
    assert skipped["character_unknown_mentions"]["kind"] == "pending_capability"
    assert is_green(payload) is False  # SC-002: the missing_input gap ⇒ not clean


# The capability-gap entries each clean fixture carries, keyed by ``(validator, code)``
# (iteration 053 — a single validator now emits MORE THAN ONE abstention, so the bare
# ``validator`` key would silently collapse them into a false green). A third-person-LIMITED
# voice carries THREE: the open-set ``undeclared_characters`` plus ``focalization``'s
# ``head_hopping`` AND ``first_person_recall`` (iteration 045 head-hopping + iteration 053
# recall honesty). A first-person voice carries only the open-set abstainer (focalization
# evaluates with no findings, no recall ceiling to declare). All are ``pending_capability``
# and none denies green (SC-002/SC-005).
_EXPECTED_GAPS = {
    "tiny-novel": {  # third person limited → open-set + head-hop + first-person-recall
        ("character_unknown_mentions", "undeclared_characters"): "pending_capability",
        ("focalization", "head_hopping"): "pending_capability",
        ("focalization", "first_person_recall"): "pending_capability",
    },
    "tiny-memoir": {  # first person → only the open-set abstainer
        ("character_unknown_mentions", "undeclared_characters"): "pending_capability",
    },
}


@pytest.mark.parametrize("fixture", ["tiny-novel", "tiny-memoir"])
def test_clean_fixture_is_green_under_refined_predicate(
    fixture: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cli: CliRunner
) -> None:
    """SC-001/SC-005: a clean fixture reads GREEN under the refined predicate even
    though it carries permanent ``pending_capability`` entries — the durable regression
    guard 043 lacked (nothing asserted green on a real clean run). A third-limited
    fixture carries both ``character_unknown_mentions`` and ``focalization``; a
    first-person fixture carries only ``character_unknown_mentions`` (iteration 045)."""
    root = copy_fixture(fixture, tmp_path)
    monkeypatch.chdir(root)

    assert cli.invoke(app, ["graph", "build", "--json"]).exit_code == 0
    result = cli.invoke(app, ["validate", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)

    # The not_evaluated entries are exactly the expected capability-gaps for this voice,
    # keyed by (validator, code) so the two focalization entries stay distinct (iter 053).
    entries = {(r["validator"], r["code"]): r["kind"] for r in payload["not_evaluated"]}
    assert entries == _EXPECTED_GAPS[fixture], payload["not_evaluated"]
    assert is_green(payload) is True  # SC-001: clean project reads green again
