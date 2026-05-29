# Quality Audit — 003-integration-architecture

**Scope:** 37 changed paths vs `main` (8 spec docs + 7 production source files + 13 test files + 1 manifest re-rooting + 4 root-level convention / README / `.specify/feature.json` edits).
**Commit range:** `0944b08..13d5315` (branch tip).
**Date:** 2026-05-29
**Conventions discovered:** `CLAUDE.md`, `CONTRIBUTING.md`, `.specify/memory/constitution.md` (v1.1.0), `specs/003-integration-architecture/plan.md`, `specs/003-integration-architecture/spec.md` (binding FR list).

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: **PASS** (97.92 % global; integrations layer **100 % per file**, threshold = 80 %). 195 / 195 tests pass; `ruff check`, `ruff format --check`, and `mypy --strict` are clean across the whole project.

**Δ vs previous audit (`13d5315`):** the prior audit (also `13d5315`) closed R6 and R7 on top of the R1–R5 closures from earlier passes. This re-audit re-runs every passes A–D check against the same commit and confirms the conventions matrix is still fully green; no drift, no new findings, no inability-to-verify notes. The audit-skill spec lets the report be re-written so subsequent diffs of `review.md` carry the verification date forward without losing history (closure table preserved below).

## 2. Conventions Compliance Matrix

