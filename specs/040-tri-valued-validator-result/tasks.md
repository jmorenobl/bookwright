---
description: "Task list for iteration 040 — Tri-valued validator result"
---

# Tasks: Tri-valued validator result (`evaluated` / `not-evaluated(reason)`)

**Input**: Design documents from `/specs/040-tri-valued-validator-result/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅,
contracts/ ✅ (`validator-protocol.md`, `validate-envelope.md`, `status-state.md`),
quickstart.md ✅

**Tests**: INCLUDED — Constitution VIII mandates test discipline (≥ 80 % coverage,
single-sourced in `[tool.coverage.report]`). The plan enumerates the test files; SC-003
requires **zero** edits to existing finding oracles (only additive not-evaluated
assertions).

**Organization**: Tasks are grouped by user story. The shared contract plumbing
(base/runner/report/validate) is Foundational and lands once, first; then US1
(focalization), US2 (setting_continuity + character_presence), US3 (status + skill).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (setup, foundational, polish carry no story label)
- Paths are repo-root relative; single project, src-layout.

## Path Conventions

Single project: `src/bookwright/`, `tests/` at repository root.

---

## Phase 1: Setup (design before code — plan § 7.3)

**Purpose**: Update the ratified contract in `bookwright-design.md` **before** any code
diverges, so the design never lags the code (FR-001).

- [ ] T001 Rewrite `bookwright-design.md § 13.1` (Spanish) to the tri-valued validator
  contract: keep `validate(...) -> list[Violation]` **unchanged**, document the
  `NotEvaluated(reason)` signal (a plain `Exception`, NOT a `BookwrightError`), the
  runner catching it before its generic handler, and the additive `not_evaluated`
  channel (sibling of `violations`/`errors`); state the green predicate `status == "ok"
  AND not_evaluated == []`. This is the FIRST task, before `base.py` is touched.

**Checkpoint**: contract is documented; code may now diverge to match it.

---

## Phase 2: Foundational (shared plumbing — BLOCKS all user stories)

**Purpose**: Introduce the `NotEvaluated` signal + `NotEvaluatedResult` record, thread
the new channel through runner → report → the `validate --json` envelope. No validator
behavior changes yet — every validator still returns lists, so the channel is empty and
nothing regresses. This is the generic, validator-agnostic layer (Assumptions).

**⚠️ CRITICAL**: No user story (US1/US2/US3) can be implemented until this phase is
complete.

- [ ] T002 In `src/bookwright/validation/base.py` add `class NotEvaluated(Exception)`
  (stores `reason: str`, calls `super().__init__(reason)`) and
  `@dataclass(frozen=True) class NotEvaluatedResult` (`validator: str`, `reason: str`,
  `to_json() -> dict[str, Any]` → `{"validator", "reason"}`); update the `Validator`
  Protocol `validate` **docstring** (not its signature) to note it MAY
  `raise NotEvaluated(reason)`; add both names to `__all__`. (283 → ~305 lines.)
- [ ] T003 In `src/bookwright/validation/__init__.py` re-export `NotEvaluated` and
  `NotEvaluatedResult` from `base`.
- [ ] T004 In `src/bookwright/validation/runner.py` widen `RunResult` to the 4-tuple
  `(list[Violation], list[ValidatorError], list[NotEvaluatedResult], list[str])`; in the
  per-validator loop add `except NotEvaluated as skip:` **before** the generic
  `except Exception`, appending `NotEvaluatedResult(validator.name, skip.reason)` and
  `continue`; sort `not_evaluated` by `validator` before return. The generic
  `except Exception` → `ValidatorError(phase="run")` path is unchanged (FR-005/FR-014).
- [ ] T005 In `src/bookwright/validation/report.py` add
  `not_evaluated: tuple[NotEvaluatedResult, ...]` to `ValidationReport`; `to_json` emits
  a top-level `"not_evaluated"` sibling key (sorted, FR-013); `render` adds a
  `not evaluated:` section and prints the "no violations found" clean line **only** when
  violations, errors, AND not_evaluated are all empty; pin the documented green predicate
  `status == "ok" AND not_evaluated == []` here (the single place "clean" is defined,
  SC-002). `failed` (the gate) is **unchanged** — not-evaluated never gates (FR-004).
- [ ] T006 In `src/bookwright/commands/validate.py` thread the runner's new
  `not_evaluated` element into `ValidationReport`; confirm the human + `--json` paths
  both carry it and the exit code stays driven solely by `failed` (FR-004).
- [ ] T007 [P] In `tests/validation/test_runner.py` add: a stub validator that raises
  `NotEvaluated("…")` is recorded in the `not_evaluated` channel (not `errors[]`); a stub
  that raises a generic `Exception` still lands in `errors[]` as a `ValidatorError`
  (FR-005); `not_evaluated` is sorted by name and a validator appears at most once.
- [ ] T008 [P] In `tests/validation/test_report.py` add: `to_json` carries the
  `not_evaluated[]` sibling key; the green predicate is **False** for a run with a
  non-empty `not_evaluated` (even when `violations == []` / `status == "ok"`) and **True**
  for an evaluated-and-clean run; the human `render` prints the `not evaluated:` section
  instead of the clean line when the channel is non-empty.

**Checkpoint**: the channel exists end-to-end and is empty (no validator raises yet); the
full suite still passes byte-for-byte (FR-012 baseline holds).

---

## Phase 3: User Story 1 — A dormant validator can no longer read as green (Priority: P1) 🎯 MVP

**Goal**: `focalization` migrates **all four** "no usable narrative voice" early returns
from `[]` to `raise NotEvaluated(reason)`, each with a distinct English reason, so the
DEBT-004 dormant-green blind spot is closed (FR-008).

**Independent Test**: Point `validate --json` at a fixture whose constitution lacks (or
`[PENDING]`-holds) the voice declaration; assert `focalization` is in `not_evaluated[]`
with a reason, is NOT in `errors[]`, and the green predicate is **False**; a constitution
declaring a usable first/third person stays evaluated (in neither channel).

- [ ] T009 [US1] In `src/bookwright/validation/validators/focalization.py` route the four
  early-return causes to `raise NotEvaluated(reason)` (FR-008): (i) no constitution and
  (ii) no parseable voice declaration → `"the constitution does not declare a narrative
  voice"`; (iii) the voice is still a `[PENDING]` placeholder (reuse iteration-039's
  `is_placeholder`) → `"the narrative-voice declaration is still unanswered ([PENDING])"`;
  (iv) a declaration present but resolving no grammatical person → `"the narrative-voice
  declaration names no grammatical person (neither first nor third)"`. A usable first/third
  person stays **evaluated**. Verify the enumeration is exhaustive over every early `[]`
  return so none keeps reading green. Stays `triples=()`, graph-free, LLM-free (FR-015).
