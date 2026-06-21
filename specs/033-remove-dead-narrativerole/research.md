# Phase 0 — Research: Remove dead `NarrativeRole` + harden parity

This is a structural-cleanup iteration of a *known, recorded* defect (DEBT-001).
The technical context carries **no NEEDS CLARIFICATION** — the design and the
spec already settle every question. The "research" here is therefore the set of
decisions that make the cleanup safe and complete, each with its rationale and
the alternatives rejected.

## D1 — The deletion is of the Python concept, not the RDF class

**Decision**: Remove the `NarrativeRole` Pydantic class from
`golem/modules/narrative.py` and its three references in `golem/__init__.py`
(import, `CONCEPTS` entry, `__all__` entry). Leave `CLASS_IRI["NarrativeRole"]`
(in `golem/namespaces.py`), `golem.ttl`, and the 17-IRI closure untouched.

**Rationale**: `golem:G11_Narrative_Role` is a frozen ontology class
(Constitution X). The defect is a *dead Python concept*, not a dead RDF class —
G11 is alive, materialized by `CharacterRole`. Design line 1603 defines G11 as
"rol de un personaje"; the design conceives of no character-independent role, so
the concept carries no capability. Deleting it loses nothing.

**Alternatives rejected**:
- *Give `NarrativeRole` its own authoring surface* (`outline/roles/*.md`) —
  rejected by the spec (Out of Scope): it fabricates a capability the design
  doesn't request and creates a second source of truth for G11.
- *Leave it and just document the collision* — rejected: that is exactly
  DEBT-001's "abierta" state; the concept surface keeps lying about what the
  system can author.

## D2 — Zero triple regression is structural, not a measurement

**Decision**: Rely on the fact that no builder ever instantiated `NarrativeRole`
(no `map_*` / outline path references it; `outline.py` `_resolve_roles` resolves
by slug against the character index and mints nothing — design § 7.4). The only
producer of G11 triples is `CharacterRole`, which is untouched.

**Rationale**: Because the deleted class is unreachable, removing it cannot drop
a triple from any build. Equivalence is therefore by construction. The parity
test's real-build assertion (`test_ingestion_parity_holds`) and
`test_character_attributes.py` (G11 typing via `CharacterRole`) jointly *observe*
that G11 still materializes after the change — the proof, not the mechanism.

**Alternatives rejected**: a bespoke before/after triple-diff fixture — rejected
as redundant: the existing real-build parity test already observes G11 from a
live graph, and `quickstart.md` documents the manual diff for human assurance.

## D3 — Hardening the parity contract: carrier-IRI collision detection

**Decision**: After removal, `"NarrativeRole"` becomes a `CLASS_IRI` key with
**no** `CONCEPTS` member — a *carrier-only IRI*, joining the existing
`CARRIER_NAMES` (`CharacterFeature`, `Dimension`, `Type`, `TimeInterval`),
materialized solely by `CharacterRole`. Add a pure helper
`carrier_iri_collisions(concepts)` that returns every concept whose class IRI
equals a carrier-only IRI, an invariant test asserting it is empty for the real
registry, and a drift simulation that re-adds `"NarrativeRole"` to a *local copy*
of the concept set and asserts the helper names it.

**Rationale**: The root cause of DEBT-001 was that `_reachable` counts a concept
"alive" whenever its `CLASS_IRI` appears in the built graph — it cannot tell a
concept that materializes *itself* from one whose IRI is materialized only by a
same-IRI carrier. Asserting `concept-class-IRIs ∩ carrier-class-IRIs = ∅` closes
that hole *by construction*: re-introducing any `NarrativeRole`-like concept
mapped to a carrier IRI is named as a failure, not silently counted reachable.

**Alternatives rejected**:
- *Track per-builder provenance of each type IRI* — rejected as over-engineering:
  the disjointness invariant is sufficient, pure, and needs no plumbing.
- *Just delete the concept and lower the reachable count* — rejected: it fixes
  the one instance but leaves the loophole open, so the same mistake recurs
  (User Story 3 / FR-006 require durability).

