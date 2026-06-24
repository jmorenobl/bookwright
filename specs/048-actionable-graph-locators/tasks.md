---
description: "Task list for iteration 048 — Actionable locators for graph-consumer validators"
---

# Tasks: Actionable locators for graph-consumer validators

**Input**: Design documents from `/specs/048-actionable-graph-locators/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓ (D1 load-bearing),
data-model.md ✓, contracts/graph-consumer-locators.md ✓, quickstart.md ✓

**Tests**: REQUIRED for this iteration. FR-012 mandates empirical verification with
`uv run pytest`; research D4 names the oracles. Test tasks are therefore included,
not optional.

**Branch**: `048-actionable-graph-locators` (already created)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 = `factual_anchor`; US2 = `temporal`
- Each task names exact file paths.

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repo root (plan.md
Structure Decision). No new module, no new dependency (Constitution II).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working tree and the touched files' current state before any edit.

- [ ] T001 Confirm clean working tree on branch `048-actionable-graph-locators` and the four gates green at baseline: `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` (records the pre-change SC-005 finding set as the no-regression baseline).
- [ ] T002 Read the current line counts of the five source files to verify ≤ 500-line headroom (Principle IV / FR-008): `src/bookwright/validation/validators/temporal.py`, `src/bookwright/validation/validators/factual_anchor.py`, `src/bookwright/validation/base.py`, `src/bookwright/commands/status.py`, `src/bookwright/io/_research_identity.py`.

---

## Phase 2: Foundational (Contract-before-code — BLOCKS all code)

**Purpose**: The zero-debt doctrine (research D5, CLAUDE.md) reconciles the plain-text
contract **before** the code diverges. These are shared prerequisites for both user
stories and MUST land first.

**⚠️ CRITICAL**: No source/test edits in Phase 3+ begin until this phase is complete.

- [ ] T003 [P] Reconcile `bookwright-design.md` § 13.2 (`temporal` + `factual_anchor` rows) and § 20.6 (in Spanish — language convention): both graph-consumer validators now emit a resolvable `relpath[:line]` locator + readable identifier; record the D1 mechanism (in-process corpus, `AnchorIdentity.relpath`-resolved file, shared `anchor_handle`) and the file-vs-`:line` granularity that differs **by design** (event = `:line` via `E13`; anchor = file-only via `AnchorIdentity.relpath`).
- [ ] T004 [P] Remove the **DEBT-015** entry from `DEBT.md` (its class is resolved; git keeps the history — FR-011).
- [ ] T005 [P] Reconcile `CLAUDE.md`: flip the iteration table row 048 to ✅ / shipped-state and update the v0.5.x track-B milestone prose + index line referencing DEBT-015 → shipped iter 048 (FR-011).
- [ ] T006 [P] Add the one-line FR-010 note to `specs/048-actionable-graph-locators/spec.md`: the uuid7/`source=None` fallback is a **defensive floor** for an identity join-miss, not the normal path (research D1 reconciliation), so spec and code agree.

**Checkpoint**: Plain-text contract reconciled — code may now diverge from it.

---

## Phase 3: User Story 1 — A defective research anchor points to its file and authored name (Priority: P1) 🎯 MVP

**Goal**: Every `factual_anchor` violation carries `source = bible/research/<topic>.md`
(not `null`) and names the anchor by its authored handle (`promotes -> constrains`,
or `promotes` alone), identical to what `status` renders — through one shared code
path (FR-003/FR-004/FR-007/FR-009/FR-010).

**Independent Test**: Build a fixture with one under-reliable/unsourced anchor; assert
the `factual_anchor` violation's `source == "bible/research/<topic>.md"` (not `null`)
and its message cites the authored handle (not the uuid7 tail); cross-check that
`status` and `factual_anchor` name + locate the same anchor identically.

### Implementation for User Story 1

- [ ] T007 [US1] Add the shared free function `anchor_handle(promotes: str, constrains: str | None) -> str` to `src/bookwright/io/_research_identity.py` — returns `f"{promotes} -> {constrains}"` when `constrains is not None`, else `promotes` alone (pure, total, no I/O; D2 / data-model 2.1). Co-locate with `AnchorIdentity` / `is_timeline_ref`.
- [ ] T008 [US1] Refactor `_anchor_line` in `src/bookwright/commands/status.py` to call `anchor_handle(gap.promotes, gap.constrains)` instead of the inline format — output MUST be **byte-identical** to today (pure extraction; the single shared resolution point, FR-007).
- [ ] T009 [P] [US1] Add the memoized `anchor_corpus()` accessor to `ValidationContext` in `src/bookwright/validation/base.py`: returns `tuple[Indexer, tuple[AnchorIdentity, ...]]` from one in-process, **non-persisting** build — reuse the memoized `self.outline()` `MapResult`, index into a fresh `resolve_indexer(manifest.bookwright.indexer)()`, add `map_research(...)` triples, **no `engine.save`** (FR-020); `_anchor_corpus` slot with `_UNSET` sentinel + an optional injectable pre-set corpus (test seam, D1/D4 / data-model 2.2). Build from `io`/`indexers`/`golem` only — do **not** import `commands._graph` (keeps the layer direction; plan Complexity Tracking).
- [ ] T010 [US1] Rewrite anchor resolution in `src/bookwright/validation/validators/factual_anchor.py`: build `id_by_uri` from `context.anchor_corpus()`; per anchor, when the identity is found set `source = identity.relpath` and the message identifier = `anchor_handle(identity.promotes_id, identity.constrains)`; on a join miss keep the defensive floor `source = None` + `_label(anchor.uri)` (FR-010). Replace every `_label(anchor.uri)` in messages and the `resolve_source(indexer, anchor.uri)` in `_violation`/`_anachronism`; leave the *source* entity's `_label(source.uri)` stable slug unchanged. Preserve the inert path (`[]` with no corpus build when `[research]` disabled / no anchors). (FR-003/FR-004/FR-005/FR-010 / data-model 2.3)

### Tests for User Story 1

- [ ] T011 [US1] Extend `tests/validation/conftest.py`: add an `AnchorIdentity` builder for the hand-built `AnchorSpec` fixtures (matching the stable `anchor/aN` URIs) and the corpus-injection seam that supplies `(engine, identities)` to `ValidationContext` so existing fixtures keep their shape (D4 / plan Testing).
- [ ] T012 [US1] Update/extend `tests/validation/test_factual_anchor.py`: a defective anchor reports `source == "bible/research/<topic>.md"` (not `null`) and a message citing the authored handle (`promotes -> constrains`, and `promotes` alone when `constrains is None`), **never** the uuid7 tail; add the FR-010 identity-less anchor case asserting the finding still emits with `source = None` + uuid7 label (defensive floor).
- [ ] T013 [US1] Add the cross-surface agreement test (in `tests/validation/test_factual_anchor.py`, `-k agreement`): for the same anchor, the `factual_anchor` finding and the `status` `anchor_gaps` entry carry a **byte-identical** handle and the **same** file (SC-003 / FR-009).
- [ ] T014 [P] [US1] Add an E2E assertion to `tests/e2e/test_research_workflow.py`: after a real `graph build` → `validate --json` over the committed research fixture, the `factual_anchor` findings carry a non-`null` `bible/research/<topic>.md` `source` and a uuid7-free, handle-based message (proves the in-process corpus resolves across the build→validate process boundary — research D1 / SC-001/SC-004).
- [ ] T015 [US1] Confirm `tests/status/test_queries.py` `_anchor_line`/handle parity is unaffected by the T008 extraction (run it; byte-identical output guarantees no update needed — if it requires a change, the extraction was not pure).

**Checkpoint**: `factual_anchor` is fully actionable and agrees with `status`; US1 testable independently.

---

## Phase 4: User Story 2 — Every timeline contradiction points to the timeline file (Priority: P1)

**Goal**: `temporal` rules (a) cycle, (b) order-vs-overlap, (c) containment-vs-order
adopt rule (d)'s `resolve_source` over a deterministically-chosen implicated event, so
all four rules emit a resolvable `bible/timeline.md:<line>` `source` (not `null`) —
FR-001/FR-002.

**Independent Test**: A `bible/timeline.md` fixture triggering rules a, b and c; assert
each emitted `temporal` violation's `source` resolves to `bible/timeline.md` (not
`null`), matching rule (d); assert byte-stability across two builds.

### Implementation for User Story 2

- [ ] T016 [US2] In `src/bookwright/validation/validators/temporal.py`, set `source = resolve_source(indexer, <event>)` for rules a/b/c over the **passed** indexer (no rebuild): rule (b)/(c) resolve from the carried triple's **subject `a`** (mirror rule d); rule (a) resolves from `component[0]` — the lexicographically smallest event URI in the SCC. All four rules end uniform; rule (d) is unchanged (FR-001/FR-002 / data-model 2.4).

### Tests for User Story 2

- [ ] T017 [US2] Update/extend `tests/validation/test_temporal.py`: a fixture triggering rules a, b and c each reports a `source` resolving to `bible/timeline.md` (line-bearing `bible/timeline.md:<line>`, like rule d), not `null`; add a two-build assertion that the `source` is byte-identical across builds (FR-002 / SC-002 / C5).

**Checkpoint**: All four `temporal` rules emit a resolvable timeline locator; US2 testable independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Whole-iteration verification that nothing semantic moved and all gates pass.

- [ ] T018 Run quickstart.md Scenarios A–D (`tests/validation/test_temporal.py`, `tests/validation/test_factual_anchor.py`, `-k agreement`, `tests/e2e/test_research_workflow.py`) and confirm each expected outcome.
- [ ] T019 Verify SC-005 no-regression: the finding **count / severity / gate & exit-code** on every existing fixture is unchanged from the T001 baseline — only `source` and message identifiers differ.
- [ ] T020 Run the full gate green: `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` (≥ 80% coverage single-sourced; FR-012). Re-confirm all five touched source files are still ≤ 500 lines.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2, T003–T006)**: contract-before-code; BLOCKS all of Phase 3/4 (zero-debt doctrine D5). The four reconciliations are independent files → all `[P]`.
- **User Stories (Phase 3 US1, Phase 4 US2)**: both depend only on Phase 2. They touch **disjoint** source files, so US1 and US2 can proceed fully in parallel.
- **Polish (Phase 5)**: depends on US1 + US2 complete.

### User Story Dependencies

- **US1 (P1, MVP)** and **US2 (P1)** are independent halves (spec): no cross-story dependency. Either can ship alone.

### Within User Story 1

- T007 (`anchor_handle`) blocks T008 (`status` uses it) and T010 (`factual_anchor` uses it).
- T009 (`anchor_corpus()` accessor) blocks T010 (consumes it) and T011 (injection seam targets it). T009 is `[P]` with T007/T008 (different file).
- T010 blocks T012/T013/T014 (they assert its output).
- T011 (conftest seam) blocks T012/T013 (unit oracles use it).
- T013 (agreement) needs both T010 and T008.

### Within User Story 2

- T016 blocks T017.

### Parallel Opportunities

- Phase 2: T003, T004, T005, T006 all `[P]` (four distinct plain-text files).
- Across stories: the entire US2 (T016–T017) runs in parallel with US1 (T007–T015) — disjoint files (`temporal.py`/`test_temporal.py` vs. the rest).
- Within US1: T009 `[P]` with T007/T008; T014 `[P]` (E2E file) with the unit-test tasks.

---

## Parallel Example: Phase 2 + the two stories

```bash
# Phase 2 — reconcile all four plain-text contracts together:
Task T003: design § 13.2 / § 20.6 (bookwright-design.md)
Task T004: remove DEBT-015 (DEBT.md)
Task T005: CLAUDE.md table/index/prose
Task T006: spec.md FR-010 note

