# Quality Audit — 039-prose-structure-seam

**Scope:** prose/structure seam (`io/prose.py`) + 3 validators rewritten, `base.py` accessors
**Commit range:** origin/main..HEAD (+ uncommitted implementation)
**Date:** 2026-06-22
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `DEBT.md`, `bookwright-design.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 (fixed) |
| LOW | 2 (1 fixed, 1 doc note added) |
| **Total** | 3 (all resolved) |

Coverage gate: **PASS** (97.52% total; `io/prose.py` 100%, all three validators ≥97%; threshold 80%).
Four gates green: pytest (1395 passed), mypy --strict, ruff check, ruff format --check.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "graph is ALWAYS a derived cache … never the source" (I) | constitution.md | io-contract | PASS | Prose validators are graph-free, `triples=()`; no indexer writes |
| "Every source file ≤ 500 lines" (IV) | CLAUDE.md | module-size | PASS | prose 80, base 283, char_presence 207, focalization 167, setting 108 |
| "no new dependency, no Markdown AST" (FR-012) | spec.md | dependency | PASS | `io/prose.py` imports only `re` + `dataclasses` |
| "≥80% coverage, single-sourced fail_under" (VIII) | constitution.md | coverage-threshold | PASS | 97.52%; no `--cov-fail-under` added |
| "frozen ontology — prose validators emit no triples" (X) | CLAUDE.md | io-contract | PASS | `triples=()` asserted in tests; no `.ttl` change |
| "no validator calls splitlines() any longer" (SC-002) | spec.md | scope-ban | PASS | grep: zero `splitlines()` in validators; deleted strippers gone |
| "each source split ONCE per run via cached accessor" (FR-006) | spec.md | io-contract | PASS (after fix) | `constitution_view()` now consumed by focalization (was dead) |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | MEDIUM | focalization.py:67-72, base.py:276 | `constitution_view()` was dead production code — only its own test called it; `_parse_declaration` re-split via `prose_view(constitution_text())`, leaving FR-006's "shared accessor" unrealized | FIXED — `validate()` consumes `project.constitution_view()`; `_parse_declaration` takes a `ProseView`; redundant `constitution_text()` guard + local import deleted |
| R2 | B | LOW | setting_continuity.py:59 | `texts = dict(files)` rebuilt once per setting (loop-invariant) | FIXED — hoisted into `validate()`, built once and shared |
| R3 | A | LOW | spec.md edge cases | Shared seam widens focalization recognition (heading-/nested-prefixed declaration now parses) — intended but unstated | FIXED — added a one-line edge-case note (inert on live fixtures, SC-001 parity holds) |

## 4. Remediation Detail

### R1 — Dead `constitution_view()` accessor (MEDIUM)
- **Where:** `validation/base.py:276` (accessor), `validators/focalization.py:67-72` (consumer).
- **Why it matters:** FR-006 mandates a cached `constitution_view()` "so each source is split once per run and shared across validators." The implementation added the accessor (satisfying the letter + a test) but `focalization` re-split the constitution itself via `prose_view(constitution_text())`, so the accessor had no production caller — plumbing justified only by "future X" (YAGNI), and FR-006's intent unmet.
- **Change applied:** `_parse_declaration(view: ProseView, …)`; `validate()` passes `project.constitution_view()`; the redundant `constitution_text()` + `None` guard and the local `prose_view` import were deleted. 9 unit-test call sites wrapped in `prose_view(...)`. Behavior byte-identical (constitution-absent → `()` → `None` → `[]`).

### R2 — Per-setting dict rebuild (LOW)
- **Where:** `validators/setting_continuity.py:59`.
- **Why it matters:** `_check_setting` runs once per setting; `dict(files)` is loop-invariant, so the map was rebuilt O(settings) times — new redundant work the refactor introduced.
- **Change applied:** hoisted `texts = dict(project.manuscript_files())` into `validate()`, passed the mapping down.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| io/prose.py | 100.00% | 80% | PASS |
| validation/base.py | 95.54% | 80% | PASS |
| validators/character_presence.py | 98.80% | 80% | PASS |
| validators/focalization.py | 97.46% | 80% | PASS |
| validators/setting_continuity.py | 97.26% | 80% | PASS |

## 6. Inability-to-verify notes

None. All four gates ran locally and are green; an independent adversarial subagent
refuted across 8 categories and surfaced no bug/debt-severity finding beyond the
three above (all resolved).
