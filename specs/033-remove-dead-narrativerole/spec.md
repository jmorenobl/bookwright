# Feature Specification: Remove dead `NarrativeRole` concept + harden ingestion-parity

**Feature Branch**: `033-remove-dead-narrativerole`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Necesidad: el concepto GOLEM de nivel superior `NarrativeRole` … es código muerto inalcanzable por diseño … Queremos eliminar `NarrativeRole` de CONCEPTS y endurecer el contrato de paridad para que un concepto muerto que comparta IRI con un carrier no pueda volver a colarse, SIN perder ninguna información … Resultado esperado: 12 conceptos, paridad honesta, cero regresión en los triples del grafo, DEBT-001 cerrada."

## Context (the defect being closed)

The top-level GOLEM concept `NarrativeRole` (`golem/modules/narrative.py`, registered in
`CONCEPTS`) is **dead code, unreachable by design**: no builder instantiates it and no
authoring path can mint it. The *only* real materialization of the RDF class
`golem:G11_Narrative_Role` is the inlined node `CharacterRole`
(`golem/modules/feature.py`, deliberately **outside** `CONCEPTS`), produced from
`narrative_roles:` in `bible/characters/*.md`. Outline `roles:` resolve by slug against
that character index and never mint (`outline.py` `_resolve_roles`, design § 7.4).

Because `CharacterRole` and `NarrativeRole` share `CLASS_IRI["NarrativeRole"]`, the
ingestion-parity test observes class **G11 materialized** in the built graph and therefore
counts `NarrativeRole` as *reachable* — so it never appears in `DEFERRED_CONCEPTS`. A dead
concept thus escapes the deferral contract by **IRI collision with a live carrier**
(recorded as **DEBT-001**). The design defines G11 as *"rol de un personaje"*
(`bookwright-design.md` line 1603) and does not conceive of character-independent roles, so
removing the dead concept loses **no** capability: G11 stays alive and materialized via
`CharacterRole`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The concept registry is honest (Priority: P1)

A maintainer (or the `bookwright-quality` workflow) reading `CONCEPTS` and the deferral
registry must find that every listed concept is either materialized by a real builder or
explicitly deferred — with no third, undocumented category of "dead but counted reachable
by IRI accident".

**Why this priority**: This is the core defect. Until the dead concept is gone, the concept
surface lies about what the system can author, and the deferral contract has a silent hole.

**Independent Test**: Inspect `CONCEPTS` — it contains exactly twelve concepts and
`NarrativeRole` is absent; the package still imports and every gate stays green.

**Acceptance Scenarios**:

1. **Given** the GOLEM package, **When** `CONCEPTS` is enumerated, **Then** it contains
   exactly twelve entries and `"NarrativeRole"` is not among them.
2. **Given** the public package surface, **When** `bookwright.golem.__all__` is read,
   **Then** `"NarrativeRole"` is absent and no import of it remains.
3. **Given** the source code and docstrings that counted "thirteen concepts"
   (`golem/__init__.py`, `golem/deferrals.py`), **When** they are read after the change,
   **Then** they say "twelve" and describe the registry accurately.

---

### User Story 2 - No information or capability is lost (Priority: P1)

Removing the dead concept must not drop a single triple from any built graph and must not
touch the frozen ontology. G11 remains a first-class frozen class, still emitted by
`CharacterRole` exactly as before.

**Why this priority**: The whole justification for the deletion is that it is information-
preserving. A regression in the graph or the ontology would invalidate the change.

**Independent Test**: Build the graph for every fixture before and after the change; the
emitted triples (including all `golem:G11_Narrative_Role` typings produced by character
roles) are identical.

**Acceptance Scenarios**:

1. **Given** any fixture with `narrative_roles:` on a character, **When** its graph is
   built after the change, **Then** the `golem:G11_Narrative_Role` triples are byte-for-byte
   identical to the pre-change build.
2. **Given** the frozen ontology, **When** `CLASS_IRI` is enumerated after the change,
   **Then** it still holds all 17 class IRIs — including `golem:G11_Narrative_Role` — and
   `golem.ttl` is unchanged (Principle X / Constitution X).
3. **Given** outline `roles:` referencing characters, **When** an outline is ingested after
   the change, **Then** role resolution behaves exactly as before (resolves by slug against
   the character index, never mints).

---

### User Story 3 - A dead concept cannot re-enter via carrier IRI collision (Priority: P1)

The ingestion-parity contract must be hardened so that re-introducing a dead concept that
shares its class IRI with a non-`CONCEPTS` carrier is **caught** rather than silently
counted reachable — permanently closing the DEBT-001 class of defect.

