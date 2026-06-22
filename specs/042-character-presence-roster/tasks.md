---
description: "Task list for iteration 042 — character_presence cross-checks settings/locations/objects (DEBT-010)"
---

# Tasks: `character_presence` unknown-mention rule cross-checks settings, locations & objects

**Input**: Design documents from `/specs/042-character-presence-roster/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/validation-context-accessors.md, quickstart.md

**Tests**: REQUIRED for this iteration. FR-015 / Principle VIII mandate that both new accessors and both new union arms (location, object) are exercised by test so nothing ships as untested dead plumbing. Test tasks are therefore included.

**Organization**: Tasks are grouped by user story. The four stories are facets of one change: US1 fixes the defect (the union widening); US2/US3/US4 are guard-rail verifications that the widening suppressed only false positives and perturbed nothing else.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 / US4 (maps to spec.md user stories)
- Exact file paths included in every task

## Path Conventions

Single src-layout package: `src/bookwright/`, `tests/` at repo root (the only layout this repo uses, per plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the empirical baseline before any edit, so regression is provable.

- [X] T001 Confirm clean baseline: run `uv run pytest tests/validation/test_character_presence.py tests/e2e` and record that they pass on the unchanged tree; confirm `tests/fixtures/tiny-historical/expected-status.md` currently pins `validation.counts.warning: 4` and `validation.counts.error: 1` (the pre-fix oracle). No code is edited in this task.

**Checkpoint**: Baseline green and the to-be-corrected oracle value (4) confirmed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the two new context accessors and the test-scaffold knobs that ALL user-story work depends on. No behavior changes here yet — these are the seams US1's union and US1/US2's tests consume.

**⚠️ CRITICAL**: No user story can be implemented or tested until this phase is complete.

- [X] T002 [P] Extend `write_project` in `tests/validation/conftest.py` with `locations=()` and `objects=()` keyword arguments that mirror the existing `settings` knob byte-for-byte — each name writes one `bible/<locations|objects>/<slug>.md` card (`---\nname: "<name>"\n---\n`). Both default to `()` so every existing caller builds a byte-identical project (contract C4, FR-011/FR-015). Keep the file ≤ 500 lines (currently 397).
- [X] T003 Add `location_names()` and `object_names()` cached accessors to `ValidationContext` in `src/bookwright/validation/base.py`, plus their two `_UNSET`-sentinel cache fields (`_location_names`, `_object_names`, `field(default=_UNSET, repr=False, compare=False)`). Each accessor is byte-for-byte the `setting_names()` body with `Setting` swapped for the lazily-imported `NarrativeLocation` (G13) / `Object` (G16) from `bookwright.golem`, resolved through the existing generic `_names_of(concept_cls)` — NO new helper (contracts C1/C2, FR-001, data-model "Memoization"). Keep the file ≤ 500 lines (321 → ~350).

**Checkpoint**: `location_names()` / `object_names()` resolve and memoize; `write_project(..., locations=[...], objects=[...])` scaffolds the cards. The validator behavior is still unchanged.

---

## Phase 3: User Story 1 — Declared settings/locations/objects stop being mis-flagged (Priority: P1) 🎯 MVP

**Goal**: Widen the unknown-mention rule's suppression set to the union of all four rosters so the capitalized tokens of declared environments (`Real`, `Fábrica`, `Paños`) stop firing spurious "no bible entry" warnings.

**Independent Test**: Over a project declaring "la Real Fábrica de Paños" whose manuscript names it, `Real`/`Fábrica`/`Paños` produce no unknown-mention warning (today each produces one).

### Tests for User Story 1 ⚠️ (write FIRST, ensure they FAIL before T007)

- [X] T004 [P] [US1] In `tests/validation/test_character_presence.py`, add a synthetic-project test (via `write_project`/`load_context`) asserting that a declared **setting** whose multi-word name is named in the manuscript produces **no** unknown-mention warning for any of its tokens (FR-003, SC-001). Must fail before T007.
- [X] T005 [P] [US1] In `tests/validation/test_character_presence.py`, add synthetic-project tests for the **location** arm (`write_project(..., locations=["…"])`) and the **object** arm (`write_project(..., objects=["…"])`): a declared location name and a declared object name — full phrase and any ≥3-letter token — produce no unknown-mention warning (US1.2/US1.3, FR-002/FR-015). Must fail before T007.
- [X] T006 [P] [US1] In `tests/validation/test_base.py`, add direct accessor tests for `location_names()` and `object_names()`: each returns the sorted `(name, bible_relpath)` pairs for its bible dir, returns `()` when the dir is absent/empty, and is memoized (contracts C1/C2, FR-015). Must fail before T003 is in place — verify against the new accessors.

### Implementation for User Story 1

- [X] T007 [US1] In `CharacterPresence.validate` (`src/bookwright/validation/validators/character_presence.py`), keep `roster = project.character_names()` feeding `_orphans`, but build the slug set `_unknown_mentions` consumes from the concatenation `roster + project.setting_names() + project.location_names() + project.object_names()` passed once through the existing module-level `_roster_slugs` (unchanged). `_orphans`, `_unknown_mentions`, the `NotEvaluated` guard, `_roster_slugs`, and `triples=()` are otherwise untouched (D2, FR-002/FR-003, contract C3). Keep the file ≤ 500 lines (214 → ~218).
- [X] T008 [US1] Correct the `tiny-historical` oracle `tests/fixtures/tiny-historical/expected-status.md`: `validation.counts.warning` `4 → 1` (the three setting-token warnings removed; the lone `factual_anchor` warning remains), `validation.counts.error` left at `1`, and update the explanatory comment block (lines ~14–15, ~91) to reflect the new count. **Do not edit the fixture manuscript or bible** (FR-011/FR-012, SC-002). Re-run `uv run pytest tests/e2e/test_orchestration_workflow.py` to confirm green.

**Checkpoint**: T004–T006 now pass; `tiny-historical` E2E green with `warning: 1`; the defect is closed. US1 is independently demonstrable.

---

## Phase 4: User Story 2 — A genuinely off-bible name still fires (Priority: P1)

**Goal**: Prove the wider roster suppresses only false positives — a proper noun absent from all four rosters still produces exactly one warning.

**Independent Test**: A manuscript proper noun present in no bible folder still yields one unknown-mention warning citing its first occurrence.

### Tests for User Story 2 ⚠️

- [X] T009 [P] [US2] In `tests/validation/test_character_presence.py`, add a synthetic-project test: a manuscript proper noun absent from characters, settings, locations and objects still produces exactly **one** `warning` with the same message/severity and first-occurrence locator as before (FR-005, SC-004). This passes against the T007 implementation (no further impl needed).

**Checkpoint**: Off-bible names still fire — the fix traded no noise for blindness.

---

## Phase 5: User Story 3 — The gate-protecting orphan rule is untouched (Priority: P1)

**Goal**: Prove the `error` orphan rule still derives exclusively from the character roster and that a declared-but-unmentioned setting/location/object yields no finding of any severity.

**Independent Test**: The set of `error` findings across the suite is byte-for-byte unchanged; an unmentioned setting produces no new finding.

### Tests for User Story 3 ⚠️

- [X] T010 [P] [US3] In `tests/validation/test_character_presence.py`, add a synthetic-project test: a declared setting/location/object that is **never** mentioned in the manuscript produces neither an orphan `error` nor any absence `warning` (FR-004, SC-003 US3.2).
- [X] T011 [US3] Run `uv run pytest tests/validation tests/e2e` and confirm the set of `error`-level findings is byte-for-byte identical to the Phase 1 baseline (0 added/removed/changed); the only count delta anywhere is `tiny-historical` warning `4 → 1` (FR-006, SC-003). No code edited in this task.

**Checkpoint**: The CI gate (`error` severity) is provably unchanged.

---

## Phase 6: User Story 4 — The `not-evaluated` guard is unchanged (Priority: P2)

**Goal**: Prove the iteration-040 tri-valued contract is intact: `character_presence` abstains only when there is no manuscript prose AND an empty character roster, with the identical reason string — regardless of declared settings/locations/objects.

**Independent Test**: A project with no prose and no characters (settings present) raises the same not-evaluated reason as iteration 040.

### Tests for User Story 4 ⚠️

- [X] T012 [P] [US4] In `tests/validation/test_character_presence.py`, add a synthetic-project test: no manuscript prose + empty character roster but with declared settings (and/or locations/objects) still raises `NotEvaluated` with the string-identical iteration-040 reason (FR-007, SC-005). Confirms the guard stays clavado on `not roster and not files` (character roster only).

**Checkpoint**: The abstain condition is provably unperturbed.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Close the debt and verify the full gate.

- [X] T013 Remove the `### DEBT-010 …` entry from `DEBT.md` (the multi-word-setting-token block at ~line 46); git preserves the history (FR-013, SC-006).
- [X] T014 Verify frozen-ontology & file-size compliance (SC-007): `git diff` over `src/bookwright/resources/schemas/golem-1.1/` and any `golem.ttl` is empty; the validator's `triples` stay `()`; `wc -l` on `src/bookwright/validation/base.py` and `src/bookwright/validation/validators/character_presence.py` and `tests/validation/conftest.py` each ≤ 500.
- [X] T015 Run the full gate: `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` — all four green, ≥80% coverage (SC-006). Run the quickstart.md scenarios as the final acceptance pass.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately (records the baseline T011 compares against).
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS all user stories** — T007's union and T004–T006 tests consume the T003 accessors / T002 scaffold knobs.
- **User Story 1 (Phase 3)**: Depends on Foundational. The MVP and the only phase with a behavior change (T007) + oracle correction (T008).
- **User Story 2 (Phase 4)**: Depends on T007 (tests the same implementation). Test-only.
- **User Story 3 (Phase 5)**: Depends on T007. Test-only + baseline comparison.
- **User Story 4 (Phase 6)**: Depends on Foundational only (guard is unchanged; needs the conftest scaffold). Test-only.
- **Polish (Phase 7)**: Depends on all user stories complete.

