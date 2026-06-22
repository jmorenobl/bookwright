# Quickstart — validate the leading dialogue-dash fix

Runnable scenarios that prove iteration 041 end to end. All commands run from the repo
root with `uv`.

## Prerequisites

```bash
uv sync
```

## 1. Seam contract — the dash is stripped (and only the leading one)

```bash
uv run python -c "from bookwright.io.prose import prose_view as p; \
print(p('—Esto es el porvenir')[0].normalized); \
print(p('—dijo Arnela—, y se fue')[0].normalized); \
print(repr(p('—')[0].normalized)); \
print(p('> —Esto')[0].normalized)"
```

Expected:

```text
Esto es el porvenir
dijo Arnela—, y se fue
''
Esto
```

(em/en dash glued or spaced → leading dash removed; internal incise dash kept;
dash-only → empty; composes with a blockquote.)

## 2. `character_presence` — both directions (FR-009)

Run the targeted tests (no validator file is edited; the behavior comes from the seam):

```bash
uv run pytest tests/io/test_prose.py tests/validation/test_character_presence.py -q
```

Expected: green — the leading-dash demonstrative (`—Esto`) produces **no** finding,
while a mid-line off-roster name (`—Pregúntale a Quirón —dijo.`) is still flagged once.

## 3. Empirical parity on the live fixture (SC-003)

```bash
uv run pytest tests/e2e/test_orchestration_workflow.py tests/fixtures/test_fixtures.py -q
```

Expected: green. The `tiny-historical` orchestration oracle now pins
`validation.counts == {error: 1, warning: 4, info: 0}` (was `warning: 5`): the spurious
`—Esto` flag is gone; `tiny-novel`/`tiny-memoir` keep `error == 0` with no pinned
warning count. The fixture manuscripts are untouched.

## 4. The whole suite + the four gates (SC-005)

```bash
uv run pytest
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

Expected: all green, coverage ≥ 80 %.

## 5. Debt trail (SC-006)

```bash
grep -c "DEBT-009" DEBT.md   # → 0  (entry removed; git keeps history)
grep -c "DEBT-011" DEBT.md   # → ≥1 (recorded by the spec audit, deferred)
```
