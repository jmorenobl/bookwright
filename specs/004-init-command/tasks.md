---
description: "Task list for iteration 4 — `bookwright init` command"
---

# Tasks: `bookwright init` Command

**Input**: Design documents from [/specs/004-init-command/](.)

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/init_command.md](contracts/init_command.md), [quickstart.md](quickstart.md)

**Tests**: Included. The spec assigns each FR a test obligation (Principle VIII, Constitution §IX) and the contract pins behavioural invariants verified by subprocess + in-process tests (contract § 7). Tests are NOT optional in this iteration.

**Organization**: Tasks grouped by user story. Setup + Foundational complete first; the five user stories (US1, US2 = P1; US3, US4 = P2; US5 = P3) may then proceed in priority order or in parallel where the test-file boundaries make it safe.

## Format: `- [ ] TaskID [P?] [Story?] Description`

- **[P]**: parallelizable — different file, no incomplete-dependency
- **[Story]**: required for user-story phase tasks (US1..US5)

## Path Conventions (per [plan.md](plan.md) § Project Structure)

- Production: `src/bookwright/`
- Tests: `tests/` at repository root
- This iteration adds `src/bookwright/commands/init.py` + private `_init_*.py` siblings, `src/bookwright/resources/project/`, `src/bookwright/resources/vocabularies/`, and `tests/commands/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lay down the new directory skeleton so the foundational and user-story phases have somewhere to land. No business logic in this phase.

- [ ] T001 Create `src/bookwright/resources/project/__init__.py` (empty marker file, makes the packaged template tree a subpackage discoverable via `importlib.resources.files("bookwright.resources.project")`).
- [ ] T002 [P] Create `src/bookwright/resources/vocabularies/__init__.py` (empty marker file, makes the packaged vocabulary stubs a subpackage).
- [ ] T003 [P] Create `tests/commands/__init__.py` (empty marker file, makes the new test subpackage discoverable by `pytest`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build every shared helper the five user stories will compose into. All file boundaries are distinct, so most tasks here are `[P]`.

**⚠️ CRITICAL**: No user-story work may begin until this phase is complete.

- [ ] T004 [P] Add the FR-021a `PROJECT_NAME` validator in [src/bookwright/commands/_init_validate.py](src/bookwright/commands/_init_validate.py): `validate_project_name(value: str) -> str` (returns the value with leading/trailing whitespace stripped) plus an `InvalidProjectNameError` carrying `(value: str, rule: Literal["empty","path_separator","dot_or_dotdot","leading_dot","too_long","reserved_name"])`. Reserved-name list per research § R3 (Windows: `CON`, `PRN`, `AUX`, `NUL`, `COM1`..`COM9`, `LPT1`..`LPT9`). Maximum length 100. No filesystem side-effects.
- [ ] T005 [P] Add resolution helpers in [src/bookwright/commands/_init_resolve.py](src/bookwright/commands/_init_resolve.py): `resolve_authors(project_root: Path) -> tuple[list[str], bool]` (per research § R1, returns `(authors, fellback_to_sentinel)`); `resolve_language() -> str` (per research § R2, validates against iteration-2 `ISO_639_1_CODES`, falls back to `"es"`); `derive_slug(raw_name: str) -> str` (per research § R3, uses `python-slugify`, re-checks the slug against the FR-021a reserved-name list); `is_interactive() -> bool` (returns `sys.stdin.isatty() and sys.stdout.isatty()`, per research § R7). No filesystem side-effects beyond the `subprocess.run(["git", "config", ...])` read in `resolve_authors`.
- [ ] T006 [P] Add the success / error JSON envelopes and the `.bookwright/init-options.json` record types in [src/bookwright/commands/_init_envelope.py](src/bookwright/commands/_init_envelope.py): pydantic models `ResolvedInvocation` (data-model § 2) and `InitOptionsRecord` (data-model § 1, `schema_version: int = 1`, `created_at`, `bookwright_version`, `options: ResolvedInvocation`); helper functions `success_envelope(resolved: ResolvedInvocation, warnings: list[str]) -> dict`; `error_envelope(code: str, message: str, details: dict, rolled_back: bool) -> dict`; `dump_success_to_stdout(payload: dict)` (uses `json.dumps(payload, separators=(",", ":")) + "\n"` per contract § 3.1); `dump_options_record(root: Path, resolved: ResolvedInvocation) -> Path` (writes `<root>/.bookwright/init-options.json` with `indent=2`, returns the path so the scaffolder can register it with the backup ledger).
- [ ] T007 [P] Add the backup ledger primitive in [src/bookwright/commands/_init_scaffold.py](src/bookwright/commands/_init_scaffold.py): `@dataclass(frozen=True) class BackupEntry` (`target: Path`, `backup_path: Path | None`, `was_directory: bool`) per data-model § 3; `class BackupLedger` with `record_new_file(target)`, `record_new_directory(target)`, `record_overwrite(target) -> Path` (copies original to `<project_root>/.bookwright/cache/backup/<secrets.token_hex(6)>/<target.relative_to(project_root)>` via `shutil.copy2`, creating the per-token parent directory if absent; returns the backup path; raises `BackupCreationError` on copy failure per FR-030 last sentence — surfaces as contract § 4 `backup_creation_error` exit 6; backups under `.bookwright/cache/` are excluded from git by the generated `.gitignore` per spec § Assumptions, so `git add .` will not stage them during the initial commit), `commit()` (success path: `unlink` every `backup_path`), `rollback()` (failure path: walk entries in reverse, restore overwrites via `shutil.move`, `unlink` new files, `rmtree` new directories — see research § R4). The ledger refuses any `target` outside `project_root` (FR-014).
- [ ] T008 Add the atomic file writer + template walker in [src/bookwright/commands/_init_scaffold.py](src/bookwright/commands/_init_scaffold.py): `write_bytes_atomic(target: Path, payload: bytes, ledger: BackupLedger)` (records in ledger; writes via `tempfile.mkstemp` + `os.fsync` + `os.replace`, per research § R6, mirrors the iteration-2 `Manifest.dump` pattern); `mkdir_tracked(target: Path, ledger: BackupLedger)` (records new directory before creation); `render_resource_tree(target_root: Path, context: dict, ledger: BackupLedger) -> None` walks `importlib.resources.files("bookwright.resources.project")` recursively, byte-copies non-`.j2` files, and renders `.j2` files via a single `jinja2.Environment(loader=PackageLoader("bookwright.resources.project", ""), autoescape=False, keep_trailing_newline=True, undefined=jinja2.StrictUndefined)` per research § R9. Empty directories are kept via their `.gitkeep` resources. Also add `dump_manifest_tracked(manifest, target: Path, ledger: BackupLedger) -> None` that registers `target` with the ledger first (recording new file via `record_new_file` or pre-existing overwrite via `record_overwrite`, per T007) and then calls iteration-2's `Manifest.dump(manifest, target)` **unchanged** — this keeps `Manifest.dump` the sole TOML writer per FR-015 + contract § 7.3 while leaving the iteration-2 public signature intact. Same file as T007, so this task is sequential after T007 (not `[P]`).
- [ ] T009 [P] Add the git subprocess wrapper in [src/bookwright/commands/_init_git.py](src/bookwright/commands/_init_git.py): `git_available() -> bool` (via `shutil.which("git")`); `is_inside_existing_repo(root: Path) -> bool` (walks parents for `.git/`); `init_and_commit(root: Path, message: str, author_name: str, ledger: BackupLedger) -> None` runs `git init`, `git add .`, `git commit -m <message>` with `cwd=root`, `check=True`, augmenting `env` with `GIT_AUTHOR_NAME/_EMAIL/_COMMITTER_*` from the resolved author plus the documented fallback email `author@bookwright.local` (per research § R8); pre-registers `<root>/.git` as a new directory in the ledger before running `git init` so a failed commit rolls back the partial repo. On `CalledProcessError`, raises `GitInitError(stderr: str)` carrying the verbatim git stderr (spec edge case under FR-022).
- [ ] T010 [P] Author the bundled vocabulary stubs in [src/bookwright/resources/vocabularies/propp.ttl](src/bookwright/resources/vocabularies/propp.ttl) and [src/bookwright/resources/vocabularies/greimas.ttl](src/bookwright/resources/vocabularies/greimas.ttl): each is a minimal valid Turtle file (prefix block for `propp:`/`greimas:` plus one empty `owl:Class` declaration), per plan.md § Project Structure. Full content lands with iteration 10.
- [ ] T011 [P] Author the packaged project template tree under [src/bookwright/resources/project/](src/bookwright/resources/project/): `README.md.j2` (uses `{{ title }}`, `{{ project_slug }}`, `{{ author }}`); literal `.gitignore` with entries `.bookwright/cache/`, `*.pyc`, `__pycache__/`, `.venv/`, `.env` (per spec § Assumptions); `manuscript/.gitkeep`; `bible/{constitution.md.j2, timeline.md, relationships.md, pov-structure.md, themes.md, glossary.md, research.md, subplots.md, characters/.gitkeep, settings/.gitkeep}` (minimal placeholders — full content lands with iteration 7, per FR-010); `outline/{arcs.md, structure.md, synopsis.md, scenes.md}` (placeholders, per FR-011); `.bookwright/{schema/.gitkeep, vocabularies/, templates/.gitkeep, cache/.gitkeep}` (no `.gitkeep` under `vocabularies/` — the `.ttl` files copied at scaffold time keep that directory non-empty). The vocabulary files themselves are copied at scaffold time from the vocabularies subpackage (not stored under `project/`), per plan.md § Structure Decision. Implementation note: the `.bookwright/cache/backup/` subdirectory is created on-demand by `_init_scaffold.BackupLedger.record_overwrite` (T007) — it does NOT appear in the resource tree and does NOT need a `.gitkeep`. It exists only when `--force`/`--here` has overwrites to back up, and is removed by `ledger.commit()` on success.
- [ ] T012 [P] Author the shared test fixtures in [tests/commands/conftest.py](tests/commands/conftest.py): `scaffold_in_tmp` (chdir into `tmp_path`, yield, restore cwd); `git_available` (skip if `shutil.which("git") is None`); `non_interactive_io` (monkeypatch `bookwright.commands._init_resolve.is_interactive` to return `False`); `fake_git_missing` (monkeypatch `bookwright.commands._init_git.git_available` to return `False`); `dirhash(path: Path) -> list[tuple[str, str]]` helper (sorted `(rel_path, sha256(bytes))` snapshot used by the rollback grid).
- [ ] T013 Register the `init` subcommand on the Typer app in [src/bookwright/cli.py](src/bookwright/cli.py) (`from bookwright.commands import init` + `app.command("init")(init.run)`). Placeholder `init.run` lands in T014; this task only wires the registration so the command appears in `bookwright --help` once `init.py` exists.
- [ ] T014 Create the Typer entry-point skeleton at [src/bookwright/commands/init.py](src/bookwright/commands/init.py): declare `def run(...)` with the full flag surface from contract § 1 (`project_name`, `--here`, `--force`, `--no-git`, `--integration`, `--integration-options`, `--json`, hidden `--ai`), `context_settings={"allow_extra_args": True, "ignore_unknown_options": True}` per research § R5, a `typer.Callback`-style pre-check that returns `typer.Exit(2)` with `code: "mutually_exclusive"` when both `project_name` and `--here` (or neither) are present (FR-002). **Precedence**: this mutex check MUST run AFTER the removed-flag pre-callback added in T032 (plan.md §"Deprecated-flag handling": removed_flag wins exit 2 over mutually_exclusive when both apply). T032 is responsible for the ordering wiring; T014 only declares the mutex check. The body raises `NotImplementedError` for now — orchestration lands in US1 (T017). Depends on T013.

**Checkpoint**: Foundational complete — every helper module, every resource, every shared fixture, and the Typer registration is on `main`. User stories now compose them.

---

## Phase 3: User Story 1 — Scaffold a new book project in one command (Priority: P1) 🎯 MVP

**Goal**: From any directory, running `bookwright init <NAME>` produces the full project tree from design § 7, populates a valid manifest, installs the Claude integration's skills directory, and creates exactly one git commit titled `Initial commit from bookwright init`.

**Independent Test**: From an empty parent directory, run `bookwright init mi-libro`. Confirm (a) directory `mi-libro/` was created, (b) it contains every file/subdirectory enumerated in `bookwright-design.md` § 7, (c) `manifest.toml` parses against the iteration-2 model with every mandatory field populated, (d) `.claude/skills/` exists with the iteration-3 marker, and (e) `git log --oneline` shows exactly one commit `Initial commit from bookwright init` with zero unstaged files (spec § US1 Independent Test, SC-002, SC-003, SC-004).

### Tests for User Story 1

- [ ] T015 [P] [US1] Author [tests/commands/test_init_default.py](tests/commands/test_init_default.py): in-process `CliRunner` invocations covering Acceptance Scenarios 1–3 — default `bookwright init mi-libro`; manifest field grid (`book.title`, `book.authors` non-empty, `book.type == "novel"` per FR-017, `book.language` per FR-018, `book.status == "idea"` per FR-019, `integration.key == "claude"`, `integration.skills_dir == ".claude/skills"`, `integration.options == {}` per FR-020); `"Mi Libro"` → directory `mi-libro/` + title `"Mi Libro"` (FR-021). Plus the FR-027 empty-target-reuse case: pre-create an empty `mi-libro/` in the parent, run `bookwright init mi-libro`, assert success with no prompt and the same on-disk tree as the default scenario. Verify every entry from design § 7 is present, the manifest round-trips through `Manifest.load`, `.claude/skills/` exists with the iteration-3 marker, and `git log` shows the one commit. Plus the FR-026 `--force` happy-path case in named mode: pre-create `mi-libro/` containing a distinctive sentinel `manifest.toml` (e.g. `# pre-existing`) AND an unrelated `notes.txt` whose content is captured as `EXPECTED_NOTES`. Run `bookwright init mi-libro --force`. Assert: (a) exit 0; (b) `manifest.toml` was overwritten — its content now parses through `Manifest.load` cleanly and matches the iteration-2 default-field grid (the pre-existing `# pre-existing` marker is gone); (c) `notes.txt` still exists with content `EXPECTED_NOTES` (FR-026 "does not delete unrelated pre-existing files"); (d) `list((project_root / ".bookwright/cache/backup").rglob("*"))` is empty post-success (`ledger.commit()` removed the backups per T007); (e) `git log` shows the one expected commit with no unstaged files. Plus the SC-001 regression guard-rail: wrap the default-flag run in `t0 = time.monotonic()` / `t1 = time.monotonic()` and assert `(t1 - t0) < 60.0` (CI budget, generous vs. the 30 s UX target — spec § SC-001 clarification — so shared runners don't flake while a runaway hook or accidental `time.sleep` still trips the suite). Uses `scaffold_in_tmp` + `git_available`.
- [ ] T016 [P] [US1] Author [tests/commands/test_init_validation.py](tests/commands/test_init_validation.py): parametrized FR-021a grid — empty, `"foo/bar"`, `"foo\\bar"`, `"."`, `".."`, `".hidden"`, 101-char name, `"CON"`, `"PRN"`, `"COM1"`, `"LPT9"`, plus the positive cases `"mi-libro"`, `"Mi Libro"`, `"Café-Society"`, `"librö-ñ"`. For each negative case, assert exit code `2`, error envelope `code: "invalid_project_name"`, `details.rule` matches the rule, and no files are written outside `tmp_path`.
- [ ] T017 [P] [US1] Author [tests/commands/test_init_options_record.py](tests/commands/test_init_options_record.py): assert `.bookwright/init-options.json` has `schema_version == 1`, `created_at` matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`, and `bookwright_version == bookwright.__version__` on every run (FR-034 envelope shape). Parametrize the `options`-round-trip assertion across every CLI flag combination the user-story tests exercise (per contract § 7.8): default named (US1); `--here` in an empty cwd (US2); `--here --force` in a non-empty cwd (US2); `--integration generic` (US3); `--integration generic --integration-options="--skills-dir .cursor/skills"` (US3); `--no-git` (US4); `--ai claude` (US5). For each combination, re-read `init-options.json`, re-parse into `InitOptionsRecord`, and assert `record.options == resolved_invocation_seen_by_init_run` (modulo `created_at`). Also assert the file is staged in the initial commit on the runs where git was initialised (`git show HEAD --stat | grep init-options.json`).

### Implementation for User Story 1

- [ ] T018 [US1] Replace the `NotImplementedError` body of [src/bookwright/commands/init.py](src/bookwright/commands/init.py) `run(...)` with the named-mode happy-path orchestration: validate (via `_init_validate.validate_project_name` + slug re-check), resolve author / language / slug / `project_root = Path.cwd() / slug` (via `_init_resolve`), apply the FR-026 + FR-027 conflict matrix for named mode (target absent → mkdir; target exists & empty → reuse, no prompt per FR-027; target exists & non-empty & no `--force` → refuse with `code: "target_not_empty"` exit 4 per FR-026; target exists & non-empty & `--force` → proceed and rely on the backup ledger to overwrite name collisions while leaving unrelated pre-existing files intact per FR-026 edge case and FR-030), construct `ResolvedInvocation` (`integration_key="claude"`, `force=<parsed --force value>`, `no_git=False`, `json_output=False`, `git_status="initialized"`, `deprecated_flags_seen=[]`), build `Manifest` via `Manifest.build(...)`. Depends on T004–T009, T014.
- [ ] T019 [US1] Wire the scaffolding pipeline into `init.run` in [src/bookwright/commands/init.py](src/bookwright/commands/init.py): instantiate `BackupLedger(project_root)`, call `render_resource_tree(project_root, context, ledger)`, write `manifest.toml` via `_init_scaffold.dump_manifest_tracked(manifest, project_root / "manifest.toml", ledger)` — the helper registers the target with the ledger (recording new file or `record_overwrite` under `.bookwright/cache/backup/` if pre-existing, per T007 / data-model § 3), then delegates to iteration-2's `Manifest.dump(manifest, target)` **without modifying its signature** (spec § Assumptions: "This iteration consumes those APIs; it does not reimplement them"). `Manifest.dump` remains the sole TOML writer per FR-015 / contract § 7.3. Then call `mkdir_tracked(project_root / ".bookwright/vocabularies", ledger)` and copy the two vocabularies from `bookwright.resources.vocabularies` into that directory; write `.bookwright/init-options.json` via `_init_envelope.dump_options_record(...)`. On any exception, call `ledger.rollback()` and re-raise. Depends on T018.
- [ ] T020 [US1] Wire the Claude integration's `setup()` into `init.run` in [src/bookwright/commands/init.py](src/bookwright/commands/init.py): `integration_cls = bookwright.integrations.get("claude")`; the orchestrator participates the integration's writes in the ledger via a thin wrapper (plan.md §Summary, bullet "The chosen integration's `setup()` runs after the rest of the tree is on disk"). Concretely: compute `skills_target = project_root / integration_cls().resolve_skills_dir(parsed_options={})`; call `_init_scaffold.mkdir_tracked(skills_target, ledger)` (T008); call `ledger.record_new_file(skills_target / bookwright.integrations.SKILL_PLACEHOLDER_MARKER_NAME)` (T007); THEN call `integration_cls().setup(project_root, manifest, parsed_options={})`. The iteration-3 stub is idempotent (`mkdir(exist_ok=True)` and `if not marker.exists(): marker.write_text(...)`) so the pre-registration changes neither on-disk bytes nor the iter-3 test pins. On `setup()` exception the standard `ledger.rollback()` from T019 unlinks the marker and removes the skills directory. NOTE: this wrapper does NOT modify the iter-3 contract (spec § Assumptions: "consumes those APIs; it does not reimplement them"); iteration 9 will revisit if real SKILL.md materialization writes files the wrapper does not know about. Depends on T019.
- [ ] T021 [US1] Wire the git init + commit step into `init.run` in [src/bookwright/commands/init.py](src/bookwright/commands/init.py): if `git_available()` and the user did not pass `--no-git` and `is_inside_existing_repo(project_root)` is False, call `_init_git.init_and_commit(project_root, "Initial commit from bookwright init", author, ledger)`. Track outcome in `resolved.git_status`. Depends on T020.
- [ ] T022 [US1] Emit the success envelope from `init.run` in [src/bookwright/commands/init.py](src/bookwright/commands/init.py): on success, on `--json` call `_init_envelope.dump_success_to_stdout(success_envelope(resolved, warnings))`; otherwise print a one-line `rich`-styled success message to stderr and a minimal final line to stdout per FR-033. Call `ledger.commit()` to delete the backups (this also handles the SC-005 "byte-for-byte equivalent on success" rule: backups are cleaned up only after every step succeeded). Returns `typer.Exit(0)`. Depends on T021.

**Checkpoint**: US1 is independently functional — the MVP scaffold path works end-to-end. T015 / T016 / T017 pass.

---

## Phase 4: User Story 2 — Initialize in the current directory (Priority: P1)

**Goal**: `bookwright init --here` scaffolds in `Path.cwd()` instead of a child directory, with the empty / non-empty + `--force` matrix and the FR-029 non-interactive refusal both honoured.

**Independent Test**: Create a clean temp directory, `cd` in, run `bookwright init --here`. Verify artifacts appear directly (no nested folder), git is initialised at the same level, and the non-empty / non-interactive / `.bookwright/`-already-exists branches each behave per spec § US2 Acceptance Scenarios 1–5.

### Tests for User Story 2

- [ ] T023 [P] [US2] Author [tests/commands/test_init_here.py](tests/commands/test_init_here.py): `CliRunner` invocations covering Acceptance Scenarios 1–5 — empty cwd with `--here`; non-empty cwd with `--here` (interactive `y` confirms; interactive `N` refuses with exit 4, `code: "user_declined_overwrite"`, no files written); non-empty cwd with `--here --force` (no prompt, name collisions overwritten, backups restored on failure); cwd containing `.bookwright/` rejected with exit 3, `code: "already_initialized"` even under `--force` (FR-028); `init mi-libro --here` rejected as `code: "mutually_exclusive"`. Plus the FR-025 invariant: with `git_available`, pre-create `.git/` in `tmp_path` via `subprocess.run(["git", "init"], cwd=tmp_path, check=True)`; commit a sentinel file with a known SHA; capture `git rev-parse HEAD` (`HEAD_BEFORE`). Run `bookwright init --here` (no `--no-git`). Assert: (a) `git rev-parse HEAD` is unchanged (`HEAD_BEFORE` is still `HEAD`); (b) the sentinel file is still tracked and its blob SHA is unchanged; (c) the success envelope `git_status == "skipped_existing_repo"`; (d) `.bookwright/init-options.json` has `options.git_status == "skipped_existing_repo"`; (e) the contract § 5 warning line `bookwright: warning: existing .git/ detected; skipped git init and commit` is on stderr; (f) the JSON envelope's `warnings` array contains the same line (when `--json` is also passed in a second sub-case).
- [ ] T024 [P] [US2] Author [tests/commands/test_init_non_interactive.py](tests/commands/test_init_non_interactive.py): with `non_interactive_io` fixture, `bookwright init --here` in a non-empty `tmp_path` must exit 4 with `code: "non_interactive_here"` and `details` pointing at `--force`; under `--json`, the error envelope is on stdout and stderr is silent (contract § 5); the directory snapshot is unchanged.

### Implementation for User Story 2

- [ ] T025 [US2] Extend `init.run` in [src/bookwright/commands/init.py](src/bookwright/commands/init.py) with `--here` mode: when `--here` is set, set `project_root = Path.cwd()`, derive `title` and `project_slug` from `project_root.name`, run a reduced FR-021a check on the basename (empty / path-separator / reserved only per research § R3), then enter the conflict matrix (`.bookwright/` exists → `already_initialized` exit 3; non-empty + no `--force` + interactive → prompt; non-empty + no `--force` + non-interactive → `non_interactive_here` exit 4; non-empty + `--force` → proceed). The interactive prompt uses `typer.confirm("bookwright: directory '<abs>' is not empty. Overwrite name collisions?", default=False)`. On negative answer, emit `code: "user_declined_overwrite"` exit 4 with the ledger empty (no rollback needed). Depends on T022.
- [ ] T026 [US2] Add the FR-025 "inside existing repo under `--here`" branch in `init.run`: when `is_inside_existing_repo(project_root)` is True and `--here` was used, set `git_status="skipped_existing_repo"`, emit the contract-§5 warning line on stderr, skip the git init/commit call, and continue with the success path. Depends on T025.

**Checkpoint**: US1 + US2 both work independently. T015–T017 + T023–T024 pass.

---

## Phase 5: User Story 3 — Choose a different AI integration (Priority: P2)

**Goal**: `--integration generic` (and `--integration-options="--skills-dir <path>"`) routes the skills installation through the iteration-3 generic integration; unknown integration keys and invalid integration options fail with the structured exception family from iteration 3.

**Independent Test**: Three runs in separate `tmp_path` directories: `init mi-libro --integration generic` (skills land in `.agents/skills/`, manifest records `key="generic"` + `skills_dir=".agents/skills"`); same with `--integration-options="--skills-dir .cursor/skills"` (skills land in `.cursor/skills/`, options recorded); `--integration unknown` fails with `code: "unknown_integration"` exit 5 + writes no files.

### Tests for User Story 3

- [ ] T027 [P] [US3] Author [tests/commands/test_init_integrations.py](tests/commands/test_init_integrations.py): parametrized matrix — `--integration claude` (default-equivalent); `--integration generic` (`.agents/skills/` present, no `.claude/`); `--integration generic --integration-options="--skills-dir .cursor/skills"` (`.cursor/skills/` present, options round-trip into manifest + init-options.json); `--integration unknown` (exit 5, `code: "unknown_integration"`, `details.value == "unknown"`, `details.valid == ["claude", "generic"]`); `--integration generic --integration-options="--cursor-dir x"` (exit 5, `code: "unknown_option"`, `details.option == "--cursor-dir"` and the same `"--cursor-dir"` substring appears verbatim in `message` — FR-006 "quotes the offending option"); `--integration generic --integration-options="--skills-dir"` (missing value → exit 5, `code: "malformed_option"`, `details.option == "--skills-dir"`, substring appears verbatim in `message`); `--integration generic --integration-options='"--skills-dir'` (unbalanced quote → exit 5, `code: "malformed_option"`; on tokenization failure assert `details.raw == '"--skills-dir'` and that the verbatim raw value appears in `message` — FR-006 "for tokenization errors, the original raw value"). Every error case asserts a `dirhash` snapshot equal to the pre-invocation state. Plus one SC-008 differential test: scaffold `init mi-libro --integration claude --no-git` and `init mi-libro --integration generic --no-git` into two sibling `tmp_path` directories (`--no-git` keeps git commit hashes out of the diff); compute `dirhash` of each excluding (a) the integration-owned skills tree (`.claude/skills/` vs `.agents/skills/`), (b) `manifest.toml` (the `[integration]` block differs), and (c) `.bookwright/init-options.json` (the `options.integration_key` field differs by design per FR-034); assert the two snapshots are byte-for-byte identical — the rest of the generated tree must NOT depend on the integration key (spec SC-008).

### Implementation for User Story 3

- [ ] T028 [US3] Extend `init.run` in [src/bookwright/commands/init.py](src/bookwright/commands/init.py): replace the hard-coded `"claude"` from US1 with the actual `--integration` flag value (default `"claude"`); resolve the class via `bookwright.integrations.get(key)`; on `UnknownIntegrationError`, hoist its `code` / `message` / `details` into the error envelope (contract § 4 "Origin: iteration 3"); parse `--integration-options` via `bookwright.integrations.parse_options(raw, integration_cls)` — iteration-3 is the only `shlex.split` site (contract § 7.4); on `UnknownOptionError`, `MalformedOptionError`, `InvalidOptionDeclarationError`, hoist the same way. The resolved options flow into `Manifest.build(...integration_options=parsed_options...)` and into `ResolvedInvocation.integration_options`. The skills directory is whatever `integration_cls().resolve_skills_dir(parsed_options)` returns — `init.run` never branches on the key (Principle V). Depends on T022.

**Checkpoint**: US1 + US2 + US3 work. T027 passes.

---

## Phase 6: User Story 4 — Skip git initialization (Priority: P2)

**Goal**: `--no-git` skips git entirely; missing git binary without `--no-git` warns + proceeds; both result in `git_status` accurately recording what happened.

**Independent Test**: `bookwright init mi-libro --no-git` in a clean parent → no `.git/`, no commit, success report explicitly notes git was skipped (`git_status: "skipped_by_flag"`). Same command with `fake_git_missing` fixture (no `--no-git`) → succeeds with `git_status: "skipped_no_binary"` and the contract § 5 warning line on stderr.

### Tests for User Story 4

- [ ] T029 [P] [US4] Author [tests/commands/test_init_no_git.py](tests/commands/test_init_no_git.py): `--no-git` happy path (no `.git/`, `git_status == "skipped_by_flag"`, exit 0); `fake_git_missing` happy path (no `.git/`, `git_status == "skipped_no_binary"`, contract § 5 warning on stderr, JSON envelope's `warnings` array contains it); `--no-git` over an already-`.git/`-bearing directory leaves the existing repo untouched (no new init, no commit, no warning since `--no-git` was explicit). Plus the commit-author email fallback (spec § Assumptions): with `git_available`, scaffold a fresh project in an env where `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, and `HOME` points to an empty tmp dir (i.e. no user-level git identity); assert the resulting `git log -1 --format='%ae'` equals `author@bookwright.local`. Then repeat with `git config --global user.email override@example.com` (in the scoped HOME) and assert the override wins — confirms the env-var fallback only fills the gap and never overrides an existing config.

