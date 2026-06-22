# Quality Audit — 042-character-presence-roster

**Scope:** 5 changed source/test/fixture files vs main (plus DEBT.md, spec artifacts)
**Commit range:** main..cfcc72f (+ unstaged implementation)
**Date:** 2026-06-22
**Conventions discovered:** CLAUDE.md, .specify/memory/constitution.md, DEBT.md, bookwright-design.md

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: PASS (0 modules below threshold, threshold = 80%; suite reports 97.59%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The graph is ALWAYS a derived cache … never the source" (Principle I) | constitution / zero-debt-doctrine.md:18 | io-contract | PASS | Union reads cached `bible()` map via `setting/location/object_names()`; `indexer` unused; no SPARQL/built-graph dependency added |
| "every source file ≤ 500 lines" (Principle IV) | CLAUDE.md | module-size | PASS | base.py 339, character_presence.py 222 |
| "one CLI subcommand per module" (Principle IV) | CLAUDE.md | layout | PASS | No CLI module touched |
| "Agent Skills only — never write to .claude/commands/" (Principle VI) | constitution | directory-ban | PASS | No skill/command files in diff |
| "≥80% coverage, single-sourced, never add --cov-fail-under" (Principle VIII) | constitution | coverage-threshold | PASS | 97.59%; no `--cov-fail-under` added |
| "stdlib `re` only — no new dep" (Constitution II) | plan.md | dependency | PASS | No deps added; `re` already imported |
| "NotEvaluated guard stays on `not roster and not files`" | plan.md / FR-007 | io-contract | PASS | character_presence.py:109 unchanged; reason string byte-identical |
| "_orphans KEEPS feeding from character_names() alone" | plan.md / FR-004 | io-contract | PASS | character_presence.py:127 passes `roster` only |
| "new accessors a byte-for-byte mirror of setting_names()" | plan.md | other | PASS | base.py:270-284 mirror :262-268 exactly |
| "DEBT-011 distinct class, NOT swept here" | plan.md | scope-ban | PASS | DEBT-011 intact in DEBT.md; only DEBT-010 removed |
| "fixture manuscript/bible UNTOUCHED; oracle-only shift" | plan.md / FR-011 | scope-ban | PASS | Only expected-status.md counts changed; fixture sources untouched |
| Workflow trail: specify→clarify→plan→tasks→analyze | CLAUDE.md | workflow-step | PASS | spec.md, checklists/requirements.md, plan.md, tasks.md all present |

## 3. Findings

No findings. The diff is a faithful, minimal implementation of the iteration-042 plan.

## 4. Remediation Detail

None.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| validation/base.py | 87.98% | 80% | PASS |
| validation/validators/character_presence.py | 98.85% | 80% | PASS |
| (full suite) | 97.59% | 80% | PASS |

## 6. Inability-to-verify notes

None. All four gates ran green; the `tiny-historical` oracle change was independently verified (baseline emitted exactly `Real`/`Fábrica`/`Paños`; the change suppresses all three, leaving the lone `factual_anchor` warning).
