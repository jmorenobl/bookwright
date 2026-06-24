---
description: "Task list for iteration 049 — unify the narrative-unit identifier"
---

# Tasks: Unify the narrative-unit identifier across `narrative_structure`'s two rules

**Input**: Design documents from `/specs/049-narrative-unit-identifier/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/narrative-unit-identifier.md, quickstart.md

**Tests**: Test work is IN SCOPE here — not as new TDD scaffolding, but because the
feature is defined by its observable message contract. FR-008 mandates flipping the
slug→name oracles, and FR-004/C4 mandates a new defensive missing-label test. These
are the deliverable's proof, so they appear as first-class tasks.

**Organization**: One user story (P1). All work serves it; there is no second story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: `[US1]` for the single user-story phase; Setup/Polish carry no label
- Exact file paths are given in every task

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repo root (per plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a green baseline and ground the exact edit sites before
changing behavior.

- [ ] T001 Confirm a clean green baseline on branch `049-narrative-unit-identifier`: run `uv run pytest tests/validation/test_narrative_structure.py tests/e2e/test_narrative_workflow.py` and record that they pass BEFORE any edit (so SC-003's "only the printed identifier differs" is provable as a delta).
- [ ] T002 Re-confirm the two edit sites and their invariants by reading `src/bookwright/validation/queries.py:179` (`load_orphan_units`, currently `-> list[str]`) and `src/bookwright/validation/validators/narrative_structure.py:42` (`_orphan_beats`, slug at line 46) and `:60` (`_unresolved_roles`, `ref.entity` at line 90); verify by grep that `_orphan_beats` is the SOLE caller of `load_orphan_units` across `src/` and `tests/` (D2).

**Checkpoint**: Baseline green, edit sites and sole-caller assumption verified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The projection change that the user-story rendering depends on. This is
the one cross-task prerequisite: `_orphan_beats` cannot render the human name until
the query supplies it.

**⚠️ CRITICAL**: T003 blocks the orphan-beat rendering task (T006).

- [ ] T003 In `src/bookwright/validation/queries.py`, widen `load_orphan_units` from `-> list[str]` to `-> list[tuple[str, str | None]]`: add `OPTIONAL { ?unit rdfs:label ?label }` to the SPARQL, `SELECT ?unit ?label`, and return `(unit_uri, label_or_None)` pairs sorted by URI with the lexicographically smallest label per URI (determinism, D2). Empty graph still returns `[]` (rule stays inert — detection unchanged, FR-006). Update the `"load_orphan_units"` export/docstring if it states the old return shape.

**Checkpoint**: Query returns `(uri, label)` pairs and type-checks; no caller updated yet (next phase).

---

## Phase 3: User Story 1 - One species of unit identifier, not two (Priority: P1) 🎯 MVP

**Goal**: Both `narrative_structure` rules name a `G9` narrative unit by its human
authored name, alone, through one shared formatting point — so the report reads as
one consistent surface (DEBT-017 closed).

**Independent Test**: Run `bookwright validate` (or the unit + E2E suites) on the
`tiny-quest` fixture that triggers both the orphan-beat and unresolved-role rules;
confirm both messages identify the unit by the same human authored name, and that
finding count, severity, `relpath:line`, and the gate outcome are unchanged.

### Implementation for User Story 1

- [ ] T004 [US1] In `src/bookwright/validation/validators/narrative_structure.py`, add the module-level pure helper `_unit_identifier(name: str | None, slug: str) -> str` returning `name if name else slug` (D3/D4 — empty-string label treated as missing); this is the SINGLE shared formatting point (FR-005/SC-006). No call site wired yet.
- [ ] T005 [US1] Wire `_unresolved_roles` (`narrative_structure.py:60`) to render its identifier through the new helper: replace the inline `'{ref.entity}'` in the message (line 90) with `_unit_identifier(ref.entity, <slug from unit_uri>)`, deriving `slug = unit_uri.rsplit("/", 1)[-1]`. Output MUST stay byte-identical to today (`ref.entity` is always present → helper returns it; FR-002/C2).
- [ ] T006 [US1] Wire `_orphan_beats` (`narrative_structure.py:42`) to the widened query (T003): iterate `(unit_uri, label)` pairs, derive `slug = unit_uri.rsplit("/", 1)[-1]` (line 46), and render the message identifier as `_unit_identifier(label, slug)` — human name in the normal path, slug fallback when `label` is falsy (FR-002/FR-003/FR-004/C1/C4). The `resolve_source`/`relpath:line` locator and `warning` severity stay exactly as they are (FR-006/C5).

**Checkpoint**: Both rules emit the unit identifier through one helper; orphan-beat now prints the human name, unresolved-role unchanged. User Story 1 is functionally complete — verify next via oracles.

---

## Phase 4: Oracle & test reconciliation (the C1–C5 proof)

**Purpose**: Flip exactly the orphan-beat message oracles from slug→name, pin the
FR-004 floor, and confirm everything else is invariant — all verified empirically
(FR-008). Which oracles actually move is decided by `uv run pytest`, not assumed (D5).

- [ ] T007 [P] [US1] In `tests/validation/test_narrative_structure.py`, update `test_orphan_beat_flagged_sequenced_not` (~line 51): assert the human name `"Orphan Beat"` is in the message (was the `orphan-beat` slug). Leave line 55's negative `"anchored-beat" not in` assertion unchanged (C1).
- [ ] T008 [P] [US1] In `tests/fixtures/tiny-quest/expected-narrative.md` (~line 70), change `orphan_beats[0].unit: omen-beat` → `unit: "Omen Beat"` (the human name) and update the trailing comment "the unit slug, as it appears in the message" → "the unit's human name". The E2E `test_validate_reports_the_orphan_beat` rides this oracle (C1). Do NOT edit the authored outline card `tests/fixtures/tiny-quest/outline/units/06-omen.md` (FR-008).
- [ ] T009 [US1] Add a NEW unit test to `tests/validation/test_narrative_structure.py` pinning FR-004/C4: an orphan unit with no `rdfs:label` (or empty label) falls back to its slug in the message — exercised either by a `G9` type triple without a label, or by asserting `_unit_identifier(None, slug) == slug` and `_unit_identifier("", slug) == slug` directly.
- [ ] T010 [US1] Run `uv run pytest tests/validation/test_narrative_structure.py tests/e2e/test_narrative_workflow.py` and reconcile any OTHER moved oracle empirically (FR-008/D5). Confirm the unresolved-role assertions (`test_unresolved_role_flagged_with_location`, E2E `test_validate_reports_the_unresolved_role`) and the invariance assertions (`test_deterministic_and_read_only`, finding-count/source tests) still pass unchanged (C2/C5/SC-003).

**Checkpoint**: Unit + E2E suites green; orphan-beat oracle is the human name; FR-004 floor pinned; invariants confirmed.

---

## Phase 5: Plain-text reconciliation (debt / design / index closure)

**Purpose**: Record DEBT-017 closure in plain text (FR-009/SC-005) and reconcile the
contract-before-code design note. Per the iteration prompt this is CONTRACT-BEFORE-CODE
for § 13; if not already done, it is reconciled here alongside the debt/index.

- [ ] T011 [P] Remove the `### DEBT-017` entry from `DEBT.md` (~line 91) and reconcile the reference at line 75 so no plain-text record still describes DEBT-017 as open (FR-009/SC-005). Git preserves the history.
- [ ] T012 [P] Reconcile `bookwright-design.md § 13` so it states that BOTH `narrative_structure` rules name the unit by its human authored name (the contract this iteration ships). Keep the edit in Spanish (language convention).
- [ ] T013 [P] In `CLAUDE.md`, reconcile the issue #1 track-B closed-list line + milestone prose to record DEBT-017 closed, and add the iteration-049 row to the iterations table.

