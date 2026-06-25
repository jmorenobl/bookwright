---
description: "Task list for iteration 052 — Move 3 second slice: judge head-hopping / broken focalization"
---

# Tasks: Move 3 second slice — judge head-hopping / broken focalization in `bookwright-continuity`

**Input**: Design documents from `/specs/052-move3-head-hopping/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: This repo enforces test discipline (Constitution VIII). The named oracles
are first-class tasks. Per FR-013 / FR-017 / § 20.6.2 decision 4, the **quality of the
LLM judgment is NOT unit-asserted** — only materialization, lint, bilingual trigger, the
new status `next_action` (including the **negative** `missing_input` case), and the
green-preservation invariant are. All behavior is verified empirically with `uv run pytest`.

**Organization**: Tasks are grouped by the two P1 user stories. US1 (skill surface) and
US2 (status discoverability) touch disjoint files and are independently testable. This
slice mirrors iteration 051 in shape; only the judged dimension and the keying
generalization differ.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` skill surface, `[US2]` status nudge
- Include exact file paths in descriptions

## Path Conventions

Single project: `src/bookwright/`, `tests/` at repository root (per plan.md Structure Decision).

---

## Phase 1: Setup (Shared Baseline)

**Purpose**: Confirm the starting state so every later delta is attributable.

- [ ] T001 Confirm branch `052-move3-head-hopping` is checked out and the four gates are green at baseline: run `uv run pytest`, `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`; record the pre-change pass so regressions are detectable.
- [ ] T002 Record the baseline `description` length for `bookwright-continuity` (current 822 chars, ≤ 1024 with ~200 slack per FR-006) so the US1 widening stays within budget: `python3 -c "from bookwright.integrations.descriptions import SKILL_DESCRIPTIONS as d; print(len(d['bookwright-continuity']))"`.

**Checkpoint**: Known-green baseline established; description budget known.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None. Both user stories ride entirely on existing seams (the packaged skill
body, the `SKILL_DESCRIPTIONS` mirror, and the pure `state → list[Action]` status rule
table). No new module, no new dependency, no shared prerequisite — US1 and US2 touch
disjoint files (plan.md Structure Decision). The deterministic validator `focalization`
is **unchanged** — it already declares the head-hopping abstention (iteration 050, FR-013).

*No foundational tasks. Both user stories may begin immediately after Setup.*

**Checkpoint**: Foundation ready — US1 and US2 can proceed in parallel.

---

## Phase 3: User Story 1 - Surface a head-hop the validator could only abstain on (Priority: P1) 🎯 MVP

**Goal**: Extend `bookwright-continuity` with a **fifth axis** ("head-hopping / broken
focalization") that reads the declared voice (proceeding only under third-person
*limited*), reads the focal POV per chapter from `bible/pov-structure.md`, reads the
roster, and judges per chapter whether the prose attributes interiority to a non-focal
character — reporting each head-hop as one more continuity deviation. The widened
bilingual `description` triggers on head-hopping prompts and is mirrored verbatim.

**Independent Test**: Materialize `bookwright-continuity`; confirm the 5th axis is present
in `## Procedimiento` and `## Output`, cites voice + POV calendar + roster as grounding,
documents the absent/`[PENDING]`-calendar grounding-gap clause, lists `bible/pov-structure.md`
under "Archivos a leer", triggers on ES+EN head-hopping prompts, and passes the lint gate.
The LLM judgment quality is **not** asserted (FR-013, § 20.6.2 decision 4).

### Implementation for User Story 1

