# Quality Audit — 002-manifest-model

**Scope:** 51 changed files vs `main` (4 modified + 47 new across `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`, `specs/002-manifest-model/`, plus `pyproject.toml`, `uv.lock`)
**Commit range:** `75e3382` (main) → `fd9e59e` (HEAD)
**Date:** 2026-05-28
**Conventions discovered:** [.specify/memory/constitution.md](.specify/memory/constitution.md) v1.1.0 (binding), [CLAUDE.md](CLAUDE.md), [specs/002-manifest-model/{spec,plan,tasks,research,data-model,quickstart}.md](specs/002-manifest-model/), [specs/002-manifest-model/contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md)
**Prior audits:** earlier reviews flagged R1 (`schema_version` non-empty validator), R2 (`invalid_uri` IPv6 coverage), R3 (`empty_host` fixture coverage), R4 (`Manifest.dump` `RuntimeError` contract gap) as the four open MEDIUM items at `0429b09`. Commit `7f57f2c` closed all four — validator added, both fixtures + parametrised rows added, contract paragraph added. This audit re-runs the four passes against HEAD and confirms the closures, then reports the residual debt.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 5 |
| **Total** | 6 |

Coverage gate: **PASS**. `uv run pytest` (74 tests, 0 failures) → 95.72 % project, `bookwright.core` aggregate 95.7 %. Threshold = 80 % ([pyproject.toml:76](pyproject.toml#L76)); local iteration target = 90 %. `ruff check`, `ruff format --check`, `mypy --strict` all green.

**Headline:** the iteration is functionally complete, the constitutional gate is green, and every prior MEDIUM (R1–R4) is now closed in code with a regression test or contract paragraph. What is left is one MEDIUM single-source-of-truth nit on the two public enum constants (`BOOK_TYPES` / `BOOK_STATUSES`) and five LOW items — three are defensive / unreachable branches that the test suite does not exercise (manifest.py L336-337, L444-445; _translate.py L41-44), one is a small builder UX nit, and one is the prior R6 constitution Sync-Impact wording note. **None of these are spec violations or constitutional MUST failures, and none block closing the spec.** The branch is mergeable as-is; addressing the five LOWs is optional polish.

## 2. Conventions Compliance Matrix

Rules extracted in Pass A.1 from the discovered convention files. Every MUST is checked positively; `PASS` is as load-bearing as `FAIL`.

### `.specify/memory/constitution.md` (v1.1.0)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden as canonical storage." | constitution.md §I | layout | PASS | Diff contains only `.py`, `.toml`, `.md`, `.lock`. No binary canonical stores. |
| "The implementation language is Python 3.11+." | constitution.md §II | language | PASS | `requires-python = ">=3.11"` ([pyproject.toml:8](pyproject.toml#L8)). |
| "Introducing an additional runtime dependency requires an amendment to the dependency list." | constitution.md §II | dependency | PASS | `packaging>=23.0` added ([pyproject.toml:22](pyproject.toml#L22)); amendment `a685b9b` (1.0.0 → 1.1.0) lands first on the branch. |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | constitution.md Tech Constraints | dependency | PASS | [pyproject.toml:20-31](pyproject.toml#L20-L31) matches exactly. No additions beyond the amended set. |
| "Build backend: hatchling. Lockfile: uv.lock committed." | constitution.md Tech Constraints | dependency | PASS | `build-backend = "hatchling.build"` ([pyproject.toml:37](pyproject.toml#L37)); `uv.lock` tracked. |
| "All production code MUST live under `src/bookwright/`. All tests under `tests/`." | constitution.md §III | layout | PASS | New code only in `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | constitution.md §IV | layout | N/A | Iteration 2 adds no CLI subcommand. |
| "No source file (production or test) may exceed 500 lines." | constitution.md §IV | module-size | PASS | Largest source: [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py) at 452 lines. Largest test: [tests/core/test_load_valid.py](tests/core/test_load_valid.py) at 195 lines. All under cap. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. AGENT_CONFIG-style dispatcher forbidden." | constitution.md §V | plugin-shape | PASS | `[integration]` block read as opaque data (FR-022). `DEFAULT_SKILLS_DIR` is a 2-entry default-table used only inside `Manifest.build`, not a runtime dispatcher. |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/`, `.agents/commands/` is prohibited." | constitution.md §VI | directory-ban | PASS | `grep -r "\.claude/commands\|\.agents/commands" src/ tests/` returns nothing. |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification." | constitution.md §VII | frontmatter-constraint | N/A | No SKILL.md emitted in this iteration. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`. CI MUST run pytest, ruff, mypy strict on every push." | constitution.md §VIII | coverage-threshold | PASS | `uv run pytest` → 95.72 %. CI gate is `--cov-fail-under=80`. Local iteration target ≥ 90 % also met. |
| "Any CLI command meant for an agent MUST accept `--json` and emit a single JSON doc on stdout, nothing else." | constitution.md §IX | io-contract | PASS (shapes only) | No CLI subcommand added. FR-024 only requires the JSON shapes be ready; all five `to_json()` shapes are JSON-clean and verified via `json.dumps` round-trip in [tests/core/test_json_shapes.py](tests/core/test_json_shapes.py). Model layer never writes to stdout/stderr (pinned by `test_future_manifest_version_attaches_one_warning`'s `capsys` assertion). |
| "Section 16 design axioms MUST NOT be reopened in spec, plan, or task discussions." | constitution.md §X | scope-ban | PASS | Pydantic v2, rdflib (deferred), TOML, Agent Skills, plain text — all honoured; no axiom reopened. |
| "v0 deliberately defers: Preset / GrafeoIndexer / integrations beyond claude+generic / Extension system / EPUB-PDF export." | constitution.md Scope & Release | scope-ban | PASS | None pulled forward. The `cursor` integration_key exercised at [tests/core/test_build.py:122-146](tests/core/test_build.py#L122-L146) only proves the *unknown-integration_key* failure path, not a plumbing addition. |
| "Amendments MUST be a dedicated PR that updates constitution.md, bumps the version, updates Sync Impact, and propagates changes." | constitution.md Governance | workflow-step | PASS (cosmetic gap → L5) | Commit `a685b9b` lands the 1.0.0 → 1.1.0 amendment first. Sync Impact wording overstates the delta — see L5. |

### `CLAUDE.md` (project instructions)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Layout: `src/bookwright/…` for production code, `tests/` at the root. No exceptions." | CLAUDE.md "Stack" | layout | PASS | Verified above. |
| "Per-command modules: each CLI subcommand in its own file under `src/bookwright/commands/<name>.py`, ≤500 lines." | CLAUDE.md "Stack" | module-size | N/A | No new subcommand. |
| "Run iteration via `/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement`." | CLAUDE.md "How work is done" | workflow-step | PASS | See A.4. |
| "Monolithic `AGENT_CONFIG`-style dispatcher is forbidden." | CLAUDE.md "Domain knobs" | plugin-shape | PASS | No dispatcher introduced. |
| "Out of v0 scope — do not implement: Preset / GrafeoIndexer / Copilot/Gemini/Cursor / Extensions / EPUB-PDF." | CLAUDE.md "Out of v0 scope" | scope-ban | PASS | None present. |
| "Source code, identifiers, commit messages, and the constitution itself are in **English**." | CLAUDE.md "Language" | other | PASS | All new module docstrings, identifiers, commit messages in English. |
| "Spec Kit specifics — skill names are hyphenated; `extensions.yml` hook entries use dot form." | CLAUDE.md "Spec Kit" | other | N/A | No skill/hook changes this iteration. |

### A.3 Track-integrity for governance / feature-owned directories

`specs/002-manifest-model/` — `find specs/002-manifest-model -type f | wc -l` == `git ls-files specs/002-manifest-model/ | wc -l` (10 files, all tracked, all in the branch diff or inherited from default). No untracked or `.gitignore`-orphaned governance files. **PASS.**

`src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/` — every file present on disk appears in `git diff main...HEAD --name-only` and there is no leftover under those trees that is not in the branch diff. **PASS.**

### A.4 Workflow-trail integrity

Spec Kit sequence: `specify → clarify → plan → tasks → analyze → implement`.

| Step | Artefact | Present | Notes |
|---|---|---|---|
| specify | spec.md | yes | 5 user stories, 24 FRs, 6 entities, 7 SCs. |
| clarify | "Clarifications / Session 2026-05-28" in spec.md | yes | 5 Q&A entries. |
| plan | plan.md | yes | Constitution Check ✅ all 10, Complexity Tracking, post-design re-check. |
| tasks | tasks.md | yes | 35 tasks across 8 phases, all `[X]`. |
| analyze | (no standalone file) | partial | Bundled in commit `017f40b`; `checklists/requirements.md` fully ticked as the actionable output. Acceptable. |
| implement | `src/bookwright/core/*`, `tests/core/*`, `src/bookwright/resources/templates/manifest.template.toml` | yes | 12 implementation commits (`e7ebaf6` → `fd9e59e`). |

**PASS.** No downstream-artefact-without-upstream-artefact case detected.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | MEDIUM | [src/bookwright/core/manifest.py:51-55](src/bookwright/core/manifest.py#L51-L55), [src/bookwright/core/manifest.py:212](src/bookwright/core/manifest.py#L212), [src/bookwright/core/manifest.py:218](src/bookwright/core/manifest.py#L218) | DRY violation: `BOOK_TYPES` / `BOOK_STATUSES` frozensets are declared at module level **and** the same five-value tuples are inlined into `Literal[...]` annotations on `BookBlock.type` / `BookBlock.status`. Two sources of truth for the same enumeration; a future "add genre `screenplay`" edit can land in one place and not the other, and `mypy --strict` will not catch the drift (the annotation drives type-check, the constant drives `__all__`/public-API consumers). Both constants are re-exported in `bookwright.core.__all__`, so they ARE the public contract. | Pick one source of truth and derive the other. Cheapest shape: `BookType = Literal["novel", "essay", "memoir", "non-fiction-narrative", "other"]`, then `BOOK_TYPES: frozenset[str] = frozenset(typing.get_args(BookType))` at module level; annotate `BookBlock.type: BookType`. Same shape for `BookStatus` / `BOOK_STATUSES`. Public surface unchanged, drift impossible, no tests need updating. |
| R2 | D | LOW | [src/bookwright/core/manifest.py:334-344](src/bookwright/core/manifest.py#L334-L344) | The `installed_not_pep440` defensive branch in `_check_cli_floor` is uncovered (lines 336-337 in the coverage report). Fires only when the installed CLI's own `__version__` fails PEP 440 parsing — possible during local dev where `bookwright.__version__` is hand-edited to e.g. `"0.0.1-dev"`. Rule id is already in the published taxonomy ([contracts/manifest_api.md:281](specs/002-manifest-model/contracts/manifest_api.md#L281)) under `installed_too_old`-adjacent. Same item as prior R5. | Add a single test in [test_version_gate.py](tests/core/test_version_gate.py): `installed_version("v1")` then `Manifest.load(load_fixture("valid_minimal.toml"))` → expect `ManifestValidationError` with `rule_id == "bookwright.cli_version_min.installed_not_pep440"`. Closes the coverage gap and pins the contract. |
| R3 | D | LOW | [src/bookwright/core/manifest.py:442-445](src/bookwright/core/manifest.py#L442-L445) | The `os.link` `FileExistsError → ManifestOverwriteError` branch in `dump()` (the TOCTOU close — race between the early `target.exists()` check and the link call) is real safety code, but no test pins it. Coverage shows lines 444-445 uncovered. The "atomicity preserves prior contents" test ([test_write.py:107-135](tests/core/test_write.py#L107-L135)) covers the `os.replace` failure path, not this one. | Optional: add a small test that monkey-patches `os.link` to raise `FileExistsError`, asserts a `ManifestOverwriteError` is raised, and asserts the tmp file was cleaned up. Closes a 2-line coverage gap and pins documented FR-019 behaviour. |
| R4 | B | LOW | [src/bookwright/core/_translate.py:41-44](src/bookwright/core/_translate.py#L41-L44) | Defensive branch in `_format_loc` for a Pydantic location tuple that starts with an `int` (`if parts: parts[-1] = …; else: parts.append(f"[{piece}]")`). Pydantic never emits this shape — locations always lead with a field/block name string — so the `else` arm is dead. Coverage shows lines 41-44 uncovered. Dead defensive code is technical debt: a future reader cannot tell whether it's reachable, and refactors may carry it forward needlessly. | Delete the `else: parts.append(f"[{piece}]")` branch and replace with `assert parts, "Pydantic loc never starts with an int"`. Or, if you'd rather keep the defensive shape, add a unit test that constructs a `pydantic.ValidationError` with a leading-int loc to pin the contract — but the assert is cheaper and clearer. |
| R5 | A | LOW | [.specify/memory/constitution.md:9-19](.specify/memory/constitution.md#L9-L19) | The Sync Impact Report for the 1.0.0 → 1.1.0 amendment reads as if all 10 principles are newly defined ("Principles defined (all new, no renames): I. Plain Text … X. Design Document Axioms"). For a MINOR amendment, the Sync Impact should describe the *delta* (added `packaging>=23.0` to Tech Constraints), not the original ratification scope. Cosmetic but confusing for the audit trail. Same item as prior R6. | Trim the "Principles defined / Added sections" subsections in the Sync Impact header to a single line: *"MINOR change: `packaging>=23.0` added to the Technical Constraints runtime dependency list (Principle II), required by FR-012 PEP 440 ordering."* Keep the rest of the constitution body unchanged. |
| R6 | B | LOW | [src/bookwright/core/_build.py:78-81](src/bookwright/core/_build.py#L78-L81) | When `Manifest.build(...)` receives more than one unknown keyword argument, only the first (in sorted order) is named in the raised `TypeError` — the others are hidden until the first is fixed. Friendlier UX would list all unknowns at once (mirroring FR-011's "surface all errors" stance for `ManifestValidationError`). Minor; not a contract violation (FR-015 only says "raise a programming-error exception immediately"). | One-line change: `raise TypeError(f"build() got unexpected keyword argument(s): {sorted(unknown)}")`. No test change strictly required; the existing assertion `assert "flavor" in str(exc_info.value)` still passes. |

## 4. Remediation Detail

No CRITICAL or HIGH findings. R1 is the only MEDIUM. The five LOWs are minor polish — three coverage / dead-branch items, one builder-UX nit, one constitution-housekeeping note. **None of these block closing the spec.**

### R1 — DRY duplication: BOOK_TYPES / BOOK_STATUSES vs Literal annotations

- **Where:** [src/bookwright/core/manifest.py:51-55, 212, 218](src/bookwright/core/manifest.py#L51-L55)
- **Why it matters:** Two parallel declarations for the same five (resp. five) enum values. Both are part of the public API (`BOOK_TYPES` and `BOOK_STATUSES` are in `bookwright.core.__all__`; the `Literal[…]` annotations drive `mypy --strict`). A future edit to one without the other ships an inconsistent enum to consumers and `mypy` will not catch the drift. The data-model.md already documents both ([specs/002-manifest-model/data-model.md:102, 108](specs/002-manifest-model/data-model.md#L102), [108](specs/002-manifest-model/data-model.md#L108)), so the doc is the third copy.
- **Suggested change:**
  ```python
  from typing import Literal, get_args
  BookType = Literal["novel", "essay", "memoir", "non-fiction-narrative", "other"]
  BookStatus = Literal["idea", "structuring", "drafting", "revising", "done"]
  BOOK_TYPES: frozenset[str] = frozenset(get_args(BookType))
  BOOK_STATUSES: frozenset[str] = frozenset(get_args(BookStatus))
  # then in BookBlock:
  type: BookType
  status: BookStatus = "drafting"
  ```
  Public surface (`BOOK_TYPES`, `BOOK_STATUSES`) unchanged. Drift impossible. No test changes required; `test_load_valid.py::test_load_accepts_every_book_type` already parametrises over `sorted(BOOK_TYPES)`.

## 5. Coverage Detail

`uv run pytest --cov=bookwright --cov-report=term-missing` (matches CI gate at [pyproject.toml:76](pyproject.toml#L76)).

| Module | Stmts | Miss | Branch | Cover | Status | Missing lines |
|---|---|---|---|---|---|---|
| `bookwright/core/__init__.py` | 3 | 0 | 0 | 100 % | PASS | — |
| `bookwright/core/_build.py` | 42 | 0 | 10 | 100 % | PASS | — |
| `bookwright/core/_translate.py` | 34 | 3 | 14 | 88 % | PASS | 41-44 (R4: dead leading-int branch in `_format_loc`) |
| `bookwright/core/errors.py` | 55 | 1 | 2 | 96 % | PASS | 82 (defensive `ValueError` on empty failures tuple; internal callers always pass non-empty) |
| `bookwright/core/iso639_1.py` | 3 | 0 | 0 | 100 % | PASS | — |
| `bookwright/core/manifest.py` | 212 | 5 | 38 | 98 % | PASS | 336-337 (R2 `installed_not_pep440`), 416 (RuntimeError on bare-construction dump — unreachable from supported entry points, contract-documented), 444-445 (R3 `os.link` TOCTOU close — race-window only) |
| **`bookwright.core` aggregate** | **349** | **9** | **64** | **~95.7 %** | **PASS** ≥ 90 % spec target |
| Iteration-1 modules (`cli.py`, `commands/check.py`, `commands/version.py`, `__main__.py`) | 65 | 4 | 12 | ~94 % | PASS | (out of this iteration's scope) |
| **Total `bookwright/`** | **415** | **13** | **76** | **95.72 %** | **PASS** ≥ 80 % CI gate |

Every remaining miss is either covered by a finding above (R2, R3, R4) or a defensive / unsupported-call-path branch documented in the contract.

## 6. Inability-to-verify notes

- Could not run the GitHub Actions matrix locally; verified each gate independently (`uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict`). Per CI `tests.yml`, these are the same four commands the matrix runs.
- `[integration].key` validity against the future v0 registry (`claude` | `generic`) is intentionally NOT the model's job (FR-022, deferred to iteration 3). The model's "non-empty string is fine" stance is correct here, not a finding.
- The `RuntimeError` raise site in `Manifest.dump` (line 416) covers an unsupported call path (`Manifest(...)` direct construction); the contract pins it at [contracts/manifest_api.md:145-149](specs/002-manifest-model/contracts/manifest_api.md#L145-L149) as "unreachable from contract-compliant code." Verifying unreachability is a reading of the code, not a test result — but the contract closes the gap to a reader's satisfaction.

## 7. Verdict on closing the spec

The user's three closure criteria, evaluated against HEAD (`fd9e59e`):

| Criterion | Verdict | Evidence |
|---|---|---|
| Implementation follows software-engineering best practices | **MET** | SOLID/DRY/KISS/YAGNI clean except for R1 (single MEDIUM, see §4). Test pyramid present (74 tests, 8 files mirroring source layout). All linters/type-checkers green. Module-size ceiling respected (largest source 452/500 lines). |
| Implementation adjusts to design or improves it | **MET** | Every FR-001..FR-024 maps to at least one test ([tests/core/](tests/core/)). The `data-model.md:84` schema_version non-empty rule, originally missing in code, is now enforced ([manifest.py:144-153](src/bookwright/core/manifest.py#L144-L153)) — a real improvement over the prior state. The contract (`manifest_api.md`) was tightened with the forward-compat-boundary and dump-mutation-semantics paragraphs as part of this iteration, pinned by regression tests. |
| No technical debt | **MOSTLY MET** | One MEDIUM (R1, single source of truth for the enum constants) is the only nontrivial residue. The five LOWs are coverage / dead-branch / cosmetic items that are bounded, named, and documented — not silent debt. Strictly speaking they exist, but they are all 1-to-5-line edits and none affect users of the public API. |

**Closing recommendation:** The spec is closable as-is. R1 is worth one extra commit because it touches the *public* enum constants and the fix is mechanical and risk-free (use `typing.get_args`). The five LOWs can be deferred to a follow-up housekeeping pass or addressed alongside iteration 3. If the team wants a strictly zero-debt close, do R1 + R2 + R4 in one tidy commit (≈ 20 lines diff, no API change) and merge.
