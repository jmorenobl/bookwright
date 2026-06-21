"""Integration tests for ``bookwright graph query`` (FR-003, SC-002)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from bookwright.cli import app

CHARACTERS_QUERY = "SELECT ?c WHERE { ?c a golem:G1_Character }"


def _build(runner: CliRunner) -> None:
    result = runner.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 0


def test_query_returns_expected_identifiers(tiny_novel: Path, runner: CliRunner) -> None:
    _build(runner)
    result = runner.invoke(app, ["graph", "query", CHARACTERS_QUERY, "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["count"] == 1
    assert payload["results"] == [{"c": "https://example.org/my-novel/character/manuel-de-aparici"}]


def test_query_table_on_stdout_without_json(tiny_novel: Path, runner: CliRunner) -> None:
    _build(runner)
    result = runner.invoke(app, ["graph", "query", CHARACTERS_QUERY])
    assert result.exit_code == 0
    assert "manuel-de-aparici" in result.stdout


def test_query_born_before_1850(tiny_novel: Path, runner: CliRunner) -> None:
    """SC-002 motivating query: the birth-year dimension makes "born before 1850"
    answerable. rdflib 7.x does not implement ordering on ``xsd:gYear`` directly,
    so the year is compared lexically — sound because ``gyear_literal`` zero-pads
    every year to four digits, making lexical order match numeric order."""
    _build(runner)
    query = (
        "SELECT ?c ?y WHERE { "
        "?c a golem:G1_Character ; golem:GP0_has_feature ?f . "
        "?f crm:P2_has_type ?t ; crm:P43_has_dimension/crm:P90_has_value ?y . "
        'FILTER(STR(?y) < "1850") }'
    )
    result = runner.invoke(app, ["graph", "query", query, "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["count"] == 1


def test_query_empty_match(tiny_novel: Path, runner: CliRunner) -> None:
    _build(runner)
    result = runner.invoke(
        app, ["graph", "query", "SELECT ?x WHERE { ?x a golem:G16_Object }", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"status": "ok", "results": [], "count": 0}


def test_query_without_built_graph(tiny_novel: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["graph", "query", CHARACTERS_QUERY, "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["code"] == "graph_not_built"
    assert "build" in payload["message"]


def test_query_invalid_sparql(tiny_novel: Path, runner: CliRunner) -> None:
    _build(runner)
    result = runner.invoke(app, ["graph", "query", "SELECT ?c WHERE {{{", "--json"])
    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["code"] == "invalid_query"


def test_query_corrupt_graph(tiny_novel: Path, runner: CliRunner) -> None:
    """A hand-broken graph.ttl yields a clean envelope (exit 2), not a traceback."""
    _build(runner)
    (tiny_novel / "bible" / "graph.ttl").write_text("@@ not turtle @@", encoding="utf-8")
    result = runner.invoke(app, ["graph", "query", CHARACTERS_QUERY, "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "graph_load_failed"


def test_query_malformed_manifest(tiny_novel: Path, runner: CliRunner) -> None:
    """An unparseable manifest.toml maps to the config envelope, not a traceback."""
    _build(runner)
    (tiny_novel / "manifest.toml").write_text("this = = invalid toml", encoding="utf-8")
    result = runner.invoke(app, ["graph", "query", CHARACTERS_QUERY, "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "invalid_manifest"


def test_query_outside_project(outside_project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["graph", "query", CHARACTERS_QUERY, "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "not_a_project"


def test_query_unknown_indexer(project_factory: Callable[..., Path], runner: CliRunner) -> None:
    # build with the default engine, then point the manifest at an unknown one
    project_factory()
    runner.invoke(app, ["graph", "build", "--json"])
    project_factory(indexer="nope")
    result = runner.invoke(app, ["graph", "query", CHARACTERS_QUERY, "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "unknown_indexer"


def test_query_help_notes_unknown_iri_returns_empty(runner: CliRunner) -> None:
    """The ``sparql`` argument help warns that an unknown IRI yields no rows (FR-008)."""
    result = runner.invoke(app, ["graph", "query", "--help"])
    assert result.exit_code == 0
    # Collapse the rich/typer line-wrapping before matching the note.
    text = " ".join(result.stdout.split())
    assert "non-existent or misspelled IRI" in text
    assert "empty result set, not an error" in text


def test_docs_note_unknown_iri_returns_empty() -> None:
    """The Spanish docs page carries the same empty-result note (FR-008, docs in ES)."""
    docs = Path(__file__).parents[3] / "docs" / "commands" / "graph-query.md"
    body = " ".join(docs.read_text(encoding="utf-8").split())
    assert "IRI inexistente o mal escrito devuelve" in body
    assert "cero resultados, no un error" in body


def test_query_human_error_goes_to_stderr(tiny_novel: Path, runner: CliRunner) -> None:
    """``graph query`` without ``--json`` and no graph built → human error on stderr.

    Pins the human-channel discipline (Principle IX): the deliverable channel
    (stdout) stays empty and the error line lands on stderr.
    """
    result = runner.invoke(app, ["graph", "query", CHARACTERS_QUERY])
    assert result.exit_code == 2
    assert result.stdout.strip() == ""
    assert result.stderr.startswith("bookwright: error:")
