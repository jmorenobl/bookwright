# Feature Specification: Provenance Model — Source / Finding / Anchor

**Feature Branch**: `012-research-provenance-model`

**Created**: 2026-06-03

**Status**: Draft

**Input**: User description: "Necesidad: la investigación que sostiene un libro (fuentes oficiales, en idioma original, con su fiabilidad) debe poder representarse en el grafo del proyecto, no solo como prosa suelta. Necesitamos un modelo de procedencia con tres entidades —Fuente, Hallazgo y Ancla— que se serialicen en Turtle y se enlacen a las entidades narrativas GOLEM que constriñen. [...] Referencia: ver bookwright-design.md § 20.2, § 20.3, § 20.5, § 20.7, § 20.8 y § 4 (modelo GOLEM, módulo Inference)."

## User Scenarios & Testing *(mandatory)*

This iteration is the **foundation** of the research & verification system
(milestone M4, released as v0.2.0). It turns the documentation that sustains a
book's verisimilitude — official sources, in their original language, with their
reliability — into **first-class data inside the project graph**, rather than
leaving it as loose prose in a single `research.md`. It introduces three
provenance concepts (Source, Finding, Anchor) that serialize to Turtle and link
to the narrative entities they constrain.

It deliberately reuses what GOLEM already provides: the **Inference** module
(`E13_Attribute_Assignment`, for traceability of claims) and the `E55_Type`
pattern (for controlled vocabularies). **No new GOLEM/ontology classes are
created** — only `E13`/`E55` plus Bookwright (`bw:`) properties.

This iteration is **data model + plain-text parsing + graph emission only**. It
does *not* deliver: the `bookwright-research` skill that drives research
(iteration 14), the `factual_anchor` structural validator (iteration 15), the
LLM-based `bookwright-verify` check (iteration 16), or vector search over the
source corpus (v0.3). The agent reads the Markdown directly.

The consumers are the human author who maintains the research files and the
agent (via future Agent Skills) that needs to ask structured questions about
what the manuscript may not contradict.

### User Story 1 - Record sources with full provenance in the graph (Priority: P1)

