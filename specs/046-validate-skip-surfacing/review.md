# Quality Audit — 046-validate-skip-surfacing

**Scope:** 2 source + 1 test (+ docs/spec) changed files vs main
**Commit range:** 2a362ac..d8ad796 + working tree
**Date:** 2026-06-23
**Conventions discovered:** CLAUDE.md, .specify/memory/constitution.md (v1.4.0), DEBT.md, bookwright-design.md

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: PASS (0 modules below threshold, threshold = 80%; suite total 97.58%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The graph is ALWAYS a derived cache … never the source" (Principle I) | constitution.md | io-contract | PASS | `validate` merges in-memory `NotEvaluatedResult`s only; no `serialize`/write in diff; graph written solely by `graph build` |
| "any agent-consumed subcommand … emits a single JSON document on stdout and only that" (Principle IX) | CLAUDE.md | io-contract | PASS | `validate.py` has zero `print`/`stdout`/`console.print`; output via `emit_json`; skip entries reuse existing `to_json` shape |
| "Every source file ≤ 500 lines, one CLI subcommand per module" (Principle IV) | CLAUDE.md | module-size | PASS | validate.py 166, runner.py 95, test 167 lines |
| "Agent Skills, never legacy commands" (Principle VI) | CLAUDE.md | directory-ban | N/A | no skill/commands dir touched |
| "≥80% coverage, single-sourced in [tool.coverage.report]; never add --cov-fail-under" (Principle VIII) | constitution.md | coverage-threshold | PASS | 97.58% total; no `--cov-fail-under` added |
| "stdlib only (Constitution II)" | CLAUDE.md (plan) | dependency | PASS | no new imports beyond existing `bookwright.validation.*` |
| "frozen ontology untouched" | CLAUDE.md (plan) | scope-ban | PASS | no `.ttl`/CLASS_IRI change |
| "Contract-before-code: update design § 13.4/§ 13.5 before code diverges" | CLAUDE.md (plan) | workflow-step | PASS | bookwright-design.md § 13.4 + § 13.5 edited; T002 marked done |
| "Resolving a debt entry removes it" | CLAUDE.md | other | PASS | DEBT-018 removed; track-A cross-ref reconciled; DEBT-019 left intact (in scope) |
| Spec Kit trail specify→…→implement | CLAUDE.md | workflow-step | PASS | spec/plan/tasks/research/data-model/contracts/quickstart all present in specs/046 |

## 3. Findings

No findings. The diff is a minimal, single-observable-delta change: it reuses the
existing `not_evaluated[]` channel (no new channel/key — FR-008), extracts the sort
key once as `not_evaluated_sort_key` imported by both sites (no DRY duplication), and
adds no plumbing for deferred scope (move 3 / DEBT-019 untouched). Layering: importing
`NotEvaluatedKind` from `bookwright.validation.base` mirrors the established
`report.py` pattern (the package `__init__` does not re-export it), so it is not a new
seam.

## 4. Remediation Detail

None required.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| commands/validate.py | covered by tests/commands/test_validate_skipped.py + existing | 80% | PASS |
| validation/runner.py | 96%+ via merged suite | 80% | PASS |
| (suite total) | 97.58% | 80% | PASS |

## 6. Inability-to-verify notes

None. All four gates ran green (`uv run pytest` 1450 passed, `ruff check`,
`ruff format --check`, `mypy --strict`).
