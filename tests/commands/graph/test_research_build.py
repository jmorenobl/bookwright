"""Integration tests for the research pass of ``graph build`` (iteration 012).

Builds the ``research="minimal"`` ``tiny_novel`` scaffold and queries the emitted graph,
proving US1-US3 end to end (quickstart sections 1-3) and the foundational regression:
a research-free build is byte-stable, adds zero research triples, and keeps the bible
E13 count unchanged (FR-015 / SC-005, research D8/D9).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

import tests.fixtures.research as fx
from bookwright.cli import app

URI_BASE = "https://example.org/my-novel/"
CHARACTER_URI = f"{URI_BASE}character/manuel-de-aparici"
SOURCE_URI = f"{URI_BASE}source/registro-tip"
TIMELINE_URI = f"{URI_BASE}timeline"

Factory = Callable[..., Path]


def _build(runner: CliRunner, *, expect: int = 0) -> None:
    result = runner.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == expect, result.stdout


def _query(runner: CliRunner, sparql: str) -> list[dict[str, str]]:
    result = runner.invoke(app, ["graph", "query", sparql, "--json"])
    assert result.exit_code == 0, result.stdout
    return list(json.loads(result.stdout)["results"])


def _e13_count(runner: CliRunner) -> int:
    rows = _query(runner, "SELECT (COUNT(?a) AS ?n) WHERE { ?a a crm:E13_Attribute_Assignment }")
    return int(rows[0]["n"])


# --- Foundational regression: research-free builds emit no research triples --


def test_research_free_build_adds_no_research_triples(
    project_factory: Factory, runner: CliRunner
) -> None:
    root = project_factory(research="none")
    _build(runner)
    # The bible's 10 inferred assertions, unchanged; no findings/anchors.
    assert _e13_count(runner) == 10
    graph_text = (root / "bible" / "graph.ttl").read_text(encoding="utf-8")
    assert "@prefix bw:" not in graph_text
    assert "bookwright.dev/vocab/bw#" not in graph_text


def test_empty_research_dir_build_is_clean(project_factory: Factory, runner: CliRunner) -> None:
    root = project_factory(research="none")
    (root / "bible" / "research").mkdir(parents=True)
    _build(runner)
    assert _e13_count(runner) == 10
    assert "@prefix bw:" not in (root / "bible" / "graph.ttl").read_text(encoding="utf-8")


# --- US1: sources become typed nodes with full provenance -------------------


def test_source_node_has_full_provenance(project_factory: Factory, runner: CliRunner) -> None:
    project_factory(research="minimal")
    _build(runner)
    rows = _query(runner, f"SELECT ?p ?o WHERE {{ <{SOURCE_URI}> ?p ?o }}")
    facets = {row["p"]: row["o"] for row in rows}
    crm = "http://www.cidoc-crm.org/cidoc-crm/"
    bw = "https://bookwright.dev/vocab/bw#"
    assert facets[f"{crm}P2_has_type"] == f"{bw}source-type/oficial"
    assert facets[f"{bw}reliability"] == f"{bw}reliability/alta"
    assert facets[f"{bw}author"] == "Ministerio del Interior (España)"
    assert f"{bw}reference" in facets
    assert f"{bw}accessDate" in facets
    # No rdf:type on a source (D2); no translation when languages match (SC-004).
    assert "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" not in facets
    assert f"{bw}translation" not in facets


def test_bad_source_type_aborts_with_no_graph(project_factory: Factory, runner: CliRunner) -> None:
    root = project_factory(research="minimal")
    sources = root / "bible" / "research" / "sources.md"
    sources.write_text(
        sources.read_text(encoding="utf-8").replace("type: oficial", "type: inventado"),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 2
    assert "inventado" in result.stdout
    assert not (root / "bible" / "graph.ttl").exists()


# --- US2: findings reify on E13 and link to the narrative -------------------


def test_finding_reified_with_claim_and_source(project_factory: Factory, runner: CliRunner) -> None:
    project_factory(research="minimal")
    _build(runner)
    rows = _query(
        runner,
        "SELECT ?f ?claim ?src WHERE { "
        "?f a crm:E13_Attribute_Assignment ; "
        "bw:claim ?claim ; "
        f"crm:P140_assigned_attribute_to <{CHARACTER_URI}> ; "
        "bw:supportedBy ?src }",
    )
    assert len(rows) == 1
    assert rows[0]["claim"] == "Un detective privado en España necesita la licencia TIP."
    assert rows[0]["src"] == SOURCE_URI
    assert "/finding/" in rows[0]["f"]


def test_open_question_is_open_with_no_claim(project_factory: Factory, runner: CliRunner) -> None:
    project_factory(research="minimal")
    _build(runner)
    open_rows = _query(
        runner, "SELECT ?o WHERE { ?o a crm:E13_Attribute_Assignment ; bw:open true }"
    )
    assert len(open_rows) == 1
    # The open question carries no claim and no supporting source.
    claim_rows = _query(
        runner,
        f"SELECT ?c WHERE {{ <{open_rows[0]['o']}> bw:claim ?c }}",
    )
    assert claim_rows == []


def test_findings_distinguishable_from_inferred_assertions(
    project_factory: Factory, runner: CliRunner
) -> None:
    project_factory(research="minimal")
    _build(runner)
    # Only the one research finding carries bw:claim — the 10 bible inferred
    # assertions never do (SC-007), so the discriminating query returns exactly one.
    claim_findings = _query(
        runner, "SELECT ?f WHERE { ?f a crm:E13_Attribute_Assignment ; bw:claim ?c }"
    )
    assert len(claim_findings) == 1


# --- US3: anchors constrain the fiction + the payoff query ------------------


def test_payoff_query_returns_anchor_claim_source(
    project_factory: Factory, runner: CliRunner
) -> None:
    project_factory(research="minimal")
    _build(runner)
    rows = _query(
        runner,
        "SELECT ?anchor ?claim ?source WHERE { "
        f"?anchor a crm:E13_Attribute_Assignment ; bw:constrains <{CHARACTER_URI}> ; "
        "bw:promotes ?finding . "
        "?finding bw:claim ?claim ; bw:supportedBy ?source }",
    )
    assert len(rows) == 1
    assert rows[0]["claim"] == "Un detective privado en España necesita la licencia TIP."
    assert rows[0]["source"] == SOURCE_URI
    assert "/anchor/" in rows[0]["anchor"]


def test_time_span_query_returns_begin_end(project_factory: Factory, runner: CliRunner) -> None:
    project_factory(research="minimal")
    _build(runner)
    rows = _query(
        runner,
        "SELECT ?b ?e WHERE { "
        f"?a bw:constrains <{CHARACTER_URI}> ; crm:P4_has_time-span ?ts . "
        "?ts crm:P82a_begin_of_the_begin ?b ; crm:P82b_end_of_the_end ?e }",
    )
    assert len(rows) == 1
    assert rows[0]["b"] == "1995"
    assert rows[0]["e"] == "2026"


def test_anchor_without_time_span_returns_no_row(
    project_factory: Factory, runner: CliRunner
) -> None:
    root = project_factory(research="minimal")
    topic = root / "bible" / "research" / "detective-licencia.md"
    topic.write_text(
        topic.read_text(encoding="utf-8").replace("    begin: 1995\n    end: 2026\n", ""),
        encoding="utf-8",
    )
    _build(runner)
    rows = _query(
        runner,
        f"SELECT ?ts WHERE {{ ?a bw:constrains <{CHARACTER_URI}> ; crm:P4_has_time-span ?ts }}",
    )
    assert rows == []


# --- Human (non-JSON) summary + warnings (D12) ------------------------------


def test_human_summary_reports_research_counts(project_factory: Factory, runner: CliRunner) -> None:
    project_factory(research="minimal")
    result = runner.invoke(app, ["graph", "build"])
    assert result.exit_code == 0
    assert "research: 1 source(s), 2 finding(s), 1 anchor(s)" in result.stderr


def test_unresolved_target_is_warned_not_fatal(project_factory: Factory, runner: CliRunner) -> None:
    root = project_factory(research="minimal")
    topic = root / "bible" / "research" / "detective-licencia.md"
    topic.write_text(
        topic.read_text(encoding="utf-8").replace(
            'bears_on: "Manuel de Aparici"', 'bears_on: "Personaje Inexistente"'
        ),
        encoding="utf-8",
    )
    # The build still succeeds (exit 0) and the graph is written (D12) ...
    result = runner.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert any(w["name"] == "Personaje Inexistente" for w in payload["research_warnings"])
    assert (root / "bible" / "graph.ttl").exists()
    # ... and the human summary surfaces the same miss.
    human = runner.invoke(app, ["graph", "build"])
    assert "Personaje Inexistente" in human.stderr


def test_anchor_constrains_timeline_links_timeline_uri(
    project_factory: Factory, runner: CliRunner
) -> None:
    root = project_factory(research="minimal")
    topic = root / "bible" / "research" / "detective-licencia.md"
    topic.write_text(
        topic.read_text(encoding="utf-8").replace(
            'constrains: "Manuel de Aparici"', "constrains: timeline"
        ),
        encoding="utf-8",
    )
    _build(runner)
    rows = _query(
        runner,
        f"SELECT ?a WHERE {{ ?a a crm:E13_Attribute_Assignment ; bw:constrains <{TIMELINE_URI}> }}",
    )
    assert len(rows) == 1


# --- iteration-14: the RICH shared fixture (SC-003/004/005/006) --------------
#
# Builds the same shared fixture the io-level conformance test reads, proving the
# reader reflects the *authored* provenance faithfully end-to-end through the
# graph. SC-006's judgment (don't promote a sub-floor finding) is enforced by the
# skill protocol body (bookwright-research.md) and the iteration-15 reliability
# validator — NOT by this reader, which builds exactly the anchors the file
# declares. Here we only assert the baja finding the fixture leaves un-anchored
# stays un-anchored.


def test_rich_conflicting_pair_maps_to_two_findings(
    project_factory: Factory, runner: CliRunner
) -> None:
    project_factory(research="rich")
    _build(runner)
    rows = _query(runner, "SELECT ?f ?c WHERE { ?f a crm:E13_Attribute_Assignment ; bw:claim ?c }")
    conflict = {row["f"] for row in rows if row["c"] in {fx.CONFLICT_CLAIM_A, fx.CONFLICT_CLAIM_B}}
    # SC-005 — two distinct findings, no silent collapse.
    assert len(conflict) == 2


def test_rich_foreign_source_translation_survives(
    project_factory: Factory, runner: CliRunner
) -> None:
    project_factory(research="rich")
    _build(runner)
    rows = _query(runner, "SELECT ?s ?t WHERE { ?s bw:translation ?t }")
    # SC-004 — exactly the two foreign-language sources (de, fr) carry a
    # translation; the two Spanish sources (book language) do not.
    assert len(rows) == 2


def test_rich_promoted_anchor_constrains_named_entity(
    project_factory: Factory, runner: CliRunner
) -> None:
    project_factory(research="rich")
    _build(runner)
    rows = _query(
        runner,
        "SELECT ?anchor ?claim WHERE { "
        f"?anchor a crm:E13_Attribute_Assignment ; bw:constrains <{CHARACTER_URI}> ; "
        "bw:promotes ?finding . ?finding bw:claim ?claim }",
    )
    # SC-003 — the promoted finding's anchor constrains the real bible character.
    assert len(rows) == 1
    assert rows[0]["claim"] == fx.PROMOTED_CLAIM
    assert "/anchor/" in rows[0]["anchor"]


def test_rich_baja_finding_is_not_anchored(project_factory: Factory, runner: CliRunner) -> None:
    project_factory(research="rich")
    _build(runner)
    # The fixture declares no anchor for the baja finding; the reader builds only
    # what is authored, so nothing promotes it (SC-006, reader side).
    rows = _query(
        runner,
        "SELECT ?anchor WHERE { "
        "?finding a crm:E13_Attribute_Assignment ; bw:claim ?c . "
        f'FILTER(STR(?c) = "{fx.BAJA_CLAIM}") '
        "?anchor bw:promotes ?finding }",
    )
    assert rows == []
