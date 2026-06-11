---
description: "Task list for iteration 019 — authored focus state"
---

# Tasks: Authored focus state

**Input**: Design documents from `/specs/019-focus-state/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-focus.md, quickstart.md

**Tests**: INCLUDED — the plan's Technical Context (plan.md:39-41) explicitly
requires unit tests for `FocusBlock` and the `Manifest` round-trip plus
integration tests for the three subcommands, at ≥ 80 % coverage (Constitution
VIII). Test tasks are therefore first-class, written before the implementation
they cover.

**Organization**: Tasks are grouped by user story. The three stories map to the
three subcommands (US1 `set` P1, US2 `show` P2, US3 `clear` P3); each is an
independently testable increment once Setup + Foundational land.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: `[US1]`/`[US2]`/`[US3]` for story tasks; Setup/Foundational/Polish carry no story label
- Every task names the exact file path and the codebase precedent it mirrors

## Path Conventions

Single-project src-layout: source under `src/bookwright/`, tests under `tests/`
at the repository root (plan.md:91-119).

## Precedents this iteration mirrors (read before starting)

| New artifact | Mirror in codebase |
|---|---|
| `core/_focus_block.py` | `src/bookwright/core/_research_block.py` |
| `Manifest.focus` field | `Manifest.research` field — `core/manifest.py:138` |
| `Manifest.set_focus` / `clear_focus` | `Manifest.set_integration` — `core/manifest.py:254` |
| `commands/focus/__init__.py` | `src/bookwright/commands/graph/__init__.py` |
| `emit_json`/`emit_error` (shared) | `src/bookwright/commands/_envelope.py` — promote from `graph/envelope.py`, then `focus`/`graph` both import from `.._envelope` |
| `commands/focus/_project.py` (`load_manifest_or_exit`) | load+fault boundary in `src/bookwright/commands/graph/query.py` (+ `commands/_envelope.invalid_manifest_payload`) |
| `_today()` test seam | `manifest._installed_version()` indirection (research D5) |

> **No `_translate.py` change is needed.** `_translate_validation_error`
> (`core/_translate.py`) is generic: `PydanticCustomError` types (`empty`,
> `not_iso_date`) and the derived `focus.<field>` loc pass through verbatim, so
> focus load-validation errors surface as normal `manifest_validation` failures
> with **no** new wiring (verified, research/data-model §validation).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold the `commands/focus/` package, plus the one shared-envelope
consolidation (T002) so no command file is born duplicating it. No behavioural
dependency on the model; T002 is a no-behaviour-change refactor of shipped `graph`
code guarded by graph's existing tests.

- [ ] T001 Create `src/bookwright/commands/focus/__init__.py` as a **bare** Typer sub-app — `app = typer.Typer(name="focus", help="Record, view, and clear the authored focus state.", no_args_is_help=True, add_completion=False)` — mirroring `commands/graph/__init__.py` but **without** any `from . import …` command-registration lines yet (each story appends its own). (contracts/cli-focus.md:8-10)
- [ ] T002 Single-source the JSON envelope instead of copying it: **move** `emit_json(payload)` and `emit_error(payload, json_output)` verbatim from `src/bookwright/commands/graph/envelope.py` into the existing shared `src/bookwright/commands/_envelope.py` (the module review R1 created to stop per-command envelope hand-rolling; already imported by `graph`/`integration`/`validate`), repoint `commands/graph/build.py` and `commands/graph/query.py` to `from .._envelope import emit_json, emit_error`, and **delete `commands/graph/envelope.py`**. **Also relocate its dedicated test**: move `tests/commands/graph/test_envelope.py` → `tests/commands/test_envelope.py` and repoint its import `from bookwright.commands.graph.envelope import emit_error` → `from bookwright.commands._envelope import emit_error` (the module is gone, so leaving the test in place would break pytest *collection* — ImportError, a red bar under Principle VIII). No `commands/focus/envelope.py` is created — `focus` imports the pair from `.._envelope`. Behaviour is unchanged; the relocated graph envelope test plus `graph`'s build/query tests must stay green. (research D6, Principle IX) *(touches shipped `graph` imports + one test move — not [P] with focus files; run `pytest tests/commands/test_envelope.py tests/commands/graph` right after.)*
- [ ] T003 [P] Create `src/bookwright/commands/focus/errors.py` defining `FocusError(BookwrightError)` (group base, no serializer) and `FocusTargetEmptyError(FocusError)` with `code = "focus_target_empty"` and the message `"--target must be a non-empty string"`; subclass `BookwrightError` from `bookwright.errors` so `to_json()` is inherited (define **no** per-class serializer). (research D6, contracts/cli-focus.md:33,99-104)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The `FocusBlock` model and its attachment to `Manifest` — every
user story reads `manifest.focus`, so nothing else can proceed until this lands.

**⚠️ CRITICAL**: No user-story work can begin until Phase 2 is complete.

- [ ] T004 Create `src/bookwright/core/_focus_block.py` defining `class FocusBlock(BaseModel)` with `model_config = ConfigDict(extra="forbid", strict=True)` and fields `target: str`, `notes: str = ""`, `updated_at: str`; mirror `core/_research_block.py` (module docstring noting Principle IV extraction). Add field validators: (a) `target` `mode="after"` rejecting empty/whitespace-only via `PydanticCustomError("empty", "target must be a non-empty string")`; (b) `updated_at` `mode="after"` requiring `re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)` **and** a successful `datetime.date.fromisoformat(value)`, else `PydanticCustomError("not_iso_date", "updated_at must be an ISO 8601 calendar date YYYY-MM-DD")`. (data-model.md:13-63, research D1/D2; FR-001, FR-008, FR-011, FR-012)
- [ ] T005 [P] Create `tests/core/test_focus_block.py` — unit tests for `FocusBlock`: valid block round-trips; empty/whitespace `target` → `empty`; non-`YYYY-MM-DD` shapes (`2026-W01-1`, `2026-6-1`, `2026/06/01`) and impossible date `2026-13-40` → `not_iso_date`; non-string `target`/`notes` → `string_type`; unknown key → `extra_forbidden`; `notes` defaults to `""` when omitted. (data-model.md:45-53; FR-001, FR-008, FR-011, FR-012) — *write before/with T004, must fail first.*
- [ ] T006 Add `focus: FocusBlock | None = None` to `class Manifest` in `src/bookwright/core/manifest.py` (alongside `research` at line 138) and import `FocusBlock` from `bookwright.core._focus_block`. `None` is the canonical "no `[focus]`" encoding (data-model.md:30-42, research D1; FR-002, FR-005). *(depends on T004)*
- [ ] T007 [P] Re-export `FocusBlock` from `src/bookwright/core/__init__.py` next to the `ResearchBlock` re-export, so `bookwright.core.FocusBlock` is public. *(depends on T004; different file from T006)*
- [ ] T008 [P] Wire the sub-app into the root CLI: add `focus` to the `from bookwright.commands import …` line and `app.add_typer(focus.app, name="focus")` in `src/bookwright/cli.py` (after the `graph` mount at line 18). *(depends on T001; different file from T004-T007)*
- [ ] T009 [P] Create `tests/core/test_manifest_focus.py` with the **load** cases (the mutation cases are added per story): `Manifest.load` of a manifest **without** `[focus]` ⇒ `manifest.focus is None` and all other fields intact (FR-002, SC-004 backward compat); load **with** a valid `[focus]` ⇒ populated `FocusBlock`; load with `[focus].updated_at = "nope"` ⇒ `ManifestValidationError` whose failure names `focus.updated_at` (FR-011, SC-005), asserting no stack trace escapes. (data-model.md:55-58) — *write before/with T006, load-failure cases must fail first.*

**Checkpoint**: Model + manifest attachment ready; the sub-app imports cleanly with zero commands registered. User stories can now begin in priority order.

---

## Phase 3: User Story 1 - Record the current focus (Priority: P1) 🎯 MVP

**Goal**: `bookwright focus set --target <text> [--notes <text>] [--json]` creates
or updates the `[focus]` block, stamps `updated_at = today`, applies the partial-
`notes` rule, rejects an empty `--target`, and preserves all other manifest bytes.

**Independent Test**: In a project with no `[focus]`, run
`focus set --target "cap-04"`; confirm `manifest.toml` gains a `[focus]` block
with `target = "cap-04"`, today's `updated_at`, and every other block/comment/
ordering unchanged (diff the file). Re-run with `--target "arco" --notes "x"` and
confirm update; run `--target "   "` and confirm exit 2 + manifest untouched.

### Tests for User Story 1 (write first, must fail) ⚠️

- [ ] T010 [P] [US1] Add `set_focus` round-trip tests to `tests/core/test_manifest_focus.py`: create-when-absent (block appended, `target`/`notes`/`updated_at` set); update-when-present; and a **comment/ordering preservation** assertion — load a manifest with author comments + a trailing block, call `set_focus`, `dump(overwrite=True)`, reload and assert every non-`[focus]` line is byte-identical (FR-009, SC-002); assert `RuntimeError` when called on a bare (non-document-backed) `Manifest()`. (data-model.md:94-103, research D3)
- [ ] T011 [P] [US1] Create `tests/commands/focus/test_set.py` (CliRunner) covering: create with `--target` only ⇒ `notes=""`; update `--target` only ⇒ existing `notes` preserved; `--notes "X"` ⇒ set; `--notes ""` ⇒ cleared; `updated_at` stamped to a monkeypatched `_today()`; empty/whitespace `--target` ⇒ exit 2, `code="focus_target_empty"` under `--json`, **manifest unchanged** (FR-008); human confirmation goes to **stderr** and stdout stays empty in non-JSON mode; `--json` emits exactly one `{"status":"ok","focus":{…}}` doc on stdout; `project_not_found` / `invalid_manifest` faults. (contracts/cli-focus.md:66-105, quickstart.md:6-58,76-90; FR-006, FR-007, FR-008, FR-013)

### Implementation for User Story 1

- [ ] T012 [US1] Add `Manifest.set_focus(*, target: str, notes: str, updated_at: str) -> None` to `src/bookwright/core/manifest.py`, mirroring `set_integration` (manifest.py:254): require `self._document` else `raise RuntimeError(...)`; create the `[focus]` `tomlkit.table()` (appended last) if absent or update keys in place if present; set `target`/`notes`/`updated_at` on the document and refresh `self.focus = FocusBlock(target=…, notes=…, updated_at=…)`. (data-model.md:94-103, research D3; FR-006, FR-009) *(same file as T006 — sequential)*
- [ ] T013a [US1] Create `src/bookwright/commands/focus/_project.py` with `load_manifest_or_exit(json_output: bool) -> tuple[Path, Manifest]`: call `find_project_root()` (same import source `graph/query.py` uses) + `Manifest.load(...)` wrapped in the shared `--json` fault boundary — `except ManifestError → emit_error(invalid_manifest_payload(exc), json_output)` then `raise typer.Exit(2)`; `except ProjectNotFoundError as exc → emit_error(exc.to_json(), json_output)` then `raise typer.Exit(2)` (the explicit `typer.Exit(2)` matching `graph/query.py`'s `EXIT_CONFIG`). Imports `emit_error`/`invalid_manifest_payload` from `.._envelope` (T002). This is the single load+fault seam reused by all three subcommands (research D10); it does **not** handle `FocusTargetEmptyError` — that stays in `set.py`. *(first consumer is T013b; reused by T016/T021)*
- [ ] T013b [US1] Create `src/bookwright/commands/focus/set.py` — `@app.command("set")` with `target: str = typer.Option(..., "--target")`, `notes: Optional[str] = typer.Option(None, "--notes")`, `json_output: bool = typer.Option(False, "--json")`. Logic: obtain `(path, manifest)` via `load_manifest_or_exit(json_output)` (T013a); reject `target.strip() == ""` by raising `FocusTargetEmptyError` (caught → `emit_error(exc.to_json(), json_output)`, exit 2, manifest never written, FR-008); resolve effective notes per research D4 (`None` ⇒ keep `manifest.focus.notes` or `""` on create; `""` ⇒ clear; `"X"` ⇒ set); add a module-level `_today() -> str` returning `date.today().isoformat()` (research D5); call `set_focus(...)` (passing `target` **verbatim**, not stripped — data-model write-shape decision 2) then `manifest.dump(path, overwrite=True)`; emit `{"status":"ok","focus":{…}}` via `emit_json` under `--json`, else confirmation to a `Console(stderr=True)`. (contracts/cli-focus.md:66-105, research D4/D5/D6/D8)
- [ ] T014 [US1] Append `from . import set as set  # noqa: E402` to `src/bookwright/commands/focus/__init__.py` so `set` self-registers on the sub-app at import. *(depends on T013b; same file appended again in US2/US3)*

