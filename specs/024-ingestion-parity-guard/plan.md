# Implementation Plan: Ingestion-parity guard + deferral registry

**Branch**: `024-ingestion-parity-guard` | **Date**: 2026-06-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/024-ingestion-parity-guard/spec.md`

## Summary

Close the silent gap between *modelled* and *fed*. Introduce a static, unit-testable
**deferral registry** — a new module `src/bookwright/golem/deferrals.py` holding a
frozen `dict[str, DeferralNote]` (concept name → reason + target version) with exactly
the seven orphan concepts. Add a deterministic **ingestion-parity test** in
`tests/golem/` that builds the GOLEM graph from a fixture exercising *every* current
authored-text ingestion path, collects the concept-level `rdf:type` IRIs that actually
appear (drawn from `CLASS_IRI`, scoped to `CONCEPTS`), derives the real orphan set, and
asserts it equals exactly the registry's key set. Document, with no behavioral change,
that `outline/` and `manuscript/` are author-only in v0.3 (manuscript-reader docstring
extended to `outline/`, plus a Spanish docs line). No orphan concept is wired here.

**Technical approach** (grounded in the codebase):

- The "alive" set is derived from a real build via `build_project_graph(root, manifest)`
  ([_graph.py:75](../../src/bookwright/commands/_graph.py#L75)), whose returned
  `BuildOutcome.engine` is the `RdflibIndexer` already holding the full graph —
  **including the reified `crm:E13_Attribute_Assignment` provenance carrier**, which is
  emitted during indexing, not by `map_bible` alone. Querying that engine for
  `SELECT DISTINCT ?t WHERE { ?s a ?t }` and intersecting with `CLASS_IRI.values()`
  (then mapping back to `CONCEPTS` names) is the faithful, deterministic liveness probe.
- **No existing committed fixture exercises the `bible/relationships.md` →
  `SocialRelationship` path** (neither `tiny-novel` nor `tiny-historical` ships a
  `relationships.md`). A new, minimal, single-purpose fixture
  `tests/fixtures/parity-exercise/` is added that drives exactly the six reachable paths
  (one character with `narrative_roles` + `born`/`features`, one setting, one
  `timeline.md` event, one `relationships.md` relationship). See research D1 for why a
  dedicated fixture beats extending `tiny-historical` (which is the oracle-pinned 023
  orchestration corpus).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `rdflib` (graph + SPARQL), `pydantic` v2 (GOLEM entities),
`typer`/`tomlkit` (manifest load) — all already locked; **no new dependency**.

**Storage**: Plain-text fixture (`bible/*.md`) → derived `bible/graph.ttl` cache
(reconstructible, Constitution I). The deferral registry is in-code static data, no I/O.

**Testing**: `pytest` in-process; the new `tests/golem/test_ingestion_parity.py`
builds the graph via `build_project_graph` and queries the `RdflibIndexer` engine.

**Target Platform**: CLI library (cross-platform); tests run in CI on Linux/macOS.

**Project Type**: Single project (src-layout, Constitution III).

**Performance Goals**: N/A — one small fixture build per test run.

**Constraints**: Behavior-neutral (no new ingestion, no CLI surface, no `--json`
envelope, no class/property added to the frozen closure). Deterministic verdict
(pure function of fixture corpus + registry). `mypy --strict` clean.

**Scale/Scope**: 1 new source module (the registry), 1 new test module, 1 new minimal
fixture, 2 doc edits (1 code docstring + 1 Spanish docs line). `CONCEPTS` = 13 keys;
deferral registry = 7 entries; reachable set = 6.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Notes |
|---|---|---|
| I — Plain Text as Source of Truth (NON-NEGOTIABLE) | ✅ PASS | The fixture is plain-text bible; the graph stays a derived cache. The registry is static code, not narrative state. |
| II — Modern Python Stack | ✅ PASS | No new dependency; `rdflib`/`pydantic` already locked. |
| III — src-layout | ✅ PASS | New module under `src/bookwright/golem/`; test under `tests/golem/`; fixture under `tests/fixtures/`. |
| IV — Modular Command Surface (≤500 lines, 1 subcommand/module) | ✅ PASS | `deferrals.py` is a tiny data module; no CLI subcommand added. |
| V — Plugin-Based Integrations | ✅ PASS | Untouched. |
| VI — Agent Skills Only (NON-NEGOTIABLE) | ✅ PASS | No skill added/changed; no `commands/` dir written. |
| VII — agentskills.io compliance | ✅ PASS | No skill touched. |
| VIII — Test Discipline, ≥80% coverage (NON-NEGOTIABLE) | ✅ PASS | The registry module is fully exercised by the parity test plus drift-simulation unit tests; coverage gate single-sourced in `pyproject`. |
| IX — JSON-over-stdout CLI Contract | ✅ PASS | No agent-consumed subcommand added; nothing emits JSON. |
| X — Design Document Axioms / frozen ontology | ✅ PASS | `CLASS_IRI`, `CONCEPTS`, `golem.ttl` unchanged; no class/property added to the closure. The registry references existing `CONCEPTS` keys only. |
| Scope & Release Discipline | ✅ PASS | Guard-only: no orphan wired, no "future X" plumbing. Ships as patch `v0.3.1` with one observable delta (the enforced contract + written note). |

**Result: PASS, no violations — Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/024-ingestion-parity-guard/
├── plan.md              # This file
├── research.md          # Phase 0 — the 5 design decisions
├── data-model.md        # Phase 1 — DeferralNote + registry shape, the partition invariant
├── quickstart.md        # Phase 1 — how to run the guard and simulate each drift
├── contracts/
│   └── parity-contract.md   # The registry shape + the parity assertion contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/golem/
├── __init__.py          # CONCEPTS lives here (UNCHANGED)
├── namespaces.py        # CLASS_IRI lives here (UNCHANGED)
└── deferrals.py         # NEW — DeferralNote + DEFERRED_CONCEPTS static registry

src/bookwright/io/
└── manuscript.py        # EDIT — docstring note extended to outline/ (author-only v0.3)

docs/
└── authoring.md         # EDIT — one Spanish line: outline/ + manuscript/ author-only in v0.3

tests/golem/
└── test_ingestion_parity.py   # NEW — the parity guard + drift-simulation unit tests

tests/fixtures/parity-exercise/
└── bible/
    ├── constitution.md
    ├── timeline.md          # one NarrativeEvent
    ├── relationships.md     # one SocialRelationship (the path no other fixture exercises)
    ├── characters/
    │   └── <one>.md         # narrative_roles + born/features → Character, NarrativeRole, CharacterFeature
    └── settings/
        └── <one>.md         # one Setting
```

**Structure Decision**: Single project, src-layout. The registry is co-located with
`CONCEPTS`/`CLASS_IRI` inside `golem/` (per the user hint: "su propio módulo, junto a
`golem/__init__.py`"), satisfying "no toques `golem/` salvo el registro nuevo." The
parity test lives in `tests/golem/` beside the closure test (`test_frozen_ontology.py`,
`test_namespaces.py`) it complements. The exercise corpus is a new, minimal fixture
(research D1) rather than a perturbation of the oracle-pinned `tiny-historical`.

## Complexity Tracking

> No Constitution violations — section intentionally empty.
