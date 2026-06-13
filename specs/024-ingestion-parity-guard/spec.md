# Feature Specification: Ingestion-parity guard + deferral registry

**Feature Branch**: `024-ingestion-parity-guard`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "Necesidad: la ontología congelada modela 13 conceptos narrativos (registrados en CONCEPTS y cubiertos por el test de clausura), pero solo ~6 son alcanzables desde texto autoral; los otros 7 están modelados pero ningún builder los alimenta — están 'muertos de cara al autor' sin que nada lo declare. Antes de cablear conceptos uno a uno, queremos un contrato explícito: para cada concepto del cierre, o hay un camino desde texto autoral, o hay una nota de diferimiento (razón + versión objetivo), respaldada por un test que asevere que el conjunto de huérfanos es exactamente el conjunto intencionadamente diferido."

## Overview

The frozen GOLEM ontology models thirteen narrative concepts (registered in the
`CONCEPTS` registry and covered by the closure test, SC-003 of iteration 005).
Only six of them are reachable from authored plain text today (`Character`,
`Setting`, `NarrativeEvent`, `SocialRelationship`, `NarrativeRole`, plus the
structural `AttributeAssignment` provenance carrier). The other seven are
modelled, registered, and frozen — but **no builder feeds them**. They are
"dead to the author," and nothing in the codebase declares that fact. The
silence between *modelled* and *fed* is the technical debt this feature closes.

This iteration introduces an explicit, testable **contract**: for every concept
in the closure, either there is an authored-text ingestion path, or there is a
**deferral note** (a short reason plus a target version). A deterministic
**ingestion-parity test** asserts that the set of concepts that do not
materialize from an exercise fixture (the *real* orphans) is **exactly** the set
declared as intentionally deferred. It also documents — in writing, with no
behavioral change — that `outline/` and `manuscript/` are author-only in v0.3:
the scaffold creates them but the engine does not ingest them.

This is a guard, not a wiring iteration. No orphan concept is wired here; that
work is iterations 025+.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The orphan/deferral contract holds automatically (Priority: P1)

A maintainer needs the gap between "modelled" and "fed" to stop rotting in
silence. Today, a contributor can read `CONCEPTS`, see thirteen narrative
concepts, and have no way to know that seven of them are unreachable from
authored text — nor which version is expected to wire each one. This story
makes the contract machine-checked: every concept is either provably reachable
or explicitly deferred with a reason and a target version, and a test fails the
moment that contract drifts.

**Why this priority**: This is the whole point of the iteration — the explicit
contract plus the test that enforces it. Without it, nothing else delivers
value.

**Independent Test**: Run the ingestion-parity test against the current code and
the exercise fixture. It passes only when the set of concepts NOT materialized
from the fixture equals the declared deferred set, with no concept appearing in
both or neither.

**Acceptance Scenarios**:

1. **Given** the current codebase (six reachable concepts, seven orphans) and a
   complete deferral registry, **When** the ingestion-parity test runs, **Then**
   it passes because the observed orphan set equals the declared deferred set.
2. **Given** a contributor adds a builder that makes a previously-orphan concept
   reachable but forgets to remove it from the deferral registry, **When** the
   ingestion-parity test runs, **Then** it fails and names the concept that is
   now fed yet still declared deferred.
3. **Given** a contributor declares a concept as deferred even though the
   exercise fixture already materializes it, **When** the ingestion-parity test
   runs, **Then** it fails and names the concept that is ingested yet declared
   deferred.
4. **Given** a contributor removes a concept from the deferral registry without
   adding a builder for it (so it becomes an undeclared orphan), **When** the
   ingestion-parity test runs, **Then** it fails and names the concept that is
   orphaned yet undeclared.

---

### User Story 2 - Liveness is observed against reality, not a hand-list (Priority: P1)

The maintainer must trust that "this concept is alive" reflects what the engine
actually produces, not a separately-maintained checklist that can lie. The
proof of liveness is the graph itself: build the GOLEM graph from a fixture that
exercises every current ingestion path, and observe which concept `rdf:type`
IRIs actually appear.

**Why this priority**: A parity test that compares two hand-maintained lists
would be theater. Deriving the "alive" set from a real graph build is what makes
the guard meaningful, so it is co-equal P1 with the contract itself.

**Independent Test**: Build the graph from the exercise fixture, collect the
distinct `rdf:type` values among the closure's concept IRIs, and confirm that
exactly the six expected reachable concepts (and no orphan concept) are present.

**Acceptance Scenarios**:

1. **Given** an exercise fixture that authors at least one character (with
   `narrative_roles` and biographical features), one setting, one timeline
   event, and one relationship, **When** the graph is built and concept types
   are collected, **Then** the reachable set observed is exactly
   {`Character`, `Setting`, `NarrativeEvent`, `SocialRelationship`,
   `NarrativeRole`} plus the `AttributeAssignment` provenance carrier.
