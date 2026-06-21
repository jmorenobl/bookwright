---
description: "Task list for iteration 033 — remove dead NarrativeRole + harden ingestion-parity"
---

# Tasks: Remove dead `NarrativeRole` concept + harden ingestion-parity

**Input**: Design documents from `/specs/033-remove-dead-narrativerole/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/golem-surface.md ✓, quickstart.md ✓

**Tests**: This iteration does not add a new test-first suite. It **edits
existing tests** (`test_triples.py`, `test_uri.py`, `test_namespaces.py`,
`test_ingestion_parity.py`) so they stop exercising the deleted class while
relocating G11 coverage onto its real carrier and *adding* two new parity
invariants. Those test edits are implementation tasks, listed inline in the
story phases — not a separate TDD block.

**Organization**: Tasks are grouped by the four user stories from spec.md. Each
file is touched by **exactly one** task (the change is a single atomic refactor;
file-atomic tasks avoid same-file conflicts across phases).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: `[US1]`..`[US4]` maps to the spec's user stories
- Exact file paths are given in every task

## Path Conventions

Single project, src-layout: source under `src/bookwright/`, tests under
`tests/`, plain-text ledgers at repo root. Unchanged by this iteration.

---

## Phase 1: Setup (baseline for the zero-regression proof)

**Purpose**: Capture the pre-change graph so SC-002 (zero triple regression) can
be proven by diff, not asserted by faith.

- [X] T001 Capture a pre-change Turtle baseline of the G11-bearing fixture: run `uv run bookwright graph build --root tests/fixtures/parity-exercise` and save the emitted graph (e.g. `cp tests/fixtures/parity-exercise/bible/graph.ttl /tmp/g11-baseline.ttl`) so the post-change build can be diffed against it for byte-for-byte `golem:G11_Narrative_Role` equivalence.

**Checkpoint**: Baseline captured — the deletion can now be made and verified.

---

## Phase 2: Foundational (the deletion every story builds on)

**Purpose**: Remove the dead concept from the GOLEM package surface. This is the
single mutation all four user stories depend on; until it lands, the count
sweeps, the coverage relocation, and the parity hardening have nothing to react
to.

**⚠️ CRITICAL**: After this phase the test suite is transiently red (test files
still import `NarrativeRole`); US1/US2 restore green. This is expected — the
phase is a blocking prerequisite, not an independently shippable increment.

- [X] T002 Delete the `NarrativeRole` class definition from `src/bookwright/golem/modules/narrative.py` (FR-001). Leave every other concept in the module untouched; the file shrinks.
- [X] T003 In `src/bookwright/golem/__init__.py` remove the three `NarrativeRole` references — the import, the `CONCEPTS` entry (→ exactly 12 concepts), and the `__all__` entry — and reconcile the module docstring "the thirteen GOLEM concept classes" → "the twelve GOLEM concept classes" (FR-002, FR-003). Do **not** touch `golem/namespaces.py` — `CLASS_IRI["NarrativeRole"]` is preserved.

**Checkpoint**: `from bookwright.golem import CONCEPTS` yields 12 entries with `NarrativeRole` absent; `from bookwright.golem import NarrativeRole` raises `ImportError`.

---

## Phase 3: User Story 1 - The concept registry is honest (Priority: P1) 🎯 MVP

**Goal**: Every listed concept is materialized or explicitly deferred — no third
"dead but counted reachable" category. The registry and its prose tell the truth.

**Independent Test**: `uv run python -c "from bookwright.golem import CONCEPTS; assert len(CONCEPTS)==12 and 'NarrativeRole' not in CONCEPTS"`; and `grep -rniE "thirteen|eleven" src/ tests/ --exclude-dir=__pycache__` returns no live concept-count assertion — both the "thirteen"/"twelve" total-count and the "eleven"/"ten" reachable-count word forms are reconciled (only frozen `CHANGELOG.md` history retains "thirteen", and it is out of `src/`/`tests/`).

- [X] T004 [P] [US1] In `src/bookwright/golem/deferrals.py` reconcile the count prose "Two of the thirteen" → "Two of the twelve" (FR-003). Do **not** change `DEFERRED_CONCEPTS` — its two entries (`RelationshipRole`, `PsychologicalState`) and their `demand-pulled` targets are out of scope (FR-010).
- [X] T005 [US1] Verify the honest-registry contract (no new file): assert `len(CONCEPTS) == 12`, `"NarrativeRole"` absent from `CONCEPTS`/`__all__`/all imports, and run a repo-wide `grep -rniE "thirteen|eleven|NarrativeRole" src/ tests/ --exclude-dir=__pycache__` confirming no live reference to a *top-level* `NarrativeRole` concept survives and no stale reachable-count token — neither "thirteen"/"twelve" total nor "eleven"/"ten" reachable — remains in live source/tests (FR-003, SC-001; the final SC-007 grep sweep runs in Phase 7).

**Checkpoint**: The concept registry and its live prose are honest — 12 concepts, no dead entry, no stale "thirteen".

---

## Phase 4: User Story 2 - No information or capability is lost (Priority: P1)

**Goal**: Zero triple regression and zero ontology change. G11 stays a frozen
first-class class, still emitted by `CharacterRole`; the test suite still covers
G11's triple/URI behaviour — relocated onto the real carrier, never dropped.

**Independent Test**: `CLASS_IRI` still holds 17 IRIs (incl. G11); `git diff --quiet -- src/bookwright/resources/schemas` (golem.ttl unchanged); the post-change `parity-exercise` graph build diffs clean against the Phase-1 baseline; `CharacterRole` still emits the `golem:G11_Narrative_Role` type.

- [X] T006 [P] [US2] Rewrite the `CharacterRole` docstring in `src/bookwright/golem/modules/feature.py` (FR-012): drop "Distinct from the top-level `NarrativeRole` concept…" and describe `CharacterRole` as the **sole** materialization of `golem:G11_Narrative_Role`. Leave `golem_class = CLASS_IRI["NarrativeRole"]` and all triple output untouched (FR-005).
- [X] T007 [P] [US2] In `tests/golem/test_triples.py` remove the `NarrativeRole` import and instantiation; route any `NarrativeUnit.roles` cross-ref through a bare `URIRef`; relocate the G11 triple/type coverage the dead class provided onto the real carrier `CharacterRole` (whose G11 typing is already asserted in `tests/golem/test_character_attributes.py:50`), so coverage does not silently drop (FR-008b).
- [X] T008 [P] [US2] In `tests/golem/test_uri.py` drop `NarrativeRole` from the `SEGMENTS` table and reconcile "12 slugged concepts" → "11" (FR-003, FR-008); keep G11 URI-pattern coverage via the `CharacterRole` character-scoped node URI (`test_character_scoped_node_uri_patterns`).
- [X] T009 [P] [US2] In `tests/golem/test_namespaces.py` **reclassify** G11's IRI from the concept bucket into the non-`CONCEPTS` carrier bucket (`12 + 5 == 17`, was `13 + 4`) and rename the `test_class_iri_maps_thirteen_concepts_plus_attribute_carriers` test off the stale "thirteen" count, updating its "13 narrative concepts" docstring — preserving the frozen 17-IRI closure assertion, never lowering the count or deleting an assertion (FR-004, FR-008a).
- [X] T010 [US2] Verify zero information loss (depends on T002, T003, T006–T009): `CLASS_IRI` == 17 with `"NarrativeRole"` present; `golem.ttl`/`schemas` byte-for-byte unchanged (`git diff --quiet`); rebuild `tests/fixtures/parity-exercise` and diff against `/tmp/g11-baseline.ttl` (identical `golem:G11_Narrative_Role` triples); `CharacterRole(...).to_triples()` still emits the G11 type (quickstart §2–3, SC-002/SC-003).

**Checkpoint**: The frozen ontology is untouched and every G11 triple is preserved; G11 coverage lives on `CharacterRole`.

---

## Phase 5: User Story 3 - A dead concept cannot re-enter via carrier IRI collision (Priority: P1)

**Goal**: Harden the ingestion-parity contract so a `CONCEPTS` member whose
class IRI is materialized only by a non-`CONCEPTS` carrier (the DEBT-001 pattern)
is *named* as a failure, not silently counted reachable.

**Independent Test**: `uv run pytest tests/golem/test_ingestion_parity.py -q` is green, including the new `carrier_iri_collisions` invariant (empty for the real registry) and the drift sim that re-adds `"NarrativeRole"` to a local copy and asserts it is named as a collision failure.

- [X] T011 [US3] Harden `tests/golem/test_ingestion_parity.py` (FR-006, FR-007, SC-004): (a) drop `NarrativeRole` from the pinned `EXPECTED_REACHABLE` set (→ 10 names); (b) add `"NarrativeRole"` to `CARRIER_NAMES` (→ 5: `CharacterFeature`, `Dimension`, `Type`, `TimeInterval`, `NarrativeRole`); (c) add the pure helper `carrier_iri_collisions(concepts)` per contract C4; (d) assert carrier-IRI disjointness `carrier_iri_collisions(set(CONCEPTS)) == set()`; (e) add the drift sim asserting `"NarrativeRole" in carrier_iri_collisions(set(CONCEPTS) | {"NarrativeRole"})`; (f) reconcile **every** stale reachable-count token in this file (doctrine §4, FR-003): the module docstring "Eleven of the thirteen" → "Ten of the twelve" **and** the two inline comments ("The eleven concepts the fixture's authored text materializes" line ~34, "Exactly the eleven reachable concepts materialize" line ~119) → "ten" — leaving no live "eleven"/"thirteen" reachable count in the file. Keep the orphan set observed from a real build `== set(DEFERRED_CONCEPTS) == {RelationshipRole, PsychologicalState}` and the existing drift sims passing unchanged.
- [X] T012 [P] [US3] Rewrite the header comment of `tests/fixtures/parity-exercise/manifest.toml` (FR-012) so it describes `golem:G11_Narrative_Role` as materialized solely by the character-scoped `CharacterRole` carrier, not as a top-level `NarrativeRole` reachable ingestion path. Touch only the comment; the fixture's `narrative_roles:` authoring stays as the live G11 observation source.
- [X] T013 [US3] Verify the hardened contract (depends on T011, T012): `uv run pytest tests/golem/test_ingestion_parity.py -q` green incl. the collision invariant and drift sim (quickstart §4, SC-004).

**Checkpoint**: The DEBT-001 loophole is provably closed — re-adding a carrier-only-IRI concept is named as a parity failure.

---

## Phase 6: User Story 4 - The debt ledger reflects reality (Priority: P2)

**Goal**: The resolved DEBT-001 entry is deleted (git keeps history); no tracked
plain-text still points to it as open.

**Independent Test**: `grep -q "DEBT-001" DEBT.md` returns non-zero (absent); no other entry references the `NarrativeRole` dead-concept gap.

- [X] T014 [P] [US4] Remove the `### DEBT-001 …` block from `DEBT.md` (FR-009, SC-005); update the "Deuda abierta" section so it reflects the new state with no archival stub.
- [X] T015 [P] [US4] In `bookwright-roadmap.md` remove (or reconcile to "resolved") the § 4 *"Decisión estructural sobre `NarrativeRole` (DEBT-001)"* item — its open decision is now made (the concept is eliminated) (FR-009). Leave the G11 status row (line ~112: "G11 ✅ inline vía `narrative_roles:`") untouched — it stays accurate.

