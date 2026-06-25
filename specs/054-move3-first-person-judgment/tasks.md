---
description: "Task list for iteration 054 — move-3 third dimension, judgment half (first-person break); closes DEBT-021"
---

# Tasks: Move 3 third dimension, second half (judgment) — judge first-person breaks in `bookwright-continuity`; close DEBT-021

**Input**: Design documents from `/specs/054-move3-first-person-judgment/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md, contracts/ (`skill-sixth-axis.md`, `status-nudge.md`), quickstart.md

**Tests**: Test tasks ARE included — the spec mandates empirical verification via `uv run pytest` (FR-017, SC-002..SC-005) and oracle updates. The *quality* of the LLM judgment is deliberately NOT unit-asserted (FR-017); only materialization, lint, trigger, the keyed nudge, and preserved green are tested.

**Organization**: Tasks are grouped by the two P1 user stories from spec.md so each is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 (skill 6th axis) or US2 (status nudge); shared/records tasks carry no story label
- Exact file paths are included in every task

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repository root.

---

## Phase 1: Setup (baseline confirmation — no code)

**Purpose**: Confirm the 053 contract this slice rides on is in place and capture the description headroom before editing. There is no new scaffolding — the `code` discriminator and `_judges(validator, code)` already ship (FR-013).

- [ ] T001 Confirm the green baseline: `uv run pytest -q` passes on the iteration branch before any edit (so later red is attributable to this slice).
- [ ] T002 Measure the description headroom: `uv run python -c "from bookwright.integrations.descriptions import SKILL_DESCRIPTIONS as D; print(len(D['bookwright-continuity']))"` — record the value (expected **1000**); the folded edit MUST stay **≤ 1024** (quickstart §1).
- [ ] T003 Confirm the 053 contract exists and stays untouched: verify `_judges("focalization", "first_person_recall")` is callable in `src/bookwright/status/rules.py` and that `focalization` already emits `Abstention(_FIRST_PERSON_RECALL_PENDING, pending_capability, code="first_person_recall")` — record `git diff --stat -- src/bookwright/validation/` MUST stay empty through the whole iteration (FR-013, quickstart §5).

**Checkpoint**: Baseline green, headroom known, contract confirmed — implementation can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None. This slice has no shared infrastructure to build — the contract plumbing (`code`, `_judges`) landed in 053. US1 (skill) and US2 (status) are independent and may proceed in parallel after Phase 1.

*(intentionally empty — proceed directly to the user stories)*

---

## Phase 3: User Story 1 — The author surfaces a first-person voice slip the validator could only abstain on (Priority: P1) 🎯 MVP

**Goal**: `bookwright-continuity` gains a **sixth axis** ("1st-person break / voice slip") that judges, under any declared third-person voice (limited OR non-limited), whether the prose slides into first person — including the pro-drop verbal morphology the deterministic check cannot see — grounded ONLY in the declared narrative voice (`bible/constitution.md`), adding on top of (never suppressing) `focalization`'s explicit-pronoun `warning`s.

**Independent Test**: Materialize the skill, confirm the 6th axis is present in `## Procedimiento` and `## Output`, cites the declared voice as grounding, carries the exact deviation phrasing, and passes the lint gate (≤ 1024). Verified by `tests/resources/test_command_body.py`, `test_command_activation.py`, and the lint/materialize gates.

### Tests for User Story 1 (write FIRST, ensure they FAIL before implementation) ⚠️

- [ ] T004 [P] [US1] In `tests/resources/test_command_body.py`, add `test_continuity_carries_the_sixth_first_person_axis`, mirroring `test_continuity_carries_the_fifth_head_hopping_axis`: assert the 6th axis is present in `## Procedimiento` AND `## Output`, names the first-person / voice-slip judgment, cites the declared voice (`bible/constitution.md`) as grounding, and carries the exact deviation phrasing "first-person voice under a narration declared in third person" / "voz de 1ª persona bajo una narración declarada en 3ª" (contract `skill-sixth-axis.md` C1/C2; FR-017). Do NOT assert LLM output quality.
- [ ] T005 [P] [US1] In `tests/resources/test_command_activation.py`, add/extend assertions that the folded 1st-person trigger fires in BOTH ES ("revisa rupturas de voz / persona narrativa") and EN ("check for voice / narrative-person breaks"), AND that the iteration-051 (4th, undeclared-character) and iteration-052 (5th, head-hopping) triggers still fire (SC-002, FR-006).

