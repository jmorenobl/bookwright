# Quality Audit — 037-focalization-pending-placeholder

**Scope:** 3 source/governance files changed in worktree (focalization.py, test_focalization.py, DEBT.md)
**Commit range:** origin/main..9505994 + worktree
**Date:** 2026-06-21
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `bookwright-design.md`, `DEBT.md`, zero-debt-doctrine.md

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; full suite 97.50%, focalization.py 91.20%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The graph is ALWAYS a derived cache … never the source" | zero-debt-doctrine.md:18 | layout | N/A | Prose validator; no graph/indexer writes, `triples=()` |
| "Every source file ≤ 500 lines, one CLI subcommand per module" | CLAUDE.md (Stack) | module-size | PASS | focalization.py = 189 lines |
| "Agent Skills, never legacy commands" | CLAUDE.md (Domain knobs) | directory-ban | N/A | No skills/commands touched |
| "≥80% coverage, single-sourced in [tool.coverage.report]" | zero-debt-doctrine.md:22 | coverage-threshold | PASS | 97.50% full suite; no `--cov-fail-under` added |
| "JSON-over-stdout … single JSON document" | CLAUDE.md (Principle IX) | io-contract | N/A | Validator emits Violations, not a CLI `--json` command |
| "frozen ontology … must not gain classes (X)" | CLAUDE.md (golem) | scope-ban | PASS | No `.ttl`/ontology change; prose-only |
| "one observable delta (scope discipline)" | zero-debt-doctrine.md:29 | scope-ban | PASS | One guard + recognizer; no speculative plumbing |
| "eliminate the cause, don't contain it" | zero-debt-doctrine.md:35 | other | PASS | Guard sits at the single `_parse_declaration` seam every finding flows through; reuses existing `return None` path |
| "record only genuinely out-of-scope debt in DEBT.md" | zero-debt-doctrine.md:54 | track-integrity | PASS | DEBT-007 removed; "Deuda abierta" = `_Ninguna por ahora._` |
| Spec Kit workflow trail (specify→…→implement) | CLAUDE.md | workflow-step | PASS | spec/plan/tasks/contracts/data-model/research all present on branch |

## 3. Findings

No findings.

## 4. Remediation Detail

None.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| validation/validators/focalization.py | 91.20% | 80% | PASS |
| (full suite) | 97.50% | 80% | PASS |

Uncovered lines in focalization.py (73, 125, 174-175) are pre-existing branches unrelated to this diff; the new guard (lines 169-170) is exercised by 6 tests.

## 6. Inability-to-verify notes

None. Full suite ran green (1363 passed, 1 skipped).
