# Data Model: Ingestion-parity guard + deferral registry

No GOLEM/RDF entity is added (the closure is frozen, Principle X). The only new data is
static, in-code, and consumed solely by the parity test.

## DeferralNote

A frozen 2-field record describing *why* a `CONCEPTS` concept is not yet fed and *when*
it is expected to be.

| Field | Type | Rule |
|---|---|---|
| `reason` | `str` | Non-empty. Short prose (one clause) on why the concept has no authored-text builder today. |
| `target_version` | `str` | Non-empty. Exactly one of `v0.3.x`, `v0.4`, or the single canonical literal `undecided` (FR-002). Free-text type, but the concept→version mapping is pinned by a test, so the value is a contract, not a comment. |

Realized as `class DeferralNote(NamedTuple)` (research D4) — immutable, hashable,
`mypy --strict` clean.

## DEFERRED_CONCEPTS (the registry)

`DEFERRED_CONCEPTS: dict[str, DeferralNote]` — concept name → note. **Exactly seven
entries** (FR-002, SC-002), each key a member of `CONCEPTS`:

| Concept (key) | GOLEM | `reason` (intent) | `target_version` |
|---|---|---|---|
| `NarrativeLocation` | G13 | scaffold/skill write `bible/locations/` but nothing ingests it | `v0.3.x` |
| `Object` | G16 | no builder, no `bible/objects/`, no skill | `v0.3.x` |
| `NarrativeUnit` | G9 | narrative structural layer, no ingestion | `v0.4` |
| `NarrativeFunction` | G10 | narrative structural layer, no ingestion | `v0.4` |
| `NarrativeSequence` | G7 | narrative structural layer, no ingestion | `v0.4` |
| `RelationshipRole` | G6 | relationships are identity + participants, no typed roles | `undecided` |
| `PsychologicalState` | G3 | no builder | `undecided` |

Reconcilable with roadmap §3's parity table (FR-012, SC-002): when iteration 025+ wires a
concept, **removing its single entry here** is the one edit that keeps the parity test
green.

## Concept partition (the invariant the test enforces)

For the `CONCEPTS` registry (13 keys), every key is in **exactly one** of two disjoint
sets:

```
reachable  = { name ∈ CONCEPTS : CLASS_IRI[name] ∈ observed_rdf_types(graph) }
orphans    = set(CONCEPTS) − reachable
INVARIANT  : orphans == set(DEFERRED_CONCEPTS)        # SC-001
             reachable ∩ set(DEFERRED_CONCEPTS) == ∅  # disjoint (edge case 1)
```

- **reachable** (derived, never hand-listed — FR-003): the six concepts
  `Character`, `Setting`, `NarrativeEvent`, `SocialRelationship`, `NarrativeRole`,
  `AttributeAssignment`.
- **orphans**: the seven keys above.

Carrier IRIs in `CLASS_IRI` but **not** in `CONCEPTS` (`CharacterFeature`, `Dimension`,
`Type`, `TimeInterval`) are filtered out before the verdict (FR-010): they never enter
`reachable`, `orphans`, or `DEFERRED_CONCEPTS`.

## Exercise fixture corpus (`tests/fixtures/parity-exercise/`)

Minimal plain-text project whose graph build materializes all six reachable concepts:

| File | Concept(s) materialized |
|---|---|
| `bible/characters/<one>.md` with `narrative_roles:` + `born:`/`features:` | `Character`, `NarrativeRole`, (`CharacterFeature` carrier), and `AttributeAssignment` via provenance reification |
| `bible/settings/<one>.md` | `Setting` |
| `bible/timeline.md` (≥1 `events:` item) | `NarrativeEvent` |
| `bible/relationships.md` (≥1 `relationships:` item) | `SocialRelationship` |
| `bible/constitution.md` | (manifest/scaffold completeness; no concept) |

The fixture MUST be valid for `bookwright graph build` (no slug collisions, resolvable
participants) so the build exits clean and the engine holds the full graph (FR-004).

## Failure-message contract (drift reporting)

A pure helper compares the two sets and yields the offending concept name(s):

```
parity_diff(reachable, deferred) -> (fed_but_deferred, undeclared_orphans)
  fed_but_deferred   = reachable ∩ deferred       # FR-006 / FR-007
  undeclared_orphans = orphans  − deferred         # FR-008
```

The parity test asserts both are empty and, on failure, names every concept in the
non-empty set (SC-003).
