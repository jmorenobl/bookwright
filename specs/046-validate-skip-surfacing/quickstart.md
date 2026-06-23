# Quickstart — `validate` surfaces ingestion-skipped bible files

Runnable validation scenarios proving the feature end to end. All run in-process
via `typer.testing.CliRunner` (the harness the other command/E2E tests use), reusing
`copy_fixture` / `is_green` from `tests/conftest.py` and the broken-YAML literal from
`tests/commands/test_status_errors.py`.

Prerequisites: `uv sync`. Reference: [contracts/validate-skip-surfacing.md](./contracts/validate-skip-surfacing.md),
[data-model.md](./data-model.md).

The broken-YAML trigger (proven in `test_status_errors.py`):

```python
(project / "bible" / "characters" / "broken.md").write_text(
    "---\nname: : :\n  bad\n---\n", encoding="utf-8"
)
```

## Scenario 1 — one skipped file is no longer silently green (P1, SC-001)

1. `copy_fixture("tiny-novel", tmp_path)` and `chdir` in; write `broken.md` (above).
2. `bookwright graph build --json` → exit 0 (a partial graph builds; the file is skipped).
3. `bookwright validate --json` → exit 0 (a skip does not gate).
4. Assert `not_evaluated[]` contains exactly one entry with
   `validator == "ingestion"`, `kind == "missing_input"`, and a `reason` naming
   `bible/characters/broken.md`.
5. Assert `is_green(payload) is False`.

**Expected**: the partial corpus stops reading as green; the omitted file is named.

## Scenario 2 — exit code unchanged by a skip (SC-002, Acceptance 3)

1. Same project as Scenario 1.
2. `bookwright validate --json` exit code == the exit code of the same fixture
   **without** the broken file (a skip alone does not break the gate).

**Expected**: the gate stays driven solely by `error`-severity violations (FR-007).

## Scenario 3 — two skips emit deterministically (FR-009, Acceptance 5)

1. Write **two** broken bible files (`broken_a.md`, `broken_b.md`).
2. Run `validate --json` twice.
3. Assert both runs emit two `ingestion` entries in the **same** order
   (byte-identical `not_evaluated[]`), proving `(validator, reason)` resolves the
   shared-`validator` tie.

**Expected**: stable, total-ordered output across runs.

## Scenario 4 — no-skip byte-identity (SC-003, FR-010)

1. `copy_fixture("tiny-novel", tmp_path)` with **no** broken file.
2. `validate --json` produces **no** `ingestion` entry; output is byte-identical to
   the pre-change behavior (the existing suite stays green with unmodified pinned
   fixtures — `test_tri_valued_validation.py` `_EXPECTED_GAPS` unchanged).

**Expected**: zero regression on clean projects.

## Scenario 5 — human report surfaces the skip (User Story 2, SC of P2)

1. Project from Scenario 1.
2. `bookwright validate` (no `--json`) → the `not evaluated:` section lists
   `ingestion [input gap]: bible file 'bible/characters/broken.md' skipped …`.

**Expected**: visible on both surfaces via the existing render (no second channel).

## Scenario 6 — `status` and `validate` agree (User Story 3, SC-004)

1. Project from Scenario 1.
2. `bookwright status --json` → exit 4, `code == "skipped_sources"` (unchanged).
3. `bookwright validate --json` → surfaces the same file in `not_evaluated[]` (new).

**Expected**: the two commands no longer disagree on reportability — `status`
refuses, `validate` surfaces + degrades green.

## Gate check

```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy --strict
```

All four must be green (FR-016).
