---
description: "Task list for iteration 043 — split character_presence (orphan error stays; unknown-mention declares not_evaluated)"
---

# Tasks: Split `character_presence` — orphan rule (`error`) stays; unknown-mention rule declares `not_evaluated`

**Input**: Design documents from `/specs/043-character-presence-split/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/validator-split.md ✅, quickstart.md ✅

**Tests**: Included — FR-014 and Principle VIII (≥80 % coverage) require them; neither validator may ship without coverage.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 / US4 (maps to the spec's user stories)
- Every task gives an exact file path

## Path Conventions

Single src-layout package: `src/bookwright/`, tests at `tests/`. Paths below are repo-root-relative.

---

## Phase 1: Setup (baseline reference)

**Purpose**: Capture the pre-change reference the byte-for-byte invariants (SC-003/SC-004) are measured against.

- [X] T001 Run `uv run pytest` from repo root and confirm the suite is green **before** any edit; record the current `error`-level finding set across fixtures (the byte-for-byte reference for SC-003/invariant I1). Confirm `character_presence` emits **zero** findings on `tests/fixtures/tiny-historical/` today (clarification Q1 / Assumptions) so the unchanged `validation.counts` claim is grounded.

**Checkpoint**: Green baseline + error-finding snapshot recorded.

---

## Phase 2: Foundational (the keystone module — blocks the ripple)

**Purpose**: Create the new abstainer validator. The registry pin, the status remedy, and the `tiny-historical` oracle all reference this validator's **name** and **reason string**, so it must exist before those ripple tasks can pass.

**⚠️ CRITICAL**: T002 blocks every registry/status/oracle task (T010, T015, T016, T017, T018, T021, T022).

- [X] T002 Create `src/bookwright/validation/validators/character_unknown_mentions.py`: a `CharacterUnknownMentions` validator with `name = "character_unknown_mentions"` and `severity_default = Severity.warning` (cosmetic — never emits) — the two attributes the `Validator` Protocol requires, mirroring `CharacterPresence` which carries **no** class-level `triples` (the abstainer emits no `Violation`, so there are trivially no triples; contract C2 / data-model D3) — and a `validate(project, indexer)` body that is **solely** `raise NotEvaluated("open-set proper-noun discovery requires semantic judgment (move 3); the deterministic heuristic was measured insufficient on real prose")` — **unconditionally**, with no reference to `project`/`indexer` state (contract C2; FR-005; data-model D3). Module/class docstring states it is a pure abstainer pending move 3. Mirror the import/shape conventions of the existing validator modules so `registry._discover_builtins` auto-discovers it (no hand-registration).

**Checkpoint**: New built-in exists and is auto-discovered; the validator set is now 7.

---

## Phase 3: User Story 1 — Unknown-mention dimension stops emitting false-positive warnings (Priority: P1) 🎯 MVP

**Goal**: No unknown-mention `warning` is ever emitted; one legible `not_evaluated` entry appears instead, on every project.

**Independent Test**: Run validation over a project whose manuscript contains capitalized words with no bible entry (organization, title word, quoted first word). Confirm **zero** unknown-mention `warning` findings and **one** `not_evaluated` entry naming `character_unknown_mentions` with the open-set reason.

### Tests for User Story 1

- [X] T003 [P] [US1] Create `tests/validation/test_character_unknown_mentions.py`: assert `CharacterUnknownMentions().validate(...)` raises `NotEvaluated` with the **exact** open-set reason string regardless of inputs — empty project, clean project, and a project with off-roster proper nouns (org / title word / quoted first word). Assert `name == "character_unknown_mentions"` and `severity_default == Severity.warning`. Reuse the `tests/validation/conftest.py` `write_project`/`load_context` pattern. (Acceptance scenarios 1–2; SC-001/SC-002.)

### Implementation for User Story 1

- [X] T004 [US1] Verify (no code) via T003 that the abstainer emits **no** `Violation` and surfaces only through `not_evaluated[]` — depends on T002. (If T003 reveals a Protocol-attr gap, fix it in `character_unknown_mentions.py`.)

**Checkpoint**: The abstainer unconditionally declares `not_evaluated`; zero unknown-mention warnings anywhere. MVP behavior delivered.

---

## Phase 4: User Story 2 — Orphan rule (`error`) untouched + heuristic deleted (Priority: P1)

**Goal**: `character_presence` keeps the orphan rule **only**, emits `error` findings byte-for-byte identical (same `validator` name), and the **entire** deterministic unknown-mention heuristic plus its now-dead consumers are deleted (FR-016/FR-017).

**Independent Test**: Run the fixtures and confirm the `error`-finding set is byte-for-byte unchanged (incl. each finding's `validator` field); an unmentioned character still yields exactly one `error`. A repo-wide grep finds zero occurrences of every deleted symbol.

### Implementation for User Story 2

- [X] T005 [US2] Edit `src/bookwright/validation/validators/character_presence.py`: **keep** `CharacterPresence` (name unchanged), `_orphans`, `_is_mentioned`, `_MIN_TOKEN_LEN`, and the `not roster and not files` `NotEvaluated` guard with its **identical** reason string. Make `validate` body: guard → `return self._orphans(roster, files)`. **Delete** `_CANDIDATE`, `_SENTENCE_END`, `_STOP_WORDS`, `_is_sentence_initial`, `_roster_slugs`, `_unknown_mentions`, and the `setting/location/object` union line. **Remove** the now-unused imports `make_slug` and `ProseView`. Trim the module/class docstring to the orphan-only rule. (Contract C1; FR-003/FR-004/FR-016; module must stay ≤500 lines — shrinks ~223→~95.)
- [X] T006 [US2] Edit `src/bookwright/validation/base.py`: **delete** `location_names()`, `object_names()`, the `_location_names`/`_object_names` cache fields, the `_names_of(NarrativeLocation)`/`_names_of(Object)` wiring, and the `NarrativeLocation`/`Object` imports left unused. **Keep** `setting_names()`, `_setting_names`, `_names_of`, the `_UNSET` sentinel, and the `Character`/`Setting` imports. (FR-017; data-model "Removed entities"; confirm zero live consumers before deleting.)
- [X] T007 [US2] Edit `tests/validation/conftest.py`: remove the `locations=` and `objects=` knobs from `write_project`, their two scaffold loops and dir creation, and update the docstring. **Keep** the `settings=` knob (still consumed by `setting_continuity` tests). (FR-017.)
- [X] T008 [P] [US2] Migrate `tests/validation/test_character_presence.py`: **keep** the orphan/guard tests (`test_no_prose_and_empty_roster_is_not_evaluated`, `test_empty_manuscript_with_roster_stays_evaluated_and_emits_orphans`, `test_orphan_bible_character_is_error`) and the clean-project test. **Delete** every unknown-mention / seam / union test (sentence-initial, heading, blockquote, dialogue-dash, mid-line, declared setting/location/object suppression, off-bible-still-fires, locator, guard-with-declared-environments). (Plan §Tests 5; depends on T005.)
- [X] T009 [P] [US2] Edit `tests/validation/test_base.py`: delete `test_location_and_object_names_read_and_cache` and `test_location_and_object_names_empty_when_dir_absent`. Leave the `setting_names()` coverage in `test_context_accessors_cache_and_read` intact. (FR-017; depends on T006/T007.)

**Checkpoint**: Orphan `error` byte-identical; dead heuristic + dead accessors fully removed; grep for deleted symbols is empty.

---

## Phase 5: User Story 3 — Each validator is atomically evaluated-or-not (Priority: P1)

**Goal**: Orphan `error` and unknown-mention `not_evaluated` both appear in the **same** run — neither suppresses the other (the bug 040 created the channel to avoid).

**Independent Test**: Run validation over a project with both a never-mentioned character and off-roster proper nouns; confirm the orphan `error` and the `character_unknown_mentions` `not_evaluated` entry both appear, and the exact `ran` set is the 7 built-ins.

### Tests for User Story 3

- [X] T010 [P] [US3] Edit `tests/validation/test_registry.py`: add `"character_unknown_mentions"` to the `_BUILTINS` pin (6 → 7). (Depends on T002.)
- [X] T011 [P] [US3] Edit `tests/validation/test_command.py`: add `"character_unknown_mentions"` to the exact `ran`-set assertion in `test_json_is_single_document_…` (6 → 7); the line-85 subset loop needs no edit. (Contract C3/C4; depends on T002.)
- [X] T012 [US3] Add a coexistence assertion (in `tests/validation/test_runner.py` or `test_command.py`): a synthetic project with a never-mentioned character **and** off-roster proper nouns yields the orphan `error` **and** the `character_unknown_mentions` `not_evaluated` entry in one run; `errors[]` does **not** contain `character_unknown_mentions` (it raised `NotEvaluated`, not a crash). (Acceptance scenario 1; contract C3; depends on T002/T005.)

**Checkpoint**: Both verdicts coexist; the 7-built-in set is pinned everywhere.

---

## Phase 6: User Story 4 — `not_evaluated` reason is legible across the existing channels (Priority: P2)

**Goal**: The honest reason surfaces through every 040 channel (`--json` `not_evaluated[]`, human report, `status` `state.validation`, `next_actions`) with **no new channel**, and the always-firing dormant nudge carries an honest, tailored remedy.

**Independent Test**: Run `validate --json` and `bookwright status` over any project; confirm the `character_unknown_mentions` `not_evaluated` entry with the open-set/move-3 reason appears in both, and the green predicate is `False`.

### Implementation for User Story 4

- [X] T013 [US4] Edit `src/bookwright/status/rules.py`: add a `_REMEDIES["character_unknown_mentions"]` clause so the always-firing `activate_dormant_validators` prompt is **honest** (e.g. "awaiting LLM semantic judgment (move 3) — no manual action available yet") instead of the generic "investigate why it could not evaluate". Use the existing dormant-prompt channel — **no** new rule, **no** new channel. (Contract C5; data-model D6; depends on T002.)

### Tests for User Story 4

- [X] T014 [P] [US4] Edit `tests/status/test_queries.py` (`test_validation_summary_surfaces_not_evaluated_sorted`): keep the subset + `sorted` assertions; update the "three validators" comment to four and add `assert "character_unknown_mentions" in names`. (Depends on T002/T013.)
- [X] T015 [US4] Edit `tests/commands/test_status.py`: change `len(state["validation"]["ran"]) == 6` → `== 7`; in `test_known_state_yields_the_exact_next_actions`, append the 4th action `"bookwright-continuity"` (the dormant nudge), update its comment (no longer "exactly three"). (Contract C5; depends on T002/T013.)
- [X] T016 [US4] Edit `tests/e2e/test_orchestration_workflow.py` — **Group A**: `len(next_actions) == 3` → `== 4` in both `test_second_status_converges` assertions (lines ~290–291); the 4th action is byte-identical across runs so `_invariant_view` equality still holds; assert the `not_evaluated` entry appears. **Also** update the module docstring (lines ~9–11) that states resolving one question "leaves `len(next_actions) == 3` unchanged" → the 4-action shape, so the file's prose no longer contradicts its assertions (no stale lore). (Depends on T002/T013.)
- [X] T017 [US4] Edit `tests/e2e/test_orchestration_workflow.py` — **Group B** (`test_focus_free_project_recommends_no_research_workstream`): reframe the `research_skills.isdisjoint(_skills(payload))` assertion to the **research-derived** skills only `{"bookwright-research", "bookwright-verify"}`, since `bookwright-continuity` is now dual-purpose (`review_continuity` **and** the always-on `activate_dormant_validators`). (Plan §Tests 13; depends on T002/T013.)

**Checkpoint**: The honest `not_evaluated` reason and the 4-action ripple are pinned across status/queries/e2e; green predicate `False` everywhere.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Fixture oracle, debt ledger, and the full gate/quickstart verification.

- [X] T018 [US4] Edit `tests/fixtures/tiny-historical/expected-status.md`: add a `not_evaluated` block (one entry: `character_unknown_mentions` + its open-set reason); change `next_actions.skills` to the 4-entry list `[bookwright-research, bookwright-verify, bookwright-continuity, bookwright-continuity]`; update the convergence prose ("tres workstreams"/`len == 3` → the 4-action shape, dormant nudge explained). **Do not** edit the fixture manuscript or bible; `validation.counts` stays byte-identical `{error: 1, warning: 1, info: 0}`. (FR-011; SC-005; depends on T002/T013.)
- [X] T019 [P] Edit `DEBT.md`: remove the **DEBT-011** (paired leading-quote markers) and **DEBT-012** (title-body scan) entries; keep DEBT-014/DEBT-018; update the track-A doctrine note so it no longer lists 011/012 as pending. (FR-010; SC-007.)
- [X] T020 Run the dead-code sweep (SC-009): `grep -rn "_unknown_mentions\|_roster_slugs\|_CANDIDATE\|_STOP_WORDS\|_is_sentence_initial\|location_names\|object_names" src tests` prints **nothing**; `grep -rn "locations=\|objects=" tests/validation/conftest.py` prints nothing; `grep -rn "setting_names" src tests` shows only `base.py` + `setting_continuity.py` (+ their tests). Confirm `git diff --stat` over `src/bookwright/io/prose.py`, `resources/schemas/golem-1.1/`, and `*golem.ttl` is empty (SC-008, FR-009/FR-013), and `wc -l` on each changed source file is ≤500.
- [X] T021 Run all four gates: `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest`. All must pass with ≥80 % coverage; `ruff` must report **no** unused import introduced by the deletions. (SC-007; FR-012; depends on every prior task.)
- [X] T022 Execute the `quickstart.md` checks end-to-end (sections 1–7) over `tests/fixtures/tiny-novel` (or a copy) to confirm `green = False`, the abstainer entry present, and counts unchanged — the empirical zero-regression proof (FR-012; depends on T021).

**Checkpoint**: All gates green, no dead code, oracle and debt ledger updated, quickstart verified.

---

## Phase 8: Convergence

- [ ] T023 Remove the leftover quickstart scratch script `_qs_check.py` at the repo root (or, if it must be kept, move it under a path `ruff`/`pyproject` excludes and make it lint-clean) so `uv run ruff check` passes — today it fails with `PLR2004` (magic value `7`) at `_qs_check.py:31`, leaving the lint gate red despite `pytest`/`mypy`/`format` being green per SC-007 / T021 (unrequested).

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2 / T002)**: blocks all ripple tasks (T010, T011, T012, T013, T014, T015, T016, T017, T018, T022).
- **US1 (Phase 3)**: depends on T002.
- **US2 (Phase 4)**: independent of US1 — `character_presence.py`/`base.py`/`conftest.py` are different files from the new module. Internal order: T005 before T008; T006/T007 before T009.
- **US3 (Phase 5)**: T010/T011 depend on T002; T012 depends on T002 + T005.
- **US4 (Phase 6)**: T013 depends on T002; T014–T017 depend on T002 + T013.
- **Polish (Phase 7)**: T018 depends on T002 + T013; T020/T021/T022 depend on essentially all prior tasks; T019 is independent.

### Within each user story

- Source edits before the tests that pin them (T005 → T008; T006/T007 → T009; T013 → T014–T017).
- Story complete and independently testable before moving on.

### Parallel opportunities

- After T002: US1 (T003) and US2 (T005/T006/T007) can proceed in parallel — disjoint files.
- T008 and T009 are `[P]` (different test files), once their source edits land.
- T010 and T011 are `[P]` (different test files), after T002.
- T014, T016/T017 (same file `test_orchestration_workflow.py` → T016 and T017 are **not** mutually `[P]`), and T019 (`DEBT.md`) can run alongside other-file work.

---

## Parallel Example

```bash
# After T002 (keystone module exists), launch the two P1 stories' disjoint edits together:
Task: "T003 [US1] tests/validation/test_character_unknown_mentions.py"
Task: "T005 [US2] src/bookwright/validation/validators/character_presence.py"
Task: "T006 [US2] src/bookwright/validation/base.py"

