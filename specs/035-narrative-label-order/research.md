# Phase 0 — Research: G9 `rdfs:label` + queryable sequence order

The spec's `/speckit-clarify` session already fixed the contested choices (ordinal
mechanism, ordinal value, ordinal provenance, predicate home + datatype). This file
records the remaining `/speckit-plan` decisions — the predicate's exact local name, the
base index, the emission site, the E13 target/attribute pair, and the one test-policy
resolution the design forces — each with rationale and rejected alternatives, plus the
empirical checks that de-risk them.

## Empirical checks run before deciding

```text
RDFS.label   ∈ frozen_terms()  → True    # unit/function labels do NOT break term closure
BW.reference ∈ frozen_terms()  → False   # bw: terms are outside the frozen GOLEM closure
PROPER_PART  ∈ frozen_terms()  → True    # the membership edge is frozen, as expected
```

Consequence: the **labels** are closure-safe everywhere; only the **ordinal**’s `bw:`
predicate sits outside the frozen closure (by design) and so determines the one test
refinement below.

---

## D1 — Ordinal mechanism: per-unit predicate triple *(confirmed from clarify)*

**Decision**: `(unit, bw:sequenceOrdinal, Literal(rank, xsd:integer))` — one triple per
member unit, **not** a reified per-membership node.

**Rationale**: A unit declares **at most one** `sequence:` (`outline.py:195–206`,
single optional key), so its membership is unique; a per-edge membership node would be
plumbing justified only by hypothetical multi-membership — speculative, dropped under
Scope & Release Discipline. The per-unit triple is one SPARQL hop from the sequence
(`?seq dlp:proper-part ?unit . ?unit bw:sequenceOrdinal ?n`) and adds no node.

**Alternatives rejected**: reified membership node carrying the index (more triples,
fully general, but YAGNI under single-membership); `rdf:Seq`/`rdf:_n` container
membership (rdflib-awkward to `ORDER BY`, and `rdf:_n` predicates are not a clean
integer literal to sort).

## D2 — Predicate local name + base index *(the /speckit-plan cosmetics)*

**Decision**: local name **`sequenceOrdinal`** → `BW["sequenceOrdinal"]` =
`https://bookwright.dev/vocab/bw#sequenceOrdinal`. Literal datatype **`xsd:integer`**
(clarified). Base index **1-based**.

**Rationale**:
- `sequenceOrdinal` reads unambiguously at the query site (`?unit bw:sequenceOrdinal
  ?n`) and does **not** collide, even by eye, with the authoring `order:` front-matter
  key — a `bw:order` would invite the false reading that it mirrors the raw authored
  integer (it does not; it is the *derived* rank, D3/clarify).
- **1-based**: in the common contiguous case the materialized rank reads identically to
  the author's `order: 1, 2, 3`, so a human eyeballing the graph sees the expected
  numbers. SC-002 asserts only *relative* order, so 0- vs 1-based is sort-identical and
  purely cosmetic; 1-based is the friendlier of the two. Concretely `rank = tuple_index
  + 1`.

**Alternatives rejected**: `bw:order` (collision-of-meaning with the authoring key);
`bw:ordinal` (fine, but less specific about *which* ordering); 0-based (sort-identical,
less human-friendly).

## D3 — Ordinal value: derived contiguous rank of the resolved total order *(confirmed)*

**Decision**: the rank is the member’s index (1-based, D2) in the **already-sorted**
`units` tuple — the tuple `_assemble_sequences` builds via `_member_sort_key`
(`outline.py:144–167`): ascending by declared `order:`, a missing `order:` placed last,
ties broken by unit slug.

**Rationale**: only a derived rank is **total and gap-free** under a missing, duplicated,
or absent authored `order:`. It reuses the existing total order verbatim (invents no new
ordering) and *is* the order the declaration resolves to — so "list in declared order"
becomes unambiguous and `ORDER BY`-clean (FR-004, edge cases). The raw authored integer
cannot represent a missing/duplicate position as a clean total order, so it is **not**
materialized.

## D4 — Emission site: `NarrativeSequence.to_triples()`

