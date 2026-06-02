# Quality Audit — 009-materialize-skills

**Scope:** 10 changed source files + 16 test files vs `main`
**Commit range:** main..4dc11bb
**Date:** 2026-06-02
**Conventions discovered:** `.specify/memory/constitution.md` (v1.2.0), `CLAUDE.md`, `CONTRIBUTING.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 2 |
| **Total** | 4 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%). Total coverage 97.19%; every changed module ≥ 96% (`materialize.py` 100%, `fs.py` 99%, `lint.py` 96%, `descriptions.py`/`errors.py`/`base.py`/`__init__.py`/`constants.py` 100%). `ruff check`, `mypy --strict`, and `pytest` (757 passed, 1 skipped) all green.

## 2. Conventions Compliance Matrix

Grouped by source file. One row per rule extracted in Pass A.1.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle … embedded databases … forbidden as canonical storage" | `constitution.md:47` | layout | PASS | Diff adds only `.py`/`.md`; frontmatter read via `yaml.safe_load`; no binary store introduced |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | `constitution.md:64` | dependency | PASS | `pyproject.toml` diff adds only a ruff per-file-ignore; `[project].dependencies` unchanged |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:72` | layout | PASS | All new prod files under `src/bookwright/{integrations,io,commands}`; all new tests under `tests/` |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:85` | module-size | PASS | Max prod = `envelope.py` 274; max test = `test_materialize.py` 198 |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`" | `constitution.md:83` | layout | N/A | No new subcommand this iteration; `init` package unchanged in shape |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY` … monolithic dispatcher forbidden" | `constitution.md:94` | plugin-shape | PASS | `setup()` shared on base; registry populated via `_register`; no if/elif over integration keys |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/`, `.agents/commands/` … is prohibited" | `constitution.md:107` | directory-ban | PASS | `materialize.py` writes only `<skills_dir>/<name>/SKILL.md` + `references/`; grep finds no command-dir writes |
| "valid YAML frontmatter; `name` < 64 … matching parent dir; `description` < 1024 … MUST fail loudly … no silent truncation" | `constitution.md:119` | frontmatter-constraint | PASS | `lint_skill_md` enforces all four rules and `raise`s `SkillLintError`; `generate_skill_md` deletes half-written dir on failure |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:135` | coverage-threshold | PASS | 97.19% total; all changed modules ≥ 96% |
| "MUST accept a `--json` flag and … emit a single well-formed JSON document on stdout and nothing else … prose to stderr" | `constitution.md:148` | io-contract | PASS | `envelope.py` writes one compact JSON doc to stdout; warnings/errors to stderr; non-zero exit via `emit_error` |
| "deferred … MUST NOT be pulled into v0 scope (preset, GrafeoIndexer, multi-integration, extension, EPUB)" | `constitution.md:197` | scope-ban | PASS | grep for grafeo/preset/epub/pandoc/vector across diff → none |
| "[design axioms] MUST NOT be reopened in spec, plan, or task discussions" | `constitution.md:159` | other | PASS | No axiom reopened; `.agents/skills/` default + rdflib + Agent-Skills-only all honored |
| "Forbidden in source/tests … `T0xx` — task IDs from tasks.md" | `CONTRIBUTING.md:58` | other | **FAIL** | `base.py:11` docstring contains `(T013)` — see R1 |
| "Allowed: `FR-0xx`/`SC-0xx`/`D-x`/`bookwright-design.md § N.M`; numbers freeze on merge" | `CONTRIBUTING.md:51` | other | PASS | All other inline refs use `FR-0xx`/`SC-0xx`/`R<n>` form |
| Spec Kit workflow trail: spec → plan → tasks → analyze → implement artifacts exist | `CLAUDE.md` | workflow-step | PASS | `spec/plan/tasks/research/data-model/quickstart.md`, `contracts/`, `checklists/requirements.md`, analysis-report commit `a231618` all present |
| Governance / feature-owned dirs must be tracked by git on this branch | `CLAUDE.md` | track-integrity | PASS | `git status` clean; every `specs/009-*` and `src/` file is committed on the branch |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | MEDIUM | src/bookwright/integrations/base.py:11 | Module docstring cites `(T013)`, a `tasks.md` task ID — explicitly forbidden in source by CONTRIBUTING.md:58 | Drop `(T013)`; the sentence stands on its own, or re-anchor to an FR if one applies |
| R2 | B | MEDIUM | src/bookwright/integrations/materialize.py:66 | `assert token not in transformed` is the sole guard for the SC-003 "no residual token" invariant; stripped under `python -O`, with no linter backstop | Replace the `assert` with an explicit `raise SkillMaterializationError(...)` so the fail-loud guarantee survives `-O` |
| R3 | A | LOW | src/bookwright/integrations/__init__.py:139 | Deprecated `SKILL_PLACEHOLDER_MARKER_NAME` is re-exported in the public `__all__` though the constant is documented "do not write in new code" | Keep it importable from `constants` for the legacy test, but drop it from `__init__.__all__` to keep the public surface clean |
| R4 | B | LOW | src/bookwright/integrations/materialize.py:163 | `assert len(description) < SKILL_DESCRIPTION_MAX_LENGTH` duplicates the authoritative assert in `get_description` (descriptions.py:41) and the loud linter Rule 3 | Drop the redundant assert; the cap is already owned by `get_description` and enforced by `lint_skill_md` |

