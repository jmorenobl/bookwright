# Quality Audit — 049-narrative-unit-identifier

**Scope:** 9 changed files vs `main` (2 source, 3 test/fixture, DEBT.md, design, roadmap, tasks)
**Commit range:** 493ea04..d62d707 (+ uncommitted implementation in working tree)
**Date:** 2026-06-24
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `DEBT.md`, `bookwright-design.md`, `bookwright-roadmap.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 (1 found and fixed during the pass) |
| LOW | 0 |
| **Total** | 0 open |

Coverage gate: PASS (`narrative_structure.py` 100%, `queries.py` 92.96%; total 97.67%, threshold = 80%).

One MEDIUM finding (dead multi-label dedup branch in `load_orphan_units`) was surfaced
by the adversarial pass and **fixed in-place during this audit** — the function now
sorts by the unique URI with no per-URI dedup loop, since each `G9` emits exactly one
`rdfs:label` (iter 035). No findings remain open.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The graph is ALWAYS a derived cache … never the source" | `zero-debt-doctrine.md:18` (Principle I) | layout | PASS | Change only *reads* `rdfs:label` (iter 035) from the loaded derived graph; writes no triples |
| "every source file ≤ 500 lines" | `CLAUDE.md` (Principle IV) | module-size | PASS | `queries.py` 252 ln, `narrative_structure.py` 128 ln |
| "one CLI subcommand per module" | `CLAUDE.md` (Principle IV) | layout | PASS | No CLI module touched |
| "Agent Skills only — never `.claude/commands/`" | `CLAUDE.md` (Principle VI) | directory-ban | PASS | No skill / commands path in diff |
| "≥ 80 % coverage, single-sourced `fail_under`; no `--cov-fail-under`" | `CLAUDE.md` (Principle VIII) | coverage-threshold | PASS | 97.67%; no `--cov-fail-under` added |
| "frozen 17-class ontology must not gain classes" | `CLAUDE.md` (Principle X) | scope-ban | PASS | No ontology / `.ttl` change |
| "no new runtime dependency without amendment" | `CLAUDE.md` (Stack, Constitution II) | dependency | PASS | No dependency change |
| "one observable delta per iteration; no future-X plumbing" | `zero-debt-doctrine.md:29` | scope-ban | PASS | Single delta: unit-identifier text; dead defensive branch removed, not added |
| "resolved debt is removed from `DEBT.md`, not marked done" | `CLAUDE.md` (Scope discipline) | other | PASS | DEBT-017 entry deleted; reconciled in roadmap §B + design §13 |
| Workflow trail: specify→clarify→plan→tasks→analyze→implement | `CLAUDE.md` | workflow-step | PASS | spec/plan/tasks/research/data-model/contracts/quickstart/checklists all present |
| Track integrity: `specs/049-*` artifacts tracked | `CLAUDE.md` (Principle I) | track-integrity | PASS | committed (specs) + this audit's working-tree edits to be committed in the same commit |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | MEDIUM (fixed) | `validation/queries.py:205-215` (pre-fix) | Multi-label dedup loop defends an impossible state (each `G9` emits one `rdfs:label`, iter 035) → unreachable branch, uncovered | Collapse to `sorted(((uri, label) …), key=uri)`; document the one-row-per-URI invariant. **Done in this pass.** |

## 4. Remediation Detail

### R1 — Dead multi-label dedup in `load_orphan_units` (fixed)

- **Where:** `src/bookwright/validation/queries.py` (former lines 205-215)
- **Why it mattered:** the `if uri not in labels … else smallest-label` loop only runs
  when one `G9` URI yields multiple rows, i.e. multiple `rdfs:label` triples per unit.
  `golem/modules/narrative.py:50` emits exactly one label per `G9`, so the branch is
  unreachable and was uncovered by the suite — exactly the "contain the smell with a
  justified guard" pattern the zero-debt doctrine §3 says to delete rather than carry.
- **Change applied:** the query result is now
  `sorted(((row["unit"], row.get("label")) for row in rows), key=lambda pair: pair[0])`.
  URIs are unique (one row per orphan unit), so sorting by URI is byte-stable and no
  dedup is needed; the invariant is documented in the docstring. The `_unit_identifier`
  slug fallback (FR-004 floor) is retained — it is a 3-line total function over its
  declared `str | None`, not a guard against an impossible multi-row state.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `validation/validators/narrative_structure.py` | 100.00% | 80% | PASS |
| `validation/queries.py` | 92.96% | 80% | PASS (uncovered line 126 is pre-existing, unrelated to this diff) |
| **Total** | 97.67% | 80% | PASS |

## 6. Inability-to-verify notes

None. All four gates (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest`)
ran green after the R1 fix.
