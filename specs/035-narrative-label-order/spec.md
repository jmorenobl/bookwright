# Feature Specification: G9 `rdfs:label` + queryable sequence order

**Feature Branch**: `035-narrative-label-order`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Necesidad: la capa narrativa no es consultable por contenido ni por orden, lo que se midió en el dogfooding. (a) Las G9_Narrative_Unit no emiten `rdfs:label`: su nombre humano (`name`) vive SOLO en el slug de la URI… (b) El `order:` declarado en las units se consume al ensamblar la secuencia y NO se materializa como triple… Queremos materializar (a) `rdfs:label` en las unidades narrativas (y, con el mismo patrón, en las funciones narrativas si encaja) con su `name` autorado, y (b) un ordinal CONSULTABLE de la membresía de secuencia que refleje el `order:` declarado…"

## Overview *(context, not a section requirement)*

The narrative-structure layer (G7/G9/G10) was wired into the graph in v0.4
(iterations 028–032): `outline/units/*.md` fiches ingest as `G9_Narrative_Unit`
nodes, their `functions:` mint `G10_Narrative_Function` nodes, and the optional
`sequence:`/`order:` keys assemble `G7_Narrative_Sequence` wholes whose member
units hang off `dlp:proper-part`. A real-book dogfooding exercise
("El Cerco de Almenara", 2026-06-21) measured a **structural recall gap**: two
authoring/agent probes fail by construction, not by chance —

- **"find the beat about <topic>" / "list the beats named X"** fails because a
  unit's human name lives **only** inside its URI slug; the model emits no
  `rdfs:label`, so no SPARQL match on a beat's name is possible.
