# Quality Audit — 014-factual-anchor-validator

**Scope:** 4 changed source files + 6 changed test files (vs `main`)
**Commit range:** `main..bca7293` (+ uncommitted working-tree refinement)
**Date:** 2026-06-04
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.3.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 3 |
| **Total** | 3 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%). Full
suite: **1028 passed, 1 skipped**, total coverage **96.78%**. Changed-module
coverage: `factual_anchor.py` 100%, `anchor_queries.py` 97.37%, `queries.py`
92.75%, `temporal.py` 96.51%. All four CI gates green locally
(`ruff check`, `ruff format --check`, `mypy --strict`, `pytest`).

This is an exemplary iteration: zero CRITICAL/HIGH/MEDIUM findings, zero
technical debt introduced. The three LOW items are all deliberate,
test-protected design choices noted for completeness, not defects to fix.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Plain Text as Source of Truth … Binary stores … forbidden as canonical storage" | `constitution.md:57` | layout | PASS | No binary canonical store in diff; graph stays a derived cache. Only `__pycache__/*.pyc` touched (gitignored, ephemeral). |
| "The implementation language is Python 3.11+ … Introducing an additional runtime dependency requires an amendment" | `constitution.md:70` | dependency | PASS | No `pyproject.toml` change; new code imports only `rdflib`, stdlib `dataclasses`/`datetime`, and in-package modules. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:84` | layout | PASS | Source under `src/bookwright/validation/…`; tests under `tests/validation/`. No co-location. |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:96` | module-size | PASS | Largest changed: `tests/test_factual_anchor.py` 397, `factual_anchor.py` 290, `temporal.py` 277, `anchor_queries.py` 223. All < 500. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`" | `constitution.md:94` | layout | N/A | No new CLI subcommand — `factual_anchor` is a `Validator` plugging into the existing `validate` command via auto-discovery. |
| "Integrations MUST be implemented as subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`" | `constitution.md:104` | plugin-shape | N/A | No integration touched. (Validator itself follows the analogous registry/auto-discovery seam — no if/elif dispatcher.) |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" | `constitution.md:117` | directory-ban | N/A | No skill/command directory writes in this diff. |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" | `constitution.md:129` | frontmatter-constraint | N/A | No `SKILL.md` generated/changed on this branch. |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:147` | coverage-threshold | PASS | 96.78% total; every changed module ≥ 92%. |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a `--json` flag … single … JSON … on stdout" | `constitution.md:167` | io-contract | N/A | No new agent-facing CLI surface. Violations flow through the existing `runner`/`report`/`validate --json` path, untouched here. |
| "Section 16 … decisions that are closed … MUST NOT be reopened" | `constitution.md:180` | scope-ban | PASS | Uses rdflib + GOLEM; `intervals_disjoint` reuse keeps temporal logic single-sourced. No axiom reopened. |
| "the `factual_anchor` validator are **later** iterations — don't pull them in" (relative to iter 012) | `CLAUDE.md` | scope-ban | PASS | This *is* the dedicated `factual_anchor` iteration (branch `014`), not premature plumbing inside an earlier one. In-scope for its own branch. |
| "adds plumbing whose only justification is 'future X' MUST be rejected" | `constitution.md:227` | scope-ban | PASS | Validator is inert when `[research].enabled` is false / no anchors (FR-015/016); no speculative hooks for deferred features. |
| Workflow: `specify → clarify → plan → tasks → analyze → implement` | `CLAUDE.md` | workflow-step | PASS | All artifacts present: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `checklists/requirements.md`; analysis-report commits in branch history. |
| Track integrity — `specs/014-…/` governance files | `CLAUDE.md` / A.3 | track-integrity | PASS (informational) | All spec artifacts committed on branch. `spec.md`/`data-model.md`/`contracts/` + `factual_anchor.py`/`test_factual_anchor.py` carry **uncommitted** working-tree deltas (the R3 unrated-vs-below refinement) — tracked & visible to git, green, but not yet committed. See note N1. |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | D | LOW | `anchor_queries.py:222` | `entity_present` interpolates a graph-derived URI into SPARQL via `<{uri}>` f-string | No action required — internal boundary (URI comes from rdflib, not user CLI input); mirrors the existing `queries.py` pattern. Noted for awareness only. |
| R2 | B | LOW | `factual_anchor.py:56-58` | Module-level `assert` (reliability-scale drift guard) is stripped under `python -O` | Keep — the same invariant is asserted by `test_reliability_scale_matches_vocabulary` (an `-O`-safe test, as its own comment notes). Defense-in-depth, not a gap. |
| R3 | B | LOW | `factual_anchor.py:155,215,230,243` | `(anchor.uri, str(BW_PROMOTES), anchor.promotes)` tuple recurs across R1/R3/R4 | Leave as-is — at the 3-occurrence threshold; each is a semantically distinct "promotes edge as locator" per rule, and extraction to a helper would obscure intent for a trivial literal. |

## 4. Remediation Detail

No CRITICAL or HIGH findings — no remediation required. The three LOW items
above are recorded as deliberate, test-protected choices; the recommended
action for each is "keep as-is."

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `validation/validators/factual_anchor.py` | 100.00% | 80% | PASS |
| `validation/anchor_queries.py` | 97.37% | 80% | PASS |
| `validation/validators/temporal.py` | 96.51% | 80% | PASS |
| `validation/queries.py` | 92.75% | 80% | PASS |
| **Project total** | **96.78%** | 80% | **PASS** |

## 6. Inability-to-verify notes

- **N1 — Uncommitted working-tree deltas.** `factual_anchor.py`,
  `test_factual_anchor.py`, `spec.md`, `data-model.md`, and
  `contracts/factual-anchor-validator.md` carry unstaged edits (the R3
  "unrated vs below-threshold" distinction + matching spec/tests). They are
  tracked, visible to `git status`, and the suite passes *with* them applied
  — but the branch tip (`bca7293`) that CI/reviewers see does **not** include
  them. Commit before opening the PR so the reviewed state matches the audited
  state. Not a track-integrity violation (files are not invisible to git), so
  not escalated above informational.
