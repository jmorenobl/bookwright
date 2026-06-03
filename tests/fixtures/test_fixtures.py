"""Each committed fixture is a *finished*, clean Bookwright project (US1, SC-001).

Copies every fixture into ``tmp_path`` and drives the real CLI in-process
(``graph build`` → ``graph query`` → ``validate``), then guards the committed
source tree itself. The contract is fixture-shape.md / data-model E1:

* ``graph build`` → exit 0, **0 skips, 0 unknown_keys, 0 unresolved** (VR-1/F2);
* ``tiny-novel`` graph query → **exactly 3 Character, 2 Setting, 5 NarrativeEvent**
  (VR-2/SC-001); ``tiny-memoir`` → its single protagonist + events in the index;
* ``validate`` → exit 0 **and** ``failed is False`` **and** zero ``error``-severity
  findings — asserted against the *error* gate, not ``status == "ok"``, because
  heuristic ``warning``s are permitted and non-gating (VR-3/F3, revised D3);
* the *committed* tree carries no derived ``graph.ttl`` / skills dir (VR-5/F5) and
  no ``[PENDING: …]`` sentinel survives in any author-fill section (VR-4/F4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from tests.conftest import FIXTURES_DIR, copy_fixture

FIXTURES = ["tiny-novel", "tiny-essay", "tiny-memoir"]

#: Expected entity counts per fixture, keyed by GOLEM rdf:type local name.
EXPECTED_COUNTS: dict[str, dict[str, int]] = {
    "tiny-novel": {"G1_Character": 3, "G12_Setting": 2, "G5_Narrative_Event": 5},
    "tiny-essay": {"G1_Character": 0, "G12_Setting": 0, "G5_Narrative_Event": 0},
    "tiny-memoir": {"G1_Character": 1, "G12_Setting": 0, "G5_Narrative_Event": 2},
}


@pytest.fixture(params=FIXTURES)
def fixture_project(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, Path]:
    """Copy the parametrized fixture into ``tmp_path`` and ``chdir`` into the copy."""
    project = copy_fixture(request.param, tmp_path)
    monkeypatch.chdir(project)
    return request.param, project


def _count(runner: CliRunner, golem_class: str) -> int:
    """Run a ``COUNT`` query for one GOLEM class and return the integer result."""
    query = f"SELECT (COUNT(?x) AS ?n) WHERE {{ ?x a golem:{golem_class} }}"
    result = runner.invoke(app, ["graph", "query", query, "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    return int(payload["results"][0]["n"]) if payload["results"] else 0


def test_fixture_builds_clean(fixture_project: tuple[str, Path], cli: CliRunner) -> None:
    """``graph build`` succeeds with zero skips / unknown keys / unresolved refs (VR-1)."""
    name, _ = fixture_project
    result = cli.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 0, f"{name}: {result.stdout}"
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["skipped"] == []
    assert payload["unknown_keys"] == []
    assert payload["unresolved_participants"] == []


def test_fixture_entity_counts(fixture_project: tuple[str, Path], cli: CliRunner) -> None:
    """Each fixture's graph holds exactly the contracted entity counts (VR-2/SC-001)."""
    name, _ = fixture_project
    assert cli.invoke(app, ["graph", "build", "--json"]).exit_code == 0
    for golem_class, expected in EXPECTED_COUNTS[name].items():
        assert _count(cli, golem_class) == expected, f"{name}/{golem_class}"


def test_fixture_validates_clean(fixture_project: tuple[str, Path], cli: CliRunner) -> None:
    """``validate`` exits 0 with zero error-severity findings (VR-3; warnings allowed)."""
    name, _ = fixture_project
    assert cli.invoke(app, ["graph", "build", "--json"]).exit_code == 0
    result = cli.invoke(app, ["validate", "--json"])
    assert result.exit_code == 0, f"{name}: {result.stdout}"
    payload = json.loads(result.stdout)
    assert payload["failed"] is False
    assert payload["summary"]["by_severity"]["error"] == 0


@pytest.mark.parametrize("name", FIXTURES)
def test_committed_tree_is_source_only(name: str) -> None:
    """No derived ``graph.ttl`` and no materialized skills dir is committed (VR-5/F5)."""
    root = FIXTURES_DIR / name
    assert root.is_dir()
    assert not (root / "bible" / "graph.ttl").exists()
    assert not (root / ".claude").exists()
    assert not (root / ".agents").exists()
    assert not list(root.rglob("SKILL.md"))


@pytest.mark.parametrize("name", FIXTURES)
def test_no_pending_sentinels(name: str) -> None:
    """A shipped fixture is *finished* — no ``[PENDING: …]`` sentinel survives (VR-4/F4)."""
    root = FIXTURES_DIR / name
    offenders = [
        path.relative_to(root).as_posix()
        for path in sorted(root.rglob("*.md"))
        if "[PENDING:" in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"{name}: PENDING sentinels in {offenders}"
