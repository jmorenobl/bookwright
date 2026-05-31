# Feature Specification: Graph Indexer + `graph` Commands

**Feature Branch**: `006-graph-indexer`

**Created**: 2026-05-31

**Status**: Draft

**Input**: User description: "Necesidad: el grafo de un proyecto Bookwright es la representación consultable de su contenido narrativo. Necesitamos poder construirlo desde los archivos markdown de la bible y manuscrito, y consultarlo desde el CLI o desde los commands. [...] Referencia: ver bookwright-design.md § 12 (Sistema de Indexers) y § 5.1 (comandos del CLI)."

## Clarifications

### Session 2026-05-31 (resolved during `/speckit-plan`; user delegated both to engineering judgment)

- **Q: How do character scalars (`born`/`died`/`features`/`narrative_roles`)
  become triples, given iteration-5's identity-only model and SC-001's
  frozen-vocabulary constraint?**
  **A:** Map each to the term the **frozen GOLEM/CIDOC ontology already
  defines** — nothing dropped, nothing minted:
  `narrative_roles[]` → `dlp:plays → golem:G11_Narrative_Role`;
  `features[]` → `golem:GP0_has_feature → golem:G17_Character_Feature` (text via
  `rdfs:label`); `born`/`died` → biographical `golem:G17_Character_Feature`
  (`crm:P2_has_type` birth/death) carrying the year via
  `crm:P43_has_dimension → crm:E54_Dimension —crm:P90_has_value→ xsd:gYear`.
  This honors FR-010 and SC-001 as written. **Consequence:** iteration-5's
  identity-only typed model is extended additively now (new `CharacterFeature`
  /`Dimension` entities, `Character.features`/`.roles`) so it can construct/emit
  these — also unblocking iteration 10's validators. See plan R1/R1a.

- **Q: Is the bible laid out as four directories (FR-009) or per design § 7?**
  **A:** Per design § 7 / what `bookwright init` actually scaffolds:
  `bible/characters/*.md` and `bible/settings/*.md` are one-entity-per-file;
  `bible/timeline.md` and `bible/relationships.md` are single collection files.
  FR-009 is corrected accordingly (see below). See plan R2.

## User Scenarios & Testing *(mandatory)*

This iteration turns a project's plain-text bible into a queryable knowledge
graph. It builds directly on the typed GOLEM domain model delivered in
iteration 5 (which knows how to construct entities and emit their triples) and
exposes two CLI verbs — `graph build` and `graph query` — plus the pluggable
indexer engine that both sit on top of. Nothing here validates semantic
coherence (iteration 10) and nothing mutates the graph from the command line
(write-back is explicitly excluded): this is build-and-read only.

The consumers are the human author at a terminal and the agent (via Agent
Skills / commands) that needs to ask structured questions about the narrative.

### User Story 1 - Build the project graph from the bible (Priority: P1)

An author (or an agent) has a Bookwright project with character, setting,
timeline, and relationship files under `bible/`. They run `bookwright graph
build` from the project root. The toolkit reads those markdown files, turns each
one's frontmatter into GOLEM instances, and writes a single Turtle file at
`bible/graph.ttl` containing every triple.

**Why this priority**: Without a built graph there is nothing to query, nothing
to validate, and no value delivered. This is the minimum viable slice: a command
that reads the bible and produces a well-formed `bible/graph.ttl`.

**Independent Test**: In a fixture project containing one valid character file,
run `graph build` and assert that `bible/graph.ttl` is created, parses as
well-formed RDF, and contains the triples implied by that file's frontmatter
(a type assertion plus one triple per recognised frontmatter key).

**Acceptance Scenarios**:

1. **Given** a project whose `bible/characters/` contains a valid character file,
   **When** `bookwright graph build` runs, **Then** `bible/graph.ttl` is created
   and contains a type-assertion triple binding that character's identifier to
   the GOLEM character class plus the triples for its declared attributes.
2. **Given** a project with several valid bible files across recognised
   subdirectories, **When** `graph build` runs, **Then** the resulting
   `bible/graph.ttl` contains the union of every file's triples and uses the
   registered short prefixes (GOLEM, RDF, RDFS, etc.) rather than expanded IRIs.
