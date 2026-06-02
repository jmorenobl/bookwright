---
description: "Task list for iteration 8 — the 10 Bookwright command source prompts"
---

# Tasks: The 10 Bookwright Command Source Prompts

**Input**: Design documents from `/specs/008-source-commands/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: INCLUDED. The validation suite (FR-030 / contracts/validation.md) is itself a
deliverable of this iteration — the authored documents are the "code" and the
`tests/resources/test_command_*.py` modules are the acceptance gate. Tests here validate
authored Markdown, not Python types.

**Organization**: Tasks are grouped by user story (priority order from spec.md) to enable
independent authoring and validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 / US4 — maps to the spec's user stories
- Every task names an exact file path

## Path Conventions

- Sources: `src/bookwright/resources/commands/<name>.md` + `…/commands/references/<topic>.md`
- Tests: `tests/resources/` (extends the iteration-7 resource-validation suite)
- Bodies are **Spanish** prose; frontmatter keys and the `[PENDING: …]` token are **English**

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the packaged-resource directory tree the sources live in.

- [ ] T001 [P] Create the directories `src/bookwright/resources/commands/` and `src/bookwright/resources/commands/references/`. Confirm the existing `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` already covers `resources/` (no edit expected; flag if it does not).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The test harness extension and the one reference every generative command links. These block clean validation of every story.

**⚠️ CRITICAL**: No story's validation passes until T002 lands; every generative body (US1) links the protocol authored in T003.

- [ ] T002 [P] Extend `tests/resources/helpers.py`: add `COMMANDS_DIR`, `REFERENCES_DIR`, the `EXPECTED_COMMANDS` tuple (the 10 names), plus `GENERATIVE_COMMANDS` (constitution, bible, outline, scenes, draft, synopsis) and `REPORT_ONLY_COMMANDS` (clarify, analyze, continuity, checklist) as the single executable source of truth for command classification (mirrors spec "Command classification"), `command_files()` (the 10 `*.md`, excluding `references/`), `reference_files()` (`references/*.md`), and `approx_tokens(text)` (use `tiktoken.get_encoding("cl100k_base")` if importable, else `ceil(len(text)/4)`). Reuse the existing `_PKG_ROOT` / `read_text` / `looks_spanish` patterns. No new runtime dep.
- [ ] T003 [P] Author `src/bookwright/resources/commands/references/pending-protocol.md` (Spanish prose): the shared `[PENDING: <pregunta>]`-and-continue vs stop-and-ask rule, plus the YAML-quoting caveat for string-typed frontmatter fields (`name: "[PENDING: …]"`). Single source of truth linked by all five generative bodies (FR-013, FR-016, R3).

**Checkpoint**: Harness + shared protocol ready — story authoring can begin.

---

## Phase 3: User Story 1 - The generative pipeline is executable end-to-end (Priority: P1) 🎯 MVP

**Goal**: Six generative command sources (constitution, bible, outline, scenes, draft, synopsis) plus the domain references they cite, so an agent can go from brief → drafted scene.

**Independent Test**: For each of the six, the `.md` exists at `commands/<name>.md`, parses (valid YAML frontmatter, `description` < 1024 chars), has a non-empty body < 5000 tokens naming concrete read/write targets, a numbered procedure, the `[PENDING:…]`-vs-ask rule, and a "Qué NO hacer" section. A human read of `bookwright-constitution.md` confirms zero-ambiguity execution (SC-004).

### Domain references cited by US1 bodies (authored in the earliest story that needs them)

- [ ] T004 [P] [US1] Author `…/commands/references/golem-character.md` — `G1_Character` fields + `name/born/died/features/narrative_roles` frontmatter contract + platonic-vs-narrative distinction (cited by bible, draft).
- [ ] T005 [P] [US1] Author `…/commands/references/golem-relationships.md` — `G4_Social_Relationship` / `G6_Relationship_Role` reified modeling + `relationships.md` container (cited by bible; reused by continuity/US2).
- [ ] T006 [P] [US1] Author `…/commands/references/golem-events-timeline.md` — `G5_Narrative_Event` vs `G3_Psychological_State` + the `timeline.md` `events` container contract (cited by bible; reused by continuity/US2).
- [ ] T007 [P] [US1] Author `…/commands/references/propp-functions.md` — Propp's narrative functions + dramatis personae roles (cited by outline, scenes).
- [ ] T008 [P] [US1] Author `…/commands/references/greimas-actants.md` — Greimas's actantial model (subject/object/sender/receiver/helper/opponent) (cited by outline, scenes).

### Generative command bodies (one file each → all parallel)

- [ ] T009 [P] [US1] Author `…/commands/bookwright-constitution.md` (FR-018): role, all 8 body sections, reads brief + constitution mold, writes `bible/constitution.md`, runs `bookwright graph build --json` inline (FR-017) and consumes the JSON, reports pending fields + activated vocabularies + suggests running `bookwright-clarify` before `bookwright-bible`. Links `references/pending-protocol.md`; states the update-in-place rule (FR-016a). Bilingual `description` (US3).
- [ ] T010 [P] [US1] Author `…/commands/bookwright-bible.md` (FR-019): single-invocation full first pass over the bible set in fixed order (constitution-derived entities first), stamps the iteration-7 molds once per entity, **ensuring `bible/characters/`, `bible/settings/`, `bible/locations/` exist (creating any absent) before stamping** (defensive robustness — the current `init` skeleton ships all three since commit `512fdd5`, but a project may be from an older skeleton or have had a directory removed), writes `bible/characters/*`, `settings/*`, `locations/*`, `timeline.md`, `relationships.md`, `themes.md`, `glossary.md`, `research.md`, `subplots.md`; **populates `pov-structure.md` only when multi-POV, else leaves a brief `POV único — no aplica` note** (the file pre-exists from `init`). Links `references/golem-character.md`, `golem-relationships.md`, `golem-events-timeline.md`, `pending-protocol.md`. Update-in-place + `[PENDING:…]` rules.
- [ ] T011 [P] [US1] Author `…/commands/bookwright-outline.md` (FR-020): reads constitution + bible, writes `outline/arcs.md`, `outline/structure.md`, `outline/synopsis.md`. Links `references/propp-functions.md`, `greimas-actants.md`, `pending-protocol.md`. Update-in-place rule.
- [ ] T012 [P] [US1] Author `…/commands/bookwright-scenes.md` (FR-021): reads outline + bible, writes `outline/scenes.md` with per-scene narrative function, characters present, location, beats. Links `references/propp-functions.md`, `greimas-actants.md`, `pending-protocol.md`. Update-in-place rule.
- [ ] T013 [P] [US1] Author `…/commands/bookwright-draft.md` (FR-022): input positional `<scene_id>` via the neutral `{ARGS}` placeholder (no agent-specific token); reads outline + scene + bible, writes the scene into the correct `manuscript/cap-NN.md` section honoring voice/focalization/constraints. Defines unknown-`<scene_id>` behavior (report and ask, never fabricate). Links `references/pending-protocol.md` (+ `golem-character.md` for voice). Update-in-place rule.
- [ ] T014 [P] [US1] Author `…/commands/bookwright-synopsis.md` (FR-023): reads current project state, updates `outline/synopsis.md` with a short version (250–350 words) and a long version (1000–2000 words) reflecting current state. **Generative: regenerates the short/long blocks each run, preserves human content outside them, marks `[PENDING:…]` where source material is missing rather than inventing plot.** Links `references/pending-protocol.md`. Update-in-place rule.

### Validation modules (format gates over the present command files)

- [ ] T015 [P] [US1] Author `tests/resources/test_command_frontmatter.py` (FR-001..FR-006): exactly the 10 `EXPECTED_COMMANDS` exist (no extras/missing); each parses via `bookwright.io.frontmatter.parse_frontmatter`; `name` present, `== basename`, `< 64` chars; `description` present, non-empty, `< 1024` chars; no `scripts` key; no `handoffs` key. (Depends on T002.)
- [ ] T016 [P] [US1] Author `tests/resources/test_command_body.py` (FR-007..FR-014): body non-empty; all eight required sections detectable by ES heading-keyword match; `helpers.looks_spanish(body)`; generative commands (`helpers.GENERATIVE_COMMANDS` — constitution/bible/outline/scenes/draft/synopsis) carry the update-in-place rule + `[PENDING:` guidance (or link `pending-protocol.md`); report-only commands (`helpers.REPORT_ONLY_COMMANDS` — clarify/analyze/continuity/checklist) carry an explicit "no escribe nada / report-only" statement (data-driven by command classification, so it covers US2 files as they land); `bookwright-constitution` and `bookwright-continuity` contain `bookwright graph build --json`. (Depends on T002.)
- [ ] T017 [P] [US1] Author `tests/resources/test_command_budget.py` (FR-015 / SC-002): for every command body, `helpers.approx_tokens(body) < 5000`. (Depends on T002.)

**Checkpoint**: The MVP generative pipeline is authored and format-gated. `bookwright-constitution.md` is human-readable end-to-end.

---

## Phase 4: User Story 2 - Quality and consistency commands report without mutating (Priority: P2)

**Goal**: Four report-only command sources (clarify, analyze, continuity, checklist) that surface gaps/contradictions and write nothing to the project.

**Independent Test**: For each, the `.md` exists, validates, frames itself **report-only** (names no project write targets, states "no escribe nada"), names the artifacts it reads, and defines the report shape. `bookwright-continuity` additionally runs `bookwright graph build --json`. Covered by the report-only branch of `test_command_body.py` (T016).

- [ ] T018 [P] [US2] Author `…/commands/bookwright-clarify.md` (FR-024): reads any artifact, returns a question list, report-only. `description` disambiguates from `checklist` (open questions ≠ artifact completeness — US3). Defines empty-project behavior ("nada que aclarar / prerequisite missing").
- [ ] T019 [P] [US2] Author `…/commands/bookwright-analyze.md` (FR-025): **pre-draft** cross-artifact consistency over constitution + bible + outline + scenes; report-only. `description` names its pre-draft phase to repel `continuity` (US3). Empty/near-empty project → "prerequisite missing".
- [ ] T020 [P] [US2] Author `…/commands/bookwright-continuity.md` (FR-026): **post-draft** manuscript-vs-bible; runs `bookwright graph build --json` inline (FR-017) and reasons over the graph; reports bible-compliance + character-arc consistency + timeline coherence; report-only. Links `references/golem-relationships.md`, `golem-events-timeline.md`. `description` names its post-draft phase to repel `analyze` (US3).
- [ ] T021 [P] [US2] Author `…/commands/bookwright-checklist.md` (FR-027): input positional `<artifact>` via the neutral `{ARGS}` placeholder; reads one named artifact, reports completeness (all sections present, no unfilled `[PENDING: …]`, no empty placeholders); **treats an explicit `no aplica` (e.g. a single-POV `pov-structure.md`) as complete, not as an empty placeholder**; report-only. Defines unknown-`<artifact>` behavior (report and ask). `description` disambiguates from `clarify` (US3).

**Checkpoint**: All 10 sources exist; the report-only quartet validates green alongside US1.

---

## Phase 5: User Story 3 - Implicit activation is precise across languages (Priority: P1)

**Goal**: Each `description` wins its own intent and loses its sibling's, in Spanish and English. The discriminating signal lives entirely in the frontmatter `description`.

**Independent Test**: The hand-run A/B battery (≥4 scenarios × ES+EN = 8 phrasings) resolves each intended command as the unambiguous top match while the named sibling stays silent (SC-003), backstopped by the keyword test.

- [ ] T022 [P] [US3] Author `tests/resources/test_command_activation.py` (SC-003 backstop): each `description` contains ≥1 ES trigger and ≥1 EN trigger; the four sibling pairs each carry their disambiguating keyword (constitution↔bible "before/después", analyze↔continuity "pre-draft/post-draft", clarify↔checklist "dudas/completitud", and the bible-not-premature signal). (Depends on T002.)
- [ ] T023 [US3] Audit and refine all 10 `description` strings (frontmatter of T009–T014, T018–T021) for bilingual triggers + sibling disambiguation per research R4, until `test_command_activation.py` passes. (Depends on all 10 bodies + T022.)
- [ ] T024 [US3] Run the SC-003 hand A/B activation battery — the four US3 scenarios in both ES and EN (8 phrasings) — and record the result (intended command top-matches, named sibling silent). (Depends on T023.)

**Checkpoint**: 8/8 activation phrasings resolve correctly; no sibling over-triggers.

---

## Phase 6: User Story 4 - Heavy domain context is offloaded to references (Priority: P3)

**Goal**: Prove the progressive-disclosure property — bodies link `references/` rather than inlining domain depth, every body stays under budget, and no citation dangles.

**Independent Test**: `references/` exists and is non-empty; every `references/…md` path cited across the 10 bodies resolves to a shipped file (FR-029 / SC-005); every body < 5000 tokens (US4 acceptance).

- [ ] T025 [P] [US4] Author `tests/resources/test_command_references.py` (FR-028/FR-029/SC-005): `references/` dir exists and is non-empty; regex-collect every `references/<file>.md` cited across the 10 bodies and assert each resolves to a shipped file (hard gate); soft-assert every shipped reference is cited by ≥1 body (no orphan). (Depends on T002 + references existing.)
- [ ] T026 [US4] Verify the offload property across all 10 bodies: confirm domain depth lives in `references/` (not inlined) and that `approx_tokens(body) < 5000` with headroom (target ≤ ~3500); move any over-budget domain prose into the appropriate `references/<topic>.md`. (Depends on all bodies + references.)

**Checkpoint**: 0 dangling references; 0 orphan references; every body within budget.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final gates, scope guard, and the human acceptance read.

- [ ] T027 [P] Out-of-scope guard (FR-031 / SC-007): add an assertion (in `test_command_frontmatter.py` or a small `test_command_scope.py`) that `commands/` contains only `.md` files — no `SKILL.md`, no helper `.py`; and confirm by `git diff` inspection that nothing was written under `.claude/skills/` or `.agents/skills/`.
- [ ] T028 Run the full gate green: `uv run pytest tests/resources/ -q` (SC-001/SC-006), then `uv run ruff check && uv run ruff format --check` and `uv run mypy --strict src tests` over `helpers.py` + the new test modules. (Depends on all prior phases.)
- [ ] T029 SC-004 acceptance read: applying the executability rubric in `contracts/command-source.md`, read `bookwright-constitution.md` end-to-end and spot-check `bookwright-continuity.md`, confirming a competent agent could execute each against a fresh project with no ambiguity.
- [ ] T030 Run the quickstart.md author-and-validate loop and confirm the Definition of Done (10/10 sources pass, every body < 5000 tokens, every description < 1024 chars, 0 dangling references, 0 out-of-scope artifacts).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: after Setup. T002 blocks all test modules; T003 (pending-protocol) is linked by every generative body.
- **US1 (Phase 3, P1)**: after Foundational. The MVP.
- **US2 (Phase 4, P2)**: after Foundational. `continuity` reuses references from US1 (T005, T006) — author those first or in parallel.
- **US3 (Phase 5, P1)**: after US1 + US2 (audits all 10 descriptions).
- **US4 (Phase 6, P3)**: after all bodies (US1 + US2) and references exist.
- **Polish (Phase 7)**: after all stories.

### Story Independence

- **US1** is self-contained once Foundational lands (its bodies cite only US1 references + the foundational protocol).
- **US2** is independently testable; its only cross-story reuse is two US1 references (`golem-relationships.md`, `golem-events-timeline.md`).
- **US3** operates on the `description` fields produced by US1/US2 — it refines, it does not author new commands.
- **US4** is a verification story over the artifacts US1/US2 produced.

### Within a story

- References before (or parallel with) the bodies that cite them.
- Bodies and their format tests are independent files → parallel.
- Description audit (US3) and offload verification (US4) edit/sweep multiple files → not parallel.

### Parallel Opportunities

- Foundational: T002 ‖ T003.
- US1: all references T004–T008 ‖ all bodies T009–T014 ‖ all test modules T015–T017 (different files; tests need T002).
- US2: all four bodies T018–T021 in parallel.
- Across stories (with capacity): once Foundational is done, US1 and US2 authoring can proceed in parallel; US3/US4 must wait for the bodies.

---

## Parallel Example: User Story 1

```bash
# Author all five domain references together:
Task: "Author references/golem-character.md"
Task: "Author references/golem-relationships.md"
Task: "Author references/golem-events-timeline.md"
Task: "Author references/propp-functions.md"
Task: "Author references/greimas-actants.md"

# Author all six generative command bodies together:
Task: "Author commands/bookwright-constitution.md"
Task: "Author commands/bookwright-bible.md"
Task: "Author commands/bookwright-outline.md"
Task: "Author commands/bookwright-scenes.md"
Task: "Author commands/bookwright-draft.md"
Task: "Author commands/bookwright-synopsis.md"

# Author the three format-gate test modules together (after T002):
Task: "Author tests/resources/test_command_frontmatter.py"
Task: "Author tests/resources/test_command_body.py"
Task: "Author tests/resources/test_command_budget.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + US3 descriptions)

1. Phase 1 Setup → Phase 2 Foundational (T002 harness + T003 protocol).
2. Phase 3 US1: five references + six generative bodies + three format tests.
3. **STOP and VALIDATE**: `uv run pytest tests/resources/test_command_budget.py tests/resources/test_command_body.py -q` over the six; read `bookwright-constitution.md` end-to-end (SC-004).
4. Refine the six descriptions (US3 subset) so the generative pipeline activates cleanly.

The generative pipeline (US1) is the reason the toolkit exists — it is the demoable MVP on its own.

### Incremental Delivery

1. Foundation → US1 (MVP, generative pipeline) → demo.
2. + US2 (report-only quartet) → all 10 sources exist.
3. + US3 (activation precision across all 10, ES+EN) → safe implicit activation.
4. + US4 (offload verification, budget headroom, no dangling references).
5. Polish: full suite green + scope guard + acceptance read.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- Bodies are Spanish; frontmatter keys + `[PENDING: …]` are English; descriptions are bilingual.
- This iteration writes **no** `SKILL.md` and nothing under any `skills_dir` (FR-031) — that is iteration 9.
- Re-running a generative command must be additive (update-in-place); every generative body states this (FR-016a).
- Commit after each logical group; the `after_tasks` git hook will offer to commit this tasks.md.
