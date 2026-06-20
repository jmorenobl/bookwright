"""The v0.4 narrative-structure flow proven end to end over the ``tiny-quest`` fixture (032).

Walks the authored path **ingest → ``graph build`` → ``validate``** against the
source-only ``tiny-quest`` project on a ``tmp_path`` copy, in-process via
``typer.testing.CliRunner`` — the same harness ``test_orchestration_workflow.py``
(023) uses: ``copy_fixture``, ``monkeypatch.chdir``, ``_payload``/``_build_cli``,
and an oracle loaded once from the co-located ``expected-narrative.md``. Every
count and identifier asserted comes from that oracle (FR-005/FR-008/FR-009); none
is hard-coded here.

Where ``graph build --json`` does not surface a fact (per-typing edges, ordered
members, role cross-refs), the test queries the **derived graph** directly through
:func:`build_project_graph` and the engine's SPARQL — the
``test_ingestion_parity::_observed_types`` pattern. The assertion surface is the
deterministic graph triples and the ``validate --json`` document only; no LLM /
judgment step is invoked (FR-011).

Four groups, mapped 1:1 to ``contracts/e2e-narrative-workflow.md``:

* **Group A** — ``graph build`` produces the oracle's G9/G10/G7 facts + Propp typings.
* **Group B** — ``validate`` reports the exact ``narrative_structure`` findings.
* **Group C** — non-regression: empty ``[vocabularies] active`` → no typings, all else identical.
* **Group D** — determinism + the committed fixture stays source-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import tomlkit
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.commands._graph import build_project_graph
from bookwright.core.manifest import Manifest
from bookwright.golem import NarrativeSequence
from bookwright.golem.namespaces import GOLEM, HAS_TYPE, PROPER_PART, REFERS_TO
from bookwright.golem.slug import make_slug
from bookwright.indexers import Indexer
from bookwright.io.bible import map_bible
from bookwright.io.frontmatter import parse_frontmatter
from bookwright.io.outline import map_outline
from tests.conftest import FIXTURES_DIR, copy_fixture

QUEST = "tiny-quest"
ORACLE_FILE = "expected-narrative.md"
VALIDATOR = "narrative_structure"

_G9 = f"<{GOLEM['G9_Narrative_Unit']}>"
_G10 = f"<{GOLEM['G10_Narrative_Function']}>"
_G7 = f"<{GOLEM['G7_Narrative_Sequence']}>"
_G11 = f"<{GOLEM['G11_Narrative_Role']}>"


# --------------------------------------------------------------------------------------
# Harness — the oracle loader, the in-process CLI helpers, and the graph-fact extractor.
# --------------------------------------------------------------------------------------


def _load_oracle() -> dict[str, Any]:
    """Load ``tiny-quest/expected-narrative.md`` front-matter — the single source of truth.

    Read from the *committed* fixture so the expectations are pinned in one place;
    the presence of the copied file in ``tmp_path`` is checked separately (Group D).
    """
    path = FIXTURES_DIR / QUEST / ORACLE_FILE
    return parse_frontmatter(path.read_text(encoding="utf-8")).metadata


@pytest.fixture()
def oracle() -> dict[str, Any]:
    """The parsed ``expected-narrative.md`` front-matter, shared across the assertions."""
    return _load_oracle()


@pytest.fixture()
def quest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copy ``tiny-quest`` into ``tmp_path`` and ``chdir`` into the copy."""
    project = copy_fixture(QUEST, tmp_path)
    monkeypatch.chdir(project)
    return project


def _payload(result: Any) -> dict[str, Any]:
    """Parse the single JSON document a ``--json`` command writes to stdout."""
    return json.loads(result.stdout)  # type: ignore[no-any-return]


def _build_cli(cli: CliRunner) -> dict[str, Any]:
    """Run ``graph build --json``; assert it succeeds and return the payload."""
    result = cli.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 0, result.stdout
    return _payload(result)


def _validate(cli: CliRunner) -> dict[str, Any]:
    """Run ``validate --json``; assert exit 0 (warning-only) and return the payload."""
    result = cli.invoke(app, ["validate", "--json"])
    assert result.exit_code == 0, result.stdout
    return _payload(result)


def _last(uri: str) -> str:
    """The final path segment of a URI — the entity/term slug used in messages."""
    return uri.rsplit("/", 1)[-1]


def _engine(root: Path) -> Indexer:
    """Build ``tiny-quest`` through the real pipeline and return the populated engine."""
    manifest = Manifest.load(root / "manifest.toml")
    return build_project_graph(root, manifest).engine