3. **Given** a previously built `bible/graph.ttl`, **When** `graph build --force`
   runs, **Then** the graph is rebuilt from scratch (any cache is ignored) and
   the output reflects the current state of the bible files.
4. **Given** a successful build, **When** it completes, **Then** the command
   reports how many source files were processed and how many triples were
   written (human-readable to stderr; machine-readable under `--json`).

---

### User Story 2 - Query the graph with SPARQL (Priority: P1)

An author or agent needs to ask a structured question of the built graph — "who
are the protagonists?", "which characters were born before 1850?" — by passing a
SPARQL query string. They run `bookwright graph query "<SPARQL>"` and get back
the result rows, either as a human-readable table or, with `--json`, as a single
parseable JSON document.

**Why this priority**: Querying is the other half of the value proposition and is
what every downstream command and validator ultimately relies on. It is
independently testable against any pre-existing graph fixture, even one not
produced by Story 1.

**Independent Test**: Against a fixture `bible/graph.ttl`, run a `SELECT` query
and assert the returned rows match the expected bindings; run the same query with
`--json` and assert stdout is a single valid JSON document and nothing else.

**Acceptance Scenarios**:

1. **Given** a built graph containing two characters, **When**
   `graph query "SELECT ?c WHERE { ?c a golem:G1_Character }"` runs, **Then** the
   output lists exactly those two character identifiers.
2. **Given** the same graph, **When** the query is run with `--json`, **Then**
   stdout contains exactly one JSON document of the form
   `{"status": "ok", "results": [...], "count": N}` and no other text; human
   progress or warnings appear only on stderr.
3. **Given** a query that matches nothing, **When** it runs, **Then** the command
   succeeds (non-error exit) and reports an empty result set (`count` 0).
4. **Given** a syntactically invalid SPARQL string, **When** the query runs,
   **Then** the command fails with a clear error naming the problem and exits
   non-zero, and under `--json` emits an error document rather than partial rows.

---

### User Story 3 - Provenance for every generated triple (Priority: P2)

When the indexer derives a triple from a bible file, it also records *where that
assertion came from* — the source file path, and the line when the value can be
located to one. This is captured as a GOLEM/CIDOC Attribute Assignment so that
later tooling can distinguish what the text states from what was inferred.

**Why this priority**: Provenance is what makes the graph auditable and is a
prerequisite for the validators of iteration 10, but a graph is already useful
for querying before provenance is wired in. It builds on Stories 1–2.

**Independent Test**: Build a graph from a single character file and assert that,
alongside the character's attribute triples, the graph contains an Attribute
Assignment that names the source path (e.g. `bible/characters/aparici.md`) and is
associated with the asserted attribute.

**Acceptance Scenarios**:

1. **Given** a character file at `bible/characters/aparici.md`, **When** the
   graph is built, **Then** each derived attribute has a corresponding Attribute
   Assignment whose source reference is `bible/characters/aparici.md`.
2. **Given** an attribute whose value can be located to a specific line in the
   source file, **When** the graph is built, **Then** the Attribute Assignment's
   source reference includes the line locator (e.g. `…aparici.md:7`).
3. **Given** the built graph, **When** it is queried for assertions about a
   given entity, **Then** the provenance records are retrievable as triples.

---

### User Story 4 - Pluggable indexer engine selected from the manifest (Priority: P2)

The graph engine sits behind an abstract interface. The v0 engine uses rdflib,
but the engine name is read from `manifest.toml > [bookwright] indexer`
(default `rdflib`), so a future engine can be plugged in without touching the
`build`/`query` command code.

**Why this priority**: This is the architectural guarantee that keeps a future
`GrafeoIndexer` (deferred to v0.3) from forcing a rewrite. It is a constraint on
*how* Stories 1–2 are built rather than a user-facing feature, hence P2, but it
is independently verifiable.

**Independent Test**: With `[bookwright] indexer = "rdflib"` (or absent), assert
the rdflib engine is selected; with an unknown engine name, assert the CLI fails
with a clear error naming the unknown engine and listing the available ones.

**Acceptance Scenarios**:

1. **Given** a manifest with no `indexer` key, **When** any `graph` command runs,
   **Then** the default `rdflib` engine is used.
