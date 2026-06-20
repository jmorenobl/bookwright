# Quickstart: Narrative-structure continuity validator

Runnable scenarios that prove the validator works end to end. See
[contracts/narrative-structure-validator.md](./contracts/narrative-structure-validator.md)
for the behavioural contract and [data-model.md](./data-model.md) for shapes.

## Prerequisites

```bash
uv sync
```

A project with the v0.4 narrative layer: characters (with `narrative_roles:` roles)
in `bible/characters/`, and beats in `outline/units/*.md`. The graph must be built so
the validator's SPARQL sees `G7`/`G9`:

```bash
uv run bookwright graph build      # writes bible/graph.ttl (includes the outline pass)
```

## Scenario 1 — orphan beat is flagged (US1)

Two unit cards; only one joins a sequence:

```text
outline/units/the-storm.md     # sequence: "Main line", order: 10
outline/units/the-flood.md     # no sequence: → orphan
```

```bash
uv run bookwright validate --json | jq '.violations[] | select(.validator=="narrative_structure")'
```

**Expected**: exactly one `narrative_structure` finding, `severity":"warning"`,
naming `the-flood`, `source` pointing at `outline/units/the-flood.md:<line>`. The
sequenced `the-storm` is **not** reported. `failed` stays `false`.

## Scenario 2 — every beat sequenced → no finding (US1 clean)

Give every unit card a `sequence:`. `validate --json` shows **no**
`narrative_structure` orphan finding.

## Scenario 3 — unresolved role is flagged (US2)

A unit card lists a role no character plays:

```yaml
---
name: "The reckoning"
roles: ["villain-that-does-not-exist"]
sequence: "Main line"
---
```

```bash
uv run bookwright validate --json | jq '.violations[] | select(.validator=="narrative_structure")'
```

**Expected**: one finding naming the beat `The reckoning` and the unresolved role
`villain-that-does-not-exist`, `source` at the card's `file:line`. A card whose
`roles:` all resolve produces no such finding.

## Scenario 4 — no `outline/units/` → inert (FR-009)

A project with no `outline/units/` directory:

```bash
uv run bookwright validate --json | jq '.violations[] | select(.validator=="narrative_structure")'
```

**Expected**: empty — zero `narrative_structure` findings; the report is otherwise
identical to before the feature.

## Scenario 5 — order gap is NOT a finding (FR-007)

A sequence whose members use sparse `order:` (10, 30 — a gap) or a duplicate:

**Expected**: **no** order-related `narrative_structure` finding. The gap is
legitimate sparse numbering, not an incoherence.

## Scenario 6 — disable by name (US3 / FR-010)

```toml
[validators]
disabled = ["narrative_structure"]
```

```bash
uv run bookwright validate --json | jq '.summary.ran | index("narrative_structure")'
```

**Expected**: `null` (not in `ran`); no `narrative_structure` findings; every other
validator unchanged.

## Automated equivalents

- `tests/validation/test_narrative_structure.py` — orphan fires, clean does not,
  unresolved role fires, good roles do not, no-`outline/units/` is inert, order-gap
  yields no finding, disable-by-name removes the findings.
- `tests/validation/test_command.py` — a `--json` envelope assertion: the finding
  appears in `violations[]` with the existing shape and no new top-level key.

Run:

```bash
uv run pytest tests/validation/test_narrative_structure.py
uv run pytest      # full suite + coverage gate
```
