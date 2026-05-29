# Quality Audit — 003-integration-architecture

**Scope:** 22 changed paths vs `main` (7 spec docs + 1 modified source + 1 modified test + 1 untracked spec artifact + 8 untracked source files + 12 untracked test files + 2 root-level conventions edits already on branch).
**Commit range:** `0944b08..25d6e9e` (branch tip) + uncommitted working tree.
**Date:** 2026-05-29
**Conventions discovered:** `CLAUDE.md`, `CONTRIBUTING.md`, `.specify/memory/constitution.md` (v1.1.0), `README.md`, `specs/003-integration-architecture/plan.md`.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 3 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 1 |
| **Total** | 5 |

Coverage gate: **PASS** (97.75 % global, threshold = 80 %; integrations layer at 99.6 % — all integrations files at 100 % except `errors.py` at 98 %). 184 / 184 tests pass; `ruff check`, `ruff format --check`, and `mypy --strict` clean on `src/bookwright/integrations` + `tests/integrations`.

## 2. Conventions Compliance Matrix

Rules extracted from `.specify/memory/constitution.md` (v1.1.0) + `specs/003-integration-architecture/plan.md` (binding for this iteration). Grouped by source.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … are forbidden." | `.specify/memory/constitution.md:55-61` (Principle I) | layout | PASS | No binary files in diff or working tree (`.coverage`, `coverage.xml` are gitignored). |
| "Python 3.11+. Required toolchain: Typer/Pydantic v2/rdflib/Jinja2/hatchling/uv/ruff/mypy strict." | `.specify/memory/constitution.md:69-75` (Principle II) | dependency | PASS | `pyproject.toml` unchanged on this branch; new integrations code is stdlib-only (`pathlib`, `shlex`, `dataclasses`, `typing`). |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | `.specify/memory/constitution.md:190-193` | dependency | PASS | No new runtime dependency declared in `pyproject.toml`. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`." | `.specify/memory/constitution.md:81-83` (Principle III) | layout | PASS | All new code under `src/bookwright/integrations/`; all new tests under `tests/integrations/`. No cross-leaks. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | `.specify/memory/constitution.md:91-92` (Principle IV) | module-size | N/A | No CLI subcommand added in this iteration. |
| "No source file (production or test) may exceed 500 lines." | `.specify/memory/constitution.md:93-95` (Principle IV) | module-size | PASS | Max integration file: `errors.py` at 151 lines; total across 7 files: 593 lines. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. A monolithic `AGENT_CONFIG`-style dispatcher is forbidden." | `.specify/memory/constitution.md:103-108` (Principle V) | plugin-shape | PASS | [src/bookwright/integrations/__init__.py:32](src/bookwright/integrations/__init__.py#L32) declares `INTEGRATION_REGISTRY`; both built-ins subclass `SkillsIntegration`; no `AGENT_CONFIG` dispatcher anywhere. |
| "Bookwright MUST emit Agent Skills (`<skills_dir>/<name>/SKILL.md`) and nothing else. Writing to `.claude/commands/`, `.agents/commands/`, or analogous legacy directories is prohibited." | `.specify/memory/constitution.md:115-119` (Principle VI, NON-NEGOTIABLE) | directory-ban | PASS | Mechanically enforced by [tests/integrations/test_no_legacy_commands.py](tests/integrations/test_no_legacy_commands.py) (AST + literal grep). Test green. |
| "name < 64 characters and exactly matching the parent directory name; description < 1024 characters." | `.specify/memory/constitution.md:127-136` (Principle VII) | frontmatter-constraint | N/A | This iteration emits no `SKILL.md` (FR-034). Constants `SKILL_NAME_MAX_LENGTH = 64` and `SKILL_DESCRIPTION_MAX_LENGTH = 1024` exposed at [src/bookwright/integrations/constants.py:16-17](src/bookwright/integrations/constants.py#L16-L17) for iteration 9. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`." | `.specify/memory/constitution.md:142-149` (Principle VIII, NON-NEGOTIABLE) | coverage-threshold | PASS | 97.75 % global; integrations layer ≥98 % per-file. |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a `--json` flag and emit a single JSON document on stdout." | `.specify/memory/constitution.md:155-163` (Principle IX) | io-contract | N/A | No CLI command added in this iteration; structured errors expose `to_dict()` for iteration 4's `init --json`. |
| "This layer MUST NOT write to stdout or stderr. Errors are raised, never printed." | `specs/003-integration-architecture/spec.md` FR-037 | io-contract | PASS | Enforced by [tests/integrations/test_no_stdio.py](tests/integrations/test_no_stdio.py) (AST-walk for `print()`, `sys.stdout`, `sys.stderr`, `from sys import …`). Test green. |
| "Preset system / GrafeoIndexer / multi-integration beyond claude+generic / extension system / pandoc — MUST NOT be pulled into v0 scope." | `.specify/memory/constitution.md:204-218` | scope-ban | PASS | Registry holds exactly `claude`+`generic`. No preset code, no `GrafeoIndexer` imports, no third integration. |
| "DEFAULT_SKILLS_DIR re-rooted from a literal in `core/manifest.py` to a derivation from the integrations registry via late import." | `plan.md:252-261` (iteration-3 structure decision) | workflow-step | PASS | [src/bookwright/core/manifest.py:58-71](src/bookwright/core/manifest.py#L58-L71) (`_default_skills_dir_map`) does the late import; covered by [tests/core/test_build.py:137-142](tests/core/test_build.py#L137-L142). |
| "Each concrete integration lives under `src/bookwright/integrations/<key>/` … base, registry, parser, errors, constants live one level up." | `plan.md:239-249` | layout | PASS | File tree exactly matches the plan: `base.py`, `__init__.py`, `options.py`, `errors.py`, `constants.py` at the layer root; `claude/` and `generic/` as subpackages. |
| "Plugin extensibility is exercised, not just claimed (FakeIntegration smoke test + pinned-file hash assertion)." | `plan.md:268-274` | workflow-step | PASS | [tests/integrations/test_plugin_contract.py:130-146](tests/integrations/test_plugin_contract.py#L130-L146) pins SHA-256 of `base.py`, `claude/__init__.py`, `generic/__init__.py`. |
| Track integrity — every governance/source artifact described in plan.md MUST be tracked by git on this branch. | derived (A.3, audit-skill rule) | track-integrity | **FAIL** | **All 8 source files under `src/bookwright/integrations/`, all 12 test files under `tests/integrations/`, and `specs/003-integration-architecture/tasks.md` are `??` (untracked). See R1–R3.** |
| Workflow trail — every step from `/speckit-specify` through `/speckit-implement` MUST produce its artifact. | `CLAUDE.md:25-50` (Spec Kit sequence) | workflow-step | PASS (artifacts exist on disk) | `spec.md`, `plan.md`, `tasks.md`, source under `src/bookwright/integrations/`, tests under `tests/integrations/` all present in working tree — though `tasks.md` and the implementation are untracked (see R1–R3). The *trail* is intact; the *commits* are not. |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A.3 | CRITICAL | [src/bookwright/integrations/](src/bookwright/integrations/) (8 .py files) | Entire iteration-3 implementation exists on disk but is untracked (`git status` reports `??`). Invisible to `git diff main...HEAD`, to humans reviewing the branch, and to CI. | `git add src/bookwright/integrations` then commit before any further work. |
| R2 | A.3 | CRITICAL | [tests/integrations/](tests/integrations/) (12 .py files) | Entire iteration-3 test suite (94 tests) untracked. Without it the FR-031 plugin-contract test, the FR-037 no-stdio guard, and the FR-032 no-legacy-commands guard never run in CI. | `git add tests/integrations` then commit. |
| R3 | A.3 | CRITICAL | [specs/003-integration-architecture/tasks.md](specs/003-integration-architecture/tasks.md) | Spec Kit governance artifact (275 lines, the `/speckit-tasks` output for this iteration) is untracked. Reviewers cannot see which tasks the implementation was supposed to satisfy. | `git add specs/003-integration-architecture/tasks.md` and include in the same commit as R1/R2. |
| R4 | D | MEDIUM | [src/bookwright/integrations/generic/__init__.py:50-56](src/bookwright/integrations/generic/__init__.py#L50-L56) → [src/bookwright/integrations/base.py:86-87](src/bookwright/integrations/base.py#L86-L87) | `--skills-dir` is user-controlled CLI input. `GenericIntegration.resolve_skills_dir({"skills_dir": "../../etc/foo"})` returns a relative `Path` whose components escape the project root, and `setup()` then `mkdir(parents=True, exist_ok=True)` outside `project_root`. The only existing guard ([tests/integrations/test_resolve_skills_dir.py:54-61](tests/integrations/test_resolve_skills_dir.py#L54-L61)) only asserts `is_absolute() is False`, which passes for `"../escape"`. FR-025 phrases the contract as "project-root relative" — currently only "not absolute" is enforced. | In `SkillsIntegration.setup()` after `target = project_root / self.resolve_skills_dir(...)`, validate `target.resolve().is_relative_to(project_root.resolve())` and raise a structured `MalformedOptionError` (or a new `OutOfProjectRootError`) if not. Add a `tests/integrations/test_setup_stub.py` case for `--skills-dir "../escape"`. |
| R5 | B | LOW | [src/bookwright/integrations/errors.py:32-33](src/bookwright/integrations/errors.py#L32-L33) | `_IntegrationError.to_dict()` is dead code — every public subclass overrides it (the only line missed in coverage on the integrations layer). Either drop the base implementation (subclasses already supply their own and the base class is private), or annotate it `# pragma: no cover` with a note that it exists as a structural fallback. | Delete lines 32-33; the abstract intent is documented in the class docstring already. |

## 4. Remediation Detail

### R1 — Integration source code is untracked

- **Where:** `src/bookwright/integrations/` — the 7 production `.py` files plus `__init__.py` files in `claude/` and `generic/`.
- **Why it matters:** `git diff main...HEAD` shows zero source code for iteration 3. A reviewer comparing the branch to `main` will see only spec edits and one modified line in `core/manifest.py` — they will not see the actual integration layer that those specs describe. CI on this branch would similarly compile and run the tests from `main`'s tree only, hiding any breakage. Track-integrity is the most load-bearing single check in this audit because everything else (Conventions, smells, security) reviews what `git` can see — if the work is invisible to `git`, none of the other gates apply to it.
- **Suggested change:**
  ```
  git add src/bookwright/integrations
  git commit -m "feat(integrations): iteration 3 — registry, base, options parser, stub setup()"
  ```
  Use one commit per logical unit if you prefer (registry+base, claude+generic, options parser, errors), but do not leave the working tree in this state across another `/speckit-implement` run.

### R2 — Integration test suite is untracked

- **Where:** `tests/integrations/` — 11 test modules + `__init__.py` + `conftest.py` (94 tests total per `pytest -q`).
- **Why it matters:** Every Principle-VI / Principle-IX guarantee in this iteration is enforced mechanically by an AST-walk test (`test_no_legacy_commands.py`, `test_no_stdio.py`) or a registry-state test (`test_plugin_contract.py`'s pinned-hash assertion). When these tests are not in `main`'s tree, none of those constitutional guarantees are enforced post-merge — the next iteration could quietly introduce a `.claude/commands/` write and the gate would silently fail to fire. Coverage that this audit reports (97.75 %) is computed against the local working tree only; on `origin/main`'s tree the integrations layer would be 0 % covered.
- **Suggested change:** Include `tests/integrations/` in the same commit as R1, or a sibling test-only commit. Verify with `git ls-files tests/integrations | wc -l` returning 13.

### R3 — `tasks.md` is untracked

- **Where:** `specs/003-integration-architecture/tasks.md` (275 lines).
- **Why it matters:** Spec Kit's `/speckit-implement` checklist scan reads this file to know which tasks remain — an untracked `tasks.md` works locally but disappears the moment another developer (or a fresh worktree) checks out the branch, and `/speckit-analyze`'s cross-artifact consistency check has nothing to compare `plan.md` against. This is also a constitutional Principle-I issue (plain text source of truth) one level up: the governance is in the file, but git doesn't know the file exists.
- **Suggested change:** `git add specs/003-integration-architecture/tasks.md`. Bundle with R1/R2.

### R4 — `--skills-dir` is not validated for project-root containment

- **Where:**
  - declared: [src/bookwright/integrations/generic/__init__.py:50-56](src/bookwright/integrations/generic/__init__.py#L50-L56) — `resolve_skills_dir` returns `Path(str(parsed_options["skills_dir"]))` with no normalization.
  - applied: [src/bookwright/integrations/base.py:86-87](src/bookwright/integrations/base.py#L86-L87) — `target = project_root / self.resolve_skills_dir(parsed_options); target.mkdir(parents=True, exist_ok=True)`.
  - existing guard: [tests/integrations/test_resolve_skills_dir.py:54-61](tests/integrations/test_resolve_skills_dir.py#L54-L61) only asserts `result.is_absolute() is False` — `Path("../../etc/foo").is_absolute()` is also `False`, so the guard passes for an escape attempt.
- **Why it matters:** The `--integration-options` string is a user-supplied CLI boundary input. FR-025 reads "The returned `Path` MUST be a relative path (project-root relative)"; FR-029 reads "`setup()` MUST NOT … touch any file outside the resolved skills directory." Both are satisfiable today by a value that traverses out of the project (`../../something`). In v0 this is the same user's own machine, so the blast radius is small; but the contract published by `FR-025` is stronger than what the code enforces, and iteration 4's `bookwright init --json` will inherit this gap. Catching it here is one `is_relative_to` call.
- **Suggested change:** In [src/bookwright/integrations/base.py](src/bookwright/integrations/base.py), tighten `setup()`:
  ```python
  resolved = self.resolve_skills_dir(parsed_options)
  target = (project_root / resolved).resolve()
  root = project_root.resolve()
  if not target.is_relative_to(root):
      raise MalformedOptionError(rule="escapes_project_root", value=str(resolved))
  target.mkdir(parents=True, exist_ok=True)
  ```
  Add `MalformedOptionError` with rule `escapes_project_root` to `tests/integrations/test_setup_stub.py` and `test_resolve_skills_dir.py`. Spec text in FR-019 lists the existing `malformed_option` rules; extending the enum here is in-scope.

### R5 — `_IntegrationError.to_dict()` base body is dead code

- **Where:** [src/bookwright/integrations/errors.py:32-33](src/bookwright/integrations/errors.py#L32-L33).
- **Why it matters:** It is the single line not hit by the integrations test suite (98 % file coverage). The base is private (`_IntegrationError`); every public subclass overrides `to_dict()` with a richer payload. Leaving the body in place suggests it is a usable fallback when in fact it would silently emit `{"code": "", "message": "…"}` for a subclass that forgot to set `code` — a "silent wrong" outcome rather than a loud failure.
- **Suggested change:** Either delete lines 32-33 (subclasses fully cover the contract; the class docstring already describes the intent), or replace with `raise NotImplementedError` so a forgetful future subclass fails loudly instead of returning a degraded dict.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/integrations/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/base.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/claude/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/constants.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/errors.py` | 98 % | 80 % | PASS (one dead line — see R5) |
| `src/bookwright/integrations/generic/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/integrations/options.py` | 100 % | 80 % | PASS |
| `src/bookwright/core/manifest.py` | 98 % | 80 % | PASS (re-rooting line included) |
| **Global** | **97.75 %** | 80 % | **PASS** |

## 6. Inability-to-verify notes

- The pinned-hash assertion in [tests/integrations/test_plugin_contract.py:41-45](tests/integrations/test_plugin_contract.py#L41-L45) couples the test suite to the exact bytes of `base.py`, `claude/__init__.py`, `generic/__init__.py`. This is intentional (FR-031 enforcement) but means any remediation to R4 that touches `base.py` will require recomputing the SHA-256 in the same commit. Not a finding — flagged so the next implementation pass knows to expect it.
- `/speckit-analyze` has not been run on this iteration on this branch (the skill produces a checklist line, not a persistent artifact). This audit verified the artifacts each Spec-Kit step produces but cannot certify that `/speckit-analyze` would itself report green; the conventions matrix above is the closest stand-in.

## Next Actions

Three buckets, in priority order.

### Bucket 1 — Restore track integrity (must run before anything else)

R1–R3 are uncommitted/untracked governance and source files. Resolve in a single bundled commit so the branch becomes reviewable:

```
git add src/bookwright/integrations tests/integrations specs/003-integration-architecture/tasks.md
git diff --cached --stat   # sanity-check what you're about to commit
git commit -m "feat(integrations): iteration 3 — registry, base, options parser, stub setup() + tests + tasks"
```

After committing, also commit the already-modified files (`specs/003-integration-architecture/{spec,plan,data-model,quickstart,contracts/integrations_api}.md`, `src/bookwright/core/manifest.py`, `tests/core/test_build.py`) — they are tracked modifications already and should land in their own logical commit per project convention.

### Bucket 2 — CRITICAL/HIGH remediations within current scope

Once track integrity is restored, apply R4 (path-traversal containment guard). Use the Spec Kit implement skill so the change is itemized:

```
/speckit-implement Apply the MEDIUM remediation from
specs/003-integration-architecture/review.md (ID: R4). Add `is_relative_to`
containment validation in SkillsIntegration.setup() and a corresponding
MalformedOptionError rule `escapes_project_root`. Extend
tests/integrations/test_setup_stub.py and test_resolve_skills_dir.py. Keep
the current PR scope; do not add new tasks to tasks.md.
```

### Bucket 3 — Local cleanup

R5 (dead `to_dict()` base body) is a local, safe cleanup. After Bucket 2 lands:

```
/simplify
```

…will pick up the diff and apply the cleanup inline. Re-run `/quality-audit` afterwards to confirm the matrix is fully green.

`specs/003-integration-architecture/checklists/quality.md` blocks the next `/speckit-implement` pass (the checklist scan stalls on unticked items); tick each item as its commit lands.
