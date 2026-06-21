# Quality Audit — 038-character-presence-heading

**Scope:** 1 changed source file + 1 test file + 2 ledger/fixture files vs `main`
**Commit range:** `main`..HEAD (impl is uncommitted in the working tree; spec docs committed)
**Date:** 2026-06-22
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `bookwright-design.md`, `DEBT.md`, `.specify/workflows/bookwright-quality/zero-debt-doctrine.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | 0 |

Coverage gate: PASS (changed module `character_presence.py` at 98.80%; project total 97.50%; threshold = 80%).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "plain-text source of truth … The graph is ALWAYS a derived cache" | `constitution.md` (Principle I) | io-contract | PASS | Prose validator; no graph/SPARQL touched; emitted `Violation`s carry `triples=()` |
| "Every source file ≤ 500 lines" | `CLAUDE.md` (Principle IV) | module-size | PASS | `character_presence.py` = 208 lines |
| "Agent Skills only — no legacy `commands/` directories" | `constitution.md` (Principle VI) | directory-ban | N/A | No skill/integration code in diff |
| "test discipline with ≥ 80 % coverage" | `constitution.md` (Principle VIII) | coverage-threshold | PASS | 98.80% on changed module; never adds `--cov-fail-under` |
| "frozen ontology — 17-class closure must not gain classes" | `constitution.md` (Principle X) | scope-ban | PASS | No `.ttl` / `CLASS_IRI` change |
| "one observable delta per iteration; no plumbing for future X" | zero-debt-doctrine §2 | scope-ban | PASS | Single local `_HEADING_MARKER` + 2-line strip; no shared utility |
| "eliminate the cause, don't contain it" | zero-debt-doctrine §3 | other | PASS | Marker is intrinsic manuscript markdown — no deletable upstream producer; guard is the minimal correct fix |
| "Debt is a CLASS — sweep every instance repo-wide" | zero-debt-doctrine §4 | other | PASS | `character_presence` is the only validator with a line-initial proper-noun heuristic (setting/focalization use closed lexicons; temporal/narrative are SPARQL) |
| "Resolving a debt entry removes it" | `CLAUDE.md` (Scope discipline) | other | PASS | DEBT-008 deleted; "Deuda abierta" now `_Ninguna por ahora._` |
| Workflow trail `specify→clarify→plan→tasks→analyze→implement` | `CLAUDE.md` (Spec Kit) | workflow-step | PASS | spec.md, plan.md, tasks.md, research.md, data-model.md, quickstart.md, checklists/ all present |

## 3. Findings

No findings.

## 4. Remediation Detail

None.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/validation/validators/character_presence.py` | 98.80% | 80% | PASS |
| Project total | 97.50% | 80% | PASS |

The one uncovered branch (`187->185` in `_roster_slugs`) is pre-existing and untouched by this diff.

## 6. Inability-to-verify notes

None — all four gates ran green (`pytest` 1365 passed / 1 skipped, `mypy --strict` clean, `ruff check` clean, `ruff format --check` clean). An independent adversarial second opinion (general-purpose subagent) attempted to refute the zero-debt bar across correctness, zero-debt, layering, and test-gap lenses and returned no BUG/DEBT/LAYERING/TEST-GAP findings.
