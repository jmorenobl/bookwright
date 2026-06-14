# Feature Specification: Index objects (G16) + `bible/objects/` scaffold + skill

**Feature Branch**: `026-index-objects`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Necesidad: la clase G16_Object está modelada (modelo Object en golem/modules/character.py, identity-only, en CLASS_IRI y CONCEPTS) pero es huérfana: no hay builder, no existe bible/objects/ en el scaffold, y bookwright-bible no menciona objetos… Queremos cablearlos como entidades de primera clase, espejo de settings/, y sacar G16 del registro de diferidos."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Objects become first-class graph entities (Priority: P1)

An author has written one Markdown file per concrete storyworld object (a weapon,
a relic, a document) under `bible/objects/`, each carrying a `name:` front-matter
field. When the project graph is built, every such file becomes a `G16_Object`
node — exactly the way `bible/settings/` files already become `G12_Setting`
nodes. A later research finding whose `bears_on:` / `constrains:` points at one of
those objects now **resolves** to the object entity instead of degrading to a
soft-miss.

**Why this priority**: This is the whole point of the iteration and a step on the
ingestion-parity north star — it turns the modelled-but-unfed `Object` class into
a fed concept, closing the v0 shortcut that left G16 orphaned. Without it nothing
else in this feature has value.

**Independent Test**: Build the graph for a fixture project that contains
`bible/objects/<slug>.md` files and assert the graph holds the corresponding
`G16_Object` nodes with `file:line` provenance on identity, and that a research
link targeting an object resolves rather than producing a soft-miss.

**Acceptance Scenarios**:

1. **Given** a project with `bible/objects/excalibur.md` whose front-matter has
   `name: "Excalibur"`, **When** the graph is built, **Then** the graph contains
   one `G16_Object` node whose identity derives from the slug of its `name`, with
   `file:line` provenance pointing at the `name:` field.
2. **Given** the same project plus a research finding whose `bears_on:` names
   "Excalibur", **When** the graph is built, **Then** the link resolves to the
   object node (no soft-miss warning for that target).
3. **Given** the production deferral registry and ingestion-parity test, **When**
   the suite runs after this iteration, **Then** `Object` is no longer in the
   deferred set, the orphan count drops from six to five, the reachable set grows
   from seven to eight, and the parity test stays green with G16 observed as a
   reachable concept.

---

### User Story 2 - The bible authoring command teaches object front-matter (Priority: P2)

When the author runs the `/bookwright-bible` skill, it now instructs writing each
concrete storyworld object as `bible/objects/<slug>.md` with `name:` front-matter,
alongside the character, setting, and location sheets it already prescribes. The
skill is re-materialized through the existing pipeline as a `SKILL.md` under both
the `claude` and `generic` integrations, with its bilingual (ES/EN) triggers
preserved.

**Why this priority**: The ingestion path (P1) is what makes objects resolve; this
story is what makes new authored objects actually carry the `name:` front-matter
the path consumes. It depends on P1's contract being settled but delivers the
author-facing half of the change.

**Independent Test**: Inspect the updated `bookwright-bible` source command and its
materialized `SKILL.md` outputs: confirm the object instruction prescribes `name:`
front-matter, that `bible/objects/` is listed among the entity directories and the
files-to-write, that both `claude` and `generic` outputs regenerate, and that the
ES and EN trigger phrases survive.

**Acceptance Scenarios**:

1. **Given** the updated source command, **When** it is read, **Then** it lists
   `bible/objects/` among the entity directories to ensure/create, and its
   procedure prescribes writing each concrete object as
   `bible/objects/<slug>.md` with a required `name:` front-matter field.
2. **Given** the materialization pipeline, **When** skills are regenerated, **Then**
   the `bookwright-bible` `SKILL.md` is produced for both `claude` and `generic`
   integrations with valid front-matter and unchanged bilingual triggers.

---

### User Story 3 - Backward compatibility with older skeletons (Priority: P3)

