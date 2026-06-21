# Quality Audit — 034-focalization-markdown-voice

**Scope:** 4 changed files vs main (focus: validator + tests + specs/034)
**Commit range:** merge-base(origin/main)..HEAD + working tree
**Date:** 2026-06-21
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `DEBT.md`, `bookwright-design.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: PASS (focalization.py 98.33%, project total 97.43%, threshold = 80%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The graph is ALWAYS a derived cache … never the source" | constitution (I) | io-contract | PASS | Validator only reads `ValidationContext`; no graph write path touched |
| "prose validator only (`triples=()`, Principle X)" | CLAUDE.md plan | io-contract | PASS | All `Violation(...)` set `triples=()`; asserted in `test_scaffold_shape_wakes_validator_through_validate` |
| "Every source file ≤ 500 lines" | constitution (IV) | module-size | PASS | `focalization.py` 183 lines; test 190 lines |
| "one CLI subcommand per module" | constitution (IV) | layout | N/A | No CLI module changed (validator, not a verb) |
| "≥80% coverage, single-sourced in `fail_under`; never add `--cov-fail-under`" | constitution (VIII) | coverage-threshold | PASS | 97.43% total; no `--cov-fail-under` added |
| "Agent Skills only — never write `.claude/commands/`" | constitution (VI) | directory-ban | N/A | No skill/command change in diff |
| "ontology frozen — no new classes; new vocab in separate .ttl" | constitution (X) | scope-ban | PASS | No GOLEM/ontology/.ttl change; prose validator only |
| "one observable delta per iteration; no plumbing for future X" | CLAUDE.md scope | scope-ban | PASS | Single delta: parser tolerates markdown-prefixed declaration |
| "record genuinely out-of-scope debt in DEBT.md; resolving removes it" | CLAUDE.md scope | workflow-step | PASS | DEBT-004 removed; intro count + DEBT-006 cross-ref reconciled |

## 3. Findings

No findings. The diff fixes the root cause (the line-anchored regex that ignored
the scaffold's own `- **Voz narrativa**:` shape) by normalizing each candidate
line before matching — a cause-elimination, not a guard. The bare form parses
byte-identically (verified), the body after the colon is never touched, and the
five voice-bearing fixtures that were silently dormant now parse.

## 4. Remediation Detail

None required.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `validation/validators/focalization.py` | 98.33% | 80% | PASS |
| project total | 97.43% | 80% | PASS |

The single uncovered line (`focalization.py:121`, the head-hopping `seen` dedup
`continue`) is **pre-existing** — outside this diff, which did not touch
`_head_hopping`. Not introduced here; not in scope.

## 6. Inability-to-verify notes

- TDD-order heuristic is N/A: both files are uncommitted working-tree changes,
  so `git log` shows no branch ordering between test and impl.
- The plan/CLAUDE.md prose predicted `tiny-historical`'s `validation.counts`
  would shift; verified empirically the now-awake validator yields 0 findings on
  that fixture's clean third-person prose, so the oracle correctly stays at
  `warning: 6` (not back-fit). Documentation prose slightly over-predicted; the
  code and oracle are honest.
