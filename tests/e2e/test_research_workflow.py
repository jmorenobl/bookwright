"""The research flow proven end to end over the ``tiny-historical`` fixture (016).

Drives the **deterministic** research pipeline in-process (``typer.testing.CliRunner``)
exactly like ``tests/e2e/test_full_workflow.py``: ``graph build`` → ``graph query`` →
``validate``, every command with ``--json`` and its single JSON document parsed off
stdout (Principle IX). Four groups, mapped 1:1 to the contract
(``specs/016-research-e2e-docs/contracts/e2e-test-contract.md``):

* **Group A** — the planted findings fire exactly once each (FR-008..FR-011).
* **Group B** — the manual ``bookwright-verify`` step's preconditions hold (FR-012).
* **Group C** — the research machinery is inert when unused (FR-013/FR-014).
* **Group D** — the committed fixture tree is source-only (E1 invariants).

The expected ``factual_anchor`` counts and the anchor identifiers come from the
co-located oracle ``tiny-historical/expected-findings.md`` (loaded once, never
hard-coded). Because ``Finding``/``Anchor`` mint random uuid7 URIs, the only stable
handle on an anchor is the bible entity it ``bw:constrains`` — so the oracle records
those slugs and the assertions resolve each anchor's target through the graph.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.golem.slug import make_slug
from bookwright.io.frontmatter import parse_frontmatter
from tests.conftest import FIXTURES_DIR, copy_fixture

HISTORICAL = "tiny-historical"
NOVEL = "tiny-novel"

#: A uuid7 URI tail — must NOT appear in a normal-path factual_anchor message (048 SC-004).
_UUID7_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

#: The authored handle a factual_anchor message names the anchor by: ``anchor '<handle>'``.
_HANDLE_RE = re.compile(r"anchor '([^']*)'")

#: The Bookwright vocabulary IRI stem; its absence from a serialized graph proves the
#: research layer contributed nothing (FR-013).
BW_NAMESPACE = "bookwright.dev/vocab/bw"

#: The payoff query a ``bookwright-verify`` run relies on: every anchor with its
#: promoted finding's claim, a supporting source, and the entity it constrains.
ANCHOR_QUERY = (
    "SELECT ?anchor ?claim ?source ?target WHERE { "
    "?anchor bw:promotes ?f . ?f bw:claim ?claim ; bw:supportedBy ?source . "
    "OPTIONAL { ?anchor bw:constrains ?target } }"
)

#: Each anchor's time-span boundaries (``begin``/``end`` years) via CIDOC P82a/P82b.
SPAN_QUERY = (
    "SELECT ?anchor ?begin ?end WHERE { "
    "?anchor bw:promotes ?f . ?anchor crm:P4_has_time-span ?ts . "
    "OPTIONAL { ?ts crm:P82a_begin_of_the_begin ?begin } "
    "OPTIONAL { ?ts crm:P82b_end_of_the_end ?end } }"
)

#: Anchors typed as the CIDOC reification node and carrying ``bw:promotes`` (FR-009).
PROMOTING_ANCHORS = "SELECT ?a WHERE { ?a a crm:E13_Attribute_Assignment ; bw:promotes ?f }"

#: Findings reached through their supporting source edge (FR-008).
SUPPORTED_FINDINGS = "SELECT ?s WHERE { ?f bw:supportedBy ?s }"


# --------------------------------------------------------------------------------------
# Harness — the oracle loader and the in-process CLI helpers (single source of truth).
# --------------------------------------------------------------------------------------


def _load_oracle() -> dict[str, Any]:
    """Load ``tiny-historical/expected-findings.md`` front-matter (the oracle, D4).

    Read from the *committed* fixture so the expectations are pinned at one place; the
    presence of the copied file in ``tmp_path`` is checked separately (Group B).
    """
    path = FIXTURES_DIR / HISTORICAL / "expected-findings.md"
    return parse_frontmatter(path.read_text(encoding="utf-8")).metadata


@pytest.fixture()
def oracle() -> dict[str, Any]:
    """The parsed expected-findings front-matter, shared across the assertions."""
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


def _build(cli: CliRunner) -> dict[str, Any]:
    """Run ``graph build --json``; assert it succeeds and return the payload."""
    result = cli.invoke(app, ["graph", "build", "--json"])
    assert result.exit_code == 0, result.stdout
    return _payload(result)


def _query(cli: CliRunner, sparql: str) -> list[dict[str, str]]:
    """Run ``graph query --json``; assert success and return the result rows."""
    result = cli.invoke(app, ["graph", "query", sparql, "--json"])
    assert result.exit_code == 0, result.stdout
    rows: list[dict[str, str]] = _payload(result)["results"]
    return rows


def _factual(violations: list[dict[str, Any]], severity: str) -> list[dict[str, Any]]:
    """The ``factual_anchor`` violations of one severity (scoped, never global, D5)."""
    return [
        v for v in violations if v["validator"] == "factual_anchor" and v["severity"] == severity
    ]


# --------------------------------------------------------------------------------------
# Group A — the deterministic flow over tiny-historical (FR-008..FR-011).
# --------------------------------------------------------------------------------------


def test_build_materializes_research_entities(cli: CliRunner, historical: Path) -> None:
    """``graph build`` succeeds and the graph holds Sources, Findings, Anchors (FR-008/009)."""
    payload = _build(cli)
    # Structural build tallies (not planted defects): the fixture's fixed entity counts.
    # Unlike the factual_anchor expectations, these aren't oracle-driven — they pin the
    # shape of the corpus itself, so update them here if the fixture's entities change.
    assert payload["sources"] == 4
    assert payload["findings"] == 6  # 4 closed findings + 2 open questions
    assert payload["anchors"] == 4
    assert (historical / "bible" / "graph.ttl").is_file()
    # The anchors are real reified nodes and the source-support edge resolves.
    assert len(_query(cli, PROMOTING_ANCHORS)) == 4
    assert _query(cli, SUPPORTED_FINDINGS)  # at least one bw:supportedBy edge


def test_query_retrieves_anchors_with_claims_and_spans(cli: CliRunner, historical: Path) -> None:
    """The payoff query returns the anchors with claims/sources incl. spans (FR-010)."""
    _build(cli)
    rows = _query(cli, ANCHOR_QUERY)
    # Every anchor row carries a non-empty claim and a resolvable source.
    assert rows
    assert all(row["claim"].strip() and row["source"] for row in rows)

    spans = {(_year(row.get("begin")), _year(row.get("end"))) for row in _query(cli, SPAN_QUERY)}
    # The dated anchors are queryable with concrete begin/end boundaries.
    assert (1851, 1851) in spans
    assert (1920, 1925) in spans


def test_validate_reports_exactly_the_planted_findings(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """``validate`` emits exactly the oracle's factual_anchor findings, no more (FR-011)."""
    _build(cli)
    result = cli.invoke(app, ["validate", "--json"])
    # The R5 anachronism is an error-severity finding, so the gate fires (non-zero exit).
    assert result.exit_code != 0
    payload = _payload(result)
    assert payload["failed"] is True

    expected = oracle["factual_anchor"]["expected_counts"]
    errors = _factual(payload["violations"], "error")
    warnings = _factual(payload["violations"], "warning")
    assert len(errors) == expected["error"]
    assert len(warnings) == expected["warning"]

    # The error is the time-span anachronism on the dated event the oracle names. The
    # implicated constrains triple still carries the (stable-slug) event target URI.
    error_anchor = oracle["factual_anchor"]["error_anchor"]
    assert any(triple[2].endswith(error_anchor) for triple in errors[0]["triples"])
    assert "anachronism" in errors[0]["message"]

    # The warning is the under-reliable anchor. Post-048 the anchor is named by its
    # authored handle (promotes -> constrains), not the uuid7 URI, so match the oracle
    # via the handle's constrains target (the anchor's uuid7 is re-minted in-process and
    # is NOT a stable handle — research D1).
    warning_anchor = oracle["factual_anchor"]["warning_anchor"]
    handle = _HANDLE_RE.search(warnings[0]["message"])
    assert handle is not None and " -> " in handle.group(1)
    assert make_slug(handle.group(1).split(" -> ", 1)[1]) == warning_anchor
    assert "minimum reliability" in warnings[0]["message"]

    # 048 (SC-001/SC-004): both findings resolve source to the anchor's research file
    # (not null) and no message names the anchor by a raw uuid7 tail.
    for finding in (errors[0], warnings[0]):
        assert finding["source"] == "bible/research/telar-y-fabrica.md"
        assert not _UUID7_RE.search(finding["message"])


