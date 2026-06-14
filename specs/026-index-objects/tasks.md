---
description: "Task list for iteration 026 — Index objects (G16) + bible/objects/ scaffold + skill"
---

# Tasks: Index objects (G16) + `bible/objects/` scaffold + skill

**Input**: Design documents from `/specs/026-index-objects/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/object-frontmatter.md, quickstart.md

**Tests**: Included — Constitution VIII (test discipline, ≥ 80 % coverage) and the spec's measurable outcomes (SC-001…SC-005) require unit/parity/scaffold coverage for the new ingestion path.

**Organization**: Tasks are grouped by user story. The single blocking prerequisite (the `bible.py` ingestion wiring) is isolated in the Foundational phase because both US1 (objects resolve) and US3 (skip/absent/collision) depend on it; US2 (the authoring command) is fully independent.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Same-file tasks are never marked [P] with each other.

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repo root (Constitution III).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working environment; no structural change (module split already shipped in iteration 025).

- [ ] T001 Verify the dev environment on branch `026-index-objects`: run `uv sync`, then confirm the baseline is green with `uv run pytest tests/io/test_bible.py tests/golem/test_ingestion_parity.py -q` (these are the files this iteration edits — capture the pre-change pass).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the objects ingestion path into the bible mapper. This is the one edit both US1 and US3 build on.

**⚠️ CRITICAL**: US1 and US3 cannot be verified until this phase is complete. (US2 is independent and may proceed in parallel.)

- [ ] T002 In [src/bookwright/io/bible.py](../../src/bookwright/io/bible.py): add `Object` to the existing `from bookwright.golem import (...)` block (line ~27, alongside `Setting`); add the constant `OBJECT_KEYS = frozenset({"name"})` beside `SETTING_KEYS`/`LOCATION_KEYS` (line ~88–89); and add `"OBJECT_KEYS"` to `__all__` (line ~59–66, keeping it sorted).
- [ ] T003 In [src/bookwright/io/bible.py](../../src/bookwright/io/bible.py) `map_bible`: add an objects `_DirSpec` after the locations pass (line ~175+) — `directory=bible_dir / "objects"`, `concept="Object"`, `builder=lambda meta, rp: Object(uri_base=uri_base, name=_require_name(meta))`, `allowed_keys=OBJECT_KEYS`, `index=False`, `into_entity_index=True` (leave `into_settings_index` at default `False`). No edit to `_bible_builders.py`. (Depends on T002)

**Checkpoint**: `bible/objects/*.md` now maps to `G16_Object` nodes; the path is concept-agnostic for skip/absent/collision via `_map_single_dir`.

---

## Phase 3: User Story 1 - Objects become first-class graph entities (Priority: P1) 🎯 MVP

**Goal**: Each `bible/objects/<slug>.md` becomes a `G16_Object` node with `file:line` provenance; a research `bears_on:`/`constrains:` to an object resolves instead of soft-missing; `Object` leaves the deferral registry and the parity guard observes G16 reachable.

**Independent Test**: Build a fixture with `bible/objects/<slug>.md` files; assert N `G16_Object` nodes with identity provenance, a research link to an object with zero soft-miss, and a green parity suite with the deferred set at 5 / reachable at 8.

### Tests for User Story 1

- [ ] T004 [US1] In [tests/io/test_bible.py](../../tests/io/test_bible.py): add an object round-trip + provenance test (mirror `test_location_name_only_builds_g13_node`) — `bible/objects/excalibur.md` with `name: "Excalibur"` yields exactly one `Object` with URI `…/object/excalibur` and `file:line` provenance starting `bible/objects/excalibur.md:` on identity (FR-001/002, SC-001, contract C1).
- [ ] T005 [US1] In [tests/io/test_bible.py](../../tests/io/test_bible.py): add an entity-index + research-resolution test (mirror the iteration-025 `test_location_enters_entity_index_for_research_resolution`) — the object slug enters `result.entity_index`, and a `map_research` pass whose `bears_on:` names the object records **zero** soft-misses for that target (FR-003, SC-002, contract C2). (Same file as T004 — sequential.)

### Implementation for User Story 1

- [ ] T006 [US1] In [src/bookwright/golem/deferrals.py](../../src/bookwright/golem/deferrals.py): remove the `"Object"` entry from `DEFERRED_CONCEPTS` (6 → 5); update the module docstring counts "Six … six" → "Five … five" (keep the "(iteration 025+)" wire-later note).
- [ ] T007 [P] [US1] Add `tests/fixtures/parity-exercise/bible/objects/<slug>.md` — one well-formed object file (`name:`) so a real build observes `G16_Object` as a reachable `rdf:type` (FR-010, SC-003).
- [ ] T008 [US1] In [tests/golem/test_ingestion_parity.py](../../tests/golem/test_ingestion_parity.py): add `"Object"` to `EXPECTED_REACHABLE` (7 → 8); remove `"Object"` from `ORPHAN_NAMES` (6 → 5) and `EXPECTED_VERSIONS` (6 → 5); change `len(DEFERRED_CONCEPTS) == 6` → `== 5`; repoint `test_drift_undeclared_orphan` from `"Object"` to a still-deferred concept (`"PsychologicalState"`); update module/test docstrings "Seven … six" → "Eight … five" (FR-010, SC-003). (Depends on T006, T007)

**Checkpoint**: Run `uv run pytest tests/io/test_bible.py -k object tests/golem/test_ingestion_parity.py -q` — US1 fully functional and independently testable (MVP).

---

## Phase 4: User Story 2 - The bible authoring command teaches object front-matter (Priority: P2)

**Goal**: `/bookwright-bible` instructs writing `bible/objects/<slug>.md` with required `name:` front-matter, lists `bible/objects/` among the entity directories and files-to-write, and re-materializes as `SKILL.md` for both `claude` and `generic` with bilingual triggers intact.

**Independent Test**: Read the updated source command and its materialized `SKILL.md`s; confirm the object instruction, the directory listing, the files-to-write entry, both integrations regenerating, and ES/EN triggers surviving.

### Implementation for User Story 2

- [ ] T009 [US2] In [src/bookwright/resources/commands/bookwright-bible.md](../../src/bookwright/resources/commands/bookwright-bible.md): add `bible/objects/` to the entity directories to ensure/create (line ~31, beside `settings/`/`locations/`); add a procedure step prescribing each concrete object as `bible/objects/<slug>.md` with a required `name:` front-matter field (after the locations step, line ~42–44); add `bible/objects/*.md` to the files-to-write list (line ~81). Keep prose Spanish; preserve bilingual triggers (FR-008).
- [ ] T010 [US2] Verify re-materialization: `uv run pytest tests/integrations/ -q` and `uv run pytest tests/resources/test_command_frontmatter.py tests/resources/test_command_activation.py -q` — the `bookwright-bible` `SKILL.md` regenerates and lints for `claude` and `generic`, front-matter valid, ES/EN triggers unchanged (FR-009, SC-005). If a resources test asserts command body content, extend it to cover the `bible/objects/` mention.

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Backward compatibility with older skeletons (Priority: P3)

**Goal**: A missing `bible/objects/` directory builds exactly as before; an object file with unusable `name` is skipped (never a crash); a same-slug pair collides exactly as characters/settings do; a freshly scaffolded project ships `bible/objects/`.

**Independent Test**: Build a project with a front-matter-less object file (recorded skipped, no exception) and one with no `objects/` dir (unaffected); scaffold a project and assert `bible/objects/.gitkeep`.

### Tests for User Story 3

- [ ] T011 [US3] In [tests/io/test_bible.py](../../tests/io/test_bible.py): add a skip test — `bible/objects/blank.md` with missing/empty/whitespace/non-string `name` is recorded under `result.skipped`, no `Object` node, build completes (FR-005, SC-004, contract C3). (Same file as T004/T005 — sequential.)
- [ ] T012 [US3] In [tests/io/test_bible.py](../../tests/io/test_bible.py): add an absent-directory test — a project with no `bible/objects/` directory yields zero object nodes and output identical to today (FR-006, SC-004, contract C4). (Same file — sequential.)
- [ ] T013 [US3] In [tests/io/test_bible.py](../../tests/io/test_bible.py): add a collision test — two object files slugging to the same identity raise `SlugCollisionError` with per-concept scope `("Object", slug)` (FR-004, contract C5). (Same file — sequential.)

### Implementation for User Story 3

- [ ] T014 [P] [US3] Add `src/bookwright/resources/project/bible/objects/.gitkeep` — one empty placeholder mirroring `bible/settings/.gitkeep` and `bible/locations/.gitkeep` (no `.tmpl`, no sample object) (FR-007).
- [ ] T015 [US3] In [tests/commands/test_init_default.py](../../tests/commands/test_init_default.py): assert a freshly scaffolded project contains `bible/objects/.gitkeep`, mirroring the existing `settings/`/`locations/` assertions (FR-007, SC-005). (Depends on T014)

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across the whole change.

- [ ] T016 Run the quickstart scenarios end-to-end ([quickstart.md](quickstart.md) Scenarios 1–6) and confirm each expectation.
- [ ] T017 Run all four CI gates: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (coverage ≥ 80 %). Confirm every pre-existing bible test passes with unchanged expected output (SC-005).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; **blocks US1 and US3** (graph-behavior). US2 does not depend on it.
- **US1 (Phase 3)**: depends on Foundational.
- **US2 (Phase 4)**: independent of Foundational and US1 — can start any time after Setup.
- **US3 (Phase 5)**: depends on Foundational.
- **Polish (Phase 6)**: depends on all desired stories complete.

### Within Each User Story

- US1: tests (T004, T005) and impl (T006–T008) — T008 depends on T006+T007.
- US3: tests (T011–T013) and impl (T014, T015) — T015 depends on T014.
- Same-file test tasks (T004/T005/T011/T012/T013 all in `tests/io/test_bible.py`) run sequentially.

### Parallel Opportunities

- T007 (parity fixture) and T014 (scaffold `.gitkeep`) are different files — parallelizable, and parallelizable with the `test_bible.py` test tasks.
- US2 (T009–T010) can be developed entirely in parallel with US1/US3 since it touches only the source command and integration tests.

---

## Parallel Example

```bash
# After Foundational (T002, T003), the file-disjoint scaffolding can land together:
Task: "T007 Add parity fixture tests/fixtures/parity-exercise/bible/objects/<slug>.md"
Task: "T014 Add scaffold src/bookwright/resources/project/bible/objects/.gitkeep"

# US2 in parallel with US1/US3 (different files entirely):
Task: "T009 Edit src/bookwright/resources/commands/bookwright-bible.md"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational (the `bible.py` wiring).
2. Phase 3 US1 → objects resolve, deferral dropped, parity green.
3. **STOP and VALIDATE**: `uv run pytest tests/io/test_bible.py -k object tests/golem/test_ingestion_parity.py -q`.

### Incremental Delivery

1. Foundational → US1 (MVP: G16 fed) → US2 (authoring command) → US3 (robustness + scaffold).
2. Each story is independently testable and adds value without breaking the prior.
3. Finish with Phase 6 (quickstart + four gates) before merge.

---

## Notes

- No ontology change (Principle X): `G16_Object` reused as-is; no class/property added.
- No new module / no `_bible_builders.py` edit — `_require_name` reused inline (research D1).
- `index=False` (not a participant), `into_entity_index=True` (research target) — the exact `Setting` profile.
- Commit after each story or logical group; the `after_tasks` git hook offers a commit now.
