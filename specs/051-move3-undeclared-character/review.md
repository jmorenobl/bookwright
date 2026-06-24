# Quality Audit — 051-move3-undeclared-character

**Scope:** 4 changed source/skill files + 4 test files + docs vs `main`
**Commit range:** e7bfe01..HEAD (+ uncommitted working tree)
**Date:** 2026-06-24
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `DEBT.md`, `bookwright-design.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; total 97.68%, `status/rules.py` at 98.55%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "plain-text source of truth … graph is ALWAYS a derived cache" | constitution.md (I) | layout | PASS | No graph mutation; rule reads aggregated `StatusState` only |
| "Agent Skills only — never write to `.claude/commands/`" | constitution.md (VI) | directory-ban | PASS | Diff touches only `resources/commands/*.md` source (materialized as SKILL.md); no `.claude/commands/` write |
| "≥80% coverage, single-sourced `fail_under=80`; no `--cov-fail-under`" | constitution.md (VIII) | coverage-threshold | PASS | 97.68% total; no `--cov-fail-under` added |
| "Every source file ≤500 lines" | CLAUDE.md (IV) | module-size | PASS | rules.py 250, descriptions.py 48, continuity.md 99, golem-character.md 79 |
| "one CLI subcommand per module" | CLAUDE.md (IV) | layout | PASS | No CLI verb added; `status/rules.py` is a pure state→actions table |
| "agent-facing cmd emits single JSON doc on stdout under --json" | CLAUDE.md (IX) | io-contract | PASS | `status` envelope untouched; rule only adds an `Action` payload |
| "Agent Skill `description` ≤1024 chars, valid YAML front-matter" | constitution.md (VII) | frontmatter-constraint | PASS | continuity description 822 chars; front-matter valid (lint_skill_md green) |
| "skill desc mirrored verbatim into SKILL_DESCRIPTIONS (SC-009)" | plan.md / descriptions.py | io-contract | PASS | descriptions.py == folded front-matter, byte-equal (test_descriptions.py green) |
| "no new runtime dependency (locked stack, Constitution II)" | CLAUDE.md / constitution.md (II) | dependency | PASS | No import/dep added; rule uses existing `NotEvaluatedKind` import only |
| "frozen ontology — no new GOLEM class (Principle X)" | CLAUDE.md (X) | scope-ban | PASS | No `golem/` or `.ttl` change; roster read is skill-layer prose |
| "move 3 is the SKILL layer — no new validator in validation/" | plan.md | scope-ban | PASS | `validation/` diff empty (committed + uncommitted) |
| "green predicate byte-identical; pending_capability never tumbles green (FR-010)" | plan.md / spec.md | io-contract | PASS | `validation/report.py` untouched; tiny-historical stays `status: ok` |
| "validator `character_unknown_mentions` UNCHANGED (FR-011)" | plan.md | scope-ban | PASS | validator diff empty |
| "Spec Kit workflow trail (specify→…→implement) produces artifacts" | CLAUDE.md | workflow-step | PASS | spec/plan/tasks/research/data-model/contracts/quickstart all present |
| "out-of-scope debt recorded in DEBT.md, never dropped" | CLAUDE.md scope discipline | scope-ban | PASS | DEBT-013 closed (struck); DEBT-021 left open as a distinct future slice |

**A.3 — Track integrity:** `specs/051-move3-undeclared-character/` files are all in the branch diff (committed) or `git status` (tasks.md modified, to be committed in this step). No on-disk-but-git-invisible governance file. OK.

**A.4 — Workflow trail:** spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/, quickstart.md, checklists/requirements.md all exist on branch; implementation present under `src/`. Trail intact.

## 3. Findings

None. The diff introduces no CRITICAL/HIGH/MEDIUM/LOW finding.

## 4. Remediation Detail

N/A — no findings.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/status/rules.py` | 98.55% | 80% | PASS (only uncovered branch `75->77` is pre-existing in `_research_queue`) |
| `src/bookwright/integrations/descriptions.py` | (data module) | 80% | PASS |
| project total | 97.68% | 80% | PASS |

New behavior covered: `judge_undeclared_characters` fire path (`test_judge_undeclared_characters_action_exact_match`), focalization-source non-fire (`test_focalization_capability_gap_does_not_fire_the_judge_nudge`), both-kinds ordering (`test_*` in test_rules.py), e2e length 4, fixture expected-status.

## 6. Inability-to-verify notes

The skill's LLM-judged prose output is correctly NOT unit-asserted (verify/continuity precedent); what is empirically tested is materialization, lint, bilingual triggers, and the new `next_action`. This is the intended contract, not a coverage gap.

**Verdict: meets the zero-debt bar. No remediation required.**
