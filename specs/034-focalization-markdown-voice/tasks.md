---
description: "Task list for iteration 034 — focalization tolerates markdown-prefixed voice declaration"
---

# Tasks: `focalization` tolerates markdown-prefixed voice declaration

**Input**: Design documents from `/specs/034-focalization-markdown-voice/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/declaration-recognition.md ✅, quickstart.md ✅

**Tests**: Tests are REQUIRED for this iteration — the spec mandates them (FR-007 binding test, Acceptance Scenario 4 marker-by-marker coverage, Constitution VIII ≥ 80 %). Test tasks are therefore included and gate implementation per story.

**Organization**: Tasks are grouped by user story. The behavioral change is a single normalization step in one validator module; US1 is the MVP and the entire shippable defect fix.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every task

## Path Conventions

Single project, src-layout (Constitution II): `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working tree and baseline are sound before touching code. No scaffolding is needed (existing module + test file).

- [ ] T001 Sync the environment and confirm the baseline is green from `main`: run `uv sync`, then `uv run pytest tests/validation/test_focalization.py -q` (must pass) and `uv run pytest tests/e2e/test_orchestration_workflow.py -q` (must pass) — capture the **current** `tiny-historical` `validation.counts` (`{error:1, warning:6}`) as the pre-change baseline for the FR-008 reconciliation in Phase 5.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The single behavioral change every user story depends on — the line-normalization step in `focalization.py`. US1, US2, and US3 all assert against the awakened parser, so this MUST land before any story's tests can pass.

⚠️ **CRITICAL**: No user story work can be validated until this phase is complete.

- [ ] T002 In `src/bookwright/validation/validators/focalization.py`, add a module-level normalization helper (e.g. `_normalize_declaration_line`) that, given a single candidate line, strips **one** line-leading bullet/blockquote marker drawn from `-`, `*`, `+`, `>` plus surrounding whitespace, then strips the named emphasis markers (`**`, `*`, `_`) **independently** on each side of the label region (no balance guard, per spec clarification / FR-002). Leave the person/limited/focal body-extraction (`_THIRD`, `_FIRST`, `_LIMITED`, focal scan) completely untouched (FR-006). Keep `focalization.py` ≤ 500 lines.
- [ ] T003 In the same file, rework recognition so `_parse_declaration` (`focalization.py:129`) matches the label against the **normalized** candidate line(s) rather than anchoring `_DECLARATION` (`focalization.py:24`) at raw line-start. Preserve: bilingual case-insensitive label `voz narrativa|narrative voice`, the colon-delimited `body` capture, first-match-wins ordering (R3), and the `None`/no-match → `None` return (R2/R4). The parsed `_Declaration` for `- **Voz narrativa**: B` MUST be byte-identical to the bare `Voz narrativa: B` form (R1 parity). Emit no new label synonyms (no false widening). No graph triples, no ontology change (`triples=()`, FR-010 / Principle X).

**Checkpoint**: The parser now recognizes the scaffold shape. Verify quickly with an ad-hoc `uv run python -c "..."` against `_parse_declaration("- **Voz narrativa**: Tercera persona limitada, centrada en Elena Vidal", ["Elena Vidal"])` returning `person="third", limited=True, focal="Elena Vidal"` before moving on.

---

## Phase 3: User Story 1 — The scaffold's own voice declaration wakes the validator (Priority: P1) 🎯 MVP

**Goal**: `focalization` parses the scaffold's `- **Voz narrativa**: …` shape identically to the bare form and fires its third-person rules — the validator is no longer dormant on the format its own scaffold emits.

**Independent Test**: Author a constitution with the scaffold's exact voice line plus a manuscript with a first-person break; run `focalization`; confirm it now produces the expected finding(s) where before it produced none.

### Tests for User Story 1

