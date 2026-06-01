# Quality Audit — 006-graph-indexer

**Scope:** 22 changed files vs `main` (17 source/test/config + 5 spec artifacts)
**Commit range:** `main`..`7424f23`
**Date:** 2026-06-01
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.2.0), `CONTRIBUTING.md`, `pyproject.toml`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 0 |
| LOW | 4 |
| **Total** | 5 |

Coverage gate: **PASS** (0 changed modules below threshold; threshold = 80%, total 96.41%, 508 tests pass). `ruff check`, `ruff format --check`, and `mypy --strict` all clean (130 files).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden as canonical storage" | `constitution.md:47` | layout | PASS | Output is `bible/graph.ttl` (Turtle); v0 writes no cache (`build.py` `--force` is a no-op). |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | `constitution.md:64` | dependency | PASS | `pyyaml>=6.0` added to `pyproject.toml:26`; constitution amended 1.1.0→1.2.0 (Sync Impact Report `:4`); `"yaml"` added to `RUNTIME_MODULES` (`check.py:21`). |
| "Runtime dependencies (minimum set): jinja2, packaging, … pyyaml, rdflib, rich, tomlkit, typer, uuid-utils" | `constitution.md:181` | dependency | PASS | `pyproject.toml:20-32` matches the list exactly; no extra runtime dep introduced. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`." | `constitution.md:72` | layout | PASS | New code under `src/bookwright/{indexers,io}/` + `commands/graph/`; all new tests under `tests/`. |
| "Each CLI subcommand MUST live in its own module … No source file … may exceed 500 lines" | `constitution.md:83` | module-size | PASS | `build.py` (119), `query.py` (87) separate modules; largest changed file `io/bible.py` = 347 lines. |
| "Integrations MUST be implemented as subclasses … registered in `INTEGRATION_REGISTRY` … monolithic dispatcher … forbidden" | `constitution.md:94` | plugin-shape | PASS | Engine seam mirrors the shape: `INDEXER_REGISTRY` + `resolve_indexer()` (`indexers/__init__.py:19-32`); no if/elif dispatcher. |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" | `constitution.md:107` | directory-ban | N/A | This iteration emits no skills; grep finds no writes to `*/commands/` dirs. |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" | `constitution.md:119` | frontmatter-constraint | N/A | No `SKILL.md` generated this iteration. |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:135` | coverage-threshold | PASS | 96.41% total; lowest changed module `io/bible.py` = 88%. |
| "CI MUST run pytest, ruff, and mypy strict on every push and pull request" | `constitution.md:140` | io-contract | PASS | `pyproject.toml:79-81` wires `--cov-fail-under=80`; all four gates green locally. |
| "Any CLI command … MUST accept a `--json` flag and … emit a single … JSON document on stdout and nothing else" | `constitution.md:148` | io-contract | PASS | `build`/`query` accept `--json`; `envelope.emit_json` writes one line to stdout; prose via `Console(stderr=True)`; `test_json_contract.py` asserts the invariant. |
| "Exit codes MUST be non-zero on error even when `--json` is set" | `constitution.md:153` | io-contract | PASS | `build.py:49-58` (exit 2/3), `query.py:46-49` (exit 2/3) raise `typer.Exit` before/independent of envelope. |
| Design axioms (rdflib over Grafeo in v0; GOLEM ontology) "MUST NOT be reopened" | `constitution.md:159` | scope-ban | PASS | `RdflibIndexer` is the only registered engine; SC-001 frozen-vocab closure tested (`test_build.py:68`). |
| "GrafeoIndexer and vector search — v0.3 … MUST NOT be pulled into v0 scope" | `constitution.md:201` | scope-ban | PASS | `GrafeoIndexer` intentionally **not** registered (`indexers/__init__.py:5-6`); no vector-search plumbing. |
| "Build backend: hatchling. Lockfile: uv.lock committed" | `constitution.md:185` | dependency | PASS | `pyproject.toml:37-39`; `uv.lock` present in branch diff. |
| "Forbidden in source/tests … US-x / +USx — user-story tags … T0xx — task IDs from tasks.md" | `CONTRIBUTING.md:58` | other | **FAIL** | `US1`/`US2` in production source `commands/graph/__init__.py:19`; `US1`–`US5`, `T020b/T032/T034/T035/T040` across 6 test files (see R1). |
| "FR-0xx / SC-0xx … D-x … bookwright-design.md § N.M" allowed in source/tests | `CONTRIBUTING.md:51` | other | PASS | Allowed tags used correctly throughout (e.g. `FR-008`, `SC-001`, `R6`, `design § 12.1`). |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | HIGH | src/bookwright/commands/graph/__init__.py:19 (+6 test files) | Forbidden `US-x`/`T0xx` planning tags in source & tests | Replace `US1/US2/T0xx` references with the allowed `FR`/`SC` tag that owns the behaviour, or drop the bare backlog pointer. |
| R2 | A | LOW | src/bookwright/commands/graph/build.py:36-38 | `--force` flag is a documented no-op (forward-compat) | Contract-sanctioned; keep, but consider a one-line stderr note when `--force` is passed so the no-op is observable, or defer the flag until the cache lands. |
| R3 | B | LOW | src/bookwright/commands/graph/query.py:75 | `_render_table` builds `Console()` (stdout) then takes the stderr branch for empty rows, leaving the stdout console unused | Move `console = Console()` below the empty-rows early return. |
| R4 | C | LOW | src/bookwright/indexers/base.py:16-21 | `IndexTriple` alias is defined + exported but the two `add_triple` signatures spell the union out inline (3× repetition) | Annotate `add_triple` params via the alias, or drop the alias if it carries no callers. |
| R5 | B | LOW | src/bookwright/io/bible.py:165, 200, 208 | `InvalidFrontmatterError("", reason)` constructed with an empty `path`; callers only read `.reason`, so the field is dead at these sites | Pass the real `relpath`, or split out a lighter `reason`-only signal for the skip path. |