**Checkpoint**: The plain-text ledger records only open debt; DEBT-001 is gone.

---

## Phase 7: Polish & Cross-Cutting Concerns (verification gates)

**Purpose**: Prove the whole change against the spec's success criteria.

- [X] T016 Run the SC-007 grep contract: `grep -rn NarrativeRole src/ tests/ --exclude-dir=__pycache__` returns **only** the preserved-key / carrier uses enumerated in contract C5 (`golem/namespaces.py`, `golem/modules/feature.py`, `tests/golem/test_character_attributes.py`, `tests/golem/test_namespaces.py` carrier bucket, `tests/golem/test_ingestion_parity.py` `CARRIER_NAMES`) — no top-level-concept import/`CONCEPTS`/`__all__`/segment/`EXPECTED_REACHABLE` reference (SC-007).
- [X] T017 Run all four CI gates green (FR-011, SC-006): `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` (≥ 80 % coverage enforced by `[tool.coverage.report]`).
- [X] T018 Walk the `quickstart.md` checks end to end (§1–§7) and confirm each prints its ✓; clean up `/tmp/g11-baseline.ttl`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — run first to capture the baseline.
- **Foundational (Phase 2)**: depends on Setup — **blocks all user stories** (it is the deletion everything reacts to).
- **User Stories (Phase 3–6)**: all depend on Foundational. US1/US2/US3 are all P1; US4 is P2. They edit disjoint files and can proceed in parallel once Phase 2 lands. The **suite returns green only after US1+US2** restore the test files the deletion broke.
- **Polish (Phase 7)**: depends on all four stories being complete.

