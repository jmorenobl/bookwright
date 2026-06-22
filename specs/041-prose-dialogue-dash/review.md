# Quality Audit — 041-prose-dialogue-dash

**Scope:** 4 source/test/oracle files (+ spec artifacts) vs `main`
**Commit range:** dba608c..6b08779 (+ uncommitted oracle/tasks edits)
**Date:** 2026-06-22
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `DEBT.md`, `.specify/workflows/bookwright-quality/zero-debt-doctrine.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 (resolved in this pass) |
| LOW | 0 |
| **Total** | 1 |

Coverage gate: **PASS** (97.57% total; `character_presence.py` 98.85%, `io/prose.py` 100%, threshold = 80%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The graph is ALWAYS a derived cache … never the source" | constitution I | layout | PASS | No graph/source-of-truth change; prose seam only |
| "Agent Skills only — never write to `.claude/commands/`" | constitution VI | directory-ban | N/A | No skills/commands touched |
| "≥80% coverage, single-sourced in `[tool.coverage.report]`" | constitution VIII | coverage-threshold | PASS | 97.57%; no `--cov-fail-under` added |
| "Every source file ≤ 500 lines" | constitution IV | module-size | PASS | `io/prose.py` 87 lines |
| "Stdlib only — `re`, no Markdown parser" | spec FR-012 | dependency | PASS | `pyproject.toml` runtime deps unchanged |
| "Frozen ontology untouched; prose validators emit `triples=()`" | constitution X | io-contract | PASS | No `.ttl`/`CLASS_IRI` change; validator diff empty |
| "No validator code edited (close the class at the SEAM)" | spec SC-004 | scope-ban | PASS | `git diff` touches only `io/prose.py` in `src/` |
| Workflow trail: specify→…→implement artifacts present | CLAUDE.md | workflow-step | PASS | spec/plan/tasks/research/data-model/contracts all present |
| Track integrity: spec dir committed | CLAUDE.md | track-integrity | PASS | All `specs/041-*` tracked; only `tasks.md`/oracle uncommitted (this review will commit) |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A/B | MEDIUM (resolved) | `src/bookwright/io/prose.py:38`; `DEBT.md` DEBT-011 | The horizontal bar `―` (U+2015) was deferred to DEBT-011 bundled with quotes, but it is a *same-class AND same-design* dialogue dash (glued, unpaired) whose fix is one code point — deferring it is the whack-a-mole issue #1 / doctrine § 4 forbid. | **Fixed in this review pass:** added `―` to `_DIALOGUE_MARKER`'s class (`[—–]`→`[—–―]`), added seam test rows D10/D11, and narrowed DEBT-011 to the genuinely-distinct *paired* quote markers (`«`/`"`/`'`). |

### R1 — Horizontal bar U+2015 belongs in the swept class, not deferred

- **Where:** `src/bookwright/io/prose.py:38` (`_DIALOGUE_MARKER`); `DEBT.md` DEBT-011.
- **Why it matters:** Issue #1's mandate (and zero-debt doctrine § 4) is to close the
  *class* at the seam, sweeping every instance you touch. The independent adversarial
  reviewer correctly isolated U+2015 from the quote markers: quotes are a distinct
  *paired* design (open/close, mid-line content, `¿¡` overlap), but `―` is a leading
  dialogue dash identical in semantics to `—`/`–` — one extra code point, no design
  question. Leaving it in DEBT-011 left a known-failing instance of the very class the
  iteration exists to close (`―Esto` fired today, verified empirically).
- **Resolution:** swept `―` into `_DIALOGUE_MARKER` (`[—–―]`) at the seam, with no
  validator change; added seam test rows D10/D11; rewrote DEBT-011 to cover only the
  leading *quote* markers; updated spec.md SC-006 / Out-of-Scope, research.md D3, and
  plan.md D3 to record the class as closed in full (`—`/`–`/`―`). All gates re-run green.

Everything else holds: the fix adds a third `elif` to the existing iterative
`_normalize` loop and edits no validator code (SC-004); it reuses `character_presence`'s
pre-existing sentence-initial exemption (the mechanism iteration 038 used for ATX
headings), so no new guard/allowlist/suppression was introduced. The `# noqa` comments
suppress ruff's ambiguous-unicode lint on the dash *literals that are the feature
itself* — the cause is not deletable, so the suppression is correct. DEBT-010
(incomplete cross-roster for multi-word settings) and DEBT-011 (leading paired quotes)
are recorded in `DEBT.md` as genuinely out-of-scope, different debt classes — not dropped.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/io/prose.py` | 100% | 80% | PASS |
| `src/bookwright/validation/validators/character_presence.py` | 98.85% | 80% | PASS |
| TOTAL | 97.57% | 80% | PASS |

## 6. Inability-to-verify notes

None. All four gates (`pytest`, `mypy --strict`, `ruff check`, `ruff format --check`)
were run and are green.
