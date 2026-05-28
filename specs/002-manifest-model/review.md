# Quality Audit — 002-manifest-model

**Scope:** 52 changed files vs `main` (4 modified + 48 new across `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`, `specs/002-manifest-model/`, plus `pyproject.toml`, `uv.lock`)
**Commit range:** `75e3382` (main) → `dceb590` (HEAD)
**Date:** 2026-05-28
**Conventions discovered:** [.specify/memory/constitution.md](.specify/memory/constitution.md) v1.1.0 (binding), [CLAUDE.md](CLAUDE.md), [specs/002-manifest-model/{spec,plan,tasks,research,data-model,quickstart}.md](specs/002-manifest-model/), [specs/002-manifest-model/contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md)
**Prior audits:** the audit at `68f241d` (refreshing `fd9e59e`) flagged six findings: R1 (MEDIUM, `BOOK_TYPES`/`BOOK_STATUSES` single source of truth), R2 (LOW, `installed_not_pep440` coverage), R3 (LOW, `os.link` TOCTOU FileExistsError coverage), R4 (LOW, `_format_loc` dead defensive branch), R5 (LOW, constitution Sync Impact wording), R6 (LOW, builder UX for multiple unknown kwargs). Commit `9753ebf` closed R1 (via `typing.get_args`), R2 (test_installed_not_pep440_is_rejected), and R4 (assert in `_format_loc`). A fresh `/code-review xhigh` pass against `68f241d` surfaced nine additional findings — eight net-new plus one overlap with R6. Commit `dceb590` closes all nine of those new findings *and* the overlapping R6. This audit re-runs the four passes against HEAD and reports the residual debt.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 2 |
| **Total** | 2 |

