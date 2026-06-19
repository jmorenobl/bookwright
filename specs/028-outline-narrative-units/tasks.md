---
description: "Task list for outline narrative-unit ingestion (G9/G10)"
---

# Tasks: Outline ingestion — narrative units & functions (G9/G10)

**Input**: Design documents from `/specs/028-outline-narrative-units/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/outline-units-ingestion.md, quickstart.md

**Tests**: INCLUDED — the spec mandates them (FR-013 parity gate, SC-003/SC-004
edge/skip counts) and names the test files (`tests/io/test_outline.py`,
`tests/golem/test_ingestion_parity.py`, `tests/integrations/test_materialize.py`)
in quickstart §6.

**Organization**: Tasks are grouped by user story (P1 → P2 → P3) so each can be
implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 maps the task to its spec user story
- Exact file paths are given in each task

## Path Conventions

Single project, src-layout: `src/bookwright/`, tests under `tests/` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm a green baseline before touching the ingestion seam.

- [ ] T001 Run the full gate suite from repo root to confirm a clean starting state: `uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy --strict` (record that 028's edits start from green; no source change in this task).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The two map-context fields both US1 (functions dedup) and US2 (role
resolution) read/write. MUST land before any units-pass behaviour.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T002 Add `functions_index: dict[str, NarrativeFunction]` (default empty) to `_MapContext` and add `roles_index: dict[str, list[URIRef]]` (default empty) to **both** `_MapContext` and the `MapResult` dataclass in `src/bookwright/io/_bible_builders.py` (per data-model.md "Indices threaded through the map"); import `URIRef` from `rdflib` and `NarrativeFunction` from `bookwright.golem.modules.narrative` as needed. No behaviour change yet — fields are unpopulated.

**Checkpoint**: The shared context carries `functions_index` / `roles_index`; the
units pass can now be built against them.

---

## Phase 3: User Story 1 - Plot structure queryable from beat cards (Priority: P1) 🎯 MVP

**Goal**: `outline/units/*.md` cards become `NarrativeUnit` (G9) entities and their
`functions` become slug-deduped `NarrativeFunction` (G10) entities, linked by
`crm:P67_refers_to`, citable by SPARQL — taking G9/G10 out of the deferral registry.

**Independent Test**: Build a project with two `outline/units/*.md` cards sharing one
function name → exactly two `NarrativeUnit`, exactly one shared `NarrativeFunction`,
one unit→function edge from each; malformed cards skipped; no `outline/units/` dir →
identical graph. The parity test observes G9/G10 reachable with three orphans left.

### Tests for User Story 1 ⚠️ (write FIRST, ensure they FAIL)

- [ ] T003 [P] [US1] Create `tests/io/test_outline.py` covering US1: (a) two cards sharing one function name → 2 `NarrativeUnit`, 1 `NarrativeFunction`, one unit→function `crm:P67_refers_to` per unit (SC-001/002); (b) within-card repeated `functions` slug-deduped to K edges (SC-002); (c) `name` but no `functions` → unit only, no edges, no error; (d) prose body not ingested (FR-003); (e) no-frontmatter / malformed-YAML card → `skipped` with reason, build continues (SC-003, R1/R2); (f) missing/empty/non-string `name` → skipped (FR-006); (g) non-list `functions` → skipped, no partial function leaked (FR-007, R2); (h) two cards whose `name` slugs collide → `SlugCollisionError` (FR-008); (i) absent `outline/units/` dir → no units, no error (FR-009, SC-006). Drive each case through `map_outline` after `map_bible` on a temp project.
- [ ] T004 [P] [US1] Update `tests/golem/test_ingestion_parity.py` constants/prose in lockstep (FR-013, SC-005): move `"NarrativeUnit"`/`"NarrativeFunction"` from `ORPHAN_NAMES` into `EXPECTED_REACHABLE`; drop both from `EXPECTED_VERSIONS`; change `len(DEFERRED_CONCEPTS) == 5` to `== 3`; rewrite the module docstring's "Eight of the thirteen … the other five are orphans" to "Ten … the other three are orphans". Leave the three drift-simulation probes (`Character`, `NarrativeEvent`, `PsychologicalState`) untouched and assert in a comment that none names a removed concept (FR-013). Will fail until T005–T008 land.

### Implementation for User Story 1

- [ ] T005 [US1] Create `src/bookwright/io/outline.py` exposing `map_outline(project_root, outline_dir, uri_base, result) -> None` (signature per contracts/outline-units-ingestion.md): import the generic engine `_DirSpec`, `_map_single_dir` from `bookwright.io.bible` and `_MapContext`, `MappedEntity`, `_require_name`, `_coerce_str_list`, `_Collisions` from `bookwright.io._bible_builders` (one-way import, no cycle). Implement `_build_unit` to (1) `_require_name` + slug, (2) `_coerce_str_list(meta.get("functions"), "functions")` and slug-dedup within the card **before** minting, (3) for each distinct function slug mint-or-reuse a `NarrativeFunction(uri_base, name)` via `ctx.functions_index`, appending one `MappedEntity` for first introduction, and reference them through the unit's `CrossRef("functions", REFERS_TO, multi=True)`, (4) build the `NarrativeUnit` and append its `MappedEntity`. Walk `outline_dir / "units"` via `_map_single_dir` with `_DirSpec(index=False, into_entity_index=False)`. Keep file ≤ 500 lines (~140). (Roles branch added in US2 — leave `roles` unhandled / empty here.)
- [ ] T006 [US1] In `src/bookwright/commands/_graph.py` `build_project_graph`, import `map_outline` and call it immediately after `map_bible`, passing `root / manifest.paths.outline` and the existing `result` (append into the same `MapResult`; downstream `result.mapped` iteration and `BuildReport` counters are unchanged — research.md D1).
- [ ] T007 [P] [US1] In `src/bookwright/golem/deferrals.py` remove the `"NarrativeUnit"` and `"NarrativeFunction"` entries from `DEFERRED_CONCEPTS` (leaving exactly `NarrativeSequence`, `RelationshipRole`, `PsychologicalState`); update the module docstring "Five of the thirteen" → "Three of the thirteen", "Exactly five entries" → "Exactly three entries", and amend the "never *materialized* by any builder over `bible/*.md`" framing so it no longer implies `outline/` is wholly unfed (FR-013, FR-014).
- [ ] T008 [P] [US1] Add an `outline/units/*.md` card (e.g. `tests/fixtures/parity-exercise/outline/units/opening.md`) with `name` and ≥ 1 `functions` name so the **live** parity build emits G9/G10 `rdf:type` IRIs (FR-013); confirm `manifest.paths.outline` in that fixture points at `outline/`.

**Checkpoint**: `graph build` over a project with unit cards yields queryable
`NarrativeUnit`/`NarrativeFunction`; `test_outline.py` US1 cases and the parity
test pass. MVP complete.

---

## Phase 4: User Story 2 - Units link to narrative roles (Priority: P2)

**Goal**: A unit's `roles` names resolve by slug against the character-scoped
narrative-role nodes characters already materialize, emitting one unit→role
`crm:P67_refers_to` edge per matching character role; zero matches = one soft
`UnresolvedReference`, unit still built. Mints nothing.

**Independent Test**: With a character declaring `narrative_roles: [hero]`, a unit
with `roles: [hero, ghost]` → one unit→role edge to the resolved `hero` node and one
unresolved-reference warning for `ghost`, the unit still built.

### Tests for User Story 2 ⚠️ (write FIRST, ensure they FAIL)

- [ ] T009 [P] [US2] Extend `tests/io/test_outline.py` with US2 cases: (a) character `narrative_roles: [hero]` + unit `roles: [hero]` → one unit→role `crm:P67_refers_to` edge to that character-scoped role node (SC-004); (b) `roles: [unknown]` matching no character role → 0 edges, exactly one `UnresolvedReference`, unit still present (SC-004, C5); (c) no `roles` key → no edges, no warning; (d) a role slug played by C characters → exactly C edges (SC-004); (e) repeated role names within one card slug-deduped before resolution so edge count is unaffected (SC-004, clarification 2026-06-19); (f) non-list `roles` → card skipped (FR-007).

### Implementation for User Story 2

- [ ] T010 [US2] In `src/bookwright/io/bible.py`, add an `_index_character_roles(ctx)` helper run by `map_bible` immediately after the character `_map_single_dir` pass: iterate the just-mapped entities, narrow with `isinstance(entity, Character)`, read each materialized character-scoped role node's URI (single source of truth, `{character.uri}/role/{slug}` — do not recompute the scheme), and append it under `make_slug(label)` into `ctx.roles_index` (many-valued). Publish the index on `result.roles_index` (research.md D2). Keep `bible.py` ≤ 500 lines.
- [ ] T011 [US2] Add the `roles` branch to `_build_unit` in `src/bookwright/io/outline.py`: `_coerce_str_list(meta.get("roles"), "roles")` and slug-dedup within the card **before** resolution; for each distinct role slug `matches = result.roles_index.get(slug, [])` — non-empty → extend the unit's `roles` (`CrossRef("roles", REFERS_TO, multi=True)`) with every matching URI (one edge per match); empty → append exactly one `UnresolvedReference(path, entity=name, name=role_name)`, emit no edge, still build the unit (FR-005, SC-004). Mint no role entity.

**Checkpoint**: Units link to existing character roles with deterministic edge counts
and soft-miss warnings; US1 + US2 both pass independently.

---

## Phase 5: User Story 3 - Authoring surface guides unit cards (Priority: P3)

**Goal**: The `bookwright-outline` skill instructs authors to create `outline/units/`
cards (`name`/`functions`/`roles`), and `bookwright init` scaffolds an
`outline/units/` directory mirroring `bible/settings/`.

**Independent Test**: Materialize integrations → the regenerated `bookwright-outline`
`SKILL.md` for both `claude` and `generic` documents the card format, keeps bilingual
triggers, passes `lint_skill_md`; a freshly initialized project contains
`outline/units/`.

### Tests for User Story 3 ⚠️ (write FIRST, ensure they FAIL)

- [ ] T012 [P] [US3] Add/extend tests asserting (a) in `tests/integrations/test_materialize.py`: the regenerated `bookwright-outline` `SKILL.md` for `claude` and `generic` instructs `outline/units/` cards with `name`/`functions`/`roles`, still triggers on ES + EN prompts, and passes the skill lint gate (SC-007, A1); (b) in the `bookwright init` scaffold test (`tests/commands/init/`): a freshly initialized project contains `outline/units/` (FR-012, A2).

### Implementation for User Story 3

- [ ] T013 [P] [US3] Update `src/bookwright/resources/commands/bookwright-outline.md` (Spanish prose, the command's existing language) to add, alongside the prose arcs/structure/synopsis instructions, a step + write-target to create one card per narrative unit under `outline/units/` with `name`/`functions`/`roles` front-matter; keep `description` bilingual and < 1024 chars (FR-011). The existing iteration-9 materializer regenerates each `SKILL.md` — no manual `SKILL.md` editing.
- [ ] T014 [P] [US3] Add `src/bookwright/resources/project/outline/units/.gitkeep` so `bookwright init` scaffolds the directory, mirroring `bible/settings/` (FR-012).

**Checkpoint**: Authors have a guided path to produce unit cards and a scaffolded
directory; all three stories pass independently.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Sweep the present-tense "outline is author-only" documentation debt class
(FR-014) and the canonical design doc, then validate end-to-end.

- [ ] T015 [P] Amend the iteration-024 author-only note in `src/bookwright/io/manuscript.py` (English) so it reads `outline/` as partially ingested — `units/` is ingested; `arcs`/`structure`/`synopsis`/`scenes` remain author-only prose (FR-014, SC-008).
- [ ] T016 [P] Amend the v0.3 author-only note in `docs/authoring.md` (kept Spanish) to the same partially-ingested framing (FR-014, SC-008).
- [ ] T017 Update `bookwright-design.md` (Spanish): add `outline/units/` to the § 7 project-tree listing and add a new § 7.4 ingestion subsection mirroring § 7.2/§ 7.3 (locations/objects precedent), documenting the `outline/units/` card surface. Also sweep the skill-output table (`Command | Input | Output`): add `outline/units/*.md` to the `/bookwright-outline` output row and, closing the one pre-existing instance of the same class, add the omitted `bible/objects/*.md` to the `/bookwright-bible` row (it is authored by `bookwright-bible.md` and ingested since iteration 026) (FR-014, SC-008).
- [ ] T018 Run the quickstart.md walkthrough and the full gate suite from repo root: `uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy --strict`; confirm coverage ≥ 80 %, the parity orphan set is exactly `{NarrativeSequence, RelationshipRole, PsychologicalState}`, and SC-008's scoped search finds no live source/doc/design statement still calling `outline/` presently wholly author-only (the roadmap's historical "author-only *en v0.3*" is out of scope by design).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — establishes a green baseline.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS US1 and US2 (both read the new context fields).
- **US1 (Phase 3)**: Depends on Foundational. The MVP — delivers entities + parity.
- **US2 (Phase 4)**: Depends on Foundational; `_build_unit` (T011) extends the module created in US1 (T005), and `roles_index` is published by T010 + consumed against the seam from T002. Practically sequenced after US1, but independently testable.
- **US3 (Phase 5)**: Depends only on the existing materializer/scaffold — independent of US1/US2 engine code; can run any time after Setup.
- **Polish (Phase 6)**: Depends on US1 being merged (the present-tense claim is only false once units are ingested).

### User Story Dependencies

- **US1 (P1)**: Foundational only. No dependency on US2/US3.
- **US2 (P2)**: Foundational + the `outline.py` module from US1 (shared file `_build_unit`). Independently testable via its own cases in `test_outline.py`.
- **US3 (P3)**: No engine dependency; touches resources/docs only.

### Within Each User Story

- Tests (T003/T004, T009, T012) are written FIRST and must FAIL before implementation.
- US1: T005 (module) before T006 (graph wiring, needs `map_outline`); T007/T008 independent of T005.
- US2: T010 (index population) before/with T011 (consumption).

### Parallel Opportunities

- US1 tests: T003 (`test_outline.py`) ∥ T004 (`test_ingestion_parity.py`) — different files.
- US1 impl: T007 (`deferrals.py`) ∥ T008 (fixture) ∥ T005 (`outline.py`); T006 follows T005.
- US3: T013 (source command) ∥ T014 (scaffold) ∥ T012 (tests).
- Polish: T015 (`manuscript.py`) ∥ T016 (`authoring.md`); T017/T018 sequential at the end.
- Across stories: US3 (resources/docs) can proceed in parallel with US1/US2 engine work by a second contributor.

---

## Parallel Example: User Story 1

```bash
# Write the failing tests together (different files):
Task: "Create tests/io/test_outline.py US1 cases"          # T003
Task: "Update tests/golem/test_ingestion_parity.py"        # T004

# Then the independent implementation pieces:
Task: "Remove G9/G10 from deferrals.py + docstrings"       # T007
Task: "Add parity-exercise outline/units/ fixture card"    # T008
# (T005 io/outline.py, then T006 _graph.py wiring)
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → confirm green.
2. Phase 2 Foundational → context fields in place.
3. Phase 3 US1 → units + functions queryable, parity green.
4. **STOP and VALIDATE**: build a two-card project, run quickstart §1–3 and the parity test.

### Incremental Delivery

1. Setup + Foundational → seam ready.
2. US1 → entities + parity (MVP) — test, demo.
3. US2 → role links — test, demo.
4. US3 → authoring surface + scaffold — test, demo.
5. Polish → doc sweep + design doc + full gate run.

---

## Notes

- [P] = different files, no incomplete-task dependency.
- No `golem/` edit and no ontology growth (Principle X): G9, G10, and `crm:P67_refers_to` already exist.
- Every touched/new source file stays ≤ 500 lines (Principle IV).
- `graph build` / `status` `--json` envelopes are unchanged (Principle IX).
- Commit after each task or logical group; verify each story's tests fail before implementing.