### Within / across stories

- T002 and T003 are independent files → parallel.
- All test-authoring tasks (T004, T005, T006, T009, T010, T012) touch test files only and are mutually independent → parallel, BUT those in `test_character_presence.py` (T004/T005/T009/T010/T012) edit the **same file**, so treat them as parallel-authorable but serialize the actual edits (or write as one batch). T006 is in `test_base.py` → truly parallel.
- T007 (the one source change) must land before T008 and before Phase 4/5 verification pass.
- T011 and T014/T015 are verification-only and run last.

### Parallel Opportunities

- Foundational: T002 ‖ T003 (different files).
- US1 test authoring: T006 (`test_base.py`) ‖ the `test_character_presence.py` batch.

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Different files, no interdependency — author together:
Task: "T002 Extend write_project with locations=/objects= in tests/validation/conftest.py"
Task: "T003 Add location_names()/object_names() accessors in src/bookwright/validation/base.py"
```

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Phase 1: confirm baseline + record oracle = 4.
2. Phase 2: accessors (T003) + conftest knobs (T002).
3. Phase 3: write failing tests (T004–T006), widen the union (T007), correct the oracle (T008).
4. **STOP & VALIDATE**: `Real`/`Fábrica`/`Paños` no longer flagged; `tiny-historical` warning `1`. This alone closes DEBT-010.

### Incremental hardening (guard-rails)

5. US2 (T009): off-bible name still fires.
6. US3 (T010–T011): orphan `error` set byte-identical.
7. US4 (T012): `not-evaluated` reason unchanged.
8. Polish (T013–T015): drop DEBT-010, prove ontology/file-size compliance, run the four gates.

### Notes

- [P] = different files, no incomplete-task dependency.
- Single source change is T007; everything else is accessors, test scaffolding, tests, oracle, debt, and gates.
- Verify each new test FAILS before T007/T003 land (TDD per template + Principle VIII).
- No fixture manuscript or bible content is edited anywhere (FR-011); the only fixture edit is the `tiny-historical` oracle count (T008).
- Commit after each logical group; the auto-git hooks offer commits between phases.
