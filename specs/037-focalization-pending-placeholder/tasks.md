---
description: "Task list for iteration 037 — focalization [PENDING] voice-placeholder suppression"
---

# Tasks: `focalization` treats an unanswered `[PENDING]` voice placeholder as no declaration

**Input**: Design documents from `/specs/037-focalization-pending-placeholder/`

**Prerequisites**: plan.md (✅), spec.md (✅), research.md (✅), data-model.md (✅),
contracts/parse-declaration.md (✅), quickstart.md (✅)

**Tests**: REQUIRED for this feature — FR-002 (the recognition boundary: suppress
a solely-`[PENDING]` body, never a body that merely *contains* the token alongside
real text), FR-007, and FR-008 explicitly mandate tests; they are part of
acceptance, not optional.

**Organization**: Two P1 user stories. Both depend on a single foundational
production change (the `_PENDING_ONLY` guard). US1 proves the validator goes
silent on the unanswered scaffold; US2 proves it wakes on a real declaration.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 (Setup, Foundational, Polish carry no story label)
- All paths are repository-root-relative.

## Path Conventions

Single project, src-layout (Constitution III). Production code in `src/bookwright/`,
tests in `tests/`. The entire production change is confined to **one file**:
`src/bookwright/validation/validators/focalization.py`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm a green baseline before touching the validator.

- [ ] T001 Sync the environment (`uv sync`) and capture the baseline: run
  `uv run pytest tests/validation/test_focalization.py -q` and confirm it is green
  with the **current** `test_template_binding` (asserting the scaffold line parses
  `is not None`). This baseline is what T009 deliberately flips.
- [ ] T002 Re-read `src/bookwright/resources/commands/references/pending-protocol.md`
  (the prose source of truth the local recognizer must mirror) and the live scaffold
  body in `src/bookwright/resources/project/bible/constitution.md.j2` to confirm the
  `[PENDING: ¿Quién narra y desde qué distancia (primera/tercera persona,
  omnisciente/limitada)?]` text is intact (it is the input the FR-007 test pins).

**Checkpoint**: Baseline green, placeholder text confirmed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The single production change both user stories rely on. Nothing in
Phase 3/4 can pass until this is complete.

**⚠️ CRITICAL**: This is the only production-code change in the iteration.

- [ ] T003 Add the module-level recognizer constant to
  `src/bookwright/validation/validators/focalization.py` (near the existing
  `_DECLARATION` / `_LABEL` compiled patterns, ~line 26):
  `_PENDING_ONLY = re.compile(r"(?i)^\s*\[pending\b[^\]]*\]\s*$")` — full `^…$`
  anchor = "body is *solely* an unanswered token" (FR-002, contract C1–C3); the
  `\b` after `pending` keeps it a keyword; `(?i)` makes `PENDING` case-insensitive.
- [ ] T004 Add the single guard inside `_parse_declaration` in
  `src/bookwright/validation/validators/focalization.py`, immediately after
  `body = match.group("body")` (~line 164):
  `if _PENDING_ONLY.match(body): return None` — routes a solely-placeholder body
  into the existing "no declaration → zero findings" path. The guard runs on the
  already markdown-normalized body (iteration 034), so the bullet/emphasis scaffold
  form is covered (FR-005). No other rule (first-person, interiority, focal
  resolution, markdown normalization) is touched (FR-006). File MUST stay ≤ 500
  lines (Constitution IV — 183 today, ~+3).

**Checkpoint**: `_parse_declaration` now returns `None` for a solely-`[PENDING]`
body. Both user stories can now be verified.

---

## Phase 3: User Story 1 - Fresh project produces no spurious focalization warnings (Priority: P1) 🎯 MVP

**Goal**: A project from the unmodified scaffold, with a manuscript containing an
interiority verb on a named character, yields **0** `focalization` findings.

**Independent Test**: Build a project whose constitution carries the exact live
scaffold voice line + a manuscript scene `Halia pensó que el faro callaba.`; run
`focalization`; assert zero findings (contract V1, SC-001).

### Tests for User Story 1