- [ ] T010 [US1] In `tests/validation/test_focalization.py` add (additive — no oracle edits,
  SC-003) one case per reason (no constitution; unparseable declaration; `[PENDING]`
  placeholder; no-person declaration) asserting `NotEvaluated` is raised with the exact
  reason, plus a case asserting a usable third-person declaration on a clean manuscript
  returns `[]` (evaluated, green) and a first-person declaration likewise — never raises.
- [ ] T011 [US1] Add a source-only fixture `tests/fixtures/tiny-undeclared-voice/`
  (manifest + `bible/` + a manuscript with prose + a constitution whose
  `- **Voz narrativa**:` is the `[PENDING: …]` placeholder a fresh `bookwright init`
  emits) plus its oracle, registered like the existing `tiny-*` fixtures in
  `tests/fixtures/`. No `graph.ttl` committed (derived cache, Constitution I).
- [ ] T012 [US1] Add `tests/e2e/test_tri_valued_validation.py`: `graph build` → `validate
  --json` over `tiny-undeclared-voice`; assert `focalization` is in `not_evaluated[]` with
  a reason, absent from `errors[]`, and the green predicate evaluates to **False** while
  `violations` may be empty (SC-001/SC-002).

**Checkpoint**: US1 fully functional — the dormant-validator-reads-green defect is
reproducibly closed and independently testable.

---

## Phase 4: User Story 2 — Validators that had nothing to inspect say so, without hiding a finding (Priority: P1)

**Goal**: `setting_continuity` and `character_presence` migrate to `NotEvaluated` **only**
on their true no-input preconditions, never by suppressing a producible finding (FR-009).

