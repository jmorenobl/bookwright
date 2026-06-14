# Quickstart / Validation: envelope cleanup + G6/G3 decision

Run from repo root after implementing the iteration. All four CI gates plus three
targeted checks must pass.

## Prerequisites

```bash
uv sync
```

## 1. CI gates (the merge bar)

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest          # ≥ 80 % coverage enforced; > 85 % on new code (SC-005)
```

## 2. US1 — success envelopes byte-identical (FR-005, SC-001/002)

```bash
uv run pytest tests/commands/test_success_envelopes.py -v
```

Expected: pins for `check`, `focus show/set/clear`, `graph query`, `graph build`
all pass — stdout bytes equal their baselines; exit codes unchanged.

```bash
# Zero hand-built {"status":"ok"} literals remain in focus/graph command modules:
grep -rn '"status": *"ok"\|"status":"ok"' src/bookwright/commands/focus \
        src/bookwright/commands/graph/query.py
```

Expected: no matches (the literals now live only in `_envelope.ok_payload` and the
`graph build` report serializer). Docstring mentions of the shape are fine.

## 3. US2 — deferral registry, zero "undecided" (FR-011, SC-003/004)

```bash
uv run pytest tests/golem/test_ingestion_parity.py -v
grep -rn '"undecided"\|undecided' src/bookwright/golem/deferrals.py
```

Expected: parity suite green (reachable 8 / orphan 5 unchanged, versions all
`v0.4`); the `test_registry_well_formed` "no undecided" assertion passes; grep
returns nothing (the literal is gone from data **and** the docstring contract).

## 4. US3 — unresolved-reference rename (FR-019, SC-007)

```bash
uv run pytest tests/commands/graph/test_build.py -v
grep -rn "UnresolvedParticipant\|unresolved_participants" src/ docs/
```

Expected: build tests green with the `unresolved_references` key at its position;
grep returns **nothing** across `src/` and `docs/`.

Manual JSON spot-check (optional) against any project with an unresolved
`setting:` or `participants:`:

```bash
uv run bookwright graph build --json | python -m json.tool | grep unresolved
```

Expected: `"unresolved_references": [...]` — never `unresolved_participants`.
Stderr (human mode) reads `N unresolved reference(s)`.

## 5. Closing check (SC-006)

The v0.3.x track closes: no `"undecided"` verdict, no hand-rolled success-envelope
literal in `focus`/`graph query`, and no `UnresolvedParticipant` misnomer remain.
Release as `v0.3.4` via the `bookwright-release` skill (CHANGELOG records the key
rename).