**Checkpoint**: US1 is fully functional and independently testable — `focus set` is the MVP write path; the feature can be demoed here.

---

## Phase 4: User Story 2 - View the current focus (Priority: P2)

**Goal**: `bookwright focus show [--json]` displays the current focus legibly
(stdout) or as one JSON document, and reports "no focus defined" gracefully
(exit 0) when the block is absent.

**Independent Test**: In a project with a hand-written `[focus]` block, run
`focus show` (legible target/notes/date on stdout) and `focus show --json`
(`{"status":"ok","focus":{…}}`). In a project without one, run both and confirm
`no focus defined` on stderr (exit 0) and `{"status":"ok","focus":null}`.

### Tests for User Story 2 (write first, must fail) ⚠️

- [ ] T015 [P] [US2] Create `tests/commands/focus/test_show.py` (CliRunner) covering: present block, human ⇒ `target`/`notes`/`updated_at` on **stdout**; present, `--json` ⇒ exactly one `{"status":"ok","focus":{"target":…,"notes":…,"updated_at":…}}` on stdout, nothing else (SC-006); absent, human ⇒ `no focus defined` on **stderr**, exit 0, no error; absent, `--json` ⇒ `{"status":"ok","focus":null}`, exit 0; `project_not_found` / `invalid_manifest` faults exit 2. (contracts/cli-focus.md:37-62; FR-003, FR-004, FR-005, FR-013)

