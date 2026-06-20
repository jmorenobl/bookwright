---
description: "Task list for the narrative-structure continuity validator (iteration 031)"
---

# Tasks: Narrative-structure continuity validator

**Input**: Design documents from `/specs/031-narrative-structure-validator/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED — the spec (plan.md "Testing", contracts/) explicitly requires a
new `tests/validation/test_narrative_structure.py` plus a `--json` envelope
assertion in `tests/validation/test_command.py`. Tests are written before the
implementation they cover.

**Organization**: Tasks are grouped by user story (US1 = orphan beat, P1/MVP;
US2 = unresolved role, P2; US3 = contract/config conformance, P3) so each story is
independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete-task dependency)
- **[Story]**: US1, US2, US3 (Setup/Foundational/Polish carry no story label)
- All paths are repository-root-relative (single project, `src/bookwright/`)

## Path Conventions

- Source: `src/bookwright/validation/`
- Tests: `tests/validation/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working baseline before touching code.

- [ ] T001 Confirm a green baseline on branch `031-narrative-structure-validator`: run `uv sync`, then `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` and verify all four gates pass before any edits.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The one shared test-harness change every story's tests depend on. No
production behavior here, but it BLOCKS the test tasks of US1, US2, and US3.

**⚠️ CRITICAL**: No user-story test can be written/run until this is complete.

- [ ] T002 Extend `tests/validation/conftest.py` **additively** (research D10): add a `units=` knob to `write_project` that writes `outline/units/*.md` cards from the given specs, and add an outline-aware indexer builder that runs `map_bible` → `map_outline` → `build_provenance` into a fresh `RdflibIndexer` (mirroring `commands/_graph.py` `build_project_graph`), so fixtures emit `G7`/`G9` triples and outline provenance. Leave the existing `build_indexer` / `write_project` signatures backward-compatible so every existing validator test (FR-011) is untouched.

**Checkpoint**: Test fixtures can now produce the narrative-structure graph and the
combined outline `MapResult`. User-story work can begin.

---

## Phase 3: User Story 1 - Author told which beats are in no plot line (Priority: P1) 🎯 MVP

**Goal**: A `narrative_structure` validator that reports each `G9_Narrative_Unit`
belonging to no `G7_Narrative_Sequence`, answered purely by SPARQL over the derived
graph, citing the unit card's `file:line` (FR-005). This is the shippable MVP.

**Independent Test**: Build the graph for a project with one sequenced unit card and
one unsequenced unit card; run validation; confirm exactly the unsequenced unit is
reported (one `warning` finding with its `file:line`) and the sequenced one is not.

### Tests for User Story 1

> Write these FIRST and confirm they FAIL before T005–T006.

