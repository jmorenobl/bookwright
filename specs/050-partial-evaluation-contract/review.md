# Quality Audit — 050-partial-evaluation-contract

**Scope:** 3 source files + 2 test modules + design/DEBT/plan/roadmap docs vs `origin/main`
**Commit range:** `origin/main..HEAD` (review applied on top of `26879b3`)
**Date:** 2026-06-24
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `bookwright-design.md`, `DEBT.md`, `.specify/workflows/bookwright-quality/zero-debt-doctrine.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 2 (both fixed in this review pass) |
| **Total** | 2 |

Coverage gate: **PASS** (97.68% total; `runner.py` and `focalization.py` at 100%; threshold = 80%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The graph is ALWAYS a derived cache … never the source" | constitution (Principle I) | io-contract | PASS | No persistence/graph-source touched; validators read-only |
| "Agent Skills only — no legacy commands/ directories" | constitution (Principle VI) | directory-ban | N/A | No skills/commands touched by this diff |
| "≥80% coverage, single-sourced in [tool.coverage.report]" | constitution (Principle VIII) | coverage-threshold | PASS | 97.68% total; no `--cov-fail-under` added |
| "Every source file ≤ 500 lines, one CLI subcommand per module" | constitution (Principle IV) | module-size | PASS | base.py 449, runner.py ~115, focalization.py 174 |
| "frozen ontology untouched; prose validator triples=()" | constitution (Principle X) | io-contract | PASS | `focalization.py:139` emits `triples=()` |
| "no new module/dep (Constitution II)" | CLAUDE.md / constitution | dependency | PASS | `pyproject.toml` unchanged; only stdlib `dataclass` |
| "THREE source edits: base.py, runner.py, focalization.py" | spec-050 | scope-ban | PASS | Exactly those 3 + a public-surface re-export sweep (in-scope) |
| "ONE name-stamping authority MUST NOT fork (FR-002)" | spec-050 | plugin-shape | PASS | `_record` shared by raise (form b) + EvalResult (form c) |
| "RunResult 4-tuple + both consumers UNCHANGED" | spec-050 | io-contract | PASS | `commands/validate.py`, `status/queries.py` untouched |
| "CONTRACT-BEFORE-CODE: update design §13.1 + DEBT.md" | spec-050 | workflow-step | PASS | design §13.1/§13.5/§20.6.1 updated; DEBT-019 removed |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | LOW | `validation/__init__.py` | `EvalResult`/`Abstention` not re-exported alongside `NotEvaluated`, yet the exported `Validator` Protocol returns `list[Violation] \| EvalResult` | Add both to imports + `__all__` (DONE) |
| R2 | B | LOW | `runner.py:104` | Redundant `abstention: Abstention` annotation (inferred from `list[Abstention]`) | Delete annotation + now-unused import (DONE) |

## 4. Remediation Detail

### R1 — Public-surface asymmetry on the form-(c) contract types
- **Where:** `src/bookwright/validation/__init__.py`
- **Why it matters:** The package re-exports `NotEvaluated` (form (b)'s public mechanism); form (c)'s `EvalResult`/`Abstention` are now part of the exported `Validator` Protocol's return type, so a custom validator implementing form (c) had to reach into `.base`. Asymmetric public surface.
- **Change applied:** added `Abstention`, `EvalResult` to the import block and `__all__`. Verified import + ruff + mypy clean.

### R2 — Redundant type annotation (zero-debt: delete the cause)
- **Where:** `src/bookwright/validation/runner.py:104`
- **Why it matters:** `found.not_evaluated` is `list[Abstention]`, so the loop variable is already inferred; the explicit annotation (and the import it kept alive) is dead weight. Adversary-flagged.
- **Change applied:** removed the annotation and the now-unused `Abstention` import. mypy `--strict` still clean.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `validation/runner.py` | 100.00% | 80% | PASS |
| `validation/validators/focalization.py` | 100.00% | 80% | PASS |
| `validation/base.py` | 97.00% | 80% | PASS (uncovered lines pre-existing, not the new dataclasses) |
| **TOTAL** | 97.68% | 80% | PASS |

## 6. Inability-to-verify notes

None. All four gates ran locally and are green. Independent adversarial second opinion (general-purpose subagent) returned: no bugs, no debt, one cosmetic nit (R2) — now resolved.
</content>
</invoke>
