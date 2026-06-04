# Feature Specification: Historical fixture, research E2E flow, and v0.2.0 documentation

**Feature Branch**: `016-research-e2e-docs`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Necesidad: antes de release v0.2.0 necesitamos una fixture realista con investigación, tests E2E del flujo investigar→anclar→validar→verificar, y documentación del nuevo sistema."

## Overview

This is the closing iteration of milestone **M4 / v0.2.0** (the research &
provenance system, design § 20 / § 15.5). The mechanism is already built across
the merged iterations: the Source/Finding/Anchor provenance model, the
`bible/research/` reader, the `[research]` manifest block, the `factual_anchor`
validator, and the `bookwright-research` / `bookwright-verify` skills. What is
missing before the release can ship is **proof and explanation**: a realistic
worked example, an automated regression that walks the whole research flow, an
inertness guarantee for projects that don't research, and a documentation set
that teaches the system. This iteration is consolidation and validation — it
adds no new product mechanism.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A worked historical example with real provenance (Priority: P1)

A novelist (or a maintainer evaluating Bookwright) needs to *see* the research
system working on something realistic, not a toy. They open a packaged example
project: a short historically-set novel whose `bible/research/` holds a genuine
research topic — real dates, real facts, real procedures — recorded through the
full provenance chain (Sources with author / original language / type /
reliability / quote, Findings that cite them, and Anchors promoted from those
Findings to constrain narrative entities). The example also deliberately
contains a manuscript chapter with a planted anachronism so the verification
layers have something concrete to catch.

**Why this priority**: Everything else in this iteration consumes this fixture —
the E2E test runs against it and the documentation references it. Without a
coherent, provenance-complete example there is nothing to test or teach, so it
is the foundational deliverable.

**Independent Test**: The fixture can be initialized/loaded as a valid Bookwright
project and its research files parse into Source/Finding/Anchor entities; it
delivers value as a standalone, readable demonstration of provenance-first
research even before any test or doc is written.

**Acceptance Scenarios**:

1. **Given** the `tiny-historical` example project, **When** a reader opens
   `bible/research/`, **Then** they find at least one research topic file, a
   Source registry with several Sources each carrying complete provenance
   (author, original language, type from the controlled vocabulary, reliability
   with justification, access date, original-language quote), and several
   Anchors that link to narrative entities.
2. **Given** the same project, **When** the graph is built from it, **Then** the
   build succeeds and the research entities are emitted into the derived graph
   alongside the characters, settings, and events.
3. **Given** the manuscript chapter, **When** a reader inspects it against the
   recorded anchors, **Then** it contains at least one unambiguous,
   deterministically-detectable anachronism that contradicts a dated anchor.

---

### User Story 2 - The research flow proven end to end (Priority: P1)

A maintainer preparing the release needs confidence that the four research
stages — build → query → validate → verify — actually compose on a real project,
and that this stays true as the code evolves. An automated regression walks the
historical example through the deterministic stages and asserts each one
behaves: the graph builds with the research triples, a query retrieves the
anchors, and the `factual_anchor` validator reports exactly the planted
structural defect and the planted hard time-span anachronism. The semantic
verify layer (`bookwright-verify`) is an LLM skill and is exercised as a
documented manual step whose deterministic inputs (retrievable anchors,
materialized skill, the anachronistic chapter) the regression confirms are in
place.

**Why this priority**: A worked example that isn't guarded by a test rots
silently. This regression is what lets the team claim "the research flow works"
at release and keep claiming it afterward; it is co-equal P1 with the fixture it
depends on.

**Independent Test**: Running the workflow test against the fixture exercises the
build/query/validate chain and asserts the expected findings, delivering a
green-or-red signal on the whole deterministic research flow in one run.

**Acceptance Scenarios**:

1. **Given** the `tiny-historical` project, **When** the graph is built, **Then**
   the build succeeds and produces a derived graph containing the research
   entities.
2. **Given** the built graph, **When** a query for anchors constraining a given
   narrative entity runs, **Then** it returns the expected anchors with their
   claims.
3. **Given** the built graph, **When** validation runs with `factual_anchor`
   active, **Then** it reports the planted structurally-malformed anchor as a
   warning and the planted time-span anachronism as an error, and reports no
   other unexpected research violations.