- [ ] T004 [P] [US1] In `tests/validation/test_focalization.py`, add marker-by-marker recognition tests (Acceptance Scenario 4 / FR-001 / FR-002): one assertion per bullet marker (`-`, `*`, `+`, `>`) and one per emphasis run (`*…*`, `**…**`, `_…_`) wrapping the label, each asserting the parsed `_Declaration` equals the bare `Voz narrativa: B` form (contract rows C2–C8, C10 single-sided). Use the module-internal `_parse_declaration` for unit precision.
- [ ] T005 [P] [US1] In `tests/validation/test_focalization.py`, add the scaffold combined-shape test (FR-003 / FR-004, contract C9): `- **Voz narrativa**: Tercera persona limitada, centrada en Elena Vidal` with `Elena Vidal` in `character_names` parses to `person="third", limited=True, focal="Elena Vidal"`. Add the English scaffold-shape test (FR / SC-002, contract C11) `- **Narrative voice**: third person limited, focused on X`. Add an indented-form test (contract C12).
- [ ] T006 [P] [US1] In `tests/validation/test_focalization.py`, add an end-to-end-through-`validate` test: a constitution whose voice line is the scaffold shape (`- **Voz narrativa**: tercera persona …`) plus a manuscript with a first-person break outside dialogue produces the first-person warning (validator awake, Acceptance Scenario 2). Assert the emitted violation(s) carry `triples == ()` (FR-010 / Principle X — directly proving no graph change, not just inferring it from untouched `.ttl` files).

### Implementation for User Story 1

- [ ] T007 [US1] Run `uv run pytest tests/validation/test_focalization.py -q` and confirm T004–T006 pass against the Phase 2 change and **all pre-existing tests still pass unchanged** (FR-006). If any new test fails, fix the normalization/recognition in `focalization.py` (not the frozen body-extraction).

**Checkpoint**: US1 is independently testable and green — the MVP defect fix is complete.

---

## Phase 4: User Story 2 — Template and parser stay bound (Priority: P1)

**Goal**: A test reads the **live** scaffold constitution template's narrative-voice line and asserts the parser accepts it, so template and parser cannot silently diverge again.

**Independent Test**: Load the narrative-voice line from the packaged scaffold template and assert the parser returns a non-`None` declaration; mutate the template's voice-line shape and the test fails.

### Tests for User Story 2

- [ ] T008 [P] [US2] In `tests/validation/test_focalization.py`, add a `template_binding` test (FR-007 / SC-004): read the packaged `src/bookwright/resources/project/bible/constitution.md.j2` via `importlib.resources` (per plan Technical Context), extract its narrative-voice line (shape `- **Voz narrativa**: [PENDING: …]`, contract §"Template-binding"), feed it to `_parse_declaration`, and assert the result is **not `None`** (recognition; per N3 `person` may be `None` for the `[PENDING:…]` body). Add a comment noting that mangling the template's voice line (e.g. removing the colon) MUST fail this test.

### Implementation for User Story 2

- [ ] T009 [US2] Run `uv run pytest tests/validation/test_focalization.py -k template_binding -q` (green), then locally sanity-check the guard per quickstart Scenario B: temporarily break the template's voice line, confirm the test fails, and **revert** the template (`constitution.md.j2` is read-only for this iteration — never committed-modified).

**Checkpoint**: US2 green — the durable anti-drift binding is in place.

---

## Phase 5: User Story 3 — The no-declaration edge case stays intact (Priority: P2)

**Goal**: Loosening the parser must not turn an absent declaration (or a markdown-prefixed line naming no person) into a false positive — zero findings stay zero.

**Independent Test**: A constitution with no narrative-voice declaration, and separately a markdown-prefixed line declaring neither first nor third person, both yield zero `focalization` findings.

### Tests for User Story 3