2. **Given** a manifest with `indexer = "rdflib"`, **When** any `graph` command
   runs, **Then** the rdflib engine is used and behaves identically to the
   default.
3. **Given** a manifest naming an indexer that is not registered, **When** a
   `graph` command runs, **Then** it fails with a clear error that names the
   unknown engine and the set of available engines, and exits non-zero.
4. **Given** the `build` and `query` command code, **When** a new engine is added
   to the registry, **Then** no change to that command code is required for it to
   be selectable.

---

### User Story 5 - Clear, fault-tolerant build reporting (Priority: P3)

A build should never silently swallow problems. Missing required directories
fail fast with an actionable message; a single malformed file does not abort the
whole build but is collected and reported at the end; an identifier collision
between two entities is a hard error because it would corrupt the graph.

**Why this priority**: Correct error behaviour is what makes the tool trustworthy
in daily use, but the happy paths (Stories 1–2) deliver value first. P3.

**Independent Test**: Run `graph build` against (a) a project missing `bible/`,
(b) a project with one malformed file among several valid ones, and (c) a project
whose files collide on a generated identifier; assert each produces the specified
outcome.

**Acceptance Scenarios**:

1. **Given** a project where `bible/` does not exist, **When** `graph build`
   runs, **Then** it fails immediately with a clear error naming the missing
   directory and exits non-zero, writing no graph file.
2. **Given** a project where `manuscript/` does not exist, **When** `graph build`
   runs, **Then** it fails with a clear error naming the missing directory.
3. **Given** a bible with one file whose frontmatter is invalid among several
   valid files, **When** `graph build` runs, **Then** the valid files are still
   processed, the invalid file is listed with the reason it failed, and the
   failures are summarised at the end of the run.
4. **Given** two bible files that produce the same entity identifier (slug
   collision within a type), **When** `graph build` runs, **Then** it fails with
   an explicit error naming the colliding identifier and the two source files.

---

### Edge Cases

- **`bible/` or `manuscript/` missing**: hard error, fail before writing
  anything, name the missing directory.
- **A file with invalid/unparseable frontmatter** (malformed YAML, missing
  required keys, wrong value types): the file is skipped, recorded with file path
  and reason, the build continues, and all such failures are reported together at
  the end. A build that had any skipped files signals this in its exit status /
  report so it is not mistaken for a clean build.
- **Slug collision** — two distinct entities of the same type whose canonical
  names slugify to the same identifier: hard error naming the identifier and both
  source files; the indexer does not silently merge or silently diverge.
- **Empty bible** (recognised directories exist but contain no files): build
  succeeds and writes an empty (or prefix-only) `bible/graph.ttl`; reports zero
  entities.
- **`graph query` before any `graph build`** (no `bible/graph.ttl` yet): clear
  error telling the user to run `graph build` first; exits non-zero.
- **Invalid SPARQL** passed to `graph query`: clear error, non-zero exit, no
  partial output; under `--json`, an error document.
- **Unknown indexer name** in the manifest: clear error naming the unknown
  engine and the available ones.
- **Frontmatter key not recognised by the entity's mapping**: ignored without
  failing the file (an unknown key is not the same as invalid frontmatter), and
  noted so the author can spot typos.
- **Running outside a Bookwright project** (no `manifest.toml`): clear error
  telling the user they are not inside a project.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a `bookwright graph build` command that
  reads the current project's `bible/` (and `manuscript/`) markdown, extracts
  GOLEM model instances, and writes all resulting triples to `bible/graph.ttl`.
- **FR-002**: `graph build` MUST accept a `--force` flag that rebuilds the graph
  from scratch, ignoring any cache.
- **FR-003**: The system MUST provide a `bookwright graph query "<SPARQL>"`
  command that executes a SPARQL query against the built graph and returns the
  results.
- **FR-004**: `graph query` MUST accept `--json`; when set it MUST emit a single
  JSON document on stdout (and only that), of the shape
  `{"status": "ok", "results": [...], "count": N}`, with all human-readable
  prose, progress, and warnings sent to stderr.
- **FR-005**: The graph engine MUST sit behind an abstract interface (Protocol)
  so the build/query commands depend on the interface, not a concrete engine.
