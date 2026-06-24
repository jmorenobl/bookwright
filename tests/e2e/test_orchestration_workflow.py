"""The orchestration loop proven end to end over the ``tiny-historical`` fixture (023).

Walks the M5 work loop in-process (``typer.testing.CliRunner``) exactly like
``tests/e2e/test_research_workflow.py``: ``focus set`` → ``graph build`` → ``status``
→ resolve one open question → ``graph build`` → ``status``, every command with
``--json`` and its single JSON document parsed off stdout (Principle IX). The
assertion is **state convergence**, not a shorter ``next_actions`` list (research D2):
the merged 020 engine aggregates per workstream, so ``research_queue`` keeps firing
while *any* open question OR anchor gap remains. Resolving one question therefore
leaves ``len(next_actions) == 4`` unchanged; only ``state.open_questions`` and the
``research_queue`` prompt/reason converge, while every other fact is byte-identical.
(The ``not_evaluated`` channel is never empty — ``character_unknown_mentions`` abstains
unconditionally, issue #1 track A — but its entry is ``kind: pending_capability`` since
iteration 044, so ``activate_dormant_validators`` NO LONGER fires: the nudge nudges only
on actionable ``missing_input`` gaps. Since iteration 051 the abstention DOES fire the
informative ``judge_undeclared_characters`` nudge (keyed on the source), a second
``bookwright-continuity``. The four actions are the research workstreams, the single
``review_continuity`` (the ``error`` count), and that judge nudge — byte-identical across
runs.)

Four groups, mapped 1:1 to ``contracts/e2e-orchestration-contract.md``:

* **Group A** — the loop proven end to end over the extended ``tiny-historical``.
* **Group B** — inertness when orchestration is unused (``tiny-novel``).
* **Group C** — the degraded ``graph unavailable`` path.
* **Group D** — committed-tree invariants (the fixture stays source-only).

Every identifier and count comes from the co-located oracle
``tiny-historical/expected-status.md`` (loaded once, never hard-coded, FR-008).
``state.graph`` is asserted *present* per run but **carved out** of the cross-run
byte-identity comparison: a closed answering finding legitimately emits different
triples than the open question it replaces (research D2).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.io.frontmatter import parse_frontmatter
from tests.conftest import FIXTURES_DIR, copy_fixture

HISTORICAL = "tiny-historical"
NOVEL = "tiny-novel"

#: The corpus dir an open question is declared in; the answering finding is copied here.
RESEARCH_DIR = Path("bible") / "research"
INDEX = RESEARCH_DIR / "_index.md"

#: The one skill whose action is the per-workstream research queue (the only action
#: whose prompt/reason converge when a question is resolved).
RESEARCH_SKILL = "bookwright-research"


# --------------------------------------------------------------------------------------
# Harness — the oracle loader and the in-process CLI helpers (single source of truth).
# --------------------------------------------------------------------------------------


def _load_oracle() -> dict[str, Any]:
    """Load ``tiny-historical/expected-status.md`` front-matter (the oracle, FR-004/D5).

    Read from the *committed* fixture so the expectations are pinned in one place; the
    presence of the copied file in ``tmp_path`` is checked separately (Group D).
    """
    path = FIXTURES_DIR / HISTORICAL / "expected-status.md"
    return parse_frontmatter(path.read_text(encoding="utf-8")).metadata


@pytest.fixture()
def oracle() -> dict[str, Any]:
    """The parsed expected-status front-matter, shared across the assertions."""
    return _load_oracle()


@pytest.fixture()
def historical(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copy ``tiny-historical`` into ``tmp_path`` and ``chdir`` into the copy."""
    project = copy_fixture(HISTORICAL, tmp_path)
    monkeypatch.chdir(project)
    return project


def _payload(result: Any) -> dict[str, Any]:
    """Parse the single JSON document a ``--json`` command writes to stdout."""
    return json.loads(result.stdout)  # type: ignore[no-any-return]


def _focus_set(cli: CliRunner, target: str) -> dict[str, Any]:
    """Run ``focus set --target <target> --json``; assert success, return the payload."""
    result = cli.invoke(app, ["focus", "set", "--target", target, "--json"])
    assert result.exit_code == 0, result.stdout
    return _payload(result)


def _build(cli: CliRunner) -> dict[str, Any]:
    """Run ``graph build --json``; assert it succeeds and return the payload."""
    result = cli.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 0, result.stdout
    return _payload(result)