Coverage gate: **PASS**. `uv run pytest` (89 tests, 0 failures) → 96.84 % project, `bookwright.core` aggregate ~97 %. Threshold = 80 % ([pyproject.toml:76](pyproject.toml#L76)); local iteration target = 90 %. `ruff check`, `ruff format --check`, `mypy --strict` all green.

**Headline:** the iteration is functionally complete and constitutionally green. Every MEDIUM raised across both audits is closed. What is left is two LOW housekeeping items — R1 (a 2-line coverage gap on the `os.link` FileExistsError race-close, inherited from the prior audit) and R2 (a constitution Sync Impact wording note, also inherited). **None of these are spec violations or constitutional MUST failures, and none block closing the spec or merging the branch.** Closing them is 1-to-5-line edits and pure optional polish.

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
| "No source file (production or test) may exceed 500 lines." | constitution.md §IV | module-size | PASS | Largest source: [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py) at 475 lines. Largest test: [tests/core/test_build.py](tests/core/test_build.py) at 252 lines. All under cap. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. AGENT_CONFIG-style dispatcher forbidden." | constitution.md §V | plugin-shape | PASS | `[integration]` block read as opaque data (FR-022). `DEFAULT_SKILLS_DIR` is a 2-entry default-table used only inside `Manifest.build`, not a runtime dispatcher. |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/`, `.agents/commands/` is prohibited." | constitution.md §VI | directory-ban | PASS | `grep -r "\.claude/commands\|\.agents/commands" src/ tests/` returns nothing. |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification." | constitution.md §VII | frontmatter-constraint | N/A | No SKILL.md emitted in this iteration. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`. CI MUST run pytest, ruff, mypy strict on every push." | constitution.md §VIII | coverage-threshold | PASS | `uv run pytest` → 96.84 %. CI gate is `--cov-fail-under=80`. Local iteration target ≥ 90 % also met. |
| "Any CLI command meant for an agent MUST accept `--json` and emit a single JSON doc on stdout, nothing else." | constitution.md §IX | io-contract | PASS (shapes only) | No CLI subcommand added. FR-024 only requires the JSON shapes be ready; all five `to_json()` shapes are JSON-clean and verified via `json.dumps` round-trip in [tests/core/test_json_shapes.py](tests/core/test_json_shapes.py). Model layer never writes to stdout/stderr (pinned by `test_future_manifest_version_attaches_one_warning`'s `capsys` assertion). |
| "Section 16 design axioms MUST NOT be reopened in spec, plan, or task discussions." | constitution.md §X | scope-ban | PASS | Pydantic v2, rdflib (deferred), TOML, Agent Skills, plain text — all honoured; no axiom reopened. |
| "v0 deliberately defers: Preset / GrafeoIndexer / integrations beyond claude+generic / Extension system / EPUB-PDF export." | constitution.md Scope & Release | scope-ban | PASS | None pulled forward. |
| "Amendments MUST be a dedicated PR that updates constitution.md, bumps the version, updates Sync Impact, and propagates changes." | constitution.md Governance | workflow-step | PASS (cosmetic gap → R2) | Commit `a685b9b` lands the 1.0.0 → 1.1.0 amendment first. Sync Impact wording overstates the delta — see R2. |

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

`specs/002-manifest-model/` — every file on disk appears in `git ls-files`; no untracked or `.gitignore`-orphaned governance files. **PASS.**

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
| implement | `src/bookwright/core/*`, `tests/core/*`, `src/bookwright/resources/templates/manifest.template.toml` | yes | 14 implementation commits (`e7ebaf6` → `dceb590`). |

**PASS.** No downstream-artefact-without-upstream-artefact case detected.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | D | LOW | [src/bookwright/core/manifest.py:453-456](src/bookwright/core/manifest.py#L453-L456) | The `os.link` `FileExistsError → ManifestOverwriteError` branch in `dump()` (the TOCTOU close — race between the early `target.exists()` check and the link call) is real safety code, but no test pins it. Coverage shows lines 455-456 uncovered. The "atomicity preserves prior contents" test ([test_write.py:107-135](tests/core/test_write.py#L107-L135)) covers the `os.replace` failure path; `test_dump_no_overwrite_swallows_tmp_unlink_failure` ([test_write.py:159-200](tests/core/test_write.py#L159-L200)) exercises the post-link unlink path. Neither triggers a `FileExistsError` from `os.link` itself. Inherited from prior audit's R3. | Optional: monkey-patch `os.link` to raise `FileExistsError`, assert `ManifestOverwriteError` is raised, and that the tmp file is cleaned up. Closes a 2-line coverage gap and pins documented FR-019 behaviour. |
| R2 | A | LOW | [.specify/memory/constitution.md:9-19](.specify/memory/constitution.md#L9-L19) | The Sync Impact Report for the 1.0.0 → 1.1.0 amendment reads as if all 10 principles are newly defined ("Principles defined (all new, no renames): I. Plain Text … X. Design Document Axioms"). For a MINOR amendment, the Sync Impact should describe the *delta* (added `packaging>=23.0` to Tech Constraints), not the original ratification scope. Cosmetic but confusing for the audit trail. Inherited from prior audit's R5. | Trim the "Principles defined / Added sections" subsections in the Sync Impact header to a single line: *"MINOR change: `packaging>=23.0` added to the Technical Constraints runtime dependency list (Principle II), required by FR-012 PEP 440 ordering."* Keep the rest of the constitution body unchanged. |

## 4. Closures recorded since the last audit

Both `9753ebf` (refactor) and `dceb590` (fix) landed since `68f241d`. Together they close every CRITICAL/HIGH/MEDIUM finding raised across the audit history.

### Closed by `9753ebf` (prior audit R1, R2, R4)
- **R1 MEDIUM (BOOK_TYPES / BOOK_STATUSES single source of truth):** `BookType` / `BookStatus` are now `Literal[...]` and `BOOK_TYPES` / `BOOK_STATUSES` derive from them via `typing.get_args` ([manifest.py:51-55](src/bookwright/core/manifest.py#L51-L55)). Public surface unchanged; drift impossible.
- **R2 LOW (installed_not_pep440 coverage):** [test_version_gate.py::test_installed_not_pep440_is_rejected](tests/core/test_version_gate.py) pins the contract rule.
- **R4 LOW (_format_loc dead branch):** Replaced the `else` arm with `assert parts, "Pydantic loc never starts with an int"` ([_translate.py:41](src/bookwright/core/_translate.py#L41)). Defensive shape kept; reader-confusion resolved.

### Closed by `dceb590` (this commit — 9 findings from a fresh `/code-review xhigh` against `68f241d`)
- **#1 HIGH (None overrides leak `tomlkit.ConvertError`):** [_build.py:99-100](src/bookwright/core/_build.py#L99-L100) filters out `None` values from `overrides` up-front. Eight new parametrised regression cases in [test_build.py::test_none_override_is_treated_as_default](tests/core/test_build.py).
- **#2 MEDIUM (Windows newline translation breaks FR-020):** [manifest.py:443](src/bookwright/core/manifest.py#L443) passes `newline=""` to `os.fdopen`. Pinned by [test_write.py::test_dump_uses_lf_line_endings](tests/core/test_write.py).
- **#3 MEDIUM (FR-021 violated when post-`os.link` unlink fails):** Best-effort cleanup with `contextlib.suppress(OSError)` ([manifest.py:464-465](src/bookwright/core/manifest.py#L464-L465)); a failing `os.unlink` after a successful `os.link` no longer raises a phantom failure. Pinned by [test_write.py::test_dump_no_overwrite_swallows_tmp_unlink_failure](tests/core/test_write.py).
- **#4 MEDIUM (misleading `not_pep440` rule from `build()` when installed CLI is broken):** [_build.py:113-122](src/bookwright/core/_build.py#L113-L122) validates `installed_version` is PEP 440 *before* substituting and raises `RuntimeError` that names the environment. Pinned by [test_build.py::test_non_pep440_installed_version_without_override_raises_runtime_error](tests/core/test_build.py) and the explicit-override counterpart that still surfaces `installed_not_pep440`.
- **#5 LOW (schema_version accepts surrounding whitespace):** [manifest.py:144-160](src/bookwright/core/manifest.py#L144-L160) adds rule `bookwright.schema_version.whitespace`; new fixture [invalid_bookwright_schema_version_whitespace.toml](tests/core/fixtures/invalid_bookwright_schema_version_whitespace.toml) and a parametrised row in [test_load_invalid.py](tests/core/test_load_invalid.py) pin it.
- **#6 LOW (cleanup `os.unlink` masks original exception):** [manifest.py:471](src/bookwright/core/manifest.py#L471) widens the suppress from `FileNotFoundError` to `OSError`.
- **#7 LOW (only first unknown override kwarg surfaced — overlapped with prior R6):** [_build.py:94-97](src/bookwright/core/_build.py#L94-L97) lists every unknown kwarg in one `TypeError`. Pinned by [test_build.py::test_multiple_unknown_overrides_are_all_reported](tests/core/test_build.py).
- **#8 cleanup (duplicate `_BUILD_OVERRIDE_ALLOWLIST` frozenset):** dropped — the table is now the single source of truth.
- **#9 efficiency (template re-read on every `build()`):** [_build.py:53-58](src/bookwright/core/_build.py#L53-L58) caches the template text with `@functools.cache`; each call still re-parses for an independent mutable document.

## 5. Coverage Detail

`uv run pytest --cov=bookwright --cov-report=term-missing` (matches CI gate at [pyproject.toml:76](pyproject.toml#L76)).

| Module | Stmts | Miss | Branch | Cover | Status | Missing lines |
|---|---|---|---|---|---|---|
| `bookwright/core/__init__.py` | 3 | 0 | 0 | 100 % | PASS | — |
| `bookwright/core/_build.py` | 51 | 0 | 12 | 100 % | PASS | — |
| `bookwright/core/_translate.py` | 33 | 2 | 12 | 93 % | PASS | 41-42 (defensive int-loc branch; `assert` + index splice — Pydantic never emits this shape, kept as a contract assertion) |
| `bookwright/core/errors.py` | 55 | 1 | 2 | 96 % | PASS | 82 (defensive `ValueError` on empty failures tuple; internal callers always pass non-empty) |
| `bookwright/core/iso639_1.py` | 3 | 0 | 0 | 100 % | PASS | — |
| `bookwright/core/manifest.py` | 218 | 3 | 40 | 98 % | PASS | 423 (RuntimeError on bare-construction dump — unreachable from supported entry points, contract-documented), 455-456 (R1 `os.link` TOCTOU close — race-window only) |
| **`bookwright.core` aggregate** | **363** | **6** | **66** | **~98 %** | **PASS** ≥ 90 % spec target |
| Iteration-1 modules (`cli.py`, `commands/check.py`, `commands/version.py`, `__main__.py`) | 65 | 4 | 12 | ~94 % | PASS | (out of this iteration's scope) |
| **Total `bookwright/`** | **429** | **10** | **78** | **96.84 %** | **PASS** ≥ 80 % CI gate |

Every remaining miss is either covered by R1 or a defensive / unsupported-call-path branch documented in the contract or this audit.

## 6. Inability-to-verify notes

- Could not run the GitHub Actions matrix locally; verified each gate independently (`uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict`). Per CI `tests.yml`, these are the same four commands the matrix runs.
- The Windows newline-translation fix (#2 above) is verified on macOS by asserting the dumped bytes contain no `\r`. The Windows-specific failure mode (`\n` → `\r\n` on text-mode write) cannot be reproduced on this platform; the assertion is the cheapest cross-platform pin.
- The `RuntimeError` raise site in `Manifest.dump` (line 423) covers an unsupported call path (`Manifest(...)` direct construction); the contract pins it at [contracts/manifest_api.md:145-149](specs/002-manifest-model/contracts/manifest_api.md#L145-L149) as "unreachable from contract-compliant code." Verifying unreachability is a reading of the code, not a test result.

## 7. Verdict on closing the spec

The user's three closure criteria, evaluated against HEAD (`dceb590`):

| Criterion | Verdict | Evidence |
|---|---|---|
| Implementation follows software-engineering best practices | **MET** | SOLID/DRY/KISS/YAGNI clean. Zero MEDIUM and zero HIGH residue. Test pyramid present (89 tests, 8 files mirroring source layout). All linters/type-checkers green. Module-size ceiling respected (largest source 475/500 lines). |
| Implementation adjusts to design or improves it | **MET** | Every FR-001..FR-024 maps to at least one test. The forward-compat-boundary and dump-mutation-semantics paragraphs in `contracts/manifest_api.md` were tightened in iteration 2 and remain pinned by regression tests. The `dceb590` fix wave added two new contractual rules (`schema_version.whitespace`, `RuntimeError` on broken installed CLI) and turned three previously latent footguns (None overrides, Windows newline drift, post-link FR-021 violation) into pinned regressions. |
| No technical debt | **MET (modulo two LOWs)** | Both residual LOWs (R1 `os.link` TOCTOU coverage, R2 constitution Sync Impact wording) are bounded, named, and documented — not silent debt. R1 is a 2-line coverage gap; R2 is a cosmetic note. Strictly speaking they exist, but they are 1-to-5-line edits and neither affects users of the public API. |

**Closing recommendation:** The spec is closable as-is. Both remaining LOWs are 100 % optional polish — R1 closes a defensive coverage gap, R2 is a constitution-housekeeping reword. Either land them in a follow-up tidy commit or merge as-is; the branch is mergeable in either form.