### Implementation for User Story 1

- [ ] T006 [US1] In `src/bookwright/resources/commands/bookwright-continuity.md`, add the **sixth** numbered axis to `## Procedimiento`, mirroring the 5th (head-hopping) axis shape (contract `skill-sixth-axis.md` C1): (a) read the declared voice in `bible/constitution.md` and proceed only under declared third person — **limited OR non-limited** (state explicitly it differs from the limited-only 5th axis; under declared first person it does NOT apply — report nothing); (b) walk the manuscript outside dialogue; (c) judge whether the narration slides into first person, **including pro-drop verbal morphology** (`Caminé`, `Me senté`, `Escribí`) the explicit-pronoun check cannot see; (d) on absent / `[PENDING]` / person-less voice, report the grounding gap and do NOT guess. State the grounding is the **declared voice only** — no roster, no POV calendar (FR-002, FR-003). Note it **adds on top of**, never suppresses, `focalization`'s explicit-pronoun `warning`s (FR-005). Update the `## Procedimiento` intro «Revisa cinco ejes…» → **seis** (C1).
- [ ] T007 [US1] In the same file `src/bookwright/resources/commands/bookwright-continuity.md`, add the sixth axis to `## Output` (contract C2): report each first-person slip as one more deviation — manuscript quote + the phrase "first-person voice under a narration declared in third person" + a suggestion (rewrite in third person, or confirm the voice). Extend the output axis enumeration to include «ruptura de 1ª persona», and restate "es un juicio, no una `error`" (FR-004, FR-014). (Same file as T006 — sequential, not [P].)
- [ ] T008 [US1] In the same file `src/bookwright/resources/commands/bookwright-continuity.md`, add a short note to the existing `bible/constitution.md` entry in `## Archivos a leer` that the declared voice also grounds the 1st-person-break axis (reuse — **no new file**, FR-016); leave roster / POV-calendar entries scoped to the 4th/5th axes; confirm `## Archivos a escribir` / `## Qué NO hacer` stay unchanged (read-only, POST-draft — FR-008, C3/C5). (Same file as T006/T007 — sequential.)
- [ ] T009 [US1] In `src/bookwright/resources/commands/bookwright-continuity.md` front-matter AND in `src/bookwright/integrations/descriptions.py:27` (`SKILL_DESCRIPTIONS["bookwright-continuity"]`), **fold** the 1st-person trigger into the existing 5th-axis voice/focalization phrase WITHOUT growing past 1024 — e.g. widen «head-hopping / saltos de punto de vista / focalización rota» to also name «rupturas de voz / persona narrativa», and the EN twin to cover "voice / narrative-person breaks". Make both edits in the SAME change so they stay **byte-identical**; re-measure with the quickstart §1 one-liner (≤ 1024). Do NOT lose any existing axis's trigger (FR-006, FR-015, C4).

**Checkpoint**: US1 complete — the skill materializes, carries the 6th axis, triggers ES+EN, and passes lint; run `uv run pytest tests/resources tests/integrations -q` green.

---

## Phase 4: User Story 2 — The author discovers how to get the first-person judgment (Priority: P1)

**Goal**: `bookwright status` adds one informative `next_action` pointing to `bookwright-continuity` for the first-person judgment when the report carries `(focalization, pending_capability, first_person_recall)` — keyed precisely on `code`, distinct from the 051/052 nudges, never degrading green.

**Independent Test**: `uv run pytest tests/status/test_rules.py tests/commands/test_status.py -q` — positive (lone first_person_recall → exactly one new action, GREEN), negative/keying (head_hopping-only → no first-person action and vice versa; declared-first-person → no nudge), all-three co-fire in table order.

### Tests for User Story 2 (write FIRST, ensure they FAIL before implementation) ⚠️

