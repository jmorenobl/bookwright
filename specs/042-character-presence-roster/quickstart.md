# Quickstart / Validation Guide: iteration 042

Proves DEBT-010 is closed: declared settings/locations/objects stop being mis-flagged as
unknown proper nouns, while genuinely off-bible names still fire and the `error` gate is
untouched. See [contracts](./contracts/validation-context-accessors.md) and
[data-model](./data-model.md) for the seams.

## Prerequisites

```bash
uv sync
```

## Scenario 1 — declared setting tokens stop firing (US1.1, the defect)

The `tiny-historical` fixture declares the setting "la Real Fábrica de Paños" under
`bible/settings/` and names it in the manuscript. Today its tokens `Real`/`Fábrica`/`Paños`
each fire one unknown-mention `warning`; after the fix they do not.

```bash
uv run pytest tests/e2e/test_orchestration_workflow.py
```

**Expected**: green. The E2E reads `tests/fixtures/tiny-historical/expected-status.md`,
whose `validation.counts.warning` is now **1** (was 4): the three setting-token warnings are
gone, the single `factual_anchor` warning remains; `validation.counts.error` stays **1**.

## Scenario 2 — location & object arms (US1.2 / US1.3, synthetic projects)

```bash
uv run pytest tests/validation/test_character_presence.py
```

**Expected**: green. Synthetic projects built with `write_project(..., locations=[...],
objects=[...])` confirm a declared location name and a declared object name (full phrase or
any ≥3-letter token) produce **no** unknown-mention warning.

## Scenario 3 — a genuinely off-bible name still fires (US2)

Covered by the same test module: a manuscript proper noun absent from all four rosters
still yields exactly **one** `warning` citing its first occurrence (SC-004).

## Scenario 4 — the orphan `error` gate is untouched (US3)

```bash
uv run pytest tests/validation/test_character_presence.py tests/e2e
```

**Expected**: the set of `error`-level findings is byte-for-byte identical to before; a
declared-but-unmentioned setting/location/object produces **no** finding of any severity
(FR-004, SC-003).

## Scenario 5 — `not-evaluated` unchanged (US4)

A project with no manuscript prose and an empty character roster (settings present) still
raises the identical not-evaluated reason from iteration 040 (SC-005).

## Full gate run

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest
```

**Expected**: all four gates green, ≥80% coverage; `git diff` over
`resources/schemas/golem-1.1/` and `golem.ttl` empty; no fixture manuscript/bible edited;
`DEBT.md` no longer contains a DEBT-010 entry (SC-006/SC-007).
