---
description: "Task list for iteration 039 — single prose/structure seam"
---

# Tasks: Single prose/structure seam for prose validators

**Input**: Design documents from `/specs/039-prose-structure-seam/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅,
contracts/prose-seam.md ✅, quickstart.md ✅

**Tests**: Test tasks ARE included — the spec explicitly mandates new/extended
tests (`tests/io/test_prose.py`; extended validator tests) and the central
acceptance gate (SC-001) is "the entire existing suite passes with zero oracle
edits". Tests are first-class here, not optional.

**Organization**: Tasks are grouped by user story. The seam and the
`ValidationContext` accessors are genuine foundational blockers (every story
reads them); the validator rewrites land in US1 (their reason to exist is
zero-regression parity), and US2/US3 add verification on top of that rewrite.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete work)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- Exact file paths are given in each task

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure the working environment is ready on the iteration branch.

- [X] T001 Confirm branch `039-prose-structure-seam` is checked out and run `uv sync` to install deps + dev group into `.venv` (no new dependency is added — SC-005 / FR-012; verify `uv.lock` stays unchanged).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared seam and its `ValidationContext` accessors. Every
user story reads these; no validator rewrite can begin until they exist.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [X] T002 Create the seam module `src/bookwright/io/prose.py` (NEW, ~80 lines, modelled on `io/frontmatter.py`'s line-tracking). Define: the frozen dataclass `ProseLine` (`number: int`, `raw: str`, `normalized: str` — NO `kind` field, per FR-002 / data-model.md); the type alias `ProseView = tuple[ProseLine, ...]`; the two private compiled recognizers `_HEADING_MARKER = re.compile(r"^#{1,6}\s+")` (strict col 0) and `_BULLET_MARKER = re.compile(r"^\s*[-*+>]\s+")` (tolerant of leading whitespace) — asymmetry deliberate, do NOT unify (FR-003 / Clarifications); a private `_normalize(line)` helper that strips ONE leading block prefix per pass with `count=1`, heading-first then bullet, looping left-to-right until neither matches (iterative, so `> - text` → `text`; terminates because each strip removes ≥1 char — contract C2); `prose_view(text: str) -> ProseView` returning one `ProseLine` per `text.splitlines()` entry with 1-based `number` from `enumerate(..., start=1)` (C1), `prose_view("") == ()`; and `is_placeholder(body: str) -> bool` compiled from `r"(?i)^\s*\[pending\b[^\]]*\]\s*$"` mirroring `focalization._PENDING_ONLY` (C3 / FR-005). Use stdlib `re` + `dataclasses` ONLY — no Markdown parser/AST (FR-012). Inline emphasis (`**`/`*`/`_`) must never trigger a pass (C2.2).

- [X] T003 [P] Create `tests/io/test_prose.py` (NEW) covering the `contracts/prose-seam.md` behaviour tables exactly: C1 splitting (`prose_view("")==()`, 1-based `number` over multi-line text, `raw` equals the `splitlines()` element); C2 `normalized` table row-by-row (`# Capítulo 1`→`Capítulo 1`, `### Escena`→`Escena`, `####### x` unchanged, `#Capítulo` unchanged, `   # text` unchanged [heading strict col 0], `- Pedro`→`Pedro`, `   - text`→`text`, `> cita`→`cita`, `> - text`→`text` [iterative], `* Pedro`→`Pedro`, `*Pedro*` unchanged, `**Voz narrativa**:` unchanged, empty→empty); C3 `is_placeholder` table (`[PENDING: …]`→True, `  [pending algo]  `→True, text-before/after→False, plain→False, empty→False). Add the new file under the existing `tests/io/` package directory (it already exists with an `__init__.py` — match that package-dir convention).

- [X] T004 Add two cached accessors to `ValidationContext` in `src/bookwright/validation/base.py` (257 → ~285 lines, FR-014). Add two dataclass fields `_manuscript_view` and `_constitution_view`, both `field(default=_UNSET, repr=False, compare=False)`, mirroring the existing six memo fields. Add `manuscript_view() -> tuple[tuple[str, ProseView], ...]` built from the already-cached `manuscript_files()` (NO second disk read — map each `(relpath, text)` through `prose_view`, keep the existing sort), and `constitution_view() -> ProseView` built from `constitution_text()` returning `()` when it is `None` (C5 / FR-006 / D6). Import `prose_view`/`ProseView` from `bookwright.io.prose` (a local import inside the methods, matching the existing `map_bible` / `Character` lazy-import idiom, keeps `validation/ → io/` acyclic). Do NOT touch `manuscript_files()` / `constitution_text()` — the whole-file checks still consume them.

