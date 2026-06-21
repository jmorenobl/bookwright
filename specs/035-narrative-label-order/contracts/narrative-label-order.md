# Contract: narrative label + queryable sequence order

The observable graph contract this iteration adds. Stated as invariants over the derived
graph; every test asserts against one of these.

## C1 — Unit label
For every `?u a golem:G9_Narrative_Unit` ingested from an `outline/units/` fiche with
authored `name N`, the graph contains **exactly one** triple `?u rdfs:label "N"` with `N`
verbatim (accents, casing, leading/trailing spaces as authored). The unit's URI slug is
unchanged.

## C2 — Function label
For every minted `?f a golem:G10_Narrative_Function` with authored `name N`, the graph
contains **exactly one** triple `?f rdfs:label "N"`. A function named by several fiches
(deduplicated by slug) carries exactly one label triple — never duplicates.

## C3 — Member ordinal
For every member unit `?u` of a sequence `?seq` (i.e. `?seq dlp:proper-part ?u`), the
graph contains **exactly one** triple `?u bw:sequenceOrdinal ?n` where `?n` is an
`xsd:integer`. A unit that is in no sequence has **no** `bw:sequenceOrdinal` triple. The
ordinal is reachable from the sequence in one hop: `?seq dlp:proper-part ?u . ?u
bw:sequenceOrdinal ?n`.

## C4 — Ordinal reproduces the resolved total order
Within one sequence, ordering its members by `bw:sequenceOrdinal` ascending yields the
exact order `_member_sort_key` already defines: ascending by declared `order:`, missing
`order:` last, ties broken by unit slug. The ordinals are **contiguous and 1-based**
(`1..k` for a k-member sequence) regardless of gaps/missing/duplicate authored `order:`.
Identical across rebuilds.

## C5 — Ordinal provenance
Each member ordinal is reified by its **own** `crm:E13_Attribute_Assignment` with
`crm:P140_assigned_attribute_to` → the unit and `crm:P141_assigned` → the sequence, and a
**file-level** `crm:P16_used_specific_object` source (the relpath, no `:line`). This E13
is distinct from the proper-part membership E13 (which assigns the unit *to* the
sequence). Labels add **no** E13 (they ride the entity identity assertion).

## C6 — Frozen ontology untouched (Principle X / SC-005)
`golem.ttl`, `CLASS_IRI` (17 IRIs), and the predicate list checked by
`tests/golem/test_namespaces.py` are unmodified. `rdfs:label` is already in
`frozen_terms()`. `bw:sequenceOrdinal` is declared in `resources/vocabularies/sources.ttl`
and lives outside the frozen closure, exactly like the `bw:reference` family.

## C7 — No regression (FR-009)
Every other emitted triple is unchanged. `narrative_structure` and all other validators
stay green. The four gates pass (`ruff check`, `ruff format --check`, `mypy --strict`,
`pytest` ≥ 80%).

## Query contract (the two demonstrative SPARQL queries, FR-007/FR-008/SC-003)

### Q1 — resolve a unit by name
```sparql
SELECT ?u WHERE {
  ?u a <https://w3id.org/golem/ontology#G9_Narrative_Unit> ;
     <http://www.w3.org/2000/01/rdf-schema#label> "La traición del senescal" .
}
```
**Must** return the matching unit URI; a name in no fiche **must** return zero rows.

### Q2 — list a sequence's units in declared order
```sparql
SELECT ?u ?n WHERE {
  <…/narrative-sequence/quest>
     <http://www.ontologydesignpatterns.org/ont/dlp/DOLCE-Lite.owl#proper-part> ?u .
  ?u <https://bookwright.dev/vocab/bw#sequenceOrdinal> ?n .
} ORDER BY ?n
```
**Must** return the member units in the author's declared order; the same query against a
different sequence **must** return only that sequence's members in its own order.
