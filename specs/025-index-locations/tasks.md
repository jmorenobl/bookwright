---
description: "Task list for: Index locations (G13) + `bible.py` split"
---

# Tasks: Index locations (G13) + `bible.py` split

**Input**: Design documents from `/specs/025-index-locations/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/location-frontmatter.md, quickstart.md

**Tests**: Included. The constitution mandates test discipline (≥ 80 % coverage, Principle VIII) and the spec defines per-story Independent Tests + nine quickstart scenarios, so test tasks are first-class here.

**Organization**: Tasks are grouped by user story (US1 P1, US2 P2, US3 P3) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (Setup, Foundational and Polish carry no story label)
- Exact file paths are included in every task

## Path Conventions

Single project, src-layout (Constitution III): `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the baseline before touching the mapper.

- [x] T001 Run `uv sync`, then capture the pre-change baseline for the behavior-preserving refactor: record `grep -c '' src/bookwright/io/bible.py` (must be 500 now) and run `uv run pytest tests/io/test_bible.py -q` to confirm the existing bible suite is green before any edit.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The behavior-preserving `io/bible.py` split (FR-013). This MUST land first because US1 adds the new location builder *into* the extracted sibling module, and every story builds through `map_bible`. No observable mapper output may change here.

**⚠️ CRITICAL**: No user-story work begins until Phase 2 is complete and the existing bible tests are green.

- [x] T002 Create `src/bookwright/io/_bible_builders.py` and move, per [data-model.md](data-model.md) §4, the symbols `_Builder`, `_ItemBuilder`, `MappedEntity`, `MapResult`, `_Collisions`, `_MapContext`, `_ItemContext`, `_require_name`, `_coerce_year`, `_coerce_str_list`, `_build_character`, `_resolve_interval`, `_build_event`, `_resolve_refs` out of `src/bookwright/io/bible.py`. The new module imports only `golem`, `io.errors`, `io.report`, and stdlib — **no import from `bible.py`** (one-way dependency, no cycle).
- [x] T003 Update `src/bookwright/io/bible.py` to `from ._bible_builders import (...)` re-exporting `MapResult`, `MappedEntity`, `_MapContext`, `_ItemContext`, `_Collisions`, `_build_character`, `_build_event`, `_resolve_refs`, `_require_name`, and the remaining moved names, so `from bookwright.io.bible import map_bible` / `MapResult` / `MappedEntity` keep resolving. Keep `map_bible`, `_map_single_dir`, `_map_collection`, `_map_collection_item`, `_build_item_index`, `_safe_parse`, `_relpath`, `_slug_of`, `_record_unknown_keys`, `_DirSpec`, `_CollectionSpec`, `build_provenance`, and the `*_KEYS` constants in `bible.py`.
- [x] T004 Verify the extraction is behavior-preserving: `uv run pytest tests/io/test_bible.py -q` passes **unchanged**, `test "$(grep -c '' src/bookwright/io/bible.py)" -le 500` holds, and `uv run ruff check && uv run ruff format --check && uv run mypy --strict` are green. (FR-013, SC-006 — the no-behavior-change guarantee.)

**Checkpoint**: `bible.py` is back under 500 lines with the sibling module in place and no output change. User stories can now begin.

---

## Phase 3: User Story 1 - Locations become first-class graph entities (Priority: P1) 🎯 MVP

**Goal**: Feed `bible/locations/*.md` into the graph as `G13_Narrative_Location` nodes — identity from `name`, optional `setting:` emitting the `dlp:generic-location` cross-ref — and make research links to locations resolve, with G13 dropping out of the deferral registry.

**Independent Test**: Build a fixture with `bible/locations/<slug>.md` (one with a resolvable `setting:`, one without) and assert the graph holds the G13 nodes, the `setting:` one carries the `dlp:generic-location` edge to its sibling setting, a research link to a location resolves (no soft-miss), and the parity suite is green with G13 reachable.

### Tests for User Story 1 ⚠️ (write first; they MUST fail before T010–T013)