- [X] T004b [P] Extend `tests/validation/test_base.py` (NEW cases, alongside `test_context_accessors_cache_and_read` / `test_constitution_text_none_when_absent`) with direct unit tests for the two new accessors (FR-006 / C5.1–C5.3 / Principle VIII — the accessors are foundational, so they get their own test, not only indirect coverage via the validators): (a) `manuscript_view()` returns sorted `(relpath, ProseView)` parallel to `manuscript_files()` (same relpaths, same order), each `ProseLine.raw` equal to the corresponding `splitlines()` element of that file's text and `normalized` block-prefix-stripped (no second disk read — built from the cached files), and is cache-identical on a second call (`is` the same object, C5.3); (b) `constitution_view()` returns the constitution's `ProseView` and `()` when `constitution_text()` is `None` (C5.2), also cache-identical on a second call. Use the existing `write_project` / `load_context` conftest helpers. Depends on T004 (and T002 for `prose_view`/`ProseLine`). Do NOT edit any existing assertion in `test_base.py` — only ADD cases.

**Checkpoint**: The seam exists, its unit tests pass (`uv run pytest tests/io/test_prose.py`), the accessors are available **and directly unit-tested** (`uv run pytest tests/validation/test_base.py`). User-story work can begin.

---

## Phase 3: User Story 1 - Zero regression across the existing validator suite (Priority: P1) 🎯 MVP

**Goal**: Rewrite the three prose validators on the shared seam and delete their
local strippers, with byte-for-byte parity — every existing test and E2E oracle
passes with ZERO oracle edits (SC-001).

**Independent Test**: Run the full existing suite (`uv run pytest`) with no
oracle edits; it stays green. Spot-check: `# Capítulo 1` does not flag
`Capítulo`; off-roster `Elena` in `# La caída de Elena` still fires;
`- **Voz narrativa**: …` parses identically to the bare form; a solely-`[PENDING: …]`
body is treated as no declaration.

### Implementation for User Story 1

- [X] T005 [P] [US1] Rewrite `character_presence` in `src/bookwright/validation/validators/character_presence.py`: DELETE the module-level `_HEADING_MARKER` constant (and its comment). In `_unknown_mentions`, iterate `project.manuscript_view()` instead of `files` + `text.splitlines()`, reading each `line.normalized` for the proper-noun scan and using `line.number` for the `f"{relpath}:{line.number}"` locator (FR-007 / D7); remove the `scan = _HEADING_MARKER.sub(...)` step (the seam already strips the marker — `_is_sentence_initial` now runs over `line.normalized`). Keep `_orphans` and `_is_mentioned` reading `project.manuscript_files()` (whole-file checks stay over full text — D6/D7). Update `validate()` to pass the view to `_unknown_mentions` and the files tuple to `_orphans`. No `splitlines()` call may remain (SC-002).

- [X] T006 [P] [US1] Rewrite `focalization` in `src/bookwright/validation/validators/focalization.py`: WIDEN `_DECLARATION` to the contract C4 pattern `re.compile(r"(?i)^\s*(?:\*\*|\*|_)*\s*(?:voz narrativa|narrative voice)(?:\*\*|\*|_)*\s*:\s*(?P<body>.+)$")` (`**` before `*` in the alternation so the longest emphasis run is consumed — C4.2); DELETE `_BULLET`, `_LEAD_EMPHASIS`, `_CLOSE_EMPHASIS`, the `_normalize_declaration_line` function, and `_PENDING_ONLY` (FR-008 / SC-002). In `_parse_declaration`, match `_DECLARATION` against each `constitution_view()` line's `.normalized` (not raw `splitlines()` over normalized text) and replace the `_PENDING_ONLY.match(body)` guard with `is_placeholder(body)` imported from `bookwright.io.prose` (FR-008b). In `_first_person_breaks` and `_head_hopping`, iterate `project.manuscript_view()` reading each `line.raw` (dialogue/first-person/head-hopping scans stay over RAW so the dialogue exemption is byte-for-byte unchanged — C6.2 / FR-008c) with `line.number` for locators. Thread `project` (or the view + constitution view) through so `validate()` passes the views; `_parse_declaration` now takes the constitution `ProseView` (or keep it taking text and call `prose_view` — prefer consuming `constitution_view()` so splitting is single-sourced, C6.3). No `splitlines()` call may remain.