**Why this priority**: Deleting the one known instance without closing the loophole would
let the same mistake recur. The hardened contract is what makes the fix durable.

**Independent Test**: With the hardened parity test in place, a simulated re-introduction of
a carrier-only-IRI concept into a local copy of the registry is named as a parity failure.

**Acceptance Scenarios**:

1. **Given** the hardened parity contract, **When** the graph is built and `G11` is observed
   as materialized, **Then** the contract recognizes `CharacterRole` as the legitimate sole
   carrier of `golem:G11_Narrative_Role` *outside* `CONCEPTS`, and does **not** attribute
   that IRI to any `CONCEPTS` member.
2. **Given** a (simulated) `CONCEPTS` member whose class IRI is materialized only by a
   non-`CONCEPTS` carrier, **When** parity is evaluated, **Then** the contract reports a
   failure that names the offending concept (the DEBT-001 pattern is detected).
3. **Given** the deferral registry after the change, **When** parity is checked against a
   real build, **Then** the orphan set still equals exactly `{RelationshipRole,
   PsychologicalState}` and the reachable set is observed from the graph, never hand-listed.

---

### User Story 4 - The debt ledger reflects reality (Priority: P2)

Once the defect is fixed, its `DEBT.md` entry (DEBT-001) must be removed so the plain-text
ledger records only open debt (git preserves the history).

**Why this priority**: The doctrine (DEBT.md preamble) is that a resolved debt entry is
deleted, not archived. Leaving it would make the ledger lie and cause the workflow to
re-detect it.

**Independent Test**: Read `DEBT.md` after the change — DEBT-001 is gone and no other entry
references the `NarrativeRole` dead-concept gap.

**Acceptance Scenarios**:

1. **Given** `DEBT.md`, **When** it is read after the change, **Then** the `### DEBT-001 …`
   block is absent and the "Deuda abierta" section reflects the new state.

---

### Edge Cases

- **G11 IRI still present but no concept owns it**: after removal, `CLASS_IRI["NarrativeRole"]`
  is materialized (by `CharacterRole`) yet maps to no `CONCEPTS` member. The parity contract
  must treat this as correct (a carrier-only IRI), not as a leaked orphan or a missing
  concept.
- **Tests that import the deleted class**: `tests/golem/test_triples.py` and
  `tests/golem/test_uri.py` import and instantiate `NarrativeRole`; these must stop
  exercising the dead class while keeping G11's triple/URI behavior covered through its real
  carrier (`CharacterRole`), so coverage does not silently drop.
- **`CLASS_IRI`-closure test conflation**: `tests/golem/test_namespaces.py` pins the 17-class
  ontology and labels G11 as "pinned in the CONCEPTS registry". After the change G11's IRI
  stays in the 17-class closure but is no longer a `CONCEPTS` member; the test/prose must be
  reconciled without changing the frozen count (still 17).
- **Slugged-concept count**: `test_uri.py` enumerates "12 slugged concepts"; after removal it
  is 11 slugged concepts (CONCEPTS is 12 total, one of which — `AttributeAssignment` — is not
  slugged).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST remove the `NarrativeRole` class from
  `src/bookwright/golem/modules/narrative.py`.
- **FR-002**: The system MUST remove every reference to `NarrativeRole` from the GOLEM public
  surface in `src/bookwright/golem/__init__.py`: its import, its `CONCEPTS` entry, and its
  `__all__` entry. After the change `CONCEPTS` MUST contain exactly twelve concepts.
- **FR-003**: The system MUST update every source docstring/comment that states the registry
  holds "thirteen concepts" (at least `golem/__init__.py` and `golem/deferrals.py`) to state
  "twelve" and to describe the registry accurately.