An author has consulted documents and testimonies — an official register, a
foreign-language archive, an academic paper — and records each as a Source in
the project's research files, with its bibliographic reference or URL, author,
original language, type, reliability (with justification), access date, and the
relevant textual quote (original plus a translation when the original language
differs from the book's). When they build the project graph, each Source becomes
a typed node carrying all of that provenance, queryable like any other entity.

**Why this priority**: Sources are the bedrock of the whole chain — a Finding
with no Source is unsupported, and an Anchor with no Source is just an opinion.
Emitting well-formed, typed Source nodes is the thinnest viable slice that
delivers value on its own: a project's source registry becomes structured,
queryable data.

**Independent Test**: In a fixture project whose `bible/research/` describes one
source, run `bookwright graph build` and assert that `bible/graph.ttl` contains a
Source node typed via the controlled vocabulary, with triples for every
provenance facet (reference/URL, author, original language, type, reliability +
justification, access date, original quote, and translation), addressed by a
`{uri_base}source/{slug}` URI.

**Acceptance Scenarios**:

1. **Given** a research file declaring a source of type `oficial` with
   reliability `alta` and a justification, **When** `graph build` runs, **Then**
   `bible/graph.ttl` contains a Source node typed via `E55_Type` from the source
   vocabulary, carrying its reference, author, original language, access date and
   reliability with justification.
2. **Given** a source whose quote is in a language other than the book's, **When**
   the graph is built, **Then** both the original-language quote and its
   translation are present; **and** when the quote language matches the book's,
   only the original quote is present (no empty translation).
3. **Given** a source whose declared type or reliability value is outside the
   controlled vocabulary, **When** `graph build` runs, **Then** the build fails
   with an explicit error naming the offending value.

---

### User Story 2 - Turn sources into real-world findings linked to the narrative (Priority: P1)

The author distills sources into Findings — concrete claims about the real world
("a private detective in Spain needs a TIP licence"; "in 1943 the Wehrmacht
called X what Y") — each supported by one or more Sources and bearing on the
narrative entity it concerns. A Finding can also stay **open**: an unresolved
question, preserving the classic role of `research.md`. When the graph is built,
each Finding is reified as an `E13_Attribute_Assignment` recording *what* is
claimed, *who* asserts it, *which* entity it bears on, and *with which* sources.

**Why this priority**: A Finding is the unit that connects the real world to the
diegesis. Without it, sources are an inert bibliography. Reifying findings on
`E13` is what makes "research" become "research that participates in the same
graph and queries as characters, settings and events".

**Independent Test**: In a fixture with a research file declaring one finding
that cites a source and bears on a character, build the graph and assert the
finding appears as an `E13_Attribute_Assignment` with its claim, asserter,
target entity and supporting source(s), addressed by a `{uri_base}finding/{uuid}`
URI. Separately assert that a finding flagged *open* is emitted without requiring
a resolved claim/source.

**Acceptance Scenarios**:

1. **Given** a research file with a finding citing two sources and bearing on a
   named character, **When** `graph build` runs, **Then** the graph contains an
   `E13_Attribute_Assignment` linking the claim, its asserter, the character it
   bears on, and both supporting sources.
2. **Given** a finding marked as *open* (an unresolved question), **When** the
   graph is built, **Then** the finding is recorded in a recoverable "open"
   state without failing the build for lacking a resolved claim or source.
3. **Given** Findings and the existing inferred-attribute assertions both reified
   on `E13`, **When** the graph is built, **Then** the two uses are
   distinguishable (by URI segment `finding` vs `assertion` and by `bw:`
   properties) and do not collide.

---

### User Story 3 - Promote findings to anchors that constrain the fiction (Priority: P2)

Not all research is binding — much is colour or context. The author marks which
Findings are **Anchors**: facts the manuscript must not contradict. Each Anchor
links to the narrative entity it constrains (a character, a setting, a narrative
event, or the timeline) and may carry a time-span so that future tooling can
detect anachronisms. Once built, the anchors are queryable: an agent can ask
"which anchors constrain this character, and with what sources?".

**Why this priority**: The Anchor is the payoff — it is the materialization of
the "historical anchors" the design promised. It depends on Sources (US1) and
Findings (US2) existing, so it follows them, but it is the slice that turns
recorded research into an enforceable constraint surface for later validation
and verification iterations.

**Independent Test**: In a fixture with an anchor constraining a given character
(and a second anchor carrying a time-span), build the graph and run a structured
(SPARQL) query that returns every anchor constraining that character together
with its claim and supporting source(s); assert the time-span-bearing anchor
emits its time-span.

**Acceptance Scenarios**:

1. **Given** a finding promoted to an anchor that constrains a named character,
   **When** `graph build` runs, **Then** the graph contains an anchor (URI
   segment `anchor`) linked via `bw:constrains` to that character.
2. **Given** several anchors across the project, **When** a structured query asks
   for the anchors constraining a specific character, **Then** it returns exactly
   those anchors with their claims and supporting sources.
3. **Given** an anchor that carries a time-span, **When** the graph is built,
   **Then** the anchor emits a `P4_has_time-span` (so downstream anachronism
   detection has the data it needs); **and** an anchor without a time-span emits
   none.
4. **Given** an anchor constraining the timeline (rather than a single entity),
   **When** the graph is built, **Then** the constraint link is emitted against
   the timeline target.

---

### Edge Cases

- **No research directory**: a project without `bible/research/` (or with an
  empty one) builds normally and emits zero research triples — projects that do
  not research pay no cost.
- **Open finding with no source**: an unresolved question is valid and must not
  fail the build for lacking sources or a resolved claim.
- **Quote without translation**: when the source's original language equals the
  book's language, no translation is recorded (and its absence is not an error).
- **Slug collision between sources**: two sources whose canonical names slug
  identically are disambiguated by the indexer following the established URI
  convention (§ 4.5); the provenance model does not silently collapse them.
- **Anchor pointing at a missing or wrong-typed narrative entity**: when the target
  name is absent from the bible, the constraint link is **reported as a build warning
  and skipped** (not emitted) and the build still succeeds; *verifying* that an
  existing target is one of the allowed kinds is the `factual_anchor` validator's job
  (iteration 15), not this iteration's.
- **Anchor whose source reliability is below the project threshold**: recorded
  faithfully; enforcing a minimum reliability for promotion is a later concern
  (validator, iteration 15), not a build-time rejection here.
- **Malformed research front-matter** (missing a required Source facet on a
  non-open finding): surfaced as an explicit parse/build error rather than a
  silently dropped triple.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST represent three provenance concepts — Source, Finding,
  Anchor — as nodes in the project graph, reusing only `E13_Attribute_Assignment`
  (reification) and `E55_Type` (typing) plus Bookwright (`bw:`) properties. It
  MUST NOT introduce any new GOLEM/ontology class.
- **FR-002**: A Source MUST record all of: reference or URL, author, original
  language, type, reliability level with a justification, access date, and a
  relevant textual quote in the original language plus a translation when the
  original language differs from the book's language.
- **FR-003**: A Source's type MUST be drawn from a controlled vocabulary of
  exactly: `primaria`, `secundaria`, `oficial`, `académica`, `periodística`,
  `testimonial`.
- **FR-004**: A Source's reliability MUST be one of exactly three levels —
  `alta`, `media`, `baja` — and MUST carry a justification.
- **FR-005**: System MUST provide a controlled-vocabulary file (`sources.ttl`)
  that defines the source types and reliability levels via `E55_Type` and the
  `bw:` properties that reify Source / Finding / Anchor over `E13`.
- **FR-006**: A Finding MUST represent a claim about the real world, reified as an
  `E13_Attribute_Assignment` capturing: what is claimed, who asserts it, which
  narrative entity it bears on, and the supporting source(s).
- **FR-007**: A Finding MUST be supportable by one *or more* Sources.
- **FR-008**: A Finding MUST be able to remain in an **open** state (an
  unresolved question) and still be recorded, without requiring a resolved claim
  or a supporting source.
- **FR-009**: An Anchor MUST represent a Finding promoted to a binding
  constraint, linked via `bw:constrains` to the narrative entity it constrains —
  one of `G1_Character`, `G12_Setting`, `G5_Narrative_Event`, or the timeline.
- **FR-010**: An Anchor MUST be able to *optionally* carry a time-span
  (`P4_has_time-span`) to enable downstream anachronism detection; an anchor
  without a time-span MUST emit none.
- **FR-011**: System MUST generate URIs by composition `{uri_base}{segment}/{token}`
  using segment `source` with a slug token, `finding` with a UUIDv7 token, and
  `anchor` with a UUIDv7 token — consistent with the established convention
  (§ 4.5).
- **FR-012**: Research content MUST live as plain text under `bible/research/`:
  one `.md` per topic with structured front-matter (its findings and anchors)
  and human-readable prose below, plus `_index.md` (topic map + global open
  questions) and `sources.md` (consolidated source registry).
- **FR-013**: `bookwright graph build` MUST parse `bible/research/` and emit the
  corresponding Source / Finding / Anchor triples into the same `bible/graph.ttl`
  as the narrative entities.
- **FR-014**: Emitted Anchors MUST be linked so that the constrained narrative
  entity can be retrieved by a structured (SPARQL) query — e.g., "all anchors
  constraining a given character, with their claims and sources".
- **FR-015**: When `bible/research/` is absent or empty, `graph build` MUST
  proceed normally and emit no research triples (existing graph-build behaviour
  is unchanged for projects that do not research).
- **FR-016**: System MUST reject, with an explicit error, a Source whose declared
  type or reliability value falls outside the controlled vocabulary, and a
  non-open Finding that omits a required provenance facet.
- **FR-017**: `bible/graph.ttl` MUST remain the *derived* artifact: research
  triples are generated from the plain-text files in `bible/research/`, never the
  reverse.
- **FR-018**: Findings and Anchors reified on `E13` MUST be distinguishable —
  via their URI segments (`finding`, `anchor`) and `bw:` properties — from the
  pre-existing inferred-attribute assertions (segment `assertion`), so the two
  uses of `E13` do not collide.

### Key Entities

- **Source (`source`)**: a document or testimony consulted. Attributes:
  reference/URL, author, original language, type (controlled), reliability level
  (controlled) + justification, access date, original-language quote, optional
  translation. Typed via `E55_Type`. URI token: slug.
- **Finding (`finding`)**: a claim about the real world supported by one or more
  Sources, bearing on a narrative entity; may be *open* (unresolved). Reified as
  `E13_Attribute_Assignment`. URI token: UUIDv7.
- **Anchor (`anchor`)**: a Finding promoted to a binding constraint, linking
  (`bw:constrains`) to the narrative entity it constrains, optionally with a
  time-span. Reified on `E13`. URI token: UUIDv7.
- **Source vocabulary (`sources.ttl`)**: controlled vocabulary defining the six
  source types and three reliability levels via `E55_Type`, plus the `bw:`
  properties that wire Source/Finding/Anchor onto the `E13`/`E55` pattern.
- **Research files (`bible/research/`)**: the plain-text source of truth — a
  per-topic `.md` (structured front-matter + prose), `_index.md`, and
  `sources.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given a research topic file that describes a source, a finding and
  an anchor, building the project graph produces triples for all three, and the
  resulting `bible/graph.ttl` parses as well-formed RDF.
- **SC-002**: A structured query over the built graph returns every anchor that
  constrains a specified narrative entity (e.g., a given character), together
  with each anchor's claim and supporting source(s).
- **SC-003**: 100% of Source / Finding / Anchor nodes in the built graph carry a
  URI following `{uri_base}{segment}/{token}` with the correct segment
  (`source` / `finding` / `anchor`) and token kind (slug / UUIDv7).
- **SC-004**: A Source in the graph exposes all of its provenance facets, and the
  translation field is present exactly when the original language differs from the
  book's language (present when it differs, absent when it matches).
- **SC-005**: Building a project that has no `bible/research/` directory completes
  successfully and adds zero research triples (no regression in existing graph
  build).
- **SC-006**: 100% of source type and reliability values outside the controlled
  vocabulary are rejected at build time with an explicit, value-naming error.
- **SC-007**: Findings/Anchors and the pre-existing inferred-attribute
  assertions can be told apart in the graph with no false matches across the two
  uses of `E13`.

## Assumptions

- **Anchor as a distinct node.** Following § 4.5 (which gives `finding` and
  `anchor` *separate* URI segments and tokens), an Anchor is modelled as its own
  node derived from / referencing its Finding, not as a boolean flag on the
  Finding. The exact promotion link is an implementation detail for
  `/speckit-plan`.
- **Open findings.** An open finding may omit a resolved claim, supporting
  sources and/or a target entity; its "open" state is recorded explicitly,
  continuing the role of the classic `research.md` open-questions list.
- **Asserter of a finding.** "Who asserts it" is the investigating agent or the
  author; the precise representation of the asserter is left to the plan.
- **Slug rules and collisions inherited.** Source slugs follow the existing
  § 4.5 generation rules (lowercase ASCII via `python-slugify`); disambiguation
  of colliding slugs is the indexer's responsibility, not the provenance model's.
- **Templates and manifest config are out of this iteration.** The
  `bible/research/` *templates* (layered resources) and the `[research]` block of
  `manifest.toml` (`enabled`, `source_languages`, `min_reliability_for_anchor`)
  are delivered in iteration 14; this iteration parses `bible/research/` content
  when present (e.g., supplied by a test fixture) and stays inert when absent.
- **No new runtime dependencies.** The model reuses the existing stack (`rdflib`,
  `pydantic`, YAML front-matter parsing, `uuid-utils`, `python-slugify`); no
  network/runtime dependency is added (respects design § 14 and the plain-text
  axiom).
- **Reliability threshold and target existence are not enforced here.** Enforcing
  a minimum reliability for promotion to anchor and checking that anchor targets
  exist and are of an allowed kind belong to the `factual_anchor` validator
  (iteration 15).
- **Coverage gate.** New code is expected to meet the project's test-coverage
  discipline (acceptance criterion: >85%; constitution: ≥80%).