def _ordered_members(root: Path) -> list[str]:
    """The lone sequence's member slugs in emitted ``dlp:proper-part`` order.

    Member order is an *emission-order* contract, never a graph fact: RDF is
    unordered, so the graph carries no member ordinal and a SPARQL re-query cannot
    recover the ``order``-sorted line (``ORDER BY`` would only yield the alphabetical
    URI order, which is the wrong sequence). The slugs are therefore read from the
    assembled :class:`NarrativeSequence` entity's emitted triples, in tuple order —
    the iteration-029 ``_member_names`` pattern. A second deterministic mapping pass
    (no vocabularies: typing does not touch membership) yields that entity.
    """
    manifest = Manifest.load(root / "manifest.toml")
    uri_base = manifest.bookwright.uri_base
    result = map_bible(root, root / manifest.paths.bible, uri_base)
    map_outline(root, root / manifest.paths.outline, uri_base, result)
    sequences = [e for e in result.entities if isinstance(e, NarrativeSequence)]
    if not sequences:
        return []
    sequence = sequences[0]
    return [
        _last(str(obj))
        for subj, pred, obj in sequence.to_triples()
        if subj == sequence.uri and pred == PROPER_PART
    ]


def _graph_facts(root: Path) -> dict[str, Any]:
    """The deterministic graph facts the oracle pins (Group A surface).

    The set-based facts (units, functions, typings, sequence identity, role
    cross-refs) are read from the derived graph via SPARQL — the graph the
    validators consume. ``members`` is the one ordered fact, so it comes from the
    entity's emitted ``dlp:proper-part`` order (:func:`_ordered_members`), not a
    SPARQL re-query the unordered graph cannot answer deterministically. ``typed``
    maps each typed function slug to its Propp term's last path segment; the
    slug/role lists are sorted because they are compared as sets.
    """
    engine = _engine(root)
    units = {_last(r["u"]): r["u"] for r in engine.query(f"SELECT ?u WHERE {{ ?u a {_G9} }}")}
    functions = sorted(_last(r["f"]) for r in engine.query(f"SELECT ?f WHERE {{ ?f a {_G10} }}"))
    typed = {
        _last(r["f"]): _last(r["t"])
        for r in engine.query(f"SELECT ?f ?t WHERE {{ ?f a {_G10} . ?f <{HAS_TYPE}> ?t }}")
    }
    sequences = sorted(r["s"] for r in engine.query(f"SELECT ?s WHERE {{ ?s a {_G7} }}"))
    members = _ordered_members(root) if sequences else []
    roles: dict[str, list[str]] = {}
    for slug, uri in units.items():
        resolved = sorted(
            _last(r["r"])
            for r in engine.query(f"SELECT ?r WHERE {{ <{uri}> <{REFERS_TO}> ?r . ?r a {_G11} }}")
        )
        if resolved:
            roles[slug] = resolved
    return {
        "units": sorted(units),
        "functions": functions,
        "typed": typed,
        "sequence_slugs": [_last(s) for s in sequences],
        "members": members,
        "roles": roles,
    }


def _ns_violations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """The ``violations[]`` entries scoped to the ``narrative_structure`` validator."""
    return [v for v in payload["violations"] if v["validator"] == VALIDATOR]


def _disable_vocabularies(root: Path) -> None:
    """Empty ``[vocabularies] active`` in the copy's manifest (Group C runtime toggle)."""
    path = root / "manifest.toml"
    doc = tomlkit.parse(path.read_text(encoding="utf-8"))
    doc["vocabularies"]["active"] = []
    path.write_text(tomlkit.dumps(doc), encoding="utf-8")


# --------------------------------------------------------------------------------------
# Group A — build produces the oracle's graph facts (FR-008).
# --------------------------------------------------------------------------------------


def test_build_succeeds_with_headline_counts(cli: CliRunner, quest: Path) -> None:
    """A0: ``graph build --json`` exits 0 and reports positive entity/triple counts."""
    payload = _build_cli(cli)
    assert payload["status"] == "ok"
    assert payload["entities"] > 0
    assert payload["triples"] > 0


def test_build_materializes_units_and_functions(quest: Path, oracle: dict[str, Any]) -> None:
    """A1/A2: the G9 unit set and the distinct G10 function count match the oracle."""
    facts = _graph_facts(quest)
    assert facts["units"] == sorted(oracle["units"]["slugs"])
    assert len(facts["units"]) == oracle["units"]["count"]
    assert len(facts["functions"]) == oracle["functions"]["count"]


def test_build_types_functions_against_propp(quest: Path, oracle: dict[str, Any]) -> None:
    """A3: the typed map equals the oracle exactly — an extra or missing
    ``crm:P2_has_type`` Propp edge fails the dict equality."""
    facts = _graph_facts(quest)
    assert facts["typed"] == oracle["functions"]["typed"]


def test_build_assembles_the_ordered_sequence(quest: Path, oracle: dict[str, Any]) -> None:
    """A4: exactly one G7 named (by slug) ``oracle.sequence.name`` with ordered members."""
    facts = _graph_facts(quest)
    assert facts["sequence_slugs"] == [make_slug(oracle["sequence"]["name"])]
    assert facts["members"] == oracle["sequence"]["members"]


def test_build_resolves_role_cross_refs(quest: Path, oracle: dict[str, Any]) -> None:
    """A5: each resolved ``roles:`` slug is a unit→role edge; the orphan card's
    ``dragon`` yields no edge (omen-beat absent from the role map)."""
    facts = _graph_facts(quest)
    expected = {unit: sorted(roles) for unit, roles in oracle["roles_resolved"].items()}
    assert facts["roles"] == expected
    orphan = oracle["narrative_structure"]["orphan_beats"][0]["unit"]
    assert orphan not in facts["roles"]