### Implementation for User Story 4

- [ ] T030 [US4] Extend the git step in `init.run` ([src/bookwright/commands/init.py](src/bookwright/commands/init.py)): when `--no-git` is set, skip the git wrapper entirely and set `git_status="skipped_by_flag"`; when `git_available()` is False and `--no-git` is NOT set, scaffold succeeds with `git_status="skipped_no_binary"` and the contract § 5 warning line added to `warnings`. The existing `is_inside_existing_repo` branch from T026 already covers `git_status="skipped_existing_repo"`. Depends on T021.

**Checkpoint**: US1 + US2 + US3 + US4 work. T029 passes.

---

## Phase 7: User Story 5 — Migrate from deprecated flags (Priority: P3)

**Goal**: `--ai claude` behaves like `--integration claude` with a stderr deprecation warning; `--ai-skills` and `--ai-commands-dir` are removed flags that fail with `code: "removed_flag"` exit 2 + a structured pointer to the modern equivalent. All before any filesystem mutation (FR-031, SC-005).

**Independent Test**: Three runs — `--ai claude` (success, warning on stderr); `--ai-skills` (exit 2, error envelope `code: "removed_flag"`, details name the rule); `--ai-commands-dir x` (exit 2, error envelope names `--integration-options="--skills-dir <path>"` as the modern form). Stderr capture confirms the wording.