- **FR-006**: The v0 engine implementation MUST use rdflib and MUST support, at
  minimum, loading a Turtle file, serializing to Turtle, adding triples,
  executing SPARQL queries, and reporting the triple count.
- **FR-007**: The engine to use MUST be read from `manifest.toml > [bookwright]
  indexer`, defaulting to `rdflib` when the key is absent; an unrecognised value
  MUST fail with a clear error that names the unknown engine and lists the
  available engines.
- **FR-008**: Adding a new engine MUST NOT require changes to the `build` or
  `query` command code (the engine is resolved through a registry/factory).
- **FR-009**: The bible parser MUST identify entity types by location, matching
  the layout `bookwright init` scaffolds (design § 7): one-entity-per-file under
  `bible/characters/` (→ Character) and `bible/settings/` (→ Setting), and the
  single collection files `bible/timeline.md` (→ Narrative Events, one per
  `events:` item) and `bible/relationships.md` (→ Social Relationships, one per
  `relationships:` item), mapping each to its corresponding GOLEM concept.
  *(Corrected from "timeline/" / "relationships/" directories per Clarifications.)*
- **FR-010**: For each source file, the parser MUST convert the file's YAML
  frontmatter into triples drawn entirely from the frozen GOLEM/CIDOC vocabulary.
  For a character, the documented frontmatter maps as: `name` → identity +
  `rdf:type golem:G1_Character`; `narrative_roles[]` → `dlp:plays
  golem:G11_Narrative_Role`; `features[]` → `golem:GP0_has_feature
  golem:G17_Character_Feature` (`rdfs:label`); `born`/`died` → biographical
  `golem:G17_Character_Feature` (`crm:P2_has_type`) with the year carried via
  `crm:P43_has_dimension → crm:E54_Dimension —crm:P90_has_value→ xsd:gYear`. The
  iteration-5 GOLEM typed model is extended additively to construct/emit these
  (see plan R1a); no class or predicate outside `frozen_terms()` is introduced.
- **FR-011**: Every generated triple MUST carry a corresponding Attribute
  Assignment that points to the source file, and to the line within that file
  when the value can be located to a specific line.
- **FR-012**: If `bible/` or `manuscript/` does not exist, `graph build` MUST
  fail with a clear error naming the missing directory and MUST NOT write a
  partial graph.
- **FR-013**: If a source file has invalid frontmatter, `graph build` MUST skip
  that file, record the file path and the reason, continue processing the rest,
  and report all such failures at the end of the run.
- **FR-014**: If two entities generate the same identifier (slug collision within
  a type), `graph build` MUST fail with an explicit error naming the colliding
  identifier and the conflicting source files.
- **FR-015**: The serialized `bible/graph.ttl` MUST parse as well-formed RDF and
  MUST use the registered short prefixes rather than fully-expanded IRIs.
- **FR-016**: `graph query` MUST report an empty-but-successful result for a query
  that matches nothing, and MUST fail with a clear error (non-zero exit, no
  partial rows) for a syntactically invalid query.
- **FR-017**: The `graph` commands MUST NOT mutate the graph from the command
  line (no write-back) beyond `build` (re)writing `bible/graph.ttl`, and MUST NOT
  perform semantic coherence validation (that is iteration 10).
- **FR-018**: `graph build` MUST report a summary of the run — number of source
  files processed, number of entities/triples produced, and number of skipped
  files — in human-readable form on stderr and, when `--json` is provided, as a
  single JSON document on stdout.

### Key Entities

- **Project Graph**: the project's knowledge graph, persisted as Turtle at
  `bible/graph.ttl`; the union of all triples derived from the bible.
- **Bible Source File**: a markdown file under a recognised `bible/`
  subdirectory whose YAML frontmatter describes one narrative entity.
- **Indexer (graph engine)**: the abstract interface plus its concrete rdflib
  implementation; loads/saves Turtle, adds triples, runs SPARQL, counts triples.
- **Indexer Registry**: the catalogue that maps an engine name (from the
  manifest) to its concrete implementation, with `rdflib` as the default.
- **Attribute Assignment (provenance record)**: ties a derived attribute to its
  source file (and line when known), per the iteration-5 domain model.
