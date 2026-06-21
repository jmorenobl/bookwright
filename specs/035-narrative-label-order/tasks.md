---
description: "Task list for iteration 035 — G9 rdfs:label + queryable sequence order"
---

# Tasks: G9 `rdfs:label` + queryable sequence order

**Input**: Design documents from `/specs/035-narrative-label-order/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/narrative-label-order.md ✅, quickstart.md ✅

**Tests**: Included. The spec explicitly requires the two demonstrative SPARQL queries to ship as automated tests (FR-007/FR-008/SC-003) and the awakened fixture/E2E counts to be reconciled (FR-011/SC-004). Emission and provenance asserts back them up.

**Organization**: Grouped by user story. US1 (unit labels) and US2 (sequence order) are both P1 and independently shippable; US3 (function labels) is P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, or US3 (maps to spec.md user stories)
- All paths are repo-root-relative.

## Path Conventions

Single project (src-layout): `src/bookwright/`, `tests/` at repository root.

---

## Phase 1: Setup (Shared term declaration)

**Purpose**: Declare the new `bw:sequenceOrdinal` predicate — the queryable-order term — once, outside the frozen GOLEM closure (Principle X, FR-005). This is the only shared prerequisite; it is consumed by US2.

- [ ] T001 [P] Add `BW_SEQUENCE_ORDINAL = BW["sequenceOrdinal"]` to `src/bookwright/golem/namespaces.py` — define the constant alongside the existing `BW` namespace and the `bw:reference`-family predicates, add it to `__all__`, and give it a one-line doc comment ("A narrative unit's 1-based position within its sequence; xsd:integer").
- [ ] T002 [P] Declare `bw:sequenceOrdinal` in `src/bookwright/resources/vocabularies/sources.ttl` as an `rdf:Property` with `rdfs:label "sequenceOrdinal"@en` and `rdfs:comment "A narrative unit's 1-based position within its narrative sequence (xsd:integer)."@en`, following the existing `bw:reference`-family declarations in the file.

**Checkpoint**: The ordinal predicate exists and is documented; it is NOT in `golem.ttl`, `CLASS_IRI`, or the `test_namespaces.py` closure list (verify in T011/T018).

---

## Phase 2: Foundational

**Purpose**: None required. No shared models, schema, or infrastructure block the user stories beyond the Setup term. Frozen ontology is untouched; existing `SluggedEntity` / `DerivedAssertion` / `RdflibIndexer` machinery is reused as-is.

**Checkpoint**: Foundation ready — user stories can proceed (US1 and US3 do not even need Phase 1; US2 does).

---

## Phase 3: User Story 1 - Find a narrative beat by its authored name (Priority: P1) 🎯 MVP

**Goal**: Every `G9_Narrative_Unit` emits a single `rdfs:label` carrying its authored `name` verbatim, so a SPARQL query can resolve a beat by name (contract C1, Q1).

**Independent Test**: Build a graph from sample entities containing ≥1 unit, run the find-by-label query (Q1), assert the unit URI is returned and an absent name returns zero rows. Removing all ordinal work does not affect this.

### Tests for User Story 1

- [ ] T003 [US1] Create `tests/golem/test_narrative_label_order.py` with the Q1 find-by-name SPARQL test (FR-007/SC-003): feed sample entities (incl. a `NarrativeUnit` named e.g. "La traición del senescal") through `RdflibIndexer`, run `SELECT ?u WHERE { ?u a <…G9_Narrative_Unit> ; rdfs:label "…" }` with full IRIs (no PREFIX reliance, matching the E2E style in contracts §Q1), assert the matching URI is returned and a name in no entity returns the empty result.
- [ ] T004 [US1] Add a unit-label emission assertion to `tests/golem/test_triples.py` (FR-001): assert a sample `NarrativeUnit` emits exactly one `(uri, rdfs:label, Literal(name))` triple with the authored name byte-for-byte.

### Implementation for User Story 1

- [ ] T005 [US1] In `src/bookwright/golem/modules/narrative.py`, override `NarrativeUnit.to_triples()` to `yield from super().to_triples()` then `yield (self.uri, RDFS.label, Literal(self.name))` (import `RDFS`, `Literal`) — the unit-label emission required by FR-001. No `derived_assertions()` change — the label rides the existing identity assertion (FR-006/D5).

**Checkpoint**: US1 complete — units are name-queryable; T003/T004 green. SC-001 satisfiable.

---

## Phase 4: User Story 2 - List a sequence's units in their declared order (Priority: P1)

**Goal**: Each member unit's resolved position in its `G7_Narrative_Sequence` is materialized as a queryable `(unit, bw:sequenceOrdinal, Literal(rank, xsd:integer))` triple reproducing the existing total order, reified by its own file-level E13 (contracts C3/C4/C5, Q2). Depends on Phase 1 (the `bw:sequenceOrdinal` term).

**Independent Test**: Build a graph from units declaring `sequence:`/`order:`, run the order query (Q2) `ORDER BY ?n`, assert URIs come back in declared order — including gap/missing/duplicate `order:`. Removing all label work does not affect this.

### Tests for User Story 2

- [ ] T006 [US2] Extend `tests/golem/test_narrative_label_order.py` with the Q2 list-in-order SPARQL test (FR-003/FR-008/SC-003): over a built graph, `SELECT ?u ?n WHERE { <…narrative-sequence/slug> dlp:proper-part ?u . ?u bw:sequenceOrdinal ?n } ORDER BY ?n`; assert members return in declared order, and the same query against a second sequence returns only its members in its own order (C3/C4).
- [ ] T007 [US2] Add the term-closure `bw:` exemption to `tests/golem/test_triples.py::test_term_closure_over_frozen_ontology` (D7): accept `predicate == RDF.type or predicate in frozen or str(predicate).startswith(str(BW))`, with a comment that `bw:` is Bookwright's own vocabulary outside the frozen GOLEM closure (same status as `bw:reference`). Leave `tests/golem/test_namespaces.py` unmodified.
- [ ] T008 [P] [US2] Add a `NarrativeSequence` ordinal-E13 assertion to `tests/golem/test_derived_assertions.py`: assert each member yields a `DerivedAssertion(target=unit.uri, attribute=self.uri, source_field="order")` reified as its own file-level `crm:E13` (target=unit via `P140`, attribute=sequence via `P141`, file-level `P16` source, no `:line`) — distinct from the proper-part membership E13 (C5/D6).
- [ ] T009 [P] [US2] Reinforce ordinal materialization in `tests/io/test_outline_sequences.py` (FR-003/FR-004): build a sequence with gap/missing/duplicate `order:` across members and assert the emitted `bw:sequenceOrdinal` objects are contiguous `1..k` `xsd:integer` with subject = each member unit URI, reproducing `_member_sort_key` order (C4, edge-case table in data-model.md).
- [ ] T010 [US2] Rewrite `tests/e2e/test_narrative_workflow.py::_ordered_members` to query the built graph via Q2 (`?seq dlp:proper-part ?u . ?u bw:sequenceOrdinal ?n` `ORDER BY ?n`) instead of reading the emitter's tuple order; fix its docstring (drop the "the graph carries no member ordinal" assumption) and keep the determinism test comparing `_graph_facts` — the byte-identical-rebuild check that verifies FR-013 (graph stays a derived cache) and SC-006 over the new labels/ordinals (D6/D8).

### Implementation for User Story 2

- [ ] T011 [US2] In `src/bookwright/golem/modules/narrative.py`, override `NarrativeSequence.to_triples()` to `yield from super().to_triples()` then, for each member at 1-based position `i` in `self.units`, `yield (ref_uri(unit), BW_SEQUENCE_ORDINAL, Literal(i, datatype=XSD.integer))` — subject is the **unit** URI (import `BW_SEQUENCE_ORDINAL`, `XSD`, and the existing `ref_uri` helper). The `units` tuple is already `_member_sort_key`-sorted, so `i` is the resolved contiguous rank — the queryable ordinal of FR-003 reproducing the total order of FR-004 (D3/D4).
- [ ] T012 [US2] In the same file, override `NarrativeSequence.derived_assertions()` to `yield from super().derived_assertions()` then, per member, `yield DerivedAssertion(target=unit.uri, attribute=self.uri, source_field="order")` so `build_provenance` reifies each as its own file-level E13 (FR-006/D6). Depends on T011 being in place (same file).

**Checkpoint**: US2 complete — sequences are order-queryable; T006–T010 green. SC-002 satisfiable. US1 + US2 both work independently.

---

## Phase 5: User Story 3 - Find a narrative function by its authored name (Priority: P2)

**Goal**: Every minted `G10_Narrative_Function` emits exactly one `rdfs:label` carrying its `name`, even when named by several fiches (slug-deduped) — contract C2.

**Independent Test**: Build a graph containing ≥1 function, query functions by `rdfs:label`, assert the function URI is returned and a function named by multiple fiches carries exactly one label triple.

### Tests for User Story 3

- [ ] T013 [US3] Add a function-label assertion to `tests/golem/test_triples.py` (FR-002): assert a sample `NarrativeFunction` emits exactly one `(uri, rdfs:label, Literal(name))`, coexisting with its existing `crm:P2_has_type`/`rdf:type` typing pair when `type_uri` is set. The **dedup invariant** (FR-002/C2 — a function named by several fiches carries exactly one label) holds because `_mint_functions` already mints exactly one `NarrativeFunction` entity per slug (existing io-layer dedup coverage); one entity ⇒ one label triple, so this entity-level assertion is sufficient and no multi-fiche test is duplicated here.

### Implementation for User Story 3

- [ ] T014 [US3] In `src/bookwright/golem/modules/narrative.py`, extend the existing `NarrativeFunction.to_triples()` override to additionally `yield (self.uri, RDFS.label, Literal(self.name))` after `super().to_triples()` (alongside the existing `type_uri` typing triples). No `derived_assertions()` change for the label (FR-006). Same file as T005/T011/T012 — sequential.

**Checkpoint**: All three stories independently functional. SC-001 (units + functions) and SC-002 satisfiable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Reconcile awakened fixture/E2E counts to the new awake totals (FR-011, no back-fitting), close DEBT-005, document the new query surface, and prove the four gates green (SC-004).

- [ ] T015 [P] Reconcile `tests/fixtures/tiny-quest/expected-narrative.md`: add the new label facts for units and functions read from a fresh `graph build` of the committed fixture; keep the `sequence.members` ordered list unchanged (now reproducible via Q2). Do NOT back-fit any number (FR-011/data-model.md triple-count deltas).
- [ ] T016 [P] Update `docs/narrative-structure.md` (Spanish): document `rdfs:label` on units/functions and the queryable `bw:sequenceOrdinal` order, embedding the two SPARQL snippets (find-by-name, list-in-order) from quickstart.md.
- [ ] T017 Remove the `DEBT-005` entry from `DEBT.md` (git retains history) and update the DEBT-006 cross-reference line that points at DEBT-005 so no dangling reference remains (FR-012).
- [ ] T018 Run the four gates from repo root and fix any fallout: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (full suite, ≥80% coverage). Confirm `tests/golem/test_namespaces.py` closure list is unmodified and green (SC-005) and `narrative_structure` + all validators stay green (FR-009/SC-004). Verify FR-010 (authoring format unchanged) by confirming the existing `tests/io/test_outline_sequences.py` and outline-parsing tests — which exercise the `name`/`functions`/`roles`/`sequence`/`order` keys (`UNIT_KEYS`) — still pass untouched, and FR-013 (graph stays a derived, reconstructible cache) via the T010 byte-identical-rebuild determinism check. Walk `specs/035-narrative-label-order/quickstart.md` to spot-check SC-001/SC-002/SC-006.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. Consumed by US2 only.
- **Foundational (Phase 2)**: Empty — no blocking work.
- **US1 (Phase 3)**: Independent — needs neither Phase 1 nor other stories.
- **US2 (Phase 4)**: Needs Phase 1 (the `bw:sequenceOrdinal` term, T001/T002). Independent of US1/US3.
- **US3 (Phase 5)**: Independent — needs neither Phase 1 nor other stories.
- **Polish (Phase 6)**: After all desired stories land (T015 reflects whichever labels/ordinals were implemented; T018 gates the whole change).

### Critical same-file serialization (NOT parallel)

- `src/bookwright/golem/modules/narrative.py` — touched by T005 (US1), T011 + T012 (US2), T014 (US3). These four MUST be sequential.
- `tests/golem/test_triples.py` — touched by T004 (US1), T007 (US2), T013 (US3). Sequential.
- `tests/golem/test_narrative_label_order.py` — created by T003 (US1), extended by T006 (US2). Sequential.

### User Story Dependencies

- US1 (P1): no dependency on other stories.
- US2 (P1): depends only on Phase 1; no dependency on US1/US3.
- US3 (P2): no dependency on other stories.

### Within Each User Story

- Tests are written first and expected to FAIL before the implementation task lands them green.
- US2: T011 (emit ordinal) before T012 (reify ordinal) — both edit `narrative.py`.

---

## Parallel Opportunities

- **Phase 1**: T001 and T002 are different files → run in parallel.
- **US2 tests**: T008 (`test_derived_assertions.py`) and T009 (`test_outline_sequences.py`) are different files → parallel. T006/T007 share files with other tasks (see serialization).
- **Polish**: T015 (fixture oracle) and T016 (docs) are different files → parallel; T017 then T018 last.
- **Across stories** (if staffed): US1, US2, US3 implementations can proceed concurrently ONLY by different developers coordinating the shared `narrative.py` / `test_triples.py` edits — otherwise treat them as sequential per the serialization note.

### Parallel Example: Phase 1 (Setup)

```bash
# Different files, no dependency between them:
Task: "Add BW_SEQUENCE_ORDINAL to src/bookwright/golem/namespaces.py"
Task: "Declare bw:sequenceOrdinal in src/bookwright/resources/vocabularies/sources.ttl"
```

### Parallel Example: US2 independent test files

```bash
Task: "Ordinal-E13 assertion in tests/golem/test_derived_assertions.py"
Task: "Ordinal materialization reinforcement in tests/io/test_outline_sequences.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup is not even required for US1.
2. Complete Phase 3 (US1): T003 → T004 → T005.
3. **STOP and VALIDATE**: units are name-queryable (SC-001 for units). Shippable increment.

### Incremental Delivery

1. US1 (unit labels) → name-by-beat retrieval works (MVP).
2. Phase 1 + US2 (sequence ordinals) → declared-order retrieval works — the harder half of the recall gap.
3. US3 (function labels) → symmetry extension, P2.
4. Polish: reconcile fixtures/docs, delete DEBT-005, four gates green.

### Notes

- [P] = different files, no incomplete-task dependency.
- Verify each test FAILS before its implementation task makes it pass.
- Commit after each task or logical group (the auto-git hook offers commits between phases).
- No new ontology class/predicate in `golem.ttl`/`CLASS_IRI`/`test_namespaces.py` closure (Principle X / SC-005) — the only term added is `bw:sequenceOrdinal` in `sources.ttl`.
- Ships as `v0.4.3` via the `bookwright-release` skill after merge (separate manual step).