# --------------------------------------------------------------------------------------
# Group B — validate reports the exact findings (FR-009).
# --------------------------------------------------------------------------------------


def test_validate_reports_the_orphan_beat(
    cli: CliRunner, quest: Path, oracle: dict[str, Any]
) -> None:
    """B1: one ``warning`` per oracle ``orphan_beats`` entry, naming the slug + phrase."""
    _build_cli(cli)
    violations = _ns_violations(_validate(cli))
    for entry in oracle["narrative_structure"]["orphan_beats"]:
        match = next(
            v
            for v in violations
            if v["source"] == entry["source"] and "orphan beat" in v["message"]
        )
        assert match["severity"] == "warning"
        assert entry["unit"] in match["message"]


def test_validate_reports_the_unresolved_role(
    cli: CliRunner, quest: Path, oracle: dict[str, Any]
) -> None:
    """B2: one ``warning`` per oracle ``unresolved_roles`` entry, naming unit + role."""
    _build_cli(cli)
    violations = _ns_violations(_validate(cli))
    for entry in oracle["narrative_structure"]["unresolved_roles"]:
        match = next(
            v
            for v in violations
            if v["source"] == entry["source"] and "resolves to no character role" in v["message"]
        )
        assert match["severity"] == "warning"
        assert entry["unit"] in match["message"]
        assert entry["role"] in match["message"]


def test_validate_finding_counts_are_exact(
    cli: CliRunner, quest: Path, oracle: dict[str, Any]
) -> None:
    """B3/B4: the scoped warning/error counts equal the oracle; no error fires overall."""
    _build_cli(cli)
    payload = _validate(cli)
    violations = _ns_violations(payload)
    counts = oracle["narrative_structure"]["counts"]
    assert sum(v["severity"] == "warning" for v in violations) == counts["warning"]
    assert sum(v["severity"] == "error" for v in violations) == counts["error"]
    # The validator is warning-only, so the whole run's error gate stays green.
    assert payload["failed"] is False
    assert all(v["severity"] != "error" for v in payload["violations"])


# --------------------------------------------------------------------------------------
# Group C — non-regression when no vocabulary is active (FR-010, edge case).
# --------------------------------------------------------------------------------------


def test_emptying_vocabularies_drops_only_the_typings(quest: Path, oracle: dict[str, Any]) -> None:
    """C1/C2: with ``active = []`` the typings vanish while every other fact is identical."""
    propp_facts = _graph_facts(quest)
    _disable_vocabularies(quest)
    noprop_facts = _graph_facts(quest)

    # C1 — no typing edge survives; the oracle's typed map is entirely absent.
    assert noprop_facts["typed"] == {}
    # C2 — units, function count, sequence + members, role cross-refs byte-identical.
    assert {k: v for k, v in noprop_facts.items() if k != "typed"} == {
        k: v for k, v in propp_facts.items() if k != "typed"
    }
    # Sanity: the Propp-active build *did* carry the typings the toggle removed.
    assert propp_facts["typed"] == oracle["functions"]["typed"]


def test_findings_survive_disabled_vocabularies(
    cli: CliRunner, quest: Path, oracle: dict[str, Any]
) -> None:
    """C3: the ``narrative_structure`` findings do not depend on vocabulary activation."""
    _disable_vocabularies(quest)
    _build_cli(cli)
    violations = _ns_violations(_validate(cli))
    counts = oracle["narrative_structure"]["counts"]
    assert sum(v["severity"] == "warning" for v in violations) == counts["warning"]
    sources = sorted(v["source"] for v in violations)
    expected_sources = sorted(
        entry["source"]
        for group in ("orphan_beats", "unresolved_roles")
        for entry in oracle["narrative_structure"][group]
    )
    assert sources == expected_sources


# --------------------------------------------------------------------------------------
# Group D — determinism + the committed fixture is source-only (FR-011).
# --------------------------------------------------------------------------------------


def test_build_and_validate_are_deterministic(cli: CliRunner, quest: Path) -> None:
    """D1: two independent build→validate passes yield byte-identical asserted facts."""
    first_facts = _graph_facts(quest)
    second_facts = _graph_facts(quest)
    assert first_facts == second_facts

    _build_cli(cli)
    first_violations = _ns_violations(_validate(cli))
    second_violations = _ns_violations(_validate(cli))
    assert first_violations == second_violations


def test_committed_fixture_is_source_only() -> None:
    """D2: committed ``tiny-quest`` ships no derived graph / skills; the oracle is inert."""
    root = FIXTURES_DIR / QUEST
    assert root.is_dir()
    assert not (root / "bible" / "graph.ttl").exists()
    assert not (root / ".claude").exists()
    assert not (root / ".agents").exists()
    assert not list(root.rglob("SKILL.md"))
    # The v0.4 worked example ships as plain source: the oracle is present-but-inert.
    assert (root / ORACLE_FILE).is_file()
    assert (root / "outline" / "units").is_dir()
