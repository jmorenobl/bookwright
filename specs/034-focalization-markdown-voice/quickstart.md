# Quickstart / Validation Guide: `focalization` markdown-prefixed voice declaration

Runnable scenarios that prove the iteration. See [contracts/declaration-recognition.md](./contracts/declaration-recognition.md)
for the full surface-form table and [data-model.md](./data-model.md) for the
(unchanged) parse model.

## Prerequisites

```bash
uv sync   # deps + dev group into .venv
```

## Scenario A — the scaffold's own voice line now wakes the validator (P1, SC-001)

The defect: today the parser ignores `- **Voz narrativa**: …`. After the fix it
parses it identically to the bare form and the third-person rules fire.

```bash
uv run pytest tests/validation/test_focalization.py -q
```

Expected: the new marker-by-marker tests (one per `-`,`*`,`+`,`>` bullet and per
`*`/`**`/`_` emphasis run, Acceptance Scenario 4) and the scaffold-shape test
(`- **Voz narrativa**: Tercera persona limitada, centrada en Elena Vidal` →
`person=third, limited=true, focal="Elena Vidal"`, FR-004) all pass; the
pre-existing tests still pass unchanged (FR-006).

## Scenario B — template ↔ parser are bound (P1, SC-004, FR-007)

```bash
uv run pytest tests/validation/test_focalization.py -k template_binding -q
```

Expected: the test reads the live
`src/bookwright/resources/project/bible/constitution.md.j2` voice line and
asserts the parser returns a non-`None` declaration. Sanity-check the guard
locally by temporarily mangling the template's voice line (e.g. delete the
colon) and re-running — the test MUST fail — then revert.

## Scenario C — no-declaration edge case preserved (P2, SC-003, FR-005)

The existing `test_no_parsable_declaration_yields_nothing` still passes, and a
markdown-prefixed line declaring no person (the scaffold's `[PENDING: …]`) yields
zero findings.

```bash
uv run pytest tests/validation/test_focalization.py -k "no_parsable or pending" -q
```

## Scenario D — whole-suite fixture reconciliation (FR-008, SC-005)

Waking the validator changes `tiny-historical`'s project-wide warning tally.
Read the **real** awake count and reconcile the oracle (do not back-fit to the
old `{error:1, warning:6}`):

```bash
# Build + inspect tiny-historical's awake focalization output to get the new count,
# then update tests/fixtures/tiny-historical/expected-status.md accordingly.
uv run pytest tests/e2e/test_orchestration_workflow.py -q   # green after reconciliation
uv run pytest tests/e2e/test_narrative_workflow.py tests/e2e/test_research_workflow.py -q  # unaffected
```

Expected after reconciliation: `tiny-historical` `validation.counts` reflects the
awake `warning` total (`error` stays 1); `tiny-novel` still `validate`s clean
(exit 0); `tiny-quest`/`tiny-essay`/`tiny-memoir` oracles unchanged.

## Scenario E — DEBT-004 removed (SC-006, FR-009)

```bash
grep -c "DEBT-004" DEBT.md   # MUST print 0
```

## Final gates (SC-005)

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest        # full suite, ≥80% coverage
```

All four MUST pass.