### Tests for User Story 5

- [ ] T031 [P] [US5] Author [tests/commands/test_init_deprecated_flags.py](tests/commands/test_init_deprecated_flags.py): `--ai claude` produces the same project tree as `--integration claude` byte-for-byte **excluding `.bookwright/init-options.json`** (the file diverges by design per FR-034 — `options.deprecated_flags_seen == ["--ai"]` for the deprecated invocation and `[]` for the modern one). The comparison uses `dirhash` with `.bookwright/init-options.json` filtered from both snapshots. Exit 0, one stderr warning line matching contract § 5, the `warnings` array under `--json` includes it, `ResolvedInvocation.deprecated_flags_seen == ["--ai"]`. `--ai-skills` and `--ai-commands-dir` (with or without a value): exit 2, `code: "removed_flag"`, `details.flag` quotes the offending flag, `details.modern` quotes the replacement; pre/post `dirhash` is identical (no scaffold side-effects, per FR-031).

### Implementation for User Story 5

- [ ] T032 [US5] Add the deprecated/removed-flag pre-callback in [src/bookwright/commands/init.py](src/bookwright/commands/init.py): a helper that inspects `click.get_current_context().args` for `--ai-skills` and `--ai-commands-dir` (both bare and `--key=value` forms) before any side-effect; on hit, emits the error envelope with `code: "removed_flag"` and exits 2. **Wire the pre-callback so it fires BEFORE the T014 mutex check** (plan.md §"Deprecated-flag handling": removed_flag wins over mutually_exclusive when both apply — both share exit 2 so the contract is only about which `code` / `message` the user sees). Add one parametrized test case in T031 covering the combined invocation `bookwright init mi-libro --here --ai-skills foo` to assert `code: "removed_flag"` (not `mutually_exclusive`) — this pins the precedence mechanically. The hidden `--ai` Typer option (already declared in T014) is now consumed: if `--ai` is set and `--integration` was not explicitly passed, route its value into `--integration`; if both are set, `--integration` wins; either way, append `"--ai"` to `resolved.deprecated_flags_seen` and emit the contract § 5 stderr warning exactly once. Depends on T028.