def _status_raw(cli: CliRunner) -> str:
    """Run ``status --json``; assert exit 0 and return the raw stdout bytes (D6)."""
    result = cli.invoke(app, ["status", "--json"])
    assert result.exit_code == 0, result.stdout
    return result.stdout


def _status(cli: CliRunner) -> dict[str, Any]:
    """Run ``status --json``; assert exit 0 and return the parsed payload."""
    return json.loads(_status_raw(cli))  # type: ignore[no-any-return]


def _first_status(cli: CliRunner, oracle: dict[str, Any]) -> dict[str, Any]:
    """The first ``status`` after ``focus set`` + ``graph build`` (the loop's frame #1)."""
    _focus_set(cli, oracle["focus"]["target"])
    _build(cli)
    return _status(cli)


def _apply_resolution(project: Path, oracle: dict[str, Any]) -> None:
    """Apply the pre-baked two-part resolution to the working copy (research D3).

    1. Copy ``_resolution/<answering_file>`` into ``bible/research/`` (adds the closed
       answering finding). 2. Drop ``resolved_id`` from ``_index.md`` ``open_questions``
       (closes the question). Rebuilding then closes exactly that one question.
    """
    resolution = oracle["resolution"]
    answering = project / resolution["answering_file"]
    shutil.copy(answering, project / RESEARCH_DIR / answering.name)

    index = project / INDEX
    resolved_line = f"- id: {resolution['resolved_id']}"
    lines = index.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if line.strip() != resolved_line]
    # Fail loudly on format drift: if the open_questions line shape ever changes, a
    # silent no-op here would leave the question open and surface as a baffling count
    # mismatch downstream. Pin that exactly one line was dropped.
    assert len(kept) == len(lines) - 1, (
        f"expected to drop exactly one {resolved_line!r} line from {INDEX}; "
        "the open_questions format may have drifted"
    )
    index.write_text("".join(kept), encoding="utf-8")


def _action(payload: dict[str, Any], skill: str) -> dict[str, Any] | None:
    """The ``next_actions`` entry whose ``skill == skill``, or ``None`` if it never fires."""
    return next((a for a in payload["next_actions"] if a["skill"] == skill), None)


def _research_action(payload: dict[str, Any]) -> dict[str, Any]:
    """The ``bookwright-research`` action — the per-workstream queue (asserted present)."""
    action = _action(payload, RESEARCH_SKILL)
    assert action is not None, "the research queue action must fire while work remains"
    return action


def _skills(payload: dict[str, Any]) -> list[str]:
    """The ordered ``skill`` of each ``next_actions`` entry."""
    return [action["skill"] for action in payload["next_actions"]]


def _invariant_view(payload: dict[str, Any]) -> dict[str, Any]:
    """The cross-run invariant subset (data-model § 4): everything that must NOT move.

    Excludes ``state.open_questions`` and the ``research_queue`` prompt/reason (the
    Δ-expected set) and ``state.graph`` (the carve-out, asserted present-not-equal).
    """
    state = payload["state"]
    research = _research_action(payload)
    return {
        "status": payload["status"],
        "focus": payload["focus"],
        "phase": state["phase"],
        "unresolved_anchors": state["unresolved_anchors"],
        "low_reliability_findings": state["low_reliability_findings"],
        "validation": state["validation"],
        "verify": _action(payload, "bookwright-verify"),
        "continuity": _action(payload, "bookwright-continuity"),
        "research_skill": research["skill"],
    }


# --------------------------------------------------------------------------------------
# Group A — the loop proven end to end over the extended tiny-historical (FR-007..010).
# --------------------------------------------------------------------------------------


