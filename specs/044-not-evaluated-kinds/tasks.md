---
description: "Task list for iteration 044 — not_evaluated kinds (capability-gap vs input-gap)"
---

# Tasks: `not_evaluated` distinguishes a capability-gap from an input-gap; green is reachable again

**Input**: Design documents from `/specs/044-not-evaluated-kinds/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/not-evaluated-kind.md, quickstart.md

**Tests**: INCLUDED. Constitution VIII mandates test discipline (≥ 80 % coverage) and
the plan enumerates the specific test files; every behavior change here is reachable
from synthetic state (SC-004), so test tasks are first-class.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 — the user story the task serves
- Paths are repo-relative; this is a single src-layout package (`src/bookwright/`, `tests/`)

---

## Phase 1: Setup (Contract-before-code — plan § 7.3 / D9)

**Purpose**: Re-document the refined contract in the plain-text design spec **before**
the code diverges from the docs (Principle I, spec Assumption). These edits land first.

- [X] T001 Update `bookwright-design.md` § 13.1 — extend the `NotEvaluated` signature note and the tri-valued result table to record the new `kind` (closed `{missing_input, pending_capability}` vocabulary, `missing_input` default), per data-model.md and contracts/ §1
- [X] T002 Update `bookwright-design.md` § 13.4 — replace the green-predicate quote with the refined form: green ⟺ `status == "ok"` AND no `not_evaluated` entry has `kind == "missing_input"`; note that `pending_capability` entries stay visible but do not deny green (FR-004), and the nudge fires only for `missing_input` (FR-005)

**Checkpoint**: The contract is documented; code may now diverge to match it.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Thread the closed `NotEvaluatedKind` vocabulary through the
`NotEvaluated` → `NotEvaluatedResult` → runner path. **No user story can be tested
until this phase is complete.** Every edit is additive; `missing_input` is the default
so every existing raise/construction is byte-for-byte unchanged (FR-002, SC-007).

- [X] T003 Add `NotEvaluatedKind(StrEnum)` to `src/bookwright/validation/base.py` (after the `Severity` enum, mirroring it) with exactly two members `missing_input = "missing_input"` and `pending_capability = "pending_capability"`; add `NotEvaluatedKind` to `__all__` (data-model.md "NotEvaluatedKind")
- [X] T004 In `src/bookwright/validation/base.py`, add `kind: NotEvaluatedKind = NotEvaluatedKind.missing_input` as the **last** parameter of `NotEvaluated.__init__` and store `self.kind = kind`; update the docstring to mention the kind defaults to `missing_input` (FR-001/FR-002, data-model.md "NotEvaluated")
- [X] T005 In `src/bookwright/validation/base.py`, add `kind: NotEvaluatedKind = NotEvaluatedKind.missing_input` as the **last** field of the frozen `NotEvaluatedResult` dataclass and add `"kind": self.kind.value` as an additive key in its `to_json` (FR-008, SC-007, data-model.md "NotEvaluatedResult")
- [X] T006 In `src/bookwright/validation/runner.py` (~line 69) stamp the kind: change the conscious-skip handler to `not_evaluated.append(NotEvaluatedResult(validator.name, skip.reason, skip.kind))`; the sort by validator name is unchanged (D3)
- [X] T007 In `src/bookwright/validation/validators/character_unknown_mentions.py`, change the raise to `raise NotEvaluated(reason, kind=NotEvaluatedKind.pending_capability)` (reason string byte-unchanged); import `NotEvaluatedKind` from `bookwright.validation.base` (FR-003, data-model.md raise inventory)

**Checkpoint**: The kind flows from the signal into the recorded result and its JSON;
`character_unknown_mentions` is the only `pending_capability` raise; all other raises
default to `missing_input`. User stories can now proceed.

---

## Phase 3: User Story 1 - A flawless project reads as green again (Priority: P1) 🎯 MVP

**Goal**: A project with no error/warning/input-gap reads **green** again — the
permanent `character_unknown_mentions` capability-gap entry stays listed but no longer
denies green, and `status` no longer fires the universal dormant-validator nudge.

**Independent Test**: Run validation/status on `tiny-novel` / `tiny-memoir`; assert the
refined green predicate is `True` while `not_evaluated` carries one `pending_capability`
entry, and `next_actions` carries **no** "activate the dormant validators" action.

### Implementation for User Story 1

- [X] T008 [US1] Refine the green-predicate docstring on `ValidationReport` in `src/bookwright/validation/report.py` (~line 50) to: green ⟺ `status == "ok"` AND no `not_evaluated` entry has `kind == "missing_input"`; note `pending_capability` does not deny green (FR-004, D4)
- [X] T009 [US1] In `src/bookwright/status/rules.py`, refine `_activate_dormant_validators` to consume only the `missing_input` subset: `dormant = [r for r in state.validation.not_evaluated if r.kind is NotEvaluatedKind.missing_input]`; import `NotEvaluatedKind` from `bookwright.validation.base` (FR-005, D7)
- [X] T010 [US1] In `src/bookwright/status/rules.py`, change the `activate_dormant_validators` rule's `applies` predicate to fire only when any `missing_input` entry exists (`applies=lambda s: any(r.kind is NotEvaluatedKind.missing_input for r in s.validation.not_evaluated)`) (FR-005)
- [X] T011 [US1] In `src/bookwright/status/rules.py`, remove the `"character_unknown_mentions"` clause from the `_REMEDIES` dict (the validator is no longer nudged on) (FR-006, D7)
- [X] T012 [US1] Update the oracle `tests/fixtures/tiny-historical/expected-status.md`: the single `not_evaluated` entry gains `kind: pending_capability`; `next_actions` length 4 → 3 (drop the **second** `bookwright-continuity`, the dormant nudge — `review_continuity` stays); `validation.counts` byte-identical (`error: 1, warning: 1, info: 0`); fixture manuscript/bible unchanged. **Also** rewrite the front-matter NOTE comments (the iteration-043 `not_evaluated` note, ~lines 84-103) and the Spanish body prose (the "El bucle, en dos fotogramas" frame that narrates "**cuatro** workstreams" / "`activate_dormant_validators` dispara en todo proyecto", ~lines 119-131) so the oracle stays internally consistent with the now-3 actions and the new `kind` — leave no stale "fires on every project" narration (FR-011, SC-006)

### Tests for User Story 1

- [X] T013 [P] [US1] In `tests/validation/test_report.py`, refine the local `_is_green(payload)` helper to filter `kind == "missing_input"`; add `test_green_predicate_true_for_capability_gap_only_run` (status ok + `pending_capability`-only ⇒ green) (SC-001, D4/D8)
- [X] T014 [P] [US1] In `tests/status/test_rules.py`, add a case asserting the dormant-validator nudge is **suppressed** when the only `not_evaluated` entry is `pending_capability`, and assert the removed `_REMEDIES["character_unknown_mentions"]` clause no longer appears (FR-005/FR-006, SC-002)
- [X] T015 [P] [US1] In `tests/validation/test_runner.py`, assert the runner stamps `kind=pending_capability` onto the `character_unknown_mentions` result and preserves `missing_input` (default) for an input-gap raise (D3)
- [X] T028 [P] [US1] **Automated fixture-level green guard (SC-001, FR-012)** — the synthetic helpers (T013) do not exercise a real clean fixture, and 043's regression escaped CI precisely because nothing asserted green on one. In `tests/e2e/test_tri_valued_validation.py`, add `test_clean_fixture_is_green_under_refined_predicate` parametrized over `tiny-novel` **and** `tiny-memoir`: `graph build` then `validate --json`, assert exit 0, assert the refined `_is_green(payload)` (the kind-filtered helper from T022) is `True`, and assert the only `not_evaluated` entry is `character_unknown_mentions` with `kind == "pending_capability"`. This is the durable regression guard the headline outcome lacked (SC-001/SC-005)
- [X] T029 [P] [US1] **Automated no-nudge guard (SC-002)** — in `tests/commands/test_status.py`, extend the `tiny-novel` clean-project status case (`test_v02_era_project_succeeds_with_empty_research_facts`, or a sibling test) to assert `next_actions` contains **no** `activate_dormant_validators` action: no `bookwright-continuity` entry whose prompt activates dormant validators (the only `not_evaluated` entry is `pending_capability`). Asserts SC-002 over the real fixture, not just synthetic state (T014)

**Checkpoint**: A clean project reads green and produces no dormant-validator nudge;
`tiny-historical` matches its updated oracle; the green/no-nudge outcome is guarded by
an automated fixture-level test (T028/T029). MVP complete.

---

## Phase 4: User Story 2 - The author can tell an actionable gap from a permanent one (Priority: P1)

**Goal**: An input-gap (e.g. `focalization` with no voice declaration) still denies
green and still nudges; a capability-gap is shown but clearly marked as a known
limitation. Both kinds appear in every surface, labeled by a **kind-generic** tag.

**Independent Test**: Construct one synthetic run with an input-conditional entry and
one with the capability-gap; assert only the former denies green and only the former
nudges, while both appear in the human report labeled by their kind.

### Implementation for User Story 2

- [X] T016 [US2] In `src/bookwright/validation/report.py`, add a module-level `_KIND_LABEL: dict[NotEvaluatedKind, str]` map (e.g. `missing_input` → `"input gap"`, `pending_capability` → `"known limitation — no action available yet"`); import `NotEvaluatedKind` (FR-007, D6)
- [X] T017 [US2] In `src/bookwright/validation/report.py` `render`, change the `not evaluated:` section line to `f"  {result.validator} [{_KIND_LABEL[result.kind]}]: {result.reason}"`; leave the line-116 clean-line early-return (`not reported and not self.errors and not self.not_evaluated`) **unchanged** so both kinds stay visible (FR-007/FR-010, D5)

### Tests for User Story 2

- [X] T018 [P] [US2] In `tests/validation/test_report.py`, assert the render labels a `pending_capability` entry with the kind-generic "known limitation" tag and an input-gap entry with the "input gap" tag, the validator-specific reason text still present; assert a capability-gap-only run does **not** print "no violations found" (FR-007/FR-010, SC-003)
- [X] T019 [P] [US2] In `tests/status/test_rules.py`, add the "both kinds at once" edge case: a run with one `missing_input` and one `pending_capability` entry is not green and the nudge prompt names **only** the `missing_input` validator (edge case, SC-004)
- [X] T020 [P] [US2] In `tests/validation/test_character_unknown_mentions.py`, assert the raise carries `kind == NotEvaluatedKind.pending_capability` with its reason string unchanged (FR-003)
- [X] T021 [P] [US2] In `tests/validation/test_focalization.py`, `tests/validation/test_setting_continuity.py`, and `tests/validation/test_character_presence.py`, assert each existing not-evaluated raise keeps the default `kind == NotEvaluatedKind.missing_input` (FR-002)
- [X] T022 [P] [US2] In `tests/e2e/test_tri_valued_validation.py`, refine the e2e `_is_green` helper to filter `kind == "missing_input"`; assert `tiny-undeclared-voice` stays **not green** (its `focalization` gap is `missing_input`) and `status` still nudges to declare the voice (SC-004, D8, quickstart Scenario B)

**Checkpoint**: Input-gaps and capability-gaps are cleanly separated across green, the
nudge, and the human report.

---

## Phase 5: User Story 3 - Tooling consumers can read the category from the contract (Priority: P2)

**Goal**: Machine consumers of `validate --json` and the `status` payload read the
category as a first-class additive `kind` field, no pre-existing field renamed/retyped.

**Independent Test**: Parse `validate --json` and the `status` payload; assert each
`not_evaluated` entry exposes a `kind` ∈ `{missing_input, pending_capability}` and that
every old key is still present.

### Implementation for User Story 3

- [X] T023 [US3] Verify (no edit expected) `src/bookwright/status/model.py`: `ValidationSummary.to_payload` already serializes each entry via `r.to_json()`, so `kind` flows into `state.validation.not_evaluated[]` automatically once T005 lands; confirm `not_evaluated` field type is unchanged (D7, plan § Phase 0 item 6)

### Tests for User Story 3

- [X] T024 [P] [US3] In `tests/validation/test_report.py`, add `test_to_json_not_evaluated_carries_kind`: each `not_evaluated[]` element of `validate --json` includes `kind` alongside the unchanged `validator` and `reason`, and no pre-existing key changed name/type (FR-008, SC-007)
- [X] T025 [P] [US3] In `tests/commands/test_status.py`, assert `state.validation.not_evaluated[]` in the status payload carries `kind` for each entry (additive), with all prior keys intact (FR-008, SC-003/SC-007)

**Checkpoint**: Both JSON surfaces expose the additive `kind` field; consumers no longer
re-derive the category from the reason string.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the whole change against the quickstart and the four CI gates.

- [X] T026 Run the quickstart scenarios (`specs/044-not-evaluated-kinds/quickstart.md` A–E) against `tiny-novel`/`tiny-memoir` (green), `tiny-undeclared-voice` (not green, still nudges), and confirm the gate exit code is unchanged for every fixture (SC-005)
- [X] T027 Run the four gates and confirm green: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥ 80 % coverage) (SC-008)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No code dependencies — contract docs land first (plan § 7.3).
- **Foundational (Phase 2)**: Depends on nothing in code; **BLOCKS all user stories** (T008–T025 all consume `NotEvaluatedKind` / the `kind` field).
- **User Stories (Phase 3–5)**: All depend on Phase 2 completion.
  - US1 (P1) and US2 (P1) both touch `report.py` and `rules.py` — see within-story notes.
  - US3 (P2) is largely verification + tests; independent of US1/US2 once Phase 2 is done.
- **Polish (Phase 6)**: Depends on all user stories complete.

### Critical cross-file notes

- `src/bookwright/validation/base.py` is edited by T003 → T004 → T005 **sequentially** (same file).
- `src/bookwright/validation/report.py` is edited by T008 (US1, docstring) then T016/T017 (US2, label + render) — **sequential, same file**; do US1's docstring edit before US2's render edits or coordinate one combined pass.
- `src/bookwright/status/rules.py` is edited by T009/T010/T011 **sequentially** (same file).
- `bookwright-design.md` is edited by T001 → T002 **sequentially** (same file).

### Parallel Opportunities

- T001/T002 are same-file → not parallel; T003–T005 same-file → not parallel.
- Foundational T006 and T007 touch different files and can run in parallel after T003–T005 land.
- All test tasks marked [P] (T013–T015, T018–T022, T024–T025) touch distinct test files and can run in parallel once their implementation tasks land.

---

## Parallel Example: Foundational + US1 tests

```bash
# After base.py edits (T003–T005) land, runner + validator are independent files:
Task: "Stamp kind in src/bookwright/validation/runner.py"            # T006
Task: "Raise pending_capability in .../character_unknown_mentions.py" # T007

