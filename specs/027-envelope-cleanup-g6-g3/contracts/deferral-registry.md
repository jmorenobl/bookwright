# Contract: deferral registry — zero "undecided" (US2, FR-008…FR-014)

`golem/deferrals.py` (`DEFERRED_CONCEPTS: dict[str, DeferralNote]`) is consumed
solely by `tests/golem/test_ingestion_parity.py`. The concept→version mapping is a
pinned contract.

## After this iteration

| Concept | reason | target_version |
|---|---|---|
| `NarrativeUnit` (G9) | narrative structural layer, no ingestion (G9) | `v0.4` |
| `NarrativeFunction` (G10) | narrative structural layer, no ingestion (G10) | `v0.4` |
| `NarrativeSequence` (G7) | narrative structural layer, no ingestion (G7) | `v0.4` |
| `RelationshipRole` (G6) | requires a typed roles/states model with attributes and an authoring surface | `v0.4` |
| `PsychologicalState` (G3) | requires a typed roles/states model with attributes and an authoring surface | `v0.4` |

## Invariants (asserted by `test_registry_well_formed`)

- Exactly 5 entries; keys ⊆ `CONCEPTS`; keys == `ORPHAN_NAMES`.
- Every `reason` non-empty; every `target_version` non-empty.
- **No entry has `target_version == "undecided"`** (new assertion — FR-011/SC-003).
- `{name: note.target_version} == EXPECTED_VERSIONS` (all five → `"v0.4"`).
- `CARRIER_NAMES` disjoint from the registry.

## Parity invariants (unchanged sets — `test_reachable_set_pin`, `test_ingestion_parity_holds`)

- `EXPECTED_REACHABLE` — the same 8 fed concepts.
- `ORPHAN_NAMES` — the same 5 orphans (G6/G3 stay orphans; **not** wired).
- The real orphan set derived from a live build equals `DEFERRED_CONCEPTS` keys.

## Frozen-ontology guard (FR-013, Principle X)

No class/property added to `golem.ttl` or `CLASS_IRI`. G6/G3 already exist in
`CLASS_IRI` + `CONCEPTS`; they remain modelled-but-unfed.