- [x] T005 [P] [US1] In `tests/io/test_bible.py`, add the core ingestion cases from [contracts/location-frontmatter.md](contracts/location-frontmatter.md): `name`-only → one G13 node with slug from `name` and file-level identity provenance; `name` + resolvable `setting` → node + `dlp:generic-location` edge with `setting:` line provenance; `name` + absent/blank `setting` → node, no edge, no warning. (FR-001/002/003, SC-001/002)
- [x] T006 [P] [US1] In `tests/io/test_bible.py`, add the unresolved-setting soft-miss case (one `UnresolvedParticipant` with `path`=file, `entity`=name, `name`=setting; node still built, build not aborted) and the slug-collision case (`pytest.raises(SlugCollisionError)`, concept `"NarrativeLocation"`). (FR-004/006, SC-002)
- [x] T007 [P] [US1] In `tests/io/test_bible.py`, add a test asserting each built location enters `result.entity_index` (keyed by slug) so a research `bears_on:`/`constrains:` target naming the location resolves instead of a soft-miss. (FR-005, SC-003)
- [x] T008 [P] [US1] Update the parity pins in `tests/golem/test_ingestion_parity.py`: `EXPECTED_REACHABLE` += `NarrativeLocation` (→ 7), `ORPHAN_NAMES` -= `NarrativeLocation` (→ 6), drop `NarrativeLocation` from `EXPECTED_VERSIONS`, `test_registry_well_formed` `len == 6`, and flip the module docstring ("Six … other seven are orphans" → "Seven … other six are orphans"). (FR-012, SC-004)
- [x] T009 [P] [US1] Add the fixture `tests/fixtures/parity-exercise/bible/locations/` with `harbor.md` (`name:` + a `setting:` resolving to an existing `bible/settings/` file) and one no-`setting:` location, so the live `parity-exercise` build observes `golem:G13_Narrative_Location`. (FR-012, SC-004)

### Implementation for User Story 1

- [x] T010 [US1] In `src/bookwright/io/_bible_builders.py` add `settings_index: dict[str, URIRef] = field(default_factory=dict)` to `_MapContext` and `into_settings_index: bool = False` to `_DirSpec`; in `src/bookwright/io/bible.py` `_map_single_dir`, after a built entity add `if spec.into_settings_index: ctx.settings_index[_slug_of(entity)] = entity.uri` (mirroring the existing `into_entity_index`/`index` blocks). (data-model.md §3/§4)
- [x] T011 [US1] In `src/bookwright/io/_bible_builders.py` add `_resolve_setting` (scoped to `ctx.settings_index`; absent/blank → no edge; unresolved string → append an `UnresolvedParticipant` to the result, no edge) and `_build_location` (builds the frozen `NarrativeLocation` from `name`, wiring the optional resolved `setting`), and re-export both from `bible.py`. (FR-002/003/004, data-model.md §4)
- [x] T012 [US1] In `src/bookwright/io/bible.py` add `LOCATION_KEYS = frozenset({"name", "setting"})` and wire the locations `_DirSpec` pass in `map_bible` **after** the settings pass (`directory=bible_dir/"locations"`, `concept="NarrativeLocation"`, `builder=lambda meta, rp: _build_location(uri_base, ctx, meta, rp)`, `allowed_keys=LOCATION_KEYS`, `index=False`, `into_entity_index=True`); give the existing settings `_DirSpec` `into_settings_index=True`. (FR-001/005/008, Assumptions ordering invariant)
- [x] T013 [US1] In `src/bookwright/golem/deferrals.py` remove the `NarrativeLocation` entry from `DEFERRED_CONCEPTS` (7 → 6) and change the docstring count "Seven" → "Six". (FR-012, SC-004)
- [x] T014 [US1] In `bookwright-design.md` rewrite § 7.2 (Spanish) to record G13 as wired — locations are now indexed as `G13_Narrative_Location` from `name:`/`setting:` front-matter — retiring the "no se indexa en v0" shortcut text, and update the "(opcional)" tree note accordingly. Reopens no axiom (Principle X).

**Checkpoint**: Locations are first-class G13 nodes, the cross-ref resolves with a graceful soft-miss, research links resolve, and the parity guard is green with G13 fed. MVP is functional.

---

## Phase 4: User Story 2 - The bible authoring command teaches location front-matter (Priority: P2)

**Goal**: The `/bookwright-bible` source command instructs authors to write each location as `bible/locations/<slug>.md` with `name:` (+ optional `setting:`) front-matter, and re-materializes as `SKILL.md` for `claude` and `generic` with bilingual triggers intact.

**Independent Test**: Read the updated source command and its materialized `SKILL.md` outputs: the location instruction now prescribes `name:` (+ optional `setting:`), the "no se indexa en v0 / sin frontmatter" wording is gone, both integrations regenerate, and the ES/EN trigger phrases survive.

### Implementation for User Story 2

- [x] T015 [US2] Edit `src/bookwright/resources/commands/bookwright-bible.md` so the `bible/locations/<slug>.md` procedure prescribes `name:` (required) and `setting:` (optional) front-matter alongside the sensory-prose sections, and remove any wording stating locations are unindexed / front-matter-free in v0. Preserve the bilingual (ES/EN) author triggers. (FR-010)
- [x] T016 [US2] Run `uv run pytest tests/integrations/ -q` to confirm the `bookwright-bible` `SKILL.md` regenerates and passes `lint_skill_md` for both `claude` and `generic`; add/adjust an assertion there if needed that the materialized skill mentions the `setting:` front-matter and keeps valid YAML front-matter with unchanged triggers. (FR-011, SC — Scenario 7)

