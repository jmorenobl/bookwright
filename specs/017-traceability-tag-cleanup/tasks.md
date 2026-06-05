---
description: "Task list for Traceability Tag Cleanup"
---

# Tasks: Traceability Tag Cleanup

**Input**: Design documents from `/specs/017-traceability-tag-cleanup/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅ (per-line classification),
data-model.md ✅, contracts/no-regression-gate.md ✅, quickstart.md ✅

**Tests**: The only new test is the no-regression gate itself (FR-010, US3) — it
is the iteration's deliverable, not coverage of other code. No other test tasks
are generated (the cleanup is comment-only and behaviour-preserving, SC-003).

**Organization**: Tasks are grouped by user story. Note: US1 (reach zero) and
US2 (preserve durable refs) are delivered by the **same edits** — each edit both
removes a forbidden tag (US1) and applies the correct conversion class from
research.md so durable refs survive (US2). The edits therefore live in the US1
phase; US2's phase is its independent acceptance check that no navigational
information was lost.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 from spec.md
- The single source of truth for *what* each edit does is the **per-line
  classification table in research.md** (`### src/` … `### tests/validation`).
  Each edit task below points at that table; do not re-derive classifications.

## Path Conventions

Single-project Python CLI: `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup

**Purpose**: Establish the baseline and the home for the gate.

- [ ] T001 Confirm the sweep baseline matches research.md before editing: run
  `grep -rnIE '\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+' src/ tests/` from the
  repo root and verify it reports **67 lines across 48 files** (2 under `src/`,
  65 under `tests/`). If the count drifted, reconcile against research.md's
  per-line table before proceeding (any new hit needs a classification).
- [ ] T002 Create the `tests/meta/` package: add `tests/meta/__init__.py`
  (empty, matching the other `tests/*/__init__.py` packages). The gate module
  lands here in Phase 5.

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Lock the safety invariant before any edit, so the cleanup cannot
silently change behaviour.

**⚠️ CRITICAL**: Must pass before Phase 3 edits begin.

- [ ] T003 Re-verify the comment-only precondition (FR-008, Assumptions): for
  every line in research.md's classification table, confirm the forbidden tag
  sits inside a `#` comment or `"""docstring"""` — **not** a test name,
  assertion, or string literal. If any hit is found in a code construct, STOP
  and surface it (edge case in spec.md) rather than editing code to satisfy the
  search.

**Checkpoint**: All 67 hits confirmed comment/docstring-only → editing can begin.

---

## Phase 3: User Story 1 — Zero forbidden tags (Priority: P1) 🎯 MVP

**Goal**: Drive the `T0xx` / `US-x` / `USx` / `+USx` count under `src/` + `tests/`
to zero by applying, file-by-file, the four edit classes (strip-token / relabel
/ remove / neutral-prose) exactly as research.md assigns them.

**Independent Test**: After this phase, the Phase-1 sweep returns zero matches
(SC-001, US1 acceptance scenarios 1–3).

**Note**: Each task below edits a distinct file subtree (no overlap) → all `[P]`.
Apply the action in the `Action` column of research.md per line; freeze every
`Keep` ref byte-for-byte (FR-007).

- [ ] T004 [P] [US1] Edit the two `src/` hits per research.md `### src/`:
  `src/bookwright/core/_research_block.py:1` (strip-token — drop `US2, `, keep
  `FR-011..FR-016`) and `src/bookwright/integrations/base.py:11` (remove — drop
  `(T013)`, prose already carries the why). These are the only `src/` touches.
- [ ] T005 [P] [US1] Edit `tests/commands/` hits per research.md
  `### tests/commands` (9 files / 15 lines): `conftest.py`,
  `graph/test_research_build.py`, `init/test_init_research_scaffold.py`,
  `test_init_default.py`, `test_init_deprecated_flags.py`, `test_init_helpers.py`,
  `test_init_here.py`, `test_init_integrations.py`, `test_init_no_git.py`.
- [ ] T006 [P] [US1] Edit `tests/core/` hits per research.md `### tests/core`
  (11 lines): `fixtures/valid_full.toml`, `fixtures/valid_minimal.toml`,
  `test_build.py`, `test_future_version.py` (lines 1, 43, 54), `test_load_invalid.py`,
  `test_load_valid.py`, `test_research_block.py`, `test_version_gate.py`,
  `test_write.py`. Preserve all `FR`/`SC`/`RB` refs listed in the Keep column.
- [ ] T007 [P] [US1] Edit `tests/e2e/` hits per research.md `### tests/e2e`
  (4 lines): `conftest.py:4`, `test_research_workflow.py` (lines 127, 191, 230).
  Strip the `US2/US3` tokens; keep `FR-008..FR-014`.
- [ ] T008 [P] [US1] Edit `tests/golem/test_provenance_entities.py` per
  research.md `### tests/golem` (lines 70, 122, 170): relabel the three section
  markers to `# --- Source ---` / `# --- Finding ---` / `# --- Anchor ---`.
- [ ] T009 [P] [US1] Edit `tests/integrations/` hits per research.md
  `### tests/integrations` (9 files): `conftest.py:48` (neutral-prose),
  `test_materialize_idempotent.py`, `test_metadata.py`, `test_option_parser.py`,
  `test_plugin_contract.py` (lines 1, 41), `test_registry.py`,
  `test_research_skill.py`, `test_skill_capabilities.py`.
- [ ] T010 [P] [US1] Edit `tests/io/` hits per research.md `### tests/io`
  (5 lines): `test_fs.py:4`, `test_research.py` (lines 86, 146, 209 → relabel to
  `# --- sources.md ---` / `# --- findings ---` / `# --- anchors ---`),
  `test_research_format.py:1`.
- [ ] T011 [P] [US1] Edit `tests/resources/test_command_body.py:7` per
  research.md `### tests/resources`: remove `(US1 + US2) `, keep "covers all 12
  files uniformly".
- [ ] T012 [P] [US1] Edit `tests/validation/` hits per research.md
  `### tests/validation` (15 lines / many files): `conftest.py`, `test_base.py`,
  `test_character_presence.py`, `test_command.py` (lines 1, 149, 268 — also drop
  the "User Story 2/3" prose), `test_factual_anchor.py` (lines 1, 276, 349),
  `test_focalization.py`, `test_queries.py`, `test_registry.py`, `test_report.py`,
  `test_setting_continuity.py`, `test_temporal.py`. Keep all `FR`/`SC`/`D`/`R`
  refs in the Keep column.
- [ ] T012b [P] [US1] Edit the two top-level `tests/` harness hits per
  research.md `### tests/ (top-level harness + fixtures)`:
  `tests/conftest.py:3` (strip-token — drop `T004, `, keep `D1/D2`) and
  `tests/fixtures/test_fixtures.py:1` (strip-token — drop `US1, `, keep
  `SC-001`). Disjoint from T004–T012's subtrees, so also `[P]`.
- [ ] T013 [US1] Run the Phase-1 sweep again across `src/` + `tests/`; confirm
  **zero** matches (SC-001). If any survive, return to the owning edit task.

**Checkpoint**: US1 complete — the codebase contains zero forbidden tags and is
independently verifiable with the single grep.

---

## Phase 4: User Story 2 — Durable traceability preserved (Priority: P2)

**Goal**: Confirm that the Phase-3 edits cancelled the debt without losing
navigational information — every genuinely-traceable hit still reaches its
"why" via a permitted `FR`/`SC`/`D` ref or `bookwright-design.md § N.M`, and no
existing durable number was altered.

**Independent Test**: For a sample of converted files, the comment/docstring now
cites a permitted reference that resolves to the same rationale; no `FR`/`SC`/`D`
number anywhere was renumbered (SC-002, SC-005, US2 acceptance scenarios 1–4).

**Depends on**: Phase 3 (the edits are the US2 work; this phase audits them).

- [ ] T014 [US2] Verify strip-token preservation: for every `S` row in
  research.md, confirm the listed Keep refs survive byte-for-byte and only the
  forbidden token + orphaned punctuation was removed (FR-003, FR-007). Run
  `git diff src/ tests/` and check each `S`-row file's kept refs are untouched.
- [ ] T015 [US2] Verify no durable number was renumbered or reworded anywhere
  in the diff (SC-005): the diff must show forbidden tokens removed and labels
  rewritten only — no `FR-0xx`/`SC-0xx`/`D-x`/`§` token changed value (FR-007).
- [ ] T016 [US2] Verify relabel / remove / neutral-prose rows: each `L`/`R`/`P`
  row's comment now reads as a behaviour-descriptive label or self-describing
  prose with no task/story ID, and where a "why" existed it is retained as
  neutral prose (FR-004, FR-005; US2 acceptance scenarios 3–4).

**Checkpoint**: US1 + US2 both hold — zero tags AND no navigational information
lost.

---

## Phase 5: User Story 3 — Permanent zero via a no-regression gate (Priority: P3)

**Goal**: Add a single pytest gate that re-runs the sweep over `src/` + `tests/`
and fails on any forbidden tag, pinning the debt at zero forever (rides
`uv run pytest` → CI, Principle VIII).

**Independent Test**: With the clean tree the gate passes; inject one tag and the
same suite run turns red, naming `file:line: token` (SC-004, US3 scenarios 1–3).

**Depends on**: Phase 3 (a gate that fails on day one because the tree is still
dirty is not shippable — US3 rationale).

- [ ] T017 [US3] Implement the gate at
  `tests/meta/test_no_traceability_tags.py` per
  contracts/no-regression-gate.md: stdlib `re` + `pathlib` only; compile
  `FORBIDDEN = re.compile(r"\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+")`; resolve
  the repo root from `__file__`; walk text files under `src/` and `tests/`,
  skipping `__pycache__`, binaries (`UnicodeDecodeError`), and the gate's own
  `Path(__file__)`; assert zero matches with a failure message listing
  `relative/path:LINE: TOKEN` one per line plus the CONTRIBUTING.md pointer
  (contract C1–C5, failure-message format).
- [ ] T018 [US3] Run the gate alone and confirm green on the cleaned tree:
  `uv run pytest tests/meta/test_no_traceability_tags.py -q` (contract C1,
  US3-AS1).
- [ ] T019 [US3] Prove the gate bites (contract C2, US3-AS2): inject a probe
  (`echo '# T013 regression probe' >> tests/conftest.py`), confirm the gate
  fails naming the `file:line: token`, then revert
  (`git checkout tests/conftest.py`). Do not commit the probe.
- [ ] T020 [US3] Confirm no false positives (contract C4–C5, FR-011): the gate
  passes with permitted `FR-021`/`SC-009`/`D-2`/`§ 20.5`/"iteration 9" content
  present and does not match its own pattern literal or `T0xx`/`US-x`/`+USx`
  placeholders in docs (research D3 — verify, don't assume).

**Checkpoint**: All three stories functional — clean tree, refs preserved, and a
gate that keeps it that way under CI.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final repo-wide verification that the cleanup changed nothing but
comments/docstrings and that every gate is green.

- [ ] T021 Confirm comment-only edits (FR-008, quickstart §2): run
  `git diff src/ tests/ | grep -E '^[-+]' | grep -vE '^[-+]{3}'` and verify
  every changed line is inside a `#` comment or `"""docstring"""` — no
  `def`/`class`/assert/test-name line appears. The only `src/` touches are
  `core/_research_block.py:1` and `integrations/base.py:11`.
- [ ] T022 Confirm `specs/` untouched (FR-012, SC-005): `git status specs/`
  shows no modified files in this iteration's working tree beyond the spec-kit
  artifacts authored before implementation.
- [ ] T023 Run the full quality gate (SC-003, quickstart §5): `uv run pytest`
  (≥80% coverage, unchanged; same tests pass) then `uv run ruff check`,
  `uv run ruff format --check`, and `uv run mypy --strict`. All green = ready to
  merge.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup; BLOCKS all editing.
- **US1 (Phase 3)**: depends on Foundational. The MVP — delivers the headline
  zero.
- **US2 (Phase 4)**: depends on US1 (it audits US1's edits).
- **US3 (Phase 5)**: depends on US1 (the tree must be clean before the gate can
  ship green). Independent of US2.
- **Polish (Phase 6)**: depends on US1 + US3 (and US2 for full confidence).

### Within User Story 1

- T004–T012b all edit disjoint file subtrees → fully parallel `[P]`.
- T013 (re-sweep) depends on T004–T012b completing.

### Parallel Opportunities

- **T004–T012b** (ten disjoint subtrees) can run in parallel — this is the bulk
  of the work and the main parallelism in the iteration.
- US2 verification (Phase 4) and US3 gate authoring (Phase 5) can proceed in
  parallel once US1 (through T013) is done — they touch different things
  (audit vs. new gate file).

---

## Parallel Example: User Story 1

```bash
# After T003 (comment-only precondition locked), launch the disjoint edits:
Task: "T004 Edit src/ hits per research.md ### src/"
Task: "T005 Edit tests/commands/ hits per research.md ### tests/commands"
Task: "T006 Edit tests/core/ hits per research.md ### tests/core"
Task: "T007 Edit tests/e2e/ hits per research.md ### tests/e2e"
Task: "T008 Edit tests/golem/ hits per research.md ### tests/golem"
Task: "T009 Edit tests/integrations/ hits per research.md ### tests/integrations"
Task: "T010 Edit tests/io/ hits per research.md ### tests/io"
Task: "T011 Edit tests/resources/ hit per research.md ### tests/resources"
Task: "T012 Edit tests/validation/ hits per research.md ### tests/validation"
Task: "T012b Edit tests/ top-level harness + fixtures hits per research.md"
# Then T013 re-sweep once all ten return.
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup (T001–T002).
2. Phase 2: Foundational comment-only guard (T003).
3. Phase 3: US1 edits (T004–T012b, parallel) → re-sweep T013.
4. **STOP and VALIDATE**: the sweep returns zero (SC-001). The debt is cancelled
   — this alone is a shippable increment.

### Incremental Delivery

1. US1 → grep returns zero (MVP).
2. US2 → audit confirms durable refs preserved, no number renumbered.
3. US3 → gate green on clean tree, bites on injection, runs in CI.
4. Polish → comment-only diff + full four-gate run green.

---

## Notes

- `[P]` tasks = different files, no dependencies.
- The per-line classification in **research.md is authoritative** for every
  edit; tasks deliberately do not restate each line to avoid drift.
- Each edit touches only `#` comment or `"""docstring"""` text (FR-008); confirm
  with `git diff` (T021) before merge.
- Existing `FR`/`SC`/`D`/`§` refs are frozen — never renumbered or reworded
  (FR-007, SC-005).
- Nothing under `specs/` is edited or scanned (FR-012).