**Checkpoint**: All five user stories work. T031 passes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Pin the cross-story invariants from contract § 7 with their dedicated parametrized test files, and run the full quality gate.

**Note on task ordering**: T037 (the AST-invariant pin) is intentionally listed between T034 and T035 below — it was added after the original Polish phase had been numbered, so renumbering would cascade through every cross-reference in this file and in plan.md / contract / data-model. The execution order is the one given in "Dependencies & Execution Order → Parallel Opportunities" at the bottom of this file: T033, T034, T036, T037 in parallel; T035 runs after all of them.

- [ ] T033 [P] Author [tests/commands/test_init_rollback.py](tests/commands/test_init_rollback.py): the FR-030 / SC-005 atomic-or-nothing grid. Parametrize one case per documented failure mode (invalid project name → `code: "invalid_project_name"`, target not empty in named mode → `code: "target_not_empty"`, already-initialized in `--here` → `code: "already_initialized"`, unknown integration → `code: "unknown_integration"`, unknown option → `code: "unknown_option"`, malformed option → `code: "malformed_option"`, removed flag → `code: "removed_flag"`, simulated `OSError` mid-scaffold via monkeypatched `write_bytes_atomic` → `code: "filesystem_error"`, simulated `GitInitError` via monkeypatched `init_and_commit` → `code: "git_error"`, simulated backup-creation failure via monkeypatched `shutil.copy2` → `code: "backup_creation_error"` exit 6 per contract § 4, simulated `PermissionError` mid-scaffold via monkeypatched `os.replace` → `code: "permission_denied"` exit 6 per contract § 4, simulated **integration `setup()` failure** via monkeypatched `bookwright.integrations.ClaudeIntegration.setup` raising mid-call after the wrapper pre-registers the skills_dir + marker (T020) → `code: "filesystem_error"`; this case proves the wrapper actually participates the integration's writes in the ledger, closing the I2 hole flagged by `/speckit-analyze`). For each: take a `dirhash` of the target directory before invocation, run the command, take a `dirhash` after; assert exact equality. Plus the FR-014 sibling-invariant per `--here` case in the grid: snapshot `dirhash(project_root.parent)` excluding `project_root` itself before/after the invocation and assert exact equality (the command must not write outside the project root, per contract § 7.2). Also assert exit code matches the contract § 4 / data-model § 5 table.
- [ ] T034 [P] Author [tests/commands/test_init_json_envelope.py](tests/commands/test_init_json_envelope.py): subprocess invocation (the existing `tests/test_cli_subprocess.py` pattern). Asserts: success run with `--json` → stdout is a single `json.loads`-able document followed by exactly one `\n` and nothing else; failure run with `--json` for each error code → same purity on stdout; stderr contains zero bytes on a no-warning success run; stderr contains exactly N lines on a run that triggers N of the four warning categories (deprecation, git-missing, existing-repo, author-fallback); no error envelope ever lands on stderr under `--json` (contract § 5 last paragraph). Additionally, pin FR-031's non-`--json` failure contract: for the same set of error codes, invoke the command WITHOUT `--json` and assert (a) stdout is empty, (b) stderr contains exactly one human-readable line prefixed by `bookwright:` identifying the failure cause, and (c) exit code matches contract § 4 — closes the cross-mode stderr-line gap that the `--json` assertions alone would miss.
- [ ] T037 [P] Author [tests/commands/test_init_ast_invariants.py](tests/commands/test_init_ast_invariants.py): mechanical pin for contract § 7.3 + § 7.4. For every source file in `src/bookwright/commands/init.py` and `src/bookwright/commands/_init_*.py`, `ast.parse(Path(src).read_text())`, walk every `ast.Call`, and assert (a) zero calls whose attribute chain resolves to `tomlkit.dumps`, `tomlkit.dump`, `tomlkit.parse`, `tomlkit.load`, or `tomlkit.loads` (FR-015 / contract § 7.3 — `Manifest.dump` is the sole TOML writer); (b) zero calls to `shlex.split` (FR-006 / contract § 7.4 — iteration-3 `parse_options` is the sole tokeniser). On regression the test fails with a precise `<file>:<lineno>` citation so the offending site is grep-able.
- [ ] T035 Run the full quality gate as defined in CLAUDE.md and quickstart.md "For implementers": `uv run pytest --cov=src/bookwright/commands/init --cov=src/bookwright/commands/_init_validate --cov=src/bookwright/commands/_init_resolve --cov=src/bookwright/commands/_init_scaffold --cov=src/bookwright/commands/_init_git --cov=src/bookwright/commands/_init_envelope --cov-fail-under=95` (slice target per plan.md § Scale/Scope) AND `uv run pytest` (global suite, ≥80 % coverage per Constitution Principle VIII) AND `uv run ruff check` AND `uv run ruff format --check` AND `uv run mypy --strict src tests`. All five must be green; fix any failures in their respective phase files (do not relax coverage thresholds or strictness). T037's AST invariant test is part of the `uv run pytest` invocation — a failure there is a Principle-V / FR-015 regression and blocks merge.
- [ ] T036 [P] Walk through every command listed in [quickstart.md](quickstart.md) §§ 1–6 against a clean checkout and confirm the observed stderr / exit code / on-disk tree matches the documented expectations. Capture any drift in this iteration's PR description so iteration 11's E2E fixture work has a clean baseline.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — starts immediately.
- **Foundational (Phase 2)**: depends on Setup. BLOCKS all user stories.
- **User Story 1 (Phase 3, P1)**: depends on Foundational. The MVP path.
- **User Story 2 (Phase 4, P1)**: depends on US1 (extends `init.run`).
- **User Story 3 (Phase 5, P2)**: depends on US1 (extends `init.run` integration handling).
- **User Story 4 (Phase 6, P2)**: depends on US1 (extends `init.run` git step).
- **User Story 5 (Phase 7, P3)**: depends on US1 + US3 (the pre-callback routes `--ai` into the integration flag that US3 wired up).
- **Polish (Phase 8)**: the rollback / JSON-envelope grids depend on every user story phase being complete; the quality gate depends on every test file existing.

### User Story Dependencies

- US1 stands alone (only depends on Foundational).
- US2, US3, US4 each extend `init.run` independently — they touch the same file, so they cannot land truly in parallel as separate commits, but their *test files* (`test_init_here.py`, `test_init_integrations.py`, `test_init_no_git.py`) are independent and can be authored in parallel.
- US5 depends on US3 because the `--ai` flag routes through `--integration` resolution.
- US2 alone adds the `--force` flag wiring that US3 / US4 also exercise; the matrix-overlap is covered by T033 (rollback grid).

### Within Each User Story

- Authoring all `[P]` test files for a story can happen first (they fail because the implementation is not present yet — TDD-flavoured loop), then implementation tasks land sequentially because they all edit `commands/init.py`.

### Parallel Opportunities

- All four Setup tasks: T001, T002, T003 in parallel.
- All eight Foundational helper / fixture / resource tasks: T004, T005, T006, T007, T009, T010, T011, T012 in parallel (T008 sequences after T007 inside the same file; T013 / T014 depend on the helpers existing).
- All test files within a user story can be authored in parallel: T015/T016/T017 (US1), T023/T024 (US2), T027 (US3 single file), T029 (US4), T031 (US5).
- Polish test files: T033, T034, T036, T037 in parallel; T035 runs after all of them.

---

## Parallel Example: Foundational Phase

```bash
# Author all independent foundational modules + resources + fixtures together:
Task: "Add the FR-021a PROJECT_NAME validator in src/bookwright/commands/_init_validate.py"
Task: "Add resolution helpers in src/bookwright/commands/_init_resolve.py"
Task: "Add success/error envelopes + records in src/bookwright/commands/_init_envelope.py"
Task: "Add backup ledger primitive in src/bookwright/commands/_init_scaffold.py"
Task: "Add git subprocess wrapper in src/bookwright/commands/_init_git.py"
Task: "Author vocabulary stubs in src/bookwright/resources/vocabularies/{propp,greimas}.ttl"
Task: "Author packaged project templates under src/bookwright/resources/project/"
Task: "Author shared test fixtures in tests/commands/conftest.py"
```

## Parallel Example: User Story 1 Tests

```bash
# Author the three US1 test files together before touching init.py orchestration:
Task: "Tests for default scaffolded tree in tests/commands/test_init_default.py"
Task: "Tests for FR-021a name-rule grid in tests/commands/test_init_validation.py"
Task: "Tests for FR-034 init-options.json envelope in tests/commands/test_init_options_record.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Setup (Phase 1).
2. Foundational (Phase 2) — every helper module + resource + fixture lands.
3. US1 (Phase 3) — `bookwright init mi-libro` works end-to-end with the Claude default and a real git commit.
4. **STOP and VALIDATE**: T015 / T016 / T017 pass; the quickstart § 1 scenario succeeds against a clean tmp directory.
5. The MVP commit is the first real user-facing artifact this iteration ships; iteration 11 (E2E fixtures) consumes it.

### Incremental Delivery

1. Foundational ready → MVP US1 → demo / dogfood.
2. Add US2 (`--here` matrix) → re-run § 2 of quickstart end-to-end → demo.
3. Add US3 (integrations) → re-run § 3 → demo.
4. Add US4 (`--no-git` + git-missing warning) → re-run § 4 → demo.
5. Add US5 (deprecated flags) → re-run quickstart § 6 "Failure modes" rows for `--ai`, `--ai-skills`, `--ai-commands-dir`.
6. Add Polish (rollback grid, JSON-envelope subprocess pin, quality gate) → open the PR.

### Parallel Team Strategy

US1 lands first because every other user story extends `init.run`. Once it is on `main`, US2 / US3 / US4 may be developed concurrently by different contributors — they touch the same file but their test files are independent so the conflict surface is small (the matrix overlap is covered by T033 in Polish). US5 lands last because it depends on the US3 integration flow.

---

## Notes

- `[P]` tasks operate on different files with no incomplete dependencies — safe to parallelize.
- `[Story]` labels (US1..US5) map tasks to the user-story phases in [spec.md](spec.md); they propagate into the test-file names so a future reader can grep `tests/commands/test_init_<story>` to recover the per-story slice.
- Per Constitution Principle VIII, every FR maps to at least one test in `tests/commands/`. The phase numbering above places every FR in a concrete file path; T035 enforces the ≥95 % slice target and ≥80 % global target.
- Per Constitution Principle IX (and contract § 7.5), every `--json` invocation MUST emit exactly one JSON document on stdout. T034 is the subprocess pin that protects this invariant across every documented failure mode.
- Per Constitution Principle V, `init.run` MUST NOT branch on the integration key (no `if key == "claude"` ladder). The skills directory and marker file are owned by the integration class, exercised by T028 and asserted by T027.
- Per spec § FR-030 and SC-005, every documented failure mode MUST leave the target directory byte-for-byte unchanged. T033 is the dirhash-snapshot pin that protects this invariant.
- Stop after T035 and let CI run the full matrix before merging. Coverage thresholds and strictness are CI gates — do not relax them locally.
