# Quality Audit — 006-graph-indexer

**Scope:** 47 changed files vs `main` (source + tests + spec artifacts)
**Commit range:** `main`..`1e1b7bd`
**Date:** 2026-06-01
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.2.0), `CONTRIBUTING.md`

## 1. Summary

| Severity | Found | Open |
|---|---|---|
| CRITICAL | 0 | 0 |
| HIGH | 0 | 0 |
| MEDIUM | 1 | 0 |
| LOW | 3 | 1 |
| **Total** | 4 | 1 |

Coverage gate: **PASS** (0 changed modules below threshold, threshold = 80%). Total line coverage 97.01%; every changed module ≥ 89%. 518 tests pass.

This re-audit follows the R1/R2/R3/R6 cleanup commits (`9ee662f`, `0d926b1`) and the iteration-10 plan insert (`1e1b7bd`). The branch is clean: no principle violation, no scope drift, no boundary-security issue.

**Resolution (applied in this change):** R1, R2, and R4 were fixed in place — see the `Status` column in Section 3. The single remaining item (R3, `to_json` duplication) is intentionally deferred to iteration 10 (`BookwrightError` consolidation), so it is left open by design.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden as canonical storage" | `.specify/memory/constitution.md:47` | layout | PASS | Graph serialized to `bible/graph.ttl` (Turtle); reports are Pydantic→JSON/stderr. No binary canonical store added. |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | `.specify/memory/constitution.md:64` | dependency | PASS | `pyyaml>=6.0` added (`pyproject.toml:26`); matches constitution v1.2.0 amendment. Runtime deps are an exact match of the allowed set. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `.specify/memory/constitution.md:72` | layout | PASS | New source under `src/bookwright/{commands/graph,indexers,io}`; new tests under `tests/`. |
| "Each CLI subcommand MUST live in its own module … No source file … may exceed 500 lines" | `.specify/memory/constitution.md:83` | module-size | PASS | `graph build`/`query` in own modules; `cli.py` 17 lines. Largest changed file `io/bible.py` = 386 lines. |
| "Integrations MUST be … registered in `INTEGRATION_REGISTRY` … `AGENT_CONFIG`-style dispatcher … forbidden" | `.specify/memory/constitution.md:94` | plugin-shape | PASS (analogous) | No integration code touched. New engine seam uses the same shape: `INDEXER_REGISTRY` + `resolve_indexer` (`indexers/__init__.py:20`); no if/elif dispatcher. |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" | `.specify/memory/constitution.md:106` | directory-ban | N/A | No skills emitted and no `commands/` directory written this iteration. |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" | `.specify/memory/constitution.md:119` | frontmatter-constraint | N/A | No `SKILL.md` generated this iteration. |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `.specify/memory/constitution.md:135` | coverage-threshold | PASS | 96.98% total; every changed module ≥ 89%. |
| "MUST accept a `--json` flag … single … JSON document on stdout and nothing else" | `.specify/memory/constitution.md:148` | io-contract | PASS | `build`/`query` accept `--json`; `envelope.emit_json` writes one doc to stdout; prose via `Console(stderr=True)`. `test_json_contract.py` asserts stdout purity. |
| "rdflib over Grafeo in v0 … GrafeoIndexer … MUST NOT be reopened" | `.specify/memory/constitution.md:159` | scope-ban | PASS | `GrafeoIndexer` not registered; explicitly noted as deferred (`indexers/__init__.py:4-6`). No vector-search plumbing. |
| "Forbidden in source/tests: `US-x` / `+USx` … `T0xx` task IDs" | `CONTRIBUTING.md:58` | other | PASS | `grep -E '(US-[0-9]|T[0-9]{3})'` over changed src/tests → no matches. |
| Workflow: `specify → clarify → plan → tasks → analyze → implement` | `CLAUDE.md` | workflow-step | PASS | All artifacts present: `spec.md`, `research.md`, `plan.md`, `tasks.md`, `review.md`, source under `src/`. Trail intact. |
| Governance artifacts tracked in branch | `CLAUDE.md` | track-integrity | PASS | All `specs/006-graph-indexer/**` files appear in `git diff main...HEAD`; working tree clean (`git status` empty). No untracked/staged-only governance file. |

