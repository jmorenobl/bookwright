"""Provenance integration tests (US3, FR-011, SC-006, R6, quickstart § 3).

Every derived assertion carries a ``crm:E13_Attribute_Assignment`` naming its
source file; a line-locatable value also carries the ``…:N`` locator. Provenance
is retrievable via SPARQL.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bookwright.cli import app

CHARACTER_URI = "https://example.org/my-novel/character/manuel-de-aparici"
SOURCE_QUERY = (
    "SELECT ?src WHERE { "
    "?a a crm:E13_Attribute_Assignment ; "
    f"crm:P140_assigned_attribute_to <{CHARACTER_URI}> ; "
    "crm:P16_used_specific_object ?src }"
)


def _sources(tiny_novel: Path, runner: CliRunner) -> set[str]:
    assert runner.invoke(app, ["graph", "build", "--json"]).exit_code == 0
    result = runner.invoke(app, ["graph", "query", SOURCE_QUERY, "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    return {row["src"] for row in payload["results"]}


def test_identity_assignment_names_the_file(tiny_novel: Path, runner: CliRunner) -> None:
    sources = _sources(tiny_novel, runner)
    assert "bible/characters/aparici.md" in sources


def test_line_locatable_value_carries_locator(tiny_novel: Path, runner: CliRunner) -> None:
    # `born: 1828` is on line 3 of bible/characters/aparici.md (line 1 is the fence).
    sources = _sources(tiny_novel, runner)
    assert "bible/characters/aparici.md:3" in sources


def test_every_derived_assertion_has_an_assignment(tiny_novel: Path, runner: CliRunner) -> None:
    """SC-006: count of E13 assignments equals the count of derived assertions
    across all entities (per-assertion provenance, not per-entity)."""
    assert runner.invoke(app, ["graph", "build", "--json"]).exit_code == 0
    count_query = "SELECT (COUNT(?a) AS ?n) WHERE { ?a a crm:E13_Attribute_Assignment }"
    result = runner.invoke(app, ["graph", "query", count_query, "--json"])
    payload = json.loads(result.stdout)
    # 1 character (identity + born + died + 1 feature + 1 role = 5)
    # + 1 setting (identity = 1)
    # + 1 event (identity + 1 participant = 2)
    # + 1 relationship (identity + 1 participant = 2)
    assert int(payload["results"][0]["n"]) == 10