**Independent Test**: (a) populated bible + empty manuscript → `setting_continuity` in
`not_evaluated[]`, `character_presence` **evaluated** still emitting its `error`-level
orphan findings byte-for-byte; (b) empty project (no roster, no prose) →
`character_presence` in `not_evaluated[]`. Neither run reads as clean.

- [ ] T013 [P] [US2] In `src/bookwright/validation/validators/setting_continuity.py`
  `raise NotEvaluated("the manuscript is empty")` when the manuscript has no readable
  prose (its sole input); stay evaluated when prose is present. Stays `triples=()`,
  graph-free (FR-015).
- [ ] T014 [P] [US2] In `src/bookwright/validation/validators/character_presence.py`
  `raise NotEvaluated("there is no manuscript prose and no bible character roster to
  cross-check")` **only** when BOTH inputs are empty (no prose AND empty roster). An empty
  manuscript with a non-empty roster MUST stay **evaluated** and emit its `error`-level
  orphan findings byte-for-byte unchanged (the rule that protects the gate, FR-004/FR-012).
- [ ] T015 [P] [US2] In `tests/validation/test_setting_continuity.py` add (additive):
  empty manuscript → `NotEvaluated` raised with `"the manuscript is empty"`; manuscript
  with prose → evaluated (existing findings unchanged).
- [ ] T016 [P] [US2] In `tests/validation/test_character_presence.py` add (additive): no
  prose AND empty roster → `NotEvaluated` with the no-inputs reason; empty manuscript +
  non-empty roster → **evaluated**, orphan `error` findings produced byte-for-byte
  unchanged (asserts the gate is preserved, FR-012).

**Checkpoint**: US1 + US2 both work independently; every "could-not-look" path across the
three migrated validators is honest, with zero finding regression.

---

## Phase 5: User Story 3 — The third state is visible everywhere green is read (Priority: P2)

**Goal**: Propagate the not-evaluated dimension into `bookwright status` derived state and
into `next_actions`, and surface the raw facts in the status-reading skill resource
(FR-010/FR-011/SC-004). Depends on US1/US2 producing the state.

**Independent Test**: `status --json` on a not-evaluated-`focalization` fixture exposes
`state.validation.not_evaluated[]` and a `next_actions` step naming the focalization
remedy; a fully-evaluated project shows neither (no false positives).

- [ ] T017 [US3] In `src/bookwright/status/model.py` add
  `not_evaluated: tuple[NotEvaluatedResult, ...]` to `ValidationSummary`; `to_payload`
  emits `"not_evaluated": [r.to_json() for r in self.not_evaluated]` under
  `state.validation` (additive, always present — empty list on the degraded path).
- [ ] T018 [US3] In `src/bookwright/status/queries.py` make `validation_summary` consume
  the runner's 4-tuple and fill `ValidationSummary.not_evaluated`; the degraded/no-build
  path constructs an empty `ValidationSummary` so the key is never missing. (depends on
  T004, T017)
