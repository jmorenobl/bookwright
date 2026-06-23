"""Oracles for the unrecognized-vocabulary-term soft warning (iteration 047, DEBT-016).

`graph build` types each authored `functions:` (Propp) / `narrative_roles:` (Greimas)
term against the active vocabulary; a non-match is minted **untyped** (no
`crm:P2_has_type`). Before this iteration that happened in silence — now it emits a
non-fatal `untyped_vocab_terms` warning naming the file/field/term/vocabulary and (in
the human render) the valid terms. The node is still ingested unchanged; the exit code
never changes (design § 4.4, contracts/graph-build-envelope.md).

Covers the Propp `functions:` site, the Greimas `narrative_roles:` site (plus the
blank-role edge case), and the no-active-vocabulary non-regression + determinism
guards. The reference fixture is `tiny-quest` (Propp active); the Greimas and no-vocab
variants edit a throwaway copy's manifest/cards.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from rdflib import Graph, URIRef
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.io.bible import map_bible
from bookwright.io.vocabularies import load_vocabulary
from tests.conftest import copy_fixture

URI_BASE = "https://example.org/tiny-quest/"
HAS_TYPE = URIRef("http://www.cidoc-crm.org/cidoc-crm/P2_has_type")


def _build_json(
    project: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    """Run ``graph build --json`` in ``project`` and return the parsed envelope."""
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 0, result.stderr
    doc: dict[str, Any] = json.loads(result.stdout)
    return doc


def _load_graph(project: Path) -> Graph:
    graph = Graph()
    graph.parse(project / "bible" / "graph.ttl", format="turtle")
    return graph


def _is_typed(graph: Graph, subject: URIRef) -> bool:
    return bool(list(graph.triples((subject, HAS_TYPE, None))))


def _set_active(project: Path, active: str) -> None:
    """Rewrite the manifest's ``[vocabularies] active`` line to ``active`` (a TOML list)."""
    manifest = project / "manifest.toml"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace('active = ["propp"]', f"active = {active}")
    manifest.write_text(text, encoding="utf-8")


# --- Propp `functions:` typo is surfaced -------------------------------


def test_propp_typo_emits_one_warning_node_still_untyped(
    tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-001/002/003/006: an unrecognized Propp term warns once; the node is
    still minted without ``crm:P2_has_type`` and the valid sibling keeps its type."""
    project = copy_fixture("tiny-quest", tmp_path)
    unit = project / "outline" / "units" / "04-struggle.md"
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            "functions: [struggle, victory]", "functions: [struggle, intimidacion]"
        ),
        encoding="utf-8",
    )
    doc = _build_json(project, runner, monkeypatch)

    assert doc["status"] == "ok"
    assert doc["untyped_vocab_terms"] == [
        {
            "path": "outline/units/04-struggle.md",
            "field": "functions",
            "term": "intimidacion",
            "vocabulary": "propp",
        }
    ]

    graph = _load_graph(project)
    assert not _is_typed(graph, URIRef(URI_BASE + "narrative-function/intimidacion"))
    assert _is_typed(graph, URIRef(URI_BASE + "narrative-function/struggle"))


def test_propp_typo_human_render_enumerates_valid_terms(
    tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-002 / SC-002: the non-``--json`` build prints the per-entry line and the
    per-vocabulary valid-term enumeration to stderr (the render branch the JSON path
    bypasses). Stays on stderr — no JSON on stdout."""
    project = copy_fixture("tiny-quest", tmp_path)
    unit = project / "outline" / "units" / "04-struggle.md"
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            "functions: [struggle, victory]", "functions: [struggle, intimidacion]"
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["graph", "build"])
    assert result.exit_code == 0
    assert result.stdout.strip() == ""  # human mode: nothing on stdout
    assert (
        "outline/units/04-struggle.md: functions 'intimidacion' is not a propp term"
        in result.stderr
    )
    assert "valid propp terms:" in result.stderr
    # The enumeration lists the sorted rdfs:labels (e.g. the valid sibling 'struggle').
    assert "struggle" in result.stderr.split("valid propp terms:")[1]


# --- Greimas `narrative_roles:` actant is surfaced the same way --------


def test_greimas_bad_role_emits_one_warning_node_untyped(
    tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-001/006: an unrecognized Greimas role warns once; its role node is
    minted without ``crm:P2_has_type`` while the valid actant keeps its type.

    The other tiny-quest characters (``protagonist``/``villain`` — not Greimas
    actants) are removed so the scenario isolates a single character: a valid actant
    (``helper``) plus an unrecognized label (``villano``)."""
    project = copy_fixture("tiny-quest", tmp_path)
    _set_active(project, '["propp", "greimas"]')
    chars = project / "bible" / "characters"
    (chars / "liria.md").unlink()
    (chars / "nerot.md").unlink()
    brenna = chars / "brenna.md"
    brenna.write_text(
        brenna.read_text(encoding="utf-8").replace(
            "narrative_roles:\n  - helper",
            "narrative_roles:\n  - helper\n  - villano",
        ),
        encoding="utf-8",
    )
    doc = _build_json(project, runner, monkeypatch)

    greimas_entries = [w for w in doc["untyped_vocab_terms"] if w["vocabulary"] == "greimas"]
    assert greimas_entries == [
        {
            "path": "bible/characters/brenna.md",
            "field": "narrative_roles",
            "term": "villano",
            "vocabulary": "greimas",
        }
    ]

    graph = _load_graph(project)
    assert not _is_typed(graph, URIRef(URI_BASE + "character/brenna/role/villano"))
    assert _is_typed(graph, URIRef(URI_BASE + "character/brenna/role/helper"))


def test_greimas_blank_role_does_not_warn(tmp_path: Path) -> None:
    """Edge case / FR-007/010: a blank/unsluggable role mints no warnable node, so
    it emits no warning (only the genuinely unrecognized label does).

    Built over an isolated single-character bible so the assertion pins exactly the
    one expected entry."""
    bible = tmp_path / "bible" / "characters"
    bible.mkdir(parents=True)
    (bible / "ghost.md").write_text(
        '---\nname: "Ghost"\nnarrative_roles: [helper, "   ", villano]\n---\n', encoding="utf-8"
    )
    result = map_bible(tmp_path, tmp_path / "bible", URI_BASE, greimas=load_vocabulary("greimas"))
    greimas_terms = [w.term for w in result.untyped_vocab_terms if w.vocabulary == "greimas"]
    assert greimas_terms == ["villano"]  # blank "   " dropped, valid 'helper' not warned


# --- No active vocabulary + determinism --------------------------------


def test_no_active_vocabulary_emits_no_warnings_and_no_typing(
    tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-009 / SC-005 / C-5: with no vocabulary active the channel is empty and
    no node is typed, even though function/role names *would* match."""
    project = copy_fixture("tiny-quest", tmp_path)
    _set_active(project, "[]")
    doc = _build_json(project, runner, monkeypatch)

    assert doc["untyped_vocab_terms"] == []
    graph = _load_graph(project)
    assert not _is_typed(graph, URIRef(URI_BASE + "narrative-function/struggle"))


def test_two_builds_are_byte_identical(
    tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-016 / SC-008 / C-6: two builds of a warning-producing project yield
    byte-identical envelopes (entry order + enumerated valid terms are stable)."""
    project = copy_fixture("tiny-quest", tmp_path)
    unit = project / "outline" / "units" / "04-struggle.md"
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            "functions: [struggle, victory]", "functions: [struggle, intimidacion]"
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    first = runner.invoke(app, ["graph", "build", "--json"])
    second = runner.invoke(app, ["graph", "build", "--json"])
    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout
