# Quickstart: narrative-sequence ingestion (G7)

Runnable validation that the `outline/units/` pass assembles `NarrativeSequence`
(G7) entities from `sequence`/`order` keys. See [contracts/sequence-ingestion.md]
for the full contract and [data-model.md](./data-model.md) for the assembly rule.

## Prerequisites

```bash
uv sync
```

## Scenario A — three ordered beats become one ordered sequence (US1, SC-001/002/003)

1. In a project, create three `outline/units/*.md` cards:
   - `a.md`: `name: "Beat A"`, `sequence: "Act I"`, `order: 1`
   - `b.md`: `name: "Beat B"`, `sequence: "Act I"`, `order: 2`
   - `c.md`: `name: "Beat C"`, `sequence: "Act I"`, `order: 3`
2. Build: `uv run bookwright graph build`
3. **Expected**: exactly one `NarrativeSequence` for `Act I` with three
   `dlp:proper-part` edges; the builder's member tuple is `(Beat A, Beat B, Beat
   C)` — assert the proper-part member order in the built entity, not triple
   order.

## Scenario B — unsequenced unit is untouched (US2, FR-004/SC-006)

1. Add `d.md`: `name: "Beat D"` (no `sequence`).
2. Rebuild. **Expected**: `Beat D` belongs to no sequence; no `NarrativeSequence`
   minted on its account; its iter-028 triples are unchanged. A project where
   **no** card declares `sequence` builds byte-for-byte the pre-feature graph.

## Scenario C — duplicate `order` tie-breaks by slug (FR-006)

1. Two `Act I` cards both with `order: 1`, names `"Zeta Beat"` and `"Alpha
   Beat"`.
2. **Expected**: members ordered `(Alpha Beat, Zeta Beat)` (slug tie-break);
   identical across two builds.

## Scenario D — single-member sequence (US1 acceptance #2/#3)

1. One card with `sequence: "Coda"`, `order: 1`.
2. **Expected**: one `NarrativeSequence` for `Coda` with exactly one
   `dlp:proper-part` edge.

## Scenario E — no sequences at all

1. Units present, none with `sequence`.
2. **Expected**: zero `NarrativeSequence` entities; graph identical to iter 028.

## Automated coverage

```bash
# the five sequence-assembly scenarios (ordered trio, dup order, no-sequence
# unit, single-member sequence, absence of sequences)
uv run pytest tests/io/test_outline_sequences.py

# parity flips: G7 fed, orphan set = {RelationshipRole, PsychologicalState}
uv run pytest tests/golem/test_ingestion_parity.py

# the edited source command still materializes & lints
uv run pytest tests/integrations/test_materialize.py

# full gates
uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest
```

## Skill surface (US3, SC-008)

Materialize integrations into a scratch project and confirm the regenerated
`bookwright-outline` `SKILL.md` (both `claude` and `generic`) documents the
optional `sequence`/`order` unit keys in both enumerations and still triggers on
Spanish and English author prompts (passes the existing skill lint gate).