- **"list the functions/units of sequence X in their declared order"** fails
  because the authored `order:` is consumed when the sequence tuple is assembled
  and is **never materialized** as a triple (RDF is unordered; the ordering today
  is merely the emitter's tuple order — `narrative.py:67-68`). SPARQL has nothing
  to `ORDER BY`.

This feature closes that gap by making the narrative layer queryable **by content**
(name labels) and **by order** (a queryable per-membership ordinal), without
touching the frozen ontology. It is the recorded resolution of **DEBT-005** and the
explicit prerequisite to any future vector-search evaluation (which is *not* in
scope here).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a narrative beat by its authored name (Priority: P1)

An author or an agent skill knows a beat by its human name ("La traición del
senescal") but not by its URI slug. They want a graph query that returns the unit
node when matched on that name, so name-based retrieval of beats becomes possible.

**Why this priority**: This is half of the measured recall gap and the most direct
unlock — without a name on the node, *no* content query over beats can succeed. It
is independently shippable: labels deliver value even if ordering were deferred.

**Independent Test**: Build the graph from a fixture that contains at least one
narrative unit, then run a SPARQL query that selects the unit by matching its
authored name against `rdfs:label`; assert the unit's URI is returned. Removing the
ordinal work entirely would not affect this test.

**Acceptance Scenarios**:

1. **Given** an `outline/units/` fiche whose `name:` is "La traición del senescal",
   **When** the graph is built, **Then** the corresponding `G9_Narrative_Unit` node
   carries an `rdfs:label` literal equal to that authored name (byte-for-byte,
   including accents and casing).
2. **Given** a built graph, **When** a SPARQL query filters units by their
   `rdfs:label`, **Then** it returns the matching unit's URI, and a query for a name
   present in no fiche returns the empty result.

---

### User Story 2 - List a sequence's units in their declared order (Priority: P1)

An author or an agent skill wants the beats of a story-line returned **in the order
the author declared** (the `order:` key), so "walk sequence X from first beat to
last" is answerable from the graph alone.

**Why this priority**: This is the other half of the measured gap and the
non-trivial part of the feature — materializing order under unordered RDF without a
new ontology class. It is independently shippable: ordering delivers value even if
labels were deferred.

**Independent Test**: Build the graph from a fixture whose units declare `sequence:`
and `order:`, then run a single SPARQL query that lists that sequence's member units
`ORDER BY` the materialized ordinal; assert the returned URIs appear in exactly the
declared order. Removing the label work entirely would not affect this test.

**Acceptance Scenarios**:

1. **Given** three units in one sequence with `order: 1`, `order: 2`, `order: 3`,
   **When** the graph is built, **Then** each `dlp:proper-part` membership carries a
   queryable integer ordinal whose ascending sort reproduces 1→2→3.
2. **Given** a built graph, **When** a SPARQL query lists a sequence's units sorted
   by that ordinal, **Then** the units come back in the author's declared order, and
   the same query against a different sequence returns only that sequence's units in
   its own order.
3. **Given** units whose `order:` has a gap, a missing value, or a duplicate, **When**
   the graph is built, **Then** the ordinal still yields the **same total order** the
   existing assembly already defines (ascending by `order:`; a missing `order:`
   sorts last; ties broken by slug) — deterministically identical across rebuilds.

---

### User Story 3 - Find a narrative function by its authored name (Priority: P2)

An author or an agent skill wants the same name-based retrieval for
`G10_Narrative_Function` nodes (e.g. a Propp-style function name), since functions
also carry an authored `name`.

**Why this priority**: A natural, low-cost symmetry extension of US1 using the
identical two-triple label pattern. Lower priority because the dogfooding gap was
measured on units (beats); functions are the secondary content axis.

**Independent Test**: Build a graph containing at least one narrative function, then
query functions by `rdfs:label`; assert the function URI is returned.

**Acceptance Scenarios**:

1. **Given** a fiche whose `functions:` introduces "Interdicción", **When** the graph
   is built, **Then** the minted `G10_Narrative_Function` node carries an `rdfs:label`
   literal equal to that authored name.
2. **Given** a function name introduced by several fiches (deduplicated by slug),
   **When** the graph is built, **Then** the shared node carries exactly one
   `rdfs:label` (no duplicate label triples).

---

### Edge Cases

- **Unit in no sequence**: a unit with no `sequence:` key gets an `rdfs:label` but no
  membership ordinal (there is no membership to order). It remains discoverable by
  name and is unaffected by the ordering mechanism.
- **Single-unit sequence**: the lone member still receives a well-defined ordinal
  (the first/only position); the order query returns one row.
- **Missing `order:` on a member**: sorts last among its sequence's members, by slug,
  exactly as today's assembly does — the materialized ordinal reflects that resolved
  position.
- **Duplicate `order:` within a sequence**: tie-broken by slug, producing a strict
  total order so the ordinal is unambiguous and builds are reproducible.
- **`order:` without `sequence:`**: remains the existing soft warning; no ordinal is
  emitted (there is no membership). Authoring behavior is unchanged.
- **Empty / absent `outline/units/`**: graph is byte-identical to today (no units, no
  labels, no ordinals).
- **Name with accents/punctuation/leading-trailing spaces as authored**: the label is
  the authored `name` verbatim (the slug, used only for identity, is unchanged).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every `G9_Narrative_Unit` MUST emit an `rdfs:label` literal carrying its
  authored `name` verbatim, following the **single `rdfs:label` triple** shape
  `CharacterRole` (`feature.py:169`) and the free-text `CharacterFeature`
  (`feature.py:140`) already emit — `(uri, rdfs:label, Literal(name))`, no new
  mechanism invented. (This is the one-triple label pattern, distinct from the
  two-triple `crm:P2_has_type` + `rdf:type` *typing* path used for Propp/Greimas.)
- **FR-002**: Every `G10_Narrative_Function` node MUST emit an `rdfs:label` literal
  carrying its authored `name` verbatim, via the identical single-triple label shape;
  a function deduplicated across fiches by slug MUST carry exactly one label triple
  (the dedup happens once at mint time in `_mint_functions`, so the label rides the
  single minted entity).
- **FR-003**: Each member unit's position within its `G7_Narrative_Sequence` (the
  `dlp:proper-part` membership) MUST be materialized as a **queryable** integer ordinal —
  reachable from the sequence in a single SPARQL hop so members can be `ORDER BY`-ed,
  whether the ordinal is attached to the member unit or to a reified membership node.
- **FR-004**: The materialized ordinal MUST reproduce the total order the existing
  assembly already defines for a sequence's members — ascending by declared `order:`,
  a missing `order:` placed last, ties broken by slug — so that sorting members by the
  ordinal yields the author's declared order and is byte-identical across rebuilds.
- **FR-005**: The feature MUST NOT add any class or predicate to the frozen GOLEM
  ontology — concretely, it adds nothing to `golem.ttl`, nothing to `CLASS_IRI`, and
  nothing to the closure-checked predicate list in `test_namespaces.py` (Principle X).
  The label uses `rdfs:label`, which already sits outside that closure by design (it is
  emitted today and is in neither checked list). The ordinal MUST likewise use a term
  outside the frozen GOLEM closure — either a predicate in Bookwright's own `bw:`
  namespace (the same place `bw:reference` etc. live, declared in a `resources/
  vocabularies/*.ttl`, never in `golem.ttl`) or a standard `rdf:`/`rdfs:` ordering term
  — never a newly minted GOLEM class or predicate. The exact predicate is a
  `/speckit-plan` decision; whatever it is, the closure test in `test_namespaces.py`
  MUST stay unmodified and green (SC-005).
- **FR-006**: The label assertions MUST NOT invent a new `crm:E13_Attribute_Assignment`:
  an `rdfs:label` rides the entity's already-emitted identity assertion (which carries
  the unit/function's `file:line` via the existing `DerivedAssertion(uri, uri, None)`),
  exactly as `CharacterRole`/`CharacterFeature` labels do today — adding a dedicated E13
  per label would be unjustified plumbing. The ordinal assertion, when it introduces a
  genuinely new attribution on the assembled sequence, MUST carry file-level provenance
  (no `:line`, since a sequence has no single source line), mirroring how minted
  functions and assembled sequences already record provenance (`key_lines={}`).
- **FR-007**: A SPARQL query MUST be able to find a narrative unit by matching its
  `rdfs:label`; this query ships as a test.
- **FR-008**: A SPARQL query MUST be able to list a sequence's member units in their
  declared order via the materialized ordinal; this query ships as a test.
- **FR-009**: Every other part of the graph MUST continue to emit the same triples it
  emits today; all existing validators — including `narrative_structure`, which cites
  units — MUST stay green.
- **FR-010**: The authoring format MUST remain unchanged: `name`, `functions`, `roles`,
  `sequence`, and `order` keys keep their current meaning and shape.
- **FR-011**: Fixture oracles and E2E expectations whose triple/label counts shift
  because units and functions now carry labels (and memberships carry ordinals) MUST be
  reconciled to the **new** awake totals, read from the freshly built graph — never
  back-fitted to make a stale number pass (the iteration-034 precedent).
- **FR-012**: The DEBT-005 entry MUST be removed from `DEBT.md` (git retains history),
  per the project's debt-resolution convention.
- **FR-013**: The graph MUST remain a fully derived cache, reconstructible from the
  plain-text `outline/` sources (Principle I) — no authored state moves into the graph.

### Key Entities *(include if feature involves data)*

- **Narrative Unit (`G9_Narrative_Unit`)**: a story beat ingested from an
  `outline/units/` fiche. Identity is its name-derived slug; gains a human-readable
  `rdfs:label` carrying the authored `name`.
- **Narrative Function (`G10_Narrative_Function`)**: a minted, slug-deduplicated
  function node referred to by units; gains a single `rdfs:label` carrying its name.
- **Narrative Sequence (`G7_Narrative_Sequence`)**: a story-line assembled from units
  sharing a `sequence:` name; its `dlp:proper-part` memberships now carry a queryable
  ordinal reflecting each member's declared `order:`.
- **Sequence membership ordinal**: the integer position of a unit within its sequence,
  materialized so SPARQL can `ORDER BY` it; not a new ontology class — a queryable shape
  over existing/permitted terms.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of ingested narrative units expose their authored name through a
  graph query — a name-to-unit query that returned 0 rows before now returns the
  matching unit.
- **SC-002**: For any sequence, a single graph query returns its member units in the
  author's declared order with 100% positional fidelity, including when `order:` values
  have gaps, are missing, or duplicate.
- **SC-003**: Two demonstrative queries — one resolving a unit by name, one listing a
  sequence in order — pass as automated tests, proving both recall axes the dogfooding
  exercise measured as broken.
- **SC-004**: Zero regression: the rest of the graph is unchanged, every existing
  validator stays green, the full test suite passes, and all four gates (`ruff check`,
  `ruff format --check`, `mypy --strict`, `pytest` ≥ 80% coverage) are green.
- **SC-005**: The frozen ontology gains no class and no property; the term-closure test
  still holds (Principle X intact).
- **SC-006**: Graph rebuilds are deterministic — the same `outline/` sources produce a
  byte-identical graph, including labels and ordinals, across runs.

## Assumptions

- **Ordinal = derived dense rank of the resolved total order, not the raw `order:`
  value.** The existing assembly already collapses gaps, missing values, and duplicate
  `order:` keys into one strict total order (ascending by `order:`, missing last, ties
  by slug — design § 7.4). Materializing that resolved rank (rather than the authored
  integers) is what makes "list in declared order" unambiguous and `ORDER BY`-clean; it
  faithfully "reflects the declared order" because it *is* the order the declaration
  resolves to. The exact base (0- vs 1-indexed) and the literal datatype are left to
  `/speckit-plan`. *(Open to confirmation in `/speckit-clarify`.)*
- **The concrete ordinal mechanism is a planning decision.** The spec requires only a
  queryable integer ordinal under Principle X. Because a unit declares **at most one**
  `sequence:` (single optional key, `outline.py:195-206`), its membership is unique, so
  a per-unit ordinal predicate (e.g. `?unit <bw:order> ?n`) and a reified-membership
  node are both viable; the choice — and the predicate term, base index, and literal
  datatype — is made and justified against Principle X in `/speckit-plan` (per the
  implementation-plan risk note for iteration 035; splitting into separate label/order
  tasks is permitted if tasks inflate beyond ~10).
- **G10 functions get labels too.** The user's "si encaja / si aplica" is read as
  *yes*: functions are slugged entities with an authored `name`, so the identical
  single-`rdfs:label`-triple pattern applies cleanly; included as P2.
- **Provenance for assembled-sequence ordinals is file-level**, mirroring the existing
  file-level provenance of minted functions and assembled sequences (no `:line`, since
  a sequence has no single source line).
- **Reference fixtures already exercise this surface**: the `tiny-quest` fixture (and
  its oracle) plus the narrative-workflow E2E include units/functions/sequences; their
  expected counts are reconciled to the awakened label/ordinal totals (FR-011).
- **Out of scope (must not be reopened in clarify)**: vector search / ChromaDB (the
  demand-pulled horizon); any new class or property in `golem.ttl`; changing the
  authoring format; the other dogfooding findings DEBT-004 (closed) and DEBT-006.