### Implementation for User Story 2

- [ ] T016 [US2] Create `src/bookwright/commands/focus/show.py` — `@app.command("show")` with `json_output: bool = typer.Option(False, "--json")`. Obtain `(path, manifest)` via `load_manifest_or_exit(json_output)` (T013a — handles the `ManifestError`/`ProjectNotFoundError` → exit 2 boundary); if `manifest.focus is None` ⇒ under `--json` `emit_json({"status":"ok","focus":null})`, else print `no focus defined` to `Console(stderr=True)`; if present ⇒ under `--json` `emit_json({"status":"ok","focus":{"target":…,"notes":…,"updated_at":…}})`, else print the three fields legibly to **stdout** (`Console()`); exit 0 in all of these. Import `emit_json` from `.._envelope`. (contracts/cli-focus.md:37-62, research D8/D10; FR-003, FR-004, FR-005) *(depends on T013a)*
- [ ] T017 [US2] Append `from . import show as show  # noqa: E402` to `src/bookwright/commands/focus/__init__.py`. *(depends on T016)*

**Checkpoint**: US1 + US2 both work independently — the author can now record and read the focus (the human + agent read loop is complete).

---

## Phase 5: User Story 3 - Clear the focus (Priority: P3)

**Goal**: `bookwright focus clear [--json]` removes the `[focus]` block,
preserving the rest of the manifest, and is a successful no-op when absent.

