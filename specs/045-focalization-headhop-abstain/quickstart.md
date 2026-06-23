# Quickstart: verify the `focalization` head-hopping abstention (iteration 045)

Runnable scenarios proving the iteration end to end. Prerequisites: `uv sync`.

## Scenario A — limited-third project abstains as a capability-gap (US1)

A fixture whose constitution declares *"Tercera persona limitada, centrada en X"*
(e.g. `tiny-novel`, `tiny-quest`, `tiny-historical`).

```bash
uv run pytest tests/validation/test_focalization.py -q
```

Expect: the new unit test passes — a parseable third-limited focal voice raises exactly
one `NotEvaluated` with `kind == NotEvaluatedKind.pending_capability` and the reason
`head-hopping / interiority attribution requires semantic judgment (move 3); the
deterministic heuristic was measured nearly dormant on real prose`. No head-hopping
`warning` is emitted (SC-001). A third-limited voice naming no focal character abstains
identically.

## Scenario B — a clean limited-third project stays GREEN (US2, SC-002)

```bash
uv run pytest tests/e2e/test_tri_valued_validation.py -q
```

Expect: `tiny-novel` (third-limited) reads **green** under the refined predicate
(`status == "ok"` AND no `not_evaluated` entry is `missing_input`) even though
`not_evaluated[]` now carries **both** `character_unknown_mentions` and `focalization`
as `pending_capability`; `tiny-memoir` (first-person) carries only
`character_unknown_mentions`. `bookwright status` adds **no** `next_action` for the
`focalization` gap.

## Scenario C — the four input-conditional abstentions are unchanged (US3, SC-003)

```bash
uv run pytest tests/validation/test_focalization.py -k "not_evaluated or pending or person or constitution" -q
```

Expect: causes (i)–(iv) still raise `NotEvaluated` with `kind == missing_input` and
byte-identical reason strings; a project with such a gap is **not** green and `status`
still nudges the author to declare/answer the voice.

## Scenario D — first-person fixtures gain no entry (SC-005)

```bash
uv run pytest tests/e2e/test_narrative_workflow.py tests/e2e/test_orchestration_workflow.py -q
```

Expect: `tiny-memoir` / `tiny-essay` produce no `focalization` `not_evaluated` entry
(evaluated-with-no-findings); `tiny-historical`'s pinned oracle now lists the additive
`focalization` `pending_capability` entry with `counts == {error:1, warning:1, info:0}`
and `next_actions` length 3 (SC-004), all unchanged otherwise.

## Scenario E — DEBT ledger + full gates (SC-006/SC-007/SC-008)

```bash
grep -c "DEBT-014" DEBT.md          # → 0  (removed, FR-011/SC-006)
grep -c "DEBT-019" DEBT.md          # → ≥1 (the dropped first-person-break check, FR-015/SC-008)
uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest
```

Expect: DEBT-014 gone, DEBT-019 present, and all four gates green (≥80% coverage).
