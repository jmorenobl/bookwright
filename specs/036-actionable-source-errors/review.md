# Quality Audit — 036-actionable-source-errors

**Scope:** 7 changed files vs main (3 source/docs + 2 tests + DEBT.md + tasks.md)
**Commit range:** main..HEAD + working tree
**Date:** 2026-06-21
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: PASS (research.py 98.19%, project 97.45%, threshold = 80%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every source file ≤ 500 lines" | `CLAUDE.md` (Principle IV) | module-size | PASS | research.py 496, query.py 102 |
| "graph is ALWAYS a derived cache … never the source" | `constitution.md` (I) | layout | PASS | No graph/cache writes in diff |
| "any agent-consumed subcommand … emits a single JSON document on stdout and only that" | `CLAUDE.md` (IX) | io-contract | PASS | query.py change is a `help=` string only; envelope untouched |
| "Agent Skills only — never write to `.claude/commands/`" | `constitution.md` (VI) | directory-ban | PASS | No skill/commands writes in diff |
| "≥ 80 % coverage … single-sourced; no `--cov-fail-under`" | `constitution.md` (VIII) | coverage-threshold | PASS | 97.45% project; no flag added |
| "new vocabulary goes in separate `.ttl` files; ontology frozen" | `CLAUDE.md` | scope-ban | N/A | No ontology/vocab change in this diff |
| "Resolving a debt entry removes it from DEBT.md" | `CLAUDE.md` | other | PASS | DEBT-006 removed; ledger now `Ninguna por ahora` |
| "JSON error envelope `{status,code,message[,details]}` single-sourced" | `CLAUDE.md` (errors.py) | io-contract | PASS | code/details byte-unchanged; only message enriched (FR-007) |

## 3. Findings

No findings. The diff is small, locator-only enrichment of error messages plus a
documented (not fixed) SPARQL footgun note.

## 4. Remediation Detail

None.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/io/research.py | 98.19% | 80% | PASS |
| (project total) | 97.45% | 80% | PASS |

Remaining uncovered lines in research.py (322, 369-370, 437-438) are pre-existing
paths untouched by this iteration; the new `_source_id` branches (225-226 unsluggable,
221 non-dict) are now covered by tests added during review.

## 6. Inability-to-verify notes

None. All four gates ran green (pytest 1356 passed, mypy --strict clean, ruff check,
ruff format --check).
