# Quality Audit — 004-init-command

**Scope:** 103 changed files vs `main` (full branch, post-Phase-9 layout).
**Commit range:** `main..3fe2ed3`
**Date:** 2026-05-29
**Conventions discovered:** [.specify/memory/constitution.md](../../.specify/memory/constitution.md) (v1.1.0, ratified 2026-05-28), [CLAUDE.md](../../CLAUDE.md), [CONTRIBUTING.md](../../CONTRIBUTING.md)

This run audits the iteration-4 branch in its post-Phase-9 state — the
`commands/init.py` + flat `_init_*.py` siblings have been collapsed into a
`commands/init/` package, R1/R2 from the prior audit are closed, and the
quality gate is green (350 tests, 97% line coverage, `ruff check`, `ruff
format --check`, `mypy --strict` all clean). The findings below are the
residual signals that survived that cleanup.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH     | 0 |
| MEDIUM   | 2 |
| LOW      | 2 |
| **Total** | 4 |

Coverage gate: **PASS** (global 97.46% — threshold 80%, no module under 94%).

## 2. Conventions Compliance Matrix

One row per rule extracted from convention files. Grouped by source file.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … are forbidden as canonical storage." | [constitution.md:54-61](../../.specify/memory/constitution.md#L54-L61) | layout | PASS | Every resource under [src/bookwright/resources/project/](../../src/bookwright/resources/project/) is `.md`, `.md.j2`, `.gitkeep`, `.gitignore`. Vocabularies are `.ttl`. No binary blobs in the diff. |
| "Python 3.11+. No support for 3.10 or earlier." | [constitution.md:189](../../.specify/memory/constitution.md#L189) | dependency | PASS | [pyproject.toml:8](../../pyproject.toml#L8) `requires-python = ">=3.11"`. |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | [constitution.md:190-193](../../.specify/memory/constitution.md#L190-L193) | dependency | PASS | [pyproject.toml:20-31](../../pyproject.toml#L20-L31) lists exactly those ten — no additions. |
| "Build backend: hatchling. Lockfile: uv.lock committed." | [constitution.md:194-195](../../.specify/memory/constitution.md#L194-L195) | dependency | PASS | [pyproject.toml:36-38](../../pyproject.toml#L36-L38) + `uv.lock` tracked at repo root. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`. No exceptions." | [constitution.md:81-83](../../.specify/memory/constitution.md#L81-L83) | layout | PASS | Diff scopes 100% to `src/bookwright/**` and `tests/**`. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | [constitution.md:92-93](../../.specify/memory/constitution.md#L92-L93) | layout | PASS | Three commands: `check.py`, `version.py`, `init/`. Package form satisfies "module under `commands/<name>`". |
| "No source file (production or test) may exceed 500 lines." | [constitution.md:93-95](../../.specify/memory/constitution.md#L93-L95) | module-size | PASS | Largest production file in the diff: [src/bookwright/commands/init/scaffold.py](../../src/bookwright/commands/init/scaffold.py) at 408 lines. Largest test file: [tests/commands/test_init_helpers.py](../../tests/commands/test_init_helpers.py) at 349. |
| "Monolithic `cli.py` files that inline subcommand bodies are prohibited." | [constitution.md:95-96](../../.specify/memory/constitution.md#L95-L96) | layout | PASS | [src/bookwright/cli.py](../../src/bookwright/cli.py) is 17 lines, only wiring. |
| "Integrations MUST be implemented as subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. A monolithic `AGENT_CONFIG`-style dispatcher is explicitly forbidden." | [constitution.md:101-108](../../.specify/memory/constitution.md#L101-L108) | plugin-shape | PASS | `init.run` calls `integrations.get(key)` + `integration_cls().resolve_skills_dir(parsed_options)` ([main.py:153-156](../../src/bookwright/commands/init/main.py#L153-L156)). No `if key == "claude"` ladder anywhere. |
| "Bookwright MUST emit Agent Skills … nothing else. Writing to `.claude/commands/`, `.agents/commands/`, or any analogous … directory is prohibited." | [constitution.md:114-119](../../.specify/memory/constitution.md#L114-L119) | directory-ban | PASS | `grep -rn '\.claude/commands\|\.agents/commands\|\.cursor/commands' src/` returns zero. The only write under the integration's tree is `SkillsIntegration.setup()`'s placeholder marker. |
| "name < 64 chars, matching parent directory; description < 1024 chars; valid YAML frontmatter." | [constitution.md:127-136](../../.specify/memory/constitution.md#L127-L136) | frontmatter-constraint | N/A | No `SKILL.md` files generated in iteration 4 — the placeholder marker is exempt. Full skill materialization lands in iteration 9. |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`." | [constitution.md:144-145](../../.specify/memory/constitution.md#L144-L145) | coverage-threshold | PASS | `pytest --cov` reports **97.46%** global, every module ≥ 94% (see §5). |
| "CI MUST run pytest, ruff, and mypy strict on every push and pull request; a red bar blocks merge." | [constitution.md:149-150](../../.specify/memory/constitution.md#L149-L150) | workflow-step | PASS | All four gates run clean locally: `pytest` (350 passed), `ruff check`, `ruff format --check`, `mypy --strict src tests`. |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a `--json` flag and, when set, emit a single well-formed JSON document on stdout and nothing else." | [constitution.md:155-163](../../.specify/memory/constitution.md#L155-L163) | io-contract | PASS | Subprocess pins in [tests/commands/test_init_json_envelope.py](../../tests/commands/test_init_json_envelope.py) verify stdout purity on success + every documented failure mode; AST invariant in [tests/commands/test_init_ast_invariants.py](../../tests/commands/test_init_ast_invariants.py) pins no rogue `tomlkit.*` or `shlex.split` calls in the init package. |
| "Preset system … v0.2. GrafeoIndexer … v0.3. Multi-integration beyond claude/generic … v0.4. Extension system … v0.5. Export … v1.0." | [constitution.md:207-213](../../.specify/memory/constitution.md#L207-L213) | scope-ban | PASS | Diff introduces no `--preset` flag, no `GrafeoIndexer` reference, no third integration, no extension plumbing, no export subcommand. |
| "Workflow: /speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement." | [CLAUDE.md:33-52](../../CLAUDE.md#L33-L52) | workflow-step | PASS | All artifacts present in branch: `spec.md` (with Session 2026-05-29 clarifications), `plan.md`, `tasks.md` (all 46 ticked), `research.md`, `data-model.md`, `contracts/init_command.md`, `quickstart.md`, prior `review.md`. `git log --all --grep=Spec` shows the full pipeline trail (specify, clarify, plan, tasks, implement, quality-audit). |
| "specs/NNN-name/ governance files tracked on branch." | [CLAUDE.md:60-62](../../CLAUDE.md#L60-L62) | track-integrity | PASS | A.3 cross-check: every file in [specs/004-init-command/](../) (10 files including the prior `review.md` and both checklists) is in `git diff main...HEAD`. `git status --porcelain` is clean. |
| "Each iteration produces a feature branch `NNN-<short-name>` with its own specs/NNN-name/{spec,plan,tasks}.md." | [CLAUDE.md:33-46](../../CLAUDE.md#L33-L46) | layout | PASS | Branch is `004-init-command`, directory is `specs/004-init-command/`, the three core files are present. |
| "Source code, identifiers, commit messages, and the constitution itself are in English." | [CLAUDE.md:131-134](../../CLAUDE.md#L131-L134) | other | PASS | All new source files (`commands/init/*.py`, tests, contracts, plan) are in English. Spanish appears only in the user-authored design docs (out of scope for this branch). |
| "Pre-commit hooks (ruff format, ruff check, check-toml, check-yaml)." | [CONTRIBUTING.md:46-52](../../CONTRIBUTING.md#L46-L52) | workflow-step | PASS | `ruff check .` and `ruff format --check .` both green; no toml/yaml in the diff that pre-commit would reject. |

No `FAIL` rows. The Spec Kit pipeline integrity (A.3) and the workflow
trail (A.4) both pass — every governance artifact this branch produced
is committed and visible to `git diff`, and the workflow steps are
materialised through the expected artifacts in order.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A/B | MEDIUM | [src/bookwright/commands/init/envelope.py:50-56](../../src/bookwright/commands/init/envelope.py#L50-L56) | `ResolvedInvocation.git_status` is `Literal["initialized","skipped_by_flag","skipped_no_binary","skipped_existing_repo","pending"]` with default `"pending"`. The published contract ([contracts/init_command.md:134-135](contracts/init_command.md#L134-L135)) and data model ([data-model.md:94](data-model.md#L94)) both list only the four real values — `"pending"` is an internal scaffold sentinel that leaks into the validation surface. | Build the public `ResolvedInvocation` only when `git_status` is settled. Move the placeholder out of the Literal (e.g. construct the model after `run_scaffold_steps` decides the status; pass `git_status` as a constructor arg rather than relying on a default). Add a regression test that round-trips `init-options.json` via `InitOptionsRecord.model_validate(...)` and asserts `git_status != "pending"`. |
| R2 | B | MEDIUM | [src/bookwright/commands/init/main.py:191-207](../../src/bookwright/commands/init/main.py#L191-L207) | `except BaseException as exc:` catches `KeyboardInterrupt` and `SystemExit` (other than `typer.Exit`) and funnels them through `classify_filesystem_failure`, which always returns `("filesystem_error", 6, ...)` for non-matching types. A user hitting Ctrl-C mid-scaffold would see a `filesystem_error` envelope instead of the underlying interruption signal. | Narrow the catch to `except Exception as exc:` plus a separate `except (KeyboardInterrupt, SystemExit):` that runs `ledger.rollback()` + project-root cleanup and then re-raises without writing an envelope. Document the rollback-on-interrupt behaviour in the `init.run` docstring. |
| R3 | B | LOW | [tests/commands/test_init_options_record.py:85](../../tests/commands/test_init_options_record.py#L85) | Dead-code expression: `(target / ".bookwright_temp").write_text("temp", encoding="utf-8") if False else None`. The `if False else None` always evaluates to `None`; the write_text is unreachable. Looks like a leftover from an earlier draft. | Delete the line outright. If the temp file was needed as a fixture artifact, lift it into a real conditional or a parametrize id; otherwise it just confuses future readers. |
| R4 | B | LOW | [tests/commands/test_init_branches.py:94-103](../../tests/commands/test_init_branches.py#L94-L103) | `test_named_mode_reserved_slug` is named for the "slugifies to a reserved name" path but its body sends `"***"` (which slugifies to empty, tripping the `empty` rule) and its own docstring says *"Skip this — covered already by derive_slug raising on '***'"*. The test name no longer matches what it asserts. | Rename to `test_named_mode_slugifies_to_empty` (or similar) and update the docstring; or, if a true reserved-slug name path is still worth covering, replace the body with an input whose slug actually lands on a reserved name (e.g., assert that `derive_slug("c o n")` → `"c-o-n"` does NOT trip and document that as the boundary). |

## 4. Remediation Detail

### R1 — Internal "pending" sentinel leaks into `ResolvedInvocation` Literal

- **Where:** [src/bookwright/commands/init/envelope.py:50-56](../../src/bookwright/commands/init/envelope.py#L50-L56)
- **Why it matters:** [contracts/init_command.md:134-135](contracts/init_command.md#L134-L135) and [data-model.md:94](data-model.md#L94) both pin `git_status` to exactly four values (`initialized`, `skipped_by_flag`, `skipped_no_binary`, `skipped_existing_repo`). The implementation adds a fifth (`"pending"`) so the model can be constructed in [main.py:160-175](../../src/bookwright/commands/init/main.py#L160-L175) before the git step decides which of the four applies. The orchestrator faithfully overwrites the field via `model_copy` in [scaffold.py:380-386](../../src/bookwright/commands/init/scaffold.py#L380-L386), so the bug is latent — but the public validation surface now silently accepts a value that consumers MUST reject. Iteration 11 (introspection) or any agent that round-trips `init-options.json` through this Pydantic model would fail to flag a `pending` value, and a future code path that reorders the orchestration could write the sentinel to disk without any test or schema check catching it.
- **Suggested change:** Two options:
  1. **Prefer:** remove `"pending"` from the Literal and stop defaulting `git_status`. Have `init.run` compute `git_status` *before* constructing `ResolvedInvocation` (the four branches in `run_scaffold_steps` lines 379-386 can live in `main.run` after the rest of resolution, then be passed as a constructor arg). The model becomes write-once.
  2. **Acceptable:** keep the internal placeholder but split the model: an internal `_ScaffoldInvocation` with the 5-state Literal (used during orchestration) and a public `ResolvedInvocation` with the 4-state Literal (used in `success_envelope` and `InitOptionsRecord.options`). Convert one to the other right before the envelope/record steps.
  Either way, add `test_init_options_record.py::test_git_status_never_pending` that parametrises every documented invocation, reads `init-options.json` back, and asserts `record.options.git_status != "pending"`.

### R2 — `except BaseException` misclassifies KeyboardInterrupt/SystemExit

- **Where:** [src/bookwright/commands/init/main.py:191-207](../../src/bookwright/commands/init/main.py#L191-L207)
- **Why it matters:** The current shape catches every `BaseException`, including `KeyboardInterrupt` and bare `SystemExit`, and routes them through `classify_filesystem_failure`. That function only special-cases `BackupCreationError`, `PermissionError`, `GitInitError`, `TargetOutsideProjectRootError`, and `OSError`; everything else falls through to the trailing `("filesystem_error", 6, {"path": "", "errno": 0})` arm ([envelope.py:225-229](../../src/bookwright/commands/init/envelope.py#L225-L229)). The net effect: a user Ctrl-C mid-scaffold gets a JSON envelope claiming `filesystem_error` instead of dying with the signal. The rollback itself is desirable, but the classification is wrong and silently hides the real cause. There is no test for the interruption path, so the regression is undetectable today.
- **Suggested change:** Split the handler:

  ```python
  except (KeyboardInterrupt, SystemExit):
      ledger.rollback()
      if cleanup_project_root and project_root.exists():
          import shutil  # noqa: PLC0415 — local cleanup only
          shutil.rmtree(project_root, ignore_errors=True)
      raise
  except Exception as exc:
      ledger.rollback()
      if cleanup_project_root and project_root.exists():
          import shutil  # noqa: PLC0415 — local cleanup only
          shutil.rmtree(project_root, ignore_errors=True)
      if isinstance(exc, typer.Exit):
          raise
      code, exit_code, details = envelope.classify_filesystem_failure(exc)
      envelope.emit_error(...)
  ```

  `typer.Exit` is a `RuntimeError` subclass, so it stays caught by the `Exception` arm and the existing re-raise path is preserved. Add one test under `test_init_rollback.py` that raises `KeyboardInterrupt` from inside a monkeypatched `render_resource_tree` and asserts `pytest.raises(KeyboardInterrupt)` plus the empty `dirhash` afterwards.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/commands/init/__init__.py` | 100% | 80% | PASS |
| `src/bookwright/commands/init/conflict.py` | 96% | 80% | PASS |
| `src/bookwright/commands/init/envelope.py` | 97% | 80% | PASS |
| `src/bookwright/commands/init/git.py` | 98% | 80% | PASS |
| `src/bookwright/commands/init/main.py` | 94% | 80% | PASS |
| `src/bookwright/commands/init/resolve.py` | 100% | 80% | PASS |
| `src/bookwright/commands/init/scaffold.py` | 97% | 80% | PASS |
| `src/bookwright/commands/init/validate.py` | 95% | 80% | PASS |
| **Global (`src/bookwright/`)** | **97.46%** | **80%** | **PASS** |

Snapshot from `uv run pytest` on `3fe2ed3`: 350 tests passed, no skips
unrelated to git availability, no warnings.

## 6. Inability-to-verify notes

- None. `pytest`, `ruff check`, `ruff format --check`, and `mypy --strict
  src tests` all ran clean during this audit.
