# Quality Audit — 044-not-evaluated-kinds

**Scope:** iteration-044 implementation diff (src + tests) vs `origin/main`
**Commit range:** `origin/main`..`32503f2`
**Date:** 2026-06-23
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `.specify/workflows/bookwright-quality/zero-debt-doctrine.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 1 (fixed) |
| **Total** | 1 |

Coverage gate: **PASS** (0 modules below threshold; threshold = 80%; total 97.55%). Four gates green (`pytest` 1442 passed / 1 skipped, `mypy --strict`, `ruff check`, `ruff format --check`).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "every changed file ≤ 500 lines" | CLAUDE.md / Principle IV | module-size | PASS | largest touched `base.py` = 355 lines |
| "stdlib only, no new dep" | spec-044 / Constitution II | dependency | PASS | only `enum.StrEnum` added; no manifest change |
| "graph stays a derived cache" | Principle I | layout | PASS | no graph/source-of-truth edits; prose validators keep `triples=()` |
| "agent-facing commands emit one JSON doc on stdout under --json" | Principle IX | io-contract | PASS | `to_json` additive (`kind` key); no stdout/stderr mixing |
| "skills materialize as SKILL.md, never legacy commands/" | Principle VI | directory-ban | N/A | no skill/integration files in diff |
| "frozen ontology untouched" | Constitution X | scope-ban | PASS | no `CLASS_IRI`/`golem.ttl` edits |
| "contract-before-code: update design §13.1/§13.4 before validators diverge" | plan §7.3 | workflow-step | PASS | `bookwright-design.md` updated on branch |
| "≥80% coverage" | Constitution VIII | coverage-threshold | PASS | 97.55% total; new files 100% |
| "FR-002: every existing `raise NotEvaluated(reason)` byte-for-byte unchanged" | spec-044 | other | PASS | trailing defaulted `kind`; 6 single-arg raises unchanged |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | LOW | tests/e2e/test_tri_valued_validation.py:42, tests/validation/test_report.py:24 | The canonical `_is_green` green-predicate helper was duplicated byte-for-byte across two test modules and edited in lockstep twice (040 → 044) — a drift surface | **FIXED**: consolidated into `tests/conftest.is_green`, imported by both suites; local copies deleted |

## 4. Remediation Detail

### R1 — Duplicated green-predicate test helper (FIXED)

- **Where:** `tests/e2e/test_tri_valued_validation.py:42`, `tests/validation/test_report.py:24`
- **Why it matters:** The green predicate is *the* canonical definition the iteration repairs; two copies edited in lockstep across milestones is exactly the drift surface the zero-debt doctrine's "sweep the class you touch" rule targets. `tests/conftest.py` already exported a non-fixture helper (`copy_fixture`), so a shared home existed.
- **Change applied:** moved the predicate to `tests/conftest.is_green` with a canonical docstring; both suites now `from tests.conftest import is_green`; the two local definitions were deleted. Gates re-run green.

Adversary nits not actioned (not debt): the `NotEvaluatedResult.kind` dataclass default mirrors the established `Severity` idiom and keeps the type ergonomic; the design-doc `(str, Enum)` illustration is internally consistent with the adjacent `Severity` example (functionally identical to the code's `StrEnum`).

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| validation/base.py | 96.55% | 80% | PASS |
| validation/report.py | 91.95% | 80% | PASS |
| validation/runner.py | 100% | 80% | PASS |
| validators/character_unknown_mentions.py | 100% | 80% | PASS |
| status/rules.py | (suite-wide 97.55%) | 80% | PASS |

## 6. Inability-to-verify notes

None — all four gates ran locally and passed.
