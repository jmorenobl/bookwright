---
description: "Task list for iteration 050 — partial-evaluation contract"
---

# Tasks: a partial-evaluation contract — a validator may emit findings **and** abstain in the same run; `focalization` recovers its first-person-break check under limited-third

**Input**: Design documents from `/specs/050-partial-evaluation-contract/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/validator-protocol.md ✅, quickstart.md ✅

**Tests**: REQUIRED for this iteration — FR-013 (focalization both-at-once), FR-014
(retarget limited-third tests), FR-015 (runner-level synthetic form-(c) test) all
mandate tests. Test tasks are therefore included and are not optional here.

**Organization**: Tasks are grouped by user story (US1/US2/US3 from spec.md). The
contract types (`EvalResult`/`Abstention`) and the runner's three-shape
normalization are **Foundational** — they block all three stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (Setup/Foundational/Polish carry no story label)
- All paths are repo-root-relative; this is a single src-layout project.

## Path Conventions

- Source: `src/bookwright/validation/…`
- Tests: `tests/validation/…`
- Docs/debt: `bookwright-design.md`, `DEBT.md`, `CLAUDE.md` (repo root)

---

## Phase 1: Setup — Contract-before-code (docs & debt, FR-010/FR-011)

**Purpose**: The written contract MUST be updated **before** the code diverges from
it (Constitution I; FR-010). These tasks touch only plain-text docs and are
independent of each other.

- [X] T001 [P] Update `bookwright-design.md` § 13.1 to document the **third** accepted `validate()` return shape: a validator MAY `return EvalResult(violations, not_evaluated)` (form (c), partial) in addition to `return list[Violation]` (a) and `raise NotEvaluated(reason, kind)` (b, the **total**-abstention shortcut). State that the runner normalizes all three into the existing `violations[]` / `not_evaluated[]` channels through one shared name-stamping point, with no new channel/sort/envelope key (FR-002).
- [X] T002 [P] Update `bookwright-design.md` § 13.2 / § 13.5 (focalization sections) and § 20.6.1 (the determinism↔LLM frontier note) to state plainly that under third-person **limited/focalized** voice `focalization` now **runs** the deterministic first-person-break check **and** abstains on head-hopping (`pending_capability`) in the **same** run — the frontier realized; the all-or-nothing suppression (DEBT-019) is gone.
- [X] T003 Remove the **DEBT-019** entry from `DEBT.md` and reconcile the track-A closed-list line that references it to reflect its closure (this iteration is its resolution; git keeps the history) — FR-011 / SC-006. Verify with `grep -c "DEBT-019" DEBT.md` → expected `0`.

**Checkpoint**: The canonical contract and debt ledger describe the partial-evaluation
contract before any code changes.

---

## Phase 2: Foundational — the contract type + runner normalization (BLOCKS all stories)

**Purpose**: `EvalResult`/`Abstention` and the runner's three-shape normalization
are the shared machinery every user story depends on. No story work can begin until
these compile and `mypy --strict` accepts the widened `Validator` Protocol return.

**⚠️ CRITICAL**: T004 → T005 are strictly ordered (runner imports the new types).

- [X] T004 In `src/bookwright/validation/base.py`: add frozen `Abstention(reason: str, kind: NotEvaluatedKind = NotEvaluatedKind.missing_input)` (the returned-not-raised sibling of `NotEvaluated`, carrying ONLY `(reason, kind)` — same closed vocabulary and same default; the validator never names itself, C2/C3) and frozen `EvalResult(violations: list[Violation], not_evaluated: list[Abstention])` (form (c) carrier). Widen the `Validator` Protocol: `def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation] | EvalResult: ...`. Add `"Abstention"` and `"EvalResult"` to `__all__` (sorted into place). `NotEvaluated`/`NotEvaluatedResult`/`NotEvaluatedKind`/`Violation` UNCHANGED. File stays ≤ 500 lines (Principle IV).
- [X] T005 In `src/bookwright/validation/runner.py`: extract the single name-stamping helper `_record(name: str, reason: str, kind: NotEvaluatedKind) -> NotEvaluatedResult` and route BOTH the `except NotEvaluated` path (form (b), behavior unchanged) AND the new form-(c) abstention loop through it (FR-002, C2 — the stamping authority MUST NOT fork). In the main loop add `isinstance(found, EvalResult)` handling: `findings = found.violations`; for each `ab in found.not_evaluated` append `_record(validator.name, ab.reason, ab.kind)`; the `else` bare-`list[Violation]` path (form (a)) is unchanged. Form (c)'s `violations` flow into the **existing** shared dedup-against-`seen` loop and `sort_key`; abstentions merge into the existing `not_evaluated[]` under `not_evaluated_sort_key`. Import `Abstention`, `EvalResult` from `base`. `RunResult` stays the 4-tuple; `sort_key`/`not_evaluated_sort_key` unchanged (C4). File stays ≤ 500 lines.

**Checkpoint**: `uv run mypy --strict` is clean across the widened return union; a
bare-`list[Violation]` validator still satisfies the Protocol (SC-004). Forms (a)
and (b) behave exactly as before. User-story work can now begin.

---

## Phase 3: User Story 1 — the deterministic first-person-break check runs again under a focalized voice (Priority: P1) 🎯 MVP

**Goal**: Under limited-third, `focalization` returns form (c): it runs
`_first_person_breaks` **and** declares the head-hopping `pending_capability`
abstention in the same run — closing DEBT-019.

**Independent Test**: Run `focalization` on a third-person-**limited** project whose
manuscript has a first-person pronoun outside dialogue; assert the result carries
**both** one `focalization` `warning` citing the marker **and** one `not_evaluated`
entry with `kind == pending_capability` (SC-001).

### Tests for User Story 1 (write/adjust FIRST, run empirically per FR-013)

- [X] T006 [US1] In `tests/validation/test_focalization.py`: add a NEW both-at-once case — a third-person-limited constitution + a manuscript with a first-person marker outside dialogue (`Yo no entendía nada.` / `I did not understand.`). Assert the returned `EvalResult` carries **exactly one** `focalization` `warning` finding citing the marker with a `relpath:line` `source`, **and exactly one** `Abstention`/`pending_capability` head-hop entry with the `_HEAD_HOPPING_PENDING` reason (FR-013/SC-001). Verify **empirically** with `uv run pytest` (the surface is what the run emits, not asserted blind).
- [X] T007 [US1] In `tests/validation/test_focalization.py`: retarget the existing limited-third tests (`test_limited_third_abstains_as_capability_gap`, `test_limited_third_with_no_named_focal_abstains_identically`, `test_english_declaration_abstains_under_limited_third`, and the placeholder-replacement wake-up test) from `pytest.raises(NotEvaluated)` to asserting the returned `EvalResult` shape: empty `violations` (these fixtures have no break) + the single head-hop `Abstention(pending_capability)` (FR-014). The English limited-third test that today asserts the first-person break does **not** fire MUST now assert it **does** fire alongside the abstention. The four `missing_input` total-abstention tests still assert `pytest.raises(NotEvaluated)` (UNCHANGED).

### Implementation for User Story 1

- [X] T008 [US1] In `src/bookwright/validation/validators/focalization.py`: at the ONE limited-third site (`focalization.py:101`), replace `raise NotEvaluated(_HEAD_HOPPING_PENDING, kind=NotEvaluatedKind.pending_capability)` with `return EvalResult(self._first_person_breaks(project.manuscript_view()), [Abstention(_HEAD_HOPPING_PENDING, NotEvaluatedKind.pending_capability)])`. Widen the `validate` signature return to `list[Violation] | EvalResult` and import `Abstention`, `EvalResult` from `base`. The four `missing_input` raises, the omniscient `list` path (`return self._first_person_breaks(...)`), the first-person `[]` path, the `_HEAD_HOPPING_PENDING` string, `_first_person_breaks` itself, the name/registration/`triples=()` — all UNTOUCHED (FR-003/FR-006/FR-008). Update the module docstring's DEBT-019 paragraph to state the break check now runs under limited-third. File stays ≤ 500 lines.

**Checkpoint**: US1 tests (T006/T007) pass; `focalization` recovers the deterministic
check under limited-third while still abstaining on head-hopping. DEBT-019 closed.

---

## Phase 4: User Story 2 — every other validator keeps working byte-for-byte; the general contract is proven decoupled from `focalization` (Priority: P1)

**Goal**: The contract is additive — forms (a)/(b) are untouched and the runner's
new form-(c) branch is proven correct **independently** of `focalization` (FR-015).

**Independent Test**: A synthetic validator returning form (c) routes its findings to
`violations[]` (deduped+sorted) and its abstention to `not_evaluated[]` with the
runner-stamped name + kind, appearing in neither `errors[]` nor the abstention
channel for its findings (SC-008).

### Tests for User Story 2

- [X] T009 [US2] In `tests/validation/test_runner.py`: add a synthetic `_Partial` fake validator (mirroring `_Good`/`_Skip`/`_SkipCapability`) whose `validate` returns `EvalResult([Violation(...)], [Abstention("<reason>", NotEvaluatedKind.pending_capability)])`. Add a test asserting: its `Violation` lands in `violations[]` (deduped against `seen`, sorted by `sort_key`); its abstention lands in `not_evaluated[]` as a `NotEvaluatedResult` with `validator == "<fake name>"` (**runner-stamped**, not self-named) and `kind == pending_capability`; the fake appears in `ran`; it appears in **neither** `errors[]` nor (for its finding) the abstention channel (FR-015/SC-008). Also assert the empty-`violations` `EvalResult([], [Abstention(r, k)])` is observationally identical to `raise NotEvaluated(r, k)` (C5 invariant) — both yield one `not_evaluated` entry and zero findings.
- [X] T010 [US2] Confirm the existing `test_runner.py` cases (isolation, dedup, deterministic sort, `not_evaluated` routing, bare-list, sort-and-dedup of `not_evaluated`, kind-stamping) and all non-`focalization` validator tests still pass **unchanged** — forms (a)/(b) are not perturbed by the widened union (FR-007). Run `uv run pytest tests/validation/ -q` and confirm no diff in other validators' behavior.

**Checkpoint**: The general three-shape contract is covered by the runner test
decoupled from `focalization`; every other validator is byte-for-byte unchanged.

---

## Phase 5: User Story 3 — the green predicate and gate are unchanged (Priority: P2)

**Goal**: The head-hopping abstention stays `pending_capability` (does not deny
green, does not trigger the `status` nudge); a first-person `warning` sets
`status = violations` but the error-only CI gate is unaffected. None of 044's
machinery changes — this iteration only **consumes** it (FR-005/SC-005).

**Independent Test**: On a clean focalized fixture the 044 green predicate holds
despite the `pending_capability` entry; on a focalized project with a first-person
break, `status = violations` but the gate (error-only) does not break.

- [X] T011 [US3] Verify (no source change expected) the three focalized shipped fixtures (`tiny-historical`/`tiny-novel`/`tiny-quest`) emit `violations`, `errors`, `not_evaluated`, and `ran` **byte-identical** to the current release — their pinned oracles are unchanged (FR-012/SC-003). Run `uv run pytest tests/ -q -k "validate or fixture or e2e or quest or novel or historical"`. If any oracle diverges, the cause is a regression in T005/T008 (the empty-`violations` form (c) MUST be observationally equal to the old `raise`), NOT an oracle edit — fixtures/oracles MUST NOT be edited.
- [X] T012 [US3] Confirm the 044 green predicate, `NotEvaluatedKind` vocabulary, `not_evaluated[]` serialization, the `status` dormant-validator nudge, and the error-only CI gate are **unchanged** (consumed, not modified): `commands/validate.py` and `status/queries.py` (the two `RunResult` consumers) require NO edits (FR-016). Run `uv run bookwright validate --json` in a focalized fixture and confirm the `pending_capability` entry is present in `not_evaluated[]` and never gates; a clean focalized project stays green (SC-005).

**Checkpoint**: All three stories are independently verified; the correctness
boundary inherited from 044 is preserved.

---

## Phase 6: Polish & Cross-Cutting (gates, agent context)

**Purpose**: Final verification across the whole change and the agent-context pointer.

- [X] T013 Update the `CLAUDE.md` plan pointer / current-state prose if the iteration-050 line needs reconciling (the milestone table row stays for the merge step; this is the in-iteration pointer only).
- [X] T014 Run the full quickstart (`specs/050-partial-evaluation-contract/quickstart.md`) scenarios 1–6 end to end and confirm each expected outcome.
- [X] T015 Run all four gates and the full suite: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥ 80% coverage enforced by `[tool.coverage.report]`). All green (SC-007). Confirm every changed source file is ≤ 500 lines (Principle IV) and the frozen ontology is untouched (Principle X).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1, T001–T003)**: Plain-text docs; no code dependency. Do first (contract-before-code, FR-010). T001/T002 are `[P]`.
- **Foundational (Phase 2, T004–T005)**: BLOCKS all stories. T004 (base.py) → T005 (runner.py imports the new types). Strict order.
- **User Story 1 (Phase 3)**: Depends on Foundational. T006/T007 (tests) before/with T008 (impl).
- **User Story 2 (Phase 4)**: Depends on Foundational. Independent of US1 (different test file, runner-level). T009 → T010.
- **User Story 3 (Phase 5)**: Depends on Foundational + US1 impl (T008) being in place so fixtures resolve. T011/T012 are verification (no expected source change).
- **Polish (Phase 6)**: After all stories. T015 is the final gate.

### User Story Dependencies

- **US1 (P1)** — needs the contract type (T004) and runner branch (T005). The MVP.
- **US2 (P1)** — needs T004/T005; otherwise fully independent of US1 (`test_runner.py`, synthetic fake). Can proceed in parallel with US1.
- **US3 (P2)** — verification; needs T008 in place for the fixtures to exercise the new path. No new source.

### Within Each User Story

- Tests are written/retargeted alongside implementation; for US1 run T006/T007 empirically (FR-013) after T008.
- Foundational (models/contract) before consumers; consumers before verification.

### Parallel Opportunities

- T001, T002 (`[P]`) — independent doc sections.
- After Foundational completes, **US1 (T006–T008)** and **US2 (T009–T010)** can proceed in parallel — different files (`test_focalization.py` / `focalization.py` vs. `test_runner.py`), no shared edits.

---

## Parallel Example

```bash
# Phase 1 docs in parallel:
Task: "Update bookwright-design.md § 13.1 (third return shape)"
Task: "Update bookwright-design.md § 13.2/13.5/20.6.1 (focalization runs break check + abstains)"