- [ ] T003 [US1] Create `tests/validation/test_narrative_structure.py` with US1 cases (using the T002 helpers): (1) a project with one unsequenced + one sequenced unit card → exactly one `narrative_structure` `warning` finding naming the orphan slug with its `outline/units/...:line` source, sequenced unit not reported (Acceptance 1, SC-001); (2) every unit card sequenced → zero findings (Acceptance 2); (3) no `outline/units/` directory → zero findings, no `errors[]` entry (Acceptance 3, FR-009, SC-004); (4) a sequence whose members carry an `order:` gap/duplicate → **no** order-related finding (FR-007, research D8); (5) **determinism & read-only (FR-008, SC-005, research D9)**: running the validator twice over the same orphan-beat project yields byte-for-byte identical finding lists (after the runner's sort), and running it does **not** mutate the indexer's graph (triple count and contents unchanged before/after) — the validator writes nothing.

### Implementation for User Story 1

- [ ] T004 [P] [US1] In `src/bookwright/validation/queries.py`: import `DLP` from `bookwright.golem.namespaces`, add `("dlp", str(DLP))` to `_PREFIXES`, and add `load_orphan_units(indexer: Indexer) -> list[str]` running the `SELECT ?unit … FILTER NOT EXISTS { ?seq a golem:G7_Narrative_Sequence ; dlp:proper-part ?unit }` query (data-model.md / research D3), returning the URIs **sorted** for determinism (research D9).
- [ ] T005 [US1] Create `src/bookwright/validation/validators/narrative_structure.py` with the `NarrativeStructure` class: `name: ClassVar[str] = "narrative_structure"`, `severity_default: ClassVar[Severity] = Severity.warning` (research D2), conforming to the `Validator` protocol. Implement the Rule a branch in `validate`: call `queries.load_orphan_units(indexer)`, and for each orphan URI emit one `Violation` (`validator="narrative_structure"`, `severity=warning`, message naming the unit by URI localname/slug, `source=resolve_source(indexer, unit_uri)`, `triples=()`) — data-model.md "Finding: orphan beat", research D4. No hand-registration (auto-discovered, FR-002/research D1).

**Checkpoint**: US1 is fully functional and independently testable — the orphan-beat
MVP. The validator is auto-discovered, runs through the existing runner, and emits
through the existing `--json` envelope.

---

## Phase 4: User Story 2 - Author told which beat references a non-existent role (Priority: P2)

**Goal**: The same validator additionally reports each unit card whose `roles:` names
a slug resolving to no character role, re-surfaced from the outline ingestion's
already-emitted `UnresolvedReference` records via a new cached
`ValidationContext.outline()` accessor (FR-006).

**Independent Test**: Build a project with one unit card whose `roles:` names a slug
no character plays and another whose `roles:` all resolve; run validation; confirm
exactly the bad reference is reported (beat name + unresolved role name + the card's
`file:line`) and the good card is not.

### Tests for User Story 2

> Write these FIRST and confirm they FAIL before T007–T008.

- [ ] T006 [US2] Add US2 cases to `tests/validation/test_narrative_structure.py` (same file as T003): (1) a unit card whose `roles:` names an unresolvable slug → one `warning` finding naming the beat and the unresolved role with the card's `file:line` (Acceptance 1, SC-002); (2) a card whose `roles:` all resolve → no finding for it (Acceptance 2); (3) no `outline/units/` → no unresolved-role finding (Acceptance 3, FR-009); assert a bible-level `UnresolvedReference` (e.g. a `participants:` miss) is NOT reported by this validator (the `"{outline}/units/"` path filter, research D6).

### Implementation for User Story 2

- [ ] T007 [P] [US2] In `src/bookwright/validation/base.py`: add a `_outline` sentinel field (`field(default=_UNSET, repr=False, compare=False)`) to `ValidationContext` and a cached `outline() -> MapResult` accessor mirroring `bible()`, running `map_bible(root, bible_dir, uri_base)` then `map_outline(root, root / paths.outline, uri_base, result)` and caching the combined `MapResult` (research D5; no vocabularies — research D5 note). Writes nothing.
- [ ] T008 [US2] Add the Rule c branch to `src/bookwright/validation/validators/narrative_structure.py`: read `project.outline().unresolved_references`, filter to records whose `path` is under `"{outline}/units/"` (where `outline = manifest.paths.outline.rstrip("/")`, research D6), and for each emit one `Violation` (message naming `ref.entity` beat + `ref.name` role; `source` via `resolve_source(indexer, unit_uri)` where `unit_uri` comes from a `{name: uri}` map built from `outline().mapped`, falling back to `ref.path`, research D7; `triples=()`). Sort references by `(path, entity, name)` (research D9). Reuse the records — do not re-implement role resolution (FR-006).

**Checkpoint**: US1 and US2 both work independently; each rule fires on its own
project and both fire on a unit that is both orphaned and bad-role-referencing.

---

## Phase 5: User Story 3 - Author can turn the validator off like any other (Priority: P3)

**Goal**: Confirm contract conformance — the validator is in the default active set,
is enable/disable-able by name, and serializes through the existing `--json` envelope
with no new top-level key (FR-002/FR-003/FR-010).

**Independent Test**: Resolve the active validators for a default project and confirm
`narrative_structure` is present; add it to `[validators] disabled` and confirm it
does not run and produces no findings; confirm a finding serializes through the
existing report shape with no new envelope key.

### Tests for User Story 3

- [ ] T009 [US3] Add US3 cases to `tests/validation/test_narrative_structure.py` (same file as T003/T006): (1) `narrative_structure` is in the resolved active set for a default project (Acceptance 1, FR-002); (2) with `[validators] disabled = ["narrative_structure"]` it does not appear in `summary.ran` and emits no findings, every other validator unchanged (Acceptance 2, SC-006); (3) with `[validators] enabled = ["narrative_structure"]` only it runs.
- [ ] T010 [P] [US3] Add a `--json` envelope assertion to `tests/validation/test_command.py` (additive): for an orphan-beat project, the `narrative_structure` finding appears in `violations[]` with the existing finding shape (validator, severity, message, source, triples), `failed` stays `false` for a warning-only run, and the envelope gains no new top-level key (FR-003, SC-003, contracts §"Output envelope").

**Checkpoint**: All three user stories independently functional; the validator is a
first-class, configurable member of the suite.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify the whole feature against gates and the quickstart.

- [ ] T011 Run all four gates green: `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` (coverage ≥ 80 %, single-sourced in `pyproject`). Confirm no existing validator's behavior/findings/severity changed (FR-011) and the frozen ontology is untouched — no class/property added to `golem.ttl` (FR-012, SC-007).
- [ ] T012 Walk `specs/031-narrative-structure-validator/quickstart.md` scenarios 1–6 against a scratch project to confirm the documented end-to-end behavior (orphan flagged, clean/inert produce nothing, unresolved role flagged, order-gap not flagged, disable-by-name removes findings).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: no dependencies — confirm baseline first.
- **Foundational (T002)**: depends on T001; BLOCKS every test task (T003, T006, T009, T010).
- **US1 (T003–T005)**: depends on T002. The MVP; independently shippable.
- **US2 (T006–T008)**: depends on T002; T008 edits the validator module T005 created, so US2 implementation follows US1's T005 (shared file). Otherwise behaviorally independent of US1.
- **US3 (T009–T010)**: depends on the validator existing (T005); behaviorally independent of US2.
- **Polish (T011–T012)**: depends on all desired stories complete.

### Within Each User Story

- Tests (T003 / T006 / T009 / T010) are written and FAIL before their implementation.
- US1: T004 (`queries.load_orphan_units`) before T005 (validator uses it).
- US2: T007 (`outline()` accessor) before T008 (validator reads it).

### Parallel Opportunities

- T004 (`queries.py`) and T007 (`base.py`) touch different files from the validator
  module and from each other — parallelizable once their story's test exists, but
  note T005 depends on T004 and T008 depends on T007.
- T010 (`test_command.py`) is a different file from `test_narrative_structure.py`,
  so it is [P] relative to T003/T006/T009.
- **Not parallel**: T003, T006, T009 all edit `tests/validation/test_narrative_structure.py`;
  T005 and T008 both edit `validators/narrative_structure.py`. Same-file tasks run sequentially.

---

## Parallel Example: cross-story implementation helpers

```bash
# After T002 + the relevant test tasks, the two seam helpers live in different files:
Task: "T004 [US1] add dlp prefix + load_orphan_units in src/bookwright/validation/queries.py"
Task: "T007 [US2] add ValidationContext.outline() + _outline in src/bookwright/validation/base.py"
# Then the validator module (T005 then T008) consumes both — sequential, same file.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 Setup (green baseline).
2. T002 Foundational test harness (CRITICAL — blocks all story tests).
3. T003–T005 US1: orphan-beat rule via SPARQL.
4. **STOP and VALIDATE**: orphan beat flagged, clean/inert produce nothing, order-gap not flagged.
5. Ships as a complete, useful validator — the first consumer of the v0.4 layer.

### Incremental Delivery

1. Setup + Foundational → harness ready.
2. US1 (orphan beat) → test independently → MVP.
3. US2 (unresolved role) → test independently → adds the ingestion-soft-miss surface.
4. US3 (config/envelope conformance) → test independently → first-class suite member.
5. Polish (gates + quickstart) → done.

---

## Notes

- [P] = different files, no incomplete-task dependency.
- This iteration adds **no** CLI subcommand, **no** ontology class/property, **no** new
  runtime dependency, and **no** new top-level `--json` key (Principles IV/X/II/IX).
- Findings default to `warning` (FR-013) — never gate CI.
- Commit after each task or logical group; keep the tree green between phases.
