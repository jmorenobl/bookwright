---
description: "Task list for iteration 053 — focalization first-person-recall honesty + abstention `code` discriminator"
---

# Tasks: Move 3 third dimension, first half — `focalization` first-person-recall honesty + the abstention `code` discriminator

**Input**: Design documents from `/specs/053-move3-first-person-honesty/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: REQUIRED. FR-018 / SC-008 mandate empirical verification via `uv run pytest`; every behavior edit lands with its oracle. Tests are written/updated before (or alongside) the code they pin and must fail first.

**Organization**: Two P1 user stories sit on top of one shared **Foundational** contract (the `code` field). The contract is the blocking prerequisite for both; once it lands, US1 (honesty) and US2 (keying) are independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 (honesty) / US2 (keying); Setup / Foundational / Polish carry no story label
- All paths are repository-relative; this is a single src-layout project (`src/bookwright/`, `tests/`)

---

## Phase 1: Setup

**Purpose**: Confirm the working environment. The branch `053-move3-first-person-honesty` and the `specs/053-*` artifacts already exist.

- [X] T001 Sync the environment and capture the pre-change baseline: `uv sync`, then `uv run pytest -q` (record the current green suite so every later red is attributable to this iteration).

---

## Phase 2: Foundational — the abstention `code` contract (BLOCKING)

**Purpose**: Add the optional `code` discriminator to the two frozen abstention dataclasses and stamp it through the runner's single naming point. **Both user stories depend on this**: US1 needs `code` on `focalization`'s abstentions, US2 keys nudges on it. This is the only cross-cutting plumbing in the iteration.

**⚠️ CRITICAL**: No US1/US2 work can begin until this phase is complete and green.

**Contract**: `contracts/abstention-code.md` (C1–C6), `data-model.md` §§ Entities.

- [X] T002 [P] In `tests/validation/test_base.py`, add tests asserting `Abstention` and `NotEvaluatedResult` each carry `code: str | None` defaulting to `None`, and that `NotEvaluatedResult.to_json()` emits a `code` key (value `None` by default; a set value round-trips). (FR-001/002/005, C6)
- [X] T003 [P] In `tests/validation/test_runner.py` and `tests/validation/test_command.py`, add/extend tests asserting the runner stamps `code` from a form (c) `EvalResult` `Abstention` and leaves `code=None` for a form (b) `raise NotEvaluated`; every serialized `not_evaluated[]` entry carries the `code` key. (FR-003/004/005, C2/C3) — write these to FAIL first.
- [X] T004 [P] In `tests/validation/test_report.py`, add a test that a `pending_capability` `not_evaluated` entry **carrying a `code`** still does not deny GREEN (the 044 predicate is `kind`-only), and update the existing exact key-set assertion at `set(entry) == {"validator", "reason", "kind"}` to `{"validator", "reason", "kind", "code"}` (the additive key, FR-005). (FR-016/FR-005, C5)
- [X] T004a [P] In `tests/commands/test_validate_skipped.py`, update `test_json_skip_entry_serializes_with_kind_keys`: change `set(entry) == {"validator", "reason", "kind"}` to `{"validator", "reason", "kind", "code"}`, assert the ingestion `missing_input` skip entry serializes `code: null` (the raised path is code-less, FR-004/FR-005), and correct the docstring "no new key" to record the additive `code` key. This is the repo-wide sweep of the `not_evaluated[]` wire-shape class (doctrine §4): all three exact key-set assertions (here, T004, T014) move in lockstep. (FR-005/FR-019, C3) — written to FAIL first.
- [X] T005 In `src/bookwright/validation/base.py`, add `code: str | None = None` as the last field of both `Abstention` and `NotEvaluatedResult` (both stay `@dataclass(frozen=True)`); append `"code": self.code` as the last key in `NotEvaluatedResult.to_json()`. Leave the `NotEvaluated` **exception** signature `(reason, kind=missing_input)` untouched (FR-004), and leave `not_evaluated_sort_key` as `(validator, reason)` — `code` is NOT a sort term (FR-005a, C4). (FR-001/002/005)
- [X] T006 In `src/bookwright/validation/runner.py`, give the single `_record` naming point a `code=None` parameter and pass it into `NotEvaluatedResult`; the form (c) `EvalResult` loop passes `abstention.code`, the form (b) `except NotEvaluated` path passes nothing (defaults to `None`). The stamping authority MUST NOT fork; the shared sort literal MUST NOT change. (FR-003/004/005a, C2)
- [X] T007 Confirm `src/bookwright/validation/report.py` is **byte-for-byte unchanged** (the 044 GREEN predicate filters `missing_input` only); make no edit. (FR-016, C5)

**Checkpoint**: `uv run pytest tests/validation/test_base.py tests/validation/test_runner.py tests/validation/test_command.py tests/validation/test_report.py tests/commands/test_validate_skipped.py -q` green. The `code` field exists end-to-end, defaults `None`, serializes additively (`code: null` for the raised ingestion skip), and never degrades green. US1 and US2 can now proceed.

---

## Phase 3: User Story 1 — `focalization` stops faking completeness on first-person recall (Priority: P1) 🎯 MVP

**Goal**: `focalization` declares an honest `pending_capability` first-person-recall `Abstention` (`code="first_person_recall"`) under **both** third-person branches, while the existing head-hopping abstention gains `code="head_hopping"` and the explicit-pronoun `warning`s stay byte-for-byte. Ends the sub-check `[]`-means-clean lie for the first-person dimension.

**Independent Test**: A third-person fixture (limited or non-limited) gains a `not_evaluated` entry `{validator: focalization, kind: pending_capability, code: first_person_recall}`; its explicit-pronoun `warning`s are unchanged; the first-person-voice fixture and the four `missing_input` causes gain no such entry. Verified via `uv run pytest`.

### Tests for User Story 1 (write/extend first — must fail before T010)

- [X] T008 [P] [US1] In `tests/validation/test_focalization.py`, add/extend tests: (a) under 3rd **limited** the `EvalResult` carries **two** abstentions — `code="head_hopping"` AND `code="first_person_recall"`, both `pending_capability` — alongside the `_first_person_breaks` violations; (b) under 3rd **non-limited** it carries exactly **one** abstention (`first_person_recall`) and the bare `list` is now an `EvalResult`; (c) the **first-person** voice branch (`return []`) and the **four** `missing_input` raises gain **no** `first_person_recall` entry; (d) the explicit-pronoun `warning`s (`yo`/`nosotros`/`nosotras`/`i`/`we`) and the regex are byte-for-byte unchanged. (FR-006/007/008/009/010/011, SC-001/SC-003) — written to FAIL first.

### Implementation for User Story 1

- [X] T009 [US1] In `src/bookwright/validation/validators/focalization.py`, define the module constant `_FIRST_PERSON_RECALL_PENDING` ("full first-person recall requires semantic judgment (move 3); the deterministic check only covers the explicit subject pronoun"). (FR-006, data-model § focalization abstention set)
- [X] T010 [US1] In `src/bookwright/validation/validators/focalization.py`, add `code="head_hopping"` to the existing head-hopping `Abstention`, add an `Abstention(_FIRST_PERSON_RECALL_PENDING, kind=pending_capability, code="first_person_recall")` to the 3rd-**limited** `EvalResult`, and wrap the 3rd-**non-limited** bare-`list` return in `EvalResult(_first_person_breaks(...), [Abstention(_FIRST_PERSON_RECALL_PENDING, pending_capability, code="first_person_recall")])`. Leave `_first_person_breaks`, the `_FIRST_PERSON` regex, the dialogue exemption, the first-person `return []` branch, and all four `raise NotEvaluated` `missing_input` sites untouched; `focalization` stays `triples=()`. (FR-006/007/008/009/010/011/014/017)
- [X] T011 [US1] In `tests/e2e/test_tri_valued_validation.py`, update the expected `not_evaluated[]` for the third-person fixtures (e.g. `tiny-novel`): add the `first_person_recall` entry and add the `code` key to every entry (`head_hopping` for the head-hop abstention; `null` for the `missing_input` raises). **Re-key the existing `_EXPECTED_GAPS` assertion** — today `{r["validator"]: r["kind"]}` collapses both `focalization` entries into one key and would silently hide the new `first_person_recall` entry (a false green). Key by `(validator, code)` (or assert the full entry set) so `tiny-novel` carries **two** distinct `focalization` entries (`head_hopping` + `first_person_recall`) and the first-person fixture (`tiny-memoir`) carries **no** `first_person_recall` entry. Third-person fixtures that were GREEN stay GREEN. (FR-019, SC-001/SC-002)

**Checkpoint**: `uv run pytest tests/validation/test_focalization.py tests/e2e/test_tri_valued_validation.py -q` green. Under any third-person voice the recall ceiling is honestly visible; the deterministic warnings are preserved; GREEN where it was GREEN.

---

## Phase 4: User Story 2 — multiple abstentions from one validator stay distinguishable in `status` (Priority: P1)

**Goal**: `status` keys its move-3 nudges on `(validator, code)`, so the 052 head-hopping nudge fires on **only** `code="head_hopping"` and never on the new first-person-recall abstention (nor mis-fires under 3rd-non-limited). To let the code-keyed predicate fire, `character_unknown_mentions` is converted from a raised total abstention (form (b)) to a returned partial abstention (form (c)) so it can carry `code="undeclared_characters"`. **No first-person nudge is added** (that is 054).

**Independent Test**: At the synthetic-state level (`tests/status/test_rules.py`, no disk): a `(focalization, pending_capability, head_hopping)` state fires the head-hop nudge; a `(focalization, pending_capability, first_person_recall)`-alone state and a `(focalization, missing_input)` state fire **no** head-hop nudge; a `(character_unknown_mentions, pending_capability, undeclared_characters)` state fires the 051 nudge; no first-person nudge in any state. Verified via `uv run pytest`.

> **Note**: US2 reads the `code="head_hopping"` value set in US1 (T010), but its keying logic is independently testable at the synthetic-state level (states are constructed directly). It depends only on the Phase 2 contract.

### Tests for User Story 2 (write/extend first — must fail before T015/T016)

- [X] T012 [P] [US2] In `tests/status/test_rules.py`, add the keying cases per contract C3: positive `(focalization, pending_capability, head_hopping)` → head-hop `next_action` present; negative `(focalization, pending_capability, first_person_recall)` **alone** → head-hop `next_action` **absent** AND no first-person `next_action`; negative `(focalization, missing_input)` → no head-hop nudge; `(character_unknown_mentions, pending_capability, undeclared_characters)` → 051 nudge present (byte-identical to 052). (FR-012/013/014/015, SC-004) — written to FAIL first.
- [X] T013 [P] [US2] In `tests/validation/test_character_unknown_mentions.py`, update the expectation from a raised `NotEvaluated` (form (b)) to a returned `EvalResult([], [Abstention(<reason>, pending_capability, code="undeclared_characters")])` (form (c)); assert `reason` and `kind` are unchanged and only the wire `code` moves from `null` to `"undeclared_characters"`. (FR-013) — written to FAIL first.
- [X] T014 [P] [US2] In `tests/commands/test_status.py`, assert `code` surfaces in the `status` payload's `not_evaluated[]` — update the existing exact key-set assertion `set(entry) == {"validator", "reason", "kind"}` to `{"validator", "reason", "kind", "code"}` — and assert the iteration-051 undeclared-character nudge is unchanged. (FR-013/FR-005, SC-004)

### Implementation for User Story 2

- [X] T015 [US2] In `src/bookwright/validation/validators/character_unknown_mentions.py`, convert the single `raise NotEvaluated(<reason>, kind=pending_capability)` to `return EvalResult([], [Abstention(<reason>, kind=pending_capability, code="undeclared_characters")])`. `reason`, `kind`, the `validator`/`reason` sort position are unchanged — the only wire delta is the additive `code` key. (FR-013, data-model § state transition)
- [X] T016 [US2] In `src/bookwright/status/rules.py`, generalize `_judges(validator)` → `_judges(validator, code)` by adding `and r.code == code` to its predicate; re-point `judge_undeclared_characters` to `_judges("character_unknown_mentions", "undeclared_characters")` and `judge_head_hopping` to `_judges("focalization", "head_hopping")`. Add **no** first-person nudge; the rule-table order and every other rule are unchanged; `activate_dormant_validators` stays `missing_input`-only. (FR-012/013/014/015/016, C1/C2)
- [X] T017 [US2] Update the orchestration oracle: in `tests/fixtures/tiny-historical/expected-status.md` add the `first_person_recall` `not_evaluated` entry (now **3** entries) plus the `code` keys, keep `next_actions` length **5** (head-hop nudge still fires; no first-person nudge); reflect the same in `tests/e2e/test_orchestration_workflow.py`. `tiny-historical` stays GREEN. (FR-019, SC-004/SC-005)

**Checkpoint**: `uv run pytest tests/status/test_rules.py tests/validation/test_character_unknown_mentions.py tests/commands/test_status.py tests/e2e/test_orchestration_workflow.py -q` green. Each move-3 nudge keys precisely on its `code`; no nudge mis-fires; GREEN preserved; `next_actions` count stable.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Verify the untouched-but-still-valid seams, reconcile the plain-text record, and pass all four gates.

- [X] T018 [P] Verify-only (no edit): confirm `src/bookwright/status/model.py` (`ValidationSummary.not_evaluated` holds `NotEvaluatedResult` directly) and `src/bookwright/status/queries.py` (`validation_summary` passes the runner output through) carry `code` for free; confirm `src/bookwright/commands/validate.py`'s ingestion-skip `NotEvaluatedResult(...)` positional call is still valid (`code` defaults `None`). (data-model § Status flow, C5)
- [X] T019 [P] Update **DEBT-021** in `DEBT.md` (do NOT remove): record that the honest first-person-recall abstention now exists (053) and that the **judgment** half (the sixth `bookwright-continuity` axis + its nudge, which closes DEBT-021) is deferred to 054. (FR-020, SC-007)
- [X] T020 [P] Reconcile the design/milestone record: reflect the abstention `code` contract addition and the `focalization` first-person-recall honesty in `bookwright-design.md` (§ 13.4/§ 13.5 / § 20.6.1–2 as appropriate), and update `CLAUDE.md` milestone prose + iteration index (add row 053, note the judgment half is 054). Keep Spanish prose in Spanish. (FR-021)
- [X] T021 Run the four CI gates from repo root: `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` — all green, coverage ≥ 80 %. Confirm no `error` finding is born from this change and the dependency set / frozen ontology are untouched. (FR-017/FR-022, SC-006/SC-008)
- [X] T022 Run the quickstart scenarios (`specs/053-move3-first-person-honesty/quickstart.md` §§ 1–5) as a final manual cross-check that the CLI surfaces the `code` keys and `first_person_recall` entry, and that GREEN fixtures stay GREEN.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup. **BLOCKS US1 and US2** — the `code` field must exist before either story can stamp or read it.
- **US1 (Phase 3)** and **US2 (Phase 4)**: both depend only on Foundational. US2's `judge_head_hopping` reads the `code="head_hopping"` value US1 sets (T010), but its keying is independently testable at the synthetic-state level (T012). If run strictly sequentially, do US1 then US2 (priority order, both P1).
- **Polish (Phase 5)**: depends on US1 + US2 complete.

### Within Each Story

- Tests (T002–T004, T008, T012–T014) are written/updated to FAIL before the implementation they pin.
- Foundational: base/runner field (T005/T006) before the validators that use it.
- US1: constant (T009) → focalization edit (T010) → e2e oracle (T011).
- US2: validator conversion (T015) and `_judges` (T016) before the orchestration oracle (T017).

### Parallel Opportunities

- T002, T003, T004, T004a ([P]) — four different test files, written before the contract code.
- Within US2: T012, T013, T014 ([P]) — three different test files.
- Polish: T018, T019, T020 ([P]) — verify-only + two different docs.
- T005 and T006 are NOT parallel (both are the contract's stamping path and T006 reads T005's field); run T005 then T006.

---

## Parallel Example: Phase 2 Foundational tests

```bash
# Author the three failing contract tests together, then land T005/T006:
Task: "test_base.py — code field + default + to_json key"
Task: "test_runner.py + test_command.py — code stamped from form (c), None from form (b)"
Task: "test_report.py — pending_capability with code still GREEN"
```

## Parallel Example: User Story 2 tests

```bash
Task: "test_rules.py — keying by (validator, code); negative first_person_recall-alone & missing_input"
Task: "test_character_unknown_mentions.py — form (b)→(c); reason/kind unchanged"
Task: "test_status.py — code surfaces in payload; 051 nudge unchanged"
```

---

## Implementation Strategy

### MVP scope

The honesty half (US1) is the iteration's headline deliverable, but it cannot ship alone: the moment `focalization` emits a **second** `pending_capability` abstention, the 052 head-hop nudge mis-fires without US2's `code` keying. So the true MVP is **Foundational + US1 + US2 together** — the contract field, the honest abstention, and the precise keying are one indivisible increment (this is why the spec bundles them). Phase 5 reconciles the record and proves the gates.

### Suggested order

1. Phase 1 Setup → baseline green.
2. Phase 2 Foundational → `code` exists end-to-end, green.
3. Phase 3 US1 → honest abstention, deterministic warnings preserved.
4. Phase 4 US2 → precise nudge keying, `character_unknown_mentions` converted.
5. Phase 5 Polish → DEBT-021 + design/milestone reconciliation, four gates.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- Contract-before-code: the `code` field (Phase 2) is doc-anchored in `contracts/abstention-code.md` and lands with its consumer (`_judges`) in the same iteration — not speculative plumbing.
- Byte-identical invariants that MUST hold: `report.py` (T007), the explicit-pronoun regex/`_first_person_breaks` (T010), the `NotEvaluated` exception signature (T005), `not_evaluated_sort_key` (T005/T006).
- No skill change, no new dependency, no `error` born, frozen ontology untouched, every changed file ≤ 500 lines.
- Commit after each task or logical group (the auto-git hooks may offer to commit between phases).
</content>
</invoke>
