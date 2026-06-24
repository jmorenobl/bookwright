# Implementation Plan: Actionable locators for graph-consumer validators

**Branch**: `048-actionable-graph-locators` | **Date**: 2026-06-24 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `specs/048-actionable-graph-locators/spec.md`

## Summary

The two **graph-consumer** validators emit unactionable findings while the prose
validators always emit `relpath:line` + a readable handle. This iteration closes
that gap (DEBT-015), in two independent halves:

- **`temporal` (the mechanical half).** Rules **(a)** cycle, **(b)**
  order-vs-overlap and **(c)** containment-vs-order emit `source=None`; only rule
  **(d)** numeric resolves `source=resolve_source(indexer, <event>)`. Events are
  `SluggedEntity` (stable URIs) with reified `E13` provenance already in the graph
  the runner hands the validator, so a/b/c just adopt rule (d)'s resolution over a
  **deterministically-chosen** implicated event. No rebuild, no new machinery.

- **`factual_anchor` (the larger half).** Every violation today sets
  `source = resolve_source(indexer, anchor.uri)`, which is **always `None`** (an
  anchor *is* the reified `E13`; no `E13` points *to* it), and names the anchor by
  `_label(anchor.uri)` — the opaque uuid7 tail. `status` already reports the same
  anchor legibly by joining each graph anchor to its `AnchorIdentity`
  (`promotes_id` / `constrains` / `relpath`). The fix resolves `source` to the
  anchor's `bible/research/<topic>.md` via that identity and names it by the
  authored handle (`promotes -> constrains`), through a **single shared resolution
  point** with `status` so the two surfaces can never diverge (FR-007/FR-009).

**Load-bearing design decision (see `research.md` D1).** The spec's literal
mechanism — "join the authored identities to the graph anchors *by URI*, the same
path `status` uses" — does **not** survive the `graph build` → `validate` process
boundary: anchors are `MintedEntity` (uuid7, **re-minted every build**), and
`validate` reads the *persisted* `graph.ttl` from a prior build, so a fresh
`map_research` mints **different** uuid7s and a URI-keyed join would miss for
*every* anchor (not just the FR-010 "stale graph" edge case). `status` only works
because it **rebuilds the graph in-process** (`build_project_graph`) and joins
within one process where the uuid7s match. The faithful, lowest-debt realization
of FR-003/FR-007 ("the same machinery `status` uses") is therefore: **resolve the
anchor sub-graph from an in-process-built research corpus** — a memoized,
non-persisting `ValidationContext` accessor returning `(engine, anchor_identities)`
from one `map_research` — and join by URI within that single build. This honors
every functional requirement with **no graph-emission / ontology change**; FR-010's
join-miss fallback becomes a defensive floor (documented reconciliation in
`research.md` D1, and a one-line note added to the spec).

Nothing semantic changes: the same `error`/`warning` findings, the same gate and
exit code (SC-005). On every fixture (`graph build` then `validate` over one
source) the in-process build is byte-equal in *content* to the persisted graph, so
the finding set is unchanged — only `source` and the message identifier differ.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II) — `from __future__ import
annotations` throughout.

**Primary Dependencies**: stdlib + the locked runtime set only. `rdflib` is used
**only** through the existing `Indexer` seam / `validation.queries` projections;
**no new dependency** (FR-006, Constitution II).

**Storage**: the derived graph (`bible/graph.ttl`) is read by `validate`; the
new in-process corpus build is **non-persisting** — a validator MUST NOT write to
disk (`Validator` protocol, FR-013). `build_project_graph`'s `engine.save(...)` is
**not** reused; the accessor indexes into a fresh in-memory engine and never saves.

**Testing**: `uv run pytest` (≥ 80% coverage, single-sourced `fail_under`). New
oracles in `tests/validation/test_temporal.py`, `tests/validation/test_factual_anchor.py`,
a cross-surface agreement test (factual_anchor ⇆ status), and an E2E assertion in
`tests/e2e/test_research_workflow.py`. The factual_anchor unit harness
(`tests/validation/conftest.py`) gains a small **injection seam**: tests inject a
pre-built `(engine, identities)` corpus into the `ValidationContext` so the existing
hand-built `AnchorSpec` graphs keep working (production builds the corpus instead).

**Target Platform**: CLI (`bookwright validate`, `bookwright status`), offline.

**Project Type**: single project (src-layout `src/bookwright/`).

**Performance Goals**: `factual_anchor` stays **inert** (returns `[]` with no build)
on a non-research project (`[research].enabled = false` or no anchors), so a
project with nothing to audit pays nothing (Edge Cases, SC). On a research project
the in-process corpus build is the same cost `status` already pays once per run.

**Constraints**: every changed source file ≤ 500 lines (Principle IV — current
sizes: `temporal.py` 277, `factual_anchor.py` 325, `base.py` 355,
`status.py` 251, `_research_identity.py` 72 — all with headroom). Frozen GOLEM
ontology untouched (Principle X / FR-008): **no** new class, predicate, or `.ttl`
change. Deterministic output (FR-002): byte-identical `source` across two
builds of the same fixture.

**Scale/Scope**: ~5 source files touched (`temporal.py`, `factual_anchor.py`,
`validation/base.py` `ValidationContext`, `io/_research_identity.py` shared helper,
`commands/status.py` `_anchor_line`), plus `bookwright-design.md` § 13 / § 20.6,
`DEBT.md`, the iteration index, and tests. No new module, no new dependency.