- [ ] T003 [US1] Extend `## Procedimiento` in `src/bookwright/resources/commands/bookwright-continuity.md`: change "cuatro ejes"/"Cuarto eje" wording to **five axes**, then add the **fifth axis — "head-hopping / saltos de punto de vista / focalización rota"** (FR-001), preserving the existing four axes. The new axis's procedure MUST instruct the agent to: (a) read the declared voice from `bible/constitution.md` ("Voz narrativa: …") and proceed **only** under third-person *limited* / focalized — under omniscient or first person, report nothing for this axis (FR-002 a, Acceptance Scenario 2); (b) read the focal POV per chapter from `bible/pov-structure.md` ("Calendario de POV" section) (FR-002 b); (c) read the character roster (`bible/characters/*.md` `name:`, as the fourth axis does) (FR-002 c); (d) judge per chapter whether the prose attributes interiority (verbs of thinking/feeling/perceiving, interior monologue) to a non-focal character (FR-002 d); (e) when the POV calendar is absent / has no "Calendario de POV" section / is a `[PENDING: …]` placeholder, **report the grounding gap and do NOT guess** the focal POV (FR-002 e, mirrors the iteration-037 `[PENDING]`-voice treatment). Cite the grounding (declared voice + POV calendar + roster) explicitly (FR-003, contract C2). [contract: skill-continuity-axis5 C1/C2]
- [ ] T004 [US1] Extend `## Output` in `src/bookwright/resources/commands/bookwright-continuity.md`: describe the head-hop report shape — each head-hop is **one more deviation** carrying a manuscript **quote**, the phrase naming the **non-focal character's interiority under the focal POV in the chapter** (e.g. "interiority of *Irene* under the POV of *Teo* in *<chapter>*"), and a **suggestion** (FR-004); state it is a **judgment, not an `error`** (no `error` born from this axis, FR-014). [contract: skill-continuity-axis5 C3]
- [ ] T005 [US1] Add `bible/pov-structure.md` (its "Calendario de POV" section) to the `## Archivos a leer` section of `src/bookwright/resources/commands/bookwright-continuity.md` as the newly-read focal-POV-per-chapter source (FR-005, FR-016). Do **NOT** create any new `references/` file — the grounding is inline; `bible/pov-structure.md` is itself the authored source. Confirm `## Archivos a escribir: Ninguno` stays true (read-only / POST-draft, FR-008). [contract: skill-continuity-axis5 C4/C5]
- [ ] T006 [US1] Widen the frontmatter `description` in `src/bookwright/resources/commands/bookwright-continuity.md` so the skill also triggers on head-hopping prompts in **both ES and EN** — e.g. "revisa head-hopping / saltos de punto de vista / focalización rota" and "check for head-hopping / POV breaks" (FR-006) — keeping all existing triggers live (bible coherence, undeclared/unbacked characters, the POST-draft↔PRE-draft `bookwright-analyze` disambiguation) and staying **< 1024 chars**. If the addition would exceed 1024, compress existing axes' trigger phrasing without losing any axis's trigger (per T002 budget). [contract: skill-continuity-axis5 C6]
- [ ] T007 [US1] Mirror the widened `description` **verbatim** into `SKILL_DESCRIPTIONS["bookwright-continuity"]` in `src/bookwright/integrations/descriptions.py:27` (FR-015) — made together with T006 so the source frontmatter and the in-code mirror never diverge. [contract: skill-continuity-axis5 C6]
- [ ] T008 [US1] Update `tests/resources/test_command_body.py`: assert the 5th-axis sections exist in `## Procedimiento` and `## Output`, that the grounding (voice + `bible/pov-structure.md` POV calendar + roster) is cited, the limited-third scoping (omniscient/first-person → nothing) and the grounding-gap clause (absent/`[PENDING]` calendar → report the gap, do not guess) are documented, `bible/pov-structure.md` is listed under "Archivos a leer", and the skill stays read-only ("Archivos a escribir: Ninguno"). Do **not** assert LLM judgment quality (FR-013). [oracle: contract C1–C5]
- [ ] T009 [US1] Update `tests/resources/test_command_activation.py`: assert the widened `description` triggers on ES+EN head-hopping keywords ("head-hopping", "saltos de punto de vista", "POV breaks") **and** that the existing iteration-051 undeclared-character triggers and the four prior axes' triggers still fire (SC-002). [oracle: contract C6]
- [ ] T010 [US1] Confirm the description equality gate `tests/integrations/test_descriptions.py` passes (it does once T006+T007 mirror verbatim) and that materialization/lint stay green for the longer body: run `uv run pytest tests/resources/test_command_body.py tests/resources/test_command_activation.py tests/integrations/test_descriptions.py tests/integrations/test_materialize.py tests/integrations/test_skill_capabilities.py` (FR-007, lint: name ≤ 64 = dir, description ≤ 1024, valid YAML). [contract: skill-continuity-axis5 C7]

