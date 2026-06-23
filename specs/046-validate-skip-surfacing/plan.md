# Implementation Plan: `validate` surfaces ingestion-skipped bible files

**Branch**: `046-validate-skip-surfacing` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/046-validate-skip-surfacing/spec.md`

## Summary

When a bible file has unusable front-matter (broken YAML), `map_bible` records it
in `MapResult.skipped` and the entity never enters the graph. `bookwright status`
refuses such a partial corpus outright (`code=skipped_sources`), but `bookwright
validate` — the CI gate — proceeds silently and emits `not_evaluated: []`, so a
partial corpus reads as fully green (the `[]`-lies-as-clean hole 040 set out to
erase; the `status`↔`validate` asymmetry DEBT-018 recorded).

This iteration makes `validate` **consume** the ingestion `skipped` list it
already has in hand (via `ValidationContext.bible().skipped`, the same memoized
`map_bible` the validators trigger) and merge one `NotEvaluatedResult` per skipped
file into the **existing** `not_evaluated[]` channel — `validator="ingestion"`,
`kind=missing_input`, `reason` citing path + cause. The unchanged 044 green
predicate then degrades green automatically (a `missing_input` entry denies green),
matching the refusal `status` already gives. No new channel, no new field, no new
kind, no predicate change.

The only secondary change is a determinism fix the merge forces: the
`not_evaluated` sort key is promoted from the partial order `lambda r: r.validator`
(safe only while each validator emits ≤ 1 entry) to the total order
`(validator, reason)`, defined **once** in `runner.py` and imported by both sort
sites (runner + the `validate` skip-merge) so the two cannot drift (FR-009). Skip
entries all share `validator="ingestion"`, so the tie-break on `reason` (paths are
unique) is what keeps multi-skip runs byte-identical.

## Technical Context

**Language/Version**: Python 3.11+ (`from __future__ import annotations`, `StrEnum`).

**Primary Dependencies**: stdlib only for this change. No new runtime dependency
(FR-014, Constitution II). Reuses `typer`/`rich` already in `validate.py`.

**Storage**: none. Validation persists nothing (FR-020); the ingestion `skipped`
list is read in-memory from the already-cached `MapResult`. The graph is **not**
rebuilt — the merge reads `project.bible().skipped`, the same memoized call the
validators trigger (research D1).

**Testing**: `pytest` via `typer.testing.CliRunner` in-process, reusing the
broken-YAML helper (`"---\nname: : :\n  bad\n---\n"`) already proven in
`tests/commands/test_status_errors.py` and the `copy_fixture` / `is_green`
helpers in `tests/conftest.py` (research D4).

**Target Platform**: CLI (`bookwright validate`), same as today.

**Project Type**: single project (src-layout, `src/bookwright/`).

**Performance Goals**: none beyond "no second graph build" — the change adds an
O(#skipped) list merge + one re-sort, negligible.

**Constraints**: each changed file ≤ 500 lines (Principle IV); the `--json` body is
the single stdout document (Principle IX); the gate stays driven solely by
`error`-severity violations (FR-007); the frozen ontology and every **validator**
module are untouched (FR-012).

**Scale/Scope**: a two-file change — `commands/validate.py` (the skip-merge) and
`validation/runner.py` (owns + exports the shared total-order key) — plus the
contract-before-code design edits, a DEBT-018 removal, and tests. No data-model
change.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Verdict | Notes |
|---|---|---|
| I — Plain text as source of truth | ✅ | Reads the in-memory `MapResult`; persists nothing; the design contract (`bookwright-design.md` § 13.4) and `DEBT.md` stay the plain-text record. |
| II — Modern Python stack / deps | ✅ | stdlib only; no dependency-list change (FR-014). |
| III — src-layout | ✅ | Edits live under `src/bookwright/`; tests under `tests/`. |
| IV — Modular command surface, ≤ 500 lines | ✅ | `validate.py` (147 → ~165) and `runner.py` (81 → ~90) stay well under 500 (FR-015). |
| V — Plugin integrations | ✅ | Untouched. |
| VI — Agent Skills only | ✅ | Untouched. |
| VII — agentskills.io compliance | ✅ | No skill change. |
| VIII — Test discipline ≥ 80 % | ✅ | New empirical tests; four gates stay green (FR-016). |
| IX — JSON-over-stdout | ✅ | Skip entries ride the existing `not_evaluated[]` serialization; one stdout document; exit code unchanged (FR-007/FR-008). |
| X — Design-document axioms | ✅ | No § 16 axiom reopened. |

**Scope & Release Discipline**: no speculative plumbing — the change only consumes
the 040/044 channel on an existing, verified-reachable input. No new `skipped[]`
channel is added (FR-008). **Initial Constitution Check: PASS. Post-Design
re-check: PASS** (no new violation introduced by the design below).

## Project Structure

### Documentation (this feature)

```text
specs/046-validate-skip-surfacing/
├── plan.md              # This file
├── spec.md              # Feature spec (already present)
├── research.md          # Phase 0 output (this run)
├── data-model.md        # Phase 1 output (this run)
├── quickstart.md        # Phase 1 output (this run)
├── contracts/
│   └── validate-skip-surfacing.md   # the observable contract delta
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── commands/
│   └── validate.py        # CHANGE: after run_validators, merge one NotEvaluatedResult
│                          #   per project.bible().skipped into not_evaluated, re-sort
│                          #   with the shared total-order key (imported from runner).
├── validation/
│   ├── runner.py          # CHANGE: promote the not_evaluated sort to a total order
│   │                      #   (validator, reason); expose it as a shared module-level
│   │                      #   callable in __all__ for validate.py to import (FR-009).
│   ├── base.py            # UNCHANGED: NotEvaluatedResult / NotEvaluatedKind reused.
│   └── report.py          # UNCHANGED: green predicate, serialization, render reused.
└── io/
    ├── bible.py           # UNCHANGED: MapResult.skipped is read, not changed.
    └── report.py          # UNCHANGED: SkippedFile{path, reason} reused.

