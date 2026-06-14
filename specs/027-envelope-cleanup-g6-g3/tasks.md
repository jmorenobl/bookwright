---
description: "Task list for iteration 027 — JSON success-envelope cleanup + G6/G3 deferral decision + unresolved-reference rename"
---

# Tasks: JSON success-envelope cleanup + G6/G3 deferral decision

**Input**: Design documents from `/specs/027-envelope-cleanup-g6-g3/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are INCLUDED because the spec mandates them as deliverables
(FR-005 byte-pinning regression test; FR-011/FR-012 parity-registry assertions and
pin edits) — not as optional TDD scaffolding.

**Organization**: Tasks are grouped by user story (US1, US2, US3) so each closes
independently. US1 and US2 are byte-/behavior-neutral; US3 is the single iteration
that deliberately changes one observable byte (the renamed `graph build` JSON key).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3
- All paths are repo-relative.

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repo root (Constitution III).

---

## Phase 1: Setup

**Purpose**: Confirm a clean working tree on `main`-derived behavior before pinning baselines.

- [X] T001 Run `uv sync` and confirm all four gates are green on the branch tip before any edit (`uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest`), so the byte baselines pinned in US1 reflect known-good current behavior.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None. The three user stories touch disjoint source files and carry no
shared blocking prerequisite. The only cross-story coupling is the `graph build`
golden inside the US1 regression test, whose value depends on the US3 key rename —
handled by an explicit US3 task (T015), not by a foundational phase.

**Checkpoint**: Proceed directly to user stories.

---

## Phase 3: User Story 1 - Success envelopes route through the single source, byte-for-byte (Priority: P1) 🎯 MVP

**Goal**: Every agent-facing success document in `focus` and `graph query` is built
via the shared `ok_payload(**fields)` + `emit_json` helper instead of a hand-rolled
`{"status":"ok",…}` literal, with byte-identical stdout; `check` and `graph build`
are confirmed already single-sourced (no rewrite).

**Independent Test**: `uv run pytest tests/commands/test_success_envelopes.py -v` —
pinned stdout bytes and exit codes for `check`, `focus show/set/clear`, `graph
query`, `graph build` all match their baselines; `grep` finds zero hand-built
`{"status":"ok"}` literals in `commands/focus/` and `commands/graph/query.py`.

### Implementation for User Story 1

- [X] T002 [P] [US1] Migrate `focus show` success to the single source in `src/bookwright/commands/focus/show.py`: replace the hand-built `{"status":"ok","focus":…}` literal with `emit_json(ok_payload(focus=…))` (set case → `focus=focus.model_dump()`; none case → `focus=None`), importing `ok_payload`/`emit_json` from `.._envelope` (mirror `commands/status.py`, research D1/D2). Bytes unchanged.
- [X] T003 [P] [US1] Migrate `focus set` success in `src/bookwright/commands/focus/set_.py`: `{"status":"ok","focus":block.model_dump()}` → `emit_json(ok_payload(focus=block.model_dump()))`. Bytes unchanged.
- [X] T004 [P] [US1] Migrate `focus clear` success in `src/bookwright/commands/focus/clear.py`: `{"status":"ok","cleared":had_focus}` → `emit_json(ok_payload(cleared=had_focus))`. Bytes unchanged.
- [X] T005 [P] [US1] Migrate `graph query` success in `src/bookwright/commands/graph/query.py`: `{"status":"ok","results":rows,"count":len(rows)}` → `emit_json(ok_payload(results=rows, count=len(rows)))` (kwarg order preserves key order, research D2). Bytes unchanged.
- [X] T006 [US1] Confirm-only (no edit) `src/bookwright/commands/check.py`: verify its `{"ok":<bool>,"checks":[…]}` envelope is built as a plain dict and emitted via `emit_json`, and is left exactly as-is (routing it through `ok_payload` would inject a `status` key and change bytes — research D3, FR-003). Record the confirmation in the task notes / PR description.
- [X] T007 [US1] Confirm-only (no edit) `src/bookwright/commands/graph/build.py`: verify success is emitted via `emit_json(report.to_json())` (the report serializer is its single source, not a hand-built literal — research D4, FR-004). No structural change here.

### Test for User Story 1

- [X] T008 [US1] Create `tests/commands/test_success_envelopes.py` (FR-005): invoke `check`, `focus show/set/clear`, `graph query`, and `graph build` in-process via the project's established CLI-invocation pattern (mirror `tests/commands/focus/test_*` and `tests/commands/graph/test_*`), capture **stdout bytes**, and assert each equals a pinned literal baseline; assert `check` carries no top-level `status` key; assert exit codes per contract (`check` 0/1, `focus *` 0, `graph query` 0, `graph build` 0/4) — research D5, contracts/success-envelope.md. The `graph build` golden uses the post-rename `unresolved_references` key (finalized by T015).

**Checkpoint**: US1 closes the success-envelope debt; focus/graph query success is single-sourced and byte-pinned. (`graph build` golden value is settled once US3 lands — T015.)

---

## Phase 4: User Story 2 - Every deferred concept carries a firm reason and target version (Priority: P1)

**Goal**: The two remaining `"undecided"` orphan entries (`RelationshipRole` G6,
`PsychologicalState` G3) become confirmed deferrals to `v0.4` with a concrete
reason; the `"undecided"` literal is eliminated from data and from the
`DeferralNote` contract; neither concept is wired (orphan/reachable sets unchanged).

**Independent Test**: `uv run pytest tests/golem/test_ingestion_parity.py -v` green
(reachable 8 / orphan 5 unchanged, all versions `v0.4`); `grep -rn "undecided"
src/bookwright/golem/deferrals.py` returns nothing.

### Implementation for User Story 2

- [X] T009 [US2] Edit `src/bookwright/golem/deferrals.py` (FR-008/FR-009/FR-011, research D6, contracts/deferral-registry.md): set the `RelationshipRole` and `PsychologicalState` entries from `target_version="undecided"` to `target_version="v0.4"`, each with `reason="requires a typed roles/states model with attributes and an authoring surface"`; remove `"undecided"` from the enumerated `target_version` values in the `DeferralNote` docstring contract (leaving only concrete versions). Do **not** wire either concept; do **not** touch `CLASS_IRI`/`golem.ttl` (FR-013). Leave the three narrative-structure entries (G9/G10/G7 → `v0.4`) unchanged (FR-014).

### Test for User Story 2

- [X] T010 [US2] Edit `tests/golem/test_ingestion_parity.py` (FR-012, research D7): change `RelationshipRole` and `PsychologicalState` in `EXPECTED_VERSIONS` from `"undecided"` to `"v0.4"`; leave `EXPECTED_REACHABLE` (8) and `ORPHAN_NAMES` (5) unchanged; add an assertion in `test_registry_well_formed` that **no** registry entry has `target_version == "undecided"` (FR-011/SC-003), so the literal can never silently return.

**Checkpoint**: US2 closes the deferral-decision debt; the registry contains zero `"undecided"` verdicts and the parity contract is honest end-to-end.

---

## Phase 5: User Story 3 - The unresolved-reference warning is named for what it is (Priority: P2)

**Goal**: Rename `UnresolvedParticipant` → `UnresolvedReference` (type, intermediate
field, `--json` key `unresolved_references`, stderr "unresolved reference(s)") across
`src/` and `docs/`, preserving the `{path, entity, name}` shape, the key's envelope
position, and soft-warning semantics. This is the one deliberate observable-byte
change of the iteration (FR-016/FR-017).

**Independent Test**: `uv run pytest tests/commands/graph/test_build.py -v` green
with `unresolved_references` at its position; `grep -rn
"UnresolvedParticipant\|unresolved_participants" src/ docs/` returns nothing
(FR-019/SC-007); stderr summary reads "N unresolved reference(s)".

### Implementation for User Story 3

- [X] T011 [US3] Rename in `src/bookwright/io/report.py` (FR-015/FR-016, research D8/D9, data-model §3): class `UnresolvedParticipant` → `UnresolvedReference` (fields `{path, entity, name}` intact), generalize its docstring and the module docstring to cover any unresolved name reference (`participants:` member **or** a location `setting:`); rename `BuildReport.unresolved_participants` field → `unresolved_references`; rename the `to_json()` key `"unresolved_participants"` → `"unresolved_references"` **keeping its exact slot** between `"unknown_keys"` and `"sources"`. No other byte of `to_json()` changes.
- [X] T012 [US3] Rename in `src/bookwright/io/_bible_builders.py` (research D8, data-model §3): update the import of the renamed type; rename `BuildResult.unresolved_participants` field → `unresolved_references`; update the 3 `…unresolved_participants.append(UnresolvedParticipant(...))` sites to the new field + type; update the 2 docstrings.
- [X] T013 [P] [US3] Update the module-docstring mention in `src/bookwright/io/bible.py` to the renamed type (research D8).
- [X] T014 [US3] Update `src/bookwright/commands/_graph.py` mapping `unresolved_participants=tuple(result.unresolved_participants)` → `unresolved_references=tuple(result.unresolved_references)` (both sides), and `src/bookwright/commands/graph/build.py`: `report.unresolved_participants` access → `report.unresolved_references`, and the stderr summary `f"{…} unresolved participant reference(s)"` → `f"{len(report.unresolved_references)} unresolved reference(s)"` (FR-018, data-model §3).
- [X] T015 [US3] Finalize the `graph build` golden in `tests/commands/test_success_envelopes.py` (from T008) so the pinned baseline carries the `unresolved_references` key at its position; assert every other byte of the `graph build` document is unchanged vs. the pre-rename order/separators/trailing newline (FR-017, research D9). *(Depends on T008 + T011/T012/T014.)*

### Test + docs for User Story 3

- [X] T016 [US3] Update `tests/commands/graph/test_build.py` to assert the `--json` envelope carries `unresolved_references` (not `unresolved_participants`) at the same position with the `{path, entity, name}` item shape, and replace the relevant golden baseline for that one key only (FR-016/FR-017, contracts/graph-build-json.md).
- [X] T017 [P] [US3] Update remaining test references to the renamed type/field/key in `tests/io/test_bible.py`, `tests/fixtures/test_fixtures.py`, and `tests/resources/conftest.py` + `tests/resources/test_frontmatter_contract.py` so the suite stays green (research D8). (Tests are outside the FR-019 `src/`+`docs/` grep but must pass.)
- [X] T018 [P] [US3] Update `docs/commands/graph-build.md` to name the `unresolved_references` key in its list of soft warnings, noting it now also covers unresolvable `setting:` locations (FR-019, contracts/graph-build-json.md).

**Checkpoint**: US3 closes the 025→027 naming deferral; model, wire, and prose all say "reference".

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Prove the closing patch via the quickstart checks and all four gates.

- [X] T019 Run `grep -rn '"status": *"ok"\|"status":"ok"' src/bookwright/commands/focus src/bookwright/commands/graph/query.py` and confirm **no** matches (SC-002) — the only `{"status":"ok"}` sources are `_envelope.ok_payload` and `BuildReport.to_json()`.
- [X] T020 Run `grep -rn "UnresolvedParticipant\|unresolved_participants" src/ docs/` and confirm **zero** matches (FR-019/SC-007); spot-check `uv run bookwright graph build --json | python -m json.tool | grep unresolved` shows `unresolved_references` only.
- [X] T021 Run the full merge bar (quickstart §1): `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest` — coverage ≥ 80 % overall and > 85 % on the new test module (SC-005); every pre-existing test passes with unchanged expected output (except the US2/US3 pin edits).
- [X] T022 Run the targeted quickstart suites (`tests/commands/test_success_envelopes.py`, `tests/golem/test_ingestion_parity.py`, `tests/commands/graph/test_build.py`) and confirm SC-001/SC-003/SC-004/SC-006/SC-007 hold; record the CHANGELOG obligation for the `unresolved_participants`→`unresolved_references` key rename for the `v0.3.4` release (research D10 — release mechanics handled by the `bookwright-release` skill, out of this iteration's edits).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: empty — no blocking prerequisites.
- **US1 (Phase 3)** and **US2 (Phase 4)**: independent; either can start after Setup.
- **US3 (Phase 5)**: independent of US2; touches `io/report.py`/`graph build` whose
  golden value in the US1 regression test is finalized by T015. Implement US3 after
  T008 exists so T015 can settle the `graph build` baseline.
- **Polish (Phase 6)**: after US1 + US2 + US3.

### Story Dependencies

- US1 (P1): self-contained except the `graph build` golden value (settled by T015 in US3).
- US2 (P1): fully independent (`golem/deferrals.py` + parity test only).
- US3 (P2): fully independent in `src/`; its only test-file coupling is finalizing the
  US1 `graph build` golden (T015) and `test_build.py` (T016).

### Within-story ordering

- US1: T002–T005 (parallel migrations) → T006/T007 (confirm) → T008 (pin test).
- US2: T009 (registry edit) → T010 (parity-test edit).
- US3: T011 (report.py) → T012 (_bible_builders.py) → T014 (_graph.py + build.py) →
  T013/T016/T017/T018 (docstring/tests/docs) → T015 (finalize graph build golden).

### Parallel Opportunities

- **Across stories**: US1 (T002–T005) and US2 (T009–T010) can proceed fully in parallel.
- **Within US1**: T002, T003, T004, T005 are different files → all `[P]`.
- **Within US3**: T013, T017, T018 are `[P]` (distinct doc/test files) once the
  source renames (T011/T012/T014) are in.

---

## Parallel Example: User Story 1 migrations

```bash
# Four independent command-module migrations, different files:
Task: "Migrate focus show in src/bookwright/commands/focus/show.py"        # T002
Task: "Migrate focus set in src/bookwright/commands/focus/set_.py"         # T003
Task: "Migrate focus clear in src/bookwright/commands/focus/clear.py"      # T004
Task: "Migrate graph query in src/bookwright/commands/graph/query.py"      # T005
```

---

## Implementation Strategy

### MVP (US1 + US2 — both P1)

1. Phase 1 Setup (T001).
2. US1 (T002–T008): single-source the success envelopes, pin the bytes.
3. US2 (T009–T010): resolve the G6/G3 deferral, kill `"undecided"`.
4. **Validate**: the two P1 stories alone already close the two debts the iteration
   was scoped around (SC-002, SC-003).

### Incremental delivery

5. US3 (T011–T018): the neutral rename — the one observable-byte change; finalize the
   `graph build` golden (T015).
6. Polish (T019–T022): grep gates + four CI gates + quickstart; note the CHANGELOG
   obligation for `v0.3.4`.

---

## Notes

- `[P]` = different files, no incomplete-task dependency.
- Byte-identity (US1) is by construction: `ok_payload(**fields)` preserves kwarg
  order and `emit_json` uses `separators=(",", ":")` + trailing `\n` (research D1/D2).
- No new ontology class/property, no new dependency, no command added/removed
  (Principle X, Constitution II). Every touched file stays ≤ 500 lines (Principle IV).
- The only deliberately changed observable byte across the whole iteration is the
  `graph build` `unresolved_references` key (US3).