**Independent Test**: In a project with a `[focus]` block, run `focus clear`;
confirm the block is gone and the rest of `manifest.toml` is preserved
(`{"status":"ok","cleared":true}`). With no block, confirm a no-op success
(`{"status":"ok","cleared":false}`, exit 0).

### Tests for User Story 3 (write first, must fail) ⚠️

- [ ] T018 [P] [US3] Add `clear_focus` round-trip tests to `tests/core/test_manifest_focus.py`: present ⇒ `[focus]` removed and `self.focus is None`, with a comment/ordering preservation assertion on the remaining manifest (FR-009, SC-002); absent ⇒ no-op, `self.focus` stays `None`, no error; `RuntimeError` on a bare `Manifest()`. (data-model.md:94-103, research D3)
- [ ] T019 [P] [US3] Create `tests/commands/focus/test_clear.py` (CliRunner): present ⇒ block removed, `--json` ⇒ `{"status":"ok","cleared":true}`, human ⇒ `focus cleared` on **stderr**, exit 0; absent ⇒ no-op, `--json` ⇒ `{"status":"ok","cleared":false}`, human ⇒ `no focus to clear` on **stderr**, exit 0; `project_not_found` / `invalid_manifest` faults exit 2. (contracts/cli-focus.md:109-137, quickstart.md:60-74; FR-009, FR-010, FR-013)