**Checkpoint**: No plain-text record describes DEBT-017 as open; design § 13 and the index reflect the unified identifier.

---

## Phase 6: Polish & Cross-Cutting Concerns (gate sweep)

**Purpose**: Prove SC-004 and the full quickstart.

- [ ] T014 Run the full gate sweep — `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict` (confirm `load_orphan_units`'s widened `list[tuple[str, str | None]]` type-checks), and `uv run pytest` (≥80% coverage) — all green (SC-004).
- [ ] T015 Walk `specs/049-narrative-unit-identifier/quickstart.md` Scenarios 1–3 and confirm the "Done when" checklist: both rules print the human name alone identically (SC-001/SC-002), invariants hold (SC-003), one helper / two call sites (SC-006), DEBT-017 gone (SC-005), gates green (SC-004).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2, T003)**: Depends on Setup. BLOCKS the orphan-beat rendering (T006).
- **User Story 1 (Phase 3)**: T004 (helper) depends only on Setup; T005 depends on T004; T006 depends on T003 + T004.
- **Oracles (Phase 4)**: Depend on the Phase 3 rendering being in place (T005/T006).
- **Plain-text reconciliation (Phase 5)**: Independent of code; can proceed any time after Setup (all three tasks touch distinct files → parallel).
- **Polish (Phase 6)**: Depends on all prior phases — it is the final green gate.

