# Quality Audit — 003-integration-architecture

**Scope:** 37 changed paths vs `main` (8 spec docs + 7 production source files + 13 test files + 1 manifest re-rooting + 4 root-level convention / README / `.specify/feature.json` edits) + 14 audit-cycle commits closing R8-R22.
**Commit range:** `0944b08..4aef578` (branch tip).
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

Coverage gate: **PASS** (98.02 % global; integrations layer **100 % per file**, threshold = 80 %). 214 / 214 tests pass; `ruff check`, `ruff format --check`, and `mypy --strict` are clean across the whole project.

**Δ vs previous audit (`13d5315`):** a fresh extra-high-effort code-review pass (15 findings across 9 angles) surfaced 13 additional correctness / cleanup items (R8-R20) and 2 deferred items (R21, R22). All 13 actionable findings are closed by individual commits; R21+R22 are accepted with a written justification and a re-open trigger. The conventions matrix remains fully green; coverage drifted from 97.92 % up to 98.02 % as the R8-R20 fixes added new test cases for previously-untested guards. No drift in any non-finding area.

## 2. Conventions Compliance Matrix

Rules extracted from `.specify/memory/constitution.md` (v1.1.0), `specs/003-integration-architecture/plan.md`, and the iteration-3 spec's binding FR list. Grouped by source.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … are forbidden." | `.specify/memory/constitution.md:55-61` (Principle I) | layout | PASS | No binary files in diff or working tree (`.coverage`, `coverage.xml` are gitignored; pyproject.toml is text). |
| "Python 3.11+. Required toolchain: Typer / Pydantic v2 / rdflib / Jinja2 / hatchling / uv / ruff / mypy strict." | `.specify/memory/constitution.md:69-75` (Principle II) | dependency | PASS | `git diff main...HEAD -- pyproject.toml` is empty — no toolchain or runtime-dependency mutation. Integrations code is stdlib-only (`pathlib`, `shlex`, `dataclasses`, `typing`, `types.MappingProxyType`). |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | `.specify/memory/constitution.md:190-193` | dependency | PASS | No new runtime dependency declared. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`." | `.specify/memory/constitution.md:81-83` (Principle III) | layout | PASS | All new code under [src/bookwright/integrations/](src/bookwright/integrations/); all new tests under [tests/integrations/](tests/integrations/). No cross-leaks. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | `.specify/memory/constitution.md:91-92` (Principle IV) | module-size | N/A | No CLI subcommand added in this iteration (`bookwright init` lands in iteration 4). |
| "No source file (production or test) may exceed 500 lines." | `.specify/memory/constitution.md:93-95` (Principle IV) | module-size | PASS | Max integration source file: [src/bookwright/integrations/options.py](src/bookwright/integrations/options.py) at **189 lines** after R8/R9/R11/R14/R15; [src/bookwright/integrations/errors.py](src/bookwright/integrations/errors.py) at 117 (collapsed from 154 in R20); [src/bookwright/integrations/__init__.py](src/bookwright/integrations/__init__.py) at 122; [src/bookwright/integrations/base.py](src/bookwright/integrations/base.py) at 108. All well under 500. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. A monolithic `AGENT_CONFIG`-style dispatcher is forbidden." | `.specify/memory/constitution.md:103-108` (Principle V) | plugin-shape | PASS | `INTEGRATION_REGISTRY` still declared at [src/bookwright/integrations/__init__.py:32](src/bookwright/integrations/__init__.py#L32); both built-ins subclass `SkillsIntegration`; no `AGENT_CONFIG` dispatcher anywhere. R17 removed the dict from `__all__` to make `_register` the canonical entry point. |
| "Bookwright MUST emit Agent Skills (`<skills_dir>/<name>/SKILL.md`) and nothing else. Writing to `.claude/commands/`, `.agents/commands/`, or analogous legacy directories is prohibited." | `.specify/memory/constitution.md:115-119` (Principle VI, NON-NEGOTIABLE) | directory-ban | PASS | Mechanically enforced by [tests/integrations/test_no_legacy_commands.py](tests/integrations/test_no_legacy_commands.py) — three AST guards. Test green. |
| "name < 64 characters and exactly matching the parent directory name; description < 1024 characters." | `.specify/memory/constitution.md:127-136` (Principle VII) | frontmatter-constraint | N/A | This iteration emits no `SKILL.md` (FR-034). Constants `SKILL_NAME_MAX_LENGTH = 64` and `SKILL_DESCRIPTION_MAX_LENGTH = 1024` exposed at [src/bookwright/integrations/constants.py:16-17](src/bookwright/integrations/constants.py#L16-L17) for iteration 9. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`." | `.specify/memory/constitution.md:142-149` (Principle VIII, NON-NEGOTIABLE) | coverage-threshold | PASS | 98.02 % global; integrations layer **100 % per file** (see § 5). |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a `--json` flag and emit a single JSON document on stdout." | `.specify/memory/constitution.md:155-163` (Principle IX) | io-contract | N/A | No CLI command added in this iteration. Structured errors expose `to_dict()` (now centralised in `_IntegrationError` after R20) for iteration 4's `init --json`. |
| "This layer MUST NOT write to stdout or stderr. Errors are raised, never printed." | `specs/003-integration-architecture/spec.md` FR-037 | io-contract | PASS | Enforced by [tests/integrations/test_no_stdio.py](tests/integrations/test_no_stdio.py). Test green. |
| "All errors raised by this layer … MUST be structured exception types carrying a stable string `code`, `message`, `value`, and `valid` where applicable." | `specs/003-integration-architecture/spec.md` FR-035 | io-contract | PASS | Six structured errors in [src/bookwright/integrations/errors.py](src/bookwright/integrations/errors.py) (new `InvalidIntegrationError` from R13); JSON round-trip pinned by [tests/integrations/test_errors_json.py](tests/integrations/test_errors_json.py) (SC-008). Every subclass derives its payload from the centralised base `to_dict()` (R20). |
| "Preset system / GrafeoIndexer / multi-integration beyond claude+generic / extension system / pandoc — MUST NOT be pulled into v0 scope." | `.specify/memory/constitution.md:204-218` | scope-ban | PASS | Registry holds exactly `claude` + `generic`. No preset code, no `GrafeoIndexer` imports, no third integration. |
| "DEFAULT_SKILLS_DIR re-rooted from a literal in `core/manifest.py` to a derivation from the integrations registry via late import." | `plan.md:252-261` (iteration-3 structure decision) | workflow-step | PASS | [src/bookwright/core/manifest.py:58-71](src/bookwright/core/manifest.py#L58-L71) (`_default_skills_dir_map`) does the late import; R10 made the call site lazy so core-only callers (those passing `integration_skills_dir=` explicitly) skip the registry entirely. |
| "Each concrete integration lives under `src/bookwright/integrations/<key>/` … base, registry, parser, errors, constants live one level up." | `plan.md:239-249` | layout | PASS | File tree unchanged from iteration tip. |
| "Plugin extensibility is exercised, not just claimed (FakeIntegration smoke test + pinned-file hash assertion)." | `plan.md:268-274` | workflow-step | PASS | [tests/integrations/test_plugin_contract.py:41-47](tests/integrations/test_plugin_contract.py#L41-L47) pins SHA-256 of `base.py` (refreshed in R19), `claude/__init__.py`, `generic/__init__.py`. R17 migrated the in-test mutators to use `_register` instead of direct dict assignment. R16 added `.gitattributes` (`* text=auto eol=lf`) so the SHA pin is stable across Windows checkouts. |
| "FR-025 + FR-029: the resolved skills directory MUST be project-root-relative AND strictly contained inside `project_root`." | `specs/003-integration-architecture/spec.md` FR-025 + FR-029 | io-contract | PASS | Enforced in [src/bookwright/integrations/base.py:87-97](src/bookwright/integrations/base.py#L87-L97) with two sequential guards: `target == root` (R6, `resolves_to_project_root`) BEFORE `not target.is_relative_to(root)` (R4, `escapes_project_root`). |
| Track integrity — every governance / source artifact described in `plan.md` MUST be tracked by git on this branch. | derived (Pass A.3) | track-integrity | PASS | `git ls-files src/bookwright/integrations tests/integrations specs/003-integration-architecture` returns the full expected set; `git ls-files --others --exclude-standard` over the same paths returns nothing. |
| Workflow trail — every step from `/speckit-specify` through `/speckit-implement` MUST produce its artifact. | `CLAUDE.md:25-50` (Spec Kit sequence) | workflow-step | PASS | All artifacts present and tracked. The audit / remediation loop (R1 → R7 → R8-R22) is itself an instance of the workflow operating end-to-end through `/speckit-implement`. |

## 3. Findings

No open findings at any severity.

### Closed in prior passes (preserved for traceability)

| ID | Severity at open | Closed by | How |
|---|---|---|---|
| R1 — Integration source code untracked | CRITICAL | `7427249` | `git add src/bookwright/integrations` bundled into iteration-3 commit. |
| R2 — Integration test suite untracked | CRITICAL | `7427249` | `git add tests/integrations` bundled into iteration-3 commit. |
| R3 — `tasks.md` untracked | CRITICAL | `7427249` | `git add specs/003-integration-architecture/tasks.md` bundled into iteration-3 commit. |
| R4 — `--skills-dir` not validated for project-root containment | MEDIUM (upgraded HIGH at audit) | `16d1e2f` | `setup()` validates `is_relative_to(project_root.resolve())` and raises `MalformedOptionError(rule="escapes_project_root")` on escape. |
| R5 — `_IntegrationError.to_dict()` base body is dead code | LOW | `ce048bc` | Body replaced with `raise NotImplementedError(...)` + `# pragma: no cover`. Subsequently superseded by R18 + R20. |
| R6 — `--skills-dir` values that collapse to `project_root` itself bypass the R4 containment guard | CRITICAL | `c80f558` (audit at `13d5315`) | `setup()` short-circuits with `MalformedOptionError(rule="resolves_to_project_root", value=str(resolved))` when `target == project_root.resolve()` BEFORE the `is_relative_to(root)` test. Covers `""`, `"."`, `"./"`, `"foo/.."`. |
| R7 — `parse_options` leaks bare `ValueError` from `shlex.split` on unbalanced quotes | CRITICAL | `c80f558` (audit at `13d5315`) | `shlex.split(raw, posix=True)` wrapped in `try / except ValueError` that re-raises as `MalformedOptionError(rule="malformed_shell_syntax", value=raw)`. |

### Closed in this audit cycle (R8-R20)

| ID | Severity at open | Closed by | How |
|---|---|---|---|
| R8 — `IntegrationOption.default` declared but never applied | HIGH (silent dead state) | `0dd7813` | `parse_options` applies declared defaults for omitted opts in both branches (empty + non-empty input). `required=True, default=X` is satisfied by the default. Happy-path tests updated to reflect GenericIntegration's default-of-`.agents/skills`. |
| R9 — Empty-input short-circuit bypasses `_validate_descriptor` | HIGH (FR-015 violation) | `5dd1518` | Validation loop moved BEFORE the `raw is None or raw.strip() == ""` short-circuit. A broken `options()` declaration now surfaces on the first parse call regardless of user input. |
| R10 — `Manifest.build` always triggers integrations import | MEDIUM | `ec5df13` | `_default_skills_dir_map()` only called when `integration_skills_dir` is absent from overrides. Core-only callers (iteration-2-style) avoid the registry entirely. Regression test monkey-patches the function to raise. |
| R11 — `--flag=` (inline empty value) silently parses as `''` | HIGH (asymmetric with bare `--flag`) | `782dd08` | Inline-equals branch checks `value == ""` and raises `MalformedOptionError(rule='missing_value')`, matching the bare-flag behaviour. |
| R12 — `existing is cls` defeats reload idempotency | MEDIUM (FR-002 violation) | `04140aa` | `_register` compares by `is OR _fqcn(existing) == _fqcn(cls)`. Reloaded submodules (new identity, same FQCN) re-register without raising; the registry rebinds to the reloaded class. Genuinely-different classes still raise `DuplicateRegistrationError`. |
| R13 — `_register` accepts `cls.key == ''` silently | MEDIUM | `bf62e1f` | New `InvalidIntegrationError` (code='invalid_integration', rule='empty_key'). `_register` raises before binding. Catches both the abstract base and forgetful subclasses on the FIRST registration, not the second. |
| R14 — Duplicate flags in `options()` silently coalesce | MEDIUM (FR-015 violation) | `231b2d2` | After `_validate_descriptor`, compare `len(set(flags)) == len(flags)`; raise `InvalidOptionDeclarationError(rule='duplicate_flag', value=<first dup>)` on mismatch. |
| R15 — `--skills-dir` and `--skills_dir` collide after normalize | MEDIUM | `33c3b5c` | Map flag→normalized identifier; raise `InvalidOptionDeclarationError(rule='colliding_identifiers')` naming BOTH colliding flags and the shared identifier on collision. |
| R16 — Pinned-SHA test breaks on Windows CRLF checkouts | MEDIUM | `4aef578` | New `.gitattributes` with `* text=auto eol=lf` + binary-extension pins. Verified pinned hashes unchanged (the three files were already LF on disk). |
| R17 — `INTEGRATION_REGISTRY` in `__all__` invited direct mutation | MEDIUM | `578abb6` | Removed from `__all__` with an in-source comment naming the canonical API (`get`, `list_keys`, `_register`). Migrated the two in-test mutators to `_register(...)` so the FR-005 / R13 guards exercise the same path. |
| R18 — `_IntegrationError.to_dict()` `NotImplementedError + pragma` masked forgetful subclasses | LOW | `e6f79da` | `__init_subclass__` enforcement (not `abc.ABC` — `BaseException.__new__` bypasses `__abstractmethods__` in CPython); rejects subclasses without `to_dict` at class-definition time. **Superseded by R20** (the base now provides a usable concrete impl, so the enforcement was removed in the same series). |
| R19 — `config: ClassVar[dict] = {}` shared mutable default | LOW | `16a89f3` | Default changed to `types.MappingProxyType({})`. Forgetful subclasses cannot accidentally mutate the base dict. Pinned-file SHA for `base.py` refreshed. |
| R20 — Five near-identical `to_dict()` overrides | LOW (drift risk) | `7d8859a` | Centralised `to_dict` in `_IntegrationError`: walk `vars(self)` minus private/dunder names + `message`. All six subclasses (including the new R13 one) drop their override and inherit the base impl. JSON payload shape unchanged (verified by the pinned-payload tests in `test_errors_json.py`). |

### Accepted — deferred to a later milestone

| ID | Severity | Re-open trigger | Justification |
|---|---|---|---|
| R21 — TOCTOU race in `setup()` between `is_relative_to(root)` and `mkdir(parents=True)` | LOW (defensive) | v0.5 — extension system | Bookwright is a single-user CLI; the v0 threat model does not contemplate concurrent hostile processes within `project_root` during `init`. A symlink-swap attack requires write access to a parent of the resolved target, which the user already has full control over. Re-open when v0.5 introduces third-party extension plugins and the threat model expands. |
| R22 — `MalformedOptionError` covers both input-parse and path-placement errors | LOW (semantic overload) | When iteration 4's `init --json` envelope ships | Splitting into two classes (e.g., `InvalidSkillsDirError`) requires coordination with the iteration-4 envelope contract that does not yet exist in code. The `rule` field already discriminates the five concrete cases (`missing_value`, `duplicate_flag`, `malformed_shell_syntax`, `resolves_to_project_root`, `escapes_project_root`). Re-open when iteration 4 lands and consumer telemetry confirms the distinction must rise from `rule` to `code`. |

## 4. Remediation Detail

R8-R20 are all closed by individual commits with self-contained context in their commit messages (`git log e5da58b..HEAD --reverse`). No remediation remains open. R21+R22 carry the re-open triggers above; flag them in the next audit by checking whether the trigger condition has become true.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/integrations/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/base.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/claude/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/constants.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/errors.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/generic/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/options.py` | 100 % | 80 % | PASS |
| `src/bookwright/core/manifest.py` | 98 % | 80 % | PASS |
| **Global** | **98.02 %** | 80 % | **PASS** |

## 6. Inability-to-verify notes

None this pass. Every rule in the matrix has a concrete on-disk verification, every closure in R8-R20 has a regression test, and the two deferred items (R21, R22) carry an explicit re-open trigger.
