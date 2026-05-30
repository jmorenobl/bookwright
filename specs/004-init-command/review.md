# Quality Audit — 004-init-command

**Scope:** 103 changed files vs `main` (full branch, post-T050 layout).
**Commit range:** `main..1c6ad45`
**Date:** 2026-05-30
**Conventions discovered:** [.specify/memory/constitution.md](../../.specify/memory/constitution.md) (v1.1.0, ratified 2026-05-28), [CLAUDE.md](../../CLAUDE.md), [CONTRIBUTING.md](../../CONTRIBUTING.md)

This audit re-runs against the iteration-4 branch after five follow-up
commits closed the prior audit's two MEDIUM items (R1 `git_status =
"pending"` sentinel, R2 `except BaseException`) and tasks T047–T050
(`dirhash` directory capture, hoisted resolution, envelope-shaped
`ValidationError`, scaffold-time `MalformedOptionError` classification).
The quality gates are all green: 356 tests pass, global line coverage is
**97.48 %**, and `ruff check`, `ruff format --check`, `mypy --strict src
tests` all run clean. The findings below are the residual signals that
survived that cleanup.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH     | 0 |
| MEDIUM   | 1 |
| LOW      | 3 |
| **Total** | 4 |

Coverage gate: **PASS** (global 97.48 %, threshold 80 %, every changed
init module ≥ 95 %).

## 2. Conventions Compliance Matrix

One row per rule extracted from convention files. Grouped by source file.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … are forbidden as canonical storage." | [constitution.md:54-61](../../.specify/memory/constitution.md#L54-L61) | layout | PASS | Every resource under [src/bookwright/resources/project/](../../src/bookwright/resources/project/) is `.md`, `.md.j2`, `.gitkeep`, `.gitignore`. Vocabularies are `.ttl`. No binary blobs in the diff. |
| "Python 3.11+. No support for 3.10 or earlier." | [constitution.md:189](../../.specify/memory/constitution.md#L189) | dependency | PASS | [pyproject.toml:8](../../pyproject.toml#L8) `requires-python = ">=3.11"`. |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | [constitution.md:190-193](../../.specify/memory/constitution.md#L190-L193) | dependency | PASS | [pyproject.toml:21-31](../../pyproject.toml#L21-L31) lists exactly those ten — no additions. |
| "Build backend: hatchling. Lockfile: uv.lock committed." | [constitution.md:194-195](../../.specify/memory/constitution.md#L194-L195) | dependency | PASS | [pyproject.toml:36-38](../../pyproject.toml#L36-L38) + `uv.lock` tracked at repo root. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`. No exceptions." | [constitution.md:81-83](../../.specify/memory/constitution.md#L81-L83) | layout | PASS | Diff scopes 100 % to `src/bookwright/**` and `tests/**`. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | [constitution.md:92-93](../../.specify/memory/constitution.md#L92-L93) | layout | PASS | Three commands at `commands/`: `check.py`, `version.py`, `init/`. Package form satisfies "module under `commands/<name>`". |
| "No source file (production or test) may exceed 500 lines." | [constitution.md:93-95](../../.specify/memory/constitution.md#L93-L95) | module-size | PASS | Largest production file: [src/bookwright/commands/init/scaffold.py](../../src/bookwright/commands/init/scaffold.py) 396 lines. Largest test: [tests/commands/test_init_helpers.py](../../tests/commands/test_init_helpers.py) 376 lines. |
| "Monolithic `cli.py` files that inline subcommand bodies are prohibited." | [constitution.md:95-96](../../.specify/memory/constitution.md#L95-L96) | layout | PASS | [src/bookwright/cli.py](../../src/bookwright/cli.py) is 16 lines, only wiring. |
| "Integrations MUST be implemented as subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. Monolithic `AGENT_CONFIG`-style dispatch forbidden." | [constitution.md:101-108](../../.specify/memory/constitution.md#L101-L108) | plugin-shape | PASS | `init.run` calls `resolve.resolve_integration(...)` → `integrations.get(key)` ([resolve.py:165](../../src/bookwright/commands/init/resolve.py#L165)) and `integration_cls()` ([main.py:141](../../src/bookwright/commands/init/main.py#L141)). No `if key == "claude"` ladder anywhere in `commands/init/`. |
| "Bookwright MUST emit Agent Skills … nothing else. Writing to `.claude/commands/`, `.agents/commands/`, or any analogous … directory is prohibited." | [constitution.md:114-119](../../.specify/memory/constitution.md#L114-L119) | directory-ban | PASS | `grep -rn '\.claude/commands\|\.agents/commands\|\.cursor/commands' src/` returns zero. The only write under the integration's tree is `SkillsIntegration.setup()`'s placeholder marker. |
| "name < 64 chars matching parent directory; description < 1024 chars; valid YAML frontmatter." | [constitution.md:127-136](../../.specify/memory/constitution.md#L127-L136) | frontmatter-constraint | N/A | No `SKILL.md` files generated in iteration 4 — the placeholder marker is exempt. Full skill materialization lands in iteration 9. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`." | [constitution.md:144-145](../../.specify/memory/constitution.md#L144-L145) | coverage-threshold | PASS | `pytest --cov` reports **97.48 %** global; every changed init module is between 95 % and 100 %. See §5. |
| "CI MUST run pytest, ruff, and mypy strict on every push and pull request; a red bar blocks merge." | [constitution.md:149-150](../../.specify/memory/constitution.md#L149-L150) | workflow-step | PASS | All four gates clean locally: `pytest` (356 passed), `ruff check` (All checks passed!), `ruff format --check` (74 files already formatted), `mypy --strict src tests` (no issues found in 74 source files). |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a `--json` flag and, when set, emit a single well-formed JSON document on stdout and nothing else." | [constitution.md:155-163](../../.specify/memory/constitution.md#L155-L163) | io-contract | PASS | Subprocess pins in [tests/commands/test_init_json_envelope.py](../../tests/commands/test_init_json_envelope.py) verify stdout purity on success + every documented failure mode (`mutually_exclusive`, `invalid_project_name`, `unknown_integration`, `removed_flag`). AST invariants in [tests/commands/test_init_ast_invariants.py](../../tests/commands/test_init_ast_invariants.py) pin zero rogue `tomlkit.*` or `shlex.split` calls in the init package. |
| "Preset system … v0.2. GrafeoIndexer … v0.3. Multi-integration beyond claude/generic … v0.4. Extension system … v0.5. Export … v1.0." | [constitution.md:207-213](../../.specify/memory/constitution.md#L207-L213) | scope-ban | PASS | Diff introduces no `--preset` flag, no `GrafeoIndexer` reference, no third integration, no extension plumbing, no export subcommand. `grep -rn 'preset\|grafeo\|export' src/bookwright/commands/init/` returns zero. |
| "Workflow: /speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement." | [CLAUDE.md:33-52](../../CLAUDE.md#L33-L52) | workflow-step | PASS | All artifacts present in branch: `spec.md` (with Session 2026-05-29 clarifications), `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/init_command.md`, `quickstart.md`, prior `review.md`. `git log --oneline main..HEAD` shows the full pipeline trail (specify, clarify, plan, tasks, implement, quality-audit rounds, T047–T050 closures). |
| "specs/NNN-name/ governance files tracked on branch." | [CLAUDE.md:60-62](../../CLAUDE.md#L60-L62) | track-integrity | PASS | A.3 cross-check: every file in [specs/004-init-command/](../) (10 files including the prior `review.md` and both checklists) is in `git diff main...HEAD`. `git status --porcelain` is clean. No uncommitted or untracked governance artifacts. |
| "Each iteration produces a feature branch `NNN-<short-name>` with its own specs/NNN-name/{spec,plan,tasks}.md." | [CLAUDE.md:33-46](../../CLAUDE.md#L33-L46) | layout | PASS | Branch is `004-init-command`, directory is `specs/004-init-command/`, the three core files are present and committed. |
| "Source code, identifiers, commit messages, and the constitution itself are in English." | [CLAUDE.md:131-134](../../CLAUDE.md#L131-L134) | other | PASS | All new source files (`commands/init/*.py`, tests, contracts, plan) are in English. Spanish appears only in the user-authored design docs (out of scope for this branch). |
| "Pre-commit hooks (ruff format, ruff check, check-toml, check-yaml)." | [CONTRIBUTING.md:46-52](../../CONTRIBUTING.md#L46-L52) | workflow-step | PASS | `ruff check .` and `ruff format --check .` both green; no toml/yaml in the diff that pre-commit would reject. |

No `FAIL` rows. Track-integrity (A.3) and workflow-trail (A.4) both
pass — every governance artifact this branch produced is committed and
visible to `git diff`, and the workflow steps are materialised through
the expected artifacts in order.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | MEDIUM | [src/bookwright/commands/init/main.py:141](../../src/bookwright/commands/init/main.py#L141), [scaffold.py:370](../../src/bookwright/commands/init/scaffold.py#L370), [scaffold.py:375](../../src/bookwright/commands/init/scaffold.py#L375) | `integration_cls()` is instantiated three times per `init` invocation (once in `main.run` to compute `skills_dir`, twice inside `run_scaffold_steps` for `mkdir_tracked` + `setup()`). The two integrations in v0 carry no per-instance state, but the pattern reads as if they did, and a future `__init__` with non-trivial cost would be invoked thrice without anyone noticing. | Build the instance once: `integration = integration_cls()` in `main.run`, then thread the *instance* (not the class) into `run_scaffold_steps`. Update the `run_scaffold_steps` signature so `integration_cls` becomes `integration: SkillsIntegration`. Single-line change in three callsites; no behavioural delta. |
| R2 | B | LOW | [tests/commands/test_init_options_record.py:85](../../tests/commands/test_init_options_record.py#L85) | Dead-code expression: `(target / ".bookwright_temp").write_text("temp", encoding="utf-8") if False else None`. The `if False else None` always evaluates to `None`; the `write_text` branch is unreachable. Leftover from an earlier draft — flagged in the prior audit (R3 then) and still on disk. | Delete the line outright. If the temp file was needed as a fixture artifact, lift it into a real conditional or a parametrize id; otherwise it just confuses future readers. |
| R3 | B | LOW | [tests/commands/test_init_branches.py:94-103](../../tests/commands/test_init_branches.py#L94-L103) | `test_named_mode_reserved_slug` is named for the "slugifies to a reserved name" path but its body sends `"***"` (which slugifies to empty, tripping the `empty` rule) and its own docstring concludes *"Skip this — covered already by derive_slug raising on '***'"*. The test name + docstring still describe an intent the body abandoned — also flagged as R4 in the prior audit, still uncorrected. | Rename to `test_named_mode_slugifies_to_empty` and rewrite the docstring; OR replace the body with a name whose slug actually lands on a reserved word and reassert the `reserved_name` rule. Either resolves the name/body drift. |
| R4 | B | LOW | [tests/commands/test_init_here.py:27,56,80,129](../../tests/commands/test_init_here.py#L27), [test_init_integrations.py:183](../../tests/commands/test_init_integrations.py#L183), [test_init_options_record.py:87](../../tests/commands/test_init_options_record.py#L87) | Six test functions across five files each carry `import os as _os  # noqa: PLC0415` at the top of their body just to call `_os.chdir(...)`. None of those files import `os` at module scope, so the alias and the lint waiver are unnecessary — a top-level `import os` removes both. The repetition reads like a pattern that was adopted once and copy-pasted without reconsidering. | In each of the five files, add `import os` to the module's import block and replace the in-body `import os as _os  # noqa: PLC0415` + `_os.chdir(...)` with a direct `os.chdir(...)`. Net delta: -6 lines, -6 noqa pragmas, -6 alias names. |

## 4. Remediation Detail

### R1 — Triple instantiation of the integration class per `init` call

- **Where:** [src/bookwright/commands/init/main.py:141](../../src/bookwright/commands/init/main.py#L141), [src/bookwright/commands/init/scaffold.py:370](../../src/bookwright/commands/init/scaffold.py#L370), [src/bookwright/commands/init/scaffold.py:375](../../src/bookwright/commands/init/scaffold.py#L375).
- **Why it matters:** The call shape `integration_cls().resolve_skills_dir(...)` / `integration_cls().setup(...)` reads as if the result is a stateless class-method. The implementation is in fact `def resolve_skills_dir(self, …)` and `def setup(self, …)` — instance methods on `SkillsIntegration`. The constitution mandates the registry shape (`integrations.get(key)` → a `type[SkillsIntegration]`), so what callers receive is genuinely the class. But there is no reason to construct three throw-away instances per invocation — and a future `__init__` with non-trivial cost (e.g. an integration that discovers an installed agent's home directory) would be invoked three times without anyone noticing. The pattern also subtly invites bugs where someone caches state on `self` in one branch and is surprised the other two branches don't see it.
- **Suggested change:** Build the instance once and thread it. Concrete diff:

  ```python
  # main.py — around line 138-141:
  integration_cls, parsed_options = resolve.resolve_integration(
      integration, integration_options, json_output=json_output
  )
  integration = integration_cls()
  skills_dir = integration.resolve_skills_dir(parsed_options).as_posix()
  ```

  Then update `run_scaffold_steps`' signature to accept the instance:

  ```python
  # scaffold.py — around line 312-321:
  def run_scaffold_steps(
      *,
      resolved: ResolvedInvocation,
      integration: _integrations.SkillsIntegration,
      parsed_options: dict[str, str | bool],
      ...
  ) -> None:
      ...
      # 4) Wire the integration's setup() through the ledger.
      skills_target = project_root / integration.resolve_skills_dir(parsed_options)
      mkdir_tracked(skills_target, ledger)
      marker = skills_target / _integrations.SKILL_PLACEHOLDER_MARKER_NAME
      if not marker.exists():
          ledger.record_new_file(marker)
      integration.setup(project_root, manifest, parsed_options)
  ```

  And the call site in `main.run`:

  ```python
  scaffold.run_scaffold_steps(
      resolved=resolved,
      integration=integration,           # was integration_cls=integration_cls,
      parsed_options=parsed_options,
      ledger=ledger,
      json_output=json_output,
      warnings=warnings,
      author_name=authors[0],
  )
  ```

  No new test should be required — the existing `test_init_default.py` and `test_init_integrations.py` already exercise both `resolve_skills_dir` and `setup`. If you want a regression guard, monkeypatch `__init__` on `ClaudeIntegration` to count instances and assert it's called exactly once per `runner.invoke(...)`.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/commands/init/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/commands/init/conflict.py` | 96 % | 80 % | PASS |
| `src/bookwright/commands/init/envelope.py` | 97 % | 80 % | PASS |
| `src/bookwright/commands/init/git.py` | 98 % | 80 % | PASS |
| `src/bookwright/commands/init/main.py` | 95 % | 80 % | PASS |
| `src/bookwright/commands/init/resolve.py` | 100 % | 80 % | PASS |
| `src/bookwright/commands/init/scaffold.py` | 97 % | 80 % | PASS |
| `src/bookwright/commands/init/validate.py` | 95 % | 80 % | PASS |
| **Global (`src/bookwright/`)** | **97.48 %** | **80 %** | **PASS** |

Snapshot from `uv run pytest` on `1c6ad45`: 356 tests passed, no
unexpected skips. The uncovered branches in `main.py` (lines 219-221,
241) are the lazy `import shutil` inside `_rollback_and_cleanup` and one
arm of `classify_filesystem_failure` not reachable from the existing
test grid — neither is on the success path.

## 6. Boundary Security

| Area | Status | Notes |
|---|---|---|
| Path traversal | PASS | `BackupLedger._ensure_under_root` ([scaffold.py:90-94](../../src/bookwright/commands/init/scaffold.py#L90-L94)) rejects writes outside the resolved `project_root` with `TargetOutsideProjectRootError`; the `--integration-options="--skills-dir <path>"` boundary is enforced by iteration-3's `resolves_to_project_root` / `escapes_project_root` rules and pinned by [tests/commands/test_init_rollback.py::test_skills_dir_resolves_to_project_root_rolls_back](../../tests/commands/test_init_rollback.py#L290-L322). |
| Shell injection | PASS | All `subprocess.run` calls use the list-form, `shell=False` default ([git.py:87-94](../../src/bookwright/commands/init/git.py#L87-L94), [resolve.py:43-49](../../src/bookwright/commands/init/resolve.py#L43-L49)). No `os.system`, no `shell=True`, no string interpolation into argv. |
| Unsafe deserialization | PASS | No `yaml.load`, no `pickle.loads`, no `eval`/`exec` in init code. `json.loads` is used only for known-shape envelopes and the iteration-2 `Manifest.load` path. |
| Hardcoded secrets | PASS | The single hardcoded string `author@bookwright.local` ([git.py:21](../../src/bookwright/commands/init/git.py#L21)) is the documented fallback commit-author email, not a credential. |
| Untrusted-input crossing trust boundary | PASS | `PROJECT_NAME` is validated by FR-021a before any filesystem work ([validate.py:52-75](../../src/bookwright/commands/init/validate.py#L52-L75)); `--integration` and `--integration-options` are validated through the iteration-3 plugin layer before scaffolding begins. Jinja2 templates use `autoescape=False` + `StrictUndefined` and consume only package-bundled `.j2` files — no user-controlled template body. |

## 7. Inability-to-verify notes

- None. `pytest`, `ruff check`, `ruff format --check`, and `mypy --strict
  src tests` all ran clean during this audit. Coverage was measured by
  the project's own `pytest --cov` configuration in
  [pyproject.toml:69-71](../../pyproject.toml#L69-L71).