## Constitution Check

*GATE: re-checked after Phase 1 design — still PASS.*

| Principle | Verdict | Why |
|---|---|---|
| I — Plain-text source of truth | ✅ | The graph stays a derived cache; the in-process corpus is rebuilt from plain text, never persisted. DEBT-015 closure recorded in `DEBT.md` (removed) + the iteration index. |
| II — Locked stack | ✅ | No new dependency; stdlib + `rdflib` via the existing seam only (FR-006). |
| III — Test discipline ≥ 80% | ✅ | New/updated oracles for both validators + a cross-surface agreement test; coverage threshold single-sourced, untouched. |
| IV — ≤ 500 lines / one subcommand per module | ✅ | All touched files keep headroom; no module split needed. |
| V / VI / VII — integrations / skills | ✅ | Not touched (no integration, no skill change). |
| VIII — Test discipline | ✅ | Empirical `uv run pytest` + four gates; no faked findings. |
| IX — JSON-over-stdout envelope | ✅ | `Violation.to_json()` shape is unchanged; only `source`/`message` *values* change. No new key. |
| X — Frozen ontology | ✅ | **No** ontology change. The in-process build emits the *same* triples `graph build` already emits (no new class/predicate); resolution is a pure read. |

**Initial Constitution Check**: PASS. **Post-Design Constitution Check**: PASS
(see Complexity Tracking for the one justified deviation — the in-process rebuild).

## Project Structure

### Documentation (this feature)

```text
specs/048-actionable-graph-locators/
├── plan.md              # This file
├── research.md          # Phase 0 — the design decisions (D1 is load-bearing)
├── data-model.md        # Phase 1 — the touched in-memory shapes
├── quickstart.md        # Phase 1 — runnable validation scenarios
├── contracts/
│   └── graph-consumer-locators.md   # the locator/handle contract both validators honor
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── validation/
│   ├── base.py                      # ValidationContext: + anchor_corpus() accessor (memoized, injectable)
│   ├── queries.py                   # resolve_source — REUSED as-is (FR-006); no change
│   └── validators/
│       ├── temporal.py              # rules a/b/c: source=resolve_source(indexer, <deterministic event>)
│       └── factual_anchor.py        # resolve via anchor_corpus() + anchor_handle(); FR-010 fallback
├── io/
│   └── _research_identity.py        # + anchor_handle(promotes, constrains) shared helper
└── commands/
    └── status.py                    # _anchor_line uses the shared anchor_handle() (single source)

tests/
├── validation/
│   ├── conftest.py                  # + AnchorIdentity builder + corpus-injection seam
│   ├── test_temporal.py             # a/b/c source + two-build byte-stability oracles
│   └── test_factual_anchor.py       # source=relpath + handle (no uuid7) oracles
├── status/test_queries.py           # _anchor_line/handle parity unaffected (shared helper)
└── e2e/test_research_workflow.py    # validate emits resolvable source + readable handle
```

**Structure Decision**: single project, no new module. The one new seam is a
memoized `ValidationContext.anchor_corpus()` accessor (mirroring the existing
`bible()` / `outline()` accessors), and one new free function `anchor_handle()` in
the lowest layer that already owns `AnchorIdentity` (`io/_research_identity.py`), so
both `status` and `factual_anchor` import the *same* handle spelling.

## Complexity Tracking

> One justified deviation from the spec's *literal* mechanism (it is impossible as
> written — see `research.md` D1).

| Decision | Why needed | Simpler alternative rejected because |
|---|---|---|
| `factual_anchor` resolves over an **in-process-built** research corpus (engine + identities from one `map_research`) instead of a URI-join against the runner's disk graph | Anchors are uuid7 (`MintedEntity`), re-minted every build; `validate` reads the *persisted* graph from a prior build, so a fresh `map_research`'s identities can **never** URI-join the disk graph's anchors. Mirroring `status`'s in-process build is the only way "the same machinery `status` uses" (FR-007/Assumption) actually resolves. | (a) *URI-join against the disk graph* — the spec's literal text — resolves **nothing** (every anchor misses → FR-010 fallback always). (b) *Emit anchor `E13` provenance + finding-id label at build* (a graph-emission "root fix") — contradicts FR-003 ("**not** by `resolve_source(anchor.uri)`") and the "anchor has no `E13`" premise, and changes build output. (c) *Stable-signature join* (constrains + source slugs + span) — uniqueness not guaranteed → fragile, real debt. |
| `ValidationContext.anchor_corpus()` builds the corpus from `io` directly (reusing the memoized `outline()` `MapResult` + `map_research`), not via `commands._graph.build_project_graph` | `build_project_graph` **persists** (`engine.save`) — forbidden in a validator — and lives in the `commands` layer (would invert layering: `validation` → `commands`). Building from `io`/`indexers`/`golem` keeps the dependency direction and mirrors the existing `outline()` precedent (its docstring already notes it reconstructs the pipeline). | Importing `commands._graph` from `validation` inverts the layer graph and would persist `graph.ttl` as a side effect of validation. Reusing `outline()`'s already-memoized `MapResult` avoids a second bible map. |

All other work is non-deviating: `temporal` a/b/c adopt rule (d)'s existing
`resolve_source` call; the shared `anchor_handle()` helper de-duplicates the handle
spelling `status` already renders.