## 4. Remediation Detail

### R1 — Forbidden user-story / task tags in source and tests

- **Where:** production source `src/bookwright/commands/graph/__init__.py:19` (`# build (US1) and query (US2) …`); test files `tests/commands/graph/test_build.py:24,68,103,162`, `test_query.py:1`, `test_provenance.py:1`, `test_json_contract.py:76`, `conftest.py:5`, `tests/indexers/test_registry.py:1`, `tests/io/test_bible.py:1,118`.
- **Why it matters:** `CONTRIBUTING.md:58` explicitly lists `US-x`/`+USx` (user-story) and `T0xx` (task IDs from `tasks.md`) as **Forbidden in source/tests** — "planning bookkeeping with no durable artifact". The companion rule (`CONTRIBUTING.md:67`) is that these numbers are *not* frozen on merge, so an inline `US1`/`T034` reference goes stale the moment the spec is renumbered, defeating the traceability the doc is trying to protect. The doc's allowed set (`FR`/`SC`/`D` + `design § N.M`) covers every legitimate "why" pointer. Note: this is a `CONTRIBUTING.md` convention (hard "Forbidden"), not a constitution non-negotiable — hence HIGH rather than CRITICAL; blast radius is comment/traceability hygiene, no functional or security impact.
- **Suggested change:** in each comment/docstring, swap the `US`/`T0` tag for the `FR`/`SC` it maps to (the mapping is already in the docstrings — e.g. `test_registry.py:1` already pairs `US4` with `FR-007/008, SC-007`, so just drop `US4`). For `commands/graph/__init__.py:19`, the sentence reads fine as "`build` and `query` register their callbacks…" with the `(US1)/(US2)` removed. No production behaviour changes; this is comment-only.

## 5. Coverage Detail

Changed modules (from `pytest --cov-report=term-missing`):

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/indexers/__init__.py | 100% | 80% | PASS |
| src/bookwright/indexers/base.py | 100% | 80% | PASS |
| src/bookwright/indexers/errors.py | 100% | 80% | PASS |
| src/bookwright/indexers/rdflib_indexer.py | 93% | 80% | PASS |
| src/bookwright/io/bible.py | 88% | 80% | PASS |
| src/bookwright/io/errors.py | 98% | 80% | PASS |
| src/bookwright/io/frontmatter.py | 100% | 80% | PASS |
| src/bookwright/io/manuscript.py | 100% | 80% | PASS |
| src/bookwright/io/project.py | 100% | 80% | PASS |
| src/bookwright/io/report.py | 100% | 80% | PASS |
| **Total (src/bookwright)** | **96.41%** | 80% | PASS |

`commands/graph/{__init__,build,query,envelope}.py`, `commands/check.py`, and `cli.py` are exercised by the `tests/commands/graph/` integration suite; the global `--cov-fail-under=80` gate passed, so none drop below threshold.

## 6. Inability-to-verify notes

- **TDD signal:** all source and its tests landed in a single squash commit (`7424f23 [Spec Kit] Implementation progress`), so `git log` cannot order impl-vs-test within the branch. The test-first heuristic is therefore inconclusive (not a finding).
- **Track integrity (A.3):** clean — `git status --porcelain` is empty for `specs/006-graph-indexer/`, `src/`, and `tests/`; every file on disk in the feature dir is in the branch diff. No uncommitted/untracked governance artifacts.
- **Workflow trail (A.4):** intact — `spec.md`, `clarify` annotations (Clarifications section + R1/R1a/R2 in `research.md`), `plan.md`, `tasks.md`, the analyze report (commit `bb4bb51`), and source code all present in order.
