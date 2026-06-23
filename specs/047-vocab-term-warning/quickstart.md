# Quickstart — Soft warning for unrecognized Propp/Greimas terms

Validates the three user stories end to end. Run from the repo root. The reference
fixture is `tests/fixtures/tiny-quest` (Propp active) plus a Greimas-active bible
character; the automated oracles (Phase 2 `tasks.md`) reuse `copy_fixture` and build
the project graph in a tmp dir.

## Prerequisites

```bash
uv sync
```

## Scenario 1 — Propp typo is surfaced (US1)

A unit card under an active `propp` vocabulary lists a `functions:` term matching no
Propp function (e.g. `intimidacion`) alongside a valid one (`struggle`).

```bash
# In a project copied from tiny-quest, edit one unit so functions: [struggle, intimidacion]
uv run bookwright graph build --json | jq '.untyped_vocab_terms, .status'
```

**Expected**:
- `status: "ok"`, exit code `0` (unchanged).
- exactly one `untyped_vocab_terms` entry:
  `{path: "outline/units/…", field: "functions", term: "intimidacion", vocabulary: "propp"}`
  — and **none** for `struggle`.
- the graph has `narrative-function/intimidacion` **without** `crm:P2_has_type`, and
  `narrative-function/struggle` **with** it (graph unchanged vs. pre-feature).
- stderr shows `valid propp terms: …` enumerating the 31 functions (sorted).

## Scenario 2 — Greimas role is surfaced the same way (US2)

A character with `greimas` active lists a `narrative_roles:` label matching no
Greimas actant alongside a valid actant.

```bash
uv run bookwright graph build --json | jq '.untyped_vocab_terms'
```

**Expected**: one entry `{field: "narrative_roles", vocabulary: "greimas", term: …}`
for the unrecognized label only; the role node is minted **without** `crm:P2_has_type`.

## Scenario 3 — No active vocabulary, nothing changes (US3)

```bash
# A project with [vocabularies] active = [] (or absent)
uv run bookwright graph build --json | jq '.untyped_vocab_terms'   # => []
```

**Expected**: empty `untyped_vocab_terms`; the envelope and the graph are
byte-identical to pre-feature output (no warning, no typing).

## Scenario 4 — Determinism (US1 AC-3 / SC-008)

```bash
uv run bookwright graph build --json > a.json
uv run bookwright graph build --json > b.json
diff a.json b.json    # => no output
```

**Expected**: byte-identical envelopes — entry order and (in the human report) the
enumerated valid terms are stable across runs.

## Gates

```bash
uv run pytest
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

All four green; coverage ≥ 80 %. The new oracles assert: the two typing sites warn
(Propp + Greimas), valid terms do not, the graph is unchanged, exit code is
invariant, the no-vocab build is byte-stable, and two builds are byte-identical.