- [ ] T010 [P] [US2] In `tests/status/test_rules.py`: **rewrite** `test_first_person_recall_alone_fires_no_judge_nudge` into a POSITIVE test — a lone `(focalization, pending_capability, first_person_recall)` synthetic state yields **exactly one** `bookwright-continuity` first-person action and stays GREEN (contract `status-nudge.md` C1, FR-009, SC-003).
- [ ] T011 [P] [US2] In `tests/status/test_rules.py`: **rewrite** `test_head_hopping_and_recall_together_fire_only_the_head_hopping_judge` into an **all-three co-fire** test — `character_unknown_mentions` + `focalization` head_hopping + `focalization` first_person_recall present → `status` emits all three move-3 actions in table order (undeclared → head-hopping → first-person), distinct prompts, no `activate_dormant_validators` (all `pending_capability`); GREEN (C5, FR-010).
- [ ] T012 [P] [US2] In `tests/status/test_rules.py`: add the NEGATIVE / keying cases (FR-011, SC-004) — (a) a `head_hopping`-only state yields **no** first-person action and the first-person nudge never fires on `head_hopping`; (b) a synthetic state with **no** `first_person_recall` abstention (declared-first-person analogue) gains **no** first-person nudge; (c) a flawless third-person state stays GREEN. Add the `judge_first_person_recall` entry to the `_TRIGGER` dict so every rule is exercised by its own synthetic state.
- [ ] T013 [P] [US2] In `tests/commands/test_status.py`, assert the new first-person `next_action` surfaces through the `--json` envelope on a `(focalization, pending_capability, first_person_recall)` state (contract `status-nudge.md` Verification).

### Implementation for User Story 2

- [ ] T014 [US2] In `src/bookwright/status/rules.py`, add `_judge_first_person_recall(state) -> Action` returning one fixed, byte-identical Action (contract C1): `skill == "bookwright-continuity"`; `prompt` directs reading the declared voice (`bible/constitution.md`) and judging per-passage first-person slides under any third person incl. pro-drop morphology — MUST NOT name the POV calendar or roster; `reason` starts `"focalization abstained on first-person recall"` and names the capability gap (explicit-pronoun-only deterministic check vs. semantic judgment). Distinct from the 051/052 builders.
- [ ] T015 [US2] In `src/bookwright/status/rules.py`, add the `Rule(name="judge_first_person_recall", applies=_judges("focalization", "first_person_recall"), build=_judge_first_person_recall)` to the `RULES` tuple, inserted **immediately after `judge_head_hopping` and before `define_focus`** (contract C2, FR-009). Use the existing `_judges` helper unchanged — do NOT modify `_judges` or the `code` contract (FR-013). (Same file as T014 — sequential.)

**Checkpoint**: US2 complete — `uv run pytest tests/status tests/commands/test_status.py -q` green; green never degraded (FR-012), validation/ still zero-diff.

---

## Phase 5: Polish & Cross-Cutting (oracle, records, gates)

**Purpose**: Reconcile the e2e oracle (co-located prose + YAML), remove the now-complete debt, reconcile the design/milestone records, and run all four gates.