- [X] T007 [P] [US1] Rewrite `setting_continuity` in `src/bookwright/validation/validators/setting_continuity.py`: in `_check_setting`, iterate `project.manuscript_view()` reading each `line.raw` instead of `text.splitlines()` (block-prefix stripping is inert for its `\bterm\b` lexicon matching, so `.raw` keeps findings + line numbers identical — FR-009 / D7), using `line.number` for the recorded `(relpath, lineno)`. KEEP the whole-file `name_re.search(text)` gate over the full file text from `manuscript_files()` (FR-009) — so `validate()`/`_check_setting` consults BOTH accessors (the `(relpath, text)` pair for the gate and the matching `(relpath, view)` for the per-line scan; pair them by `relpath`). No constant is deleted; no `splitlines()` call may remain.

- [X] T008 [US1] Extend the three validator test files for seam-parity coverage (depends on T005–T007): in `tests/validation/test_character_presence.py` assert `# Capítulo 1` does NOT flag `Capítulo` and `# La caída de Elena` (off-roster `Elena`) still flags `Elena` (US1 AS2/AS3); in `tests/validation/test_focalization.py` assert `- **Voz narrativa**: tercera persona, limitada` parses identically to the bare `Voz narrativa: tercera persona, limitada` form (US1 AS4) and a body that is solely `[PENDING: …]` yields zero findings (US1 AS5); in `tests/validation/test_setting_continuity.py` assert findings + line numbers are unchanged when manuscript lines carry a leading bullet/blockquote. Do NOT edit any existing assertion or fixture oracle — only ADD cases.

- [X] T009 [US1] Run the FULL existing suite with ZERO oracle edits — `uv run pytest` (D10 parity gate / SC-001). Every current validator test and E2E oracle (`tiny-historical`, `tiny-quest`, etc.) must stay green. If any live fixture's findings move, STOP and inspect the fixture (a pre-existing bullet/blockquote name the heading-only stripper happened to skip) — resolve by examining the fixture, NEVER by loosening the seam (research D10). No oracle file may be modified.

**Checkpoint**: The refactor is behaviour-preserving — the three validators read the seam, all strippers are gone, and the entire suite is green with no oracle edits. This is the MVP.

---

## Phase 4: User Story 2 - A new Markdown surface is handled without touching a validator (Priority: P1)

**Goal**: Prove the seam closes the CLASS — a `> blockquote` off-roster mention
is handled correctly with NO validator-code change.

**Independent Test**: Add a blockquote fixture/case and assert the seam strips
`> ` so the off-roster name is line-initial-exempt, with the validator source
untouched by the fixture.

**Dependency**: Requires US1 (the validators must already read the seam). No US1
validator code changes for this story — that is the whole point (SC-003).

### Implementation for User Story 2

- [X] T010 [US2] In `tests/validation/test_character_presence.py` add a `blockquote` case (selectable with `pytest -k blockquote`, per quickstart §3): a manuscript line `> Quevedo lo dijo` where `Quevedo` is off the bible roster. Assert at the seam level `prose_view("> Quevedo lo dijo")[0].normalized == "Quevedo lo dijo"` AND at the validator level that `Quevedo` is NOT flagged (line-initial after stripping — D9 / FR-011 / SC-003), contrasting with the raw `> Quevedo …` where it would be non-initial → flagged. The fixture/test must require NO change to any validator source.

- [X] T011 [US2] Verify no validator contains blockquote/`>`-specific (or any markup-stripping) code — run the SC-002 grep from quickstart §5 over the three validators: `grep -nE "_HEADING_MARKER|_BULLET|_LEAD_EMPHASIS|_CLOSE_EMPHASIS|_normalize_declaration_line|_PENDING_ONLY|splitlines" src/bookwright/validation/validators/{character_presence,focalization,setting_continuity}.py` → expect NO matches (the seam alone classifies and normalizes — US2 AS2 / SC-002).

**Checkpoint**: The new surface works with zero validator change — the class is demonstrably closed, not patched a fourth time.

---

## Phase 5: User Story 3 - The author's source-line locators are unchanged (Priority: P2)