4. **Given** the materialized `bookwright-verify` skill and the anachronistic
   chapter, **When** the documented manual verification procedure is followed,
   **Then** the produced report flags the planted manuscript anachronism — and
   the regression confirms the inputs that procedure needs (queryable anchors,
   the skill present in the project) exist.

---

### User Story 3 - The system is inert when unused (Priority: P2)

An author who does not research at all — no `[research]` manifest block (or it is
disabled) and no `bible/research/` directory — must be able to build, query, and
validate their project exactly as they could before the research system existed.
The research machinery imposes zero cost, zero new required files, and zero
behavioral change on projects that never opt in.

**Why this priority**: This is the non-regression guarantee for the entire
existing v0.1 user base. It protects the milestone's core promise (§ 20.9:
"un proyecto que no investigue no pague coste alguno"); it is high-value but
ranks just below the worked-example/E2E pair because it guards existing behavior
rather than demonstrating the new one.

**Independent Test**: Running build → validate against an existing
research-free fixture (e.g. `tiny-novel`) and against a project whose
`[research]` block is disabled yields identical, unchanged results with no
research entities and no `factual_anchor` findings — provable on its own.

**Acceptance Scenarios**:

1. **Given** a project with no `bible/research/` directory, **When** the graph is
   built, **Then** the build succeeds with zero research entities and no error or
   warning about the missing directory.
2. **Given** a project with `[research].enabled = false`, **When** validation
   runs, **Then** `factual_anchor` produces no findings and overall validation
   behaves identically to a v0.1 project.
3. **Given** a research-free project, **When** the full build/query/validate flow
   runs, **Then** its outcome is unchanged from before this milestone (no new
   required inputs, no altered exit behavior).

---

### User Story 4 - The new system is documented for release (Priority: P2)

A reader of the documentation site needs to understand the research system well
enough to use it: what research means in Bookwright, the Source/Finding/Anchor
model, the research skill's protocol, how verification works across the two
layers (deterministic validator + LLM skill), and how multilingualism and
provenance are handled. The command and validation reference pages must cover the
new surface, and the changelog must record the v0.2.0 release.

**Why this priority**: A shipped system nobody can learn is half-shipped, but the
mechanism and its tests must exist first; documentation is the final layer over a
proven system, hence P2 alongside inertness.

**Independent Test**: Building the documentation site produces a navigable
research page plus updated command/validation reference and a v0.2.0 changelog
entry, with no build warnings — verifiable by building the docs and reading them.

**Acceptance Scenarios**:

1. **Given** the documentation site, **When** a reader opens the research page,
   **Then** it explains the purpose of research, the Source/Finding/Anchor model,
   the research skill protocol, the two-layer verification, and multilingualism
   and provenance, and it is reachable from the site navigation.
2. **Given** the command reference, **When** a reader looks for the new authoring
   surface, **Then** `bookwright-research` and `bookwright-verify` are documented
   there, and the validation reference documents `factual_anchor`.
3. **Given** the changelog, **When** a reader looks for the latest release,
   **Then** there is a v0.2.0 entry describing the research and verification
   system.
4. **Given** the documentation sources, **When** the site is built, **Then** the
   build completes with no warnings.

---

### Edge Cases

- **A defect that aborts the build vs. a defect the validator catches.** The
  research reader's fault model is strict: a missing required Source facet or
  malformed front-matter aborts the build entirely. The planted "malformed
  anchor" must therefore be malformed at the *validation* level (e.g. an anchor
  promoted from a finding lacking a sufficiently-reliable source), not at the
  *parse* level — otherwise the graph never builds and the later stages can't
  run. The fixture must keep these two failure modes distinct.
- **A fixture that is both "realistic/coherent" and "contains planted defects."**
  The example must read as a genuine documented novel while still carrying
  exactly the defects the test asserts on; the planted anachronism and malformed
  anchor must be the *only* research violations, so the test can assert an exact
  count rather than a lower bound.
- **`[research]` present but disabled vs. absent entirely.** Both must yield
  inert behavior; the inertness test must cover the disabled-block case as well
  as the no-directory case.