def test_focus_set_records_the_authored_target(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """A1: ``focus set`` records the target; ``status.focus`` reflects it (FR-002)."""
    target = oracle["focus"]["target"]
    _focus_set(cli, target)
    _build(cli)
    payload = _status(cli)
    assert payload["focus"] is not None
    assert payload["focus"]["target"] == target


def test_build_makes_the_graph_available(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """A2: ``graph build`` makes the graph available with entity/triple counts (FR-003)."""
    payload = _first_status(cli, oracle)
    graph = payload["state"]["graph"]
    assert graph["available"] is True
    assert isinstance(graph["entities"], int) and graph["entities"] > 0
    assert isinstance(graph["triples"], int) and graph["triples"] > 0


def test_first_status_reports_the_oracle_facts(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """A3: every deterministic fact of data-model § 2.1 holds, oracle-sourced (FR-008)."""
    state = _first_status(cli, oracle)["state"]

    assert state["phase"] == oracle["phase"]

    questions = state["open_questions"]
    assert questions["count"] == len(oracle["open_questions"]["ids"])
    assert [q["id"] for q in questions["items"]] == oracle["open_questions"]["ids"]
    assert all(q["file"] == oracle["open_questions"]["file"] for q in questions["items"])

    anchors = state["unresolved_anchors"]
    assert anchors["count"] == len(oracle["unresolved_anchors"])
    assert anchors["items"] == oracle["unresolved_anchors"]

    findings = state["low_reliability_findings"]
    assert findings["count"] == len(oracle["low_reliability_findings"])
    assert findings["items"] == oracle["low_reliability_findings"]

    assert state["validation"]["counts"] == oracle["validation"]["counts"]


def test_first_status_enumerates_the_firing_actions(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """A4: ``next_actions`` are the oracle's 3 skills in order, each shaped (FR-008)."""
    payload = _first_status(cli, oracle)
    assert _skills(payload) == oracle["next_actions"]["skills"]
    for action in payload["next_actions"]:
        assert action.keys() == {"skill", "prompt", "reason"}
        assert action["prompt"] and action["reason"]

    prompt = _research_action(payload)["prompt"]
    for question_id in oracle["open_questions"]["ids"]:
        assert question_id in prompt


def test_resolution_closes_exactly_one_question(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """A5: applying the resolution + rebuild closes exactly the resolved id (FR-005)."""
    _first_status(cli, oracle)
    _apply_resolution(historical, oracle)
    _build(cli)
    questions = _status(cli)["state"]["open_questions"]

    assert questions["count"] == 1
    assert [q["id"] for q in questions["items"]] == [oracle["resolution"]["remaining_id"]]
    assert all(q["id"] != oracle["resolution"]["resolved_id"] for q in questions["items"])


def test_second_status_converges(cli: CliRunner, historical: Path, oracle: dict[str, Any]) -> None:
    """A6: the second ``status`` converges — Δ where expected, byte-identical else (FR-009)."""
    before = _first_status(cli, oracle)
    _apply_resolution(historical, oracle)
    _build(cli)
    after = _status(cli)

    resolved = oracle["resolution"]["resolved_id"]
    remaining = oracle["resolution"]["remaining_id"]

    # Δ-expected: the research queue drops the resolved id, keeps the remaining one,
    # and its reason reflects the new count.
    research_before = _research_action(before)
    research_after = _research_action(after)
    assert resolved in research_before["prompt"]
    assert resolved not in research_after["prompt"]
    assert remaining in research_after["prompt"]
    assert research_before["reason"] != research_after["reason"]
    # The count is oracle-derived (FR-008), not a hard-coded literal: resolving one of
    # the oracle's questions leaves len(ids) - 1 open, and the reason reflects that.
    before_count = len(oracle["open_questions"]["ids"])
    after_count = before_count - 1
    assert f"{before_count} open research question" in research_before["reason"]
    assert f"{after_count} open research question" in research_after["reason"]

    # The abstainer keeps the not_evaluated channel non-empty in both runs, as a
    # pending_capability entry (iteration 044) — visible, but not nudged on.
    for payload in (before, after):
        entry = next(
            r
            for r in payload["state"]["validation"]["not_evaluated"]
            if r["validator"] == "character_unknown_mentions"
        )
        assert entry["kind"] == "pending_capability"

    # Invariant: everything else byte-identical; the list length is unchanged (NOT N-1).
    # Four actions: the research workstreams plus review_continuity, plus the iteration-051
    # judge nudge (`judge_undeclared_characters`, a second `bookwright-continuity` keyed on
    # the `character_unknown_mentions` abstention). The capability-gap entries still do not
    # fire `activate_dormant_validators` (044).
    assert len(after["next_actions"]) == 4
    assert len(before["next_actions"]) == 4
    assert _invariant_view(after) == _invariant_view(before)


def test_graph_facts_are_per_run_but_carved_out(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """A7: ``state.graph`` is available+counted in each run but excluded from equality (D2)."""
    before = _first_status(cli, oracle)
    _apply_resolution(historical, oracle)
    _build(cli)
    after = _status(cli)

    for payload in (before, after):
        graph = payload["state"]["graph"]
        assert graph["available"] is True
        assert isinstance(graph["entities"], int)
        assert isinstance(graph["triples"], int)

    # The carve-out is real: a closed finding emits different triples than the open
    # question it replaced, so the headline metrics legitimately move.
    assert before["state"]["graph"] != after["state"]["graph"]


def test_status_is_byte_identical_across_repeats(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """A8: repeating ``status`` on an unchanged corpus yields byte-identical output (FR-010)."""
    _focus_set(cli, oracle["focus"]["target"])
    _build(cli)
    assert _status_raw(cli) == _status_raw(cli)


# --------------------------------------------------------------------------------------
# Group B — inertness when orchestration is unused (tiny-novel, FR-011).
# --------------------------------------------------------------------------------------


def test_focus_free_project_recommends_no_research_workstream(
    cli: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, oracle: dict[str, Any]
) -> None:
    """B1: a focus-free / research-free project fires no research-derived workstream (FR-011).

    The shipped 020 engine still emits the ``define_focus`` nudge (rule ⑤) for any
    project without a ``[focus]`` block, so ``next_actions`` is not literally empty — but
    none of the *research-derived* workstreams (the oracle's firing skills) fire, and the
    derived research state is empty. That is the faithful inertness contract: the
    orchestration *queue* machinery costs an unused project nothing.
    """
    project = copy_fixture(NOVEL, tmp_path)
    monkeypatch.chdir(project)
    _build(cli)
    payload = _status(cli)

    assert payload["focus"] is None
    state = payload["state"]
    assert state["open_questions"]["count"] == 0
    assert state["unresolved_anchors"]["count"] == 0
    assert state["low_reliability_findings"]["count"] == 0

    # The *research-derived* workstreams must not fire on a research-free project. Note
    # `bookwright-continuity` is multi-purpose — `review_continuity` (not firing here, no
    # errors), `activate_dormant_validators` (also NOT firing since iteration 044: the
    # `not_evaluated` entries are `pending_capability`, and that nudge nudges only on
    # `missing_input` gaps), AND `judge_undeclared_characters` (iteration 051), which DOES
    # fire on the `character_unknown_mentions` abstention — informative, never degrading
    # green. So the inertness check covers research/verify; the judge continuity nudge may
    # legitimately appear.
    research_skills = {"bookwright-research", "bookwright-verify"}
    assert research_skills.isdisjoint(_skills(payload))


def test_build_and_validate_behave_pre_m5(
    cli: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """B2: ``build``/``validate`` on a focus-free project exit/behave as pre-M5 (FR-011)."""
    project = copy_fixture(NOVEL, tmp_path)
    monkeypatch.chdir(project)
    _build(cli)
    result = cli.invoke(app, ["validate", "--json"])
    assert result.exit_code == 0, result.stdout
    assert _payload(result)["failed"] is False


# --------------------------------------------------------------------------------------
# Group C — the degraded path (FR-012).
# --------------------------------------------------------------------------------------


def test_unbuildable_corpus_degrades_not_fails(
    cli: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C1: a corpus missing its build prerequisites degrades to exit-0, not a failure (FR-012)."""
    project = copy_fixture(NOVEL, tmp_path)
    shutil.rmtree(project / "bible")
    monkeypatch.chdir(project)
    payload = _status(cli)

    assert payload["status"] == "ok"
    assert payload["state"]["graph"]["available"] is False


# --------------------------------------------------------------------------------------
# Group D — the committed fixture tree is source-only (extends 016 Group D).
# --------------------------------------------------------------------------------------


def test_committed_fixture_is_source_only() -> None:
    """D1: committed ``tiny-historical`` ships no derived graph / skills; the orchestration
    material is present-but-inert."""
    root = FIXTURES_DIR / HISTORICAL
    assert root.is_dir()
    assert not (root / "bible" / "graph.ttl").exists()
    assert not (root / ".claude").exists()
    assert not (root / ".agents").exists()
    assert not list(root.rglob("SKILL.md"))
    # The orchestration additions ship as plain source.
    assert (root / "expected-status.md").is_file()
    assert (root / "_resolution" / "q-libro-de-jornales.md").is_file()


def test_resolution_is_outside_the_corpus(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """D3: ``_resolution/`` is outside the corpus dirs — the first build never reads it (FR-005)."""
    resolution_dir = historical / "_resolution"
    assert resolution_dir.is_dir()
    for corpus in ("bible", "manuscript", "outline"):
        assert not (historical / corpus / "_resolution").exists()

    # The proof: the FIRST status reports both questions still open (answering finding unread).
    state = _first_status(cli, oracle)["state"]
    assert state["open_questions"]["count"] == len(oracle["open_questions"]["ids"])
