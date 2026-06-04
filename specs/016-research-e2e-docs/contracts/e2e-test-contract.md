# Contract — `tests/e2e/test_research_workflow.py`

In-process CLI (`typer.testing.CliRunner`) over fixtures copied to `tmp_path` via
`tests/conftest.py::copy_fixture` + `monkeypatch.chdir`. Mirrors `tests/e2e/test_full_workflow.py`
and `tests/fixtures/test_fixtures.py`. Every command is invoked with `--json` and the JSON is
parsed off stdout (Constitution IX). The expected `factual_anchor` counts + anchor identifiers
come from `tiny-historical/expected-findings.md` (loaded once), never hard-coded twice.

## Group A — the deterministic flow over `tiny-historical` (US2 / FR-008..FR-011)

| Test | Asserts | FR |
|---|---|---|
| build succeeds w/ research entities | `graph build --json` exit 0; the graph holds Sources, Findings, Anchors (e.g. `bw:` triples present; an anchor `E13` with `bw:promotes`; a `bw:supportedBy` source). | FR-008/FR-009 |
| query retrieves anchors | `graph query --json` with the payoff SPARQL (`?anchor bw:promotes ?f . ?f bw:claim ?c ; bw:supportedBy ?s`) returns the fixture's anchors with claims/sources, **including the dated anchor**; a span query returns its `begin`/`end`. | FR-010 |
| validate reports exactly the planted findings | `validate --json` → `factual_anchor` emits **exactly** `{warning: 1, error: 1}` (the counts from the oracle); the warning is on `warning_anchor`, the error on `error_anchor`; **no other** `factual_anchor` findings. | FR-011 |

The validate assertion is scoped to `validator == "factual_anchor"` findings (other validators
may emit unrelated heuristic warnings; the fixture is built so they don't, but the assertion
must be specific to be robust). Exit code: `validate` returns non-zero because there is an
`error`-severity finding — assert that too (the error gate fires).

## Group B — verify preconditions (US2 / FR-012)

| Test | Asserts | FR |
|---|---|---|
| anchors queryable for verify | the same payoff query returns the `contradicted_anchor` (the dated anchor the prose violates) with its claim + source. | FR-012 |
| verify skill materialized | `integration use claude` in the tmp copy → `.claude/skills/bookwright-verify/SKILL.md` exists (and `bookwright-research/SKILL.md`). | FR-012 |
| oracle present | `expected-findings.md` exists in the fixture root and parses (front-matter loads). | FR-012 |

No LLM is invoked; the test confirms the manual step *can* run. The expected findings of that
manual step live in the oracle body + `docs/research.md`.

## Group C — inertness (US3 / FR-013, FR-014)

| Test | Asserts | FR |
|---|---|---|
| no-directory inertness | `tiny-novel` (research-free): build → query → validate; derived `graph.ttl` has **no** `bw:` prefix; E13 count == bible baseline; **zero** `factual_anchor` findings; `validate` exit 0, `failed is False`. | FR-013 |
| disabled-block inertness | copy `tiny-historical`, set `[research].enabled = false`; build → validate; **zero** `factual_anchor` findings; overall validation behaves like a clean project (no `error` from the research layer). | FR-014 |

## Group D — fixture hygiene (E1 invariants)

| Test | Asserts |
|---|---|
| source-only committed tree | `tiny-historical` ships no `bible/graph.ttl`, no `.claude/`/`.agents/`, no `SKILL.md`. |
| no PENDING sentinels | no `[PENDING:` in any `*.md` of the committed fixture. |

## Non-goals (asserted-by-omission, FR-022)

No ChromaDB/vector import, no new CLI command, no new manifest field. The test only consumes
the existing `graph build/query`, `validate`, and `integration use` surfaces.