2. **Given** the same fixture, **When** concept types are collected, **Then**
   none of the seven orphan concepts (`NarrativeLocation`, `Object`,
   `PsychologicalState`, `RelationshipRole`, `NarrativeUnit`,
   `NarrativeFunction`, `NarrativeSequence`) appears.
3. **Given** the parity test is run twice on the same fixture and registry,
   **When** the verdicts are compared, **Then** they are identical (the test is
   a pure function of the fixture corpus and the deferral registry).

---

### User Story 3 - Author-only directories are documented, not silently inert (Priority: P2)

A contributor reading the manuscript reader (or the docs) must learn that
`outline/` and `manuscript/` are author-only in v0.3 by design: the scaffold
creates them, but the engine does not ingest them. Today this is a legitimate v0
decision that is nowhere stated, so it looks like an oversight.

**Why this priority**: It removes a second, related silence and prevents a
future contributor from "fixing" a non-bug. It is documentation only, with no
behavioral change, so it ranks below the enforced contract.

**Independent Test**: Read the manuscript-reader module and/or the relevant
docs page and confirm a written note states that `outline/` and `manuscript/`
are author-only in v0.3 and not ingested by the engine; confirm no ingestion
behavior changed (the existing presence-check semantics are unchanged).

**Acceptance Scenarios**:

1. **Given** the manuscript-reader source, **When** a contributor reads it,
   **Then** a note explains that `manuscript/` is author-only in v0.3 (presence
   check only, no prose mining) and points to the deferral rationale.
2. **Given** the docs and/or the manuscript-reader source, **When** a
   contributor looks for the status of `outline/`, **Then** a written note
   states that `outline/` is author-only in v0.3 and not ingested by the engine.
3. **Given** the documentation change, **When** the test suite runs, **Then** no
   ingestion behavior has changed (no new directory is read, no new entity is
   materialized).

---

### Edge Cases

- **A concept is both reachable and listed as deferred**: the test must fail
  (covered by US1 scenario 3). The deferred registry and the observed reachable
  set must be disjoint.
- **A concept is neither reachable nor declared deferred** (an undeclared
  orphan): the test must fail (covered by US1 scenario 4).
- **`CharacterFeature` and the non-concept carrier IRIs**: `CLASS_IRI` contains
  entries that are not in `CONCEPTS` (`CharacterFeature`, `Dimension`, `Type`,
  `TimeInterval`). The parity contract is scoped to the `CONCEPTS` registry, so
  these carrier IRIs are out of scope for the orphan/deferred bookkeeping and
  must not appear in the deferred registry nor cause a verdict.
- **A new concept is added to `CONCEPTS`** (future ontology work is frozen, but
  the registry could still gain a `CONCEPTS` entry pointing at an existing
  class): every `CONCEPTS` key must be partitioned — it is either observed
  reachable in the fixture or present in the deferred registry. A `CONCEPTS`
  entry that is in neither must fail the test (this is the same failure mode as
  an undeclared orphan).
- **The fixture under-exercises an existing path** (e.g. omits
  `narrative_roles`, so `NarrativeRole` silently disappears): this would make a
  reachable concept look orphaned and the test would fail, surfacing the
  fixture gap. The fixture MUST exercise every current ingestion path.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a static **deferral registry** — plain
  text/code, unit-testable — with one entry per `CONCEPTS` concept that is not
  reachable from authored text today. Each entry MUST carry a short reason and a
  target version.
- **FR-002**: The deferral registry MUST contain exactly these seven concepts
  with these target versions: `NarrativeLocation` (G13) → `v0.3.x`; `Object`
  (G16) → `v0.3.x`; `NarrativeUnit` (G9), `NarrativeFunction` (G10),
  `NarrativeSequence` (G7) → `v0.4`; `RelationshipRole` (G6) and
  `PsychologicalState` (G3) → "undecided" / "to be decided".
- **FR-003**: The system MUST determine the set of *reachable* concepts by
  **building the GOLEM graph from an exercise fixture** and observing which
  concept-level `rdf:type` IRIs (drawn from the closure) actually appear — never
  by consulting a hand-maintained list of "alive" concepts.
- **FR-004**: The exercise fixture MUST exercise **every** current authored-text
  ingestion path, such that all six reachable concepts (`Character`, `Setting`,
  `NarrativeEvent`, `SocialRelationship`, `NarrativeRole`, and the
  `AttributeAssignment` provenance carrier) materialize.
- **FR-005**: The system MUST provide a deterministic **ingestion-parity test**
  that asserts the set of `CONCEPTS` concepts NOT materialized from the fixture
  (the real orphans) is **exactly** the set declared in the deferral registry —
  no concept in both, none in neither.
- **FR-006**: The ingestion-parity test MUST fail when a concept becomes
  reachable (a builder is added) but is still declared deferred, and the failure
  message MUST identify the offending concept.
- **FR-007**: The ingestion-parity test MUST fail when a concept is declared
  deferred but is actually materialized by the fixture, and the failure message
  MUST identify the offending concept.
