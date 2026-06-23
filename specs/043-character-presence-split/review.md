# Quality Audit — 043-character-presence-split

**Scope:** 17 changed files vs `main` (src + tests + spec + DEBT.md)
**Commit range:** `772928c`..`d0c17ed` (+ uncommitted working tree)
**Date:** 2026-06-23
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `.specify/workflows/bookwright-quality/zero-debt-doctrine.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: **PASS** (0 modules below threshold; threshold = 80%; suite total 97.55%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every source file ≤ 500 lines, one CLI subcommand per module" | `CLAUDE.md` | module-size | PASS | character_presence 72, character_unknown_mentions 35, base 321, rules 212 |
| "stdlib only, no new dep" (Constitution II locked stack) | `CLAUDE.md`/constitution | dependency | PASS | `pyproject.toml` unchanged in range; new validator imports only `indexers`+`validation.base` |
| "graph is a derived cache, never source of truth" (Principle I) | constitution | layout | PASS | No graph mutation; validators read only |
| "JSON-over-stdout: single JSON doc on stdout, prose on stderr" (IX) | constitution | io-contract | PASS | No envelope touched; `not_evaluated[]` is the existing 040 channel |
| "Agent Skills, never legacy commands/ dir" (VI) | constitution | directory-ban | PASS | No `.claude/commands/` writes |
| "test discipline ≥ 80% coverage" (VIII) | constitution | coverage-threshold | PASS | 97.55% total; both new modules 100% |
| "no plumbing whose only justification is future X" (Scope & Release) | constitution | scope-ban | PASS | move-3 heuristic fully DELETED, not parked; abstainer holds no dead branches |
| "out-of-scope debt → DEBT.md, swept class removed" | CLAUDE.md | scope-ban | PASS | DEBT-011/012 removed (subsumed by abstain approach) |
| "eliminate the cause over a guard" | zero-debt-doctrine | other | PASS | FPs vanish by abstaining, not by adding a quote/title guard to `io/prose.py` |

## 3. Findings

No findings.

## 4. Remediation Detail

None.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `validators/character_presence.py` | 100% | 80% | PASS |
| `validators/character_unknown_mentions.py` | 100% | 80% | PASS |
| `validation/base.py` | (net deletion) | 80% | PASS |
| `status/rules.py` | (net addition, covered) | 80% | PASS |

## 6. Inability-to-verify notes

None — all four gates ran green (`pytest` 1430 passed / 97.55%, `mypy --strict` clean,
`ruff check` clean, `ruff format --check` clean). The leftover scratch file `_qs_check.py`
was removed during the review pass. An independent adversarial subagent attempted to refute
the zero-debt bar (dead code, gate parity, coverage, layering, suppressions) and found no
deletable cause, missing test, or masked error.