- [ ] T005 [US1] Add `test_live_scaffold_constitution_yields_nothing` to
  `tests/validation/test_focalization.py` (FR-007 / SC-001 / contract C2,V1): read
  the EXACT scaffold body via `importlib.resources` from
  `bookwright.resources.project.bible/constitution.md.j2` (placeholder intact — its
  body really contains "tercera persona"/"limitada", unlike the existing simplified
  `test_pending_markdown_declaration_yields_nothing` which does NOT reproduce the
  bug), write it as the project constitution plus a manuscript scene with an
  interiority verb on a named character (`Halia pensó que el faro callaba.`), run
  the validator, and assert `== []`. This test FAILS before T003/T004.
- [ ] T006 [P] [US1] Add `test_live_scaffold_first_person_yields_nothing` to
  `tests/validation/test_focalization.py` (acceptance scenario 2): same untouched
  scaffold constitution + a first-person manuscript line outside dialogue (`Yo no
  entendía nada.`); assert `== []` (no person declared ⇒ neither first-person nor
  head-hopping rule may fire).
- [ ] T007 [US1] Add `test_pending_recognition_boundary` (a parametrized
  `_parse_declaration` unit test) to `tests/validation/test_focalization.py`
  (FR-002 / FR-004 / contract C3,C4,C5): assert the **recognition boundary** the
  `_PENDING_ONLY` regex draws — the over-match guard US2 depends on. Cover, with no
  project fixture (pure `_parse_declaration(text, _NAMES)` calls):
  (C3, suppress) `Voz narrativa:   [pending: ¿x?]  ` → `is None` (surrounding
  whitespace + lowercase keyword tolerated);
  (C4, do NOT suppress) `Voz narrativa: Tercera persona [PENDING: ¿focal?]` → real
  declaration, `person == "third"` (real text BEFORE a leftover token);
  (C5, do NOT suppress) `Voz narrativa: [PENDING: …] tercera persona` → real
  declaration, `person == "third"` (real text AFTER the token — body not *solely*
  the token);
  (FR-004, suppress on EN label) `Narrative voice: [PENDING: who narrates?]` →
  `is None` (suppression is label-agnostic). C3/EN FAIL before T003/T004; C4/C5 must
  stay green (the guard must not over-match a partially-authored body).

### Implementation for User Story 1

- [ ] T008 [US1] Run `uv run pytest tests/validation/test_focalization.py -q` and
  confirm T005/T006/T007 now PASS on top of the T003/T004 guard. No new production
  code — the foundational change already delivers US1; this task confirms the
  increment.

**Checkpoint**: US1 is independently verifiable — the MVP (the entire defect fix) is
done.

---

## Phase 4: User Story 2 - Answering the voice prompt wakes the validator (Priority: P1)

**Goal**: Replacing the `[PENDING: …]` body with a real voice restores today's
behavior exactly — the validator parses person/limited/focal and resumes flagging
head-hopping; no regression on existing fixtures.

**Independent Test**: Take the same project, replace only the placeholder body with
a real third-person-limited voice focalized on a character, keep a head-hopping
manuscript, run `focalization`, assert the head-hopping finding fires (contract V2,
SC-002).

### Tests for User Story 2

- [ ] T009 [US2] Add `test_replacing_placeholder_with_real_voice_wakes_validator` to
  `tests/validation/test_focalization.py` (FR-008 / SC-002 / contract V2): start
  from the scaffold but replace ONLY the placeholder body with `Tercera persona
  limitada, focalizada en Halia`, keep a manuscript where a *non-focal* character
  gets an interiority verb, run the validator, and assert the head-hopping finding
  fires (and `Violation.triples == ()`, contract V4 / FR-010).
- [ ] T010 [US2] FLIP the existing `test_template_binding` in
  `tests/validation/test_focalization.py` from `assert _parse_declaration(...) is
  not None` to `is None` and update its comment: the live placeholder line now
  parses to `None` BY DESIGN (the anti-drift guarantee is preserved — it still binds
  the live template body to the parser, now asserting the correct suppressed result).
  Leaving it red would fail the gate.

