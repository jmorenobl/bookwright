---
description: "Task list for iteration 001-repo-bootstrap"
---

# Tasks: Bootstrap inicial del repositorio Bookwright

**Input**: Design documents from `/Users/jorge/Projects/bookwright/specs/001-repo-bootstrap/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md — all present.

**Tests**: Test tasks are INCLUDED. FR-009c explicitly requires the suite to cover both the human-readable and `--json` output for `version` and `check`. FR-018 mandates two smoke tests at minimum.

**Organization**: Tasks are grouped by user story (US1 = P1 onboarding, US2 = P2 CI quality gates, US3 = P3 pre-commit hooks, US4 = P4 `bookwright check`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks).
- **[Story]**: Maps to a user story (`US1`, `US2`, `US3`, `US4`). Setup, Foundational and Polish phases carry no story label.
- File paths are absolute from the repository root (`/Users/jorge/Projects/bookwright`).

## Path Conventions

Single project, src-layout (Constitución Principio III):

- Production code: `src/bookwright/…`
- Tests: `tests/…` at repository root
- CI: `.github/workflows/…`
- Project config: repository root

All paths shown below match exactly `plan.md § Project Structure → Source Code`. Anything outside that tree is out of scope.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bring the empty repo to a state where `uv sync` resolves a deterministic environment from a committed lockfile, with linter/type-checker/test-runner configuration in place but no source code yet.

**Generation policy**: prefer deterministic CLI generators over hand-authoring (`uv init`, `uv add`, `curl` from canonical URLs). Edit only the deltas the generator cannot set. Hand-authoring is reserved for project-specific files with no canonical generator (CI workflows, README, pre-commit config, tool config blocks).

- [ ] T001 Generate the package scaffold deterministically by running, from repo root:
  ```bash
  uv init --package --name bookwright --build-backend hatch --python 3.11 \
    --description "Spec-driven authoring toolkit for novels, essays, and memoirs." \
    --no-readme --vcs none
  ```
  This creates: `pyproject.toml` (PEP 621 skeleton with hatchling backend and an entry point), `src/bookwright/__init__.py` (a `hello()` stub, replaced in T012), `.python-version` (single line `3.11`), `.gitignore` (Python template). `--vcs none` because git is already initialized; `--no-readme` because T010 authors the README intentionally. After the command, create the remaining empty directories `src/bookwright/commands/`, `tests/`, `.github/workflows/` with a `.gitkeep` in each (these will hold real files in later phases but must exist now so the tree matches plan.md § Project Structure).
- [ ] T002 Add the full runtime dependency set (Constitución § Technical Constraints) and dev dependencies deterministically with `uv add` (atomically updates both `pyproject.toml` and `uv.lock`):
  ```bash
  uv add 'typer>=0.12' 'rich>=13.7' 'rdflib>=7.0' 'pydantic>=2.5' \
         'tomlkit>=0.12' 'jinja2>=3.1' 'python-slugify>=8.0' \
         'platformdirs>=4.2' 'uuid-utils>=0.16'

  uv add --dev 'pytest>=8.0' 'pytest-cov>=5.0' 'ruff>=0.5' 'mypy>=1.10' 'pre-commit>=3.7'
  ```
  Do NOT edit `[project].dependencies` or `[dependency-groups].dev` by hand — `uv add` keeps `pyproject.toml` and `uv.lock` in sync; hand-editing risks drift. This task subsumes T011 (lockfile generation): `uv.lock` is produced as a side effect of the first `uv add` and updated atomically on each subsequent invocation.
- [ ] T002b Apply targeted edits to `pyproject.toml` for fields `uv init` / `uv add` cannot set on their own (still a small, surgical set of changes — every other piece of metadata stays generator-produced). Inspect the file produced by T001 first, then:
  1. `[project].name`: change from `"bookwright"` (uv init derived it from the module name) to `"bookwright-cli"` (PyPI distribution name per Constitución § Technical Constraints).
  2. `[project].version` → dynamic: ensure the file has `dynamic = ["version"]` (no literal `version = "..."` line under `[project]`). If `uv init --build-backend hatch` already produced this, leave as-is; if it wrote a literal version, remove that line and add `dynamic = ["version"]`. Hatchling will read `__version__` from `src/bookwright/__init__.py` (configured by T006).
  3. Add `license = "Apache-2.0"` (SPDX string per PEP 639) and `license-files = ["LICENSE"]`. Do NOT use the deprecated `license = { text = "..." }` form. Do NOT add `License :: OSI Approved :: Apache Software License` to classifiers — the SPDX expression supersedes it (research.md R13).
  4. Add `classifiers = ["Development Status :: 3 - Alpha", "Intended Audience :: Developers", "Programming Language :: Python :: 3", "Programming Language :: Python :: 3.11", "Programming Language :: Python :: 3.12", "Operating System :: POSIX", "Operating System :: MacOS"]`.
  5. `[project.scripts].bookwright`: change the value `uv init` wrote (likely `"bookwright:main"` pointing at the `hello()` stub) to `"bookwright.cli:app"` (the Typer app from T015).
- [ ] T003 [P] Add `[tool.ruff]` and `[tool.ruff.lint]` blocks to `pyproject.toml` per research.md R6 (`line-length = 100`, `target-version = "py311"`, `src = ["src", "tests"]`, `select = ["E","W","F","I","B","UP","RUF","SIM","PL"]`).
- [ ] T004 [P] Add `[tool.mypy]` block to `pyproject.toml` per research.md R7 (`strict = true`, `python_version = "3.11"`, `files = ["src", "tests"]`).
- [ ] T005 [P] Add `[tool.pytest.ini_options]` and `[tool.coverage.run]` blocks to `pyproject.toml` per research.md R8 (`testpaths = ["tests"]`, `addopts = "-ra --cov=bookwright --cov-report=term-missing --cov-report=xml --cov-fail-under=80"`, `source = ["src/bookwright"]`, `branch = true`). The `--cov-fail-under=80` activates the Constitución Principio VIII (NON-NEGOTIABLE) coverage gate from day one — the iteration's ~200 LOC surface is trivially covered by T018/T019/T019b/T024.
- [ ] T006 [P] Ensure `[tool.hatch.build]` and `[tool.hatch.version]` blocks in `pyproject.toml` match research.md R2: `[tool.hatch.build].include = ["src/bookwright"]` and `[tool.hatch.version].path = "src/bookwright/__init__.py"`. `uv init --build-backend hatch` may have created these blocks with different defaults — overwrite/add as needed so the values are exactly the ones above.
- [ ] T007 [P] Verify `.python-version` (created by `uv init --python 3.11` in T001) contains the single line `3.11`. No edit needed unless the file is missing.
- [ ] T008 [P] Extend the `.gitignore` created by `uv init` in T001 to also cover: `htmlcov/`, `coverage.xml`, `.coverage`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, and `.scratch/` (a scratch directory used by `quickstart.md` to exercise pre-commit hooks without mutating tracked files). The uv-init template already covers `.venv/`, `__pycache__/`, `*.pyc`, `dist/`, `*.egg-info/`; do not duplicate those.
- [ ] T009 [P] Fetch the canonical Apache-2.0 text deterministically: `curl -fsSL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE` (run from repo root). This guarantees the bit-exact official text without manual copy-paste.
- [ ] T010 [P] Create initial `README.md` at repo root with sections: project tagline, install via `uv` (link to https://docs.astral.sh/uv/), `uv sync`, `uv run bookwright --help`. (Detailed pre-commit/quickstart content lands in the Polish phase.)
- [ ] T011 Verify the lockfile is consistent with `pyproject.toml` after all Phase 1 edits: `uv lock --check` (exits non-zero if the lockfile drifted from the manifest, e.g. because T003–T006 inadvertently changed something the resolver cares about). `uv.lock` itself was already generated by the first `uv add` in T002; this task is the consistency gate, not a regeneration step.

**Checkpoint**: `uv sync --frozen` resolves the environment offline (using cached wheels) or online without re-resolving. No Python code exists yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Author the Python package skeleton (`__version__`, Typer app entrypoint, empty command registry, test harness scaffolding) that every user story will hang code off. After this phase, `python -m bookwright --help` exits cleanly even though no subcommands are registered yet.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T012 Replace the contents of `src/bookwright/__init__.py` (a `hello()` stub created by `uv init` in T001) with a module docstring and the single source-of-truth line `__version__ = "0.0.1"` (data-model.md E1, research.md R11). Hatchling reads this at build-time. The file MUST NOT export the `hello()` function any more — T002b already retargeted `[project.scripts].bookwright` away from it.
- [ ] T013 [P] Create `src/bookwright/__main__.py` that imports `app` from `bookwright.cli` and invokes `app()` when executed as a module.
- [ ] T014 [P] Create `src/bookwright/commands/__init__.py` (empty package marker).
- [ ] T015 Create `src/bookwright/cli.py` with a `typer.Typer(name="bookwright", help="Bookwright — Spec-driven authoring toolkit.", no_args_is_help=True, add_completion=False)` instance bound to module-level `app`, per research.md R3. No subcommand registrations yet — those are added by US1 and US4.
- [ ] T016 [P] Create `tests/__init__.py` (empty package marker).
- [ ] T017 [P] Create `tests/conftest.py` with a `runner` fixture returning `typer.testing.CliRunner()` and any path helpers shared across the smoke tests.

**Checkpoint**: `uv run python -c "from bookwright.cli import app; app(['--help'], standalone_mode=False)"` exits 0 and prints the bare-bones Typer help. The full quality gate (`uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`) passes on an empty test suite.

---

## Phase 3: User Story 1 — Onboarding sin fricción (Priority: P1) 🎯 MVP

**Goal**: From a clean clone, a developer with Python 3.11+ and `uv` installed can run `uv sync`, then `uv run bookwright --help` and `uv run bookwright version` (both human and `--json` modes) and get sensible output in under 60 s end-to-end. Covers FR-001 through FR-006, FR-009a, FR-009b (version slice), FR-009c (version slice), and FR-018 (smoke import + version subprocess).

**Independent Test**: On a fresh checkout, `uv sync` succeeds; `uv run bookwright --help` lists `version`; `uv run bookwright version` prints the package version and `unknown` for the GOLEM schema; `uv run bookwright version --json` emits exactly `{"package_version":"0.0.1","golem_schema_version":"unknown"}` on stdout with empty (or stderr-only) noise.

### Tests for User Story 1 (FR-009c, FR-018, Principio IX)

- [ ] T018 [P] [US1] Write `tests/test_smoke_import.py` — imports `bookwright`, asserts `bookwright.__version__` is a non-empty string matching a semver-ish pattern (FR-018 smoke test #1).
- [ ] T019 [P] [US1] Write `tests/test_cli_version.py` — uses the `runner` fixture (Typer `CliRunner`) to invoke `bookwright version` and assert (a) exit code 0, (b) stdout in human mode contains the package version and the literal `unknown`. Then invoke `bookwright version --json` and assert (a) exit code 0, (b) stdout is **exactly** `json.dumps({"package_version": bookwright.__version__, "golem_schema_version": "unknown"}, separators=(",", ":")) + "\n"` (byte-level equality, not `json.loads(...)` — the byte-equality assertion is the load-bearing test for Principio IX per FR-009a, and catches any extra whitespace, ANSI escapes, or trailing prose). Covers FR-009c for `version`.
- [ ] T019b [P] [US1] Write `tests/test_cli_subprocess.py` — invoke the CLI as a real subprocess to exercise the `[project.scripts].bookwright` entry point and `__main__.py` wiring (which `CliRunner` does NOT cover): `result = subprocess.run([sys.executable, "-m", "bookwright", "version", "--json"], capture_output=True, text=True, check=False)`. Assert: (a) `result.returncode == 0`; (b) `result.stdout` equals exactly the byte sequence `json.dumps({"package_version": bookwright.__version__, "golem_schema_version": "unknown"}, separators=(",", ":")) + "\n"`; (c) `result.stderr == ""` for the clean case. This is the only test that proves end-to-end that an external agent invoking `bookwright` sees a pure-JSON stdout — required by Principio IX. Also covers FR-018's "subproceso o equivalente" clause with the real subprocess form.

### Implementation for User Story 1

- [ ] T020 [US1] Implement `src/bookwright/commands/version.py` with a `run(json_output: bool = typer.Option(False, "--json", help="Emit a single JSON document on stdout."))` callback. Read `__version__` directly via `from bookwright import __version__` (research.md R11). For the GOLEM schema, use `importlib.resources.files("bookwright").joinpath("schemas/golem/VERSION")` with a `try/except (FileNotFoundError, ModuleNotFoundError)` (and the missing-resource case) returning the literal `"unknown"` (FR-006, research.md R5). In human mode print via `rich.console.Console()` to stdout; in `--json` mode emit `json.dumps({"package_version": ..., "golem_schema_version": ...}, separators=(",", ":"))` followed by a single newline to stdout and nothing else (research.md R4). MUST NOT import `rdflib` or any domain dependency.
- [ ] T021 [US1] Register the `version` subcommand in `src/bookwright/cli.py`: add `from bookwright.commands import version` and `app.command("version")(version.run)` immediately after the `Typer` instantiation from T015.

**Checkpoint**: US1 acceptance scenarios 1–3 (spec.md) pass end-to-end. `uv run pytest tests/test_smoke_import.py tests/test_cli_version.py tests/test_cli_subprocess.py` is green. `uv run bookwright --help` lists `version`. This is the MVP cut.

---

## Phase 4: User Story 2 — Quality gates en CI (Priority: P2)

**Goal**: Every push (any branch) and every PR against `main` triggers a CI pipeline that runs the test suite on Python 3.11 + 3.12 and lint + format check + `mypy --strict` on 3.12, with `uv sync --frozen` and a 10-minute timeout. Covers FR-014 through FR-017 and FR-020 (coverage XML artifact).

**Independent Test**: Push the branch to GitHub; the `quality` job appears in Actions, runs both matrix cells, and either turns green (clean code) or red with actionable logs (planted failure). The `coverage-3.12` artifact is downloadable.

### Implementation for User Story 2

- [ ] T022 [US2] Create `.github/workflows/tests.yml` exactly per research.md R9 and data-model.md E5: `on: push: {} / pull_request: { branches: [main] }`; single `quality` job, `runs-on: ubuntu-latest`, `timeout-minutes: 10`, `strategy.fail-fast: false`, `matrix.python-version: ["3.11", "3.12"]`; steps in order — checkout (`actions/checkout@v4`), `astral-sh/setup-uv@v3` with `enable-cache: true`, `uv python install ${{ matrix.python-version }}`, `uv sync --frozen`, then guarded by `if: matrix.python-version == '3.12'` the steps `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`; always-run `uv run pytest`; finally `actions/upload-artifact@v4` with `name: coverage-${{ matrix.python-version }}`, `path: coverage.xml`, also guarded by `if: matrix.python-version == '3.12'`.

**Checkpoint**: US2 acceptance scenarios 1–4 pass. The first push to the feature branch triggers the workflow and runs green on the code shipped by US1 + foundational phases.

---

## Phase 5: User Story 3 — Higiene local con pre-commit (Priority: P3)

**Goal**: `uv run pre-commit install` activates four hooks (`ruff-format`, `ruff` with `--fix --exit-non-zero-on-fix`, `check-toml`, `check-yaml`) that gate every local `git commit`. Covers FR-010, FR-011, FR-012 (lint rule selection lives in `pyproject.toml`, already done in Phase 1).

**Independent Test**: After `uv run pre-commit install`, attempting to commit a malformed `pyproject.toml` is rejected by `check-toml` with a line/reason; committing a Python file with non-canonical formatting triggers `ruff-format` to rewrite it and abort the commit so the dev re-stages.

### Implementation for User Story 3

- [ ] T023 [US3] Create `.pre-commit-config.yaml` at repo root exactly per research.md R10 and data-model.md E4: two `repos` entries — (1) `https://github.com/astral-sh/ruff-pre-commit` at `rev: v0.5.7` with hooks `ruff-format` and `ruff` (the latter with `args: [--fix, --exit-non-zero-on-fix]`); (2) `https://github.com/pre-commit/pre-commit-hooks` at `rev: v4.6.0` with hooks `check-toml` and `check-yaml`.