## D4 — Coverage relocation, not coverage loss

**Decision**: Move the G11 triple/URI coverage that `test_triples.py` and
`test_uri.py` get today from instantiating `NarrativeRole` onto its real carrier:
G11 type emission is already asserted in
`tests/golem/test_character_attributes.py:50`
(`(role, RDF.type, ns.CLASS_IRI["NarrativeRole"]) in triples`), and the
`/role/{slug}` URI segment in
`test_uri.py::test_character_scoped_node_uri_patterns`. In `test_triples.py`,
keep `NarrativeUnit.roles` cross-ref coverage by passing a **bare `URIRef`** role
member (the model already accepts bare URIRefs —
`test_cross_reference_accepts_bare_uriref`), so removing the dead class drops no
assertion.

**Rationale**: Principle VIII forbids a silent coverage drop. The carrier already
carries every behaviour the dead class was standing in for, so the relocation is
real, not nominal.

**Alternatives rejected**: deleting the `NarrativeUnit(..., roles=...)` coverage
outright — rejected: it would silently drop the units→roles cross-ref assertion.

## D5 — The "thirteen → twelve" sweep is a debt *class*, swept whole

**Decision**: Reconcile **every** live "thirteen concepts" / "Eleven of the
thirteen" occurrence in source and tests in one pass: `golem/__init__.py`
("thirteen GOLEM concept classes" → "twelve"), `golem/deferrals.py` ("Two of the
thirteen" → "Two of the twelve"), `test_ingestion_parity.py` module docstring +
inline comments ("Eleven of the thirteen" → "Ten of the twelve"; "the eleven
concepts" → "the ten concepts"), `test_namespaces.py` (test name + "13 narrative
concepts" docstring), `test_uri.py` ("12 slugged concepts" → "11"). Leave the
**historical** "thirteen `CONCEPTS`" note in `CHANGELOG.md` untouched.

**Rationale**: Doctrine §4 — debt of the same class the iteration touches is
swept in full, not a cited subset. The CHANGELOG note was true at its v0.3.1
release; Principle I forbids rewriting released history.

**Alternatives rejected**: fixing only the cited files — rejected as a partial
sweep that re-seeds the same lie elsewhere.

## D6 — Ledger + roadmap reconciliation

**Decision**: Remove the entire `### DEBT-001 …` block from `DEBT.md` (the
"Deuda abierta" section returns to an empty state, matching the ledger doctrine:
resolved debt is deleted, not archived — git keeps history). Remove the
`bookwright-roadmap.md` §4 "Decisión estructural sobre `NarrativeRole`
(DEBT-001)" item, whose open decision is now made. **Keep** the roadmap's G11
status row (line 112: "G11 ✅ inline vía `narrative_roles:`") — it stays accurate
because G11 is still materialized via `CharacterRole`.

**Rationale**: FR-009 + the DEBT.md preamble. A resolved entry left in place
makes the ledger lie and causes the `bookwright-quality` workflow to re-detect
the debt on every pass.

**Alternatives rejected**: moving DEBT-001 to an "aceptada / resuelta" section —
rejected: the ledger has no archival section by design (it would duplicate git).

## D7 — Frozen-ontology test reclassification, never count-lowering

**Decision**: In `test_namespaces.py`, rename
`test_class_iri_maps_thirteen_concepts_plus_attribute_carriers` and move
`"NarrativeRole"` from the local `concepts` set into the `carriers` set, so the
assertion becomes `12 concepts + 5 carriers == 17` — the frozen 17 preserved.

**Rationale**: Edge case in the spec — G11's IRI stays in the 17-IRI closure but
is no longer a `CONCEPTS` member. The honest move is to reclassify the bucket,
not lower the closure count or delete the assertion (that would weaken the
Principle X backstop).

**Alternatives rejected**: asserting `… == 16` — rejected: it would falsely
claim the ontology shrank; the ontology is frozen and unchanged.
