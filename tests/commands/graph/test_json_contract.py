"""The JSON-over-stdout invariant for the ``graph`` verbs (Principle IX, SC-003)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.commands import graph as graph_pkg
from bookwright.commands.graph import build as build_mod
from bookwright.commands.graph import query as query_mod


def _assert_single_json_doc(stdout: str) -> dict[str, Any]:
    """stdout must be exactly one JSON document and nothing else."""
    stripped = stdout.strip()
    assert stripped, "expected a JSON document on stdout"
    doc: dict[str, Any] = json.loads(stripped)  # raises if not valid JSON
    # exactly one document: no trailing content after the first parse
    assert stdout.count("\n") <= 1 or stdout.rstrip("\n").count("\n") == 0
    return doc


def test_build_json_only_on_stdout(tiny_novel: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 0
    doc = _assert_single_json_doc(result.stdout)
    assert doc["status"] == "ok"


def test_build_human_prose_goes_to_stderr(tiny_novel: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["graph", "build"])
    assert result.exit_code == 0
    # no JSON on stdout in human mode; the summary is on stderr
    assert result.stdout.strip() == ""
    assert "entities" in result.stderr


def _build(runner: CliRunner) -> None:
    assert runner.invoke(app, ["graph", "build", "--json"]).exit_code == 0


def test_query_success_json_only_on_stdout(tiny_novel: Path, runner: CliRunner) -> None:
    _build(runner)
    result = runner.invoke(
        app, ["graph", "query", "SELECT ?c WHERE { ?c a golem:G1_Character }", "--json"]
    )
    assert result.exit_code == 0
    doc = _assert_single_json_doc(result.stdout)
    assert doc["status"] == "ok"


def test_query_empty_json_only_on_stdout(tiny_novel: Path, runner: CliRunner) -> None:
    _build(runner)
    result = runner.invoke(
        app, ["graph", "query", "SELECT ?x WHERE { ?x a golem:G16_Object }", "--json"]
    )
    assert result.exit_code == 0
    doc = _assert_single_json_doc(result.stdout)
    assert doc == {"status": "ok", "results": [], "count": 0}


def test_query_error_json_only_on_stdout(tiny_novel: Path, runner: CliRunner) -> None:
    # no graph built yet → error envelope, still a single JSON doc on stdout
    result = runner.invoke(
        app, ["graph", "query", "SELECT ?c WHERE { ?c a golem:G1_Character }", "--json"]
    )
    assert result.exit_code == 2
    doc = _assert_single_json_doc(result.stdout)
    assert doc["status"] == "error"


# --- FR-017: read-only boundary ---------------------------------------------


def test_query_does_not_mutate_the_graph(tiny_novel: Path, runner: CliRunner) -> None:
    """FR-017: ``graph query`` is read-only — the Turtle is byte-for-byte unchanged."""
    _build(runner)
    graph_file = tiny_novel / "bible" / "graph.ttl"
    before = graph_file.read_bytes()
    result = runner.invoke(
        app, ["graph", "query", "SELECT ?c WHERE { ?c a golem:G1_Character }", "--json"]
    )
    assert result.exit_code == 0
    assert graph_file.read_bytes() == before


def test_graph_exposes_no_mutation_verb_beyond_build() -> None:
    """The only write verb the sub-app exposes is ``build``; ``query`` is read-only."""
    names = {command.name for command in graph_pkg.app.registered_commands}
    assert names == {"build", "query"}


def test_graph_verbs_import_no_validator() -> None:
    """Semantic coherence is iteration 10: neither verb imports a validator."""
    source = Path(build_mod.__file__).read_text(encoding="utf-8") + Path(
        query_mod.__file__
    ).read_text(encoding="utf-8")
    assert "validator" not in source.lower()