**Checkpoint**: US3 acceptance scenarios 1–4 pass when validated by hand using the recipes in `quickstart.md § Activar pre-commit hooks localmente`.

---

## Phase 6: User Story 4 — `bookwright check` (Priority: P4)

**Goal**: `bookwright check` (human + `--json`) verifies that the running interpreter is ≥ 3.11 and that every declared runtime dependency is importable, exits 0 on full pass and ≠ 0 on any failure, and completes in < 5 s. Covers FR-007, FR-008, FR-009, FR-009a (check slice), FR-009b (check slice), FR-009c (check slice).

**Independent Test**: With a valid environment, `uv run bookwright check` prints `OK` per check and exits 0; `uv run bookwright check --json` emits a JSON document matching `contracts/check.schema.json` with `ok: true`. Forcing a missing dependency (rename a module in `.venv`) makes the corresponding `dependency:<name>` check report `fail` and the process exit non-zero.

### Tests for User Story 4 (FR-009c)

- [ ] T024 [US4] Write `tests/test_cli_check.py` — import the constant `from bookwright.commands.check import RUNTIME_MODULES` (exposed by T025). Invoke `bookwright check` via the `runner` fixture and assert (a) exit code 0 in the test environment, (b) stdout in human mode contains `OK` lines for each check. Then invoke `bookwright check --json` and assert: (a) exit code 0; (b) `parsed = json.loads(result.stdout)` yields a dict with `parsed["ok"] is True`; (c) exactly one `python_version` check is present (`sum(1 for c in parsed["checks"] if c["name"] == "python_version") == 1`); (d) the dependency check set is **exactly** `{f"dependency:{m}" for m in RUNTIME_MODULES}` — derived from the imported constant so any drift between `RUNTIME_MODULES` and the test fails loudly; (e) `result.stdout == json.dumps(parsed, separators=(",", ":")) + "\n"` (byte-equality of stdout via re-serialization — proves no extra whitespace, ANSI escapes, or trailing prose, per Principio IX). Also include a unit-level test that monkeypatches `importlib.import_module` to raise `ImportError` for one declared module and asserts that the corresponding `dependency:<name>` check yields `status: "fail"` with non-empty `detail`, the aggregate `ok` becomes `False`, and the exit code is 1.

