# Quality Audit — 001-repo-bootstrap

**Scope:** 32 changed files vs `main`
**Commit range:** `987824f`..`b286bc6`
**Date:** 2026-05-28
**Conventions discovered:**

- `CLAUDE.md` (project-level)
- `.specify/memory/constitution.md` v1.0.0 (10 principles, 3 non-negotiable)
- `specs/001-repo-bootstrap/spec.md` (FR-001 … FR-022)
- `specs/001-repo-bootstrap/plan.md` (Project Structure, forbidden dirs)
- `specs/001-repo-bootstrap/contracts/{version,check}.schema.json`
- `bookwright-design.md` (referenced by plan/research)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 4 |
| **Total** | **5** |

Coverage gate: **PASS** (89.02% over `src/bookwright`, threshold = 80%; gate `--cov-fail-under=80` is active in `pyproject.toml`). Test suite: 7 passed in 0.36s. `ruff check`, `ruff format --check`, and `mypy --strict` all green locally.

The iteration is in unusually good shape. Every binding rule in the constitution, every FR in the spec, every file in `plan.md § Project Structure → Source Code`, and every forbidden directory ban is satisfied. Findings are cleanup nits and one pre-commit hygiene concern — none block merge.

## 2. Conventions Compliance Matrix

Rows grouped by source. Every `MUST` / non-negotiable / "required" rule extracted in A.1 has an explicit verdict. `N/A` indicates the rule's preconditions don't apply at this iteration (e.g. integrations, skill emission).