- **FR-004**: The RDF class `golem:G11_Narrative_Role` MUST remain in the frozen ontology:
  `CLASS_IRI` MUST still hold all 17 class IRIs (including `NarrativeRole`'s IRI) and
  `golem.ttl` MUST NOT change (Constitution X / Principle X). The deletion is of the *Python
  concept*, not the *RDF class*.
- **FR-005**: `CharacterRole` MUST remain the materializing carrier of
  `golem:G11_Narrative_Role`, unchanged. Building the graph for any fixture MUST produce the
  same G11 triples as before the change (zero triple regression).
- **FR-006**: The ingestion-parity contract (`tests/golem/test_ingestion_parity.py`) MUST be
  hardened so that a `CONCEPTS` member whose class IRI is materialized **only** by a
  non-`CONCEPTS` carrier (the DEBT-001 collision pattern) is reported as a parity failure
  naming the offending concept. It MUST recognize `CharacterRole` as the legitimate carrier
  of G11 outside `CONCEPTS`.
- **FR-007**: After the change, the parity test's pinned reachable set MUST drop
  `NarrativeRole` (ten reachable concepts), the orphan/deferred set MUST remain exactly
  `{RelationshipRole, PsychologicalState}`, and the reachable set MUST continue to be
  observed from a real graph build rather than hand-listed.
- **FR-008**: All tests that import, instantiate, or pin `NarrativeRole` — at minimum
  `tests/golem/test_triples.py`, `tests/golem/test_uri.py`, and `tests/golem/test_namespaces.py`
  — MUST be updated so they no longer exercise the deleted class, while G11's triple and URI
  behavior stays covered through its real carrier (`CharacterRole`). Concept/segment counts in
  those tests and their comments MUST be reconciled (e.g. "12 slugged concepts" → 11).
- **FR-009**: The `### DEBT-001 …` entry MUST be removed from `DEBT.md` (no archival section;
  git retains history), and any cross-reference to it in tracked plain-text MUST be reconciled.
- **FR-010**: The change MUST NOT alter the deferral registry's two entries (G6
  `RelationshipRole`, G3 `PsychologicalState`) nor their `demand-pulled` targets; the G6/G3
  deferrals are out of scope.
- **FR-011**: All four CI gates (`ruff check`, `ruff format --check`, `mypy --strict`,
  `pytest` with ≥ 80 % coverage) MUST pass after the change.

### Key Entities *(include if feature involves data)*

- **`NarrativeRole` (Python concept, being removed)**: a top-level GOLEM concept class in
  `CONCEPTS` with no builder and no authoring path — dead code. Subject of deletion.
- **`golem:G11_Narrative_Role` (RDF class, preserved)**: a frozen ontology class. Survives
  unchanged; remains in `CLASS_IRI` and `golem.ttl`.
- **`CharacterRole` (carrier, preserved)**: the inlined, character-scoped node (outside
  `CONCEPTS`) that is the sole real materialization of `golem:G11_Narrative_Role`.
- **`CONCEPTS` (registry)**: the concept name → class map; shrinks from thirteen to twelve.
- **`DEFERRED_CONCEPTS` (deferral registry)**: unchanged — exactly `{RelationshipRole,
  PsychologicalState}`, both `demand-pulled`.
- **DEBT-001 (debt ledger entry)**: the recorded defect; removed when the fix lands.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `CONCEPTS` contains exactly **12** concepts and `NarrativeRole` is absent from
  `CONCEPTS`, `__all__`, and all GOLEM imports.
- **SC-002**: Building the graph over every fixture yields the **same** triples as before the
  change — in particular, every `golem:G11_Narrative_Role` triple is preserved (zero
  regression).
- **SC-003**: The frozen ontology is unchanged: `CLASS_IRI` still holds **17** class IRIs
  (including G11) and `golem.ttl` has no diff.
- **SC-004**: The ingestion-parity contract **fails** (naming the concept) when a concept
  whose class IRI is carried only by a non-`CONCEPTS` carrier is added to a local copy of the
  registry — i.e. the DEBT-001 loophole is provably closed — while passing for the real
  registry whose orphan set equals `{RelationshipRole, PsychologicalState}`.
- **SC-005**: `DEBT.md` no longer contains DEBT-001.
- **SC-006**: All four gates pass (ruff check, ruff format --check, mypy --strict, pytest
  ≥ 80 % coverage).

## Assumptions

- G11 is, per design line 1603, *"rol de un personaje"*; the design does not call for
  character-independent narrative roles, so deleting the dead concept removes no authoring,
  auditing, or verification capability. (Owner decision — not reopened in clarify.)
- Historical per-iteration artifacts under `specs/005-golem-domain-model/` are a frozen
  record of a past iteration and are **not** edited by this change; only live source, tests,
  and the debt ledger are touched.
- The `parity-exercise` fixture and its `narrative_roles:` authoring continue to materialize
  G11 via `CharacterRole`, providing the live observation the hardened parity test needs.

## Out of Scope *(owner decision — do NOT reopen in clarify)*

- Giving `NarrativeRole` its own authoring surface (e.g. `outline/roles/*.md`) — **rejected**:
  it would fabricate a capability the design does not request and introduce a second source of
  truth for G11.
- Touching the G6 (`RelationshipRole`) / G3 (`PsychologicalState`) deferrals.
- Any change to the frozen ontology — the RDF class `golem:G11_Narrative_Role` and
  `golem.ttl` MUST NOT change (Principle X).
