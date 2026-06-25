# Quality Audit — 053-move3-first-person-honesty

**Scope:** 5 changed source files (+ tests, docs) vs `main`
**Commit range:** 8b593b8..HEAD (working tree)
**Date:** 2026-06-25
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `DEBT.md`, `bookwright-design.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: **PASS** (changed validators `focalization` / `character_unknown_mentions` at 100.00%; total 97.68%, threshold = 80%).
Four gates: `pytest` 1490 passed / 1 skipped, `mypy --strict` clean (268 files), `ruff check` clean, `ruff format --check` clean.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "plain-text source of truth … graph is ALWAYS a derived cache" | constitution.md (I) | layout | N/A | No graph/cache code touched |
| "Agent Skills only — no legacy `commands/` directories" | constitution.md (VI) | directory-ban | PASS | No write to `.claude/commands/`; no `SKILL.md` changed |
| "test discipline with ≥ 80 % coverage" | constitution.md (VIII) | coverage-threshold | PASS | 97.68% total; changed validators 100% |
| "Every source file ≤ 500 lines" | constitution.md (IV) | module-size | PASS | base.py 463 (max), focalization 208, rules 288, runner 121 |
| "substituting any [stack dep] requires an amendment" | constitution.md (II) | dependency | PASS | `pyproject.toml`/`uv.lock` unchanged |
| "any agent-consumed subcommand … single JSON document on stdout" | constitution.md (IX) | io-contract | PASS | `code` added additively to `not_evaluated[]` JSON; no stdout change |
| "do NOT add `--cov-fail-under` anywhere" | CLAUDE.md | coverage-threshold | PASS | No coverage config touched |
| "`code` is NOT a sort term" (spec FR-005a) | plan.md / spec.md | io-contract | PASS | `not_evaluated_sort_key` stays `(validator, reason)` (runner.py:73) |
| "the raised `NotEvaluated` does NOT gain `code`" | plan.md | io-contract | PASS | `NotEvaluated.__init__` unchanged (base.py:155) |
| "`_first_person_breaks` / regex / 4 missing_input raises UNTOUCHED" | plan.md | scope-ban | PASS | byte-identical (focalization.py:82,104,111,154,194,197) |
| "REMOVING any DEBT.md entry [forbidden]" | plan.md | scope-ban | PASS | DEBT-021 updated, not removed |
| "no new validator in `validation/`" | plan.md | scope-ban | PASS | No new validator module |
| Workflow trail (specify→…→implement) | CLAUDE.md | workflow-step | PASS | spec/plan/tasks/contracts/data-model all present in specs/053 |

## 3. Findings

No findings. The diff implements exactly the contracted delta:

- `Abstention` + `NotEvaluatedResult` gain `code: str | None = None`, serialized additively in
  `NotEvaluatedResult.to_json` (mirrors how 044 added `kind`).
- The runner's single `_record` naming point stamps `code`: form (c) passes `abstention.code`,
  form (b) defaults `None`. No second naming authority.
- `focalization` declares `code="first_person_recall"` under BOTH third-person branches (the
  non-limited branch now wrapped in `EvalResult`); the existing head-hopping abstention gains
  `code="head_hopping"`. The deterministic core is byte-identical.
- `character_unknown_mentions` converts form (b)→(c) to carry `code="undeclared_characters"`
  (observationally additive — only the `code` key changes from `null`).
- `status._judges(validator, code)` keys precisely; `judge_head_hopping` no longer mis-fires on
  the new recall abstention.

Zero-debt check: the `recall` Abstention is hoisted to a shared local before the limited/non-limited
split (focalization.py:124) — DRY, not a guard. No suppression/justification-comment smell with a
deletable cause behind it.

## 4. Remediation Detail

None required.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `validation/validators/focalization.py` | 100.00% | 80% | PASS |
| `validation/validators/character_unknown_mentions.py` | 100.00% | 80% | PASS |
| `validation/base.py` | 100.00% | 80% | PASS |
| `validation/runner.py` | 100.00% | 80% | PASS |
| `status/rules.py` | 100.00% | 80% | PASS |
| **Total** | 97.68% | 80% | PASS |

## 6. Inability-to-verify notes

None. All four gates ran locally and green. An independent adversarial subagent attempted to refute
the zero-debt bar on seven fronts and returned no must-fix findings.
