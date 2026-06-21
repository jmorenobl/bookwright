---
description: "Task list for iteration 038 — character_presence ignores markdown heading markers"
---

# Tasks: `character_presence` does not flag the first word of a markdown heading

**Input**: Design documents from `/specs/038-character-presence-heading/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (all present)

**Tests**: REQUESTED — FR-006 and FR-007 mandate two regression tests; they are
included below and written FIRST (TDD).

**Organization**: Two user stories, both P1, both served by one source edit (the
marker-stripping seam in `_unknown_mentions`). That edit is the single foundational
prerequisite; each story then adds its own regression test.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 (heading-opening word exempt) or US2 (in-heading-body name still flagged)
- Exact file paths included in every task.

## Path Conventions

- Single project, src-layout: `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working environment; no scaffolding needed (single-module patch).

- [ ] T001 Sync the dev environment: run `uv sync` from repo root so `.venv` has deps + dev group, then confirm the baseline is green with `uv run pytest tests/validation/test_character_presence.py -q` (the four existing tests must pass before any edit — establishes the FR-003 parity baseline).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The single source change both user stories depend on — strip a leading
ATX heading marker before the proper-noun heuristic runs in
`src/bookwright/validation/validators/character_presence.py`.

**⚠️ CRITICAL**: Both US1 and US2 assert behavior produced by this one edit. It must
land before either story's test can pass (the tests are authored first and will fail
until this is in place).

- [ ] T002 Add the module-level recognizer `_HEADING_MARKER = re.compile(r"^#{1,6}\s+")` to `src/bookwright/validation/validators/character_presence.py` (near `_CANDIDATE`/`_SENTENCE_END`, with a one-line comment: ATX opening marker, anchored at `^`, no leading whitespace — research D2). `re` is already imported.
- [ ] T003 In `_unknown_mentions` (`src/bookwright/validation/validators/character_presence.py`), inside the `for lineno, line in enumerate(text.splitlines(), start=1)` loop, compute `scan = _HEADING_MARKER.sub("", line, count=1)` (the line with any single leading ATX marker removed, else the line unchanged), then change `_CANDIDATE.finditer(line)` → `_CANDIDATE.finditer(scan)` and `_is_sentence_initial(line, match.start())` → `_is_sentence_initial(scan, match.start())`. Leave `lineno` (and thus the `relpath:line` locator) untouched — it comes from `enumerate`, not the match offset (FR-005, research D3). Do not touch `_orphans`/`_is_mentioned`, `_STOP_WORDS`, `_is_sentence_initial`, the dedup, message text, or `warning` severity (FR-004).

**Checkpoint**: The marker-stripping seam is live; a heading's first content word now
lands at offset 0 and is exempted by the existing empty-prefix branch of
`_is_sentence_initial`. Both stories' tests can now go green.

---

## Phase 3: User Story 1 - Heading-opening words produce no spurious warnings (Priority: P1) 🎯 MVP

**Goal**: A manuscript organized under markdown headings (`# Capítulo 1`,
`## Escena …`, multi-depth) with no out-of-roster prose names yields **zero**
`character_presence` findings (SC-001).

**Independent Test**: Build a synthetic in-test project whose manuscript carries
multi-depth headings + plain prose with only roster names; run
`CharacterPresence().validate(...)`; assert `[]` — no `proper noun '…'` warning for any
heading-opening word.

### Tests for User Story 1 ⚠️ (write FIRST, must FAIL before T002/T003 land)

