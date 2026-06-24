# Quickstart: Verify the unified narrative-unit identifier (iteration 049)

A run guide proving DEBT-017 is closed: both `narrative_structure` rules name a
`G9` unit by its human authored name, identically. Implementation details live in
[plan.md](./plan.md) / [data-model.md](./data-model.md); message behavior in
[contracts/narrative-unit-identifier.md](./contracts/narrative-unit-identifier.md).

## Prerequisites

```bash
uv sync
```

## Scenario 1 — Unit + E2E suites (the oracle proof)

```bash
uv run pytest tests/validation/test_narrative_structure.py tests/e2e/test_narrative_workflow.py
```

**Expected**: green. The orphan-beat oracle now asserts the **human name**:
- `test_orphan_beat_flagged_sequenced_not` finds `"Orphan Beat"` in the message
  (not the `orphan-beat` slug).
- `test_validate_reports_the_orphan_beat` (over `tiny-quest`) matches
  `"Omen Beat"` from the updated `expected-narrative.md` oracle.
- The unresolved-role assertions are unchanged (they already named the human name).
- The new FR-004 floor test confirms a label-less orphan falls back to its slug.

## Scenario 2 — End-to-end on the `tiny-quest` fixture (manual read)

```bash
uv run pytest tests/e2e/test_narrative_workflow.py -q
```

Then inspect that both `narrative_structure` warnings name the same unit the same
way — e.g. both `'Omen Beat'`, neither `'omen-beat'`. The `source`
(`outline/units/06-omen.md:3`), `warning` severity, and counts (2 warnings, 0
errors, `failed: false`) are unchanged (SC-003).

## Scenario 3 — Full gate sweep

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest
```

**Expected**: all green, coverage ≥ 80 % (SC-004). `load_orphan_units`'s widened
return type (`list[tuple[str, str | None]]`) type-checks under `--strict`.

## Done when

- [ ] Both rules print the human authored name, alone, identically (SC-001/SC-002).
- [ ] Finding count, severity, `relpath:line`, and gate are unchanged on every
      fixture (SC-003).
- [ ] One shared `_unit_identifier` helper, two call sites — no second
      identifier-formatting expression (SC-006).
- [ ] `DEBT.md` no longer contains DEBT-017; no plain-text record describes it as
      open (SC-005).
- [ ] Four CI gates green (SC-004).