# After Foundational (T004/T005), the two P1 stories in parallel:
Task: "US1 — focalization.py limited-third returns EvalResult + focalization tests"
Task: "US2 — test_runner.py synthetic _Partial form-(c) test"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup (contract-before-code docs).
2. Phase 2 Foundational (`EvalResult`/`Abstention` + runner three-shape normalization) — CRITICAL, blocks everything.
3. Phase 3 US1 (`focalization` adopts form (c) + tests).
4. **STOP and VALIDATE**: `uv run pytest tests/validation/test_focalization.py -q` — the both-at-once case passes, DEBT-019 closed.

### Incremental Delivery

1. Setup + Foundational → contract live, `mypy --strict` clean.
2. US1 → focalization recovers the break check (MVP, closes DEBT-019).
3. US2 → general contract proven decoupled (runner synthetic test); back-compat confirmed.
4. US3 → green predicate / gate / fixtures unchanged.
5. Polish → all four gates + quickstart green.

---

## Notes

- `[P]` = different files, no incomplete dependency.
- Scope guardrails (FR-016): ONLY `validation/base.py`, `validation/runner.py`,
  `validation/validators/focalization.py`, the two validation test modules, and the
  design/DEBT/CLAUDE docs change. **No** other validator, command, envelope, or
  `.ttl`. `focalization` stays a prose validator (`triples = ()`, no graph access).
- The empty-`violations` `EvalResult` MUST stay observationally equal to a `raise
  NotEvaluated` of the same `(reason, kind)` — this is what keeps the three focalized
  fixtures byte-identical (FR-012). If an oracle diverges, fix the code, not the oracle.
- No new module, no new dependency (Constitution II); every changed file ≤ 500 lines
  (Principle IV); frozen ontology untouched (Principle X).