### Constitution (`.specify/memory/constitution.md`)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact ... MUST be Markdown, TOML, or Turtle (RDF)" (Principle I, NON-NEGOTIABLE) | constitution.md §I | layout / no-binary | PASS | Diff contains only `.md`, `.toml`, `.yaml`, `.py`, `.json` schema, `.txt`-shape LICENSE; no binaries |
| "Implementation language is Python 3.11+" (Principle II) | constitution.md §II | dependency | PASS | [pyproject.toml:8](pyproject.toml#L8) `requires-python = ">=3.11"`; CI matrix runs 3.11 + 3.12 |
| "Toolchain: Typer, Pydantic v2, rdflib, Jinja2, hatchling, uv, ruff, mypy strict" | constitution.md §II | dependency | PASS | All present in [pyproject.toml:20-29](pyproject.toml#L20-L29) and dev group; `uv.lock` committed |
| "Adding an additional runtime dependency requires an amendment" | constitution.md §II | dependency | PASS | Runtime deps in pyproject equal the constitutional set exactly (9 entries, no extras) |
| "Runtime dependencies (minimum set): typer, rich, rdflib, pydantic, tomlkit, jinja2, python-slugify, platformdirs, uuid-utils" | constitution.md §TC | dependency | PASS | All nine present in [pyproject.toml:20-29](pyproject.toml#L20-L29); none extra |
| "Build backend: hatchling. Lockfile: uv.lock committed" | constitution.md §TC | dependency | PASS | `[build-system].build-backend = "hatchling.build"`; `uv.lock` (215 KB) tracked |
| "PyPI package name bookwright-cli" | constitution.md §TC | dependency | PASS | [pyproject.toml:2](pyproject.toml#L2) `name = "bookwright-cli"` |
| "All production code MUST live under src/bookwright/" (Principle III) | constitution.md §III | layout | PASS | All production modules under [src/bookwright/](src/bookwright/) |
| "All automated tests MUST live under tests/" (Principle III) | constitution.md §III | layout | PASS | All tests under [tests/](tests/); none colocated with source |
| "No production module may be imported from outside src/bookwright/" | constitution.md §III | layout | PASS | No imports cross the boundary |
| "Each CLI subcommand MUST live in its own module under src/bookwright/commands/<name>.py" (Principle IV) | constitution.md §IV | plugin-shape | PASS | [commands/version.py](src/bookwright/commands/version.py), [commands/check.py](src/bookwright/commands/check.py) |
| "No source file (production or test) may exceed 500 lines" (Principle IV) | constitution.md §IV | module-size | PASS | Largest file is `check.py` at 73 lines |
| "Monolithic cli.py files that inline subcommand bodies are prohibited" (Principle IV) | constitution.md §IV | plugin-shape | PASS | [cli.py](src/bookwright/cli.py) is 21 lines; only orchestrates registration |
| "SkillsIntegration + INTEGRATION_REGISTRY (Principle V)" | constitution.md §V | plugin-shape | N/A | Integrations are out of scope for iter-1 (lands in iter-3 per plan.md) |
| "Agent Skills Only — No Legacy Commands" (Principle VI, NON-NEGOTIABLE) | constitution.md §VI | directory-ban | PASS | No `.claude/commands/` or `.agents/commands/` in tree; verified via `ls` |
| "agentskills.io standard compliance" (Principle VII) | constitution.md §VII | frontmatter-constraint | N/A | No SKILL.md emitted in this iteration |
| "Tests are mandatory ... CI MUST run pytest, ruff, and mypy strict" (Principle VIII, NON-NEGOTIABLE) | constitution.md §VIII | coverage-threshold | PASS | All four gates in [`.github/workflows/tests.yml`](.github/workflows/tests.yml); 7 tests passing |
| "v0 MUST hold minimum 80% line coverage across src/bookwright/" | constitution.md §VIII | coverage-threshold | PASS | 89.02% measured locally; `--cov-fail-under=80` active in [pyproject.toml:51](pyproject.toml#L51) |
| "Any CLI command ... MUST accept a `--json` flag" (Principle IX) | constitution.md §IX | io-contract | PASS | Both `version` and `check` expose `--json` |
| "When set, emit a single well-formed JSON document on stdout and nothing else" | constitution.md §IX | io-contract | PASS | Subprocess test [tests/test_cli_subprocess.py:33-34](tests/test_cli_subprocess.py#L33-L34) asserts byte-exact stdout and empty stderr |
| "Exit codes MUST be non-zero on error" (Principle IX) | constitution.md §IX | io-contract | PASS | [check.py:73](src/bookwright/commands/check.py#L73) `raise typer.Exit(code=0 if ok else 1)`; tested in `test_check_failure_when_dependency_missing` |
| "Section 16 axioms MUST NOT be reopened" (Principle X) | constitution.md §X | scope-ban | PASS | No edits to `bookwright-design.md` or its §16 in the diff |
| "Preset system → v0.2; GrafeoIndexer → v0.3; multi-integration → v0.4; extension system → v0.5; EPUB/PDF → v1.0 (deferred, do NOT introduce plumbing)" | constitution.md §S&RD | scope-ban | PASS | No symbols, files, or imports tied to deferred features |

### Spec (`specs/001-repo-bootstrap/spec.md`)

| Rule | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Tanto version como check MUST aceptar --json ... stdout MUST be exactly `json.dumps(payload, separators=(',', ':')) + '\n'`" | spec.md FR-009a | io-contract | PASS | [version.py:32](src/bookwright/commands/version.py#L32), [check.py:65](src/bookwright/commands/check.py#L65) emit exactly that form |
| "version --json: claves package_version y golem_schema_version" | spec.md FR-009b | io-contract | PASS | [version.py:27-30](src/bookwright/commands/version.py#L27-L30); contract validated by [version.schema.json](specs/001-repo-bootstrap/contracts/version.schema.json) |
| "check --json: campos `checks` (list with name/status/detail) y `ok` booleano" | spec.md FR-009b | io-contract | PASS | [check.py:59-63](src/bookwright/commands/check.py#L59-L63); schema in [check.schema.json](specs/001-repo-bootstrap/contracts/check.schema.json) |
| "La suite MUST cubrir tanto humano como --json para version y check" | spec.md FR-009c | coverage-threshold | PASS | 4 test files exercise both modes; CliRunner + subprocess paths |
| "matriz Python 3.11 + 3.12 para tests" | spec.md FR-015a | workflow-step | PASS | [tests.yml:15](.github/workflows/tests.yml#L15) `matrix.python-version: ["3.11", "3.12"]` |
| "--cov-fail-under=80 desde día uno sin excepciones" | spec.md FR-020 | coverage-threshold | PASS | [pyproject.toml:51](pyproject.toml#L51) addopts includes `--cov-fail-under=80` |
| "MUST NOT introducir lógica de dominio (manifest, GOLEM, indexer, ...)" | spec.md FR-021 | scope-ban | PASS | No imports of `rdflib`, `pydantic`, `tomlkit`, `jinja2`, `slugify`, `platformdirs`, `uuid_utils` in source — declared in pyproject only |
| "MUST NOT añadir dependencias fuera de las constitucionales" | spec.md FR-022 | dependency | PASS | Runtime deps = constitutional set, no additions |
| "lookup de schema GOLEM lee `src/bookwright/schemas/golem/VERSION`; si no existe, reporta `unknown`" | spec.md FR-006 | io-contract | PASS | [version.py:13-18](src/bookwright/commands/version.py#L13-L18); test confirms `"unknown"` in human and `--json` output |
| "version MUST NOT importar rdflib ni dependencias de dominio" | spec.md FR-006 | scope-ban | PASS | [version.py](src/bookwright/commands/version.py) imports only stdlib + typer + rich |
| "check MUST verificar Python ≥ 3.11 y deps importables" | spec.md FR-007 | io-contract | PASS | [check.py:30-50](src/bookwright/commands/check.py#L30-L50) |
| "exit 0 si pasa, ≠ 0 si falla" | spec.md FR-008 | io-contract | PASS | `typer.Exit(code=0 if ok else 1)` |
| "pre-commit MUST cubrir ruff format + ruff check + check-toml + check-yaml" | spec.md FR-011 | workflow-step | PASS | All four in [`.pre-commit-config.yaml`](.pre-commit-config.yaml) |
| "Lint rule sets E, W, F, I, B, UP, RUF, SIM, PL; line-length 100" | spec.md FR-012 | dependency | PASS | [pyproject.toml:43-46](pyproject.toml#L43-L46) |
| "mypy strict mode" | spec.md FR-013 | dependency | PASS | [pyproject.toml:48-51](pyproject.toml#L48-L51) `strict = true` |
| "CI dispara en push y en PR contra main" | spec.md FR-014 | workflow-step | PASS | [tests.yml:3-6](.github/workflows/tests.yml#L3-L6) |
| "Lockfile MUST commitearse" | spec.md FR-002 | dependency | PASS | `uv.lock` tracked, 215 KB |
| "Entry point MUST llamarse `bookwright`" | spec.md FR-003 | io-contract | PASS | [pyproject.toml:32](pyproject.toml#L32) `[project.scripts].bookwright = "bookwright.cli:app"` |
| "FR-018: dos smoke tests mínimos (import + version vía subprocess)" | spec.md FR-018 | workflow-step | PASS | [tests/test_smoke_import.py](tests/test_smoke_import.py), [tests/test_cli_subprocess.py](tests/test_cli_subprocess.py) |

### Plan (`specs/001-repo-bootstrap/plan.md`)

| Rule | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "src/bookwright/{core,golem,integrations,indexers,validation,io,resources}/ MUST NOT be created" | plan.md §Project Structure | directory-ban | PASS | `find src/bookwright -type d` returns only `commands/` |
| "tests/{integration,e2e,fixtures}/, docs/, scripts/, CHANGELOG.md, CONTRIBUTING.md MUST NOT exist" | plan.md §Project Structure | directory-ban | PASS | None present in repo root or tests/ |
| ".github/workflows/release.yml / docs.yml MUST NOT exist" | plan.md §Project Structure | directory-ban | PASS | Only `tests.yml` present |

### CLAUDE.md (project)

| Rule | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Per-command modules ≤500 lines (Principle IV)" | CLAUDE.md | module-size | PASS | Largest 73 lines |
| "uuid-utils not uuid7" | CLAUDE.md | dependency | PASS | [pyproject.toml:28](pyproject.toml#L28) `"uuid-utils>=0.16"` |

### Workflow trail (A.4) — Spec Kit sequence

CLAUDE.md mandates `/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement`. Reverse walk:

| Step | Artifact expected | Present? | Status |
|---|---|---|---|
| specify | `spec.md` | ✓ ([spec.md](specs/001-repo-bootstrap/spec.md)) | PASS |
| clarify | "Clarifications" section in spec | ✓ ("Session 2026-05-28" with 4 Q&A) | PASS |
| plan | `plan.md` + `research.md` + `data-model.md` + `contracts/` + `quickstart.md` | All five present | PASS |
| tasks | `tasks.md` | ✓ ([tasks.md](specs/001-repo-bootstrap/tasks.md)) | PASS |
| analyze | analysis report or checklist entry | ✓ — `checklists/requirements.md` present; previous audit artifacts cleaned up per commit `ee24fd5` | PASS |
| implement | source code under `src/bookwright/` | ✓ — package skeleton, two commands, tests, CI, pre-commit all landed in commit `e522da5` | PASS |

No broken trail. Every step's artifact exists.

### Track integrity (A.3) — governance directories

| Directory | Files on disk | All committed on branch? | Status |
|---|---|---|---|
| `specs/001-repo-bootstrap/` | 7 .md, 2 schema JSON, 1 checklist | Yes — all 11 appear in `git diff main...HEAD` | OK |
| `.specify/` | constitution, templates, extensions.yml, git-config.yml | Diff has `.specify/extensions.yml`, `.specify/extensions/git/git-config.yml`, `.specify/feature.json` (per-project files); upstream templates inherited from main | OK |
| `.claude/skills/` | 14 speckit skills | Inherited from `main` (no changes on branch) | OK |
| Repo root | `pyproject.toml`, `uv.lock`, `LICENSE`, `README.md`, `CLAUDE.md`, configs | All tracked and in diff | OK |

`git status --porcelain` is clean — no uncommitted governance artifacts.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | D | MEDIUM | [.pre-commit-config.yaml:3](.pre-commit-config.yaml#L3) | `ruff-pre-commit` pinned at `v0.5.7` while pyproject declares `ruff>=0.5` — the hook runs in its own isolated venv and may drift from the CI/local ruff version | Either pin pyproject `ruff` to the same patch range as the hook (`ruff==0.5.7` or `ruff~=0.5.7`), or document that the two versions are intentionally independent and add a periodic bump policy |
| R2 | B | LOW | [src/bookwright/cli.py:15-17](src/bookwright/cli.py#L15-L17) | Empty `@app.callback()` `_root` function with a docstring that duplicates `app.help`; multi-command Typer apps render `--help` correctly without a root callback | Remove the callback; if `--help` output regresses, restore with a clear comment explaining the dependency |
| R3 | B | LOW | [src/bookwright/__main__.py:6-11](src/bookwright/__main__.py#L6-L11) | `def main()` wrapper exists only to be called from the `if __name__ == "__main__":` guard two lines below; one extra hop with no caller | Collapse to `if __name__ == "__main__": app()` |
| R4 | D | LOW | [tests/test_cli_check.py:17](tests/test_cli_check.py#L17) | `assert "OK" in result.stdout` is weak — passes if any single `OK` substring appears (it always will, given the `OK  ` tag column), so it doesn't actually verify per-check rendering | Assert the count of `OK` occurrences equals `len(RUNTIME_MODULES) + 1`, or grep each expected `check["name"]` from the output |
| R5 | D | LOW | (gap, not a file) | No subprocess byte-exact stdout test for `bookwright check --json` — only `version --json` is covered end-to-end. Principle IX byte-exactness for `check` is only proven through `CliRunner` | Mirror [tests/test_cli_subprocess.py](tests/test_cli_subprocess.py) for `check --json`: assert `result.stdout` byte-equals the expected JSON and `result.stderr == ""` |

## 4. Remediation Detail

### R1 — Pre-commit ruff rev drift

- **Where:** [.pre-commit-config.yaml:2-7](.pre-commit-config.yaml#L2-L7) vs [pyproject.toml:38](pyproject.toml#L38)
- **Why it matters:** the pre-commit `ruff` hook runs in an isolated venv at exactly `v0.5.7`, while `uv run ruff …` (used in CI and by quickstart) resolves ruff from `uv.lock`, which floats with `>=0.5`. New ruff releases regularly change which rules `select = ["RUF", ...]` activates. A developer can pass pre-commit but fail CI's `ruff check`, or vice versa. The friction is silent — there's no signal in either output that the versions differ.
- **Suggested change:** pin pyproject's dev dependency to the same rev (`"ruff==0.5.7"` or `"ruff~=0.5.7"`), and regenerate `uv.lock`. Future bumps then happen in one PR that touches both `.pre-commit-config.yaml` and `pyproject.toml`. Alternatively, switch the hook to `local` and have it call `uv run ruff` — then there's exactly one ruff in the project.

### R2 — Empty Typer root callback

- **Where:** [src/bookwright/cli.py:15-17](src/bookwright/cli.py#L15-L17)
- **Why it matters:** the callback is dead structurally: `app = Typer(no_args_is_help=True, help="…")` already renders `bookwright --help` correctly with multiple subcommands. The empty body and duplicate docstring add weight without altering behavior, and contradict CLAUDE.md's "default to writing no comments / no boilerplate".
- **Suggested change:** delete lines 15-17. Verify with `uv run bookwright --help` that the top-level help still renders the description and subcommand list.

### R3 — Redundant `main()` wrapper in `__main__.py`

- **Where:** [src/bookwright/__main__.py:6-11](src/bookwright/__main__.py#L6-L11)
- **Why it matters:** `def main(): app()` only exists to be called by the `if __name__ == "__main__":` guard. The wrapper is not exported, not referenced by `[project.scripts]` (which targets `bookwright.cli:app` directly), and not tested. It's a YAGNI smell flagged in CLAUDE.md ("Don't add features ... beyond what the task requires").
- **Suggested change:** replace lines 3-11 with `from bookwright.cli import app` and `if __name__ == "__main__": app()`.

### R4 — Weak smoke assertion in `test_check_human`

- **Where:** [tests/test_cli_check.py:14-17](tests/test_cli_check.py#L14-L17)
- **Why it matters:** the test passes whenever the substring `OK` appears anywhere — and given the renderer prints `OK  ` as the leading tag, this can't fail meaningfully even if `check.py` regresses to printing only one line and skipping the rest of the loop. It earns coverage but not signal.
- **Suggested change:** add `from bookwright.commands.check import RUNTIME_MODULES` (already imported in the same file for `test_check_json_byte_exact`) and assert `result.stdout.count("OK") >= len(RUNTIME_MODULES) + 1`, or assert each `dependency:<m>` name appears in stdout.

### R5 — Missing subprocess byte-exact test for `check --json`

- **Where:** [tests/test_cli_subprocess.py](tests/test_cli_subprocess.py) (gap)
- **Why it matters:** Principle IX hinges on stdout being byte-exact JSON for any agent-consumed command. `version --json` has a subprocess-level proof; `check --json` only has CliRunner coverage. CliRunner uses `mix_stderr=True` by default, so a regression that leaks rich output to stdout in `--json` mode could in principle slip past `test_check_json_byte_exact`'s `result.stdout == json.dumps(...)` assertion if the byte stream happened to align (the current implementation doesn't leak, but the test isn't a full proof at the entry-point boundary).
- **Suggested change:** add a `test_check_json_subprocess_stdout_pure()` that mirrors `test_version_json_subprocess_stdout_pure`: invoke `[sys.executable, "-m", "bookwright", "check", "--json"]`, assert `result.returncode == 0`, `result.stderr == ""`, and `result.stdout` byte-equals the expected JSON (re-built from `RUNTIME_MODULES` and `sys.version_info`).

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/__init__.py` | 100% | 80% | PASS |
| `src/bookwright/__main__.py` | 0% (5 stmts, 2 branches uncovered) | 80% | Below module gate but not the project gate. Acceptable because the file is exercised by the `test_cli_subprocess` end-to-end (which goes through `python -m bookwright`) but coverage tooling doesn't trace subprocesses by default. Could be raised by configuring `coverage` with `concurrency = ["multiprocessing"]` and a `.coveragerc` parallel block; not required for the 80% project gate. |
| `src/bookwright/cli.py` | 100% | 80% | PASS |
| `src/bookwright/commands/__init__.py` | 100% (empty) | 80% | PASS |
| `src/bookwright/commands/check.py` | 96% (line 34 unhit — the < 3.11 branch) | 80% | PASS — the unhit branch is the "found 3.10.x" failure path, untestable without a different interpreter. |
| `src/bookwright/commands/version.py` | 100% | 80% | PASS |
| **Project total** | **89.02%** | **80%** | **PASS** |

## 6. Inability-to-verify notes

- **Pre-commit hooks** (FR-010 / FR-011) — the configuration file is correct and matches the spec, but the hooks themselves are only exercised by hand per `quickstart.md § Activar pre-commit hooks localmente`. There is no automated test that asserts `pre-commit run --all-files` exits cleanly. Not a finding, just a coverage note; adding a `pre-commit run --all-files` step to CI would close it.
- **`bookwright check` < 5 s wall-clock budget (SC-004)** — not directly asserted by a test; relies on the suite's 0.36 s total runtime as indirect evidence.
- **Entry-point script (`[project.scripts].bookwright = "bookwright.cli:app"`)** — exercised implicitly via `uv run bookwright --help` in the quickstart but not by a subprocess test (the subprocess test uses `python -m bookwright`, which routes through `__main__.py`, not the console script). A regression in the entry-point string would not be caught by the current suite.