- [ ] T019 [US3] In `src/bookwright/status/rules.py` add a static `_REMEDIES` map
  (`focalization` → "declare the narrative voice in the constitution"; `setting_continuity`
  → "add manuscript prose to validate"; `character_presence` → "add a bible character
  roster and manuscript prose") and a pure `Rule("activate_dormant_validators", …)` that
  applies iff `state.validation.not_evaluated` is non-empty, building one `Action`
  (`skill="bookwright-continuity"`, count-driven `reason` via `_plural`, `prompt`
  enumerating each dormant validator's remedy). Place it after `review_continuity`, before
  `define_focus` in `RULES`. (depends on T017)
- [ ] T020 [US3] In `src/bookwright/resources/commands/bookwright-research.md` extend the
  startup `bookwright status --json` step (Spanish, "Próximos pasos / Punto de partida")
  to list the **raw** `state.validation.not_evaluated` facts among the raw facts it
  surfaces — read from `state.validation`, NOT from `next_actions[]` (FR-011), mirroring
  the existing `state.open_questions` / `state.unresolved_anchors` enumeration.
- [ ] T021 [P] [US3] In `tests/status/test_rules.py` add: with a not-evaluated
  `focalization` in the validation summary, `activate_dormant_validators` yields a
  `next_actions` step whose prompt names the focalization remedy (SC-004); with an empty
  `not_evaluated`, the rule produces nothing (no false positives).
- [ ] T022 [P] [US3] In `tests/status/test_queries.py` add: `validation_summary` surfaces
  `not_evaluated` from the runner 4-tuple into `state.validation`, sorted by name; the
  degraded path still emits an empty `not_evaluated` list.

**Checkpoint**: all three stories independently functional; the third state is visible in
every surface where green is read.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: prove the feature end-to-end and re-assert the quality bar and parity.

- [ ] T023 Run the quickstart scenarios (`specs/040-tri-valued-validator-result/quickstart.md`):
  Scenario 1 (dormant focalization not green), Scenario 2 (a/b/c), Scenario 3 (status +
  next_actions), and the gate/exit-code check (`validate; echo exit=$?` → 0 on a
  solely-not-evaluated run, yet not reported clean).
- [ ] T024 Verify parity (SC-003 / FR-012): run `uv run pytest` and confirm **zero** edits
  to pre-existing `Violation` finding oracles — every migrated trigger fired only on inputs
  that already returned `[]`. Then run the four gates: `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥ 80 % coverage);
  confirm every changed/new source file stays ≤ 500 lines (SC-005).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1, T001)**: no code dependency; MUST precede all code (plan § 7.3).
- **Foundational (Phase 2, T002–T008)**: depends on T001; BLOCKS all user stories.
- **User Stories (Phases 3–5)**: all depend on Foundational completion.
  - US1 (P1) and US2 (P1) are independent of each other and may proceed in parallel.
  - US3 (P2) depends conceptually on US1/US2 producing not-evaluated state, but its code
    (status model/queries/rules) only depends on the Foundational types (T002/T004); its
    tests are most meaningful once US1 exists.
- **Polish (Phase 6)**: depends on all desired stories being complete.

### Key intra-task dependencies

- T003 needs T002 (exports the new names).
- T004 needs T002 (`NotEvaluatedResult`). T005/T006 need T004 (4-tuple).
- T007/T008 need T004/T005. 
- T009 (US1) needs Foundational; uses iteration-039 `is_placeholder`.
- T012 (US1 E2E) needs T009 + T011 (fixture).
- T018 (US3 queries) needs T004 + T017. T019 (US3 rule) needs T017.

### Parallel Opportunities

- T007 ∥ T008 (different test files).
- US1 (T009–T012) ∥ US2 (T013–T016) once Foundational is done.
- Within US2: T013 ∥ T014 (different validators); T015 ∥ T016 (different test files).
- Within US3: T021 ∥ T022 (different test files).

---

## Parallel Example: User Story 2

```bash
# Both validators are different files — migrate in parallel:
Task: "setting_continuity.py → NotEvaluated on empty manuscript (T013)"
Task: "character_presence.py → NotEvaluated only when prose AND roster empty (T014)"

# Their tests are different files — write in parallel:
Task: "test_setting_continuity.py additive not-evaluated cases (T015)"
Task: "test_character_presence.py additive cases incl. gate-preserved orphans (T016)"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 (T001 — design contract).
2. Phase 2 (T002–T008 — shared plumbing; channel empty, suite green).
3. Phase 3 (T009–T012 — focalization migrates; the DEBT-004 dormant-green defect closes).
4. **STOP and VALIDATE**: the dormant-validator blind spot (the entire point of the
   iteration) is demonstrably closed via the E2E fixture.

### Incremental Delivery

1. Foundational → channel exists, zero behavior change.
2. + US1 → dormant focalization is honest (MVP, SC-001/SC-002).
3. + US2 → empty-input validators are honest, gate still protected (FR-012).
4. + US3 → the third state reaches `status` + `next_actions` + the skill (SC-004).
5. Polish → quickstart proven, four gates green, parity verified.

---

## Notes

- [P] = different files, no incomplete-task dependency.
- SC-003 is load-bearing: **no** existing finding oracle may be edited — only additive
  not-evaluated assertions. Every migrated trigger must fire only on inputs that already
  returned `[]`; verify empirically before adding any oracle.
- Prose validators stay graph-free, LLM-free, `triples=()`, frozen ontology untouched
  (Principle X / FR-015).
- After this merges, `v0.5.0` releases ONCE for iterations 039 + 040 via the
  `bookwright-release` skill (separate manual step, not part of this iteration's code).