# US1 tests across distinct files run together once T008–T012 land:
Task: "Green predicate true for capability-gap in tests/validation/test_report.py"  # T013
Task: "Nudge suppressed for capability-gap in tests/status/test_rules.py"           # T014
Task: "Runner stamps kind in tests/validation/test_runner.py"                       # T015
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 (Setup) → contract documented.
2. Phase 2 (Foundational) → the kind machinery threaded end to end.
3. Phase 3 (US1) → clean project reads green, no universal nudge; `tiny-historical` oracle matches.
4. **STOP and VALIDATE**: `tiny-novel`/`tiny-memoir` green; `next_actions` 4 → 3 on `tiny-historical`.

### Incremental Delivery

1. Setup + Foundational → kind flows to JSON.
2. US1 → reachable green (the headline). MVP.
3. US2 → input-gap vs capability-gap separation, labeled human report.
4. US3 → first-class `kind` field verified across both JSON surfaces.
5. Polish → quickstart + four gates green.

---

## Notes

- [P] = different files, no dependencies on incomplete tasks.
- This iteration is **additive only**: no pre-existing key renamed/retyped (SC-007); prose validators keep `triples=()`; the frozen 17-class ontology is untouched; no new runtime dependency (stdlib `StrEnum` only); every changed file stays ≤ 500 lines.
- Out of scope (do not touch): `character_presence` orphan rule, `io/prose.py`, move 3 itself, the `focalization` head-hopping not-evaluated (iteration 045).
- Commit after each task or logical group; the CI gate is unchanged (only `error` findings gate).
