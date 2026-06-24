# Quickstart: validating the partial-evaluation contract (iteration 050)

Run guide proving the feature end to end. References [the contract](./contracts/validator-protocol.md)
and [data-model.md](./data-model.md); does not duplicate code.

## Prerequisites

```bash
uv sync
```

## Scenario 1 — the runner normalizes form (c) (general contract, SC-008/FR-015)

A synthetic validator (decoupled from `focalization`) returns
`EvalResult([Violation(...)], [Abstention("…", pending_capability)])`.

```bash
uv run pytest tests/validation/test_runner.py -q
```

**Expected**: the new form-(c) test passes — the synthetic validator's finding
lands in `violations[]` (deduped + sorted), its abstention lands in
`not_evaluated[]` with the **runner-stamped** validator name and its `kind`, and
the validator appears in **neither** `errors[]` nor (for its finding) the
abstention channel. The existing isolation/dedup/sort/`NotEvaluated`/kind tests
still pass unchanged.

## Scenario 2 — `focalization` runs the break check AND abstains (SC-001/FR-013)

A third-person-**limited** voice + a first-person marker outside dialogue.

```bash
uv run pytest tests/validation/test_focalization.py -q
```

**Expected**: the new both-at-once test passes — the returned `EvalResult` carries
**exactly one** `focalization` `warning` citing the marker (with a `relpath:line`
locator) **and exactly one** `not_evaluated`/`pending_capability` head-hop entry,
in the same run. The retargeted limited-third tests assert the `EvalResult` shape
(empty `violations`, the head-hop abstention) instead of `pytest.raises(
NotEvaluated)`. The four `missing_input` total-abstention tests still raise.

## Scenario 3 — the three focalized fixtures stay byte-identical (SC-003/FR-012)

```bash
uv run pytest tests/ -q -k "validate or fixture or e2e or quest or novel or historical"
```

**Expected**: `tiny-historical` / `tiny-novel` / `tiny-quest` emit `violations`,
`errors`, `not_evaluated`, and `ran` byte-identical to the current release — their
pinned oracles are unchanged. (They are limited-third with no first-person break,
so form (c) emits exactly today's single head-hop entry.)

## Scenario 4 — green predicate + gate unchanged (SC-005/FR-005)

- A clean focalized project stays **green**: `status == "ok"` and no
  `not_evaluated` entry has `kind == "missing_input"` (the `pending_capability`
  head-hop entry does not deny green).
- A focalized project **with** a first-person break is `status = violations`
  (a real `warning`) but the error-only CI gate is **unaffected** (no `error`).

```bash
uv run bookwright validate --json   # in a focalized fixture project
```

**Expected**: the `--json` envelope is unchanged in shape; the `pending_capability`
entry is visible in `not_evaluated[]` and never gates.

## Scenario 5 — all four gates green (SC-007)

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest        # ≥ 80% coverage enforced by [tool.coverage.report]
```

**Expected**: all four gates pass. `mypy --strict` is clean across the widened
`validate` return type (`list[Violation] | EvalResult`), and a bare-list validator
still type-checks against the `Validator` Protocol (SC-004).

## Scenario 6 — DEBT-019 removed (SC-006/FR-011)

```bash
grep -c "DEBT-019" DEBT.md   # expected: 0
```

**Expected**: no DEBT-019 entry remains; the track-A closed-list line is
reconciled to reflect its closure.