bookwright-design.md       # CONTRACT-BEFORE-CODE: § 13.4 gains the `ingestion`
                           #   pseudo-source paragraph; § 13.5 move-1 note reconciled
                           #   (skips are now surfaced by validate). Edit BEFORE code.
DEBT.md                    # REMOVE DEBT-018; reconcile its track-A cross-reference.

tests/
├── commands/
│   └── test_validate_skipped.py   # NEW: P1/P2/P3 + multi-skip determinism + no-skip
│                                  #   byte-identity (SC-001..005).
└── e2e/
    └── test_tri_valued_validation.py  # UNCHANGED unless a pinned fixture moves
                                       #   (none do — skip-free fixtures are byte-identical).
```

**Structure Decision**: single-project src-layout (unchanged). The change is
deliberately confined to the two modules FR-012 names; no validator module, no
data-model module, and no third helper module is introduced (the shared key lives
in `runner.py`, not a new file).

## Phase 0 — Research

See [research.md](./research.md). Decisions resolved (no open NEEDS CLARIFICATION):

- **D1 — read path, no rebuild**: `project.bible().skipped` is read in
  `commands/validate.py`; `map_bible` is memoized on `ValidationContext` and already
  triggered by the validators, so this is a cache hit, not a second graph build. It
  is safe on a missing/empty bible dir (`_map_single_dir` early-returns → empty
  `skipped`).
- **D2 — entry shape**: `NotEvaluatedResult(validator="ingestion", reason=…,
  kind=NotEvaluatedKind.missing_input)`, reason template `bible file '<path>'
  skipped (unusable front-matter): <reason>` (FR-003/FR-004, Clarifications).
- **D3 — total-order key, single definition**: promote the runner's
  `not_evaluated` sort to `(validator, reason)`; define it once as
  `not_evaluated_sort_key` in `runner.py` (added to `__all__`) and import it in
  `validate.py` (FR-009). No skip-free fixture reorders (validator names already
  unique — FR-010).
- **D4 — test reuse**: reuse the broken-YAML literal and the `copy_fixture` /
  `is_green` helpers; build the failing project on top of an existing source-only
  fixture.
- **D5 — gate/exit unchanged**: a skip is not a `Violation`; `report.failed` reads
  only `error`-severity violations, so the exit code is untouched (FR-007).

## Phase 1 — Design & Contracts

- [data-model.md](./data-model.md): no new types. Documents that
  `NotEvaluatedResult` (frozen, 044) is reused verbatim with a sentinel
  `validator="ingestion"`, and that `MapResult.skipped : list[SkippedFile{path,
  reason}]` is the read-only input.
- [contracts/validate-skip-surfacing.md](./contracts/validate-skip-surfacing.md):
  the observable `--json` and human-report delta for a skipped bible file, the
  byte-identity guarantees, and the unchanged green predicate / exit code.
- [quickstart.md](./quickstart.md): runnable validation scenarios (one-skip,
  two-skip determinism, no-skip byte-identity, `status` cross-command agreement).
- **Contract-before-code (plan § 7.3 discipline)**: update `bookwright-design.md`
  § 13.4 (add the `ingestion` pseudo-source paragraph to the not-evaluated channel
  description) and reconcile § 13.5 move-1 (skips are surfaced by `validate`)
  **before** the code diverges. The design is the binding contract; it leads.
- **Agent context**: the managed Spec Kit block in `CLAUDE.md` is repointed to this
  plan.

### Key design decisions (the whole change, concretely)

1. **`runner.py` — promote + share the key.** Replace the inline
   `not_evaluated.sort(key=lambda r: r.validator)` with a module-level callable:

   ```python
   def not_evaluated_sort_key(result: NotEvaluatedResult) -> tuple[str, str]:
       """Total order for not_evaluated[] (FR-009): (validator, reason).

       A total order, not the old partial `validator`-only key: skip entries all
       share validator="ingestion", so the reason tie-break (paths are unique) is
       what keeps multi-skip runs byte-identical. The single shared definition both
       the runner and the validate skip-merge import — no duplicated sort literal.
       """
       return (result.validator, result.reason)
   ```

   Add `not_evaluated_sort_key` to `__all__`; the runner sorts with it.

2. **`commands/validate.py` — merge skips after the run.** In `_validate`, after
   `run_validators(...)` returns `not_evaluated`, before building the
   `ValidationReport`:

   ```python
   from bookwright.validation import NotEvaluatedResult
   from bookwright.validation.base import NotEvaluatedKind
   from bookwright.validation.runner import not_evaluated_sort_key

   skip_entries = [
       NotEvaluatedResult(
           "ingestion",
           f"bible file '{s.path}' skipped (unusable front-matter): {s.reason}",
           NotEvaluatedKind.missing_input,
       )
       for s in project.bible().skipped
   ]
   merged = sorted([*not_evaluated, *skip_entries], key=not_evaluated_sort_key)
   report = ValidationReport(..., not_evaluated=tuple(merged))
   ```

   `NotEvaluatedResult` is re-exported from `bookwright.validation`;
   `NotEvaluatedKind` is imported from `bookwright.validation.base` (where it is
   defined and where `report.py` already imports it — it is **not** in the package
   `__init__` re-exports); the sort key is imported from `runner`. No new module.

3. **Nothing else moves.** `base.py`, `report.py` (green predicate, `_KIND_LABEL`
   render, `to_json`), `status.py` (aborts on a skip before embedding validation —
   FR-008), the nudge / `_REMEDIES`, and every validator are untouched.

### Known regression / debt accounting

- **Removed**: DEBT-018 (closed by this iteration — FR-013); its track-A
  cross-reference (`DEBT.md` line ~51 `Track A … DEBT-018, DEBT-019`) is
  reconciled to drop the dangling pointer.
- **Untouched debt**: DEBT-019 (partial-evaluation contract) is out of scope and
  stays recorded. No new debt is introduced.

## Complexity Tracking

No constitutional violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
