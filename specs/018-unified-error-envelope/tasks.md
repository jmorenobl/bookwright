---
description: "Task list for Unified Error Envelope (shared BookwrightError base)"
---

# Tasks: Unified Error Envelope (shared `BookwrightError` base)

**Input**: Design documents from `/specs/018-unified-error-envelope/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/error-envelope.md, quickstart.md

**Tests**: Included. They are not optional gold-plating here — FR-013 mandates updating the
flat-shape assertions, research.md mandates a new SC-006 cross-hierarchy test, and the existing
error-shape suite is the regression net that proves the byte-identical guarantee (FR-004/SC-005).

**Organization**: One atomic refactor seen through three story-lenses. Tasks are partitioned by
**file ownership** so the stories stay genuinely independent and parallelizable:
- Foundational owns the new base (`src/bookwright/errors.py`).
- US1 owns the four already-canonical hierarchies (`io`, `indexers`, `validation`, `commands.validate`).
- US2 owns the two legacy flat hierarchies (`core`, `golem`) + their tests + their contract docs.
- US3 owns the cross-hierarchy proof and the regression guardrails.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 (Setup, Foundational, Polish carry no story label)

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repository root.

---

## Phase 1: Setup (Baseline safety net)

**Purpose**: Capture the pre-refactor green baseline so the byte-identical (SC-005) and
unchanged-codes/exit-codes (SC-004) guarantees can be proven, not assumed.

- [ ] T001 Record the pre-refactor baseline on branch `018-unified-error-envelope`: run the error-shape safety net (`uv run pytest tests/core/test_json_shapes.py tests/golem/test_slug.py tests/indexers/test_query_errors.py tests/validation/test_base.py tests/validation/test_command.py tests/io/`) and the four gates (`uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest`), and capture the current `code` strings + the JSON bodies of one representative error per hierarchy (e.g. via `uv run bookwright validate --json` in a non-project dir and in a malformed-manifest dir) as the byte-identical/exit-code reference for T009/T015/T019.

**Checkpoint**: Net is green and the reference bodies are recorded — refactor may begin.

---

## Phase 2: Foundational (Blocking prerequisite for ALL stories)

**Purpose**: Create the single source of truth. No story can migrate onto a base that does not exist.

**⚠️ CRITICAL**: T002–T004 block every task in US1, US2, and US3.

- [ ] T002 Create the shared base in new root module `src/bookwright/errors.py`: `class BookwrightError(Exception)` with the annotation-only class attribute `code: str` — **NOT** `ClassVar[str]` (research Decision 2: `ClassVar` makes the per-instance `self.code` override of `_UsageError` a hard `mypy --strict` error; declare `code: str` so subclasses set it at class scope AND `_UsageError` may set `self.code` per instance), an `__init__(self, message: str, details: dict[str, Any] | None = None)` that sets `self.message`/`self.details` and calls `super().__init__(message)`, and the **one** `to_json(self) -> dict[str, Any]` that builds `{"status":"error","code":self.code,"message":self.message}` in that key order and appends `"details"` **only when `self.details` is truthy**. Module imports stdlib `typing` only and **nothing** from `core/golem/io/indexers/validation/commands` (FR-010). Use the reference implementation in data-model.md verbatim, with a docstring citing Principle IX / review finding R3.
- [ ] T003 [P] Add focused unit tests for the base itself in `tests/test_errors.py`: (a) populated `details` → envelope includes it; (b) empty/`None` `details` → `"details"` key absent (not `null`, not `{}`); (c) key order is exactly `status, code, message[, details]`; (d) a subclass that sets `self.code` in `__init__` overrides the class-level default in the emitted envelope. This gives the new base direct coverage independent of the migrated subclasses.
- [ ] T004 [P] Add an import-isolation guard in `tests/test_errors.py` asserting FR-010/INV-4: importing `bookwright.errors` pulls in none of `bookwright.core`, `bookwright.golem`, `bookwright.io`, `bookwright.indexers`, `bookwright.validation`, `bookwright.commands` (e.g. assert those modules are absent from `sys.modules` after a fresh import, or assert no such name appears in the module's import graph). Proves no new import cycle is structurally possible.

**Checkpoint**: `BookwrightError` exists, is unit-tested, and is provably cycle-free. US1 and US2 can now proceed in parallel.

---

## Phase 3: User Story 1 - Single source of truth across the canonical hierarchies (Priority: P1) 🎯 MVP

**Goal**: Migrate the four hierarchies that already emit the canonical envelope (`io`, `indexers`,
`validation/base`, `commands/validate._UsageError`) onto `BookwrightError`, deleting every per-class
`to_json()`, with **byte-identical** output. This is the safe MVP: the base demonstrably serves
multiple hierarchies through one method with **zero observable change**.

**Independent Test**: Run the four canonical hierarchies' existing error-shape tests **unchanged** —
they pass byte-for-byte; and `grep -rn "def to_json" src/bookwright/{io,indexers,validation,commands}`
shows no error class redefining it (only the out-of-scope `Violation`/`ValidatorError` survive).

**⚠️ The existing canonical tests are the guard — they must keep passing without edits after each migration below.**

- [ ] T005 [P] [US1] Migrate `src/bookwright/io/errors.py`: change `IOError_` base from `Exception` to `BookwrightError` (keep it abstract — no `code`, no `to_json`); for each of `ProjectNotFoundError`, `MissingDirectoryError`, `InvalidFrontmatterError`, `ResearchError`, `SlugCollisionError` **delete** the `to_json()` method and replace the `__init__` tail (`...; self.message = message`) with `super().__init__(message, {<details>})` using the details keys from data-model.md (`start` / `name,path` / `path,reason` / `relpath,value` / `identifier,sources`). Preserve every public attribute (`self.path`, etc.) verbatim so catch sites and tests are untouched.
- [ ] T006 [P] [US1] Migrate `src/bookwright/indexers/errors.py`: change `IndexerError` base to `BookwrightError` (abstract); for `UnknownIndexerError`, `GraphNotBuiltError`, `GraphLoadError`, `InvalidQueryError` delete each `to_json()` and route through `super().__init__(message, {<details>})` with details keys `name,available` / `path` / `path,reason` / `reason`. Preserve public attributes.
- [ ] T007 [P] [US1] Migrate `src/bookwright/validation/base.py`: change `UnknownValidatorError` base to `BookwrightError`, delete its `to_json()`, and pass `super().__init__(self.message, {"names": <names>})`. Leave `Violation` and `ValidatorError` **completely unchanged** — they are finding payloads with their own shape (FR-012), not error envelopes.
- [ ] T008 [P] [US1] Migrate `src/bookwright/commands/validate.py` `_UsageError`: change its base to `BookwrightError`; in `__init__` set `self.code = code` **before** calling `super().__init__(message, details)`, then **delete** the local `to_json()`. Keep it a single class (FR-016) and preserve the `exc.start`/`exc.names` attributes the command handler reads. Do **not** touch the `except ManifestError` / `except UnknownValidatorError` / `except UnknownIndexerError` blocks in this file.
- [ ] T009 [US1] Verify byte-identical output (FR-004/SC-005): run `uv run pytest tests/io/ tests/indexers/test_query_errors.py tests/validation/test_base.py tests/validation/test_command.py` and confirm they pass with **zero edits**, and that the captured T001 reference bodies for these hierarchies match exactly.

**Checkpoint**: Four hierarchies now inherit the single `to_json()`; output unchanged. Shippable MVP (no consumer-visible change).

---

## Phase 4: User Story 2 - Uniform envelope by normalizing the flat hierarchies (Priority: P2)

**Goal**: Migrate the two legacy flat-shape hierarchies (`core/errors.py`, `golem/errors.py`) onto the
base and **normalize** their `{"error": …}` bodies to the canonical `{status, code, message, details}`
envelope (lossless: former `"error"` → `code`, message preserved, remaining fields → `details`), then
update the now-obsolete tests and contract docs.

**Independent Test**: Trigger a manifest error and a golem error under `--json` and assert each emits a
single canonical envelope whose `code` equals the former flat `"error"` value (e.g. `manifest_not_found`,
`golem_empty_slug`), with the former flat fields under `details`.

**⚠️ Files are disjoint from US1 (`core`, `golem`) — this phase can run in parallel with Phase 3.**

- [ ] T010 [P] [US2] Migrate + normalize `src/bookwright/core/errors.py`: change `ManifestError` base to `BookwrightError` (abstract — no `code`); for `ManifestNotFoundError`, `ManifestSyntaxError`, `ManifestValidationError`, `ManifestOverwriteError` **delete** each `to_json()` and call `super().__init__(message, {<details>})` per the Decision 5 map — `manifest_not_found`→`{path}`, `manifest_syntax`→`{field,line,column}` (line/column may be `null`), `manifest_validation`→`{failures}` **with the existing summary string now passed as the top-level `message`** (the one error that gains a top-level message), `manifest_overwrite_refused`→`{path}`. Assign each `code` at class scope using the former `"error"` string verbatim. Leave `ManifestWarning` (the pydantic warning payload) untouched (FR-012).
- [ ] T011 [P] [US2] Migrate + normalize `src/bookwright/golem/errors.py`: change `GolemError` base to `BookwrightError` (abstract); for `EmptySlugError` delete `to_json()`, set `code = "golem_empty_slug"` at class scope, and call `super().__init__(message, {"name": name})`. Preserve `self.name`.
- [ ] T012 [US2] Update `tests/core/test_json_shapes.py`: rewrite the four manifest-error assertions (currently `payload["error"] == …` at the `manifest_validation`/`manifest_syntax`/`manifest_not_found`/`manifest_overwrite_refused` cases) to assert the canonical envelope — `payload["status"] == "error"`, `payload["code"] == <former error name>`, and the former flat fields under `payload["details"][…]`; additionally assert `manifest_validation` now carries a top-level `payload["message"]`. **Do not modify** the `ManifestWarning` test — it stays flat (out of scope).
- [ ] T013 [US2] Update `tests/golem/test_slug.py` (the assertion at line 49): change `to_json()["error"] == "golem_empty_slug"` to `to_json()["code"] == "golem_empty_slug"`, and add `to_json()["status"] == "error"` and `to_json()["details"]["name"] == name`.
- [ ] T014 [P] [US2] Update the contract docs that describe the former flat shapes to the unified envelope (FR-014), each deferring to `specs/018-unified-error-envelope/contracts/error-envelope.md` as authoritative: the error sections of `specs/002-manifest-model/data-model.md` and `specs/002-manifest-model/contracts/manifest_api.md`, and of `specs/005-golem-domain-model/data-model.md` and `specs/005-golem-domain-model/contracts/golem_api.md`. Replace each flat `{"error": …}` example with the canonical `{status, code, message[, details]}` body. (Already-canonical docs stay unchanged.)
- [ ] T015 [US2] Verify normalization end-to-end (User Story 2 independent test / quickstart manual check): in a temp dir, run `uv run bookwright validate --json` against a missing/invalid manifest and confirm stdout is exactly one canonical envelope with `code == "manifest_not_found"` (or the relevant code) and former flat fields under `details`; construct an empty-slug condition and confirm `{"status":"error","code":"golem_empty_slug","details":{"name":…}}`.

**Checkpoint**: The two oldest modules now emit the same envelope as the rest of the CLI; no flat shape remains.

---

## Phase 5: User Story 3 - No regression; single-source-of-truth proven across all six (Priority: P3)

**Goal**: Bound the blast radius. Prove the envelope is now single-sourced across **every** former
hierarchy (SC-006) and that nothing outside the two normalized bodies changed: byte-identical canonical
output, unchanged codes/exit codes, and zero catch-site edits.

**Independent Test**: The SC-006 test (T016) passes; the grep-based single-source/no-flat checks return
the expected results; codes and exit codes match the T001 baseline; every `except <PackageError>` site is byte-unchanged.

**⚠️ Depends on US1 + US2 (it spans all six hierarchies).**

- [ ] T016 [P] [US3] Add the SC-006 cross-hierarchy test in `tests/test_errors.py`: construct one representative error from **each** former hierarchy — `core.ManifestNotFoundError`, `golem.EmptySlugError`, `io.ProjectNotFoundError`, `indexers.GraphNotBuiltError`, `validation.UnknownValidatorError`, `commands.validate._UsageError` — and assert each (a) is an instance of `BookwrightError`, (b) does **not** define `to_json` in its own `__dict__` (the inherited base method is the only one), and (c) serializes to a well-formed canonical envelope. This is the executable proof of SC-002/SC-006.
- [ ] T017 [US3] Verify SC-001/SC-003 by static inspection: `grep -rn "def to_json" src/bookwright` shows `to_json` defined only on `BookwrightError` among error classes (surviving hits are the deliberately out-of-scope `ManifestWarning`, `Violation`, `ValidatorError`, and the `io/report.py`/`validation/report.py` success builders); `grep -rn '"error":' src/bookwright/{core,golem,io,indexers,validation,commands}/*.py` returns nothing in the migrated error modules (no flat shape remains).
- [ ] T018 [US3] Verify SC-008 (zero catch-site edits): confirm `git diff` touches none of the catch blocks `except ManifestError` (`src/bookwright/commands/integration/use.py:56`, `src/bookwright/commands/graph/build.py:51`, `src/bookwright/commands/graph/query.py:46`, `src/bookwright/commands/validate.py:95`), `except UnknownValidatorError` (`src/bookwright/commands/validate.py:104`), and `except UnknownIndexerError` (`src/bookwright/commands/validate.py:122`); the per-package roots remain valid catch targets through the new two-level hierarchy.
- [ ] T019 [US3] Verify SC-004 (codes + exit codes unchanged): diff every error's `code` string and every failing command's exit code against the T001 baseline and confirm zero differences across all six hierarchies.

**Checkpoint**: The refactor is provably complete and bounded — single source of truth, zero residual flat shape, zero regression.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Close the loop on the four gates, the surviving documentation references, and the quickstart.

- [ ] T020 Run all four CI gates green (SC-007): `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict` (must be clean given the deliberate non-`ClassVar` `code: str` + per-instance `self.code` override — see T002), and `uv run pytest` at ≥ 80 % coverage. Confirm coverage did not drop (net code shrinks; the base is exercised by every migrated error plus T003/T016).
- [ ] T021 [P] Update the architecture note in `CLAUDE.md` that currently describes "the project error/warning hierarchy (`errors.py`, every public error has a `.to_json()` contract)" to reflect the single shared base `src/bookwright/errors.py` (`BookwrightError`) as the one owner of the envelope, so the repo guide no longer implies per-package `to_json()`.
- [ ] T022 Run the full `quickstart.md` verification block (the `uv run pytest …` safety net, the four gates, and the three manual sanity checks — single source of truth, no flat shapes, no import cycle) and confirm every check passes as written.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS US1, US2, US3**.
- **US1 (Phase 3)** and **US2 (Phase 4)**: Both depend only on Foundational. Disjoint file sets
  (`io`/`indexers`/`validation`/`commands` vs `core`/`golem`) — **fully parallelizable with each other**.
- **US3 (Phase 5)**: Depends on US1 **and** US2 (it spans all six hierarchies).
- **Polish (Phase 6)**: Depends on US1 + US2 + US3.

### Within Each Story

- US1: T005–T008 are parallel (different files); T009 (byte-identical verification) runs after them.
- US2: T010/T011 parallel; T012/T013 update the matching tests after their migration; T014 (docs) is
  independent and parallel; T015 (end-to-end verify) runs after T010–T013.
- US3: T016 (test) is parallel; T017–T019 are verifications run after the test.

### Parallel Opportunities

- **T003 + T004** (base tests) once T002 lands.
- **All of US1's T005–T008** simultaneously (four different `errors.py` modules).
- **US1 and US2 in parallel** — the central design choice that makes the two stories independent.
- **T010 + T011 + T014** within US2 (two source modules + the doc set, all different files).

---

## Parallel Example: US1 + US2 after Foundational

```bash
# Migrate the four canonical hierarchies (US1) at once:
Task: "T005 Migrate src/bookwright/io/errors.py onto BookwrightError"
Task: "T006 Migrate src/bookwright/indexers/errors.py onto BookwrightError"
Task: "T007 Migrate src/bookwright/validation/base.py UnknownValidatorError"
Task: "T008 Migrate src/bookwright/commands/validate.py _UsageError"

# Simultaneously normalize the two flat hierarchies (US2):
Task: "T010 Migrate + normalize src/bookwright/core/errors.py"
Task: "T011 Migrate + normalize src/bookwright/golem/errors.py"
Task: "T014 Update specs/002 + specs/005 contract docs to the unified envelope"
```

---

## Implementation Strategy

### MVP First (Foundational + US1)

1. Phase 1 Setup → record the green baseline.
2. Phase 2 Foundational → the base exists, unit-tested, cycle-free.
3. Phase 3 US1 → four hierarchies inherit the single `to_json()`, **byte-identical**.
4. **STOP and VALIDATE**: existing canonical tests pass unedited — a complete, zero-observable-change increment. Safe to merge as the MVP.

### Incremental Delivery

1. Foundational → base ready.
2. US1 → single source of truth proven on the safe (no-shape-change) hierarchies → merge-able MVP.
3. US2 → normalize the two flat hierarchies + update their tests/docs → the observable uniformity payoff.
4. US3 → cross-hierarchy SC-006 proof + regression guardrails → bounds the blast radius.
5. Polish → four gates green, docs reconciled, quickstart verified.

---

## Notes

- **No shortcuts by construction**: every measurable success criterion has an explicit task —
  SC-001/SC-003→T017, SC-002/SC-006→T016, SC-004→T019, SC-005→T009, SC-007→T020, SC-008→T018.
  Nothing is left to "it should still work."
- **No per-class `to_json()` survives** on any error class (INV-1); the only surviving `to_json`
  among non-error types are the explicitly out-of-scope payloads (`ManifestWarning`, `Violation`,
  `ValidatorError`, success-report builders) — guarded by T017.
- **Zero catch-site edits** is an invariant, not a hope — T018 diffs the exact six catch blocks.
- The `code: str` (NOT `ClassVar`) decision in T002 is load-bearing for `mypy --strict`; do not
  "tidy" it to `ClassVar` — that breaks `_UsageError`'s per-instance override (research Decision 2).
- Commit after each logical group; stop at any checkpoint to validate the story independently.