- **Reliability threshold interplay.** Whether a borderline anchor is flagged
  depends on the project's `min_reliability_for_anchor`; the fixture's planted
  under-reliable/unsourced anchor must be unambiguous under the fixture's own
  configured threshold so detection is deterministic.

## Requirements *(mandatory)*

### Functional Requirements

**Fixture**

- **FR-001**: The project MUST ship a `tiny-historical` example fixture: a short,
  coherent, historically-set narrative that is a valid Bookwright project
  (initializable/loadable, with the standard bible/outline/manuscript skeleton).
- **FR-002**: The fixture MUST include a populated `bible/research/` with at least
  one research topic, a Source registry holding several Sources, and several
  Anchors.
- **FR-003**: Every Source in the fixture MUST carry complete provenance:
  reference, author, original language, type (from the controlled Source
  vocabulary), reliability with justification, access date, and an
  original-language quote — exercising the multilingual provenance fields.
- **FR-004**: At least one Anchor in the fixture MUST carry a temporal reference
  (time-span) so the anachronism detection path is exercised.
- **FR-005**: The fixture's anchors MUST link to real narrative entities
  (character / setting / event / timeline) present in the same project.
- **FR-006**: The fixture MUST contain a manuscript chapter with at least one
  deliberate, unambiguous anachronism that contradicts a dated anchor, suitable
  for the verify layer to detect.
- **FR-007**: The fixture MUST contain exactly one planted structural defect that
  the `factual_anchor` validator flags as a warning (an anchor whose support is
  missing or under-reliable, i.e. parseable but failing structural validation)
  and exactly one planted hard time-span anachronism the validator flags as an
  error; aside from these, the fixture MUST produce no other research
  violations.

**E2E tests**

- **FR-008**: An automated end-to-end test MUST walk the historical fixture
  through the deterministic stages: build the graph, query it for anchors, and
  run validation.
- **FR-009**: The E2E test MUST assert the graph build succeeds and the research
  entities (Sources, Findings, Anchors) are present in the derived graph.
- **FR-010**: The E2E test MUST assert a query retrieves the fixture's anchors
  (including those constraining a specified narrative entity) with their claims.
- **FR-011**: The E2E test MUST assert that `factual_anchor` reports the planted
  malformed anchor (warning) and the planted time-span anachronism (error), and
  reports no other unexpected research findings.
- **FR-012**: The verify (LLM) layer MUST be exercised as a documented **manual**
  verification step against the fixture; the automated test MUST confirm the
  deterministic preconditions that step relies on (the anchors are queryable and
  the `bookwright-verify` skill is materialized in the project).
- **FR-013**: An automated test MUST prove inertness: a project with **no**
  `bible/research/` builds, queries, and validates with zero research entities
  and no research-related findings, behaving identically to a v0.1 project.
- **FR-014**: An automated test MUST prove that a project whose `[research]`
  block is **disabled** (or absent) yields no `factual_anchor` findings and
  unchanged overall validation behavior.

**Documentation**

- **FR-015**: The documentation site MUST gain a research page covering: what
  research is in Bookwright, the Source/Finding/Anchor model, the research skill
  protocol, how verification works (the two layers), and multilingualism and
  provenance.
- **FR-016**: The command reference MUST document `bookwright-research` and
  `bookwright-verify`; the validation reference MUST document `factual_anchor`.
- **FR-017**: The research page MUST be reachable from the documentation site
  navigation.
- **FR-018**: The changelog MUST gain a v0.2.0 entry describing the research and
  verification system.

**Quality gates**

- **FR-019**: The full test suite MUST keep overall coverage above the v0.1
  threshold (≥ 80 %), and the new M4 code MUST be covered above 85 %.
- **FR-020**: Lint, format, type-check (strict), pre-commit, and CI MUST all pass.
- **FR-021**: The documentation site MUST build with no warnings.
- **FR-022**: The fixture and tests MUST NOT introduce vector search or any other
  v0.3+ mechanism; verification reads the research Markdown directly.

### Key Entities *(include if data involved)*

- **`tiny-historical` fixture**: A self-contained example Bookwright project with
  a historical setting, complete bible/outline/manuscript, and a populated
  `bible/research/`. The shared input for the E2E test and the documentation.
- **Source**: A consulted document/testimony with provenance facets (reference,
  author, original language, type, reliability + justification, access date,
  original-language quote). Several appear in the fixture with full provenance.
