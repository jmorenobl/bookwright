# Implementation Plan: `factual_anchor` Validator

**Branch**: `014-factual-anchor-validator` | **Date**: 2026-06-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-factual-anchor-validator/spec.md`

## Summary

Add a fifth built-in deterministic validator, `factual_anchor`, that audits the
**structural integrity** of research anchors over the already-built graph and flags
**hard anachronisms** between an anchor's time-span and the interval of the event it
constrains. It conforms to the existing `Validator` Protocol, is auto-discovered by
the registry, obeys `[validators]` selection, and is inert when `[research].enabled
= false` or when there are no anchors — paying nothing on non-research projects.

Two severity tiers, exactly as the spec and design § 13.2 / § 20.6 mandate:

- **warnings** — structural defects: unsourced anchor (FR-006), source missing a
  mandatory provenance facet (one warning per facet, FR-007), best supporting
  reliability below `[research].min_reliability_for_anchor` (FR-008), promoted
  finding or constrained narrative entity missing from the graph (FR-009).
- **errors** — a chronological clash between an anchor's time-span and the interval
  of the event (or the timeline) it constrains (FR-010).

The single most important engineering decision (and the one the "zero technical
debt" directive turns on) is **FR-011**: the anachronism check MUST reuse the
`temporal` validator's interval reasoning, not re-implement it. The plan extracts
one pure predicate — `intervals_disjoint` — into the shared `queries` module,
rewires `temporal`'s overlap-disjoint branch to call it, and has `factual_anchor`
call the *same* function. There is then exactly one place in the codebase that
decides "two year ranges provably do not overlap," and the existing `temporal`
test suite pins its behaviour so the extraction is provably behaviour-preserving.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II/§ Technical Constraints).

**Primary Dependencies**: `rdflib` (graph + SPARQL through the `Indexer` seam),
`pydantic` v2 (the `[research]` manifest block already modelled). No new runtime
dependency — a new dependency would require a constitutional amendment (Principle
II); none is needed.

**Storage**: none. The validator is a pure read-only graph consumer (FR-003): it
reads `bible/graph.ttl` through `indexer.query(...)` and the manifest through the
`ValidationContext`. It writes nothing, fetches nothing, invokes no LLM.

**Testing**: `pytest` with the existing `tests/validation/` harness
(`conftest.py`). Per-violation-kind unit tests plus inert/no-research cases
(SC-006). Coverage gate ≥ 80 % single-sourced in `[tool.coverage.report]`.

**Target Platform**: cross-platform CLI (the `bookwright validate` subcommand).

**Project Type**: single project, src-layout (`src/bookwright/`, `tests/`).

**Performance Goals**: not a hotspot. One graph load already amortised across all
validators; `factual_anchor` issues a small fixed set of SPARQL projections
(anchors, their findings' sources, source facets, event intervals) — linear in the
number of anchors/sources, no combinatorial blow-up. No new performance budget.

**Constraints**: deterministic and side-effect-free (FR-003, Principle IX-adjacent
validator contract); every new source file ≤ 500 lines (Principle IV); adds **no**
GOLEM ontology class (Constitution X) — it only reads the `bw:` / CIDOC triples
iterations 012–013 already emit. Output ordering is byte-stable (the runner's
explicit total-order sort already guarantees this for any `Violation` set).

**Scale/Scope**: one new validator module, one new graph-projection module, one
small shared predicate added to `queries.py`, one three-line refactor of
`temporal.py`. No CLI surface change, no manifest schema change, no new vocabulary.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ PASS | Reads the derived `graph.ttl` cache + the TOML manifest; writes nothing. The graph stays a derived cache, never a source. |
| II. Modern Python stack | ✅ PASS | No new runtime dependency. `rdflib` / `pydantic` only. |
| III. src-layout | ✅ PASS | New code under `src/bookwright/validation/`; tests under `tests/validation/`. |
| IV. Modular command surface | ✅ PASS | No new CLI subcommand. New files split by concern, each well under 500 lines; `queries.py` grows by ~2 small functions and stays < 220 lines. |
| V. Plugin-based integrations | ✅ N/A | No integration change. |
| VI. Agent Skills only | ✅ N/A | No skill emitted. |
| VII. agentskills.io compliance | ✅ N/A | No skill emitted. |
| VIII. Test discipline (≥ 80 %) | ✅ PASS | Unit suite covers each violation kind + clean + inert + no-research (SC-006); coverage gate unchanged and single-sourced. |
| IX. JSON-over-stdout | ✅ PASS | The validator only returns `Violation`s; the existing `validate --json` path serializes them — output contract untouched (FR-005). |
| X. Design-document axioms | ✅ PASS | No GOLEM class added; no axiom reopened. Reads existing `bw:`/CIDOC vocabulary only. |
| Scope & release discipline | ✅ PASS | This is the M4/v0.2 `factual_anchor` iteration (design § 20.6). It deliberately does **not** build the `bookwright-verify` LLM check, any auto-fix, or vector search (FR-017, Assumptions). No "future X" plumbing. |

**Result: PASS — no violations, Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/014-factual-anchor-validator/
├── plan.md              # This file
├── research.md          # Phase 0 — design decisions (D1..D9)
├── data-model.md        # Phase 1 — in-memory projections + violation kinds
├── quickstart.md        # Phase 1 — how to exercise the validator end-to-end
├── contracts/
│   └── factual-anchor-validator.md   # The validator's behavioural contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/validation/
├── base.py                     # (unchanged) Validator Protocol, Violation, Severity, ValidationContext
├── queries.py                  # EDIT: + intervals_disjoint(), + load_timeline_bounds(),
│                               #        export parse_gyear (was _parse_year); docstring widened
├── anchor_queries.py           # NEW: anchor/finding/source graph projections
│                               #      (AnchorRecord, load_anchors, source-facet + reliability reads)
├── registry.py                 # (unchanged) auto-discovers the new module — no edit needed
├── runner.py                   # (unchanged) total-order sort already covers the new Violations
└── validators/
    ├── temporal.py             # EDIT: overlap-disjoint branch now calls intervals_disjoint()
    └── factual_anchor.py       # NEW: the FactualAnchor validator + its rule methods

tests/validation/
├── conftest.py                 # EDIT: add a research-aware graph builder helper
├── test_temporal.py            # (unchanged) pins the behaviour the refactor must preserve
├── test_queries.py             # NEW (or extend): unit-test intervals_disjoint + load_timeline_bounds
└── test_factual_anchor.py      # NEW: one test per violation kind + clean/inert/no-research
```