A project carrying older v0-style trees keeps building without error. A project
with no `bible/objects/` directory at all behaves exactly as before. An object
file with no usable front-matter (missing/empty `name`) is treated as
non-ingestible and skipped gracefully — never a crash — exactly as the mapper
already treats characters and settings with unusable front-matter.

**Why this priority**: Robustness is a prerequisite for merging, but it rides
underneath the visible behavior of P1/P2 rather than being the headline. It must
hold, but it is verified by existing tests staying green plus the new skip/absent
cases.

**Independent Test**: Build a project with a front-matter-less object file and a
project with no `objects/` directory; assert the first reports the file as skipped
(not mapped, no exception) and the second is unaffected.

**Acceptance Scenarios**:

1. **Given** `bible/objects/blank.md` with no usable front-matter (missing/empty
   `name`), **When** the graph is built, **Then** the file is recorded as skipped,
   no object node is created for it, and the build completes normally.
2. **Given** a project with no `bible/objects/` directory, **When** the graph is
   built, **Then** the result is identical to current behavior (no error, no object
   nodes).
3. **Given** two object files resolving to the same slug, **When** the graph is
   built, **Then** the collision is rejected exactly as it is for characters and
   settings (per-concept collision, the existing collision error).

---

### Edge Cases

- An object whose `name:` is missing or empty is skipped as unusable front-matter
  (same contract as characters/settings), never a crash.
- Two object files resolving to the same slug are rejected as a collision, exactly
  as characters and settings already are (per-concept collision scope).
- An object file carrying extra unknown front-matter keys produces the existing
  `unknown_keys` soft warning, not an abort — but only once it has produced an
  entity (consistent with the current single-directory contract).
- A `name:` that is present but not a string is treated as unusable front-matter
  for that file (same `name`-required contract as settings), skipped gracefully.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The bible mapper MUST process `bible/objects/*.md` as a
  one-entity-per-file directory, mirroring `bible/settings/`, building an `Object`
  (G16) entity from each file's front-matter.
- **FR-002**: An object's front-matter MUST accept `name` (a required, non-empty
  string) as its only ingestible key. `name` is the identity source; the slug
  derives from it. The v0 of the class is identity-only, exactly like `Setting`.
- **FR-003**: Built `Object` entities MUST feed the research target index (the
  same `entity_index` characters, settings, locations, and events feed) so that a
  research `bears_on:` / `constrains:` link to an object resolves instead of
  producing a soft-miss. Objects MUST NOT feed the participant-resolution index
  (they are not event/relationship participants in v0), mirroring `Setting`.
- **FR-004**: The mapper MUST reject a slug collision between two object files the
  same way it does for characters and settings (per-concept collision, raising the
  existing collision error).
- **FR-005**: An object file with missing/empty/unusable `name` front-matter MUST
  be skipped as a non-ingestible file (recorded under skipped), exactly as the
  mapper handles unusable front-matter today — never a crash.
- **FR-006**: A project with no `bible/objects/` directory MUST build exactly as it
  does today (no error, no object nodes).
- **FR-007**: The project scaffold (`resources/project/`) MUST include a
  `bible/objects/` directory with the same starter material as `bible/settings/`
  and `bible/locations/` (i.e. the placeholder that keeps an otherwise-empty entity
  directory present in the scaffold).
- **FR-008**: The `/bookwright-bible` source command MUST be updated so
  `bible/objects/` is listed among the entity directories to ensure/create and its
  procedure prescribes writing each concrete object as `bible/objects/<slug>.md`
  with a required `name:` front-matter field, and `bible/objects/*.md` is added to
  its files-to-write list.
- **FR-009**: The updated command MUST re-materialize as a `SKILL.md` through the
  existing pipeline for both the `claude` and `generic` integrations, preserving
  its bilingual (ES/EN) author triggers.
- **FR-010**: `Object` MUST be removed from the iteration-024 deferral registry;
  the ingestion-parity test MUST stay green with G16 now observed as a reachable
  (fed) concept, the deferred set reduced to five entries and the reachable set
  grown to eight.