**Decision**: emit both the existing `dlp:proper-part` edges **and** the new per-unit
ordinals from `NarrativeSequence.to_triples()`. The unit itself emits **no** ordinal.

**Rationale**: the ordinal is *relational* — the unit does not know its rank; only the
assembled sequence holds the resolved member order. A unit in no sequence therefore
gets a label but no ordinal (edge case ✓), exactly as desired. Implementation: override
`to_triples` to `yield from super().to_triples()` (`rdf:type` + proper-part via the
existing `units` cross-ref) then, for each member at 1-based position `i`, yield
`(ref_uri(unit), BW_SEQUENCE_ORDINAL, Literal(i, datatype=XSD.integer))`. The subject is
the **unit** URI (one hop from the sequence), the same override pattern
`NarrativeFunction` already uses for its `crm:P2_has_type` triples.

**Alternatives rejected**: threading the rank into `NarrativeUnit` at build time (the
unit would need to know its sequence — couples the unit to assembly, breaks the
"unit declares at most one sequence but is built before assembly" flow); emitting from
`_assemble_sequences` directly into the engine (bypasses the uniform `to_triples`
pipeline `_graph.py` depends on).

## D5 — Labels: single `rdfs:label` triple, riding the identity assertion

**Decision**:
- `NarrativeUnit.to_triples()` overrides to add `(self.uri, rdfs:label,
  Literal(self.name))` after `super().to_triples()`.
- `NarrativeFunction.to_triples()` (already overridden for typing) additionally yields
  `(self.uri, rdfs:label, Literal(self.name))`.
- **No new E13**: the label rides the entity's already-emitted identity assertion (the
  base `DerivedAssertion(uri, uri, None)` → file-level provenance), exactly as
  `CharacterRole` (`feature.py:169`) and free-text `CharacterFeature` (`feature.py:140`)
  do. `derived_assertions()` is **not** changed for labels.

**Rationale**: this is the one-triple label pattern the spec mandates (FR-001/FR-002),
distinct from the two-triple `P2_has_type` + `rdf:type` typing path. A function
deduplicated across fiches is minted **once** in `_mint_functions` (`outline.py:292–298`),
so the single minted entity yields exactly one label triple (FR-002, no duplicates) for
free. `rdfs:label` ∈ `frozen_terms()` (checked above), so it never disturbs term
closure.

**Sequences get no label**: FR-001/FR-002 scope labels to units and functions only. A
sequence is addressed by its slug URI; adding a sequence label would be out-of-scope
speculative surface (Scope & Release Discipline). The order query binds the sequence by
its `narrative-sequence/<slug>` URI.

## D6 — Ordinal provenance: its own file-level E13, target=unit / attribute=sequence

**Decision**: override `NarrativeSequence.derived_assertions()` to `yield from
super().derived_assertions()` (identity + one proper-part E13 per member, all file-level
because the assembled sequence carries `key_lines={}`) then, per member, yield
`DerivedAssertion(target=unit.uri, attribute=self.uri, source_field="order")`.
`build_provenance` (`bible.py:241–255`) turns each into an `AttributeAssignment(target=
unit, attribute=sequence, source=relpath)` — file-level, no `:line`, since `key_lines`
is empty.

**Rationale**:
- FR-006 mandates the ordinal be reified as **its own** E13 (the ordinal is relational —
  a property of the assembled membership — so it cannot ride the unit's identity
  assertion the way the label does; structural provenance holds: every non-identity
  assertion is reified).
- **target = unit** (`P140_assigned_attribute_to`): the ordinal is an attribute *of the
  unit* (its position). **attribute = sequence** (`P141_assigned`): the context it
  positions the unit within. This is distinct in direction from the existing
  proper-part membership E13 (target=sequence, attribute=unit), so the two reifications
  do not collide.
- The **literal rank lives in the main graph** (the `bw:sequenceOrdinal` triple), not in
  the E13 — exactly as a biographical-year E13 points at the *feature node* while the
  year literal lives on a separate `Dimension` (`feature.py:129–138`). Established
  precedent: E13s reify nodes; literals live on the asserted triples.