Status values: `PASS`, `FAIL`, `N/A`. No `FAIL` rows.

## 3. Findings

| ID | Pass | Severity | Status | Location | Summary | Recommendation |
|---|---|---|---|---|---|---|
| R1 | B | MEDIUM | ✅ RESOLVED | src/bookwright/commands/graph/build.py:51 | Three identical `except` blocks (`ProjectNotFoundError`, `MissingDirectoryError`, `UnknownIndexerError`) each `emit_error(exc.to_json(), …); raise typer.Exit(EXIT_CONFIG)` | Collapsed into one tuple-`except`, matching sibling `query.py:49-56`. |
| R2 | A | LOW | ✅ RESOLVED | specs/006-graph-indexer/contracts/cli-graph.md | `error_payload("invalid_manifest", …)` emitted a `code` not enumerated in the `cli-graph.md` error tables | Added `invalid_manifest` (exit 2) to the build and query error tables. |
| R3 | B | LOW | ⏳ DEFERRED | src/bookwright/indexers/errors.py (+ io/errors.py, core, golem) | Four error modules hand-roll the same `to_json()` `{status,code,message,details}` envelope | No action this PR — scheduled as **iteration 10** (`BookwrightError` consolidation, commit `1e1b7bd`). Left open by design. |
| R4 | B | LOW | ✅ RESOLVED | src/bookwright/indexers/rdflib_indexer.py:83 | `except InvalidQueryError: raise` was dead — nothing in the `try` raised it before the following `except Exception` wraps rdflib errors | Removed the dead re-raise. |

(IDs stable, sorted severity desc, file asc, line asc.)

## 4. Remediation Detail

### R1 — Duplicated exit-2 exception handlers in `graph build` (✅ RESOLVED)

- **Where:** `src/bookwright/commands/graph/build.py:51`
- **Why it matters:** the three blocks were byte-for-byte identical apart from the caught type, while the sibling command `query.py:49-56` already handles its exit-2 family as a single tuple-`except`. A future change to exit-2 handling would have needed three edits here but one in `query.py`.
- **Applied:** the three blocks were collapsed into:
  ```python
  except (ProjectNotFoundError, MissingDirectoryError, UnknownIndexerError) as exc:
      emit_error(exc.to_json(), json_output)
      raise typer.Exit(EXIT_CONFIG) from exc
  ```
  `ManifestError` (different payload builder) and `SlugCollisionError` (exit 3) remain their own blocks.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| commands/graph/build.py | 89% | 80% | PASS |
| commands/graph/envelope.py | 100% | 80% | PASS |
| commands/graph/query.py | 94% | 80% | PASS |
| indexers/base.py | 100% | 80% | PASS |
| indexers/errors.py | 100% | 80% | PASS |
| indexers/rdflib_indexer.py | 98% | 80% | PASS |
| io/bible.py | 92% | 80% | PASS |
| io/errors.py | 98% | 80% | PASS |
| io/frontmatter.py | 100% | 80% | PASS |
| io/manuscript.py | 100% | 80% | PASS |
| io/project.py | 100% | 80% | PASS |
| io/report.py | 100% | 80% | PASS |
| **TOTAL (repo)** | **96.98%** | 80% | PASS |

## 6. Inability-to-verify notes

- **Security boundary (informational, not a finding):** `manifest.paths.{graph,bible,manuscript}` are joined to the project root and could in principle point outside it via `..`. This is an author-controlled local file (same trust domain), not a path-traversal vector at a hostile-input boundary; manifest validation lives in iteration 002's model. No action.
- No runner/dependency gaps: `uv run pytest` ran cleanly with coverage; all four CI gates reproduce locally.
