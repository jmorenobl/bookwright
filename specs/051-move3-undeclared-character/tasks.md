---
description: "Task list for iteration 051 — Move 3 first slice: judge undeclared characters"
---

# Tasks: Move 3 first slice — judge undeclared characters in `bookwright-continuity`

**Input**: Design documents from `/specs/051-move3-undeclared-character/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: This repo enforces test discipline (Constitution VIII). The named oracles
are first-class tasks. Per FR-013 / § 20.6.2 decision 4, the **quality of the LLM
judgment is NOT unit-asserted** — only materialization, lint, bilingual trigger, the
new status `next_action`, and the green-preservation invariant are. All behavior is
verified empirically with `uv run pytest`.

**Organization**: Tasks are grouped by the two P1 user stories. US1 (skill surface)
and US2 (status discoverability) touch disjoint files and are independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` skill surface, `[US2]` status nudge
- Include exact file paths in descriptions

## Path Conventions

Single project: `src/bookwright/`, `tests/` at repository root (per plan.md Structure Decision).

---

## Phase 1: Setup (Shared Baseline)

**Purpose**: Confirm the starting state so every later delta is attributable.

- [ ] T001 Confirm branch `051-move3-undeclared-character` is checked out and the four gates are green at baseline: run `uv run pytest`, `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`; record the pre-change pass so regressions are detectable.

**Checkpoint**: Known-green baseline established.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None. The two user stories ride entirely on existing seams (the packaged
skill body, the `SKILL_DESCRIPTIONS` mirror, the `references/` offload, and the pure
`state → list[Action]` status rule table). No new module, no new dependency, no shared
prerequisite — US1 and US2 touch disjoint files (plan.md Structure Decision).

*No foundational tasks. Both user stories may begin immediately after Setup.*

**Checkpoint**: Foundation ready — US1 and US2 can proceed in parallel.

---

## Phase 3: User Story 1 - Surface a character used but never declared (Priority: P1) 🎯 MVP