- [ ] T004 [US1] Add `test_heading_first_word_is_not_flagged` to `tests/validation/test_character_presence.py` using the `write_project` / `load_context` / `RdflibIndexer` helpers (mirror the existing tests' shape via the local `_run`). Author a **synthetic in-test** manuscript with headings at multiple depths and roster-only prose, e.g. `characters=["Aparici"]`, `manuscript={"cap-01.md": "# Capítulo 1\n\nAparici llegó al muelle.\n\n## Escena en el faro\n\nAllí esperó.\n\n###### El faro\n\nVolvió.\n"}`. Assert `_run(project_root) == []` (no finding attributable to `Capítulo`, `Escena`, `El`, etc.). Per Clarifications 2026-06-21 the test authors its own heading-bearing manuscript — the `bookwright init` scaffold ships an empty `manuscript/` (FR-006).

**Checkpoint**: US1 is independently verifiable — heading markers no longer flood
spurious proper-noun warnings.

---

## Phase 4: User Story 2 - A real out-of-roster name inside a heading body is still flagged (Priority: P1)

**Goal**: Stripping the marker restores the title to ordinary prose — it does **not**
exempt the whole line. An off-roster name later in a heading body (`Elena` in
`# La caída de Elena`) still fires exactly once (SC-002), proving the marker — not the
title — is removed.

**Independent Test**: Build a manuscript whose heading is `# La caída de Elena` with
`Elena` absent from the roster; run `character_presence`; assert the
`proper noun 'Elena' …` warning fires, citing the heading's `relpath:line`.

### Tests for User Story 2 ⚠️ (write FIRST, must FAIL before T002/T003 land)

- [ ] T005 [P] [US2] Add `test_name_in_heading_body_is_still_flagged` to `tests/validation/test_character_presence.py`: `characters=["Aparici"]`, `manuscript={"cap-01.md": "# La caída de Elena\n\nAparici la recordó.\n"}` (`Elena` not in roster and not in the body). Filter findings to `Severity.warning`; assert exactly one whose `message` contains `Elena` and whose `source` is `manuscript/cap-01.md:1` — `La` opens the title and is exempt, `Elena` is mid-line and fires (FR-002 / FR-007). Additionally assert `findings[…].triples == ()` on the emitted finding to pin the prose-validator-no-graph contract at the test level (FR-009 / Principle X — the frozen ontology is untouched). This test is [P] with T004: same target file but independent, additive functions — author them in one editing pass to avoid a merge conflict.

**Checkpoint**: US2 is independently verifiable — the fix narrows to the marker, leaving
no silent blind spot for title-only names.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Cancel the debt entry and prove the whole change against the gates.

- [ ] T006 [P] Remove the DEBT-008 entry from `DEBT.md` and make the "Deuda abierta" section read `_Ninguna por ahora._` (git retains the history; debt-cancellation convention, FR-008 / SC-005). Confirm with `grep -c "DEBT-008" DEBT.md` → `0`.
- [ ] T007 Run the full quality gates from repo root: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (full suite, ≥ 80 % coverage enforced). All four must pass (SC-004). Confirm `src/bookwright/validation/validators/character_presence.py` stays ≤ 500 lines (Principle IV; ~206 after the edit).
- [ ] T008 Walk the `quickstart.md` scenarios as a final acceptance pass: Scenario 1 (zero findings on headings), Scenario 2 (`Elena` flagged once), Scenario 3 (existing four tests green unchanged — FR-003 parity), Scenario 5 (`DEBT-008` gone). Confirm the existing fixtures were not edited.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — establishes the green baseline.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS both user stories** — the
  single source edit is what makes either story's test pass.
- **User Stories (Phase 3, 4)**: Both depend only on Foundational. Once T002/T003 land,
  both stories pass; their tests are otherwise independent.
- **Polish (Phase 5)**: Depends on both stories' tests existing and the source edit
  landing (gates run the whole suite).

### User Story Dependencies

- **US1 (P1)**: Independent — needs only the Foundational source edit.
- **US2 (P1)**: Independent — needs only the Foundational source edit. No dependency on US1.

### Within Each Story (TDD note)

- The two regression tests (T004, T005) are authored to FAIL against the pre-edit code,
  then pass once T002/T003 land. If you prefer strict red-green, write T004/T005 before
  T002/T003 and watch them fail; either ordering ends in the same green state.

### Parallel Opportunities

- T004 (US1 test) and T005 (US2 test) are additive, independent functions in the same
  file — author them together in one pass ([P] across stories; one file, no logic conflict).
- T006 (DEBT.md edit) is [P] with the test authoring — different file entirely.
- T002 and T003 touch the same function and must be sequential.

---

## Parallel Example

```bash
# After the Foundational edit (T002, T003), the two story tests + the debt edit are
# independent and can be authored in one editing pass:
Task T004: "test_heading_first_word_is_not_flagged in tests/validation/test_character_presence.py"
Task T005: "test_name_in_heading_body_is_still_flagged in tests/validation/test_character_presence.py"
Task T006: "Remove DEBT-008 from DEBT.md"
```

---

## Implementation Strategy

### MVP (User Story 1)

1. Phase 1: Setup — green baseline.
2. Phase 2: Foundational — the `_HEADING_MARKER` + `scan` edit (T002, T003).
3. Phase 3: US1 test (T004) → **STOP and VALIDATE**: headings produce zero findings.
4. This alone closes the user-visible defect (the warning flood).

### Incremental Delivery

1. Setup + Foundational → seam live.
2. US1 (T004) → spurious heading warnings gone (MVP).
3. US2 (T005) → proves no blind spot for title-only names.
4. Polish (T006–T008) → debt cancelled, gates green, quickstart walked.

---

## Notes

- [P] = different files (or independent additive functions), no logic conflict.
- This is a prose-level validator: no graph access, `triples=()` on every `Violation`,
  frozen GOLEM ontology untouched (FR-009 / Principle X).
- The `_HEADING_MARKER` recognizer stays **local** to `character_presence.py` — no shared
  markdown utility (Scope discipline; mirrors iter 037's local `_PENDING_ONLY`).
- Do not edit the four existing tests — their unchanged-pass is the FR-003 parity proof.
- Commit after the logical group (source edit + tests + debt edit) per the iteration's
  patch shape.