- **Finding**: A concrete claim about the real world supported by one or more
  Sources. Findings underpin the fixture's anchors.
- **Anchor**: A Finding promoted to a binding constraint linking to a narrative
  entity; at least one carries a time-span. The fixture plants one structurally
  malformed anchor and one with an anachronistic time-span.
- **Research workflow test**: The automated regression walking
  build → query → validate over the fixture and asserting the planted findings,
  plus the inertness assertions for research-free / disabled projects.
- **Research documentation set**: The new research page, the updated
  command/validation reference, and the v0.2.0 changelog entry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can open the `tiny-historical` fixture and find a complete
  provenance chain — at least one topic, several fully-attributed Sources, and
  several Anchors (at least one temporal) linking to narrative entities.
- **SC-002**: The research E2E test passes, asserting all four deterministic
  outcomes: build succeeds with research entities, query retrieves anchors,
  `factual_anchor` reports exactly the planted warning and the planted error, and
  the verify preconditions are present.
- **SC-003**: Running the full build/query/validate flow on a research-free
  project and on a `[research]`-disabled project produces results identical to
  v0.1 behavior, with zero research entities and zero `factual_anchor` findings.
- **SC-004**: A reader can reach the research page from the site navigation and it
  covers all five required topics; `bookwright-research`, `bookwright-verify`, and
  `factual_anchor` each appear in the reference; the changelog has a v0.2.0 entry.
- **SC-005**: Overall test coverage stays ≥ 80 % and new M4 code is ≥ 85 %.
- **SC-006**: Lint, format, strict type-check, pre-commit, and CI are green, and
  the documentation site builds with zero warnings.
- **SC-007**: No vector-search or other v0.3+ capability is introduced by this
  iteration.

## Assumptions

- This is plan iteration 17 (spec directory `016`), the final iteration of
  M4/v0.2.0. It assumes iterations 13–16 (provenance model, research skill,
  `factual_anchor` validator, `bookwright-verify` skill — spec dirs 012–015) are
  already on `main`; in particular the `bookwright-verify` work (spec 015) must
  land before this iteration merges.
- "E2E" here means the deterministic stages (build → query → validate) are
  automated; the `bookwright-verify` LLM stage is, by design (§ 20.6), a
  documented manual verification, since it requires agent/LLM judgment and is not
  deterministically testable in CI. The automated test asserts the manual step's
  preconditions, not the LLM's output.
- The "malformed anchor" the validator catches is malformed at the validation
  layer (e.g. unsourced / under-reliable), not at the parse layer — a
  parse-level defect would abort the build (per the research reader's strict
  fault model) and prevent the rest of the flow from running.
- The fixture follows the existing `tests/fixtures/tiny-*` conventions
  (short-but-coherent, Spanish narrative prose consistent with the other
  fixtures, English identifiers/structure) and the existing E2E test conventions
  (`tests/e2e/`, fixtures-as-input, `tmp_path` where a project is mutated).
- "New M4 code" for the ≥ 85 % coverage target refers to the source code added
  across M4 (research IO, provenance model, `factual_anchor`, research/verify
  skill plumbing) as it stands at release, measured by the existing coverage
  tooling; this iteration mostly adds fixtures/tests/docs rather than new
  `src/` code.
- Documentation prose (the research page, reference pages, narrative parts of the
  changelog) is written in Spanish to match the existing docs site and design
  documents; identifiers and command names stay as-is.
- The fixture's `manifest.toml` configures `[research]` (enabled, source
  languages, `min_reliability_for_anchor`) and activates the `factual_anchor`
  validator and the `sources` vocabulary, so the planted defects are detected
  deterministically under the fixture's own configuration.

## Out of Scope

- Vector search over the research corpus (ChromaDB / semantic retrieval) — that is
  v0.3 (design § 20.12). Verification reads the research Markdown directly.
- Any new product mechanism: this iteration adds a fixture, tests, and docs only;
  it changes no validator logic, no provenance model, and no skill behavior.
- Automating the `bookwright-verify` LLM judgment in CI; it remains a manual,
  documented step.
- Actually publishing/tagging the v0.2.0 release (this iteration makes it
  *ready*; the release action itself is a separate step).