**Checkpoint**: US1 complete — the fifth axis is materialized, mirrored, triggers bilingually, and lints. Independently testable per quickstart §1.

---

## Phase 4: User Story 2 - Discover *how* to get the head-hopping judgment (Priority: P1)

**Goal**: `bookwright status` adds **one** informative `next_action` pointing to
`bookwright-continuity` for the head-hopping judgment whenever the report carries a
`(focalization, pending_capability)` abstention — distinct from the 051 undeclared-character
action, never degrading green. The keying mechanism is **generalized**: the name-only
`_JUDGE_SOURCES` frozenset is deleted and replaced by a shared `_judges(validator)`
predicate requiring `validator == <name> AND kind is pending_capability`.

**Independent Test**: Empirically via `uv run pytest`. A `(focalization, pending_capability)`
state produces exactly one new head-hopping continuity action while staying GREEN; a
`(focalization, missing_input)`-only state does **not** (negative case); the 051
`character_unknown_mentions` nudge is byte-identical; green predicate unchanged.

### Implementation for User Story 2

- [ ] T011 [US2] In `src/bookwright/status/rules.py`: **delete** the `_JUDGE_SOURCES: frozenset[str]` constant and its comment block (lines ~155-161), and add a shared predicate factory `_judges(validator: str) -> Callable[[StatusState], bool]` returning `lambda s: any(r.validator == validator and r.kind is NotEvaluatedKind.pending_capability for r in s.validation.not_evaluated)` (doctrine §3 — delete the ill-fitting frozenset, don't guard it; FR-010, contract C1).
- [ ] T012 [US2] In `src/bookwright/status/rules.py`: **retarget** the `judge_undeclared_characters` Rule's `applies` to `_judges("character_unknown_mentions")` — its builder `_judge_undeclared_characters`, prompt, and reason stay **unchanged**; behavior is **byte-identical** (`character_unknown_mentions` always abstains `pending_capability`) (FR-010, contract C2).
- [ ] T013 [US2] In `src/bookwright/status/rules.py`: add a builder `_judge_head_hopping(state)` returning **one** `Action` — `skill="bookwright-continuity"`; a fixed-template head-hopping `prompt` (read the declared narrative voice + the `bible/pov-structure.md` POV calendar + the roster; under limited-third, judge per chapter whether the prose attributes interiority to a non-focal POV character; report each as a deviation); a head-hopping `reason` (focalization abstained on head-hopping under limited-third — the semantic judgment is available via the skill). The prompt/reason MUST be **distinct** from the 051 `_judge_undeclared_characters` action (FR-011, contract C3). `Rule.build` stays one-Rule-one-Action (NOT a list, NOT merged).
- [ ] T014 [US2] In `src/bookwright/status/rules.py`: register `Rule(name="judge_head_hopping", applies=_judges("focalization"), build=_judge_head_hopping)` in the `RULES` tuple **immediately after `judge_undeclared_characters` and before `define_focus`** (FR-009, contract C4), so emitted `next_actions` order is deterministic. Leave `activate_dormant_validators` (`missing_input`-only) and the `bootstrap_graph` short-circuit untouched.
- [ ] T015 [US2] Update `tests/status/test_rules.py`: (a) add `judge_head_hopping` to the `_TRIGGER` mapping with trigger state `make_state(not_evaluated=(_DORMANT_FOCAL_CAP,))` so `test_every_rule_is_exercised_by_a_synthetic_state` stays exhaustive; (b) **RETARGET** `test_focalization_capability_gap_does_not_fire_the_judge_nudge` — it must now assert `(focalization, pending_capability)` fires **exactly one** `bookwright-continuity` head-hopping action (the point of this slice); (c) add an **exact-match** test asserting the head-hopping action's prompt + reason (distinct from the 051 action); (d) add the **negative** test: `(focalization, missing_input)` (`_DORMANT_FOCAL`) fires `activate_dormant_validators` and **NOT** `judge_head_hopping` (SC-004, contract C5); (e) update `test_both_kinds_at_once_*` / priority-order tests for the shifted action counts and the co-fire ordering (contract C7). [oracle: contract C1–C7]
- [ ] T016 [US2] Update `tests/commands/test_status.py`: assert the head-hopping `next_action` appears in the `--json` envelope on a project carrying `(focalization, pending_capability)`, distinct from the 051 undeclared-character action (FR-009/FR-011, SC-003).
- [ ] T017 [US2] Verify the green invariant is byte-identical: the iteration-044 green predicate in `src/bookwright/validation/report.py` (`missing_input`-only filter) is **untouched**; confirm no edit landed under `validation/` (FR-012, FR-013, SC-005/SC-006). Run `git diff --stat src/bookwright/validation/` → expect empty.

**Checkpoint**: US2 complete — the head-hopping nudge fires on `(focalization, pending_capability)`, not on `missing_input`; green preserved; 051 nudge intact. Independently testable per quickstart §2–§3.

---

## Phase 5: Oracle reconciliation (e2e fixture)

**Purpose**: Flip the `tiny-historical` status oracle to record the new 5th action, with
green / counts / abstentions byte-identical. (Depends on US2 — the rule must emit the
action before the oracle records it.)

- [ ] T018 Update `tests/fixtures/tiny-historical/expected-status.md`: the `next_actions` list grows **4 → 5** — a third `bookwright-continuity` entry (the head-hopping nudge) emitted **after** the undeclared-character judge and **before** any focus action; `validation.counts`, the `not_evaluated` entries, and the **GREEN** status stay byte-identical. Update the front-matter NOTE prose accordingly (FR-017, SC-003).
- [ ] T019 Confirm `tests/e2e/test_orchestration_workflow.py` passes (it reads the oracle front-matter; passes once T018 records the 5th action — no test-code change unless it hard-codes a count) and that the `tiny-novel` / `tiny-memoir` green controls stay GREEN: run `uv run pytest tests/e2e/test_orchestration_workflow.py`.

**Checkpoint**: The e2e oracle reflects the 5th action; all status-layer fixtures green.

---

## Phase 6: Contract-before-code reconciliation (design + index)

**Purpose**: Reconcile the canonical records (FR-018). No `DEBT.md` entry is removed.

- [ ] T020 [P] Update `bookwright-design.md`: mark § 20.6.2 **second vertical slice (head-hopping / broken focalization) as LANDED**, and reframe § 13.5 to reflect that move 3's second dimension shipped (the third — 1st-person break / pro-drop recall, DEBT-021 — remains open and needs a new `focalization` abstention). Keep edits in Spanish (language convention).
- [ ] T021 [P] Update `CLAUDE.md`: refresh the milestone prose (current state / v0.5.x track narrative) and add the iteration index **row 052** (move-3 second slice — head-hopping judgment; `bookwright-continuity` 5th axis + `status` `judge_head_hopping` nudge; judgment not gate; green byte-identical; issue #1 track C). Bump the patch-version line per the release convention if recording it here.
- [ ] T022 [P] Confirm **no `DEBT.md` entry is removed** — head-hopping carries no open debt of its own (its honesty was closed by 045/050; its judgment is this slice), and **DEBT-021** (1st-person pro-drop recall) **stays open** (FR-018, SC-007). Run `git diff DEBT.md` → expect empty.
- [ ] T023 [P] Refresh the managed `<!-- SPECKIT START -->…<!-- SPECKIT END -->` block in `CLAUDE.md` to point at this iteration's plan (`specs/052-move3-head-hopping/plan.md`) if not already current (agent-context update, plan.md Phase 1 step 4).

**Checkpoint**: Canonical records reconciled; debt trail intact.

---

## Phase 7: Polish & Gates (Cross-Cutting)

**Purpose**: Prove the whole slice green end to end (SC-008).

- [ ] T024 Run the quickstart validation guide end to end (`specs/052-move3-head-hopping/quickstart.md` §1–§4), including `uv run bookwright status --json --project tests/fixtures/tiny-historical | python3 -m json.tool` → well-formed envelope, three `bookwright-continuity` entries (continuity-errors, undeclared-characters judge, head-hopping judge), project stays GREEN, no LLM invoked by the CLI.
- [ ] T025 Run all four gates: `uv run pytest` (≥ 80 % coverage), `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`. All green (SC-008). Confirm every changed file stays ≤ 500 lines (Principle IV) — `status/rules.py` was 251 lines; the +helper/+rule keeps it well under.

**Checkpoint**: Iteration 052 complete — all gates green, contract reconciled.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: None (no tasks).
- **US1 (Phase 3)** and **US2 (Phase 4)**: Both depend only on Setup; touch **disjoint files** (`resources/commands/bookwright-continuity.md` + `descriptions.py` vs. `status/rules.py`). They can proceed **fully in parallel**.
- **Oracle reconciliation (Phase 5)**: Depends on **US2** (the rule must emit the head-hopping action before the `tiny-historical` oracle records it).
- **Design+index reconciliation (Phase 6)**: Depends on US1+US2 landing (records shipped behavior); its four tasks are mutually `[P]`.
- **Gates (Phase 7)**: Depends on all prior phases.

### User Story Dependencies

- **US1 (P1)** and **US2 (P1)**: Independent of each other — either can ship first; the MVP is US1 (the skill surface restoring the lost head-hop signal). US2 closes the discoverability loop.

### Within Each User Story

- **US1**: body edits (T003–T006) before their mirror (T007) and oracles (T008–T010). T006+T007 are a **paired** edit (source + verbatim mirror) — do them together or the equality gate fails.
- **US2**: the keying generalization (T011) and `judge_undeclared_characters` retarget (T012) before the new builder/rule (T013–T014) before the oracles (T015–T017).

### Parallel Opportunities

- **US1 ∥ US2**: the two stories run concurrently (disjoint files).
- Within Phase 6, T020 / T021 / T022 / T023 are all `[P]` (distinct files: design / CLAUDE.md / DEBT.md / CLAUDE.md-managed-block — sequence T021 & T023 since both touch `CLAUDE.md`).

---

## Parallel Example: US1 ∥ US2

```bash
# Two developers (or two passes) on disjoint files after Setup:
# Developer A — US1 (skill surface):
#   edit src/bookwright/resources/commands/bookwright-continuity.md (T003–T006)
#   edit src/bookwright/integrations/descriptions.py (T007)
#   update tests/resources/*.py (T008–T009)
# Developer B — US2 (status nudge):
#   edit src/bookwright/status/rules.py (T011–T014)
#   update tests/status/test_rules.py + tests/commands/test_status.py (T015–T016)
```

---

## Implementation Strategy

### MVP First (US1)

1. Phase 1: Setup → known-green baseline + description budget.
2. Phase 3: US1 → the fifth axis materializes, mirrors, triggers, lints (restores the lost head-hop signal — the measured *Irene*-under-*Teo* case).
3. **STOP and VALIDATE**: quickstart §1 green.

### Incremental Delivery

1. Setup → baseline.
2. US1 → skill surface (MVP — the judgment capability exists).
3. US2 → discoverability nudge (the author is signposted to it) + oracle reconciliation.
4. Design/index reconciliation + gates → ship.

---

## Notes

- [P] = different files, no dependencies.
- The **LLM judgment quality is NOT unit-asserted** (FR-013, § 20.6.2 decision 4) — only materialization, lint, bilingual trigger, the status `next_action` (incl. the negative `missing_input` case), and green-preservation.
- The deterministic `focalization` validator and **everything under `validation/`** stay **unchanged** (FR-013) — it already declares the head-hopping abstention (iteration 050).
- Green predicate (`validation/report.py`, `missing_input`-only) is **byte-for-byte unchanged** (FR-012); `activate_dormant_validators` stays `missing_input`-only.
- **No `DEBT.md` entry removed** (DEBT-021 stays open); no new dependency (Constitution II); frozen ontology untouched (Principle X); no new validator in `validation/`.
- Every changed file ≤ 500 lines (Principle IV). Commit after each task or logical group.
</content>
</invoke>