# After Phase 2 — the two independent halves run concurrently:
Developer/agent A: US1 (T007 → T008/T009 → T010 → T011 → T012/T013/T014/T015)
Developer/agent B: US2 (T016 → T017)
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational (contract reconciled).
2. Phase 3 US1 (`factual_anchor` actionable + agrees with `status`).
3. **STOP and VALIDATE**: Scenarios B & C green; SC-001/SC-003/SC-004 met. This is the larger half and the core DEBT-015 defect — shippable alone.

### Incremental Delivery

1. Setup + Foundational → contract ready.
2. US1 → the `null`+uuid7 worst case is gone (MVP).
3. US2 → the self-inconsistent `temporal` rules a/b/c now locate the timeline.
4. Polish → full gate + SC-005 no-regression.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task.
- Two halves touch disjoint files: US1 = `io/_research_identity.py`, `commands/status.py`, `validation/base.py`, `validators/factual_anchor.py` (+ unit/e2e/agreement tests); US2 = `validators/temporal.py` (+ `test_temporal.py`).
- No new module, no new dependency, no ontology change (FR-006/FR-008); every touched file stays ≤ 500 lines (Principle IV).
- The in-process corpus build **never** persists (`engine.save` not reused — FR-020); the frozen GOLEM ontology is untouched (Principle X).
- Commit per task or logical group; the auto-git hooks are advisory in this flow.