- [ ] T010 [P] [US3] In `tests/validation/test_focalization.py`, confirm `test_no_parsable_declaration_yields_nothing` still passes, and add a `pending`/none-person test (FR-005 / SC-003, contract N3): a markdown-prefixed voice line whose body names no recognizable person (e.g. the scaffold's `- **Voz narrativa**: [PENDING: …]`) yields zero findings even with first-person prose present. Add the no-label-mid-sentence non-match case (contract N4).

### Implementation for User Story 3

- [ ] T011 [US3] Run `uv run pytest tests/validation/test_focalization.py -k "no_parsable or pending" -q` (green). No source change expected — this re-proves the guardrail; if it fails, the Phase 2 normalization over-widened and must be tightened.

**Checkpoint**: All three user stories green in isolation.

---

## Phase 6: Polish & Cross-Cutting — fixture reconciliation, debt, gates (FR-008 / FR-009 / SC-005 / SC-006)

**Purpose**: Reconcile the whole fixture suite to the **awake** validator honestly, remove the cancelled debt, and confirm all four gates pass. These touch shared oracle/debt artifacts and run after every story is green.

- [ ] T012 Build `tiny-historical` and read the **real** awake `focalization` warning output to determine its new project-wide `validation.counts.warning` total — do NOT back-fit to the old `{error:1, warning:6}`. Use e.g. `uv run pytest tests/e2e/test_orchestration_workflow.py -q` to surface the actual-vs-oracle diff, or build the fixture and inspect `status`. Record the new warning total (error stays 1).
- [ ] T013 Update `tests/fixtures/tiny-historical/expected-status.md` to the awake count: the `counts:` block (`error: 1`, `warning: <new total>` at lines ~60–62) **and** every prose statement of the project-wide count — the `# NOTE ON validation.counts` header (lines ~13–15) and the `{error: 1, warning: 6, info: 0}` prose at line ~87 — reconciled honestly to the new total. Do not leave any prose pinned to the old dormant `6`.
- [ ] T014 [P] Verify the other voice-bearing fixtures need no oracle edit (FR-008): `tiny-novel` (no oracle — `validate` must still exit 0 with warnings allowed), `tiny-quest` (`expected-narrative.md` / `test_narrative_workflow.py` scoped to `validator == "narrative_structure"`), `tiny-essay` / `tiny-memoir` (first person → no focalization rule fires → zero findings), and `tiny-historical/expected-findings.md` (read only for `factual_anchor`-scoped values by `test_research_workflow.py`; reconcile any project-wide count stated in its prose, otherwise leave untouched). Make any honest prose reconciliation found; do not suppress warnings.
- [ ] T015 [P] Remove the `DEBT-004` entry from `DEBT.md` (FR-009 / SC-006) and reconcile its cross-references: update the DEBT-006 `Por qué se difiere` line that reads "clase distinta (UX de errores) a DEBT-004/005" to "a DEBT-005" so it no longer points at the deleted entry. Confirm `grep -c "DEBT-004" DEBT.md` prints `0`.
- [ ] T016 Run the affected E2E suites green: `uv run pytest tests/e2e/test_orchestration_workflow.py tests/e2e/test_narrative_workflow.py tests/e2e/test_research_workflow.py -q`. `test_orchestration_workflow.py` must now match the reconciled `tiny-historical` counts; the narrative/research suites must be unaffected.
- [ ] T017 Run all four gates (SC-005): `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, and `uv run pytest` (full suite, ≥ 80 % coverage single-sourced in `[tool.coverage.report]`). All MUST pass. Fix any lint/type/coverage gap before declaring done.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first to fix the baseline.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS all user stories** — T002→T003 are the behavioral change every story asserts against.
- **User Stories (Phases 3–5)**: All depend on Phase 2. Independent of each other once Phase 2 lands (they touch only `tests/validation/test_focalization.py`, additively). Recommended order P1 (US1) → P1 (US2) → P2 (US3).
- **Polish (Phase 6)**: Depends on all user stories being green (the awake count read in T012 is only meaningful once recognition is correct).

### User Story Dependencies

- **US1 (P1)**: Foundational only. The MVP.
- **US2 (P1)**: Foundational only. Independent of US1.
- **US3 (P2)**: Foundational only. Independent of US1/US2 (re-proves the no-false-positive guardrail).

### Within Each Story

- Test tasks marked `[P]` add disjoint test functions to the same file additively and can be authored together; the per-story "run" task (T007/T009/T011) follows them.

### Parallel Opportunities

- T002 and T003 are sequential (same function, T003 builds on T002's helper).
- Test-authoring tasks across stories — T004, T005, T006 (US1), T008 (US2), T010 (US3) — are all `[P]`: they add independent test functions to `test_focalization.py` and depend only on Phase 2. They can be written in one pass after T003.
- T014 and T015 are `[P]` (different files: fixtures vs `DEBT.md`).

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 (T001) → Phase 2 (T002–T003) → Phase 3 (T004–T007).
2. **STOP and validate**: the scaffold shape now wakes the validator — the entire shippable defect fix. This is independently demonstrable.

### Incremental Delivery

1. Add US2 (T008–T009) — the anti-drift binding test (durability).
2. Add US3 (T010–T011) — re-prove the edge-case guardrail.
3. Phase 6 (T012–T017) — reconcile fixtures honestly, delete DEBT-004, green all four gates. Ships as `v0.4.2`.

### Notes

- No GOLEM/ontology/graph change (Principle X): the validator emits `Violation`s with `triples=()`.
- `constitution.md.j2` is **read, not edited** — it is the binding test's fixture of truth.
- Read the awake `tiny-historical` count from the validator (T012); never back-fit the oracle to the old dormant value (FR-008).
