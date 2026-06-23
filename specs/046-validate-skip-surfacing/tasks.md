---
description: "Task list for iteration 046 — validate surfaces ingestion-skipped bible files"
---

# Tasks: `validate` surfaces ingestion-skipped bible files

**Input**: Design documents from `specs/046-validate-skip-surfacing/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅,
contracts/validate-skip-surfacing.md ✅, quickstart.md ✅

**Tests**: REQUESTED. FR-016 / SC-001..005 mandate empirical `uv run pytest`
verification, and quickstart.md enumerates six runnable scenarios. Test tasks are
therefore included and (per the suite's house style) are written **before** the
code that satisfies them where practical.

**Organization**: grouped by user story (US1 P1, US2 P2, US3 P2) so each is an
independently testable increment. This is a deliberately small two-file code change
(`commands/validate.py` + `validation/runner.py`) — the bulk of the work is
contract-before-code design edits, tests, and debt reconciliation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no incomplete-task dependency)
- **[Story]**: US1 / US2 / US3 (Setup/Foundational/Polish carry no story label)
- Every task names exact file paths.

## Path Conventions

Single project, src-layout: source under `src/bookwright/`, tests under `tests/`,
design/debt records at repo root. Paths below are repo-relative.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: confirm the working state before any edit. No scaffolding is needed —
the channel (040), kind vocabulary (044), and read path (`ValidationContext.bible()`)
already exist; this iteration only consumes them.

- [ ] T001 Confirm clean baseline: run `uv run pytest -q`, `uv run ruff check`,
  `uv run ruff format --check`, and `uv run mypy --strict` and verify all four gates
  are green on branch `046-validate-skip-surfacing` before editing (establishes the
  byte-identity reference for SC-003 / FR-010).

**Checkpoint**: baseline green and reproducible.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the contract-before-code design edits (the design is the binding
contract and MUST lead the code — plan § 7.3) and the shared total-order key in
`runner.py` that the US1 skip-merge imports. **No user-story code may begin until
these land.**

**⚠️ CRITICAL**: The design edits (T002) precede the code divergence; the runner
key (T003) is imported by US1's merge (T009), so US1 is blocked on it.

- [ ] T002 Contract-before-code design edit in `bookwright-design.md`: add the
  `ingestion` pseudo-source paragraph to the not-evaluated channel description in
  § 13.4 (a skipped bible file becomes a `not_evaluated` entry with
  `validator="ingestion"`, `kind=missing_input`, reason citing path + cause), and
  reconcile § 13.5 move-1 so it states that ingestion skips are now **surfaced by
  `validate`** (degrading green), not only refused by `status` (plan § 7.3 / Phase 1).
  Keep these edits in Spanish (language convention).

- [ ] T003 Promote the `not_evaluated` sort to a total order in
  `src/bookwright/validation/runner.py` (FR-009, plan decision 1): define a
  module-level `def not_evaluated_sort_key(result: NotEvaluatedResult) -> tuple[str, str]:`
  returning `(result.validator, result.reason)` with the FR-009 docstring; replace
  the inline `not_evaluated.sort(key=lambda r: r.validator)` (line 80) with
  `not_evaluated.sort(key=not_evaluated_sort_key)`; add `"not_evaluated_sort_key"`
  to `__all__`. This MUST NOT reorder any skip-free fixture (validator names are
  already unique — FR-010); the file stays ≤ 500 lines (FR-015).

**Checkpoint**: design contract states the new behavior; the shared key exists and
is importable. The full suite still passes (T003 is a no-op for existing fixtures).

---

## Phase 3: User Story 1 — A skipped bible file is no longer silently green (Priority: P1) 🎯 MVP

**Goal**: `validate` consumes `project.bible().skipped` and merges one
`NotEvaluatedResult(validator="ingestion", reason=…, kind=missing_input)` per skipped
bible file into the existing `not_evaluated[]`, so a partial corpus stops reading as
green while the exit code is unchanged.

**Independent Test**: build a project with one bible character file whose
front-matter is broken YAML; run `validate --json`; assert (a) exactly one
`not_evaluated` entry naming that file with `kind == "missing_input"`, (b)
`is_green(payload) is False`, and (c) the exit code equals the no-skip run's.

### Tests for User Story 1 (write first; they FAIL until T009) ⚠️

- [ ] T004 [P] [US1] Create `tests/commands/test_validate_skipped.py` with a fixture
  helper that does `copy_fixture("tiny-novel", tmp_path)`, writes a broken-YAML bible
  file using the literal `"---\nname: : :\n  bad\n---\n"` (reused from
  `tests/commands/test_status_errors.py`), and runs `validate --json` in-process via
  `typer.testing.CliRunner` (quickstart Scenario 1). Assert exit 0, exactly one
  `not_evaluated` entry with `validator == "ingestion"`, `kind == "missing_input"`,
  and a `reason` naming `bible/characters/broken.md`; assert `is_green(payload) is
  False` (SC-001, Acceptance 1–2).

- [ ] T005 [P] [US1] Add a test in `tests/commands/test_validate_skipped.py`
  asserting the `validate --json` exit code on the one-skip project equals the exit
  code of the same fixture **without** the broken file (quickstart Scenario 2,
  SC-002, Acceptance 3) — a skip alone does not move the gate.

- [ ] T006 [P] [US1] Add a determinism test in
  `tests/commands/test_validate_skipped.py`: write **two** broken bible files
  (`broken_a.md`, `broken_b.md`), run `validate --json` twice, and assert both runs
  emit two `ingestion` entries in byte-identical order (quickstart Scenario 3,
  Acceptance 5) — proving `(validator, reason)` resolves the shared-`validator` tie.

### Implementation for User Story 1

- [ ] T009 [US1] Merge the ingestion skips in `src/bookwright/commands/validate.py`
  `_validate` (plan decision 2): after `run_validators(...)` returns `not_evaluated`
  (line 108) and **before** constructing `ValidationReport` (line 109), build
  `skip_entries = [NotEvaluatedResult("ingestion", f"bible file '{s.path}' skipped
  (unusable front-matter): {s.reason}", NotEvaluatedKind.missing_input) for s in
  project.bible().skipped]`, then pass
  `not_evaluated=tuple(sorted([*not_evaluated, *skip_entries], key=not_evaluated_sort_key))`.
  Add imports: `NotEvaluatedResult` from `bookwright.validation`, `NotEvaluatedKind`
  from `bookwright.validation.base`, `not_evaluated_sort_key` from
  `bookwright.validation.runner`. Read path is the memoized `project.bible()` (no
  graph rebuild, safe/empty on a missing bible dir — research D1). File stays ≤ 500
  lines (FR-015); no validator module touched (FR-012).

**Checkpoint**: T004–T006 pass. The MVP is complete — a skipped bible file is
surfaced and denies green, with the gate untouched.

---

## Phase 4: User Story 2 — The skip is visible in both `validate` surfaces (Priority: P2)

**Goal**: the skip is readable on **both** surfaces `validate` emits — the `--json`
envelope and the human report — via the existing `not_evaluated[]` rendering (no
second channel).

**Independent Test**: for the broken-YAML project, assert the skip entry appears in
(a) the `--json` `not_evaluated[]` with its `kind` keys, and (b) the human report's
`not evaluated:` section with its kind label.

### Tests for User Story 2 ⚠️

- [ ] T010 [P] [US2] Add a test in `tests/commands/test_validate_skipped.py`
  asserting the `--json` skip entry serializes with `validator`, `reason`, and `kind`
  keys (the existing `NotEvaluatedResult.to_json` shape — Acceptance 1, US2). (Rides
  the T009 code; no further source change.)

- [ ] T011 [P] [US2] Add a human-report test in
  `tests/commands/test_validate_skipped.py`: run `validate` **without** `--json` and
  assert the `not evaluated:` section lists
  `ingestion [input gap]: bible file 'bible/characters/broken.md' skipped …`
  (quickstart Scenario 5, Acceptance 2, US2) — `missing_input` renders as `input gap`
  via the unchanged `_KIND_LABEL`.

**Checkpoint**: the skip is proven visible on both surfaces; no source change beyond
T009 (US2 is observable-only over the P1 channel).

---

## Phase 5: User Story 3 — `validate` and `status` agree a skip is reportable (Priority: P2)

**Goal**: resolve the `status`↔`validate` asymmetry (DEBT-018's framing) — `status`
still refuses (`skipped_sources`) and `validate` now surfaces the same file, so
neither reads a partial corpus as fully fine.

**Independent Test**: for the broken-YAML project, assert `status --json` still exits
4 with `code == "skipped_sources"` AND `validate --json` surfaces the same file in
`not_evaluated[]`.

### Tests for User Story 3 ⚠️

- [ ] T012 [P] [US3] Add a cross-command test in
  `tests/commands/test_validate_skipped.py`: on the one-skip project assert
  `status --json` → exit 4, `code == "skipped_sources"` (unchanged) and
  `validate --json` → surfaces the same `bible/characters/broken.md` in
  `not_evaluated[]` (quickstart Scenario 6, SC-004, US3 Acceptance 1). The two report
  it by different pre-existing mechanisms — confirm both, not a shared third channel.

**Checkpoint**: cross-command agreement proven; `status` confirmed unedited.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: debt reconciliation, no-skip byte-identity guard, and the four-gate
close.

- [ ] T013 [P] Remove the DEBT-018 entry from `DEBT.md` (FR-013 / SC-005; git keeps
  the history) and reconcile its track-A cross-reference (the `Track A … DEBT-018,
  DEBT-019` pointer, ~line 51) to drop the dangling DEBT-018 reference. Leave
  DEBT-019 (partial-evaluation contract) recorded and untouched (out of scope).

- [ ] T014 [P] Add the no-skip byte-identity assertion to
  `tests/commands/test_validate_skipped.py` (quickstart Scenario 4, SC-003 / FR-010):
  on a plain `tiny-novel` fixture with **no** broken file, assert `validate --json`
  produces **no** `ingestion` entry and is byte-identical to the pre-change output.
  Confirm `tests/e2e/test_tri_valued_validation.py` `_EXPECTED_GAPS` is **unchanged**
  (no pinned skip-free fixture edited).

- [ ] T015 Run the full quickstart gate (`uv run pytest && uv run ruff check &&
  uv run ruff format --check && uv run mypy --strict`) and confirm all four are green
  (FR-016, SC-003). Verify the agent-context block in `CLAUDE.md` points at this
  iteration's plan (already repointed during planning — confirm only).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: no dependencies — run first to fix the baseline.
- **Foundational (T002–T003)**: depends on Setup. **Blocks US1** (T009 imports
  `not_evaluated_sort_key` from T003; T002 is the contract that must lead the code).
- **US1 (Phase 3)**: depends on Foundational. The MVP.
- **US2 (Phase 4)** and **US3 (Phase 5)**: depend on US1's code (T009) — they are
  observable-only tests over the same merge; both are independently testable and do
  not depend on each other.
- **Polish (Phase 6)**: T013 (DEBT) is independent of code and may run any time after
  Setup; T014/T015 depend on US1.

### Within User Story 1

- Tests T004–T006 are authored first and FAIL until the merge (T009) lands.
- T009 is the single source change for the whole feature; US2/US3 add no source.

### Parallel Opportunities

- T004, T005, T006 ([P], US1 tests) — all add independent test functions to the same
  new file; author together, but if one author owns the file, treat the file
  creation (T004) as first and T005/T006 as appends.
- T010, T011 (US2) and T012 (US3) are [P] across stories once T009 lands.
- T013 (DEBT) and T014 (byte-identity test) are [P] with each other.
- T002 (design) and T003 (runner key) touch different files and are [P] within
  Foundational.

---

## Parallel Example: Foundational

```bash
# Different files, no inter-dependency — run together:
Task: "T002 design edit in bookwright-design.md §13.4/§13.5"
Task: "T003 promote not_evaluated_sort_key in src/bookwright/validation/runner.py"
```

## Parallel Example: cross-story tests (after T009)

```bash
Task: "T010 [US2] --json kind-keys assertion in tests/commands/test_validate_skipped.py"
Task: "T011 [US2] human-report assertion in tests/commands/test_validate_skipped.py"
Task: "T012 [US3] status/validate cross-command agreement in tests/commands/test_validate_skipped.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. T001 baseline green.
2. T002–T003 Foundational (design contract + shared sort key).
3. T004–T006 US1 tests (red), then T009 (the merge) → green.
4. **STOP and VALIDATE**: a skipped bible file is surfaced and denies green; exit
   code unchanged. That is the whole DEBT-018 closure.

### Incremental Delivery

1. Setup + Foundational → channel-consumption ready.
2. US1 → MVP (surface + degrade green).
3. US2 → both-surfaces visibility proven.
4. US3 → cross-command agreement proven.
5. Polish → DEBT-018 removed, byte-identity guarded, four gates green.

---

## Notes

- This is intentionally a **two-file code change**: `validation/runner.py` (the
  shared total-order key, T003) and `commands/validate.py` (the skip-merge, T009).
  Everything else is design contract, tests, and debt records.
- No validator module is touched; `base.py`, `report.py`, `status.py`, the green
  predicate, the `kind` vocabulary, and the frozen ontology are unchanged
  (FR-011/FR-012).
- `kind=missing_input` (never `pending_capability`) is load-bearing: it is what
  degrades green via the unchanged 044 predicate (FR-002/FR-006).
- Commit after each task or logical group; the auto-git `after_tasks` hook offers a
  commit when this file lands.
</content>
</invoke>