- **FR-011**: The feature MUST NOT add any class or property to the frozen ontology
  (Principle X): `G16_Object` already exists in `CLASS_IRI` and `CONCEPTS` and is
  reused as-is.
- **FR-012**: The feature MUST NOT introduce object cross-refs (e.g. object →
  bearer character) nor any object attribute beyond identity; both are out of
  scope for this patch.

### Key Entities *(include if feature involves data)*

- **Object (G16)**: A concrete thing within the storyworld (a weapon, a relic, a
  document), modelled by the existing frozen `Object` class (`golem:G16_Object`,
  `path_segment` `object`). Identity-only in v0, exactly like `Setting`: its only
  attribute is its identity (slug from `name`). No new attributes, no cross-refs.
- **Object front-matter**: The ingestible front-matter of a `bible/objects/*.md`
  file — `name` (required string) as the sole ingested key. Any prose body remains
  human prose, not ingested.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Building a fixture with N well-formed object files yields exactly N
  `G16_Object` nodes in the graph, each with `file:line` provenance for its
  identity.
- **SC-002**: A research finding linking to an object resolves with zero soft-miss
  warnings for that target, where before this iteration it produced one.
- **SC-003**: After this iteration the deferral registry has exactly five entries
  (no `Object`), the ingestion-parity reachable set has exactly eight concepts (the
  prior seven plus `Object`), and the full parity test suite is green.
- **SC-004**: A project with a front-matter-less object file, and a project with no
  `bible/objects/` directory, both build with zero errors.
- **SC-005**: A freshly scaffolded project contains a `bible/objects/` directory
  mirroring `bible/settings/` and `bible/locations/`, and the `bookwright-bible`
  `SKILL.md` for both `claude` and `generic` prescribes object sheets — all four CI
  gates (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest` at ≥ 80 %
  coverage) pass, and every pre-existing bible test passes with unchanged expected
  output.

## Assumptions

- Objects are processed as a one-entity-per-file directory pass identical in shape
  to the settings pass: identity-only, feeding the research `entity_index` but not
  the participant `slug_index`. Their position in the mapping order is immaterial
  because objects carry no cross-ref to another concept in v0.
- The scaffold's "starter material" for `bible/objects/` mirrors whatever
  `bible/settings/` and `bible/locations/` ship today (the placeholder that keeps
  the directory present); no authored sample object is required.
- The existing `io/bible.py` / `io/_bible_builders.py` split (iteration 025) leaves
  ample headroom under the 500-line Principle IV ceiling, so this additive change
  needs no further module split.
- Existing fixtures will gain `bible/objects/` files as needed to exercise the new
  path (e.g. the `parity-exercise` fixture, which currently has none) plus a
  research link targeting an object, without altering the meaning of other
  fixtures.
- `Object`'s `path_segment` (`object`) and `CLASS_IRI`/`CONCEPTS` registration are
  taken as-is from the existing model; this feature only adds a builder, scaffold,
  skill copy, and fixture coverage.

## Out of Scope

- Any new class or property in the frozen GOLEM ontology (Principle X) — G16
  already exists.
- Object cross-refs (e.g. object → bearer character, object → location) — deferred
  beyond this patch.
- Object attributes beyond identity (no typed object taxonomy, no provenance/owner
  fields) — the v0 class is identity-only, like `Setting`.
- Changes to the `factual_anchor` validator or research behavior beyond object
  links now resolving as a side effect of G16 becoming fed.
- Wiring the other deferred concepts (narrative-structure layer G7/G9/G10,
  RelationshipRole/G6, PsychologicalState/G3) — those are their own iterations.

**Reference**: `bookwright-design.md § 4.2` (G16 as a concept and its URI).
Principle I (plain-text source of truth), Principle X (frozen ontology). Direct
precedent: the settings builder in `io/bible.py` and, just shipped, the locations
builder (iteration 025).
