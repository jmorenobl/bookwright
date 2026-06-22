# Quality Audit — 040-tri-valued-validator-result

**Scope:** validation tri-valued result (issue #1, facet B) — `NotEvaluated`/`NotEvaluatedResult` channel
**Commit range:** merge-base(origin/main)..HEAD (folds 039 seam; 040-proper is the validation/status/skill delta)
**Date:** 2026-06-22
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `DEBT.md`, `.specify/workflows/bookwright-quality/zero-debt-doctrine.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 (fixed) |
| LOW | 1 (fixed) |
| **Total** | 2 (both fixed in-tree) |

Coverage gate: **PASS** (97.57% total, threshold 80%). Four gates green.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "graph is ALWAYS a derived cache … never the source" | constitution I | io-contract | PASS | Prose validators stay graph-free, `triples=()`; no graph writes |
| "agent-consumed subcommand … emits a single JSON document on stdout" | constitution IX | io-contract | PASS | `not_evaluated[]` added to the one envelope; human render on stderr/console |
| "Every source file ≤ 500 lines" | constitution IV | module-size | PASS | `base.py` 321, `rules.py` 192, all changed files < 500 |
| "Agent Skills only — never `.claude/commands/`" | constitution VI | directory-ban | PASS | `resources/commands/bookwright-research.md` is the source-command (→ SKILL.md) |
| "≥80% coverage, single-sourced `fail_under`" | constitution VIII | coverage-threshold | PASS | 97.57%; no `--cov-fail-under` added |
| "frozen ontology — `triples=()`" | constitution X | scope-ban | PASS | No ontology/`.ttl` change; prose validators only |
| "one observable delta per iteration" | zero-debt §2 | scope-ban | PASS | Tri-valued result + 3 migrations; no future plumbing |

## 3. Findings (all resolved)

| ID | Pass | Severity | Location | Summary | Resolution |
|---|---|---|---|---|---|
| R1 | B | MEDIUM | status/rules.py:129-142 | `_activate_dormant_validators` built the prompt from `with_remedy` only while `reason` counted all `dormant` — an unmapped (custom) dormant validator was silently dropped from the prompt; the all-unmapped else-branch was untested | Unified to one clause per dormant validator (mapped → remedy, unmapped → `_GENERIC_REMEDY`); dead else-branch removed; prompt and count can never disagree. New test `test_activate_dormant_validators_falls_back_for_unmapped_validators` |
| R2 | B | LOW | validators/focalization.py:73-75 | cause-(i) reason `"there is no constitution to read…"` fired for a present-but-empty constitution (`constitution_view()` returns `()` for both absent and empty), misdescribing the cause in an author-facing reason | Guard on `constitution_text() is None`; empty-but-present now falls through to cause (ii). New test `test_empty_constitution_is_no_declaration_not_no_constitution` |

## 4. Rejected (considered, not debt)

- **setting_continuity consumes `manuscript_view()` but reads only `.raw`/`.number`.** Originated in 039, not 040. `manuscript_view()` is memoized and already built by the other prose validators, so reusing the cached view is correct reuse — reverting to a private `splitlines()` pass would re-introduce a duplicate scan. Uniform "all prose validators consume the seam" is the 039 design intent. Not debt.
- **`status == "ok"` reads green for a not-evaluated-only run unless the consumer applies the compound predicate.** By design and documented (`report.py` docstring, e2e test): green = `status == "ok" AND not_evaluated == []` (SC-002). No change.

## 5. Coverage Detail

Total 97.57% (threshold 80%). Changed modules at/above project norm; the new `activate_dormant_validators` branches are now all exercised (the prior 136-137 else-branch gap is eliminated by the unification).

## 6. Inability-to-verify notes

None — all four gates run locally and green.