### Implementation for User Story 3

- [ ] T020 [US3] Add `Manifest.clear_focus() -> None` to `src/bookwright/core/manifest.py`, mirroring the `set_integration` guard (require `self._document` else `RuntimeError`): if the `[focus]` key is present in the document, `del document["focus"]`; always set `self.focus = None`; no-op (no error) when already absent. (data-model.md:91-103, research D3; FR-010) *(same file as T012 — sequential)*
- [ ] T021 [US3] Create `src/bookwright/commands/focus/clear.py` — `@app.command("clear")` with `json_output: bool = typer.Option(False, "--json")`. Obtain `(path, manifest)` via `load_manifest_or_exit(json_output)` (T013a — handles the project/manifest fault boundary); record `had_focus = manifest.focus is not None`; call `manifest.clear_focus()`; only `dump(path, overwrite=True)` when `had_focus` (avoid a pointless rewrite on the no-op, keeping bytes untouched); emit `{"status":"ok","cleared": had_focus}` under `--json`, else `focus cleared`/`no focus to clear` to `Console(stderr=True)`; exit 0. Import `emit_json` from `.._envelope`. (contracts/cli-focus.md:109-137, research D8/D10; FR-010) *(depends on T013a)*
- [ ] T022 [US3] Append `from . import clear as clear  # noqa: E402` to `src/bookwright/commands/focus/__init__.py`. *(depends on T021)*

**Checkpoint**: All three subcommands are independently functional — the full authored-focus surface is complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, the canonical design-doc edit (FR-014), and the gate sweep.