### User Story Dependencies

- **US1 (P1)**: registry/count honesty — files: `deferrals.py` + verification. Independent of US2–US4.
- **US2 (P1)**: ontology/coverage preservation — files: `feature.py`, `test_triples.py`, `test_uri.py`, `test_namespaces.py`. Independent of US1/US3/US4.
- **US3 (P1)**: parity hardening — files: `test_ingestion_parity.py`, `parity-exercise/manifest.toml`. Independent of US1/US2/US4.
- **US4 (P2)**: ledger — files: `DEBT.md`, `bookwright-roadmap.md`. Independent of all.

### Within Each User Story

- The file-edit tasks are independent (different files, all `[P]`).
- Each story's verification task (T005, T010, T013) depends on that story's edits (and on Foundational).

### Parallel Opportunities

- US2's four edits (T006, T007, T008, T009) run in parallel.
- US3's two edits (T011, T012) run in parallel (T011 is the only edit to its file; T012 a different file).
- US4's two edits (T014, T015) run in parallel.
- Across stories: once Phase 2 lands, T004/T006/T007/T008/T009/T011/T012/T014/T015 are all different files and can run together.

---

## Parallel Example: after Foundational (Phase 2) completes

```bash
# All file-atomic edits across US1–US4 touch disjoint files — launch together:
Task: "T004 deferrals.py count thirteen→twelve"
Task: "T006 feature.py CharacterRole docstring rewrite"
Task: "T007 test_triples.py drop NarrativeRole, relocate G11 to CharacterRole"
Task: "T008 test_uri.py drop SEGMENTS entry, 12→11 slugged"
Task: "T009 test_namespaces.py reclassify G11 IRI, 12+5=17, rename test"
Task: "T011 test_ingestion_parity.py harden (CARRIER_NAMES + collisions + drift)"
Task: "T012 parity-exercise/manifest.toml header rewrite"
Task: "T014 DEBT.md remove DEBT-001"
Task: "T015 bookwright-roadmap.md reconcile §4 entry"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 (baseline) → Phase 2 (the deletion) → Phase 3 (US1).
2. **STOP and VALIDATE**: `CONCEPTS == 12`, `NarrativeRole` absent, no stale "thirteen" in live source. The registry is honest — the core defect is closed.

### Incremental Delivery

1. Setup + Foundational → the dead concept is gone (suite transiently red).
2. US1 → honest registry (MVP).
3. US2 → suite green again; ontology proven unchanged, G11 coverage relocated.
4. US3 → DEBT-001 loophole provably closed.
5. US4 → ledger cleaned.
6. Polish → SC-007 grep + four gates + quickstart all green ⇒ iteration done.

Because this is one atomic refactor, the realistic order is **Phase 1 → 2 → (US1+US2 together to restore green) → US3 → US4 → Phase 7**.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task.
- Every touched file is owned by exactly one task — no same-file contention.
- The frozen ontology is the load-bearing guard: `golem.ttl`/`schemas` and the 17-IRI `CLASS_IRI` closure MUST NOT change (Principle X). T010 and T016/T017 verify this.
- Commit after each story (the `after_tasks`/`after_implement` git hooks offer this).
- Do **not** edit: `golem/namespaces.py` (key preserved), `golem.ttl`/`schemas/` (frozen), `CHANGELOG.md` (frozen history — Principle I), `tests/golem/test_character_attributes.py` (the relocation target — already covers the carrier), `specs/005-golem-domain-model/` (frozen historical artifact).