# Registry/command pins in parallel (different files):
Task: "T010 [US3] tests/validation/test_registry.py — _BUILTINS 6→7"
Task: "T011 [US3] tests/validation/test_command.py — ran set 6→7"
```

---

## Implementation Strategy

### MVP (Setup + Foundational + US1)

1. T001 baseline.
2. T002 keystone abstainer module.
3. T003/T004 — the abstainer unconditionally declares `not_evaluated`; **zero** unknown-mention warnings. This alone is the issue #1 deliverable.

### Incremental delivery

1. MVP (US1) → the false-positive flood is gone.
2. US2 → orphan `error` byte-identical, dead heuristic + dead accessors swept.
3. US3 → both verdicts coexist; 7-built-in set pinned.
4. US4 → honest reason + 4-action ripple across status/e2e.
5. Polish → oracle, `DEBT.md`, gates, quickstart.

### Notes

- `[P]` = different files, no incomplete-task dependency.
- This iteration is **deletion-heavy**: net lines removed > added; `character_presence.py` shrinks ~223→~95.
- Verify migrated/deleted tests fail-or-vanish appropriately before claiming green.
- Commit after each logical group (the auto-git hook offers per phase).
- The byte-for-byte `error` invariant (SC-003) and the unchanged `tiny-historical` counts (SC-005) are the two load-bearing non-regressions — check them explicitly in T020/T021.
