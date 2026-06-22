# Quickstart: Tri-valued validator result

Runnable validation scenarios that prove the feature end-to-end. See
[data-model.md](./data-model.md) and [contracts/](./contracts/) for shapes.

## Prerequisites

```bash
uv sync
```

Iteration 039 (the prose seam: `io/prose.py` with `is_placeholder`, the cached
`manuscript_view()` / `constitution_view()` accessors) is on `main` — this iteration
reuses its placeholder detection.

## Scenario 1 — a dormant validator no longer reads as green (US1, SC-001/SC-002)

Fixture: a project whose constitution does **not** declare a narrative voice (or
carries the `- **Voz narrativa**: [PENDING: …]` placeholder a fresh `bookwright init`
emits) and a manuscript with prose.

```bash
cd <fixture-with-undeclared-voice>
uv run bookwright graph build
uv run bookwright validate --json | tee /tmp/v.json
```

**Expected** (`/tmp/v.json`):

- `not_evaluated[]` contains `{"validator": "focalization", "reason": "…"}` with a
  legible reason.
- The green predicate `status == "ok" AND not_evaluated == []` evaluates to **False**
  (the run is **not** clean), even though `violations` may be empty.
- `errors[]` does **not** contain `focalization` (it did not crash — FR-005).

Variants (FR-008, distinct reasons):
- no constitution file → reason names the missing/absent voice declaration;
- `[PENDING: …]` voice → reason names the unanswered placeholder;
- `- **Voz narrativa**: narrador omnisciente` (no first/third person) → reason names
  the unresolved grammatical person;
- `- **Voz narrativa**: tercera persona limitada` + clean manuscript →
  `focalization` is **evaluated** with zero findings (NOT in `not_evaluated`) — a
  legitimate green (FR-003).

## Scenario 2 — nothing to inspect, without hiding a finding (US2)

```bash
# (a) populated bible (characters + settings), EMPTY manuscript dir
uv run bookwright validate --json
#   → setting_continuity in not_evaluated[] ("the manuscript is empty")
#   → character_presence EVALUATED: still emits its error-level orphan findings,
#     byte-for-byte unchanged (NOT in not_evaluated) — gate behavior preserved.

# (b) empty project: no roster, no prose
uv run bookwright validate --json
#   → character_presence in not_evaluated[] (no-inputs reason)

# (c) manuscript prose present
uv run bookwright validate --json
#   → both validators evaluate; any existing findings produced byte-for-byte
#     unchanged from today (FR-012).
```

## Scenario 3 — the third state is visible where green is read (US3, SC-004)

```bash
cd <fixture-with-undeclared-voice>
uv run bookwright status --json | tee /tmp/s.json
```

**Expected** (`/tmp/s.json`):

- `state.validation.not_evaluated[]` lists `focalization` with its reason.
- `next_actions[]` contains a step naming the concrete remedy: *declare the narrative
  voice in the constitution to activate `focalization`* (SC-004).
- On a project where every active validator evaluated: no `not_evaluated` entries and
  no activation action (no false positives, US3 scenario 2).

## Gate / CI behavior (Edge Case "the gate")

```bash
# A run consisting solely of not-evaluated validators (no error findings):
uv run bookwright validate ; echo "exit=$?"
#   → exit=0 (not-evaluated is not a finding) ...
#   → ... but the report is NOT "no violations found" — it shows the
#     "not evaluated:" section instead.
```

## Quality gates

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest                     # full suite, ≥ 80 % coverage; ZERO finding-oracle edits (SC-003)
```

**Parity check (SC-003 / FR-012):** the entire pre-existing suite passes with **no**
edits to `Violation` finding counts; only new not-evaluated assertions are added.
Every migrated trigger fires only on inputs that already produced `[]`.
