# Quickstart — validating `not_evaluated` kinds

Runnable scenarios that prove the feature end to end. Prerequisites:
`uv sync`; run from the repo root.

## Scenario A — a clean project reads green again (SC-001, US1)

A flawless fixture (`tiny-novel` / `tiny-memoir`) carries only the permanent
`character_unknown_mentions` capability-gap entry.

```bash
# (copy the fixture to a temp dir or run in place per the e2e harness)
bookwright graph build --json
bookwright validate --json | python -m json.tool
```

Expected:

- `status == "ok"`, `failed == false`, `by_severity` all zero.
- `not_evaluated` has exactly one entry:
  `{ "validator": "character_unknown_mentions", "kind": "pending_capability", "reason": "…move 3…" }`.
- **Refined green predicate is `True`**: `status == "ok"` and no entry has
  `kind == "missing_input"`.

```bash
bookwright status --json | python -c "import sys,json; s=json.load(sys.stdin); \
  print('actions', [a['skill'] for a in s['next_actions']])"
```

Expected (SC-002): **no** `bookwright-continuity` "activate the dormant
validators" action — the only `not_evaluated` entry is `pending_capability`.

## Scenario B — an input gap is still not green and still nudges (SC-004, US2)

`tiny-undeclared-voice` ships a constitution with the `[PENDING]` narrative-voice
placeholder, so `focalization` raises `missing_input`.

```bash
bookwright graph build --json
bookwright validate --json | python -c "import sys,json; p=json.load(sys.stdin); \
  print('kinds', {r['validator']: r['kind'] for r in p['not_evaluated']})"
```

Expected:

- `focalization` appears with `kind == "missing_input"`.
- The refined green predicate is **`False`** (a `missing_input` entry denies green).
- `bookwright status` still recommends `bookwright-continuity` to declare the
  narrative voice (the nudge names `focalization`, not `character_unknown_mentions`).

## Scenario C — both kinds at once (edge case)

A project missing the voice declaration **and** carrying the capability-gap:

- The run is **not** green (the `missing_input` entry denies it).
- The dormant-validator nudge names **only** `focalization`.
- Both entries are listed in `--json`, `status`, and the human report, each with
  its `kind`.

## Scenario D — the gate is unaffected (SC-005)

```bash
bookwright validate --json; echo "exit=$?"
```

For every fixture the exit code is identical to before this change: only an
`error` `Violation` makes it non-zero. Neither `not_evaluated` kind changes the
exit code.

## Scenario E — the human report stays honest (FR-010)

```bash
bookwright validate            # no --json: the human report
```

A capability-gap-only project prints the `not evaluated:` section (labeled
`[known limitation — no action available yet]`), **not** "no violations found".

## Oracle — `tiny-historical` (SC-006)

`tests/e2e/test_orchestration_workflow.py` asserts against
`tests/fixtures/tiny-historical/expected-status.md`:

- the single `not_evaluated` entry (`character_unknown_mentions`) now carries
  `kind: pending_capability`;
- `next_actions` length is **3** (down from 4 — the universal dormant nudge is
  gone);
- `validation.counts` is byte-identical (`error: 1, warning: 1, info: 0`),
  `error` stays 1;
- the fixture manuscript/bible is unchanged.

## Gates

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest          # ≥ 80 % coverage enforced
```

All four must pass (SC-008).