- **`source_field="order"`** names the originating front-matter key (the
  `DerivedAssertion` convention). Because the assembled sequence's `key_lines={}`,
  `build_provenance` resolves it to file-level provenance (no `:line`) — the
  minted-function / assembled-sequence precedent (`outline.py:152`, `298`).

**Determinism note (honest)**: `AttributeAssignment` is a `MintedEntity`; its URI is a
time-ordered `uuid7` (iteration 012, FR-013) — so the raw `graph.ttl` bytes were never
literally identical across runs even before this change. SC-006 ("byte-identical graph,
including labels and ordinals") holds for the **asserted facts** — the deterministic
`rdfs:label` and `bw:sequenceOrdinal` triples (and proper-part membership) — which is
exactly what the determinism tests compare (`test_narrative_workflow.py::
test_build_and_validate_are_deterministic` compares `_graph_facts`, never E13 mint URIs).
This change introduces **no new** source of non-determinism.

**Alternative rejected**: extending `AttributeAssignment` to carry a literal `attribute`
so the rank value lives in the E13 — a new provenance mechanism, rejected as out of
scope and inconsistent with the year-E13 precedent; the spec asks to reuse the existing
E13 path, not extend it.

## D7 — Term-closure test resolution (the one test-policy change)

**Problem**: `test_triples.py::test_term_closure_over_frozen_ontology` iterates
`_sample_entities()` (which includes a `NarrativeSequence` with a member unit) and
asserts every emitted predicate is `RDF.type` or ∈ `frozen_terms()`. With D1/D4 the
sequence now emits `bw:sequenceOrdinal`, which is **not** frozen → the test would fail.

**Why this is not a Principle X violation**: `bw:` is Bookwright's own vocabulary,
declared in `sources.ttl`, intentionally outside the frozen GOLEM closure — the same
status as `bw:reference`/`bw:claim`/… The codebase already tolerates this implicitly by
**excluding** the research entities (`Source`/`Finding`/`Anchor`, which emit `bw:` terms)
from `_sample_entities()`. The only thing that changed is that a *registered narrative
concept* now also carries a `bw:` term, so the tolerance must become explicit.

**Decision**: refine the assertion to accept the `bw:` namespace as the legitimate
non-frozen home for Bookwright's own declared predicates:

```python
is_bw = str(predicate).startswith(str(ns.BW))
assert predicate == RDF.type or predicate in frozen or is_bw, f"predicate {predicate} not frozen/bw"
```

with a comment explaining the rationale. The frozen GOLEM closure — `golem.ttl`,
`CLASS_IRI`, and the **`test_namespaces.py` closure list** — is left **unmodified and
green** (SC-005). This is the honest fix, not a back-fit: it states an invariant the
suite already relied on.

**Alternatives rejected**: dropping `seq` from `_sample_entities()` (loses coverage of a
core concept's `rdf:type` and emission); special-casing only `bw:sequenceOrdinal` (more
brittle than recognising the whole `bw:` namespace, which is the actual invariant).

## D8 — The two demonstrative SPARQL queries (FR-007/FR-008/SC-003)

Shipped in a new `tests/golem/test_narrative_label_order.py` over a graph built by
feeding sample entities through `RdflibIndexer` (full IRIs, no PREFIX reliance, matching
the E2E’s `<{GOLEM[...]}>` style):

**Q1 — find a unit by its authored name** (US1):
```sparql
SELECT ?u WHERE { ?u a <…G9_Narrative_Unit> ; <…rdfs#label> "La traición del senescal" }
```
Returns the matching unit URI; a name present in no fiche returns the empty result.

**Q2 — list a sequence’s units in declared order** (US2):
```sparql
SELECT ?u ?n WHERE {
  <…/narrative-sequence/quest> <…dlp#proper-part> ?u .
  ?u <…bw#sequenceOrdinal> ?n
} ORDER BY ?n
```
Returns the member units in ascending ordinal — the author's declared order.

The E2E `_ordered_members` is rewritten to use **Q2 against the derived graph** (it
previously read tuple order off the entity because "the graph carries no member
ordinal" — the precise assumption this iteration overturns), proving the order axis end
to end. Its docstring is corrected accordingly.
