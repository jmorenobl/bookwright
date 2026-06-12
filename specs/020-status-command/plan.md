# Implementation Plan: Derived project status and next actions

**Branch**: `020-status-command` | **Date**: 2026-06-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/020-status-command/spec.md`

## Summary

Add `bookwright status`: a deterministic, LLM-free, network-free CLI verb that
(1) rebuilds the knowledge graph in memory from the corpus by reusing the
`graph build` pipeline (recomputation **is** the freshness mechanism — see
research.md D1), refreshing the derived `bible/graph.ttl` cache exactly as
`graph build` does; (2) aggregates the state facts — project phase
(`manifest.book.status`), focus echo (`[focus]`, iteration 019), open research
questions, anchors without sufficient support, low-reliability findings, and a
validation summary obtained from the existing validation runner; (3) maps the
facts through a static rule table (a pure `state → list[Action]` function,
unit-testable with no graph or project on disk) into `next_actions`; (4) emits
the report through a new shared success-envelope helper
(`{"status":"ok","focus":…,"state":…,"next_actions":…}`, Principle IX) and
regenerates `.bookwright/cache/status.json` with the byte-identical document.

Key design constraint discovered during planning: `Finding`/`Anchor` entities
mint fresh uuid7 URIs on every build, so the report MUST identify items by
**corpus-stable identifiers** (authored finding `id`s, file relpaths, claim
texts) and never by minted URIs — otherwise SC-002 (byte-identical repeated
runs) is unachievable. This drives an additive extension of
`io/research.ResearchResult` (research.md D2) and a small predicate-extraction
refactor of the `factual_anchor` validator so its detection logic is reused,
not duplicated (research.md D3).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: existing runtime set only — `typer` (CLI verb),
`rich` (stderr prose / human report), `rdflib` via the `Indexer` seam (SPARQL
aggregation), `pydantic` v2 + `tomlkit` (manifest), stdlib `json` (envelope +
cache). **No new dependencies.**

**Storage**: plain-text derived caches only — refreshes `bible/graph.ttl`
(Turtle, existing behavior reused from `graph build`) and writes
`.bookwright/cache/status.json` (compact JSON, write-only output, regenerated
every run, already gitignored by the scaffold). No new canonical storage
(Principle I).

**Testing**: `pytest` with ≥ 80 % global coverage (Principle VIII); unit tests
for the pure rule table (no graph, no disk), query-level tests against an
in-memory `RdflibIndexer`, command-level tests against known-state fixtures,
byte-identity double-run tests, and `factual_anchor` parity guards.

**Target Platform**: same as the CLI today — any OS with Python 3.11+;
no network, no LLM (FR-014).

**Project Type**: CLI subcommand + small library subpackage (src-layout).

**Performance Goals**: interactive CLI latency on `tiny-*` fixture-sized
projects (sub-second); the full pipeline (`map_bible` + `map_research` +
indexing + validators + aggregation) already runs in this envelope for
`graph build` + `validate`.

**Constraints**: byte-identical output across runs on an unchanged corpus
(SC-002): no timestamps, no random values, no environment data, no minted
URIs in the report; ordering fixed by rule priority then corpus-stable keys
(FR-010, FR-011a). Exit 0 whenever the report is computed (FR-015); unified
error envelope (iteration 018) on failures.

**Scale/Scope**: one new CLI verb, one new `src/bookwright/status/`
subpackage (3 modules), one shared envelope helper, one extracted build
pipeline helper, additive `io/research.py` extension, predicate extraction in
`factual_anchor`. No ontology changes (Principle X).

## Constitution Check

*GATE: evaluated before Phase 0; re-evaluated after Phase 1 design.*

| # | Principle | Verdict | Evidence |
|---|---|---|---|
| I | Plain text as source of truth | ✅ PASS | Only writes are two derived, reconstructible, gitignored caches: `bible/graph.ttl` (existing refresh, Turtle) and `.bookwright/cache/status.json` (plain JSON, regenerated every run, never read back — FR-012). No binary stores. |
| II | Modern Python stack | ✅ PASS | No new runtime dependency; uses `typer`/`rich`/`rdflib`/`pydantic` already locked. |
| III | src-layout | ✅ PASS | All code under `src/bookwright/`; all tests under `tests/`. |
| IV | Modular command surface | ✅ PASS | `commands/status.py` is one module registering one verb; pure rules / queries / model split into `src/bookwright/status/` keeps every file well under 500 lines. |
| V | Plugin-based integrations | ✅ N/A | No integration surface touched. |
| VI | Agent Skills only | ✅ N/A | This iteration emits no skills (skill consumption is 021–022, spec Out of Scope). No `commands/` directories written. |
| VII | agentskills.io compliance | ✅ N/A | No SKILL.md generated. |
| VIII | Test discipline | ✅ PASS | Unit (rules, queries, envelope), integration (command flow vs. fixtures, error envelopes, byte-identity), parity guards for the `factual_anchor` refactor; ≥ 80 % coverage gate unchanged. |
| IX | JSON-over-stdout | ✅ PASS | `--json` emits exactly one document via the shared `emit_json`; prose to stderr; non-zero exits carry the iteration-018 error envelope; new success-envelope helper single-sources the `{"status":"ok",…}` skeleton. |
| X | Design axioms | ✅ PASS | Pure aggregation over the frozen 17-class ontology; no new classes/properties (authored ids deliberately stay **out** of the graph — research.md D2); rdflib via the `Indexer` seam; no reopened § 16 axiom. |

**Scope & Release Discipline**: ✅ PASS — iteration 020 is exactly the next
planned M5 step (`bookwright status`, design § 21.4–21.6). No vector search,
no export, no cancelled capability, no "future X" plumbing: every refactor
(build-pipeline extraction, anchor-predicate extraction, `ResearchResult`
records) is consumed by this iteration's own code.

**Post-Phase-1 re-check**: ✅ PASS — the design artifacts introduce no new
violations; Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/020-status-command/
├── plan.md              # This file
├── research.md          # Phase 0 output (decisions D1–D8)
├── data-model.md        # Phase 1 output (state model, rule table, records)
├── quickstart.md        # Phase 1 output (validation scenarios)
├── contracts/
│   └── cli-status.md    # Phase 1 output (CLI/JSON/cache/exit-code contract)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── cli.py                          # MODIFIED: register app.command("status")
├── commands/
│   ├── _envelope.py                # MODIFIED: add ok_payload() success-envelope helper
│   ├── _graph.py                   # NEW: build_project_graph() — pipeline extracted
│   │                               #   from graph/build.py, shared by build + status
│   ├── graph/
│   │   └── build.py                # MODIFIED: thin wrapper over _graph.build_project_graph
│   └── status.py                   # NEW: the CLI verb (orchestration, envelope, cache)
├── status/                         # NEW subpackage: derived-state domain logic
│   ├── __init__.py                 # public surface re-exports
│   ├── model.py                    # StatusState, fact records, Action (+ payload shape)
│   ├── queries.py                  # SPARQL aggregations via the Indexer seam
│   └── rules.py                    # RULES table + next_actions(state) — pure, no I/O
├── io/
│   └── research.py                 # MODIFIED (additive): FindingIdentity/AnchorIdentity
│                                   #   exposing authored identity on ResearchResult
└── validation/
    └── validators/
        └── factual_anchor.py       # MODIFIED: R1/R3/R4 decisions extracted as pure
                                    #   module-level predicates (messages stay put)

tests/
├── status/                         # NEW
│   ├── __init__.py
│   ├── test_model.py               # state/payload serialization, determinism of shapes
│   ├── test_queries.py             # aggregations vs. in-memory RdflibIndexer
│   └── test_rules.py               # rule table in isolation: synthetic states → exact actions
├── commands/
│   ├── test_status.py              # NEW: fixture-driven command flow, facts + exact
│   │                               #   next_actions, cache regeneration, byte-identity
│   └── test_status_errors.py       # NEW: error envelopes, exit codes, degraded paths
├── io/…                            # MODIFIED: research record extension coverage
└── validation/test_factual_anchor.py  # MODIFIED: parity guards for extracted predicates
```

**Structure Decision**: single project (src-layout, Constitution III). The
command itself is one module (`commands/status.py`, Constitution IV); the
derived-state domain logic gets its own `src/bookwright/status/` subpackage —
mirroring how `validation/` separates reasoning from its CLI verb — so the
rule table is importable and unit-testable with zero CLI or graph coupling
(FR-008) and every file stays far from the 500-line ceiling. The graph-build
pipeline moves to `commands/_graph.py` (the established `_envelope.py` /
`_project.py` shared-helper naming) so `graph build` and `status` consume one
implementation (research.md D1).

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
