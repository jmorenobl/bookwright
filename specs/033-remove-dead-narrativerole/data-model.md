# Phase 1 — Data Model: concepts, IRIs, carriers, deferrals

This iteration adds no entities and changes no schema. It **shrinks one registry
by one entry** and **reclassifies one IRI** from the concept bucket to the
carrier bucket. The "data model" here is the set of registries whose contents
the change must leave in a precise, mutually consistent state.

## Registry 1 — `CONCEPTS` (`golem/__init__.py`)

Concept name → Python class. **Before**: 13 entries. **After**: 12 entries
(`"NarrativeRole"` removed).

| # | Concept | Class IRI key | Materializing builder | Status after change |
|---|---|---|---|---|
| 1 | Character | Character | `map_bible` characters | reachable |
| 2 | Object | Object | bible objects | reachable |
| 3 | SocialRelationship | SocialRelationship | `relationships.md` | reachable |
| 4 | RelationshipRole | RelationshipRole | — (G6) | **deferred** |
| 5 | NarrativeEvent | NarrativeEvent | `timeline.md` | reachable |
| 6 | PsychologicalState | PsychologicalState | — (G3) | **deferred** |
| 7 | Setting | Setting | bible settings | reachable |
| 8 | NarrativeLocation | NarrativeLocation | bible locations | reachable |
| 9 | NarrativeUnit | NarrativeUnit | `outline/units/*.md` (028) | reachable |
| 10 | NarrativeFunction | NarrativeFunction | `outline/units/*.md` (028) | reachable |
| 11 | NarrativeSequence | NarrativeSequence | `outline/units/*.md` (029) | reachable |
| 12 | AttributeAssignment | AttributeAssignment | indexer reification | reachable |
| ~~—~~ | ~~NarrativeRole~~ | ~~NarrativeRole~~ | ~~none — dead~~ | **REMOVED** |

Reachable concepts: **10** (was 11). Deferred concepts: **2** (unchanged).
`AttributeAssignment` is reachable but not slugged ⇒ **11 slugged** concepts
(was 12).

**Invariant** (must hold after change): `set(DEFERRED_CONCEPTS) ⊆ set(CONCEPTS)`,
`len(CONCEPTS) == 12`, `"NarrativeRole" ∉ CONCEPTS`.

## Registry 2 — `CLASS_IRI` (`golem/namespaces.py`) — FROZEN, UNCHANGED

Class IRI key → `URIRef`. **17 entries, before and after.** This iteration does
**not** touch it. Its keys partition into:

- **Concept IRIs** — the 12 keys above that are also `CONCEPTS` members.
- **Carrier-only IRIs** — 5 keys present in `CLASS_IRI` but **not** in `CONCEPTS`:
  `CharacterFeature`, `Dimension`, `Type`, `TimeInterval`, **and now
  `NarrativeRole`** (materialized solely by the `CharacterRole` carrier).

`12 + 5 = 17`. Before the change the split was `13 + 4` (G11's IRI counted as a
concept IRI); the change **moves** G11's IRI across the line, preserving the 17.

## Registry 3 — `DEFERRED_CONCEPTS` (`golem/deferrals.py`) — UNCHANGED

| Concept | `target_version` |
|---|---|
| RelationshipRole | `demand-pulled` (G6) |
| PsychologicalState | `demand-pulled` (G3) |

Exactly two entries; both keys are `CONCEPTS` members; both targets
`demand-pulled`. **FR-010: not edited by this change.**

## Registry 4 — parity-test contracts (`tests/golem/test_ingestion_parity.py`)

| Constant | Before | After |
|---|---|---|
| `EXPECTED_REACHABLE` | 11 names (incl. `NarrativeRole`) | **10 names** (drop `NarrativeRole`) |
| `ORPHAN_NAMES` | `{PsychologicalState, RelationshipRole}` | unchanged |
| `EXPECTED_VERSIONS` | `{…: demand-pulled ×2}` | unchanged |
| `CARRIER_NAMES` | `{CharacterFeature, Dimension, Type, TimeInterval}` | **+ `NarrativeRole`** (5) |

## The carrier — `CharacterRole` (`golem/modules/feature.py`) — UNCHANGED behaviour

```
CharacterRole.golem_class == CLASS_IRI["NarrativeRole"]   # PRESERVED
URI:    {character.uri}/role/{slug(label)}
emits:  (uri, rdf:type, golem:G11_Narrative_Role)
        (uri, rdfs:label, <role text>)
        (uri, crm:P2_has_type, <actant E55_Type>)   # only when type_uri set (030)
```

Only its **docstring** changes (drop the "Distinct from the top-level
`NarrativeRole` concept" phrasing; describe it as the sole materialization of
G11). Its triple output is byte-for-byte identical ⇒ zero G11 regression.

## State transitions

None. No entity has lifecycle/state. The only "transition" is the registry edit
above, applied once.

## Validation rules enforced by tests (post-change)

1. `len(CONCEPTS) == 12` and `"NarrativeRole" ∉ CONCEPTS` (FR-002, SC-001).
2. `len(CLASS_IRI) == 17`, partitioned `12 concept + 5 carrier` (FR-004, SC-003).
3. Carrier-IRI disjointness: `{CLASS_IRI[c] for c in CONCEPTS}` ∩
   `{CLASS_IRI[k] for k in CARRIER_NAMES}` `== ∅` (FR-006 — the DEBT-001 guard).
4. Real-build orphan set `== set(DEFERRED_CONCEPTS)` (FR-007).
5. G11 still materialized in the real build via `CharacterRole` (FR-005, SC-002).
