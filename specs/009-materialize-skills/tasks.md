---
description: "Task list for iteration 9 — Materialize commands as Agent Skills"
---

# Tasks: Materialize commands as Agent Skills

**Input**: Design documents from `/specs/009-materialize-skills/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/generate_skill_md.md, contracts/lint_skill_md.md, quickstart.md

**Tests**: INCLUDED. The spec defines per-story Independent Tests, the plan enumerates the
test files, and Constitution VIII mandates ≥80% coverage — so test tasks are first-class here.

**Organization**: Tasks are grouped by user story (P1 → P2 → P3) so each story is an
independently testable increment. The heavy lifting is one shared helper
(`generate_skill_md`) plus a pure linter (`lint_skill_md`); US2 (idempotency) and US3
(capability-aware) are thin, additive deltas on top of the US1 core.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 (omitted for Setup, Foundational, Polish)
- Exact file paths are given in every task.

## Path Conventions

Single-project src-layout (Constitution III): production code under
`src/bookwright/…`, tests under `tests/…` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: shared constant + error types + the extracted transactional-fs layer that
both the linter and the materializer depend on. Project itself is already initialized
(iterations 1–8 are on `main`).

- [X] T001 [P] In `src/bookwright/integrations/constants.py`: add `SKILL_BODY_MAX_TOKENS: Final[int] = 5000` (Tier-2 body budget, R6/FR-015); add `DEFAULT_SKILL_LICENSE: Final[str] = "Apache-2.0"` (the design default inherited when a source declares no `license`, FR-005/A-002 — single source of truth); add `INJECTION_READ_COMMANDS: Final[frozenset[str]] = frozenset({"cat", "head", "tail"})` (the deny-by-default allowlist of project-file read commands for the FR-013 injection invariant — file-read only, `ls`/`find` deliberately excluded); and mark `SKILL_PLACEHOLDER_MARKER_NAME` as deprecated in its docstring/comment (no longer written after T007).
- [X] T002 [P] Add `SkillLintError` and `SkillMaterializationError` to `src/bookwright/integrations/errors.py`, both inheriting `_IntegrationError` (reuse `to_dict()`): `SkillLintError(code="skill_lint_failed", *, skill, rule, detail)` with `rule ∈ {name_mismatch, description_too_long, body_over_budget, invalid_frontmatter, forbidden_injection}`; `SkillMaterializationError(code="skill_materialization_failed", *, skill, rule, detail)` with `rule ∈ {dangling_reference, name_frontmatter_mismatch}` — the latter for a source whose frontmatter `name` ≠ filename stem (data-model § 6, FR-016/FR-020).
- [X] T021 [P] **Extract the transactional-fs layer** to a new `src/bookwright/io/fs.py`: move `BackupLedger`, `BackupEntry`, `mkdir_tracked`, `write_bytes_atomic` (and their private helpers like `_register_target`) out of `src/bookwright/commands/init/scaffold.py`; add a `FileLedger` `typing.Protocol` (`record_new_file`, `record_new_directory`, `record_overwrite` — structurally satisfied by `BackupLedger`) and a no-op `NullLedger`. `scaffold.py` imports them from `io.fs` and keeps the command-specific surface (resource-tree render, `dump_manifest_tracked`, the apply orchestration). `io.fs` imports only stdlib + `bookwright.io.errors` — no `commands`/`integrations` import (acyclic). Update the existing importers: `tests/commands/test_init_helpers.py` (move the `BackupLedger`/`mkdir_tracked`/`write_bytes_atomic` unit tests into a new `tests/io/test_fs.py`, repoint imports to `bookwright.io.fs`) and `tests/resources/test_skeleton_renders.py` (repoint its `BackupLedger` import). Add a `NullLedger` no-op test in `tests/io/test_fs.py` (FR-019, plan "Transactional integrity"). **Blocks T009/T010/T011** (the materializer and shared `setup()` import from `io.fs`). Behaviour is unchanged — this is a move + protocol addition, gated by `mypy --strict` + the relocated tests.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the authoritative description data table — a pure, dependency-free module that
the materializer reads. Blocks US1.

**⚠️ CRITICAL**: US1 materialization cannot run until `descriptions.py` exists.

- [X] T003 Create `src/bookwright/integrations/descriptions.py` with `SKILL_DESCRIPTIONS: dict[str, str]` (one entry per command in the 10-command roster, seeded from each iteration-8 source `*.md` frontmatter `description`, bilingual ES/EN triggers preserved) and `get_description(name: str, fallback: str) -> str` returning `SKILL_DESCRIPTIONS.get(name, fallback)` and asserting the result `< SKILL_DESCRIPTION_MAX_LENGTH` in this **one** place (R1/R3, FR-004).
- [X] T004 [P] Add `tests/integrations/test_descriptions.py`: assert every `SKILL_DESCRIPTIONS` value `< 1024` chars, that all 10 roster keys are present, and that `get_description` returns the dict value when keyed and the `fallback` for a missing key (FR-004, SC-002). **Add the v0 equality gate** (SC-009): for each roster command, assert `SKILL_DESCRIPTIONS[name] == parse_frontmatter(source).metadata["description"]` — the dict mirrors the source verbatim in v0; accidental drift fails CI, while a deliberate divergence is an explicit, reviewed edit to this expectation.

**Checkpoint**: description source-of-truth ready — materializer can be built.

---

## Phase 3: User Story 1 - Author gets working skills after `init` (Priority: P1) 🎯 MVP

**Goal**: every source command becomes a ready-to-invoke `<skills_dir>/<command>/SKILL.md`
with valid frontmatter (`name`==dir, authoritative `description`, `license`, `metadata`), a body
with `{ARGS}`→`$ARGUMENTS`, inline `bookwright … --json` calls intact, and cited
`references/` copied alongside — all gated by the agentskills.io linter (abort on failure).

**Independent Test**: run `init` (or call `setup()`) into an empty `tmp_path` with the Claude
integration; assert one `<skills_dir>/<command>/SKILL.md` per source command, each with
`name` == parent dir and a body containing `$ARGUMENTS` (no `{ARGS}`/`{SCRIPT}`), and that
every generated `SKILL.md` lints clean.

### Tests for User Story 1 ⚠️ (write first, expect FAIL before T005–T008)

- [X] T005 [P] [US1] Add `tests/integrations/test_skill_lint.py`: each of the 10 sources, once materialized, lints clean; crafted samples each raise the matching `rule` for `name_mismatch` (name≠dir), `description_too_long` (1024+ chars), `body_over_budget` (5000+ token body), and `invalid_frontmatter` (malformed YAML fence / empty metadata) (FR-015, SC-002). (Rule 5 `forbidden_injection` is added in US3/T015.)
- [X] T006 [P] [US1] Add `tests/integrations/test_materialize.py`: `generate_skill_md` over each source produces a `SKILL.md` whose frontmatter has `name`==dir, `description` from `SKILL_DESCRIPTIONS`, `license: Apache-2.0`, `metadata.author: bookwright`, `metadata.version == bookwright.__version__`; the materialized body equals `source_body.replace("{ARGS}", "$ARGUMENTS")` **exactly** — a single strong assertion proving the sole transform is the token substitution, that inline `bookwright … --json` calls survive verbatim (FR-008/009), and that all instructional content is preserved (FR-018); as a corollary the body contains `$ARGUMENTS` and **zero** `{ARGS}`/`{SCRIPT}` tokens (FR-007, SC-003); cited `references/<file>.md` are copied into the skill's own `references/` (SC-004); a body citing a missing reference raises `SkillMaterializationError(rule="dangling_reference")`; **a source whose frontmatter `name` ≠ filename stem raises `SkillMaterializationError(rule="name_frontmatter_mismatch")` (FR-020)**; **both authoring errors are pre-write — assert the offending `<command>/` directory does not exist on disk after the raise (zero partial state, even with a `NullLedger`)**; `iter_command_sources()` yields exactly the 10-command roster and skips the `references/` subdir; an empty roster writes no skill dirs (edge case); no write escapes `target_dir` (FR-017, SC-007); **passing a recording `FileLedger` fake (or a real `BackupLedger`), every created `<command>/`, `references/`, `SKILL.md` and reference file is recorded (FR-019)**; **a `--json` regression guard: the known agent-facing call `bookwright graph build --json` is present verbatim in the materialized bodies that carry it (FR-009)**.
- [X] T007 [P] [US1] Rewrite `tests/integrations/test_setup_stub.py` → `tests/integrations/test_setup_materialize.py`: the shared `setup()` materializes one `SKILL.md` per command under the resolved `skills_dir`, writes **no** `.bookwright-skills-placeholder`, keeps iteration-3 containment guards (`resolves_to_project_root` / `escapes_project_root` still raise `MalformedOptionError`), and is callable for both `claude` and `generic` (FR-001, FR-017). **Ledger contract**: `setup()` defaults to a `NullLedger` when `ledger` is omitted (standalone-callable); when given a real `BackupLedger`, every materialized path is recorded. **Orphan rollback (SC-008, FR-019)**: with a **pre-existing** `skills_dir`, force a lint failure on one command (monkeypatch a crafted source / `lint_skill_md`), then run the ledger's `rollback()` and assert **zero** `<command>/` directories remain and the pre-existing `skills_dir` content the user already had is untouched.

### Implementation for User Story 1

- [X] T008 [US1] Create `src/bookwright/integrations/lint.py` with `approx_tokens(text)` (tiktoken `cl100k_base` if importable, else `math.ceil(len(text)/4)`; optional import only — no new runtime dep, R6) and `lint_skill_md(skill_dir: Path) -> None` enforcing rules 1–4 in order — `invalid_frontmatter` (parse via `bookwright.io.frontmatter.parse_frontmatter`, non-empty metadata), `name_mismatch` (`metadata["name"] == skill_dir.name` and `< 64`), `description_too_long` (`0 < len < 1024`), `body_over_budget` (`approx_tokens(body) < SKILL_BODY_MAX_TOKENS`) — raising `SkillLintError(skill, rule, detail)` on the first violation; pure, never mutates the filesystem (contract `lint_skill_md.md`, FR-015).
- [X] T009 [US1] Create `src/bookwright/integrations/materialize.py` with `iter_command_sources()` (enumerate `*.md` at the top of `importlib.resources.files("bookwright.resources").joinpath("commands")`, excluding `references/`, R4), `_transform_body` (`body.replace("{ARGS}", "$ARGUMENTS")` + post-condition assert no `{ARGS}`/`{SCRIPT}` survives, R2/FR-007/SC-003), `_render_frontmatter` (ordered `name`/`description`/`license`/`metadata` → `yaml.safe_dump(allow_unicode=True, sort_keys=False)` between `---` fences, R5/FR-003/005/006; `license = fm.metadata.get("license", DEFAULT_SKILL_LICENSE)` — honour a source-declared license, fall back to the design default; no source declares one in v0, so all inherit `Apache-2.0`, FR-005/A-002), `_resolve_references` (**pure, no writes**: for each distinct `references/<file>.md` cited in the body, resolve the packaged `commands/references/<file>.md` and check it exists — a missing source → `SkillMaterializationError(rule="dangling_reference")`; returns the resolved `(file, source_path)` copy-list, FR-010), `_copy_references` (write the already-resolved copy-list into `skill_dir/references/` via `mkdir_tracked`/`write_bytes_atomic`), and `generate_skill_md(command_path, target_dir, integration, *, ledger: FileLedger) -> Path | None` doing steps 1 + 3–8 of the contract **with all authoring validation strictly before the first write**: derive `name` from the filename stem and **validate `fm.metadata.get("name") == name` else raise `SkillMaterializationError(rule="name_frontmatter_mismatch")`** (FR-020); resolve description via `get_description`; transform body; **resolve cited references via `_resolve_references` (pre-write existence check — a `dangling_reference` aborts here, before any directory is created, leaving zero on-disk state)**; render frontmatter; **then, at the single first mutation point**, create `skill_dir` via `mkdir_tracked(skill_dir, ledger)`, write `SKILL.md`, and copy the resolved references via `write_bytes_atomic(.., ledger)` (every created path recorded — FR-019); then `lint_skill_md(skill_dir)` — on `SkillLintError` delete `skill_dir` and re-raise (FR-016, the only post-write error; stale ledger entries inert at rollback); import `SkillsIntegration` and `FileLedger` under `TYPE_CHECKING` only (R1), and `mkdir_tracked`/`write_bytes_atomic` from `bookwright.io.fs` at module level. **The idempotency guard is added in US2/T014 (its test is T013).**
- [X] T010 [US1] Rewrite `setup()` in `src/bookwright/integrations/base.py`: add a keyword-only `ledger: FileLedger | None = None` → `ledger = ledger or NullLedger()` (standalone-callable; `FileLedger`/`NullLedger` imported from `bookwright.io.fs`); drop the placeholder-marker stub; keep the containment guards (`resolves_to_project_root` / `escapes_project_root` → `MalformedOptionError`), `mkdir_tracked(target, ledger)` the resolved target, then `for command_path in iter_command_sources(): generate_skill_md(command_path, target, self, ledger=ledger)` (module-level import of `generate_skill_md` + `iter_command_sources`; no `try/except` swallow — errors propagate, FR-001/FR-016/FR-019). Remove the now-unused `SKILL_PLACEHOLDER_MARKER_NAME` import.
- [X] T011 [US1] Update `src/bookwright/commands/init/scaffold.py` step 4: keep `mkdir_tracked(skills_target, ledger)` but drop the `.bookwright-skills-placeholder` pre-record block (lines ~371–373); call `integration.setup(project_root, manifest, parsed_options, ledger=ledger)` passing the **live `BackupLedger`** so the materializer records every created path and whole-`init` rollback unwinds them — including over a pre-existing `skills_dir` (FR-019/SC-008, R7). `scaffold.py` now imports the fs primitives from `bookwright.io.fs` (T021).
- [X] T012 [US1] Update existing tests that asserted the placeholder marker to the materialization contract: `tests/integrations/test_plugin_contract.py`, `tests/integrations/test_quickstart.py`, `tests/integrations/test_constants.py` (mark constant deprecated), and `tests/commands/test_init_default.py` — assert generated `SKILL.md` files instead of the marker; remove marker-presence assertions.

**Checkpoint**: `init` produces working, lint-clean skills for both integrations — MVP demonstrable end-to-end.

---

## Phase 4: User Story 2 - Re-running `init` preserves customizations (Priority: P2)

**Goal**: materialization is idempotent at `SKILL.md` granularity — an existing skill is never
overwritten (user edits survive), while a deleted skill is regenerated in full.

**Independent Test**: materialize; hand-edit one `SKILL.md`; re-run → that file is byte-for-byte
unchanged; delete one skill dir; re-run → only that skill is regenerated, others untouched.

### Tests for User Story 2 ⚠️

- [X] T013 [P] [US2] Add `tests/integrations/test_materialize_idempotent.py`: after a first materialization, mutate one `SKILL.md`, re-run `setup()`/`generate_skill_md`, assert the edited file is byte-for-byte identical and `generate_skill_md` returned `None` for it; delete one skill dir, re-run, assert only the missing skill is recreated (incl. its `references/`) and all others are untouched (FR-014, SC-005, A-005).

### Implementation for User Story 2

- [X] T014 [US2] Add the idempotency guard at the top of `generate_skill_md` in `src/bookwright/integrations/materialize.py` (contract step 2): if `skill_dir / "SKILL.md"` exists, return `None` immediately — write nothing, copy no references (FR-014, SC-005).

**Checkpoint**: re-running `init` is safe; US1 + US2 both hold.

---

## Phase 5: User Story 3 - Capability-aware output per integration (Priority: P3)

**Goal**: generic and Claude both emit standard-only skills in v0 (no `` !`shell` `` syntax
auto-emitted); bodies differ only by `skills_dir` + token substitution. The linter enforces the
FR-013 invariant guarding any injection that *does* appear (user-added / future).

**Independent Test**: materialize the same command for `claude` and `generic`; assert the two
bodies are identical (only `skills_dir` differs), neither contains `` !`shell` `` syntax, and a
crafted skill with a `` !`/usr/local/bin/wrapper` `` injection is rejected by the linter.

### Tests for User Story 3 ⚠️

- [X] T015 [P] [US3] Add `tests/integrations/test_skill_capabilities.py`: for each command, the materialized body for `claude` (`supports_dynamic_context=True`) and `generic` (`supports_dynamic_context=False`) is identical (US3 AC-3); no generated body contains `` !`…` `` syntax (FR-011/012, SC-006); a crafted body with an injection that targets a non-existent wrapper raises `SkillLintError(rule="forbidden_injection")`, while one that reads a project file (`` !`cat bible/constitution.md` ``) or invokes `bookwright` passes (FR-013, SC-006).

### Implementation for User Story 3

- [X] T016 [US3] Add rule 5 `forbidden_injection` to `lint_skill_md` in `src/bookwright/integrations/lint.py` as a **deny-by-default allowlist** (not a denylist heuristic): scan the body for `` !`…` `` dynamic-context injections; for each, `argv = shlex.split(cmd)` and permit **only** if (a) `argv[0] == "bookwright"`, or (b) `argv[0] in INJECTION_READ_COMMANDS` **and** no argument is an absolute path or starts with `~`; everything else (empty command, unknown executable, absolute/home path) raises `SkillLintError(rule="forbidden_injection")` (contract rule 5, FR-013). This makes the invariant a verifiable grammar, never touches the filesystem, and is secure-by-default. The materializer emits none in v0, so generated skills pass trivially — this guards user customizations and future iterations.

**Checkpoint**: all three stories independently functional; per-integration behavior correct.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T017 [P] Add end-to-end test under `tests/commands/init/` (create the package `__init__.py`): run `bookwright init` into `tmp_path` for `claude`, `generic`, and `generic --skills-dir .cursor/skills`; assert one `SKILL.md` per command, every file lints clean (SC-001/SC-002), no `.bookwright-skills-placeholder` remains, nothing is written outside the resolved `skills_dir` (SC-007), and that a forced lint failure yields a `skill_lint_failed` JSON error envelope with no invalid `SKILL.md` left on disk (FR-016, quickstart "Failure you should see"). **Orphan-rollback E2E (SC-008/FR-019)**: pre-create a non-empty `skills_dir` (e.g. `.claude/skills/` with a user file) and run `init --here --force` with a forced mid-roster failure; assert the run aborts, **zero** materialized `bookwright-*` directories remain, and the user's pre-existing file in `skills_dir` is untouched.
- [X] T018 Run `uv run ruff check && uv run ruff format --check && uv run mypy --strict src tests` and fix any findings (Constitution II/III/VIII CI gates).
- [X] T019 Run `uv run pytest -q` and confirm the full suite is green with ≥80% coverage on the new modules (`materialize.py`, `lint.py`, `descriptions.py`) (Constitution VIII).
- [X] T020 Walk the `quickstart.md` commands manually (claude + generic init, idempotency edit/delete loop) and confirm observed behavior matches the documented output; fix any drift.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001, T002, T021 — no dependencies, fully parallel (different files).
- **Foundational (Phase 2)**: T003 is independent — it reuses the **pre-existing** `SKILL_DESCRIPTION_MAX_LENGTH` (not a T001 addition), so it can land in parallel with Phase 1; T004 depends on T003. Blocks US1.
- **US1 (Phase 3)**: depends on Phase 2 **and T021** (the materializer/`setup()` import `io.fs`). Tests T005–T007 first (expect fail), then T008→T009→T010→T011, then T012.
- **US2 (Phase 4)**: depends on US1 (`generate_skill_md` must exist). Adds one guard + its test.
- **US3 (Phase 5)**: depends on US1 (`lint.py`, `materialize.py` must exist). Independent of US2.
- **Polish (Phase 6)**: depends on all desired stories complete.

### Story Independence

- **US1 (P1)**: the MVP — first-run generation + linting. Standalone.
- **US2 (P2)**: a re-run guarantee layered on US1's helper; does not touch US3.
- **US3 (P3)**: a per-integration invariant layered on US1's helper; does not touch US2.

### Within US1 (ordering)

- `io/fs.py` (T021) before `materialize.py` (T009) and `base.py` (T010) — both import the
  fs primitives / `FileLedger` from it.
- `lint.py` (T008) and `materialize.py` (T009) — T009 imports `lint_skill_md`, so T008 before T009.
- `base.py` setup (T010) imports `generate_skill_md` + `iter_command_sources` → after T009.
- `scaffold.py` (T011) after T010 (setup() must already materialize) and after T021 (imports `io.fs`).
- Existing-test cleanup (T012) last in the story (after marker is gone).

### Parallel Opportunities

- T001 ‖ T002 ‖ T021 (different files).
- All story test files are mutually independent and can be authored in parallel: T005 ‖ T006 ‖ T007 (US1), T013 (US2), T015 (US3), T017 (E2E).
- T004 ‖ the US1 test trio once T003 lands.
- US2 and US3 implementation (T014, T016) can proceed in parallel once US1 is merged — different files (`materialize.py` vs `lint.py`).

---

## Parallel Example: User Story 1 tests

```bash
# Author the three US1 test files together (they target different files):
Task: "test_skill_lint.py — rules 1–4 pass/fail in tests/integrations/test_skill_lint.py"
Task: "test_materialize.py — generation/roster/tokens/refs in tests/integrations/test_materialize.py"
Task: "test_setup_materialize.py — shared setup() contract in tests/integrations/test_setup_materialize.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup (T001–T002 + T021 fs extraction) → Phase 2 Foundational (T003–T004).
2. Phase 3 US1 (T005–T012): build the linter, the materializer (ledger-tracked), the shared
   `setup()`, wire `scaffold.py`, and update legacy tests.
3. **STOP and VALIDATE**: `init` into an empty dir produces lint-clean skills for both
   integrations. This is a shippable increment.

### Incremental Delivery

1. US1 → MVP (working skills after `init`).
2. + US2 (T013–T014) → safe re-runs (idempotency).
3. + US3 (T015–T016) → capability-aware invariant + linter rule 5.
4. + Polish (T017–T020) → E2E coverage and all four CI gates green.

---

## Notes

- [P] = different files, no incomplete-task dependency.
- Tests precede implementation within each story (write, watch fail, then implement).
- `generate_skill_md` is built once in US1 (T009) and extended by one guard in US2 (T014);
  `lint.py` is built in US1 (T008) and gains rule 5 in US3 (T016) — these are the only two
  files touched across stories, and the additions are non-conflicting.
- No `` !`shell` `` auto-injection, no `.bookwright/scripts/` wrappers, no new runtime
  dependency, no third integration (scope discipline — plan Constitution Check).
- Commit after each task or logical group; merge to `main` only when `/speckit-analyze` is
  clean and all four gates pass.