- [ ] T023 [P] Document the `[focus]` block in `bookwright-design.md § 8.1` (the canonical `manifest.toml` TOML listing), in **Spanish** (language convention): the three fields (`target`, `notes`, `updated_at`), that the block is optional and CLI-stamped, consistent with the worked example already in `§ 21.3`. (research D9; FR-014)
- [ ] T024 [P] Add a one-line entry for the `focus` command group to `docs/` (the mkdocs CLI reference, in Spanish) if a per-command reference page exists; otherwise skip with a note. (docs group, never imported by `src/`)
- [ ] T025 Run the quickstart walkthrough end-to-end (`specs/019-focus-state/quickstart.md`) against a scratch project and confirm every console block matches actual output (set → show → partial-notes update → clear → empty-target error).
- [ ] T026 Run all four gates green: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥ 80 % coverage, single-sourced in `[tool.coverage.report]` — do not add `--cov-fail-under`). Fix any finding before closing the iteration.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)**: no dependencies — start immediately. T001 and T003 are parallel; T002 is an independent `_envelope`/`graph` refactor (disjoint files) but touches shipped code, so run the graph tests after it. T002 must land before any focus command module (T013a/T016/T021), which import `emit_json`/`emit_error` from `.._envelope`.
- **Foundational (Phase 2)**: T004 first; then T006 (needs T004), with T005/T007/T008/T009 parallel by file. **Blocks all user stories.**
- **User Stories (Phase 3-5)**: each depends only on Phase 2. They are independently testable, but two implementation files are shared and therefore serialize:
  - `core/manifest.py` — T012 (US1 `set_focus`) and T020 (US3 `clear_focus`) edit the same file → not parallel.
  - `commands/focus/__init__.py` — T014/T017/T022 each append one import line → not parallel.
  - `commands/focus/_project.py` — created once in US1 (T013a) and consumed by US2 (T016) and US3 (T021); those two command modules therefore depend on T013a as well as Phase 2.
  - `tests/core/test_manifest_focus.py` — T009/T010/T018 append distinct cases → sequence by phase.
  Recommended order is priority order P1 → P2 → P3 (US1 is the MVP).
- **Polish (Phase 6)**: after the stories you intend to ship; T023/T024 parallel; T025 then T026 last.

### Within each story

- Tests (T010/T011, T015, T018/T019) are written **first and must fail** before their implementation (Constitution VIII test discipline).
- Shared load helper before the commands that call it (T013a → T013b/T016/T021).
- Manifest mutation method before the command that calls it (T012 → T013b; T020 → T021).
- Command module before its `__init__` registration line (T013b → T014; T016 → T017; T021 → T022).

### Parallel opportunities

- Phase 1: T001 and T003 in parallel. T002 edits disjoint files (so it does not
  block T001/T003) but it is a refactor of shipped `graph` code plus a test move,
  so treat it as its own serialized step and run the graph/envelope tests right
  after it rather than folding it into the [P] batch.
- Phase 2: T005, T007, T008, T009 once T004 lands (T006 also needs T004).
- Within a story, the two test tasks marked [P] (different files) run together, e.g. T010 ∥ T011, T018 ∥ T019.
- Phase 6: T023 ∥ T024.

---

## Parallel Example: User Story 1

```bash
# Write the two failing test files together (different files):
Task: "set_focus round-trip + preservation tests in tests/core/test_manifest_focus.py"   # T010
Task: "focus set CLI tests (create/update/partial-notes/empty-target/--json) in tests/commands/focus/test_set.py"  # T011

# Then implement in dependency order (same-file/registration → sequential):
#   T012 set_focus → T013a _project.py → T013b set.py → T014 register in __init__.py
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational (CRITICAL — blocks all) → 3. Phase 3 US1.
4. **STOP and VALIDATE**: `focus set` writes/updates `[focus]`, stamps the date,
   rejects an empty target, preserves the manifest. This alone is a shippable slice.

### Incremental delivery

1. Setup + Foundational → model + manifest field ready.
2. US1 (`set`) → record focus → MVP.
3. US2 (`show`) → read it back (human + `--json` contract for future skills).
4. US3 (`clear`) → reset.
5. Polish → design-doc edit (FR-014) + gate sweep.

Each story leaves the build green and adds value without breaking the prior ones.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- This iteration adds **no** graph/SPARQL/skills *behaviour* — derived `status`,
  `next_actions`, and skill consumption are iteration 020-022 (spec Out of Scope).
  The only `graph` touch is T002's envelope consolidation (repoint two imports,
  delete `graph/envelope.py`, move its test): a no-behaviour-change refactor that
  *reduces* duplication, guarded by graph's existing tests.
- `manifest_version` does **not** change — the `[focus]` block is purely additive
  (data-model.md:106-109; FR-002, SC-004).
- Commit after each task or logical group (the `extensions.yml` git hooks offer
  this between phases).
- Verify each test task fails before writing its implementation.
