---
description: "Task list for iteration 024 — Ingestion-parity guard + deferral registry"
---

# Tasks: Ingestion-parity guard + deferral registry

**Input**: Design documents from `/specs/024-ingestion-parity-guard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/parity-contract.md, quickstart.md

**Tests**: This iteration **is** a test/registry/docs iteration. The parity test is the
observable deliverable (US1/US2), so test tasks are mandatory and ordered TDD-first per
the user hint: build the static registry + the exercise fixture, then write the parity
test (live probe + reachable-set pin + three drift simulations via the pure `parity_diff`
helper), then add the two behavior-neutral doc notes last.

**Organization**: Tasks are grouped by user story. US1 (contract) and US2 (liveness) are
co-equal P1 and share a single test module (`tests/golem/test_ingestion_parity.py`); they
are presented together in Phase 3. US3 (docs) is P2 and lands last.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 (Setup/Foundational/Polish carry no story label)
- File paths are exact and relative to repo root.

## Path Conventions

Single project, src-layout (Constitution III): `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the baseline the guard reads from is exactly as the design assumes.

- [ ] T001 Confirm the closure baseline before adding anything: verify `CONCEPTS` (in `src/bookwright/golem/__init__.py`) has exactly 13 keys and `CLASS_IRI` (in `src/bookwright/golem/namespaces.py`) carries the four non-concept carriers (`CharacterFeature`, `Dimension`, `Type`, `TimeInterval`) plus the 13 concept IRIs — record the exact concept names (`Character`, `Setting`, `NarrativeEvent`, `SocialRelationship`, `NarrativeRole`, `AttributeAssignment`, `NarrativeLocation`, `Object`, `NarrativeUnit`, `NarrativeFunction`, `NarrativeSequence`, `RelationshipRole`, `PsychologicalState`) to use verbatim as registry keys. Do NOT edit either file (Principle X; per the hint "no toques `golem/` salvo el registro nuevo").

**Checkpoint**: Concept names and carriers confirmed — registry + fixture can be authored against real keys.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the two static artifacts the parity test consumes — the deferral
registry (US1's core data) and the exercise fixture (US2's corpus). Per the TDD ordering,
both land before the test module is written.

**⚠️ CRITICAL**: The parity test (Phase 3) cannot be written or run until both exist.