def test_validate_never_rewrites_the_derived_graph(cli: CliRunner, historical: Path) -> None:
    """The in-process anchor corpus persists nothing — validate writes no graph (FR-013)."""
    _build(cli)
    graph = historical / "bible" / "graph.ttl"
    before = graph.read_bytes()
    result = cli.invoke(app, ["validate", "--json"])
    assert result.exit_code != 0  # the planted anachronism gates, so validate did run
    # factual_anchor's in-process corpus build never calls engine.save, and validate is
    # a pure read: graph.ttl is byte-for-byte what `graph build` wrote (research D1/FR-013).
    assert graph.read_bytes() == before


# --------------------------------------------------------------------------------------
# Group B — verify-step preconditions (FR-012).
# --------------------------------------------------------------------------------------


def test_contradicted_anchor_is_queryable_for_verify(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """The dated anchor the prose contradicts is queryable with its claim + source (FR-012)."""
    _build(cli)
    contradicted = oracle["verify"]["contradicted_anchor"]
    rows = [
        row for row in _query(cli, ANCHOR_QUERY) if row.get("target", "").endswith(contradicted)
    ]
    assert rows, f"no anchor constrains {contradicted!r}"
    assert all(row["claim"].strip() and row["source"] for row in rows)


def test_verify_skill_materializes(cli: CliRunner, historical: Path) -> None:
    """``integration use claude`` writes the verify (and research) skills (FR-012)."""
    result = cli.invoke(app, ["integration", "use", "claude", "--json"])
    assert result.exit_code == 0, result.stdout
    skills = historical / ".claude" / "skills"
    assert (skills / "bookwright-verify" / "SKILL.md").is_file()
    assert (skills / "bookwright-research" / "SKILL.md").is_file()


def test_oracle_is_present_and_parses(
    cli: CliRunner, historical: Path, oracle: dict[str, Any]
) -> None:
    """The co-located oracle ships in the fixture root and its front-matter loads (FR-012)."""
    copied = historical / "expected-findings.md"
    assert copied.is_file()
    front_matter = parse_frontmatter(copied.read_text(encoding="utf-8")).metadata
    assert front_matter == oracle  # the copy and the committed source agree
    assert "manuscript_file" in oracle["verify"]
    assert (historical / oracle["verify"]["manuscript_file"]).is_file()


# --------------------------------------------------------------------------------------
# Group C — inertness when the research system is unused (FR-013, FR-014).
# --------------------------------------------------------------------------------------


def test_research_free_project_is_inert(
    cli: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A project with no ``bible/research/`` pays nothing for the research layer (FR-013)."""
    project = copy_fixture(NOVEL, tmp_path)
    monkeypatch.chdir(project)
    _build(cli)

    graph_text = (project / "bible" / "graph.ttl").read_text(encoding="utf-8")
    assert BW_NAMESPACE not in graph_text  # no research vocabulary emitted at all
    assert not _query(cli, PROMOTING_ANCHORS)  # no anchors → research added zero E13

    result = cli.invoke(app, ["validate", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = _payload(result)
    assert payload["failed"] is False
    assert not _factual(payload["violations"], "error")
    assert not _factual(payload["violations"], "warning")


def test_disabled_research_block_is_inert(
    cli: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Flipping ``[research].enabled = false`` silences the research layer entirely (FR-014)."""
    project = copy_fixture(HISTORICAL, tmp_path)
    manifest = project / "manifest.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("enabled = true", "enabled = false"),
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    _build(cli)

    result = cli.invoke(app, ["validate", "--json"])
    # With research off, the R5 error is gone; overall validation behaves like v0.1.
    assert result.exit_code == 0, result.stdout
    payload = _payload(result)
    assert payload["failed"] is False
    assert not _factual(payload["violations"], "error")
    assert not _factual(payload["violations"], "warning")


# --------------------------------------------------------------------------------------
# Group D — the committed fixture tree is source-only (E1 invariants).
# --------------------------------------------------------------------------------------


def test_committed_fixture_is_source_only() -> None:
    """The committed ``tiny-historical`` ships no derived graph and no materialized skills."""
    root = FIXTURES_DIR / HISTORICAL
    assert root.is_dir()
    assert not (root / "bible" / "graph.ttl").exists()
    assert not (root / ".claude").exists()
    assert not (root / ".agents").exists()
    assert not list(root.rglob("SKILL.md"))


def test_committed_fixture_has_no_pending_sentinels() -> None:
    """The fixture is *finished* — no ``[PENDING: …]`` sentinel survives in any file."""
    root = FIXTURES_DIR / HISTORICAL
    offenders = [
        path.relative_to(root).as_posix()
        for path in sorted(root.rglob("*.md"))
        if "[PENDING:" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


# --------------------------------------------------------------------------------------
# Helpers.
# --------------------------------------------------------------------------------------


def _year(raw: str | None) -> int | None:
    """Coerce a ``gYear`` cell (``"1851"``) to ``int``; pass ``None`` through."""
    return int(raw) if raw is not None else None