**Goal**: Reported `relpath:line` locators are identical to today — the line
number is `ProseLine.number`, never a regex match offset.

**Independent Test**: Assert findings emitted over the normalized view carry the
same 1-based line numbers as today.

**Dependency**: Requires US1.

### Implementation for User Story 3

- [X] T012 [US3] Add/confirm a locator assertion (in `tests/validation/test_character_presence.py` and/or `test_focalization.py`): a finding on a line that carries a leading marker (e.g. a heading whose later word is off-roster, or a first-person break on a `- `-prefixed line) reports the line's 1-based source `number`, NOT the offset of the regex match within the stripped text (FR-010 / SC-004 / US3 AS1). Confirm the existing E2E oracle locators are byte-identical (already covered by T009, asserted explicitly here).

**Checkpoint**: All three stories pass independently; locators are provably stable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across the whole change.

- [X] T013 Verify file-size budget (FR-014 / SC-005): `src/bookwright/io/prose.py` ~80 lines, `base.py` ~285, each rewritten validator < 210 — every changed/new file ≤ 500 lines. Confirm `uv.lock` and the dependency set are byte-identical (no new runtime dep).

- [X] T014 Run the four CI gates (quickstart §6 / SC-006): `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥ 80% coverage enforced via `[tool.coverage.report] fail_under=80` — do NOT add `--cov-fail-under`). All green.

- [X] T015 Run `/speckit-analyze` for cross-artifact consistency before merge (per the project's fixed iteration sequence). Confirm prose validators stayed graph-free, LLM-free, `triples=()`, and the frozen 17-class GOLEM ontology is untouched (FR-013 / Principle X).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all user stories. T002 (the seam) must precede T003 (its tests) and T004 (the accessors import it); T004b (accessor unit tests) follows T004.
- **US1 (Phase 3)**: Depends on Foundational (needs `prose_view` + the accessors). T005/T006/T007 are parallelizable (different files); T008 depends on them; T009 depends on all rewrites.
- **US2 (Phase 4)**: Depends on US1 (validators must read the seam). Adds verification only — no US1 source change.
- **US3 (Phase 5)**: Depends on US1. Adds verification only.
- **Polish (Phase 6)**: Depends on US1–US3 complete.

### Within US1

- T005, T006, T007 touch three separate validator files → parallel.
- T008 (extended tests) after the rewrites it asserts against.
- T009 (full-suite parity gate) last — it is the SC-001 gate the whole story rests on.

### Parallel Opportunities

- T003 (seam tests) can be authored in parallel with T004 (accessors) once T002 lands — different files. T004b (accessor unit tests) is `[P]` with T003 once T004 lands (different file — `test_base.py`).
- T005 / T006 / T007 (the three validator rewrites) run fully in parallel.

---

## Parallel Example: User Story 1

```bash
# After Foundational (T002–T004) is complete, launch the three rewrites together:
Task: "Rewrite character_presence on the seam (delete _HEADING_MARKER) in src/bookwright/validation/validators/character_presence.py"
Task: "Rewrite focalization (widen _DECLARATION, delete 4 strippers + _PENDING_ONLY, use is_placeholder) in src/bookwright/validation/validators/focalization.py"
Task: "Rewrite setting_continuity to iterate manuscript_view() reading .raw in src/bookwright/validation/validators/setting_continuity.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup (T001).
2. Phase 2: Foundational — the seam + accessors + seam unit tests (T002–T004). CRITICAL, blocks everything.
3. Phase 3: US1 — rewrite the three validators, delete strippers, prove zero regression (T005–T009).
4. **STOP and VALIDATE**: `uv run pytest` green with zero oracle edits → the refactor is behaviour-preserving. This is shippable.

### Incremental Delivery

1. Setup + Foundational → seam ready.
2. US1 → MVP (behaviour-preserving refactor, all strippers gone).
3. US2 → the class-closure proof (blockquote surface, no validator touched).
4. US3 → locator-stability proof.
5. Polish → file-size, dependency, and four-gate verification.

### Notes

- [P] tasks = different files, no incomplete dependency.
- The whole iteration's premise is a STRUCTURAL refactor, not a behaviour change — never loosen the seam to make a test pass (research D10); a moved finding is a signal to inspect a fixture, not to relax parity.
- Facet B (tri-valued `evaluated` / `not-evaluated(reason)` result) is iteration 040 — explicitly OUT OF SCOPE here.