### Within User Story 1

- T004 (helper) before T005 and T006 (both call it).
- T003 (query) before T006 (orphan rule consumes the widened pairs).
- T005 and T006 touch the same file (`narrative_structure.py`) → NOT parallel with each other or with T004.
- Oracle tasks T007 and T008 touch different files → parallel; T009 shares the test file with T007 (sequence after T007); T010 is the empirical gate after all oracle edits.

### Parallel Opportunities

- **T007 ∥ T008**: different oracle files (`test_narrative_structure.py` vs `expected-narrative.md`).
- **T011 ∥ T012 ∥ T013**: `DEBT.md`, `bookwright-design.md`, `CLAUDE.md` — three distinct plain-text files, no shared lines.
- The Phase 5 reconciliation block can run in parallel with the Phase 3/4 code+oracle work (no file overlap).

---

## Parallel Example: oracle + plain-text reconciliation

```bash
# Oracle edits on distinct files (after T005/T006 land):
Task: "T007 Update orphan-beat oracle in tests/validation/test_narrative_structure.py"
Task: "T008 Update unit value in tests/fixtures/tiny-quest/expected-narrative.md"

# Plain-text closure on three distinct files (any time after Setup):
Task: "T011 Remove DEBT-017 from DEBT.md"
Task: "T012 Reconcile bookwright-design.md § 13"
Task: "T013 Add iteration-049 row + track-B prose in CLAUDE.md"
```

---

## Implementation Strategy

### MVP (User Story 1 — the whole feature)

1. Phase 1: Setup — green baseline + verify edit sites/sole caller.
2. Phase 2: Foundational — widen `load_orphan_units` (T003).
3. Phase 3: helper + wire both rules (T004→T005→T006).
4. Phase 4: flip oracles, pin FR-004 floor, prove invariants (T007–T010).
5. **STOP and VALIDATE**: both rules name the unit by the human name, identically; counts/severity/locator/gate unchanged.
6. Phase 5–6: close the plain-text debt/design/index, run the four gates.

There is one user story; the MVP is the complete deliverable.

---

## Notes

- [P] = different files, no dependency on incomplete tasks.
- This iteration ships ONE observable delta: the orphan-beat rule's printed identifier (slug → human name). The unresolved-role rule's text is byte-identical (FR-002).
- Consistency is structural, not asserted: one `_unit_identifier` helper, two call sites (FR-005/SC-006). Do NOT add a second identifier-formatting expression.
- Frozen ontology untouched (Principle X); no new dependency (Constitution II); each changed file ≤ 500 lines (Principle IV).
- Commit after each logical group; the `after_tasks` git hook offers a commit for this artifact.