(IDs sorted by severity desc, file asc, line asc.)

## 4. Remediation Detail

### R1 — Forbidden task-ID tag in source

- **Where:** `src/bookwright/integrations/base.py:11`
- **Why it matters:** CONTRIBUTING.md:58 lists `T0xx` task IDs as **forbidden** in source/tests — they are "planning bookkeeping with no durable artifact." Once iteration 9 merges, `tasks.md` numbering is no longer load-bearing, so the `(T013)` pointer goes stale and misleads a future reader navigating back to the *why*. The allowed alternative is an `FR-0xx`/`SC-0xx`/`D-x` ref or no tag.
- **Suggested change:** edit the docstring line ``"`setup()` is implemented once here (T013); no v0 subclass overrides it."`` to drop `(T013)`. If a requirement justifies the single-implementation decision, cite that instead (e.g. `FR-xxx`); otherwise the bare statement is fine.

### R2 — `assert` guards a fail-loud invariant that can be compiled out

- **Where:** `src/bookwright/integrations/materialize.py:61-67` (`_transform_body`)
- **Why it matters:** SC-003 requires that no `{ARGS}`/`{SCRIPT}` token survive the body transform. The check is an `assert`, which Python strips entirely under `-O`. Unlike the description cap (which the linter re-checks with a real `raise`), there is **no** `lint_skill_md` rule for residual template tokens — so under `-O` a malformed source could ship a `{SCRIPT}` token into a `SKILL.md` silently, which runs against the project's pervasive fail-loudly stance (Principle VII spirit). The input is trusted in-repo authoring, so the practical risk is low, but the guard is structurally fragile.
- **Suggested change:** convert the loop body to `raise SkillMaterializationError(skill=..., rule="residual_token", detail=...)` (the error type already exists) so the invariant holds regardless of optimization level.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/integrations/materialize.py | 100% | 80% | PASS |
| src/bookwright/integrations/lint.py | 96% | 80% | PASS |
| src/bookwright/integrations/descriptions.py | 100% | 80% | PASS |
| src/bookwright/integrations/errors.py | 100% | 80% | PASS |
| src/bookwright/integrations/base.py | 100% | 80% | PASS |
| src/bookwright/integrations/constants.py | 100% | 80% | PASS |
| src/bookwright/integrations/__init__.py | 100% | 80% | PASS |
| src/bookwright/io/fs.py | 99% | 80% | PASS |
| src/bookwright/commands/init/scaffold.py | (within init pkg, ≥98% suite) | 80% | PASS |
| src/bookwright/commands/init/envelope.py | (within init pkg, ≥98% suite) | 80% | PASS |

## 6. Inability-to-verify notes

- **TDD ordering (Pass D heuristic):** all iteration-9 source and tests landed in a single commit (`4dc11bb`), so the implementation-vs-test landing-order signal is **N/A** — it cannot confirm or deny test-first development.
- **`python -O` behavior (R2):** the residual-token risk is reasoned about statically; it was not exercised by running the suite under `-O` (the suite runs assertions-enabled, as does CI).
- **Boundary-security (Pass D):** no path-traversal, unsafe-deserialization (`yaml.safe_load` confirmed), shell-injection (`shell=True`/`eval`/`exec`/`pickle` grep clean), or hardcoded-secret findings. Skills-dir containment is validated at the `setup()` entry (`is_relative_to(root)` + `resolves_to_project_root` guard); reference filenames are constrained to `[\w-]+` from packaged sources, not user input.