### Implementation for User Story 4

- [ ] T025 [US4] Implement `src/bookwright/commands/check.py` per research.md R12 and data-model.md P2. Expose the declared runtime modules as a module-level public constant `RUNTIME_MODULES: tuple[str, ...] = ("typer", "rich", "rdflib", "pydantic", "tomlkit", "jinja2", "slugify", "platformdirs", "uuid_utils")` (importable by tests — this is the single source of truth for the import-probe set; T024 imports it and asserts the runtime checks match exactly, so the constant is guarded by its test). Do NOT inline the literal inside `run()`. Then implement `run(json_output: bool = typer.Option(False, "--json"))` that (a) builds a list of `CheckResult`-shaped dicts starting with the `python_version` check (`sys.version_info >= (3, 11)`, `detail` always set to `f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"` on OK, `f"found X.Y.Z, requires >=3.11"` on fail), then iterates over `RUNTIME_MODULES` and appends `{"name": f"dependency:{m}", "status": "ok"}` on success or `{"name": ..., "status": "fail", "detail": str(exc)}` on `ImportError`; (b) computes `ok = all(c["status"] == "ok" for c in checks)`; (c) in `--json` mode emits `json.dumps({"ok": ok, "checks": checks}, separators=(",", ":"))` + newline to stdout and nothing else; (d) in human mode prints a `rich` table or list with one OK/FAIL line per check; (e) raises `typer.Exit(code=0 if ok else 1)`.
- [ ] T026 [US4] Register the `check` subcommand in `src/bookwright/cli.py`: add `from bookwright.commands import check` and `app.command("check")(check.run)`. This is a small edit to the same file modified in T021 — sequential, not parallel.