- **Build Report**: the per-run summary — files processed, triples written,
  skipped files with reasons, collisions.
- **Query Result**: the rows returned by a SPARQL query, renderable as a table
  or as the `--json` document.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a valid bible, `graph build` produces a `bible/graph.ttl` that
  parses as well-formed RDF 100% of the time, with zero predicates or classes
  absent from the frozen GOLEM vocabulary.
- **SC-002**: A `SELECT` query that should match N entities returns exactly N
  result rows — no missing and no spurious rows — for every fixture query.
- **SC-003**: With `--json`, stdout is exactly one valid JSON document and
  contains no human-readable prose; this holds for success, empty-result, and
  error cases.
- **SC-004**: A build over a bible containing one malformed file among otherwise
  valid files completes, processes 100% of the valid files, and lists the one
  failure with its reason — no silent data loss.
- **SC-005**: A slug collision is detected and reported 100% of the time and
  never results in a graph that silently merges two distinct entities.
- **SC-006**: 100% of triples derived from the bible have an associated Attribute
  Assignment naming their source file.
- **SC-007**: Switching the engine name in the manifest, or adding a new engine
  to the registry, requires zero edits to the `build`/`query` command code.

## Assumptions

- **Iteration 5 domain model is available and is extended here**: typed GOLEM
  classes that construct entities, generate deterministic ASCII slugs, and emit
  triples (including Attribute Assignment with source path and optional line) are
  available. Slug rules and URI patterns are owned by iteration 5 and reused
  as-is. **However**, iteration 5's model is *identity-only*; to satisfy FR-010
  this iteration extends it **additively** (new `CharacterFeature`/`Dimension`
  entities and `Character.features`/`.roles` fields) using terms already in the
  frozen ontology — see plan R1a. The extension is backward-compatible (existing
  identity-only behaviour and tests preserved).
- **Indexer Protocol shape**: the engine interface follows design § 12.1
  (`load`, `save`, `add_triple`, `query`, `construct`, `count`); `GrafeoIndexer`
  is a deferred stub (v0.3) and MUST NOT be implemented here.
- **Manifest is available**: iteration 2's manifest model supplies
  `[bookwright] uri_base` and `[bookwright] indexer`; this iteration reads them
  and does not re-validate `uri_base`.
- **Recognised bible subdirectories**: `characters/`, `settings/`, `timeline/`,
  and `relationships/` (per design § 7), each mapping to a GOLEM concept.
  Character frontmatter is the documented schema; the other types follow the
  analogous frontmatter-to-property mapping for their GOLEM module. *(The exact
  frontmatter schema for non-character types is a likely clarification target.)*
- **Manuscript role in this iteration**: `manuscript/` is read so its presence is
  required and so provenance can reference manuscript lines; deep prose mining
  (NLP, mention extraction) is **not** in scope — entity extraction is driven by
  bible frontmatter. *(How much, if anything, is extracted from manuscript prose
  is a likely clarification target.)*
- **Cache semantics**: a `.bookwright/cache/` may speed up rebuilds; `--force`
  bypasses it. The precise default (incremental vs. always-full) behaviour is a
  likely clarification target; the conservative default is a full rebuild every
  time, with caching as an optimisation that never changes output.
- **`graph query` supports SELECT at minimum**: ASK/CONSTRUCT handling, if
  included, follows the same stdout/stderr and `--json` contract.
- **Commands run from the project root**, locating the project via `manifest.toml`
  the same way other Bookwright commands do.

## Dependencies

- **Iteration 5 (GOLEM domain model)**: supplies the typed entities, slug/URI
  generation, RDF serialization, and Attribute Assignment provenance.
- **Iteration 2 (Manifest model)**: supplies `[bookwright] uri_base` and
  `[bookwright] indexer`.
- **rdflib**: the v0 graph engine (parse/serialize Turtle, SPARQL).

## Out of Scope

- Validators and semantic consistency checks (iteration 10).
- Mutating the graph from the command line / write-back; only read and
  (re)build are supported.
- `GrafeoIndexer` and vector search (v0.3) — only the pluggable seam is built.
- A `graph stats` (or other) subcommand beyond `build` and `query` for v0.
- Deep prose/manuscript mining beyond what bible frontmatter drives.