- [ ] T002 [P] Create the deferral registry module `src/bookwright/golem/deferrals.py`: define `class DeferralNote(NamedTuple): reason: str; target_version: str` and `DEFERRED_CONCEPTS: dict[str, DeferralNote]` with **exactly seven** entries keyed by concept name — `NarrativeLocation`→`v0.3.x`, `Object`→`v0.3.x`, `NarrativeUnit`→`v0.4`, `NarrativeFunction`→`v0.4`, `NarrativeSequence`→`v0.4`, `RelationshipRole`→`undecided`, `PsychologicalState`→`undecided` — each with a non-empty one-clause reason from data-model.md §DEFERRED_CONCEPTS. Import only `typing` (no `CONCEPTS` import — keep the module dependency-free per contracts §1); add a module docstring stating it is consumed solely by the parity test and that removing one entry is the single edit that wires a concept (FR-002, FR-012, SC-002, research D4).
- [ ] T003 [P] Create the exercise fixture root `tests/fixtures/parity-exercise/` with a valid `bookwright.toml` manifest (mirror the minimal shape of an existing fixture, e.g. `tests/fixtures/tiny-historical/bookwright.toml`) so `build_project_graph(root, manifest)` and `bookwright graph build` exit clean (data-model.md §Exercise fixture, FR-004).
- [ ] T004 [P] Author the fixture character `tests/fixtures/parity-exercise/bible/characters/<one>.md` with front-matter carrying a non-empty `narrative_roles:` list **and** `born:`/`features:` so the build materializes `Character`, `NarrativeRole`, the `CharacterFeature` carrier, and the `AttributeAssignment` provenance reification (FR-004; assumption "NarrativeRole counts as reachable").
- [ ] T005 [P] Author the fixture setting `tests/fixtures/parity-exercise/bible/settings/<one>.md` (one Setting) and `tests/fixtures/parity-exercise/bible/timeline.md` with ≥1 `events:` item (one NarrativeEvent) (FR-004, data-model.md §Exercise fixture).
- [ ] T006 [P] Author the fixture `tests/fixtures/parity-exercise/bible/relationships.md` with ≥1 `relationships:` item whose participants resolve to the authored character/setting (no slug collisions) — this is the one path no committed fixture exercises (`SocialRelationship`, [bible.py:210](../../src/bookwright/io/bible.py#L210); research D1) — plus `tests/fixtures/parity-exercise/bible/constitution.md` for scaffold completeness.
- [ ] T007 Manually verify the fixture exercises every path before any test depends on it: run `uv run --project . bookwright graph build` from a copy of `tests/fixtures/parity-exercise/` and confirm exit 0 and that `bible/graph.ttl` contains the six concept IRIs (`G1_Character`, `G12_Setting`, `G5_Narrative_Event`, `G4_Social_Relationship`, `G11_Narrative_Role`, `E13_Attribute_Assignment`) and **none** of the seven orphan IRIs (per quickstart.md §2). If any reachable IRI is missing, fix the front-matter in T004–T006 (the fixture must not under-exercise a path — spec Edge Cases).

**Checkpoint**: Registry + fixture exist and the fixture provably materializes the six reachable concepts — the parity test can now be written.

---

## Phase 3: US1 + US2 — The orphan/deferral contract holds, observed against reality (Priority: P1) 🎯 MVP

**Goal**: A single deterministic test asserts that the orphan set derived from a real
graph build of the fixture equals exactly the deferral registry's keys (US1), where the
"alive" set is observed from the graph the engine actually produces, never hand-listed
(US2). On drift it fails naming the offending concept.

**Independent Test**: `uv run pytest tests/golem/test_ingestion_parity.py -v` — passes on
current code; the reachable-set pin confirms exactly the six reachable concepts and no
orphan IRI; the three drift simulations each fail naming the offending concept.

### Tests for US1 + US2 (write FIRST; the live + pin assertions must pass on current code, the simulations must fail under perturbed copies)

- [ ] T008 [US2] In a new module `tests/golem/test_ingestion_parity.py`, add a session/module-scoped fixture that loads the `parity-exercise` manifest and calls `build_project_graph(parity_exercise_root, manifest)` ([_graph.py:75](../../src/bookwright/commands/_graph.py#L75)), then collects observed `rdf:type` IRIs via `outcome.engine.query("SELECT DISTINCT ?t WHERE { ?s a ?t }")`. Derive `reachable = {name for name in CONCEPTS if CLASS_IRI[name] in types}` and `orphans = set(CONCEPTS) - reachable` (FR-003, research D2/D3).
- [ ] T009 [P] [US2] Add the **reachable-set pin** test: assert `reachable == {"Character", "Setting", "NarrativeEvent", "SocialRelationship", "NarrativeRole", "AttributeAssignment"}` and that **none** of the seven orphan IRIs (`NarrativeLocation`, `Object`, `PsychologicalState`, `RelationshipRole`, `NarrativeUnit`, `NarrativeFunction`, `NarrativeSequence`) appears in the observed `types` (US2 scenarios 1–2, FR-004).
- [ ] T010 [P] [US1] Add the **registry well-formedness** test: assert `set(DEFERRED_CONCEPTS) <= set(CONCEPTS)`, `len(DEFERRED_CONCEPTS) == 7`, the key set equals the seven names, every `reason`/`target_version` is non-empty, and no carrier name (`CharacterFeature`, `Dimension`, `Type`, `TimeInterval`) appears (FR-002, FR-010, SC-002, contracts §1).
- [ ] T011 [US1] Define the pure helper `parity_diff(reachable: set[str], deferred: set[str]) -> tuple[set[str], set[str]]` returning `(fed_but_deferred = reachable & deferred, undeclared_orphans = (set(CONCEPTS) - reachable) - deferred)` in `tests/golem/test_ingestion_parity.py`, with a docstring tying it to FR-006/007/008 (data-model.md §Failure-message contract, research D5).
- [ ] T012 [US1] Add the **live guard** test: assert `orphans == set(DEFERRED_CONCEPTS)`; on failure, call `parity_diff(reachable, set(DEFERRED_CONCEPTS))` and include both returned sets in the assertion message so a real drift names the offending concept(s) (FR-005, SC-001, contracts §2).
- [ ] T013 [P] [US1] Add the three **drift-simulation** tests driving `parity_diff` on perturbed *local copies* (never mutating `DEFERRED_CONCEPTS`): (a) a reachable concept added to the deferred copy → `fed_but_deferred` names it (FR-006); (b) same condition viewed from the registry side (FR-007); (c) a real orphan dropped from the deferred copy → `undeclared_orphans` names it (FR-008). Assert each named concept appears in the corresponding returned set (SC-003, contracts §3, research D5).
- [ ] T014 [P] [US2] Add the **determinism** test: build/derive (or re-query the cached engine for) `reachable`/`orphans` twice and assert the two verdicts are identical, since the probe is `DISTINCT ?t` (set-valued, order-independent) and `parity_diff` is a pure set function (FR-009, SC-004, contracts §2).

**Checkpoint**: `uv run pytest tests/golem/test_ingestion_parity.py -v` is green; the guard, the reachable-set pin, registry well-formedness, the three named-failure simulations, and determinism all hold. MVP delivered.

---

## Phase 4: US3 — Author-only directories documented, not silently inert (Priority: P2)

**Goal**: Document, with zero behavioral change, that `outline/` and `manuscript/` are
author-only in v0.3 — scaffold-created, engine-not-ingested.

**Independent Test**: `grep -i outline src/bookwright/io/manuscript.py docs/authoring.md`
shows the note in both; the full suite confirms no ingestion behavior changed.

- [ ] T015 [P] [US3] Extend the module docstring of [src/bookwright/io/manuscript.py](../../src/bookwright/io/manuscript.py) (which already says v0 does no prose mining) so it explicitly states that **both** `manuscript/` and `outline/` are author-only in v0.3 — presence/scaffold only, engine does not ingest them — and points to the deferral rationale. Change docstring **only**; `manuscript_present` and all logic stay byte-identical (FR-011, SC-005, research D6). English (code convention).
- [ ] T016 [P] [US3] Add one Spanish line to [docs/authoring.md](../../docs/authoring.md) stating that `outline/` and `manuscript/` are author-only in v0.3 (the scaffold creates them but the engine does not ingest them) (FR-011, SC-005, research D6). Spanish (docs convention, CLAUDE.md).

**Checkpoint**: Both notes present; no ingestion path was added; behavior unchanged.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Prove determinism, behavior-neutrality, and the four CI gates per quickstart.

- [ ] T017 Run the quickstart end to end (quickstart.md §1–§5): the registry one-liner (§3) prints the seven sorted keys; the fixture build (§2) shows the six IRIs and no orphan IRI; the parity test passes twice with identical verdict (§5/SC-004).
- [ ] T018 Run the full suite to confirm behavior-neutrality (SC-005): `uv run pytest` stays green with the 023 orchestration E2E (`tests/e2e/test_orchestration_workflow.py`) and the closure tests (`test_frozen_ontology.py`, `test_namespaces.py`) **unchanged** — no class/property added to the frozen closure (SC-006, Principle X).
- [ ] T019 Run the four CI gates green (SC-006): `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥80% coverage, single-sourced in `pyproject`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup (T001 confirms the names used). Registry (T002) and fixture (T003–T007) are independent of each other but both BLOCK Phase 3.
- **US1 + US2 (Phase 3)**: Depends on T002 (registry) and T007 (verified fixture). The single test module is the joint deliverable.
- **US3 (Phase 4)**: Independent of Phase 2/3 — can run any time after Setup; ordered last because it is behavior-neutral docs (user hint).
- **Polish (Phase 5)**: Depends on Phases 3 and 4 being complete.

### Within Phase 3

- T008 (probe fixture) before T009/T012/T014 (they consume `reachable`/`orphans`).
- T011 (`parity_diff`) before T012 (live message) and T013 (simulations).
- T009, T010, T013, T014 are mutually parallel once their prerequisite (T008/T011) exists.

### Parallel Opportunities

- **Phase 2**: T002 (registry) ∥ T004 ∥ T005 ∥ T006 (distinct fixture files); T003 before the build-dependent T007. T002 and the whole fixture set run fully in parallel.
- **Phase 3**: after T008 → T009 ∥ T014; after T011 → T013. (All edit the same test file, so "parallel" = independent authorship; commit as one logical group.)
- **Phase 4**: T015 (code) ∥ T016 (docs) — different files, no dependency.

---

## Parallel Example: Phase 2 (Foundational artifacts)

```bash
# Registry and the four fixture files are independent — author together:
Task: "Create src/bookwright/golem/deferrals.py (DeferralNote + DEFERRED_CONCEPTS)"   # T002
Task: "Author tests/fixtures/parity-exercise/bible/characters/<one>.md"               # T004
Task: "Author tests/fixtures/parity-exercise/bible/settings/<one>.md + timeline.md"   # T005
Task: "Author tests/fixtures/parity-exercise/bible/relationships.md + constitution.md"# T006
# Then T007 verifies the assembled fixture builds clean.
```

---

## Implementation Strategy

### MVP (US1 + US2 — the whole point of the iteration)

1. Phase 1: Setup (confirm names).
2. Phase 2: Foundational — registry + fixture, verified by a clean build (T007).
3. Phase 3: the parity test — live guard, reachable-set pin, registry well-formedness, three named-failure simulations, determinism.
4. **STOP and VALIDATE**: `uv run pytest tests/golem/test_ingestion_parity.py -v` green.

### Incremental Delivery

1. Setup + Foundational → artifacts ready.
2. US1 + US2 → the enforced contract (MVP, the observable delta of patch `v0.3.1`).
3. US3 → the two behavior-neutral doc notes.
4. Polish → quickstart + full suite + four gates.

---

## Notes

- [P] = different files, no dependencies; for the shared test module it means independent authorship, committed as one group.
- Behavior-neutral iteration: no CLI surface, no `--json` envelope, no class/property added to the frozen closure (Principle X), no orphan wired.
- The single edit that wires a concept later is removing its entry from `DEFERRED_CONCEPTS` (FR-012) — the parity test stays green only if a builder feeds it.
- Verify the fixture build (T007) before depending on it; verify the parity test fails under each simulated drift (T013).
- Keep `tiny-historical`/`tiny-novel` untouched — the parity corpus is the dedicated `parity-exercise` fixture (research D1).
