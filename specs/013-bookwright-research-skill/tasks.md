---
description: "Task list — bookwright-research Skill + bible/research/"
---

# Tasks: `bookwright-research` Skill + `bible/research/`

**Input**: Design documents from `/specs/013-bookwright-research-skill/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅,
contracts/ ✅ (`research-block.md`, `research-file-format.md`,
`research-skill.md`), quickstart.md ✅

**Tests**: INCLUDED. Constitution VIII mandates the single-sourced ≥ 80 %
coverage gate and the new `core/_research_block.py` is fully exercised by its
unit suite (SC-007). New tests reuse a **single shared** research fixture
(`tests/fixtures/research.py`) and **extend** iteration-13's graph-build suite
rather than fork parallel copies. Test tasks are required, not optional.

**Organization**: Tasks are grouped by user story (US1 P1, US2 P2, US3 P3) so
each story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1/US2/US3)
- Every task carries an exact file path.

## Path Conventions

Single project, src-layout: `src/bookwright/`, tests at `tests/`. All paths
below are repository-relative.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the iteration-13 dependency is present so the emitted
format has a reader to parse it.

- [X] T001 Verify the parse-target dependency is on `main` and importable: run `uv sync` then `uv run python -c "from bookwright.io.research import map_research; from bookwright.golem.namespaces import RELIABILITY_IRI; print(sorted(RELIABILITY_IRI))"` — confirms `io/research.py` and `RELIABILITY_IRI` (`{alta,media,baja}`) exist before any emitting/validating code is written (plan Dependencies; research.md R4/R5).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: One **single shared** research fixture — the source of truth for
both the US1 format-conformance test and the Polish graph-build test — built by
extending iteration-13's already-shipped fixture rather than forking a parallel
copy (DRY; no duplicate fixture trees).

**⚠️ CRITICAL**: The shared fixture must exist before the conformance and
graph-build tests that read it. Reuse, don't reinvent: iteration-13's
`scaffold_project` (today's `with_research=True`, renamed to `research="minimal"`
in T002) already wires a research dir into a real bible — extend that, keep it green.

- [X] T002 Establish the **single shared** research fixture module `tests/fixtures/research.py` (the existing `tests/fixtures/` package is the home for shared fixtures): (a) relocate the iteration-13 `RESEARCH_SOURCES_MD` / `RESEARCH_TOPIC_MD` / `RESEARCH_INDEX_MD` constants out of `tests/commands/graph/conftest.py` **byte-identical** and re-import them there, so `scaffold_project(research="minimal")` and `tests/commands/graph/test_research_build.py` stay byte-stable (run that module and confirm green — a zero-regression relocation, not a rewrite); (b) add a richer `write_research_fixture(research_dir: Path)` builder whose content additionally satisfies SC-004 (≥1 foreign-language source carrying `translation`, since `original_language != book.language`), SC-005 (a conflicting-account pair → two findings, each with its own source), and SC-006 (a `baja`-reliability finding left **un-anchored** alongside a promoted ≥`media` finding), plus ≥1 open finding — every file conformant to [contracts/research-file-format.md](contracts/research-file-format.md) so `map_research()` raises zero `ResearchError`, and the promoted finding's anchor `constrains` an entity that exists in the tiny-novel bible (e.g. the `aparici` character) so SC-003's link resolves to a real triple, not a soft `ResearchWarning`; (c) **replace** the boolean `with_research` knob on `scaffold_project` with a single tri-state `research: Literal["none", "minimal", "rich"] = "none"` — one knob, no overlapping flags. `"none"` = no research dir (today's `with_research=False`); `"minimal"` = the relocated **byte-identical** constants (today's `with_research=True`); `"rich"` = `write_research_fixture()`. Migrate the existing `with_research=False/True` call sites — **only** in `tests/commands/graph/test_research_build.py` (and the `conftest.py` signature/docstring) — to `research="none"/"minimal"` **in this same task** (mechanical; the `"minimal"` path is byte-identical, so the 10-E13 count and every assertion stay stable). T026 then builds with `research="rich"`. No parallel fixture tree under `tests/fixtures/research/` — **one source of truth, one knob**, consumed by T003 and T026.

**Checkpoint**: Dependency confirmed and shared fixture in place — user stories can begin.

---

## Phase 3: User Story 1 - Guided rigorous research into structured, provenanced findings (Priority: P1) 🎯 MVP

**Goal**: Ship the `bookwright-research` source command that materializes (via
the unchanged iteration-9 pipeline) into a lint-passing `SKILL.md` for both
integrations, encoding the seven-step protocol and instructing the agent to
emit `bible/research/*` files in the exact shape `map_research()` parses, then
run `bookwright graph build --json`.

**Independent Test**: `bookwright init` materializes a valid
`bookwright-research` skill in both `claude` and `generic`; the conformant
fixture (T002) round-trips through `map_research()` with zero `ResearchError`;
`lint_skill_md` passes over the generated skill; the SC-009 description mirror
is green.

### Tests for User Story 1 ⚠️

> Write these FIRST and confirm they FAIL before implementation.

- [X] T003 [P] [US1] Format-conformance test in `tests/io/test_research_format.py`: write the shared `write_research_fixture()` (T002) content into a tmp `bible/research/`, load it through `map_research()` and assert zero `ResearchError`; assert the conflicting pair yields **two** distinct findings each with its own source (SC-005), and every finding's source carries `original_quote` (and `translation` for the foreign source) (SC-004) — contract IDs in [contracts/research-file-format.md](contracts/research-file-format.md). Imports the shared fixture; defines no fixture content of its own.
- [X] T004 [P] [US1] Materialization-compliance test in `tests/integrations/test_research_skill.py`: materialize `bookwright-research` for **both** `claude` and `generic`, assert `SKILL.md` `name == "bookwright-research"` (== parent dir), `description` < 1024 chars, body has no residual `{SCRIPT}`/other token, `references/research-format.md` is copied, and `lint_skill_md` passes (SK-1..SK-5, SC-001) — [contracts/research-skill.md](contracts/research-skill.md).
- [X] T005 [US1] **No new mirror test.** SC-009 byte-identity for `bookwright-research` is enforced by the **existing** `tests/integrations/test_descriptions.py` once T008a adds the command to `_ROSTER` (it already asserts `set(SKILL_DESCRIPTIONS)==set(_ROSTER)` and per-name front-matter equality). This task is the confirmation step only: after T008/T008a, run `uv run pytest tests/integrations/test_descriptions.py` and confirm green. Do **not** add a duplicate assertion in `test_research_skill.py` (SK-6, research.md R2).

### Implementation for User Story 1

- [X] T006 [P] [US1] Create the reference doc `src/bookwright/resources/commands/references/research-format.md` — author-facing rendering of [contracts/research-file-format.md](contracts/research-file-format.md): vocab tables (`type`, `reliability`), required source facets, the translation rule, finding/anchor shapes, soft-vs-fatal notes (cited by the skill; satisfies SK-4 `dangling_reference`).
- [X] T007 [US1] Create the source command `src/bookwright/resources/commands/bookwright-research.md` as a **first-class generative command** — it is classified generative in T008a, so `tests/resources/test_command_body.py` enforces the same body contract as the other ten (no reduced/special-cased command). Front-matter `name: bookwright-research`; bilingual ES+EN `description` ≤ 1024 with a negative boundary (NOT verify, NOT bible) per [contracts/research-skill.md](contracts/research-skill.md) "description". Spanish body carrying **all eight required sections** (`## Rol`, `## Input`, `## Procedimiento`, `## Output`, `## Archivos a leer`, `## Archivos a escribir`, `## Información faltante`, `## Qué NO hacer`); `## Procedimiento` encodes the seven steps in order (FR-005); the **`actualización en sitio`** update-in-place rule plus `[PENDING:`/`pending-protocol.md` guidance required of every generative command (the iteration-8 command-body contract that `tests/resources/test_command_body.py` enforces; here it carries this iteration's FR-017 re-run safety); output/persistence/`enabled=false`/re-run-safety instructions citing `references/research-format.md` (FR-006, FR-016, FR-017); final step `bookwright graph build --json` (FR-018); no fetching/network (FR-007). Body uses only `{ARGS}` (SK-5).
- [X] T008 [US1] Add `SKILL_DESCRIPTIONS["bookwright-research"]` to `src/bookwright/integrations/descriptions.py`, byte-identical to T007's front-matter `description` (R2; makes T005 pass).
- [X] T008a [US1] Register `bookwright-research` in **every command-inventory guard** — these are intentional change-detector tripwires, so the eleventh command must be declared in each, never routed around: `EXPECTED_COMMANDS` **and** `GENERATIVE_COMMANDS` in `tests/resources/helpers.py` (research writes files + merges in place → generative, which is what makes `test_command_body.py` enforce T007's marker/sections), `_ROSTER` in `tests/integrations/test_descriptions.py`, and `_ROSTER` in `tests/integrations/test_materialize.py`; bump the "the 10 commands" docstrings/comments to 11 in `tests/resources/helpers.py` and `tests/resources/test_command_frontmatter.py`. Keep `GENERATIVE_COMMANDS ∪ REPORT_ONLY_COMMANDS` covering the full `EXPECTED_COMMANDS` inventory. (The glob-derived rosters in `test_setup_materialize.py` / `test_e2e_materialize.py` auto-include the new command and now exercise its materialization end-to-end — they must stay green, which is free coverage, not extra work.)
- [X] T009 [US1] Run `uv run pytest tests/io/test_research_format.py tests/integrations/ tests/resources/` and the `lint_skill_md` path; confirm T003–T005 pass, the inventory guards (T008a) and the body/frontmatter/materialize suites are green for the eleven commands, and the skill materializes for both integrations.

**Checkpoint**: The research skill ships, materializes, lints, and the emitted format parses — MVP is independently demoable.

---

## Phase 4: User Story 2 - Configure the research system per project (Priority: P2)

**Goal**: Add the optional `[research]` manifest block (`enabled`,
`source_languages`, `min_reliability_for_anchor`) with defaults applied on
absence, field-naming validation errors, and the block written with comments
into the scaffolded `manifest.template.toml`.

**Independent Test**: Load a manifest with `[research]` and confirm the three
fields; load one without it and confirm defaults (`True`/`[]`/`"media"`); load
a bad `min_reliability_for_anchor` / non-ISO `source_languages` / unknown key
and confirm each raises a field-naming error (RB-1..RB-8).

### Tests for User Story 2 ⚠️

> Write these FIRST and confirm they FAIL before implementation.

- [X] T010 [P] [US2] Block test suite in `tests/core/test_research_block.py` covering RB-1..RB-8 from [contracts/research-block.md](contracts/research-block.md): present block exposes all three fields (RB-1); absent block loads with defaults (RB-2); `min_reliability_for_anchor = "altísima"` → error naming `research.min_reliability_for_anchor` (RB-3); `source_languages = ["de","zz"]` → error naming `research.source_languages[1]` (RB-4); `enabled = false` round-trips (RB-5); unknown key `foo` → `extra="forbid"` error (RB-6); anti-drift: `set(get_args(...))` of the `Literal` equals `set(RELIABILITY_IRI)` (RB-8, test imports `golem`, production does not).

### Implementation for User Story 2

- [X] T011 [US2] Create `src/bookwright/core/_research_block.py` — `ResearchBlock(BaseModel)` with `ConfigDict(extra="forbid", strict=True)`, `enabled: bool = True`, `source_languages: list[str] = Field(default_factory=list)`, `min_reliability_for_anchor: Literal["alta","media","baja"] = "media"`; a `@field_validator("source_languages", mode="after")` rejecting non-`ISO_639_1_CODES` entries with a `PydanticCustomError` carrying `{"index": i, "value": entry}` (mirrors `BookBlock._check_language`). Keep file ≤ 500 lines; no `golem` import (data-model.md §1, research.md R5).
- [X] T012 [US2] Edit `src/bookwright/core/manifest.py`: import `ResearchBlock` from `._research_block` and add `research: ResearchBlock = Field(default_factory=ResearchBlock)` to `Manifest` (one import + one field; keep `manifest.py` from growing — logic stays in T011's module).
- [X] T013 [US2] Edit `src/bookwright/core/__init__.py` to re-export `ResearchBlock` from `bookwright.core` (parallel to existing block re-exports).
- [X] T014 [US2] Edit `src/bookwright/resources/templates/manifest.template.toml`: add the `[research]` block with `enabled = true`, `source_languages = []`, `min_reliability_for_anchor = "media"`, each line preceded by its explanatory comment, exactly as in [contracts/research-block.md](contracts/research-block.md) "TOML surface" (FR-014a). No `_BUILD_OVERRIDE_ALLOWLIST_TABLE` entry (Non-goals).
- [X] T015 [US2] Add a comment round-trip test (RB-7) in `tests/core/test_research_block.py`: build/scaffold a manifest from the template, `load → dump → load`, assert the three `[research]` comment lines and values persist byte-stable through tomlkit (SC-002).
- [X] T016 [US2] Run `uv run pytest tests/core/test_research_block.py` and confirm T010 + T015 pass; verify defaults apply on an `[research]`-less fixture manifest.

**Checkpoint**: The block loads, validates, and ships in the scaffold with surviving comments — US1 and US2 both work independently.

---

## Phase 5: User Story 3 - `bible/research/` scaffolding and bible integration (Priority: P3)

**Goal**: Replace the legacy single `bible/research.md` starter with a
`bible/research/` directory (`_index.md` + `sources.md`), add layer-resolvable
packaged templates, and point `/bookwright-bible` + `/bookwright-clarify` at
`bible/research/_index.md`.

**Independent Test**: `bookwright init` produces `bible/research/_index.md` and
`sources.md` (no stray `bible/research.md`), both parsing cleanly through
`map_research()`; an override template in the project's template dir is
preferred over the packaged one; `/bookwright-bible` writes
`bible/research/_index.md`; `/bookwright-clarify` collects open questions.

### Tests for User Story 3 ⚠️

> Write these FIRST and confirm they FAIL before implementation.

- [X] T017 [P] [US3] Scaffold test in `tests/commands/init/test_init_research_scaffold.py`: after `init`, assert `bible/research/_index.md` and `bible/research/sources.md` exist and `bible/research.md` does **not** (US3-1); the scaffolded starter files parse through `map_research()` with zero `ResearchError` (R7 "must parse cleanly"); the generated `manifest.toml` contains the `[research]` block (FR-014a — depends on T014); and a project override under the template dir shadows the packaged `_index.md.tmpl` (FR-008, US3-2).

### Implementation for User Story 3

- [X] T018 [P] [US3] Delete the legacy starter `src/bookwright/resources/project/bible/research.md` (R7; FR-009 — the bible builder must not reference a path that no longer scaffolds).
- [X] T019 [P] [US3] Create `src/bookwright/resources/project/bible/research/_index.md` — valid empty/placeholder starter: `open_questions:` front-matter (may be empty list) + human-facing topic-map/open-questions prose; MUST parse through `map_research()` (R7).
- [X] T020 [P] [US3] Create `src/bookwright/resources/project/bible/research/sources.md` — valid starter with an empty/placeholder `sources:` list that parses through `map_research()` (R7).
- [X] T021 [P] [US3] Create `src/bookwright/resources/templates/bible/research/_index.md.tmpl` — layer-resolvable per-index skeleton, mirroring `templates/bible/character.md.tmpl` style (FR-008).
- [X] T022 [P] [US3] Create `src/bookwright/resources/templates/bible/research/sources.md.tmpl` — layer-resolvable sources-registry skeleton (FR-008).
- [X] T023 [P] [US3] Create `src/bookwright/resources/templates/bible/research/tema.md.tmpl` — per-`<topic>` skeleton (findings + anchors front-matter + heading), the format the skill points authors at (FR-008; data-model.md §2b).
- [X] T023a [US3] Register the three new molds in the mold guard `_REQUIRED_HEADINGS` in `tests/resources/test_mold_structure.py` — add `_index.md.tmpl`, `sources.md.tmpl`, `tema.md.tmpl` with their **actual** required headings so `test_every_mold_has_required_headings_listed` (`on_disk == set(_REQUIRED_HEADINGS)`) stays green and `test_mold_parses_and_has_headings` verifies each declared heading is literally present in T021–T023's molds. Intentional change-detector guard — declare the new molds, don't bypass it.
- [X] T024 [US3] Edit `src/bookwright/resources/commands/bookwright-bible.md` (body only — leave `description` untouched to keep SC-009 green): step 6 + the "Archivos a escribir" list create `bible/research/_index.md` instead of `bible/research.md` (FR-009, R8).
- [X] T025 [US3] Edit `src/bookwright/resources/commands/bookwright-clarify.md` (body only): the open-questions sweep names `bible/research/_index.md` (`open_questions:`) as its target (FR-010, R8). If either T024/T025 description changes, update `descriptions.py` in lockstep.

**Checkpoint**: All three slices are independently functional; research is wired into init, templates, bible, and clarify.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end proof, the SPARQL anchor check, and the four CI gates.

- [X] T026 [US1] Extend the iteration-13 graph-build suite `tests/commands/graph/test_research_build.py` (do **not** spin up a parallel `tests/e2e/`) with a build over the **rich** shared fixture — `scaffold_project(..., research="rich")` (T002): assert the conflicting pair maps to **two** findings (SC-005) and the foreign source's `translation` survives (SC-004); a SPARQL query retrieves the promoted finding's anchor `constrains`-ing a named bible entity (SC-003); and the `baja`-only finding yields **no** anchor — confirming `map_research` reflects the authored promotion faithfully and never auto-promotes. Note in the test that SC-006's *judgment* (don't promote a sub-floor finding) is enforced by the skill protocol body (T007) and the iteration-15 reliability-floor validator, **not** by this reader (which builds whatever anchors the file declares). Reuse the module's `_query` / `_e13_count` helpers.
- [X] T027 Run `uv run pytest` (full suite) and pass the **single-sourced** coverage gate (`[tool.coverage.report] fail_under = 80`; do not add a second threshold). The only new production Python module is `core/_research_block.py` — confirm it is **fully exercised** by its unit suite (T010/T015); add targeted unit tests if any branch is uncovered. The Markdown command, the templates, and the TOML block are data, not line-coverage-measured (SC-007 reworded — meet the enforceable project gate; there is no separate per-diff > 85 % gate).
- [X] T028 [P] Run `uv run ruff check && uv run ruff format --check && uv run mypy --strict`; fix any findings in the new/edited files.
- [X] T029 Execute [quickstart.md](quickstart.md) steps 1–6 manually against a throwaway `init`ed project to confirm the documented behavior matches reality (scaffold, block+comments round-trip, skill materialization, format parse, bible/clarify wiring).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup; T002 fixture blocks T003 and T026.
- **User Stories (Phase 3–5)**: each depends only on Setup + Foundational and is independently testable. Recommended order P1 → P2 → P3.
- **Polish (Phase 6)**: depends on the stories whose behavior it exercises (T026 needs US1's reader path + T002; T027–T029 need all merged).

### User Story Dependencies

- **US1 (P1)**: needs T002 (fixture) for T003; otherwise self-contained (command + reference + descriptions entry). The MVP.
- **US2 (P2)**: fully independent (pure `core/` code + template edit). No dependency on US1.
- **US3 (P3)**: independent for the scaffold/template/wiring parts; **T017's `[research]`-in-manifest assertion depends on T014 (US2)**. If US3 ships before US2, scope that one assertion out until T014 lands.

### Within Each User Story

- Tests (T003, T004, T010, T017) are written FIRST and must FAIL before implementation. T005 is a post-T008a confirmation step, not a fail-first test.
- US1: reference doc (T006) before/with the command (T007); command before its mirror entry (T008); the inventory-guard registration (T008a) after T007+T008, since it declares the now-existing command.
- US2: `_research_block.py` (T011) before the `manifest.py`/`__init__.py` wiring (T012–T013) before the template (T014) and round-trip test (T015).
- US3: delete legacy (T018) and create starters/templates (T019–T023) before the bible/clarify body edits (T024–T025); the mold-guard registration (T023a) after T021–T023, since it declares their headings.

### Parallel Opportunities

- **Setup/Foundational**: T001 then T002 (sequential — T002 needs the reader confirmed).
- **US1**: T003/T004 (tests, different concerns) in parallel; T006 parallel with the test-writing; T008a sequential after T007+T008; T005 is a post-T008a confirmation, not a fail-first test.
- **US2**: T010 alone (single test file); implementation T011 is the gate for T012–T015.
- **US3**: T017 (test) parallel with nothing it blocks; T018–T023 are all different files → fully parallel; T023a sequential after T021–T023; T024/T025 are different files → parallel.
- **Cross-story**: once Foundational is done, US1 / US2 / US3 can be staffed in parallel (only the T017↔T014 note applies).
- **Polish**: T028 parallel with T027 review.

---

## Parallel Example: User Story 3

```bash
# After T002, launch the independent scaffold/template files together:
Task: "Delete src/bookwright/resources/project/bible/research.md"
Task: "Create src/bookwright/resources/project/bible/research/_index.md"
Task: "Create src/bookwright/resources/project/bible/research/sources.md"
Task: "Create src/bookwright/resources/templates/bible/research/_index.md.tmpl"
Task: "Create src/bookwright/resources/templates/bible/research/sources.md.tmpl"
Task: "Create src/bookwright/resources/templates/bible/research/tema.md.tmpl"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup (T001) → Phase 2 Foundational (T002).
2. Phase 3 US1 (T003–T009): the research skill that materializes, lints, and
   emits a format the reader parses.
3. **STOP and VALIDATE**: materialize in both integrations, parse the fixture,
   run `lint_skill_md`, confirm the SC-009 mirror is green. Demoable MVP.

### Incremental Delivery

1. Setup + Foundational → ready.
2. US1 → test independently → MVP (the research command).
3. US2 → test independently → projects can configure `[research]`.
4. US3 → test independently → research wired into init/bible/clarify.
5. Polish (E2E + gates) → merge when all four CI gates are green.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- [Story] maps each task to its user story for traceability.
- This iteration adds **zero** triples-emitting code and **no** new GOLEM class
  — the ontology stays frozen (Constitution X); it only causes conformant files
  to exist for the iteration-13 reader.
- No new runtime dependency, no fetcher, no network (FR-007, Constitution II) —
  the skill instructs; the agent searches.
- Source code/identifiers in English; the `SKILL.md`/command bodies stay Spanish
  with bilingual ES+EN triggers in `description` (project convention).
- Commit after each task or logical group; stop at any checkpoint to validate a
  story independently.