- [ ] T016 In `tests/fixtures/tiny-historical/expected-status.md`, update the **co-located prose + YAML** oracle in ONE consistent edit (FR-017, SC-003): (i) `next_actions` skills list **5 → 6** (a fourth `bookwright-continuity`); (ii) prose «enumera **cinco** workstreams… **tercer** `bookwright-continuity`» → **seis** / a **fourth**, naming the new first-person nudge alongside 051/052; (iii) convergence-frame prose «las acciones `verify`/`continuity` (las **tres**)… `len(next_actions)` **sigue siendo 5**» → **las cuatro** / **6**; (iv) inline `# nudge:` / iteration comments gain the 054 first-person rule. Leaving any of (ii)–(iv) stale is a forbidden inconsistent oracle.
- [ ] T017 Run `uv run pytest tests/e2e/test_orchestration_workflow.py -q` — confirm `tiny-historical` reads `next_actions` length 5 → 6 and stays GREEN; `tiny-novel` / `tiny-memoir` stay GREEN (FR-017, SC-005). (Depends on T016 + US2.)
- [ ] T018 [P] Reconcile `DEBT-021` in `DEBT.md` per the existing closed-debt convention (git keeps history) — the dimension is complete (honesty 053 + judgment 054): (a) remove the **open `### DEBT-021` section** under `## Deuda abierta`; AND (b) in the **Track C — move 3** bullet of the issue-#1 re-disposición closed-debt summary blockquote (the one already recording `~~DEBT-013~~`), **replace** the stale forward-looking sentence "Queda DEBT-021 … plegado con el head-hopping para rebanadas posteriores de move 3" with a struck-through closed record `~~DEBT-021~~ (cerrada en la iteración 054, mitad de juicio — el 6º eje de `bookwright-continuity` + el nudge `judge_first_person_recall`, anclado SOLO en la voz declarada)`, mirroring the `~~DEBT-013~~` entry there. Verify `grep -n "### DEBT-021" DEBT.md` returns nothing (no open section) AND `grep -n "~~DEBT-021~~" DEBT.md` finds the struck-through closed record (FR-018, SC-007). Leaving the line-92 forward reference stale is a forbidden inconsistent record.
- [ ] T019 [P] Reconcile `bookwright-design.md` § 20.6.2 / § 13.5: mark the third move-3 dimension (first-person break) **landed** and the **first move-3 wave complete** (051 + 052 + 053/054); record the 1st-person axis grounds on the **declared voice only** (supersede the older "voz + roster + POV" phrasing — see `research.md` Decision 1). Spanish, per language conventions (FR-018, SC-007).
- [ ] T020 Run `git diff --stat -- src/bookwright/validation/` and confirm it is **empty** (zero diff under `validation/`, FR-013, SC-006); confirm the iteration-044 green predicate in `src/bookwright/validation/report.py` is byte-for-byte unchanged and `activate_dormant_validators` stays `missing_input`-only (FR-012).
- [ ] T021 Run all four gates green (SC-008): `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥ 80 % coverage). Confirm each changed file stays ≤ 500 lines (FR-019).

> Note: the milestone prose / iteration index row 054 in `CLAUDE.md` and `CHANGELOG.md` are reconciled at **release time** by the `bookwright-release` flow (not in this implementation task list), per the merge ritual.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — run first.
- **Foundational (Phase 2)**: empty — no blocker.
- **US1 (Phase 3)** and **US2 (Phase 4)**: both depend only on Phase 1; they touch **disjoint files** (`resources/commands/bookwright-continuity.md` + `descriptions.py` vs. `status/rules.py` + status tests) and can proceed **fully in parallel**.
- **Polish (Phase 5)**: T016/T017 depend on US2 (the nudge must exist for the oracle to be green); T018/T019 (records) are independent; T020/T021 (gates) run last after all code + oracle edits.

### User Story Dependencies

- **US1 (P1)**: independent — skill + description only.
- **US2 (P1)**: independent — status nudge only. (No code dependency on US1; they share only the conceptual contract.)

### Within Each User Story

- Tests (T004–T005 for US1; T010–T013 for US2) written FIRST and confirmed FAILING before implementation.
- US1 implementation T006→T007→T008→T009 are **sequential** (all edit the same `bookwright-continuity.md`; T009 also edits `descriptions.py` in the same logical change).
- US2 implementation T014→T015 are **sequential** (same `status/rules.py`).

### Parallel Opportunities

- US1 and US2 are independent — assign to two workstreams concurrently.
- Within US1: T004 and T005 are [P] (different test files).
- Within US2: T010–T013 are [P] across two test files (T010–T012 in `test_rules.py` are same-file, treat as one [P] group vs. T013 in `test_status.py`).
- In Polish: T018 and T019 are [P] (different record files).

---

## Parallel Example: the two user stories

```bash
# Workstream A — US1 (skill):
#   T004/T005 (tests) → T006→T007→T008→T009 (skill body + description)
# Workstream B — US2 (status), concurrently:
#   T010–T013 (tests) → T014→T015 (rule builder + RULES insertion)
```

---

## Implementation Strategy

### MVP (US1 alone)

US1 (the 6th axis) is the substantive deliverable — it restores the lost signal. Completing US1 alone gives a skill that judges first-person breaks; US2 (the nudge) makes it **discoverable**. Both are P1 and small; ship together.

### Incremental Delivery

1. Phase 1 setup → baseline + headroom confirmed.
2. US1 + US2 in parallel → both test-first, then implement.
3. Phase 5 → reconcile the oracle, remove DEBT-021, reconcile design, run gates.

---

## Notes

- **Zero diff under `validation/`** (FR-013) is a hard invariant — re-check at T003 and T020.
- The skill is LLM-judged prose: do **not** unit-assert judgment quality (FR-017); assert structure, lint, trigger, the keyed nudge, and preserved green.
- The iteration-044 green predicate stays byte-for-byte identical; `activate_dormant_validators` stays `missing_input`-only (FR-012).
- Commit after each logical group; the milestone/index reconciliation in `CLAUDE.md`/`CHANGELOG.md` happens at release time, not here.