**Checkpoint**: US4 acceptance scenarios 1–3 pass. `uv run bookwright check` returns in < 5 s (SC-004). Full suite `uv run pytest` still under 10 s (SC-005).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Close out the iteration by fleshing out the README, validating the quickstart end-to-end, and confirming the repo tree matches the plan exactly. Nothing here adds new functionality.

- [ ] T027 [P] Flesh out `README.md` at repo root: add sections covering local quality gates (`uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`), `uv run pre-commit install` activation (US3, SC-007), the offline failure mode of `uv sync` (Edge Case in spec), and a link to `specs/001-repo-bootstrap/quickstart.md` for the canonical onboarding walkthrough.
- [ ] T028 Execute the full quality gate locally and confirm cero issues: `uv sync --frozen && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`. Fix any drift before declaring done.
- [ ] T029 Walk through `specs/001-repo-bootstrap/quickstart.md § Definición de "done"` checklist by hand and tick every box; record any deviation as a bug to fix before merge.
- [ ] T030 Compare the resulting working tree against `plan.md § Project Structure → Source Code` and confirm bit-for-bit equivalence: no extra directories under `src/bookwright/` (no `core/`, `golem/`, `integrations/`, `indexers/`, `validation/`, `io/`, `resources/`), no extra tests subdirectories, no `docs/`, `scripts/`, `CHANGELOG.md`, `CONTRIBUTING.md`, no `release.yml` / `docs.yml`. FR-021 + FR-022 enforcement.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately. T002 (`uv add`) depends on T001 (`uv init`) having produced `pyproject.toml`. T002b depends on T002. T003–T006 depend on T002b (they edit the same file). T011 (`uv lock --check`) depends on all preceding Phase 1 tasks since it gates lockfile consistency after every edit.
- **Phase 2 (Foundational)**: Depends on Phase 1 — needs `pyproject.toml` to resolve `typer` so `cli.py` can `import typer`. BLOCKS all user stories.
- **Phase 3 (US1)**: Depends on Phase 2. Delivers the MVP.
- **Phase 4 (US2)**: Depends on Phase 2 for tests to exist and on US1 for them to be non-empty. The workflow file itself can be authored after Phase 2, but the workflow stays meaningful only once US1 has shipped at least the smoke tests.
- **Phase 5 (US3)**: Depends on Phase 1 (needs `pyproject.toml` to define ruff config that the pre-commit hooks honor). Independent of US1/US2/US4 in terms of code reach.
- **Phase 6 (US4)**: Depends on Phase 2 for the Typer app, on US1's T021 only because both edit `cli.py` — sequential, not blocking.
- **Phase 7 (Polish)**: Depends on Phases 1–6 being complete.

