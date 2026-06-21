# Phase 1 — Data Model: G9 `rdfs:label` + queryable sequence order

No new ontology class. No new entity type. Three existing GOLEM concepts gain emitted
triples; one new `bw:` predicate is declared. The authoring format is unchanged (FR-010).

## Entities (deltas only)

### `NarrativeUnit` (`golem:G9_Narrative_Unit`)
- **Unchanged**: identity (name-slug URI), `functions`/`roles` cross-refs, no new field.
- **New emission** (`to_triples` override): `(self.uri, rdfs:label, Literal(self.name))`
  — the authored `name` verbatim, including accents/casing/spacing (the slug, used only
  for identity, is unchanged).
- **Provenance**: unchanged — the label rides the existing identity
  `DerivedAssertion(uri, uri, None)`; **no** new E13 (FR-006). `derived_assertions()` is
  not overridden.

### `NarrativeFunction` (`golem:G10_Narrative_Function`)
- **Unchanged**: identity, optional `type_uri` + its `crm:P2_has_type`/`rdf:type` pair
  and that link's E13 (iteration 030).
- **New emission** (extend the existing `to_triples` override): `(self.uri, rdfs:label,
  Literal(self.name))`.
- **Dedup invariant**: the function is minted **once** per distinct slug in
  `_mint_functions`, so exactly one label triple exists even when many fiches name it
  (FR-002).
- **Provenance**: unchanged — label rides identity; no new E13.

### `NarrativeSequence` (`golem:G7_Narrative_Sequence`)
- **Unchanged**: identity (sequence-name slug), `units` cross-ref → one
  `dlp:proper-part` edge per member, in resolved order; no new field. The `units` tuple
  is already sorted by `_member_sort_key` at assembly time.
- **New emission** (`to_triples` override): after `super().to_triples()`, for each member
  at 1-based position `i` in `units`:
  `(ref_uri(unit), bw:sequenceOrdinal, Literal(i, datatype=xsd:integer))`.
- **New provenance** (`derived_assertions` override): after `super().derived_assertions()`
  (identity + per-member proper-part E13s, all file-level), one extra per member:
  `DerivedAssertion(target=unit.uri, attribute=self.uri, source_field="order")` →
  its own file-level `crm:E13_Attribute_Assignment` (FR-006, D6).

## New term

### `bw:sequenceOrdinal`
- **IRI**: `https://bookwright.dev/vocab/bw#sequenceOrdinal`.
- **Python**: `BW_SEQUENCE_ORDINAL = BW["sequenceOrdinal"]` in `golem/namespaces.py`
  (added to `__all__`, with a one-line doc comment in the research/provenance predicate
  block).
- **Declaration**: `sources.ttl` —
  ```turtle
  bw:sequenceOrdinal a rdf:Property ;
      rdfs:label "sequenceOrdinal"@en ;
      rdfs:comment "A narrative unit's 1-based position within its narrative sequence (xsd:integer)."@en .
  ```
- **Closure status**: outside `golem.ttl`, `CLASS_IRI`, and the `test_namespaces.py`
  closure list — exactly like the `bw:reference` family (Principle X, FR-005/SC-005).
- **Object**: `xsd:integer` literal; value = the member's derived contiguous rank (D3).

## Ordinal value rules (FR-004, edge cases)

The rank is the member's 1-based index in the `_member_sort_key`-sorted `units` tuple,
which already collapses every authoring shape into one strict total order:

| Authoring shape | Resolved order (existing) | Materialized ordinal |
|---|---|---|
| `order: 1, 2, 3` contiguous | ascending by `order` | `1, 2, 3` |
| `order:` with a gap (`1, 5, 9`) | ascending by `order` | `1, 2, 3` (contiguous, gap collapsed) |
| missing `order:` on a member | that member placed **last**, by slug | gets the last ordinal(s) |
| duplicate `order:` within a sequence | tie-broken by unit slug | distinct, strict ranks |
| single-member sequence | the lone member | `1` |
| `order:` without `sequence:` | no membership (soft `UnknownKey` warning) | **none emitted** |
| unit with no `sequence:` | not a member | **none emitted** (label still emitted) |
| empty/absent `outline/units/` | no units | no labels, no ordinals (byte-identical) |

Sorting members by `bw:sequenceOrdinal` reproduces the declared order with 100%
positional fidelity (SC-002) and is identical across rebuilds (the sort is total — SC-006
for the asserted facts).

## Triple-count deltas (for fixture-oracle reconciliation, FR-011)

Per build, relative to today:
- `+1` `rdfs:label` triple per `NarrativeUnit`.
- `+1` `rdfs:label` triple per distinct `NarrativeFunction`.
- `+1` `bw:sequenceOrdinal` triple per **member** unit (units in a sequence only).
- `+1` `crm:E13_Attribute_Assignment` (+ its own type/target/attribute/source triples)
  per member unit (the ordinal’s reification).

The `tiny-quest` oracle pins **set/count** facts and the ordered `members` list; it does
**not** pin a total triple count, and the E2E asserts only `triples > 0`. Oracle
reconciliation therefore adds the new **label facts** (FR-011) and keeps `members`
unchanged (now reproducible via SPARQL). No back-fitting: every added fact is read from
a fresh `graph build` of the committed fixture.
