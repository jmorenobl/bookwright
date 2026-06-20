"""``bookwright status`` — fixture-driven command flow (020, user stories 1-3).

Facts against the known-state ``tiny-historical`` fixture (cross-checked with
the owning tools, SC-003), graceful degradation (FR-013/SC-006), the exact
``next_actions``, the ``--json``/cache byte-identity contract (SC-002), and
corpus safety (SC-007). Error paths live in
``test_status_errors.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from rdflib import Graph
from typer.testing import CliRunner

from bookwright.cli import app
from tests.commands.conftest import dirhash
from tests.commands.graph.conftest import scaffold_project
from tests.conftest import copy_fixture


def _status_json(runner: CliRunner) -> tuple[int, dict[str, Any]]:
    result = runner.invoke(app, ["status", "--json"])
    return result.exit_code, json.loads(result.stdout)


@pytest.fixture()
def tiny_historical(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch copy of the research E2E fixture, cwd inside it."""
    root = copy_fixture("tiny-historical", tmp_path)
    monkeypatch.chdir(root)
    return root


# --- Story 1: facts on a known-state corpus ------------------------------------


def test_known_state_facts_match_the_fixture(tiny_historical: Path, runner: CliRunner) -> None:
    exit_code, payload = _status_json(runner)
    assert exit_code == 0
    state = payload["state"]
    assert state["phase"] == "drafting"
    assert state["graph"]["available"] is True
    assert state["graph"]["entities"] > 0

    questions = state["open_questions"]
    assert questions["count"] == 2
    assert [q["id"] for q in questions["items"]] == ["q-libro-de-jornales", "q-origen-telares"]
    assert all(q["file"] == "bible/research/_index.md" for q in questions["items"])

    anchors = state["unresolved_anchors"]
    assert anchors["count"] == 1
    assert anchors["items"][0]["promotes"] == "rumor-incendio"
    assert anchors["items"][0]["problems"] == ["under_reliable"]
    assert anchors["items"][0]["file"] == "bible/research/telar-y-fabrica.md"

    low = state["low_reliability_findings"]
    assert low["count"] == 1
    assert low["items"][0] == {
        "id": "rumor-incendio",
        "best_reliability": "baja",
        "file": "bible/research/telar-y-fabrica.md",
    }

    assert state["validation"]["counts"]["error"] >= 1
    assert len(state["validation"]["ran"]) == 6


def test_facts_agree_with_the_owning_tools(tiny_historical: Path, runner: CliRunner) -> None:
    # SC-003 parity: validation counts ≡ `validate --json` by_severity
    # on the corpus status just rebuilt; focus ≡ `focus show --json`.
    _, payload = _status_json(runner)
    validate = runner.invoke(app, ["validate", "--json"])
    by_severity = json.loads(validate.stdout)["summary"]["by_severity"]
    assert payload["state"]["validation"]["counts"] == by_severity

    focus = runner.invoke(app, ["focus", "show", "--json"])
    assert payload["focus"] == json.loads(focus.stdout)["focus"]


def test_v02_era_project_succeeds_with_empty_research_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    # SC-006: no [focus], no bible/research/ — a v0.2-era corpus degrades, never errors.
    root = copy_fixture("tiny-novel", tmp_path)
    monkeypatch.chdir(root)
    exit_code, payload = _status_json(runner)
    assert exit_code == 0
    assert payload["focus"] is None
    state = payload["state"]
    for fact in ("open_questions", "unresolved_anchors", "low_reliability_findings"):
        assert state[fact] == {"count": 0, "items": []}
    # never a research/verify action on a research-free corpus
    assert all(
        action["skill"] not in {"bookwright-research", "bookwright-verify"}
        for action in payload["next_actions"]
    )


def test_stale_graph_cache_is_refreshed_from_the_corpus(
    tiny_historical: Path, runner: CliRunner
) -> None:
    # Stale-cache acceptance (FR-001): the on-disk graph.ttl is junk; the report
    # still reflects the corpus because status rebuilds (D1), and the refresh
    # leaves a valid Turtle cache behind.
    graph_file = tiny_historical / "bible" / "graph.ttl"
    graph_file.write_text("# stale junk, not the corpus\n", encoding="utf-8")
    exit_code, payload = _status_json(runner)
    assert exit_code == 0
    assert payload["state"]["graph"]["entities"] > 0
    refreshed = Graph()
    refreshed.parse(str(graph_file), format="turtle")
    assert len(refreshed) == payload["state"]["graph"]["triples"]