**Structure Decision**: single project, src-layout. The validator follows the
exact shape of the four shipped validators (`temporal`, `character_presence`,
`setting_continuity`, `focalization`): a class with `name`/`severity_default`
class vars and a `validate(project, indexer)` method, dropped into
`validation/validators/` where `registry._discover_builtins()` finds it by
iterating the package — **no hand-registration** (FR-004). Graph SPARQL lives in a
sibling projection module (`anchor_queries.py`), mirroring how `temporal` keeps its
SPARQL in `queries.py`, so the validator body stays pure reasoning over plain
in-memory shapes and is trivially unit-testable.

## Phase 0 — Research

See [research.md](research.md). All spec ambiguities were already closed in the
spec's Clarifications session; Phase 0 records the **design decisions** that turn
the requirements into code, the most load-bearing being D1 (the shared
`intervals_disjoint` extraction for FR-011) and D2 (reading the anchor time-span,
whose graph shape — `crm:E52_Time-Span` + `P82a`/`P82b` — differs from an event's
boundary shape, so it is read into the *same* `EventInterval` model rather than
reusing `load_intervals` verbatim).

## Phase 1 — Design & Contracts

- [data-model.md](data-model.md) — `AnchorRecord`, the reused `EventInterval`,
  `SourceFacets`, the reliability ordering, and the five violation kinds with their
  severity, message template, and `source`/`triples` payload.
- [contracts/factual-anchor-validator.md](contracts/factual-anchor-validator.md) —
  the validator's behavioural contract: discovery, the inert preconditions, each
  rule's trigger and output, and the `intervals_disjoint` signature both validators
  share.
- [quickstart.md](quickstart.md) — build a graph with one malformed anchor of each
  kind and one clean anchor, run `bookwright validate`, observe the findings.

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.