Rules extracted from `.specify/memory/constitution.md` (v1.1.0), `specs/003-integration-architecture/plan.md`, and the iteration-3 spec's binding FR list. Grouped by source.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … are forbidden." | `.specify/memory/constitution.md:55-61` (Principle I) | layout | PASS | No binary files in diff or working tree (`.coverage`, `coverage.xml` are gitignored; pyproject.toml is text). |
| "Python 3.11+. Required toolchain: Typer / Pydantic v2 / rdflib / Jinja2 / hatchling / uv / ruff / mypy strict." | `.specify/memory/constitution.md:69-75` (Principle II) | dependency | PASS | `git diff main...HEAD -- pyproject.toml` is empty — no toolchain or runtime-dependency mutation. Integrations code is stdlib-only (`pathlib`, `shlex`, `dataclasses`, `typing`). |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | `.specify/memory/constitution.md:190-193` | dependency | PASS | No new runtime dependency declared. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`." | `.specify/memory/constitution.md:81-83` (Principle III) | layout | PASS | All new code under [src/bookwright/integrations/](src/bookwright/integrations/); all new tests under [tests/integrations/](tests/integrations/). No cross-leaks. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | `.specify/memory/constitution.md:91-92` (Principle IV) | module-size | N/A | No CLI subcommand added in this iteration (`bookwright init` lands in iteration 4). |
| "No source file (production or test) may exceed 500 lines." | `.specify/memory/constitution.md:93-95` (Principle IV) | module-size | PASS | Max integration source file: [src/bookwright/integrations/errors.py](src/bookwright/integrations/errors.py) at **154 lines**; [src/bookwright/integrations/options.py](src/bookwright/integrations/options.py) at 141; [src/bookwright/integrations/__init__.py](src/bookwright/integrations/__init__.py) at 111; [src/bookwright/integrations/base.py](src/bookwright/integrations/base.py) at 105. Max test file: [tests/integrations/test_setup_stub.py](tests/integrations/test_setup_stub.py) at **238**. All well under 500. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. A monolithic `AGENT_CONFIG`-style dispatcher is forbidden." | `.specify/memory/constitution.md:103-108` (Principle V) | plugin-shape | PASS | [src/bookwright/integrations/__init__.py:32](src/bookwright/integrations/__init__.py#L32) declares `INTEGRATION_REGISTRY`; both built-ins subclass `SkillsIntegration` ([src/bookwright/integrations/claude/__init__.py:10](src/bookwright/integrations/claude/__init__.py#L10), [src/bookwright/integrations/generic/__init__.py:13](src/bookwright/integrations/generic/__init__.py#L13)); no `AGENT_CONFIG` dispatcher anywhere in the diff. |
| "Bookwright MUST emit Agent Skills (`<skills_dir>/<name>/SKILL.md`) and nothing else. Writing to `.claude/commands/`, `.agents/commands/`, or analogous legacy directories is prohibited." | `.specify/memory/constitution.md:115-119` (Principle VI, NON-NEGOTIABLE) | directory-ban | PASS | Mechanically enforced by [tests/integrations/test_no_legacy_commands.py](tests/integrations/test_no_legacy_commands.py) — three AST guards (legacy class names, `*commands/*` literals, `Path(... "commands" ...)` joins). Test green. |
| "name < 64 characters and exactly matching the parent directory name; description < 1024 characters." | `.specify/memory/constitution.md:127-136` (Principle VII) | frontmatter-constraint | N/A | This iteration emits no `SKILL.md` (FR-034). Constants `SKILL_NAME_MAX_LENGTH = 64` and `SKILL_DESCRIPTION_MAX_LENGTH = 1024` are exposed at [src/bookwright/integrations/constants.py:16-17](src/bookwright/integrations/constants.py#L16-L17) for iteration 9. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`." | `.specify/memory/constitution.md:142-149` (Principle VIII, NON-NEGOTIABLE) | coverage-threshold | PASS | 97.92 % global; integrations layer **100 % per file** (see § 5). |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a `--json` flag and emit a single JSON document on stdout." | `.specify/memory/constitution.md:155-163` (Principle IX) | io-contract | N/A | No CLI command added in this iteration. Structured errors expose `to_dict()` ([src/bookwright/integrations/errors.py:33-36](src/bookwright/integrations/errors.py#L33-L36)) for iteration 4's `init --json`. |
| "This layer MUST NOT write to stdout or stderr. Errors are raised, never printed." | `specs/003-integration-architecture/spec.md` FR-037 | io-contract | PASS | Enforced by [tests/integrations/test_no_stdio.py](tests/integrations/test_no_stdio.py) (AST walk for `print()`, `sys.stdout`, `sys.stderr`, `from sys import …`). Test green. |
| "All errors raised by this layer … MUST be structured exception types carrying a stable string `code`, `message`, `value`, and `valid` where applicable." | `specs/003-integration-architecture/spec.md` FR-035 | io-contract | PASS | Five structured errors in [src/bookwright/integrations/errors.py](src/bookwright/integrations/errors.py); JSON round-trip pinned by [tests/integrations/test_errors_json.py](tests/integrations/test_errors_json.py) (SC-008). `shlex.split` is the last bare-exception path and is wrapped by R7's `try/except ValueError → MalformedOptionError(rule="malformed_shell_syntax")` ([src/bookwright/integrations/options.py:83-90](src/bookwright/integrations/options.py#L83-L90)). |
| "Preset system / GrafeoIndexer / multi-integration beyond claude+generic / extension system / pandoc — MUST NOT be pulled into v0 scope." | `.specify/memory/constitution.md:204-218` | scope-ban | PASS | Registry holds exactly `claude` + `generic` ([src/bookwright/integrations/__init__.py:62-73](src/bookwright/integrations/__init__.py#L62-L73)). No preset code, no `GrafeoIndexer` imports, no third integration. |
| "DEFAULT_SKILLS_DIR re-rooted from a literal in `core/manifest.py` to a derivation from the integrations registry via late import." | `plan.md:252-261` (iteration-3 structure decision) | workflow-step | PASS | [src/bookwright/core/manifest.py:58-71](src/bookwright/core/manifest.py#L58-L71) (`_default_skills_dir_map`) does the late import; consumed by `_build_manifest` (commit `7427249`). Iteration-2 round-trip tests under [tests/core/](tests/core/) still green. |
| "Each concrete integration lives under `src/bookwright/integrations/<key>/` … base, registry, parser, errors, constants live one level up." | `plan.md:239-249` | layout | PASS | File tree exactly matches the plan: `base.py`, `__init__.py`, `options.py`, `errors.py`, `constants.py` at the layer root; `claude/`, `generic/` as subpackages. |
| "Plugin extensibility is exercised, not just claimed (FakeIntegration smoke test + pinned-file hash assertion)." | `plan.md:268-274` | workflow-step | PASS | [tests/integrations/test_plugin_contract.py:41-47](tests/integrations/test_plugin_contract.py#L41-L47) pins SHA-256 of `base.py`, `claude/__init__.py`, `generic/__init__.py`; recomputed locally — all three match. |
| "FR-025 + FR-029: the resolved skills directory MUST be project-root-relative AND strictly contained inside `project_root`." | `specs/003-integration-architecture/spec.md` FR-025 + FR-029 | io-contract | PASS | Enforced in [src/bookwright/integrations/base.py:87-97](src/bookwright/integrations/base.py#L87-L97) with two sequential guards: `target == root` (R6, `resolves_to_project_root`) BEFORE `not target.is_relative_to(root)` (R4, `escapes_project_root`). Both rules covered by [tests/integrations/test_setup_stub.py](tests/integrations/test_setup_stub.py) (3 escape attempts + 4 collapse attempts). |
| Track integrity — every governance / source artifact described in `plan.md` MUST be tracked by git on this branch. | derived (Pass A.3) | track-integrity | PASS | `git ls-files src/bookwright/integrations tests/integrations specs/003-integration-architecture \| wc -l = 30`; `git ls-files --others --exclude-standard` over the same paths returns nothing. Working-tree status clean. |
| Workflow trail — every step from `/speckit-specify` through `/speckit-implement` MUST produce its artifact. | `CLAUDE.md:25-50` (Spec Kit sequence) | workflow-step | PASS | `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/integrations_api.md`, `quickstart.md`, `tasks.md`, source, tests all present and tracked. `/speckit-clarify` step recorded a "no clarifications needed" verdict in [specs/003-integration-architecture/checklists/requirements.md:49-51](specs/003-integration-architecture/checklists/requirements.md#L49-L51). The audit / remediation loop (`review.md` → R4 → R5 → R6+R7) is itself an instance of the workflow operating end-to-end. |

## 3. Findings

No open findings at any severity.

### Closed in prior passes (preserved for traceability)

| ID | Severity at open | Closed by | How |
|---|---|---|---|
| R1 — Integration source code untracked | CRITICAL | `7427249` | `git add src/bookwright/integrations` bundled into iteration-3 commit. |
| R2 — Integration test suite untracked | CRITICAL | `7427249` | `git add tests/integrations` bundled into iteration-3 commit. |
| R3 — `tasks.md` untracked | CRITICAL | `7427249` | `git add specs/003-integration-architecture/tasks.md` bundled into iteration-3 commit. |
| R4 — `--skills-dir` not validated for project-root containment | MEDIUM (upgraded HIGH at audit) | `16d1e2f` | `setup()` validates `is_relative_to(project_root.resolve())` and raises `MalformedOptionError(rule="escapes_project_root")` on escape. |
| R5 — `_IntegrationError.to_dict()` base body is dead code | LOW | `ce048bc` | Body replaced with `raise NotImplementedError(...)` + `# pragma: no cover`. Integrations layer reached 100 % per-file. |
| R6 — `--skills-dir` values that collapse to `project_root` itself bypass the R4 containment guard | CRITICAL | `c80f558` (audit at `13d5315`) | `setup()` short-circuits with `MalformedOptionError(rule="resolves_to_project_root", value=str(resolved))` when `target == project_root.resolve()` BEFORE the `is_relative_to(root)` test. Covers `""`, `"."`, `"./"`, `"foo/.."`. `base.py` SHA-256 pin in [tests/integrations/test_plugin_contract.py:43](tests/integrations/test_plugin_contract.py#L43) refreshed. |
| R7 — `parse_options` leaks bare `ValueError` from `shlex.split` on unbalanced quotes | CRITICAL | `c80f558` (audit at `13d5315`) | `shlex.split(raw, posix=True)` wrapped in `try / except ValueError` that re-raises as `MalformedOptionError(rule="malformed_shell_syntax", value=raw)`. Covered by 4 new parametric tests in [tests/integrations/test_option_parser.py:93-117](tests/integrations/test_option_parser.py#L93-L117). |

## 4. Remediation Detail

None this pass.

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
| `src/bookwright/core/manifest.py` | 98 % | 80 % | PASS (R2 late-import branch covered) |
| **Global** | **97.92 %** | 80 % | **PASS** |

## 6. Inability-to-verify notes

None this pass. Every rule in the matrix has a concrete on-disk verification, and every previously-open finding (R1–R7) is mechanically pinned by a regression test or a directly-checkable invariant.
