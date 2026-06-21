# Quality Audit — 033-remove-dead-narrativerole

**Scope:** 9 changed source/test files vs origin/main (22 total incl. spec artifacts)
**Commit range:** origin/main..HEAD (+ working-tree review fix)
**Date:** 2026-06-21
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.5.0), `DEBT.md`, `.specify/workflows/bookwright-quality/zero-debt-doctrine.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 1 |
| **Total** | 1 |

Coverage gate: PASS (97.30% total, threshold = 80%; `narrative_structure.py` 100%, all touched golem modules ≥97%).

All four gates green: `pytest` 1322 passed / 1 skipped, `mypy --strict` clean (260 files), `ruff check` clean, `ruff format --check` 261 files formatted.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "plain-text source of truth … graph is ALWAYS a derived cache" | constitution.md (I) | io-contract | PASS | No graph/source change; only registry + tests + ledger touched |
| "Agent Skills only — never write to `.claude/commands/`" | constitution.md (VI) | directory-ban | N/A | No skill/integration files in diff |
| "≥80% coverage, single-sourced fail_under; no `--cov-fail-under`" | constitution.md (VIII) | coverage-threshold | PASS | 97.30%; no `--cov-fail-under` added |
| "Every source file ≤ 500 lines" | CLAUDE.md (IV) | module-size | PASS | `narrative.py` 64L, `feature.py` ~170L, `__init__.py` <80L |
| "Ontology frozen — 17-class CLASS_IRI must not gain classes" | constitution.md (X) | scope-ban | PASS | `CLASS_IRI` still 17 (12 concept + 5 carrier); `golem.ttl` untouched; `G11_Narrative_Role` preserved |
| "Don't implement ahead of the plan / scope discipline" | CLAUDE.md | scope-ban | PASS | Pure deletion + parity hardening; no speculative plumbing; G6/G3 deferrals untouched |
| "Debt is a CLASS — sweep every instance repo-wide" | zero-debt-doctrine §4 | other | PASS | All live "thirteen"/"eleven" count prose swept; CHANGELOG history correctly preserved |
| "Found debt is never left untracked" | zero-debt-doctrine §5 | track-integrity | PASS | DEBT-001 removed (resolved); DEBT-003 recorded for out-of-scope design-doc drift |
| "design.md / roadmap edits in Spanish" | CLAUDE.md | other | PASS | roadmap §4 + DEBT.md edits in Spanish |

Track integrity (A.3): all `specs/033-*` artifacts appear in the branch diff; no uncommitted/untracked governance file. Workflow trail (A.4): spec → plan → tasks → analyze (resolution commit `8f95cbf`) → implement all present.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | LOW | bookwright-design.md:203 | Canonical URI-table still lists G11 segment `narrative-role`, which no code mints (real materialization is `{character}/role/{slug}`) | Out-of-scope (frozen canonical doc, pre-existing drift, spec deliberately excluded it). Recorded as DEBT-003; resolve in a design-doc iteration. |

## 4. Remediation Detail

### R1 — Stale `narrative-role` URI segment in frozen design table (recorded as DEBT-003)
- **Where:** `bookwright-design.md:203`
- **Why it matters:** the canonical design's per-concept URI table assigns G11 a top-level `narrative-role` segment that was never materialized (it was the dead `NarrativeRole.path_segment`, removed this iteration). The live `CharacterRole` node uses `{character}/role/{slug}`. The design already states the correct semantics at line 1603 (G11 = "rol de un personaje") and § 7.4, so this is an internal doc inconsistency, pre-existing this iteration.
- **Suggested change:** none now — recorded in `DEBT.md` as DEBT-003. `bookwright-design.md` is the owner-authored frozen canonical spec (load-bearing numbering); spec-033 deliberately scoped doc edits to `DEBT.md` + roadmap §4 and cites the design as authority. Editing it belongs in a documentation iteration, in Spanish, without renumbering.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| golem/__init__.py | 100% | 80% | PASS |
| golem/modules/narrative.py | ≥97% | 80% | PASS |
| golem/modules/feature.py | ≥97% | 80% | PASS |
| golem/deferrals.py | 100% | 80% | PASS |
| **TOTAL** | 97.30% | 80% | PASS |

## 6. Inability-to-verify notes

None — all four gates ran locally and passed.