**Checkpoint**: Authored locations now carry the front-matter the US1 ingestion path consumes.

---

## Phase 5: User Story 3 - Backward compatibility and a legible mapper (Priority: P3)

**Goal**: Old v0-style location files (prose, no ingestible front-matter) and projects with no `bible/locations/` directory keep building without error; the split confirmed legible and under the 500-line ceiling with no behavior change.

**Independent Test**: Build a project with a frontmatter-less location file (recorded as skipped, no node, no exception) and a project with no `locations/` directory (unaffected); confirm `io/bible.py` ≤ 500 lines and pre-existing bible tests pass unchanged.

### Tests for User Story 3 ⚠️

- [x] T017 [P] [US3] In `tests/io/test_bible.py`, add the backward-compat skip/absent cases: a frontmatter-less / missing-or-empty-`name` / non-string-`name` / non-string-`setting` location file is recorded under `result.skipped` (`SkippedFile`) with no node and no crash; and a project with no `bible/locations/` directory builds identically (no error, no location nodes). (FR-007/008/009, SC-005, Edge Cases)

### Verification for User Story 3

- [x] T018 [US3] Confirm the split outcome holds after US1's additions: `test "$(grep -c '' src/bookwright/io/bible.py)" -le 500` and the full `tests/io/test_bible.py` suite — pre-existing cases unchanged — passes. (FR-013, SC-006)

**Checkpoint**: Robustness and the size limit hold; all three stories are independently green.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation across stories.

- [x] T019 [P] Walk the nine [quickstart.md](quickstart.md) scenarios end-to-end (G13 nodes + resolved/soft-miss/absent setting, research resolution, skip/absent, collision, command re-materialization, parity guard, module ≤ 500 lines) and confirm each passes as written.
- [x] T020 Run all four CI gates green: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, and `uv run pytest` (≥ 80 % coverage, single-sourced in `[tool.coverage.report]`). (SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup; **blocks all user stories** (the split must land before the location builder is added to the sibling module).
- **US1 (Phase 3)**: depends on Foundational. The MVP — delivers the headline.
- **US2 (Phase 4)**: depends on Foundational; logically follows US1 (its front-matter contract is what the command teaches) but touches disjoint files (`resources/commands/`, `tests/integrations/`) so it can proceed in parallel with US1 once the contract in data-model/contracts is settled.
- **US3 (Phase 5)**: depends on Foundational + US1 (it verifies the split survives US1's additions and exercises the skip path through the new locations pass).
- **Polish (Phase 6)**: depends on US1–US3.

### Within User Story 1

- Tests T005–T009 (all `[P]`, distinct test files / fixture) are written first and MUST fail before implementation.
- Implementation order: T010 (dataclass fields) → T011 (`_resolve_setting`/`_build_location`) → T012 (`map_bible` wiring) are sequential (same two source files); T013 (deferrals) and T014 (design doc) are independent and `[P]` with each other.

### Parallel Opportunities

- US1 tests/fixture: **T005, T006, T007** share `tests/io/test_bible.py` so coordinate edits, but **T008** (parity test) and **T009** (fixture dir) are fully `[P]` against them and each other.
- US1 vs US2: once the front-matter contract is fixed (it already is, in contracts/), **T015–T016** can run alongside **T010–T014** — different files.
- Polish **T019** `[P]` with final review; **T020** runs last.

---

## Parallel Example: User Story 1 tests

```bash
# Distinct files — launch together:
Task: "T008 Update parity pins in tests/golem/test_ingestion_parity.py"
Task: "T009 Add fixture tests/fixtures/parity-exercise/bible/locations/"
# tests/io/test_bible.py cases (T005–T007) edit one file — group them into a single change.
```

---

## Implementation Strategy

### MVP First (Foundational + User Story 1)

1. Phase 1 Setup → baseline captured.
2. Phase 2 Foundational → `bible.py` split, existing tests green, ≤ 500 lines.
3. Phase 3 US1 → locations indexed, cross-ref + soft-miss, research resolution, parity green.
4. **STOP and VALIDATE**: run the US1 Independent Test. This is the shippable patch (`v0.3.2`).

### Incremental Delivery

1. Foundational → split landed (invisible).
2. US1 → locations are first-class G13 nodes (the observable delta).
3. US2 → authoring command teaches the front-matter.
4. US3 → backward-compat + size limit verified.
5. Polish → quickstart + all four gates.

---

## Notes

- `[P]` = different files, no dependency on incomplete tasks.
- The frozen ontology is untouched (Principle X): `G13_Narrative_Location` and `dlp:generic-location` already exist — no class/property is added.
- No CLI surface, no `--json` envelope change; the unresolved `setting:` reuses the existing `unresolved_participants` channel (the neutral rename is deferred to iteration 027).
- Commit after each task or logical group (the optional `before_*` git hooks offer this between phases).