### Implementation for User Story 2

- [ ] T011 [US2] Run `uv run pytest tests/validation/test_focalization.py -q` and
  confirm the full file is green: T009 wakes, T010 flipped, and every pre-existing
  fixture (bare / English / markdown-prefixed iteration-034 forms) is byte-identical
  (FR-003 / contract V3 / SC-002 — no finding added or removed).

**Checkpoint**: Both P1 stories pass; the validator suppresses only the unanswered
placeholder and wakes on any real declaration.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Close the debt and prove the whole change against all gates.

- [ ] T012 Remove the DEBT-007 entry from `DEBT.md` (FR-009 / SC-004): delete the
  `### DEBT-007 …` block (~lines 46+) under "## Deuda abierta". Confirm
  `_Ninguna por ahora._` remains as the section's only content (git keeps history;
  `grep -c "DEBT-007" DEBT.md` MUST print `0`).
- [ ] T013 Run the full quickstart validation (`specs/037-focalization-pending-placeholder/quickstart.md`):
  the two unit `python -c` one-liners (scaffold→`None`, real-voice→declaration), the
  focalization test run, and `grep -c "DEBT-007" DEBT.md`.
- [ ] T014 Run all four gates (SC-003):
  `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest`
  — all green, coverage ≥ 80 %. Confirm `focalization.py` ≤ 500 lines.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS both user stories** (the
  T003/T004 guard is the only production change; every test phase asserts against it).
- **User Story 1 (Phase 3)**: Depends on Foundational. The MVP — the complete defect fix.
- **User Story 2 (Phase 4)**: Depends on Foundational. Independent of US1 (different
  assertions, same file) but conventionally follows it; both share
  `tests/validation/test_focalization.py`, so their edits serialize on that file.
- **Polish (Phase 5)**: Depends on US1 + US2 complete.

### Within / Across User Stories

- T005, T006 and T007 touch the same test file as T009/T010 → only T006 is marked
  `[P]` (it is logically independent of T005); all other test-edit tasks serialize
  on `tests/validation/test_focalization.py` and must be applied sequentially.
- Tests T005/T006/T007(C3,EN)/T009 are written to FAIL before the guard, then pass
  after; T007's C4/C5 cases must stay green throughout (the guard must NOT over-match
  a partially-authored body); T010 flips a passing assertion that the guard makes
  false.

### Parallel Opportunities

This is a one-file production change, so parallelism is minimal by design:

- T005 ‖ T006 may be authored together conceptually, but both edit the one test
  file — apply sequentially to avoid a same-file conflict (only T006 carries `[P]`).
- The four gates in T014 each run independently but are bundled as one `&&` chain.

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 (Setup) → confirm green baseline.
2. Phase 2 (Foundational) → add `_PENDING_ONLY` + the guard (T003, T004).
3. Phase 3 (US1) → scaffold-zero-findings + recognition-boundary tests pass (T005–T008).
4. **STOP and VALIDATE**: the entire defect (the head-hopping flood on a fresh
   project) is gone. This is shippable.

### Incremental Delivery

1. Setup + Foundational → the cause is suppressed.
2. + US1 → fresh scaffold is silent (MVP, the whole defect).
3. + US2 → confirmed no over-correction; a real declaration still wakes the
   validator and existing fixtures are byte-identical.
4. + Polish → DEBT-007 removed, all four gates green; ships as `v0.4.5`.

---

## Notes

- The recognizer stays **local** to `focalization.py` — no shared `[PENDING]`
  utility (clarification: that would be speculative plumbing for validators this
  iteration does not touch). `references/pending-protocol.md` stays the prose source
  of truth it mirrors.
- The constitution template (`constitution.md.j2`) is **NOT** reworded — the
  parser-level suppression keeps the author prompt useful (clarification).
- Prose validator: no graph, `Violation.triples == ()`, frozen ontology untouched
  (Constitution X / FR-010).
- `[P]` = different files, no dependencies; nearly all task edits here land in one
  production file + one test file, so most serialize.
- Commit after each logical group (the auto-git hook offers between phases).
