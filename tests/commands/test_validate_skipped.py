"""``bookwright validate`` surfaces ingestion-skipped bible files (iteration 046).

When ``map_bible`` omits a bible file with unusable front-matter, that entity never
enters the graph and ``validate`` — the CI gate — would otherwise read the partial
corpus as fully evaluated (``not_evaluated: []``). This suite proves the iteration-046
closure of DEBT-018: each skipped file becomes one ``not_evaluated`` entry with
``validator="ingestion"``, ``kind="missing_input"`` (degrading green via the unchanged
044 predicate) while the exit code stays driven solely by ``error``-severity findings.

In-process via ``typer.testing.CliRunner`` (the harness the other command/E2E tests
use), reusing ``copy_fixture`` / ``is_green`` and the broken-YAML literal proven in
``tests/commands/test_status_errors.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from tests.conftest import copy_fixture, is_green

FIXTURE = "tiny-novel"

# The broken-YAML trigger reused verbatim from test_status_errors.py: map_bible omits
# the file (records it in MapResult.skipped) rather than ingesting a partial entity.
_BROKEN_YAML = "---\nname: : :\n  bad\n---\n"


def _write_broken(project: Path, name: str) -> str:
    """Drop a broken-YAML bible character file; return its project-relative path."""
    (project / "bible" / "characters" / name).write_text(_BROKEN_YAML, encoding="utf-8")
    return f"bible/characters/{name}"


def _validate_payload(cli: CliRunner) -> tuple[int, dict[str, object]]:
    """Run ``validate --json`` in-process; return (exit_code, parsed envelope)."""
    result = cli.invoke(app, ["validate", "--json"])
    payload: dict[str, object] = json.loads(result.stdout)
    return result.exit_code, payload


def _ingestion_entries(payload: dict[str, object]) -> list[dict[str, str]]:
    not_evaluated = payload["not_evaluated"]
    assert isinstance(not_evaluated, list)
    entries: list[dict[str, str]] = [r for r in not_evaluated if r["validator"] == "ingestion"]
    return entries


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copy the source-only ``tiny-novel`` fixture into ``tmp_path``; cwd inside it."""
    root = copy_fixture(FIXTURE, tmp_path)
    monkeypatch.chdir(root)
    return root


# --- User Story 1: a skipped bible file is no longer silently green ----------


def test_one_skip_surfaces_and_denies_green(project: Path, cli: CliRunner) -> None:
    """SC-001 (quickstart Scenario 1): one omitted file → exactly one ingestion
    entry naming it with kind=missing_input, and the run stops reading green."""
    relpath = _write_broken(project, "broken.md")
    cli.invoke(app, ["graph", "build", "--json"])  # writes the partial graph

    exit_code, payload = _validate_payload(cli)
    assert exit_code == 0, payload  # a skip never gates validate (FR-007)

    entries = _ingestion_entries(payload)
    assert len(entries) == 1, payload["not_evaluated"]
    entry = entries[0]
    assert entry["kind"] == "missing_input"  # FR-002 — degrades green
    assert relpath in entry["reason"]  # FR-003 — names the omitted file
    assert is_green(payload) is False  # SC-001 — partial corpus is not clean


def test_skip_alone_does_not_move_the_gate(project: Path, cli: CliRunner) -> None:
    """SC-002 (quickstart Scenario 2): the exit code with a skip equals the exit
    code of the same fixture without the broken file — a skip is not a Violation."""
    no_skip_exit, _ = _validate_payload(cli)

    _write_broken(project, "broken.md")
    cli.invoke(app, ["graph", "build", "--json"])
    skip_exit, _ = _validate_payload(cli)

    assert skip_exit == no_skip_exit  # FR-007 — the gate stays error-driven


def test_two_skips_are_deterministically_ordered(project: Path, cli: CliRunner) -> None:
    """FR-009 (quickstart Scenario 3): two omitted files emit two ingestion entries in
    byte-identical order across runs — the (validator, reason) tie-break resolves the
    shared validator="ingestion"."""
    rel_b = _write_broken(project, "broken_b.md")
    rel_a = _write_broken(project, "broken_a.md")
    cli.invoke(app, ["graph", "build", "--json"])

    _, first = _validate_payload(cli)
    _, second = _validate_payload(cli)

    reasons_first = [r["reason"] for r in _ingestion_entries(first)]
    reasons_second = [r["reason"] for r in _ingestion_entries(second)]
    assert len(reasons_first) == 2
    assert reasons_first == reasons_second  # stable across runs
    # reason carries the unique path, so broken_a sorts before broken_b.
    assert any(rel_a in r for r in reasons_first)
    assert any(rel_b in r for r in reasons_first)
    assert reasons_first == sorted(reasons_first)


# --- User Story 2: the skip is visible on both validate surfaces -------------


def test_json_skip_entry_serializes_with_kind_keys(project: Path, cli: CliRunner) -> None:
    """Story 2 (Acceptance 1): the --json skip entry carries validator/reason/kind —
    the existing NotEvaluatedResult.to_json shape, no new key."""
    _write_broken(project, "broken.md")
    cli.invoke(app, ["graph", "build", "--json"])

    _, payload = _validate_payload(cli)
    entry = _ingestion_entries(payload)[0]
    assert set(entry) == {"validator", "reason", "kind"}


def test_human_report_lists_the_skip(project: Path, cli: CliRunner) -> None:
    """Story 2 (quickstart Scenario 5): without --json the skip appears in the
    ``not evaluated:`` section, missing_input rendered as ``input gap``."""
    relpath = _write_broken(project, "broken.md")
    cli.invoke(app, ["graph", "build", "--json"])

    result = cli.invoke(app, ["validate"])
    assert "not evaluated:" in result.stdout
    assert f"ingestion [input gap]: bible file '{relpath}' skipped" in result.stdout


# --- User Story 3: validate and status agree a skip is reportable ------------


def test_status_and_validate_agree_on_a_skip(project: Path, cli: CliRunner) -> None:
    """SC-004 (quickstart Scenario 6): status still refuses the partial corpus
    (exit 4, skipped_sources) while validate surfaces the same file — different
    pre-existing mechanisms, no shared third channel."""
    relpath = _write_broken(project, "broken.md")
    cli.invoke(app, ["graph", "build", "--json"])

    status_result = cli.invoke(app, ["status", "--json"])
    status_payload = json.loads(status_result.stdout)
    assert status_result.exit_code == 4
    assert status_payload["code"] == "skipped_sources"  # status: a hard refusal

    _, validate_payload = _validate_payload(cli)
    assert any(relpath in r["reason"] for r in _ingestion_entries(validate_payload))


# --- Polish: no-skip byte-identity -------------------------------------------


def test_no_skip_emits_no_ingestion_entry(project: Path, cli: CliRunner) -> None:
    """SC-003 / FR-010 (quickstart Scenario 4): a clean project produces no ingestion
    entry — promoting the sort key reorders nothing on a skip-free run."""
    cli.invoke(app, ["graph", "build", "--json"])

    _, payload = _validate_payload(cli)
    assert _ingestion_entries(payload) == []