**Goal**: Extend `bookwright-continuity` with a **fourth axis** ("open-set mentions /
undeclared characters") that reads the authored person roster from the sheets, scans the
manuscript for proper nouns, and judges which name a *person used in the prose but absent
from `bible/characters/`* — separating real signal (e.g. `Amelia`) from noise
(organizations, place names, vocatives, title words). The CLI stays deterministic; the
judgment is the agent's at runtime.

**Independent Test**: Materialize the skill, confirm the 4th axis is present in
`## Procedimiento` and `## Output`, cites the roster as grounding, passes the lint gate,
and triggers bilingually — all via `uv run pytest` on the resources/integrations oracles.
LLM judgment quality is not asserted.

### Implementation for User Story 1

- [ ] T002 [US1] Add the fourth axis to `## Procedimiento` and `## Output` in `src/bookwright/resources/commands/bookwright-continuity.md`: the agent reads the authored person roster from `bible/characters/*.md` `name:` fields (stating the name comes from the **sheet**, not a graph label — `G1_Character` has no `rdfs:label`), reads `bible/settings|locations|objects` names to know which proper nouns are already declared, scans the manuscript for proper nouns, and judges person-without-a-sheet vs. org/place-name/vocative/title-word. Output reports each undeclared-person mention as one more deviation: manuscript quote + "no entry in `bible/characters/`" (ES/EN) + suggestion. Cite the roster as the grounding (§ 20.6.2 decision 3) and reference `references/golem-character.md`. Preserve the existing three axes; keep the report-only / no-writes statement and the inline `bookwright graph build --json`. Keep the file ≤ 500 lines. (FR-001/002/003/004/005/008)

- [ ] T003 [US1] Widen the frontmatter `description` in `src/bookwright/resources/commands/bookwright-continuity.md` so the skill also triggers on undeclared-character prompts in **both ES and EN** (e.g. "revisa si hay personajes sin declarar / mencionados pero sin ficha", "check for undeclared / unbacked characters"), keeping the three existing concerns and the `post-draft` sibling-disambiguation keyword, staying `< 1024` chars. (FR-006/007)

- [ ] T004 [US1] Mirror the widened `description` **verbatim** into `SKILL_DESCRIPTIONS["bookwright-continuity"]` in `src/bookwright/integrations/descriptions.py` (SC-009 equality gate). Make this edit together with T003 so the source frontmatter and the mirror never diverge.

- [ ] T005 [P] [US1] Extend `src/bookwright/resources/commands/references/golem-character.md` to document that the **person roster is read from the sheets, not from the graph**: `G1_Character` carries no `rdfs:label`; the authored name lives in the sheet's `name:` field and in the URI slug. (FR-005, D2)

- [ ] T006 [US1] Update `tests/resources/test_command_body.py` to assert the 4th-axis content in `bookwright-continuity`'s body (the new axis text inside `## Procedimiento`/`## Output`, the "no entry in `bible/characters/`" report phrasing, the roster grounding), while keeping the existing eight required ES headings, non-empty-Spanish, report-only, and inline-`graph build` assertions green. (depends on T002)

- [ ] T007 [US1] Update `tests/resources/test_command_activation.py` to assert the widened bilingual undeclared-character trigger keywords for `bookwright-continuity` and that the `post-draft` sibling-disambiguation keyword is retained. (depends on T003)

- [ ] T008 [US1] Run the SC-009 mirror + materialization/lint oracles green: `uv run pytest tests/integrations/test_descriptions.py tests/integrations/test_materialize.py tests/integrations/test_skill_capabilities.py` — confirms the verbatim mirror, `description` < 1024, `name` ≤ 64 matching its dir, valid YAML. Fix `descriptions.py`/frontmatter if any drift. (verifies T003/T004/T005; FR-007)

**Checkpoint**: The skill materializes, lints, carries the 4th axis, triggers bilingually — US1 independently testable (SC-001/SC-002).

---

## Phase 4: User Story 2 - Discover *how* to get the semantic judgment (Priority: P1)

**Goal**: `bookwright status` gains **one** informative `next_action` pointing to
`bookwright-continuity` whenever the validation report carries a `not_evaluated` entry
whose **source validator** is `character_unknown_mentions`. Restores the nudge iteration
044 removed — now that running the skill is an actionable remedy — keyed on the abstaining
**source** (not the `pending_capability` kind), and **informative** (never degrades green).

**Independent Test**: `uv run pytest` on `tests/status/test_rules.py`,
`tests/commands/test_status.py`, and the `tiny-historical` oracle: the abstention yields
exactly one continuity judge action while GREEN stays byte-identical; `tiny-novel`/
`tiny-memoir` stay GREEN carrying the same informative nudge.

### Implementation for User Story 2

- [ ] T009 [US2] In `src/bookwright/status/rules.py` add a module-level frozenset of judge source-validator names (today `{"character_unknown_mentions"}`) and a builder `_judge_undeclared_characters(state)` that returns exactly **one** `Action`: `skill="bookwright-continuity"`, a fixed English `prompt` (scan the manuscript for proper nouns, read the authored roster from `bible/characters/` `name:` plus settings/locations/objects, report each person used in the prose with no sheet in `bible/characters/`), and a fixed English `reason` (`character_unknown_mentions` abstained — open-set proper-noun discovery is a capability gap; the skill provides the semantic judgment). Templates are fixed with **no minted data** (byte-identical per state). Keep file ≤ 500 lines. (FR-009, E4)

- [ ] T010 [US2] Register `Rule(name="judge_undeclared_characters", applies=…, build=_judge_undeclared_characters)` in the `RULES` tuple in `src/bookwright/status/rules.py`, positioned **after** `activate_dormant_validators` and **before** `define_focus`. The predicate (`applies`) returns `True` iff any `state.validation.not_evaluated` entry has `validator` in the judge source-set — keyed on the **source validator, NOT** on the `pending_capability` kind (so `focalization`'s head-hopping abstention does not fire it). Do NOT re-add a `character_unknown_mentions` clause to `_REMEDIES`; `activate_dormant_validators` stays `missing_input`-only (iteration 044). (FR-009/FR-011, D3, contract table position)

- [ ] T011 [US2] Update `tests/status/test_rules.py`: (a) add `judge_undeclared_characters` to `_TRIGGER` so `test_every_rule_is_exercised_by_a_synthetic_state` stays exhaustive; (b) add an exact-match test asserting the judge action's `skill`/`prompt`/`reason`; (c) **retarget** `test_capability_gap_only_run_suppresses_the_dormant_nudge` — a `pending_capability` `character_unknown_mentions` entry now **does** produce the `bookwright-continuity` judge action while still producing **no** `activate_dormant_validators` action (rename/repurpose to assert exactly that). Keep `test_removed_character_unknown_mentions_remedy_clause_is_gone` green. (depends on T009/T010)

- [ ] T012 [US2] Update `tests/commands/test_status.py` to assert the new `bookwright-continuity` judge `next_action` appears in the `status --json` envelope on a project carrying the `character_unknown_mentions` `pending_capability` abstention, and that the `--json` envelope shape is otherwise unchanged. (depends on T010)

- [ ] T013 [US2] Update `tests/fixtures/tiny-historical/expected-status.md`: `next_actions.skills` gains a second `bookwright-continuity` (emitted after `review_continuity`); `validation.counts`, the `not_evaluated` entries, and the GREEN status stay **byte-identical**; update the front-matter NOTE prose to explain the added informative nudge. (depends on T010; consumed by `tests/e2e/test_orchestration_workflow.py`)

- [ ] T014 [US2] Confirm the green-preservation invariant green: `uv run pytest tests/status/test_rules.py tests/commands/test_status.py tests/e2e/test_orchestration_workflow.py` — `tiny-historical` carries the nudge and stays GREEN; the flawless controls `tiny-novel`/`tiny-memoir` stay GREEN carrying the same nudge (informative). Also run `tests/status/test_queries.py` to confirm `character_unknown_mentions` is still "ALWAYS dormant" / unchanged. (FR-010/FR-011, SC-003/SC-004/SC-005)

**Checkpoint**: The discoverability loop closes end to end; green predicate byte-for-byte unchanged — US2 independently testable.

---

## Phase 5: Reconciliation & Polish (Cross-Cutting)

**Purpose**: Land the contract-before-code records and prove the whole slice green.

- [ ] T015 [P] Remove `DEBT-013` from `DEBT.md` — this slice is its cure (the skill distinguishes org/place-name from person-without-a-sheet, exactly what DEBT-013 asked, "to close when move 3 lands"). Git retains the history. (FR-014, SC-006)

- [ ] T016 [P] Reconcile `bookwright-design.md`: mark § 20.6.2 **first vertical slice as LANDED** (continuity now answers the `character_unknown_mentions` abstention anchored in the roster); reframe § 13.5 accordingly. Keep edits in Spanish. (FR-015, SC-006)

- [ ] T017 Update `CLAUDE.md`: add iteration index **row 051** and update the milestone prose to record the move-3 first slice (issue #1 track A); keep the SPECKIT-managed block pointing at this plan. (FR-015)

- [ ] T018 Run the full quickstart and all four gates green: `uv run pytest` (≥ 80 % coverage), `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`; then the quickstart.md manual cross-checks (`bookwright validate --json` shows the `character_unknown_mentions` `pending_capability` entry; `bookwright status --json` lists `bookwright-continuity` in `next_actions`; clean fixtures stay green). (SC-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: empty — nothing blocks the stories.
- **User Story 1 (Phase 3)** and **User Story 2 (Phase 4)**: both depend only on Setup;
  they touch disjoint files and may run **fully in parallel**.
- **Reconciliation & Polish (Phase 5)**: depends on US1 + US2 landing (T018 is the final
  green gate over everything).

### User Story Dependencies

- **US1 (P1, skill surface)**: independent — `resources/commands/*`, `descriptions.py`,
  `references/golem-character.md`, and their resources/integrations oracles.
- **US2 (P1, status nudge)**: independent — `status/rules.py`, `test_rules.py`,
  `test_status.py`, the `tiny-historical` oracle. No shared file with US1.

### Within Each User Story

- US1: T002/T003/T004 (skill body + description + mirror) before T006/T007 (body/trigger
  oracles); T005 parallel; T008 verifies.
- US2: T009 (builder + source-set) → T010 (rule registration) → T011/T012/T013 (oracles)
  → T014 verifies.

### Parallel Opportunities

- US1 and US2 run in parallel after Setup (disjoint files).
- T005 `[P]` (reference doc) parallel with T002–T004.
- Phase 5 records T015 `[P]` (DEBT.md) and T016 `[P]` (design.md) parallel with each
  other and with US1/US2 finishing; T017/T018 last.

---

## Parallel Example: the two stories together

```bash
# After T001 (baseline green), run both stories concurrently — disjoint files:
# Story US1 — skill surface:
Task: "Add 4th axis to bookwright-continuity.md (## Procedimiento + ## Output)"        # T002
Task: "Widen description (ES+EN, <1024, keep post-draft)"                              # T003
Task: "Mirror description into integrations/descriptions.py"                            # T004
Task: "Extend references/golem-character.md (roster from sheets, not graph)"            # T005 [P]

# Story US2 — status nudge:
Task: "Add source-set + _judge_undeclared_characters builder in status/rules.py"       # T009
Task: "Register judge_undeclared_characters Rule after activate_dormant_validators"     # T010
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → known-green baseline.
2. Phase 3 US1 → the skill carries the 4th axis, lints, triggers bilingually.
3. **STOP and VALIDATE**: `uv run pytest tests/resources tests/integrations` green.
   This is the headline move-3 capability (the `Amelia` case becomes visible).

### Incremental Delivery

1. Setup → baseline.
2. US1 (skill) → test → the judgment capability exists.
3. US2 (status) → test → the discoverability loop closes (the author finds the skill).
4. Phase 5 → reconcile records (DEBT-013 removed, design/§ 20.6.2 landed, index row 051),
   final four-gate green.

### Notes

- `[P]` tasks = different files, no dependencies.
- The deterministic validator `character_unknown_mentions` is **never touched** (FR-011) —
  no task edits `validation/validators/character_unknown_mentions.py`.
- No new dependency, no ontology change, no LLM in the CLI; green predicate byte-for-byte
  unchanged (FR-010/FR-012). Every changed file stays ≤ 500 lines.
- Commit after each logical group (the auto-git hooks are advisory in this flow).