### User Story Dependencies

- **US1 (P1)**: After Foundational. No dependency on any other story. **MVP.**
- **US2 (P2)**: After Foundational. Logically depends on US1 to have produced tests, but the YAML file itself is authorable in isolation.
- **US3 (P3)**: After Setup (Phase 1) — the lint config lives in `pyproject.toml`. Story is fully independent of US1, US2, US4.
- **US4 (P4)**: After Foundational. Shares `cli.py` editing with US1 (T021 then T026 sequentially); otherwise independent.

### Within Each User Story

- Tests are authored alongside the implementation, not strictly before. They are validated against the implementation in the same task chunk. (The constitution does not mandate TDD ordering; FR-009c only mandates coverage existence.)
- `cli.py` modifications (T021, T026) are sequential because they touch the same file.

### Parallel Opportunities

- T002b / T003 / T004 / T005 / T006 — all edit disjoint top-level tables in `pyproject.toml` and are textually independent, but they all touch the same file, so they are parallel in planning but serialize on edit. Treat as a single sequential batch by one dev.
- T007 / T008 / T009 / T010 — disjoint files, fully parallel.
- T013 / T014 / T016 / T017 — disjoint files inside Phase 2, fully parallel.
- T018 / T019 / T019b inside US1 — disjoint test files, fully parallel.
- T027 (Polish README) is parallel with T028 (gate) only if you trust the gate to complete first; safer to serialize.