def test_degraded_no_bible_project_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.chdir(scaffold_project(tmp_path / "bare", with_bible=False))
    exit_code, payload = _status_json(runner)
    assert exit_code == 0
    state = payload["state"]
    assert state["graph"] == {"available": False, "entities": 0, "triples": 0}
    assert state["open_questions"] == {"count": 0, "items": []}
    assert state["validation"] == {
        "counts": {"error": 0, "warning": 0, "info": 0},
        "ran": [],
    }
    # D5 short-circuit: at most the single bootstrap action.
    assert [a["skill"] for a in payload["next_actions"]] == ["bookwright-bible"]


def test_human_mode_prints_the_report_on_stdout(tiny_historical: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "phase: drafting" in result.stdout
    assert "open questions (2):" in result.stdout
    assert "next actions:" in result.stdout


# --- Story 2: deterministic next actions ----------------------------------------


def test_known_state_yields_the_exact_next_actions(
    tiny_historical: Path, runner: CliRunner
) -> None:
    _, payload = _status_json(runner)
    actions = payload["next_actions"]
    # The fixture carries an authored [focus] block (iteration 023), so rule ⑤
    # (define_focus) does NOT fire — exactly three research-derived workstreams remain.
    assert [a["skill"] for a in actions] == [
        "bookwright-research",
        "bookwright-verify",
        "bookwright-continuity",
    ]
    research = actions[0]
    # The prompt lists the queue; the reason cites the count (FR-009).
    assert research["reason"] == "2 open research questions and 1 unresolved anchor"
    assert "q-libro-de-jornales" in research["prompt"]
    assert "q-origen-telares" in research["prompt"]
    assert "rumor-incendio" in research["prompt"]
    # With a focus defined, the define-focus recommendation is absent.
    assert all(a["skill"] != "bookwright focus set" for a in actions)
    # SC-004: each action carries all three non-empty components.
    assert all(a["skill"] and a["prompt"] and a["reason"] for a in actions)


# --- Story 3: JSON contract + cache (SC-002) -------------------------------------


def test_json_stdout_is_one_document_with_the_contract_keys(
    tiny_historical: Path, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)  # parses ⇒ nothing else on stdout (FR-011)
    assert list(payload) == ["status", "focus", "state", "next_actions"]
    assert payload["status"] == "ok"


def test_double_run_is_byte_identical_and_stdout_equals_cache(
    tiny_historical: Path, runner: CliRunner
) -> None:
    cache = tiny_historical / ".bookwright" / "cache" / "status.json"
    first = runner.invoke(app, ["status", "--json"])
    cache_first = cache.read_bytes()
    second = runner.invoke(app, ["status", "--json"])
    cache_second = cache.read_bytes()
    # SC-002: identical bytes across runs, and stdout ≡ cache —
    # even though bible/graph.ttl was rewritten with fresh minted URIs.
    assert first.stdout == second.stdout
    assert cache_first == cache_second
    assert first.stdout.encode("utf-8") == cache_first


def test_human_mode_also_regenerates_the_cache(tiny_historical: Path, runner: CliRunner) -> None:
    # FR-012: the cache is a side effect of every successful run, both modes;
    # the missing .bookwright/cache/ directory is created on demand.
    cache = tiny_historical / ".bookwright" / "cache" / "status.json"
    assert not cache.exists()
    json_run = runner.invoke(app, ["status", "--json"])
    json_bytes = cache.read_bytes()
    cache.unlink()
    human_run = runner.invoke(app, ["status"])
    assert human_run.exit_code == 0
    assert cache.read_bytes() == json_bytes == json_run.stdout.encode("utf-8")


# --- SC-007: the corpus is never touched ----------------------------------------


def _corpus_digest(root: Path) -> dict[str, str]:
    """sha256 per corpus file — everything except the two sanctioned caches."""
    exempt = {"bible/graph.ttl", ".bookwright/cache/status.json"}
    return {rel: h for rel, h in dirhash(root) if h != "<DIR>" and rel not in exempt}


def test_corpus_files_are_byte_identical_after_a_run(
    tiny_historical: Path, runner: CliRunner
) -> None:
    before = _corpus_digest(tiny_historical)
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    assert _corpus_digest(tiny_historical) == before
    # ... and the two derived caches are exactly what changed/appeared.
    assert (tiny_historical / "bible" / "graph.ttl").exists()
    assert (tiny_historical / ".bookwright" / "cache" / "status.json").exists()