- **FR-008**: The ingestion-parity test MUST fail when a `CONCEPTS` concept is
  neither materialized by the fixture nor declared deferred (an undeclared
  orphan), and the failure message MUST identify the offending concept.
- **FR-009**: The parity verdict MUST be a pure function of the fixture corpus
  and the deferral registry: identical inputs yield an identical verdict across
  runs (no nondeterminism, no environment dependence).
- **FR-010**: The parity contract MUST be scoped to the `CONCEPTS` registry.
  `CLASS_IRI` entries that are not `CONCEPTS` concepts (`CharacterFeature`,
  `Dimension`, `Type`, `TimeInterval`) MUST NOT appear in the deferral registry
  and MUST NOT affect the verdict.
- **FR-011**: The system MUST document, in writing, that `outline/` and
  `manuscript/` are **author-only in v0.3** — the scaffold creates them but the
  engine does not ingest them — as a note in the manuscript-reader code and/or
  the docs. This MUST NOT change any ingestion behavior.
- **FR-012**: The deferral registry's entries MUST be reconcilable with the
  roadmap's §3 parity table; when a future iteration wires a concept, removing
  it from the registry MUST be the single edit that keeps the parity test green.

### Out of Scope

- **Wiring any orphan concept** — no builder, no new `bible/` subdirectory, no
  new skill. That is iterations 025+.
- **Touching the frozen ontology** — no class or property is added to the
  closure (Principle X). `CLASS_IRI`, `CONCEPTS`, and `golem.ttl` are unchanged.
- **Any new ingestion of `outline/` or `manuscript/`** — that is v0.4. This
  iteration only *documents* that they are not ingested today.

### Key Entities

- **Deferral registry**: a static, unit-testable mapping from an orphaned
  `CONCEPTS` concept name to a record of (short reason, target version). Seven
  entries today. Plain text/code, no runtime state, no I/O.
- **Concept**: a `CONCEPTS` registry entry (name → frozen GOLEM/CIDOC-CRM class),
  each with a concept-level `rdf:type` IRI drawn from the frozen closure.
- **Exercise fixture**: a minimal authored-text project (bible front-matter)
  that drives every current ingestion path so that all reachable concepts
  materialize when the graph is built.
- **Reachable set**: the concepts whose `rdf:type` IRI is observed in the graph
  built from the exercise fixture (derived, never hand-listed).
- **Orphan set**: `CONCEPTS` concepts minus the reachable set; the contract
  requires this to equal the deferral registry's key set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every one of the thirteen `CONCEPTS` concepts is accounted for by
  exactly one of two states — observed reachable in the fixture graph, or
  present in the deferral registry — with zero concepts in both states and zero
  in neither.
- **SC-002**: The deferral registry has exactly seven entries, each with a
  non-empty reason and a target version, matching the roadmap §3 parity table.
- **SC-003**: The ingestion-parity test passes on the current `main`-equivalent
  code and fails under each of the three drift conditions (newly-fed-but-still-
  deferred; declared-deferred-but-actually-fed; undeclared-orphan), with a
  failure message naming the offending concept.
- **SC-004**: Running the parity test twice on the same fixture and registry
  yields byte-identical verdicts (determinism).
- **SC-005**: A written note stating `outline/` and `manuscript/` are
  author-only in v0.3 (scaffold-created, engine-not-ingested) is present in the
  manuscript-reader code and/or docs, and the full test suite confirms no
  ingestion behavior changed.
- **SC-006**: The four CI gates (`ruff check`, `ruff format --check`,
  `mypy --strict`, `pytest` at ≥80% coverage) remain green, and no class or
  property is added to the frozen closure.

## Assumptions

- **Reachable set is exactly six today**: `Character`, `Setting`,
  `NarrativeEvent`, `SocialRelationship`, `NarrativeRole`, and the structural
  `AttributeAssignment` provenance carrier — matching the roadmap §3 table
  (where `CharacterFeature`/G17 is also alive but is a character-scoped carrier
  excluded from `CONCEPTS`, hence outside the parity contract's concept set).
- **`NarrativeRole` counts as reachable** because it materializes inline via a
  character's `narrative_roles:` front-matter, so the fixture must include at
  least one character with non-empty `narrative_roles`.
- **The parity contract is scoped to `CONCEPTS`**, not the full `CLASS_IRI`
  closure; the carrier IRIs (`CharacterFeature`, `Dimension`, `Type`,
  `TimeInterval`) are deliberately outside it.
- **`RelationshipRole` (G6) and `PsychologicalState` (G3)** are deferred with an
  "undecided / to be decided" target version (the wire-or-formally-defer call is
  iteration 027's, per the plan), not a concrete version.
- **The exercise fixture may reuse or extend an existing test fixture** rather
  than introduce a wholly new corpus, as long as it provably exercises every
  current ingestion path; the graph is a derived cache, reconstructible from the
  fixture's plain text (Constitution I).
- **No new CLI surface, command, or `--json` envelope** is introduced; this is a
  test/registry/documentation iteration with no observable runtime behavior
  change beyond the written notes.