---

## Parallel Example: Phase 1 Setup

```bash
# After T001 (uv init) + T002 (uv add) + T002b (pyproject edits) land, these can run in parallel:
Task: "Verify .python-version is '3.11' (created by uv init)"                                  # T007
Task: "Extend uv-init .gitignore with htmlcov/, coverage.xml, .pytest_cache, .scratch/, etc."  # T008
Task: "Fetch canonical LICENSE: curl -fsSL https://www.apache.org/licenses/LICENSE-2.0.txt"     # T009
Task: "Create initial README.md with install + uv sync + bookwright --help"                    # T010
```

## Parallel Example: User Story 1

```bash
# After T015 (cli.py skeleton) lands, the three test files are disjoint:
Task: "Write tests/test_smoke_import.py asserting bookwright.__version__ is set"
Task: "Write tests/test_cli_version.py covering human and --json modes (byte-exact stdout)"
Task: "Write tests/test_cli_subprocess.py exercising the entry point via subprocess.run"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (`pyproject.toml` + `uv.lock` + scaffolding files).
2. Complete Phase 2: Foundational (package skeleton + empty Typer app + test fixtures).
3. Complete Phase 3: US1 (`version` command + smoke tests).
4. **STOP and VALIDATE**: walk through US1 acceptance scenarios in `spec.md`; run `uv run pytest tests/test_cli_version.py tests/test_smoke_import.py`. If green, the MVP is shipped.

### Incremental Delivery

1. Setup + Foundational → repo can be cloned and Python package imports.
2. Add US1 → `bookwright version` works (MVP).
3. Add US2 → CI gates every push/PR.
4. Add US3 → pre-commit hooks gate local commits.
5. Add US4 → `bookwright check` returns environment verdict.
6. Polish → README + quickstart validation + tree audit.
7. Merge to `main`.

### Suggested MVP Scope

**User Story 1 only** (Phase 1 + Phase 2 + Phase 3). Delivers a working `bookwright version` invocable from a clean clone in under 60 s. Iterations 2+ in the implementation plan can layer on top.

---

## Notes

- `[P]` tasks = different files, no dependencies on incomplete tasks.
- `[Story]` label maps each task to its user story for traceability.
- All file paths are concrete and absolute from repo root; no placeholders.
- Spec/plan/research/data-model/contracts/quickstart are all in the feature dir and were used as source-of-truth for every task above.
- FR-021 / FR-022: avoid scope creep. If a task tempts you to create files outside `plan.md § Project Structure → Source Code`, stop and reject.
