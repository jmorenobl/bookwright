# Quality Audit — 003-integration-architecture

**Scope:** 37 changed paths vs `main` (8 spec docs + 7 production source files + 13 test files + 1 manifest re-rooting + 4 root-level conventions/readme/feature.json edits + 7 commits' worth of refreshes).
**Commit range:** `318d89a..HEAD` (branch tip).
**Date:** 2026-05-29
**Conventions discovered:** `CLAUDE.md`, `CONTRIBUTING.md`, `.specify/memory/constitution.md` (v1.1.0), `README.md`, `specs/003-integration-architecture/plan.md`.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: **PASS** (97.92 % global, threshold = 80 %; integrations layer **100 % per file**). 195 / 195 tests pass; `ruff check`, `ruff format --check`, and `mypy --strict` clean across the project.

**Δ vs previous audit (`df6f655`):** R1–R5 remain closed from prior audits. **R6 and R7 closed in this pass** by the same commit:
- **R6** (CRITICAL): `--skills-dir=`, `--skills-dir .`, `--skills-dir ./`, `--skills-dir ""`, and any other value whose `resolve_skills_dir(...)` collapsed to `Path(".")` slipped past the iteration-3 R4 containment guard and dropped `.bookwright-skills-placeholder` directly at `project_root`. Closed by adding an explicit `target == root` short-circuit before the `is_relative_to(root)` test, surfacing as `MalformedOptionError(rule="resolves_to_project_root", ...)`.
- **R7** (CRITICAL): `parse_options(...)` let `shlex.split(raw, posix=True)` raise a bare `ValueError("No closing quotation")` on unbalanced quotes, violating FR-035's all-errors-are-structured contract that iteration 4's `--json` envelope depends on. Closed by wrapping the `shlex.split` call in a `try/except ValueError` that re-raises as `MalformedOptionError(rule="malformed_shell_syntax", value=raw)`.

Spec deltas: `spec.md` FR-019 rule-id list extended (`malformed_shell_syntax`, `resolves_to_project_root`); `data-model.md § 6.3` `rule` enum extended and `value` semantics clarified to distinguish the three "where does this come from" sources (token, raw input, resolved path).

## 2. Conventions Compliance Matrix

Rules extracted from `.specify/memory/constitution.md` (v1.1.0) + `specs/003-integration-architecture/plan.md` (binding for this iteration). Grouped by source.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … are forbidden." | `.specify/memory/constitution.md:55-61` (Principle I) | layout | PASS | No binary files in diff or working tree (`.coverage`, `coverage.xml` are gitignored). |
| "Python 3.11+. Required toolchain: Typer/Pydantic v2/rdflib/Jinja2/hatchling/uv/ruff/mypy strict." | `.specify/memory/constitution.md:69-75` (Principle II) | dependency | PASS | `pyproject.toml` unchanged on this branch; new integrations code is stdlib-only (`pathlib`, `shlex`, `dataclasses`, `typing`). |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | `.specify/memory/constitution.md:190-193` | dependency | PASS | No new runtime dependency declared in `pyproject.toml`. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`." | `.specify/memory/constitution.md:81-83` (Principle III) | layout | PASS | All new code under `src/bookwright/integrations/`; all new tests under `tests/integrations/`. No cross-leaks. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | `.specify/memory/constitution.md:91-92` (Principle IV) | module-size | N/A | No CLI subcommand added in this iteration. |
| "No source file (production or test) may exceed 500 lines." | `.specify/memory/constitution.md:93-95` (Principle IV) | module-size | PASS | Max integration file: `errors.py` at 154 lines; `base.py` at 105 lines (post-R6 fix); `options.py` at 141 lines (post-R7 fix). Total across 7 files: 613 lines. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. A monolithic `AGENT_CONFIG`-style dispatcher is forbidden." | `.specify/memory/constitution.md:103-108` (Principle V) | plugin-shape | PASS | [src/bookwright/integrations/__init__.py:32](src/bookwright/integrations/__init__.py#L32) declares `INTEGRATION_REGISTRY`; both built-ins subclass `SkillsIntegration`; no `AGENT_CONFIG` dispatcher anywhere. |
| "Bookwright MUST emit Agent Skills (`<skills_dir>/<name>/SKILL.md`) and nothing else. Writing to `.claude/commands/`, `.agents/commands/`, or analogous legacy directories is prohibited." | `.specify/memory/constitution.md:115-119` (Principle VI, NON-NEGOTIABLE) | directory-ban | PASS | Mechanically enforced by [tests/integrations/test_no_legacy_commands.py](tests/integrations/test_no_legacy_commands.py) (AST + literal grep). Test green. |
| "name < 64 characters and exactly matching the parent directory name; description < 1024 characters." | `.specify/memory/constitution.md:127-136` (Principle VII) | frontmatter-constraint | N/A | This iteration emits no `SKILL.md` (FR-034). Constants `SKILL_NAME_MAX_LENGTH = 64` and `SKILL_DESCRIPTION_MAX_LENGTH = 1024` exposed at [src/bookwright/integrations/constants.py:16-17](src/bookwright/integrations/constants.py#L16-L17) for iteration 9. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`." | `.specify/memory/constitution.md:142-149` (Principle VIII, NON-NEGOTIABLE) | coverage-threshold | PASS | 97.92 % global; integrations layer **100 % per-file**. |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a `--json` flag and emit a single JSON document on stdout." | `.specify/memory/constitution.md:155-163` (Principle IX) | io-contract | N/A | No CLI command added in this iteration; structured errors expose `to_dict()` for iteration 4's `init --json`. |
| "This layer MUST NOT write to stdout or stderr. Errors are raised, never printed." | `specs/003-integration-architecture/spec.md` FR-037 | io-contract | PASS | Enforced by [tests/integrations/test_no_stdio.py](tests/integrations/test_no_stdio.py) (AST-walk for `print()`, `sys.stdout`, `sys.stderr`, `from sys import …`). Test green. |
| "All error paths MUST raise structured exceptions; nothing is written to stdout/stderr." | `specs/003-integration-architecture/spec.md` FR-035 + `options.py` parser docstring | io-contract | PASS (post-R7) | `parse_options` now wraps `shlex.split` (the last remaining bare-exception path) in a `try/except` that re-raises as `MalformedOptionError(rule="malformed_shell_syntax")`. Covered by [tests/integrations/test_option_parser.py](tests/integrations/test_option_parser.py) (4 parametric inputs: `"\"unclosed`, `'unclosed`, single-`"`, single-`'`). |
| "Preset system / GrafeoIndexer / multi-integration beyond claude+generic / extension system / pandoc — MUST NOT be pulled into v0 scope." | `.specify/memory/constitution.md:204-218` | scope-ban | PASS | Registry holds exactly `claude`+`generic`. No preset code, no `GrafeoIndexer` imports, no third integration. |
| "DEFAULT_SKILLS_DIR re-rooted from a literal in `core/manifest.py` to a derivation from the integrations registry via late import." | `plan.md:252-261` (iteration-3 structure decision) | workflow-step | PASS | [src/bookwright/core/manifest.py:58-71](src/bookwright/core/manifest.py#L58-L71) (`_default_skills_dir_map`) does the late import; covered by [tests/core/test_build.py:137-142](tests/core/test_build.py#L137-L142). |
| "Each concrete integration lives under `src/bookwright/integrations/<key>/` … base, registry, parser, errors, constants live one level up." | `plan.md:239-249` | layout | PASS | File tree exactly matches the plan: `base.py`, `__init__.py`, `options.py`, `errors.py`, `constants.py` at the layer root; `claude/` and `generic/` as subpackages. |
| "Plugin extensibility is exercised, not just claimed (FakeIntegration smoke test + pinned-file hash assertion)." | `plan.md:268-274` | workflow-step | PASS | [tests/integrations/test_plugin_contract.py:130-146](tests/integrations/test_plugin_contract.py#L130-L146) pins SHA-256 of `base.py`, `claude/__init__.py`, `generic/__init__.py`. `base.py` hash refreshed in this audit's R6 commit after the new `resolves_to_project_root` guard; `claude/` and `generic/` unchanged. |
| "FR-025 + FR-029: the resolved skills directory MUST be project-root-relative AND strictly contained inside `project_root`." | `specs/003-integration-architecture/spec.md` FR-025 + FR-029 | io-contract | PASS (post-R6) | Enforced in [src/bookwright/integrations/base.py:87-97](src/bookwright/integrations/base.py#L87-L97) with two sequential guards: `target == root` (R6, `resolves_to_project_root`) and `not target.is_relative_to(root)` (R4, `escapes_project_root`). Covered by [tests/integrations/test_setup_stub.py](tests/integrations/test_setup_stub.py) (3 escape attempts + 4 collapse attempts: `""`, `"."`, `"./"`, `"foo/.."`). |
| Track integrity — every governance/source artifact described in plan.md MUST be tracked by git on this branch. | derived (A.3, audit-skill rule) | track-integrity | PASS | All 7 source files under `src/bookwright/integrations/` (`git ls-files = 7`), all 13 files under `tests/integrations/` (`git ls-files = 13`), and `specs/003-integration-architecture/tasks.md` are tracked. Closed by commit `7427249`. |
| Workflow trail — every step from `/speckit-specify` through `/speckit-implement` MUST produce its artifact. | `CLAUDE.md:25-50` (Spec Kit sequence) | workflow-step | PASS | `spec.md`, `plan.md`, `tasks.md`, source, tests all present and tracked. The audit/remediation loop (`review.md` → R4 → R5 → R6+R7) is itself an instance of the workflow operating end-to-end. |

## 3. Findings

No open findings.

### Closed since previous audit

| ID | Closed by | How |
|---|---|---|
| R1 — Integration source code untracked (CRITICAL) | `7427249` | `git add src/bookwright/integrations` bundled into iteration-3 commit. |
| R2 — Integration test suite untracked (CRITICAL) | `7427249` | `git add tests/integrations` bundled into iteration-3 commit. |
| R3 — `tasks.md` untracked (CRITICAL) | `7427249` | `git add specs/003-integration-architecture/tasks.md` bundled into iteration-3 commit. |
| R4 — `--skills-dir` not validated for project-root containment (MEDIUM) | `16d1e2f` | `setup()` validates `is_relative_to(project_root.resolve())` and raises `MalformedOptionError(rule="escapes_project_root")` on escape. |
| R5 — `_IntegrationError.to_dict()` base body is dead code (LOW) | `ce048bc` | Body replaced with `raise NotImplementedError(...)` + `# pragma: no cover`. Integrations layer reached 100 % per-file. |
| **R6 — `--skills-dir` values that collapse to `project_root` itself bypass the R4 containment guard (CRITICAL)** | this audit's fix commit | `setup()` now short-circuits with `MalformedOptionError(rule="resolves_to_project_root", value=str(resolved))` when `target == project_root.resolve()` BEFORE the `is_relative_to(root)` test. Covers `""`, `"."`, `"./"`, `"foo/.."`, and any equivalent input. `base.py` SHA-256 in [tests/integrations/test_plugin_contract.py](tests/integrations/test_plugin_contract.py) refreshed; FR-019 rule-id list and `data-model.md § 6.3` rule enum extended. |
| **R7 — `parse_options` leaks bare `ValueError` from `shlex.split` on unbalanced quotes (CRITICAL)** | this audit's fix commit | `shlex.split(raw, posix=True)` wrapped in `try/except ValueError` that re-raises as `MalformedOptionError(rule="malformed_shell_syntax", value=raw)`. Iteration-4's `--json` envelope can now read `.to_dict()` for this failure path. Covered by 4 new parametric tests in [tests/integrations/test_option_parser.py](tests/integrations/test_option_parser.py). `options.py` is not in the pinned-file set, no hash refresh needed. |

## 4. Remediation Detail

### R6 — `resolves_to_project_root` rule

**Root cause.** The R4 fix added `if not target.is_relative_to(root): raise ...escapes_project_root...`. But `target == root` satisfies `is_relative_to` (pathlib treats a path as relative to itself). Any input the user supplies that normalizes to `Path(".")` — `""`, `"."`, `"./"`, `"foo/.."`, etc. — therefore collapses into `project_root` after `(project_root / Path(".")).resolve()`, slips past the R4 guard, no-ops `mkdir(...)`, and writes `.bookwright-skills-placeholder` directly at the project root.

**Fix.** Add an explicit equality short-circuit BEFORE the `is_relative_to` test, with its own rule id so the JSON envelope can distinguish "lands AT root" from "lands OUTSIDE root":

```python
if target == root:
    raise MalformedOptionError(rule="resolves_to_project_root", value=str(resolved))
if not target.is_relative_to(root):
    raise MalformedOptionError(rule="escapes_project_root", value=str(resolved))
```

**Test coverage added.** `test_generic_setup_rejects_skills_dir_that_resolves_to_project_root` parametrized over four collapse forms: `""` → echoes `"."`, `"."` → `"."`, `"./"` → `"."`, `"foo/.."` → `"foo/.."`. Each case additionally asserts that `.bookwright-skills-placeholder` did NOT land at `project_root` and that `.agents/skills` was NOT created either — proves the guard fires before any disk mutation.

**Spec/data-model updates.** `spec.md` FR-019 rule-id list now mentions `resolves_to_project_root`. `data-model.md § 6.3` rule enum extended; `value` semantics clarified that for the two project-root rules it is `str(resolved)` (a `Path`-normalized view), which is why `""` and `"./"` both surface as `"."`.

**Pin refresh.** `base.py` SHA-256 in [tests/integrations/test_plugin_contract.py:43](tests/integrations/test_plugin_contract.py#L43) recomputed from `ffe99b…` (post-R4) → `ab33fc…` (post-R6).

### R7 — `malformed_shell_syntax` rule

**Root cause.** `parse_options(...)` called `shlex.split(raw, posix=True)` with no exception handler. `shlex` raises `ValueError("No closing quotation")` on unbalanced quotes — a bare built-in exception with no `code`/`message`/`to_dict()`. Iteration 4's `init --json` envelope would catch the exception and have nothing structured to serialize, producing either a stack trace or a non-conforming JSON payload.

**Fix.** Wrap the call in `try/except ValueError` and re-raise as a structured error, preserving the original via `from exc`:

```python
try:
    tokens = shlex.split(raw, posix=True)
except ValueError as exc:
    raise MalformedOptionError(rule="malformed_shell_syntax", value=raw) from exc
```

The `value` field carries the entire raw input (not a single flag) so the caller can echo the offending string back. `data-model.md § 6.3` documents this exception to the "value = offending flag" rule.

**Test coverage added.** `test_unbalanced_quotes_raise_structured_malformed_option` parametrized over four shell-syntax violations: `'--skills-dir "unclosed'`, `"--skills-dir 'unclosed"`, bare `"`, bare `'`. Each asserts `payload["code"] == "malformed_option"`, `payload["rule"] == "malformed_shell_syntax"`, and `payload["value"] == raw`.

**No pin refresh needed.** `options.py` is not in the pinned-file set.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/integrations/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/base.py` | 100 % | 80 % | PASS (R6 guard branch covered) |
| `src/bookwright/integrations/claude/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/constants.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/errors.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/generic/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/options.py` | 100 % | 80 % | PASS (R7 except-branch covered) |
| `src/bookwright/core/manifest.py` | 98 % | 80 % | PASS |
| **Global** | **97.92 %** | 80 % | **PASS** |

## 6. Inability-to-verify notes

- None this pass. Both R6 and R7 are exercised by parametric tests that name the exact failure mode they prevent.

## Next Actions

Iteration 3 is finding-free at every severity. The conventions matrix is fully green, the integrations layer is at 100 % per-file coverage, and the workflow trail is intact.

### Bucket — Move on to iteration 4

R1–R7 are all closed. Nothing in this audit blocks the next iteration. Proceed with:

```
/speckit-specify <iteration-4 prompt from bookwright-implementation-plan.md>
```

…which kicks off the `bookwright init` command (M0, depends on iterations 1, 2, 3 — all now on this branch). Iteration 4 will be the first consumer of the integrations layer (`SkillsIntegration.setup()` invoked from `init --skills-dir …`); the structured errors closed by R6 and R7 are the surface its `--json` envelope will rely on.

The checklist `specs/003-integration-architecture/checklists/quality.md` has been refreshed to mark R6 and R7 closed; no items remain open at any severity. Iteration 3 is ready to merge to `main`.
