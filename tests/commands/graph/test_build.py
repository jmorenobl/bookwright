"""Integration tests for ``bookwright graph build``.

Happy path FR-001 / SC-001; engine selection FR-007 / SC-007; fault paths
FR-012 / FR-013 / FR-014 / SC-004 / SC-005.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rdflib import Graph
from rdflib.namespace import RDF
from rdflib.term import URIRef
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.golem.namespaces import frozen_terms


def _build_json(runner: CliRunner, args: list[str] | None = None) -> tuple[int, dict[str, Any]]:
    result = runner.invoke(app, ["graph", "build", "--json", *(args or [])])
    return result.exit_code, json.loads(result.stdout)


# --- FR-001 / SC-001: happy path --------------------------------------------


def test_build_writes_parseable_turtle(tiny_novel: Path, runner: CliRunner) -> None:
    exit_code, _payload = _build_json(runner)
    assert exit_code == 0
    graph_file = tiny_novel / "bible" / "graph.ttl"
    assert graph_file.exists()
    text = graph_file.read_text(encoding="utf-8")
    Graph().parse(data=text, format="turtle")  # parses as RDF
    assert "@prefix golem:" in text  # short prefixes (FR-015)


def test_build_report_shape(tiny_novel: Path, runner: CliRunner) -> None:
    exit_code, payload = _build_json(runner)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["files_processed"] == 4
    assert payload["entities"] == 4
    assert payload["triples"] > 0
    assert payload["graph_path"] == "bible/graph.ttl"
    assert payload["skipped"] == []
    assert payload["unknown_keys"] == []
    assert payload["unresolved_references"] == []


def test_unresolved_reference_key_and_shape(
    project_factory: Callable[..., Path], runner: CliRunner
) -> None:
    """An unmatched ``participants:`` member surfaces under ``unresolved_references``
    at its envelope slot with the ``{path, entity, name}`` shape (FR-016/FR-017)."""
    root: Path = project_factory()
    (root / "bible" / "timeline.md").write_text(
        '---\nevents:\n  - name: "Duelo"\n    participants: ["Nadie Conocido"]\n---\n',
        encoding="utf-8",
    )
    exit_code, payload = _build_json(runner)
    assert exit_code == 0  # soft warning never changes the exit code
    assert payload["unresolved_references"] == [
        {"path": "bible/timeline.md", "entity": "Duelo", "name": "Nadie Conocido"}
    ]
    # The key keeps its slot after "unknown_keys"; "untyped_vocab_terms" (iteration
    # 047) sits between it and "sources" (FR-017).
    keys = list(payload)
    assert keys[keys.index("unknown_keys") + 1] == "unresolved_references"
    assert keys[keys.index("unresolved_references") + 1] == "untyped_vocab_terms"
    assert keys[keys.index("untyped_vocab_terms") + 1] == "sources"


def test_build_summary_on_stderr(tiny_novel: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["graph", "build"])
    assert result.exit_code == 0
    assert "entities" in result.stderr
    assert "triples" in result.stderr


def test_force_rebuilds_idempotently(tiny_novel: Path, runner: CliRunner) -> None:
    code1, first = _build_json(runner)
    code2, second = _build_json(runner, ["--force"])
    assert code1 == code2 == 0
    # v0 has no cache to bypass: the report is identical run-to-run. (The graph
    # itself is not byte-identical only because each provenance E13 carries a
    # fresh uuid7 identity by iteration-5 design — the counts are stable.)
    assert first["triples"] == second["triples"]
    assert first["entities"] == second["entities"]


# --- SC-001: frozen-vocabulary closure at the build level -------------------


def test_build_uses_only_frozen_vocabulary(tiny_novel: Path, runner: CliRunner) -> None:
    _build_json(runner)
    graph = Graph()
    graph.parse(str(tiny_novel / "bible" / "graph.ttl"), format="turtle")
    frozen = frozen_terms()
    used: set[URIRef] = set()
    for _s, p, o in graph:
        if isinstance(p, URIRef):
            used.add(p)
        if p == RDF.type and isinstance(o, URIRef):
            used.add(o)
    assert used <= frozen, f"out-of-vocabulary terms: {used - frozen}"


# --- FR-018: empty-bible edge case (reports zero entities) ------------------


def test_empty_bible_builds_successfully(
    project_factory: Callable[..., Path], runner: CliRunner
) -> None:
    root: Path = project_factory(with_bible=False)
    # recognised dirs exist but contain no entities
    (root / "bible" / "characters").mkdir(parents=True)
    (root / "bible" / "settings").mkdir(parents=True)
    exit_code, payload = _build_json(runner)
    assert exit_code == 0
    assert payload["entities"] == 0
    graph_file = root / "bible" / "graph.ttl"
    assert graph_file.exists()
    Graph().parse(str(graph_file), format="turtle")  # well-formed (prefix-only)


# --- FR-012 / FR-013 / FR-014: fault paths ----------------------------------


def test_build_outside_project(outside_project: Path, runner: CliRunner) -> None:
    exit_code, payload = _build_json(runner)
    assert exit_code == 2
    assert payload["code"] == "not_a_project"


def test_build_malformed_manifest(tiny_novel: Path, runner: CliRunner) -> None:
    """An unparseable manifest.toml maps to the config envelope (exit 2), not a traceback."""
    (tiny_novel / "manifest.toml").write_text("this = = invalid toml", encoding="utf-8")
    exit_code, payload = _build_json(runner)
    assert exit_code == 2
    assert payload["code"] == "invalid_manifest"
    assert not (tiny_novel / "bible" / "graph.ttl").exists()


def test_build_missing_bible(project_factory: Callable[..., Path], runner: CliRunner) -> None:
    root: Path = project_factory(with_bible=False)
    exit_code, payload = _build_json(runner)
    assert exit_code == 2
    assert payload["code"] == "missing_directory"
    assert payload["details"]["name"] == "bible"
    assert not (root / "bible" / "graph.ttl").exists()


def test_build_missing_manuscript(project_factory: Callable[..., Path], runner: CliRunner) -> None:
    root: Path = project_factory(with_manuscript=False)
    exit_code, payload = _build_json(runner)
    assert exit_code == 2
    assert payload["code"] == "missing_directory"
    assert payload["details"]["name"] == "manuscript"


def test_build_skips_malformed_file_exit_4(
    project_factory: Callable[..., Path], runner: CliRunner
) -> None:
    root: Path = project_factory()
    (root / "bible" / "characters" / "broken.md").write_text(
        "---\nname: : :\n  bad\n---\n", encoding="utf-8"
    )
    exit_code, payload = _build_json(runner)
    assert exit_code == 4
    assert payload["status"] == "ok"
    assert any("broken.md" in s["path"] for s in payload["skipped"])
    assert (root / "bible" / "graph.ttl").exists()  # valid files still written


def test_build_slug_collision_exit_3(
    project_factory: Callable[..., Path], runner: CliRunner
) -> None:
    root: Path = project_factory()
    (root / "bible" / "characters" / "dup.md").write_text(
        '---\nname: "Manuel de Aparici"\n---\n', encoding="utf-8"
    )
    # remove any prior graph so we can assert none is written
    graph_file = root / "bible" / "graph.ttl"
    if graph_file.exists():
        graph_file.unlink()
    exit_code, payload = _build_json(runner)
    assert exit_code == 3
    assert payload["code"] == "slug_collision"
    assert payload["details"]["identifier"] == "manuel-de-aparici"
    assert len(payload["details"]["sources"]) == 2
    assert not graph_file.exists()


# --- FR-007 / SC-007: unknown indexer ---------------------------------------


def test_build_unknown_indexer_exit_2(
    project_factory: Callable[..., Path], runner: CliRunner
) -> None:
    project_factory(indexer="nope")
    exit_code, payload = _build_json(runner)
    assert exit_code == 2
    assert payload["code"] == "unknown_indexer"
    assert "rdflib" in payload["details"]["available"]
