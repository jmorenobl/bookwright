# Phase 0 Research — `validate` surfaces ingestion-skipped bible files

All decisions resolved against the existing code; no open NEEDS CLARIFICATION.

## D1 — Read path: consume the memoized `MapResult`, never rebuild the graph

**Decision**: In `commands/validate.py`, read `project.bible().skipped` after
`run_validators(...)` returns; do **not** call `build_project_graph` or re-run
`map_bible` by hand.

**Rationale**: `ValidationContext.bible()` (`validation/base.py:246`) memoizes the
`MapResult` on first call and every prose/character validator already triggers it,
so by the time `_validate` returns from `run_validators` the result is cached — the
skip-merge is a cache hit, not a second ingestion. `MapResult.skipped` is a
`list[SkippedFile{path, reason}]` populated by `map_bible` (`io/bible.py:306+`).
This mirrors how `status` learns about skips (`commands/status.py:151`:
`outcome.report.skipped`) but without the `build_project_graph` round-trip, because
`validate` already has the mapped result in hand.

**Safety on a missing/empty bible dir**: `_map_single_dir` (`io/bible.py:294`)
early-returns when the directory is absent, so `map_bible` always returns a
well-formed `MapResult` with `skipped == []` — reading `.skipped` never raises and
a project with no bible simply produces no skip entries (FR-010).

**Alternatives considered**:
- *A mirror `skipped[]` channel on `ValidationReport`* — rejected by FR-008 (no new
  channel; reuse `not_evaluated[]`).
- *Hard error like `status`* — rejected by the spec's recommended posture
  (surface + degrade green, don't break the exit code; DEBT-018's focus is the
  *silence*, FR-007 / Assumptions).

## D2 — Entry shape: one `NotEvaluatedResult` per skipped file

**Decision**: each skipped file becomes
`NotEvaluatedResult(validator="ingestion", reason="bible file '<path>' skipped
(unusable front-matter): <reason>", kind=NotEvaluatedKind.missing_input)`.

**Rationale**:
- `validator="ingestion"` (FR-004, Clarifications 2026-06-23) — a single shared
  sentinel for the non-validator origin (a skipped file is not a validator). All
  skip entries share it; that shared identifier is exactly the tie FR-009's total
  order resolves.
- `kind=missing_input` (FR-002/FR-006) — a skip is input-conditional (the author
  fixes the YAML and the file is evaluated again), so it **denies green** under the
  044 predicate. `pending_capability` would leave the partial corpus reading green
  — the bug.
- The reason carries the path + cause (FR-003). The path-uniqueness is the only
  load-bearing property (it makes `(validator, reason)` a true total order); the
  exact wording is cosmetic, locked here.

**Import surface**: `NotEvaluatedResult` is re-exported from
`bookwright.validation` (`validation/__init__.py`); `NotEvaluatedKind` is **not**
in that re-export — it is imported from `bookwright.validation.base` (the same path
`report.py` uses). The model is frozen and reused verbatim (FR-011) — no new field,
no new kind.

## D3 — Total-order key, defined once, imported by both sort sites

**Decision**: promote the `not_evaluated` sort from the partial order
`lambda r: r.validator` (`validation/runner.py:80`) to the total order
`(validator, reason)`, defined once as a module-level callable
`not_evaluated_sort_key` in `runner.py` (added to `__all__`) and imported by the
`validate` skip-merge.

**Rationale**: the old key is only a partial order — ties (same validator) fall
back to insertion order. It is safe **today** solely because each validator emits
at most one `not_evaluated` entry, so no ties exist. Skip entries break that
assumption: they all carry `validator="ingestion"`, so without a tie-break two
skipped files could emit in input/filesystem order and the JSON/human report would
not be byte-identical across runs (FR-009, Acceptance Scenario 5). Tie-breaking on
`reason` (which embeds the unique path) restores a total order.

Defining it **once** and importing it at both sites eliminates the divergence
*cause* (no duplicated sort literal to drift), per the zero-debt doctrine and the
Clarifications 2026-06-23 answer — rather than guarding two copies. The sibling
`sort_key` for `Violation` already lives in `runner.py` and is exported, so this
follows the established shape.

**No skip-free reordering (FR-010)**: validator names are already unique among the
runner's own entries, so adding the `reason` tie-break changes no existing order —
pinned skip-free fixtures stay byte-identical (verified by the unchanged suite,
SC-003).

**Alternatives considered**:
- *Sort only in `validate.py`* — rejected: the runner already sorts, so two sort
  sites exist; leaving the runner on the partial key would let the two diverge
  (the exact FR-009 hazard).
- *Sort key in a new shared module* — rejected by FR-012 (no third module; the key
  lives in `runner.py`).

## D4 — Test construction: reuse the proven broken-YAML helper

**Decision**: build the failing project by writing the literal
`"---\nname: : :\n  bad\n---\n"` into a `bible/characters/*.md` file on top of an
existing source-only fixture, then run `graph build` + `validate --json`
in-process via `CliRunner`. Reuse `copy_fixture` and `is_green` from
`tests/conftest.py`.

**Rationale**: that exact broken-YAML literal is already the skip trigger proven in
`tests/commands/test_status_errors.py:108` (it produces a `skipped_sources` abort,
i.e. a real `SkippedFile`), so the new test exercises the same ingestion path the
spec verified by hand (`bible/characters/rota.md`). `is_green` encodes the 044
predicate, so the not-green assertion routes through the production predicate, not a
reimplementation. The cross-command test (SC-004 / User Story 3) reuses the same
project to assert `status` still exits `skipped_sources` while `validate` now
surfaces the file.

## D5 — Gate / exit code is untouched

**Decision**: a skip emits no `Violation`; the exit code is computed exactly as
today.

**Rationale**: `ValidationReport.failed` (`validation/report.py:80`) is
`any(v.severity == Severity.error for v in self.violations)` — it ignores
`not_evaluated` entirely (FR-004). A skip-derived `NotEvaluatedResult` adds to
`not_evaluated[]` only, so `report.failed` is unchanged and `validate`'s
`raise typer.Exit(EXIT_GATE if report.failed else EXIT_OK)` keeps the same exit
code for the same set of findings (FR-007, SC-002, Acceptance Scenario 3).
