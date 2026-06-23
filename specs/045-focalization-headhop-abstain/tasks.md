---
description: "Task list for iteration 045 — focalization head-hopping abstains as a capability-gap"
---

# Tasks: `focalization` head-hopping abstains as a permanent capability-gap

**Input**: Design documents from `/specs/045-focalization-headhop-abstain/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/focalization-validator.md, quickstart.md

**Tests**: INCLUDED — the spec/plan §7.4 explicitly request unit + E2E test changes (FR-016).

**Organization**: Tasks are grouped by the three user stories. The change is local to one
validator (`validators/focalization.py`) plus its contract doc, tests, the pinned oracle,
and `DEBT.md`. US1 is the code change; US2/US3 are properties verified by tests that the US1
edit must preserve.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 (Setup / Foundational / Polish have no story label)

## Path Conventions

Single project, src-layout. Source under `src/bookwright/`, tests under `tests/`, design
docs and `DEBT.md` at repository root.

---

## Phase 1: Setup (Baseline & deletion-safety)

**Purpose**: Establish a green baseline and confirm the deletion is safe before touching code.

- [X] T001 Run `uv run pytest -q` to confirm a green starting point on branch `045-focalization-headhop-abstain`; note the current `tiny-historical` `not_evaluated`/`counts`/`next_actions` values as the diff baseline.
- [X] T002 Confirm zero external consumers of every symbol slated for deletion (FR-007): grep `_head_hopping`, `_INTERIORITY`, `\.focal`, and the `character_names` threading across `src/` and `tests/`; verify all hits are inside `src/bookwright/validation/validators/focalization.py` (or its now-to-be-deleted tests). Record the grep result so the deletion is provably safe.

**Checkpoint**: Baseline captured, deletion confirmed safe.

---

## Phase 2: Foundational (Contract-before-code — BLOCKS the validator edit)

**Purpose**: Constitution I requires the canonical contract to be updated **before** the
code diverges (FR-014), and out-of-scope debt to be recorded in plain text (FR-011/FR-015).
These MUST land before the `focalization.py` edit in Phase 3.

**⚠️ CRITICAL**: Do not edit `focalization.py` until T003 and T004 are done.

- [X] T003 Update `bookwright-design.md`: (a) § 13.2 — annotate the `focalization` row so that under a declared third-person-**limited** voice the validator now **abstains wholly** (`pending_capability`, head-hopping is move 3), and the first-person-break check runs only under third-person **non-limited**; (b) § 13.5 — add a one-line note that the abstention is *whole-validator* (the deterministic first-person-break check no longer runs for the limited-third case — DEBT-019), so the written contract does not over-claim (FR-014, plan §7.3). Keep prose in Spanish (design doc language convention).
- [X] T004 Edit `DEBT.md`: remove the **DEBT-014** entry (FR-011/SC-006 — its honesty half closes here; git keeps history) and confirm a **DEBT-019** entry is present recording that the deterministic first-person-break check no longer runs under a limited-third voice (debt class: validators are all-or-nothing; closed by a partial-evaluation contract or move 3) (FR-015/SC-008). Verify with `grep -c "DEBT-014" DEBT.md` → 0 and `grep -c "DEBT-019" DEBT.md` → ≥1.

**Checkpoint**: Written contract and debt ledger match the intended post-045 behavior; code may now diverge.

---

## Phase 3: User Story 1 — Head-hopping stops dozing in green; the gap becomes visible and honest (Priority: P1) 🎯 MVP

**Goal**: A parseable third-person-limited/focalized voice makes `focalization` raise one
`pending_capability` `not_evaluated` entry instead of running the near-dormant heuristic;
the whole head-hopping-only chain is deleted (zero dead code).

**Independent Test**: Run validation on a project declaring "Tercera persona limitada,
focalizada en X" → `focalization` emits no head-hopping `warning` and exactly one
`not_evaluated` entry with `kind == pending_capability` and the FR-002 reason.

### Tests for User Story 1 (write/adjust FIRST, expect failures before T007)

- [X] T005 [P] [US1] In `tests/validation/test_focalization.py`: **delete** `test_head_hopping_on_non_focal_character_warns` (it exercised the deleted heuristic — FR-016, no retarget), and **add** a unit test asserting a parseable third-limited focal voice raises exactly one `NotEvaluated` with `kind == NotEvaluatedKind.pending_capability` and the verbatim FR-002 reason `head-hopping / interiority attribution requires semantic judgment (move 3); the deterministic heuristic was measured nearly dormant on real prose`; plus an edge-case test that a third-limited voice naming **no** focal character abstains identically.
- [X] T006 [P] [US1] In `tests/validation/test_focalization.py`: **retarget** the two tests that asserted a finding under limited-third to the abstention — `test_english_declaration_parses_equivalently` (declares third-limited focused on Aparici; now must assert `NotEvaluated(kind=pending_capability)`, making the DEBT-019 drop concrete) and `test_replacing_placeholder_with_real_voice_wakes_validator` (the `[PENDING]`→real-voice transition now yields a `pending_capability` abstention, not a head-hopping warning). **Update** the parser tests for `_parse_declaration`'s dropped `character_names` argument and removed `.focal` field: `test_bullet_marker_parses_like_bare_form`, `test_emphasis_run_parses_like_bare_form`, `test_scaffold_shape_parses_to_concrete_values` (drop the `focal == "Elena Vidal"` assertion), `test_english_scaffold_shape_parses`, `test_indented_scaffold_shape_parses`, `test_pending_recognition_boundary`, `test_template_binding`, `test_label_mid_sentence_is_not_a_declaration`, and the module-level `_BARE = _parse_declaration(prose_view(...), _NAMES)` fixture (drop `_NAMES`); keep them asserting `person`/`limited`.

### Implementation for User Story 1

- [X] T007 [US1] Edit `src/bookwright/validation/validators/focalization.py`: under `person == "third"` and `limited`, `raise NotEvaluated(<FR-002 reason>, kind=NotEvaluatedKind.pending_capability)` **before** `_first_person_breaks` runs; the `not limited` third-person branch still returns `self._first_person_breaks(view)` and first-person still returns `[]` (FR-008). **Delete** the whole head-hopping-only chain (FR-007, confirmed by T002): `Focalization._head_hopping`, the module `_INTERIORITY` regex, the `_Declaration.focal` field, the focal-name computation in `_parse_declaration`, `_parse_declaration`'s `character_names` parameter, and the orphaned `character_names = [...]` computation in `validate`. Preserve byte-for-byte: the four `missing_input` raises with their reason strings, the 037 `_PENDING_ONLY` guard (FR-005), `triples=()`, and the single-validator identity/registration (FR-006/FR-012). Confirm the file stays ≤ 500 lines.
- [X] T008 [US1] Run `uv run pytest tests/validation/test_focalization.py -q` and confirm T005/T006 pass; then `uv run mypy --strict` to confirm the dropped parameter/field cause no type errors anywhere.

**Checkpoint**: `focalization` abstains as `pending_capability` under limited-third with zero dead code; unit suite green.

---

## Phase 4: User Story 2 — A clean focalized project stays green and asks for no impossible action (Priority: P1)

**Goal**: The new `focalization` capability-gap entry does not deny green and adds no
`next_action` (it consumes 044's refined predicate/nudge unchanged — FR-009).

**Independent Test**: On a clean third-limited fixture, the green predicate (`status == "ok"`
AND no `not_evaluated` entry has `kind == "missing_input"`) is `True` despite the new entry,
and `status`'s `next_actions` gains no `bookwright-continuity` action for it.

### Tests for User Story 2

- [X] T009 [US2] In `tests/e2e/test_tri_valued_validation.py::test_clean_fixture_is_green_under_refined_predicate`: split the shared `entries == {...}` literal **per fixture** — `tiny-novel` (third-limited) now carries both `character_unknown_mentions` and `focalization` as `pending_capability` and stays **green**; `tiny-memoir` (first-person) carries only `character_unknown_mentions` (SC-002/SC-005). Assert the green predicate holds and no `focalization` `next_action` is added.

**Checkpoint**: Clean focal-voice project verified green with the additive entry; no impossible action surfaced.

---

## Phase 5: User Story 3 — The four input-conditional abstentions keep their actionable meaning (Priority: P2)

**Goal**: Causes (i) no constitution, (ii) no declared voice, (iii) `[PENDING]` placeholder,
(iv) no grammatical person stay `kind == missing_input` with byte-identical reasons — they
keep denying green and firing the dormant-validator nudge (FR-004/SC-003).

**Independent Test**: For each of the four causes, `focalization` raises `not_evaluated` with
`kind == missing_input` (unchanged from 044) and `status` still nudges the author.

### Tests for User Story 3

- [X] T010 [US3] In `tests/validation/test_focalization.py`: confirm the four `missing_input` not-evaluated tests and the live-scaffold `[PENDING]` tests still pass **unchanged** after the T007 edit (reason strings byte-for-byte, `kind == missing_input`); if any only fail due to the dropped `character_names`/`focal` parser surface, fix the call site, not the asserted reason/kind. Also confirm `test_first_person_outside_dialogue_warns`, `test_dialogue_line_is_exempt`, `test_usable_third_person_is_evaluated_and_clean`, `test_usable_first_person_is_evaluated_and_clean`, `test_first_person_locator_is_source_line_over_raw`, and `test_bullet_prefixed_line_stays_dialogue_exempt` (non-limited third / first-person → still evaluate, FR-008) pass unchanged.

**Checkpoint**: The actionable half of `focalization`'s honesty contract is preserved.

---

## Phase 6: Oracle, Polish & Gates

**Purpose**: Correct the one pinned oracle empirically and run the full gate set + quickstart.

- [X] T011 Update `tests/fixtures/tiny-historical/expected-status.md`: add a second `not_evaluated` entry (`validator: focalization`, the FR-002 reason, `kind: pending_capability`), keeping the list **sorted by validator name** (`character_unknown_mentions` then `focalization`); leave `validation.counts` `{error: 1, warning: 1, info: 0}` and `next_actions` length 3 unchanged; update the explanatory prose. Do **not** edit the fixture manuscript/constitution (FR-010/SC-004). Verify with `uv run pytest -k tiny_historical` (or the relevant E2E test), not by hand-computing.
- [X] T012 Confirm nothing else regresses: run `uv run pytest tests/e2e/test_narrative_workflow.py tests/e2e/test_orchestration_workflow.py -q` (tiny-quest third-limited gains the entry and stays green; tiny-memoir/tiny-essay gain none — SC-005).
- [X] T013 Run the full gate set + quickstart Scenario E: `grep -c "DEBT-014" DEBT.md` → 0, `grep -c "DEBT-019" DEBT.md` → ≥1, then `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` (≥80% coverage) all green (SC-006/SC-007/SC-008).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2, T003–T004)**: Contract-before-code — MUST complete before the `focalization.py` edit (T007). Blocks Phase 3 implementation.
- **User Story 1 (Phase 3)**: Depends on Phase 2. The MVP — the code change everything else verifies.
- **User Story 2 (Phase 4)** and **User Story 3 (Phase 5)**: Depend on the T007 code change being in place (their tests assert behavior US1 produces). Can be done in parallel with each other.
- **Polish (Phase 6)**: Depends on US1–US3 being complete (oracle + full-suite verification).

### Within User Story 1

- T005/T006 (test edits) are written first and expected to fail until T007.
- T007 (the validator edit) makes them pass; T008 verifies + type-checks.

### Parallel Opportunities

- T005 and T006 touch the same file (`test_focalization.py`) → **not** mutually parallel; both are `[P]` only relative to T003/T004 (different files). Treat them as sequential edits to one file.
- T003 (design doc) and T004 (`DEBT.md`) are different files → can run in parallel.
- Once T007 lands, T009 (US2) and T010 (US3) touch different files (`test_tri_valued_validation.py` vs `test_focalization.py`) and can proceed in parallel.

## Parallel Example: Phase 2 (Foundational)

```bash
# Different files, no ordering between them:
Task: "T003 Update bookwright-design.md § 13.2 + § 13.5"
Task: "T004 Edit DEBT.md — remove DEBT-014, confirm DEBT-019"
```

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Phase 1 (baseline + deletion-safety grep).
2. Phase 2 (contract-before-code: design doc + DEBT ledger).
3. Phase 3 (US1: delete the heuristic chain, add the `pending_capability` raise; unit tests green).
4. **STOP and VALIDATE**: `focalization` abstains honestly; zero dead code.

### Incremental Delivery

1. MVP (US1) → honest capability-gap, deletion complete.
2. US2 → clean focal project stays green (per-fixture E2E split).
3. US3 → four `missing_input` abstentions preserved.
4. Polish → oracle correction + four gates green.

---

## Notes

- This iteration **consumes** 044 machinery — no edit to the green predicate, `NotEvaluatedKind`, `not_evaluated[]` serialization, the `status` nudge, `_REMEDIES["focalization"]`, or `_KIND_LABEL` (FR-009).
- Known, recorded regression: limited-third abstains the whole run, so `_first_person_breaks` no longer runs for that case — **DEBT-019** (FR-015), not silently dropped.
- Out of scope: move 3 itself, a partial-evaluation contract, `validate` skipped-input propagation (DEBT-018/046), `character_presence`/`character_unknown_mentions` (043).
- `focalization` stays a single validator, stdlib only, `triples=()`, frozen ontology untouched, every changed file ≤ 500 lines.
- Commit after each phase (or logical group); the spec's user stories map 1:1 to phases 3–5 for traceability.
