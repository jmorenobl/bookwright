---
description: "Task list for iteration 041 — leading Spanish dialogue-dash in the prose seam"
---

# Tasks: The prose seam recognizes the leading Spanish dialogue dash

**Input**: Design documents from `specs/041-prose-dialogue-dash/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅,
contracts/dialogue-marker.md ✅, quickstart.md ✅

**Tests**: REQUESTED — FR-009 mandates a both-directions regression test; the spec's
User Stories each carry an explicit Independent Test, and quickstart.md defines runnable
scenarios. Test tasks are therefore included.

**Organization**: Tasks are grouped by user story. Both stories are P1 and are served by
**one** seam edit (Phase 2); the stories diverge only in their *tests* (US1 proves the
leading dash is neutralized; US2 proves nothing else is). The load-bearing constraint
(issue #1 / SC-004): **no validator file is edited** — the entire source change is the
single seam `src/bookwright/io/prose.py`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2; Setup/Foundational/Polish carry no story label
- Exact file paths are given in each task

## Path Conventions

Single project, src-layout (Constitution III): `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working tree and baseline are ready; no scaffolding is needed
(this iteration touches one existing module + tests).

- [X] T001 Sync the environment and confirm a green baseline before any edit: run
      `uv sync`, then `uv run pytest tests/io/test_prose.py tests/validation/test_character_presence.py -q`
      and record that they pass on `041-prose-dialogue-dash` (so any later red is this change's).
- [X] T002 Capture the empirical pre-change parity baseline cited in plan.md/research.md
      (D4): from the repo root run
      `uv run python -c "from bookwright.io.prose import prose_view as p; print([l.normalized for l in p('—Esto es el porvenir')])"`
      and confirm today's seam leaves `—Esto…` glued (word not at offset 0) — the defect
      this iteration removes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The single shared-seam change that BOTH user stories depend on. This is the
only source edit in the iteration.

**⚠️ CRITICAL**: No user-story test can pass until this is complete. Per SC-004 the diff
to every `src/bookwright/validation/validators/*` file is **empty**.

- [X] T003 In `src/bookwright/io/prose.py`, add the module-level recognizer
      `_DIALOGUE_MARKER = re.compile(r"^\s*[—–]\s*")` next to `_HEADING_MARKER` /
      `_BULLET_MARKER`, with a comment noting: em `—` (U+2014) / en `–` (U+2013) only;
      leading whitespace tolerated; trailing `\s*` (NOT `\s+`) because Spanish glues the
      dash to the word (`—Esto`); a leading typographic dash is unambiguous so no
      bullet-vs-emphasis guard is needed (research D1/D3; the ASCII hyphen bullet `- `
      stays owned by `_BULLET_MARKER`).
- [X] T004 In `src/bookwright/io/prose.py`, extend the existing `_normalize` loop with a
      third `elif` branch — order heading → bullet → **dialogue** —
      `elif _DIALOGUE_MARKER.match(line): line = _DIALOGUE_MARKER.sub("", line, count=1)`
      (one pass per marker, `count=1`, so only the LEADING dash is removed and internal
      incise dashes survive — data-model I1/I2, FR-003). Update the `_normalize` and
      module docstrings to name the leading dialogue dash alongside heading/bullet/blockquote.
- [X] T005 Verify the foundational edit against the seam contract by hand (quickstart §1):
      run the one-liner
      `uv run python -c "from bookwright.io.prose import prose_view as p; print(p('—Esto es el porvenir')[0].normalized); print(p('—dijo Arnela—, y se fue')[0].normalized); print(repr(p('—')[0].normalized)); print(p('> —Esto')[0].normalized)"`
      and confirm it prints `Esto es el porvenir` / `dijo Arnela—, y se fue` / `''` /
      `Esto` (FR-001/003, I3). Confirm `wc -l src/bookwright/io/prose.py` stays ≤ 500
      (~87 lines, Constitution IV).

**Checkpoint**: The seam strips the leading dialogue dash and only it; both stories'
tests can now be written and pass.

---

## Phase 3: User Story 1 — Dialogue-heavy prose produces no spurious warnings (Priority: P1) 🎯 MVP

**Goal**: After the seam strips the leading dash, the first spoken word lands at offset 0
and inherits `character_presence`'s existing sentence-initial exemption — so a
dialogue-dominated manuscript yields **zero** findings attributable to a dialogue-opening
word (FR-002, SC-001).

**Independent Test**: Feed the seam `—Esto es el porvenir` (and the en-dash / spaced
variants); assert `normalized` begins at offset 0 with `Esto`; run `character_presence`
on a roster lacking `Esto` and assert no `proper noun 'Esto' …` finding.

### Tests for User Story 1

- [X] T006 [P] [US1] In `tests/io/test_prose.py`, extend the C2 `normalized`-table
      parametrization with the leading-dialogue-dash rows from
      contracts/dialogue-marker.md that prove the **removal**: D1 `—Esto es el porvenir`
      → `Esto es el porvenir`, D2 `— Claro` → `Claro`, D3 `–Esto` (en dash) → `Esto`,
      D4 `  —Esto` → `Esto`, D6 `—` → `` (empty), D7 `> —Esto` → `Esto` (composes with
      blockquote across two passes). Mirror the existing single-row
      `ProseLine(number=1, raw=…, normalized=…)` assertion shape.
- [X] T007 [P] [US1] In `tests/validation/test_character_presence.py`, add a test
      (mirroring `test_heading_first_word_is_not_flagged` /
      `test_blockquote_off_roster_mention_is_not_flagged`) that builds a project whose
      roster lacks `Esto`, with a manuscript line `—Esto es el porvenir`, and asserts
      `character_presence` emits **no** finding mentioning `Esto` (leading dash stripped →
      line-initial → exempt). Per SC-004 this is a validator-LEVEL test; no validator
      source is touched.

### Implementation for User Story 1

- [X] T008 [US1] Correct the one pinned oracle that shifts: in
      `tests/fixtures/tiny-historical/expected-status.md` change
      `validation.counts.warning` `5 → 4` (and the matching prose note
      `{error: 1, warning: 5, info: 0}` → `{… warning: 4 …}`), because the seam now
      removes the spurious `Esto` dialogue-dash flag — exactly as iteration 038 corrected
      `6 → 5` for the spurious `Capítulo`. **Do NOT edit the fixture manuscript** (FR-008,
      SC-003).
- [X] T009 [US1] Confirm the fixture parity end to end: run
      `uv run pytest tests/e2e/test_orchestration_workflow.py tests/fixtures/test_fixtures.py -q`
      and verify green — `tiny-historical` now pins `{error: 1, warning: 4, info: 0}`,
      while `tiny-novel`/`tiny-memoir` (which carry leading-dash dialogue but assert only
      `error == 0`, no pinned warning count) need no edit (research D4, SC-003).

**Checkpoint**: US1 is fully functional and independently testable — dialogue openings no
longer flag, and the live fixture parity is restored downward.

---

## Phase 4: User Story 2 — A real out-of-roster name inside dialogue is still flagged (Priority: P1)

**Goal**: The seam neutralizes **only** the leading marker, never the line content. A
genuine off-roster name later in a dialogue line (`Quirón` in
`—Pregúntale a Quirón —dijo.`) is still flagged, and internal incise dashes
(`—dijo Arnela—`) are left intact (FR-003/FR-004, SC-002).

**Independent Test**: Feed the seam `—Pregúntale a Quirón —dijo.` with `Quirón` absent
from the roster; assert the leading dash is removed but the internal dash and `Quirón`
remain; run `character_presence` and assert the `Quirón` finding fires exactly once while
the opening position produces nothing.

### Tests for User Story 2

- [X] T010 [P] [US2] In `tests/io/test_prose.py`, add the C2 rows from
      contracts/dialogue-marker.md that prove **only the leading** dash is stripped:
      D5 `—dijo Arnela—, y se fue` → `dijo Arnela—, y se fue` (internal incise dash kept,
      FR-003 / I2), D8 `Pregúntale a Quirón —dijo.` → unchanged (no leading dash → mid-line
      dashes are content), and the D9 non-regression anchor `- Pedro` → `Pedro` (ASCII
      hyphen bullet stays owned by `_BULLET_MARKER`, FR-005). Same single-row assertion
      shape as T006.
- [X] T011 [P] [US2] In `tests/validation/test_character_presence.py`, add the
      mid-line-name half of the both-directions test (FR-009): a roster lacking `Quirón`,
      a manuscript line `—Pregúntale a Quirón —dijo.`, asserting the `proper noun 'Quirón'`
      warning fires exactly once (per-distinct-name collapsing) and the opening word is
      NOT flagged — proving only the leading marker was neutralized (SC-002).

**Checkpoint**: Both P1 stories pass — the leading dash is neutralized (US1) and nothing
beyond it is (US2). The both-directions guarantee of FR-009 is covered across T007+T011.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Close the debt trail and prove the full suite + four gates.

- [X] T012 Remove the `DEBT-009` entry from `DEBT.md` (git retains the history), per the
      debt-cancellation convention (FR-011, SC-006). Leave `DEBT-011` (the same-class
      `«`/`"`/`―` leading-quote / horizontal-bar deferral, already recorded by the spec
      audit) in place — it is NOT closed here. Verify: `grep -c "DEBT-009" DEBT.md` → `0`
      and `grep -c "DEBT-011" DEBT.md` → `≥1`.
- [X] T013 Run the full suite and all four gates (quickstart §4, SC-005):
      `uv run pytest` (≥ 80 % coverage), `uv run ruff check`,
      `uv run ruff format --check`, `uv run mypy --strict`. All green.
- [X] T014 Final SC-004 audit: confirm `git diff --stat` shows the only `src/` change is
      `src/bookwright/io/prose.py` (no file under `src/bookwright/validation/validators/`
      appears) — the proof the surface-marker class is closed at the seam, not patched
      per-validator.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup; **BLOCKS both user stories** (the single
  seam edit is the substrate both stories test).
- **User Story 1 (Phase 3)** and **User Story 2 (Phase 4)**: both depend only on Phase 2.
  Once T003–T005 land, US1 and US2 are independent and can proceed in parallel.
- **Polish (Phase 5)**: depends on both stories being complete.

### Within Each User Story

- US1: T006 ‖ T007 (different files, parallel) → T008 (oracle) → T009 (e2e verify).
- US2: T010 ‖ T011 (different files, parallel). No ordering against US1 beyond Phase 2.

### Parallel Opportunities

- T006, T007, T010, T011 all touch **test** files independent of each other and can run in
  parallel once Phase 2 (T003–T005) is done.
- T008 (oracle fixture) is independent of the test files and may run alongside them; T009
  must follow T008 (it asserts the corrected count).

---

## Parallel Example: after Phase 2 completes

```bash
# All four test-authoring tasks touch independent files — run together:
Task: "T006 [US1] C2-D removal rows in tests/io/test_prose.py"
Task: "T007 [US1] leading-dash-not-flagged test in tests/validation/test_character_presence.py"
Task: "T010 [US2] C2-D leading-only rows in tests/io/test_prose.py"
Task: "T011 [US2] mid-line-name-flagged test in tests/validation/test_character_presence.py"
# (T006 and T010 both edit test_prose.py — if authored by one worker, do them in one pass.)
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup (T001–T002) → green baseline captured.
2. Phase 2 Foundational (T003–T005) → the seam strips the leading dialogue dash.
3. Phase 3 US1 (T006–T009) → dialogue openings no longer flag; fixture parity restored.
4. **STOP and VALIDATE**: `uv run pytest tests/io/test_prose.py tests/validation/test_character_presence.py tests/e2e/test_orchestration_workflow.py -q` green.

This is already a shippable patch (the defect, DEBT-009, is closed).

### Incremental Delivery

1. Setup + Foundational → seam ready.
2. + US1 → spurious dialogue-dash warnings gone (MVP, closes the dogfood finding).
3. + US2 → over-correction guard proven (internal dashes intact, mid-line names flagged).
4. + Polish → DEBT-009 removed, four gates green.

---

## Notes

- [P] = different files, no incomplete-task dependency. T006 and T010 share
  `tests/io/test_prose.py`; treat as sequential if one worker authors both.
- The entire source delta is `src/bookwright/io/prose.py` (~6 lines): one recognizer +
  one `elif` branch + docstring. No validator, no graph, no ontology, no new dependency
  (FR-006/FR-012, Constitution II/X).
- Commit after each phase (the auto-git hooks offer between phases); keep commit messages
  in English.
- Verify the new tests fail before T003–T004 land (the seam edit is what makes them pass).
