# Feature Specification: Index locations (G13) + `bible.py` split

**Feature Branch**: `025-index-locations`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Necesidad: hoy bible/locations/*.md no se procesa en absoluto (atajo de v0)… Queremos que las localizaciones entren al grafo como entidades de primera clase… y sacar G13 del registro de diferidos de la iteración 024. (+ refactor que baja io/bible.py por debajo de 500 líneas, sin cambio de comportamiento)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Locations become first-class graph entities (Priority: P1)

An author has written one Markdown file per concrete place under `bible/locations/`,
each carrying `name:` front-matter (and optionally `setting:` naming the broad
universe it sits inside). When the project graph is built, every such file becomes
a `G13_Narrative_Location` node in the graph — exactly the way `bible/settings/`
files already become `G12_Setting` nodes. A later research finding whose
`bears_on:` / `constrains:` points at one of those locations now **resolves** to
the location entity instead of degrading to a soft-miss.

**Why this priority**: This is the whole point of the iteration and the
ingestion-parity north star — it turns the modelled-but-unfed `NarrativeLocation`
class into a fed concept, closing the v0 shortcut documented in design § 7.2.
Without it, nothing else in this feature has value.

**Independent Test**: Build the graph for a fixture project that contains
`bible/locations/<slug>.md` files (one with a resolvable `setting:`, one without)
and assert the graph holds the corresponding `G13_Narrative_Location` nodes, that
the `setting:` one carries the `dlp:generic-location` cross-ref edge to its
sibling setting, and that a research link targeting a location resolves rather
than producing a soft-miss.

**Acceptance Scenarios**:

1. **Given** a project with `bible/locations/harbor.md` whose front-matter has
   `name: "The Harbor"`, **When** the graph is built, **Then** the graph contains
   one `G13_Narrative_Location` node whose identity derives from the slug of its
   `name`, with `file:line` provenance pointing at the `name:` field.
2. **Given** `bible/locations/harbor.md` with `setting: "The Old Crossing"` where
   `bible/settings/the-old-crossing.md` exists, **When** the graph is built,
   **Then** a `dlp:generic-location` cross-ref edge is emitted from the location
   to that setting's node.
3. **Given** the same project plus a research finding whose `bears_on:` names "The
   Harbor", **When** the graph is built, **Then** the link resolves to the
   location node (no soft-miss warning for that target).
4. **Given** `bible/locations/harbor.md` with `setting: "Nowhere"` that matches no
   sibling setting, **When** the graph is built, **Then** the location node is
   still created and the unresolved `setting:` is surfaced as a mapper soft
   warning (no crash, no aborted build).
5. **Given** the production deferral registry and ingestion-parity test, **When**
   the suite runs after this iteration, **Then** `NarrativeLocation` is no longer
   in the deferred set, the orphan count drops from seven to six, and the parity
   test stays green with G13 observed as a reachable concept.

---

### User Story 2 - The bible authoring command teaches location front-matter (Priority: P2)

When the author runs the `/bookwright-bible` skill, it now instructs writing each
concrete location as `bible/locations/<slug>.md` with `name:` front-matter (plus
optional `setting:`) **in addition to** the sensory prose sections it already
asks for. The skill is re-materialized through the existing pipeline as a
`SKILL.md` under both the `claude` and `generic` integrations, with its bilingual
(ES/EN) triggers preserved.

**Why this priority**: The ingestion path (P1) is what makes locations resolve;
this story is what makes new authored locations actually carry the front-matter
the path consumes. It depends on P1's contract being settled but delivers the
author-facing half of the change.

**Independent Test**: Inspect the updated `bookwright-bible` source command and
its materialized `SKILL.md` outputs: confirm the location instruction now
prescribes `name:` (+ optional `setting:`) front-matter, that the "no se indexa en
v0 / sin frontmatter" wording is gone, that both `claude` and `generic` outputs
regenerate, and that the ES and EN trigger phrases survive.

**Acceptance Scenarios**:

1. **Given** the updated source command, **When** it is read, **Then** the
   procedure for `bible/locations/<slug>.md` prescribes `name:` (required) and
   `setting:` (optional) front-matter alongside the sensory prose sections, and no
   longer says locations are unindexed / front-matter-free in v0.
2. **Given** the materialization pipeline, **When** skills are regenerated, **Then**
   the `bookwright-bible` `SKILL.md` is produced for both `claude` and `generic`
   integrations with valid front-matter and unchanged bilingual triggers.

---

### User Story 3 - Backward compatibility and a legible mapper (Priority: P3)

A project carrying older v0-style location files (sensory prose, **no** ingestible
front-matter) keeps building without error: each such file is treated as
non-ingestible and skipped gracefully, exactly as the mapper already treats a file
with unusable front-matter — never a crash. A project with no `bible/locations/`
directory at all behaves exactly as before. Alongside this, the `io/bible.py`
module — currently exactly at the 500-line Principle IV ceiling — is split so that
adding the locations builder leaves it legible and under the limit, with **no
change to any observable output**.

**Why this priority**: Robustness and the constitutional size limit are
prerequisites for merging, but they ride underneath the visible behavior of P1/P2
rather than being the headline. They must hold, but they are verified by existing
tests staying green plus the new skip/absent cases.

**Independent Test**: Build a project with a frontmatter-less location file and a
project with no `locations/` directory; assert the first reports the file as
skipped (not mapped, no exception) and the second is unaffected. Separately,
confirm `io/bible.py` is under 500 lines after the split and that the pre-existing
bible mapper tests pass unchanged.

**Acceptance Scenarios**:

1. **Given** `bible/locations/old-place.md` with no ingestible front-matter,
   **When** the graph is built, **Then** the file is recorded as skipped, no
   location node is created for it, and the build completes normally.
2. **Given** a project with no `bible/locations/` directory, **When** the graph is
   built, **Then** the result is identical to current behavior (no error, no
   location nodes).
3. **Given** the split `io/bible.py` and its sibling module, **When** the bible
   mapper test suite runs, **Then** all pre-existing tests pass with no change to
   their expected outputs and `io/bible.py` is ≤ 500 lines.

---

### Edge Cases

- A location whose `name:` is missing or empty is skipped as unusable
  front-matter (same contract as characters/settings), never a crash.
- Two location files resolving to the same slug are rejected as a collision,
  exactly as characters and settings already are (per-concept collision scope).
- A `setting:` value that is present but not a string is treated as unusable
  front-matter for that file (the validation requires `setting`, when present, to
  be a string).
- A location's `setting:` naming a real **character** or **event** rather than a
  setting does not resolve (resolution is scoped to the sibling settings index),
  surfacing the same unresolved soft warning as a non-existent name.
- A location file carrying extra unknown front-matter keys produces the existing
  `unknown_keys` soft warning, not an abort — but only once it has produced an
  entity (consistent with the current single-dir contract).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The bible mapper MUST process `bible/locations/*.md` as a
  one-entity-per-file directory, mirroring `bible/settings/`, building a
  `NarrativeLocation` (G13) entity from each file's front-matter.
- **FR-002**: A location's front-matter MUST accept `name` (a required, non-empty
  string) and `setting` (an optional string naming a sibling setting). `name` is
  the identity source; the slug derives from it.
- **FR-003**: When `setting` is present and resolves against the settings index,
  the mapper MUST emit the `dlp:generic-location` cross-ref from the location to
  that setting's node.
- **FR-004**: When `setting` is present but does not resolve to a sibling setting,
  the mapper MUST surface a soft warning consistent with its existing
  unresolved-reference contract and still build the location node — never abort
  the build.
- **FR-005**: Built `NarrativeLocation` entities MUST feed the research target
  index (the same index characters, settings, and events feed) so that a research
  `bears_on:` / `constrains:` link to a location resolves instead of producing a
  soft-miss.
- **FR-006**: The mapper MUST reject a slug collision between two location files
  the same way it does for characters and settings (per-concept collision,
  raising the existing collision error).
- **FR-007**: A location file with missing/empty/unusable `name` front-matter, or
  with `setting` present but not a string, MUST be skipped as a non-ingestible
  file (recorded under skipped), exactly as the mapper handles unusable
  front-matter today — never a crash.
- **FR-008**: A project with no `bible/locations/` directory MUST build exactly as
  it does today (no error, no location nodes).
- **FR-009**: A v0-style location file with no ingestible front-matter MUST be
  treated as a non-ingestible file (graceful skip), preserving backward
  compatibility.
- **FR-010**: The `/bookwright-bible` source command MUST be updated so each
  concrete location is written with `name:` (required) and `setting:` (optional)
  front-matter in addition to its sensory prose sections, and MUST no longer state
  that locations are unindexed / front-matter-free in v0.
- **FR-011**: The updated command MUST re-materialize as a `SKILL.md` through the
  existing pipeline for both the `claude` and `generic` integrations, preserving
  its bilingual (ES/EN) author triggers.
- **FR-012**: `NarrativeLocation` MUST be removed from the iteration-024 deferral
  registry; the ingestion-parity test MUST stay green with G13 now observed as a
  reachable (fed) concept and the orphan set reduced to six.
- **FR-013**: `io/bible.py` MUST be brought below the 500-line Principle IV ceiling
  by extracting part of the module (e.g. the concrete builders and/or the
  directory/collection-spec machinery) into a sibling module, with **no change to
  any observable mapper output**; the existing bible tests MUST continue to pass
  unchanged.
- **FR-014**: The feature MUST NOT add any class or property to the frozen
  ontology (Principle X): `G13_Narrative_Location` and `dlp:generic-location`
  already exist and are reused as-is.
- **FR-015**: The feature MUST NOT change the `factual_anchor` validator or any
  research behavior beyond the now-resolving location links being the consequence
  of G13 becoming a fed concept.

### Key Entities *(include if feature involves data)*

- **NarrativeLocation (G13)**: A concrete place within the story world, modelled
  by the existing frozen `NarrativeLocation` class (`golem:G13_Narrative_Location`,
  `path_segment` `location`). Identity-only in v0, exactly like `Setting`: its only
  attributes are its identity (slug from `name`) and an optional cross-ref to its
  setting. No new attributes are introduced.
- **Location front-matter**: The ingestible front-matter of a `bible/locations/*.md`
  file — `name` (required string) and `setting` (optional string). Sensory prose
  sections remain human prose, not ingested.
- **`dlp:generic-location` cross-ref**: The already-modelled edge from a location
  to the setting it sits within, emitted when `setting:` resolves against the
  sibling settings index.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Building a fixture with N well-formed location files yields exactly N
  `G13_Narrative_Location` nodes in the graph, each with `file:line` provenance for
  its identity.
- **SC-002**: A location declaring a resolvable `setting:` produces exactly one
  `dlp:generic-location` edge to that setting; a location with no `setting:` (or an
  unresolvable one) produces none, and the unresolvable case yields a soft warning
  with the build still succeeding.
- **SC-003**: A research finding linking to a location resolves with zero soft-miss
  warnings for that target, where before this iteration it produced one.
- **SC-004**: After this iteration the deferral registry has exactly six entries
  (no `NarrativeLocation`), the ingestion-parity reachable set has exactly seven
  concepts (the prior six plus `NarrativeLocation`), and the full parity test suite
  is green.
- **SC-005**: A project with a frontmatter-less v0 location file, and a project with
  no `bible/locations/` directory, both build with zero errors.
- **SC-006**: `io/bible.py` is ≤ 500 lines after the change, all four CI gates
  (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest` at ≥ 80 %
  coverage) pass, and every pre-existing bible test passes with unchanged expected
  output.

## Assumptions

- Locations are processed **after** settings in the mapping pass, so a location's
  `setting:` can resolve against an already-populated settings index — mirroring how
  events resolve participants against already-built characters.
- Resolution of `setting:` is scoped to the **settings** index only (a location's
  setting is a `G12_Setting`), not the participant index or the general research
  index; an unresolved `setting:` reuses the mapper's existing unresolved-reference
  soft-warning channel rather than introducing a new warning category. The exact
  field/representation is left to the plan phase.
- `NarrativeLocation` does **not** feed the participant-resolution index (locations
  are not event/relationship participants in v0); it feeds only the research target
  index, mirroring how `Setting` participates today.
- Location attributes beyond identity + `setting` are out of scope: the v0 of the
  class is identity-only, exactly like `Setting`.
- The refactor of `io/bible.py` is a same-patch, behavior-preserving extraction
  (no release of its own); the locations builder is the observable delta that ships
  with it.
- Existing fixtures will gain `bible/locations/` files as needed to exercise the
  new path (e.g. the `parity-exercise` fixture, which currently has none), without
  altering the meaning of other fixtures.

## Out of Scope

- Any new class or property in the frozen GOLEM ontology (Principle X) — G13 and
  `dlp:generic-location` already exist.
- Changes to the `factual_anchor` validator or research behavior beyond location
  links now resolving as a side effect of G13 becoming fed.
- Location attributes beyond identity + `setting` (no sensory data, no typed place
  taxonomy) — the v0 class is identity-only, like `Setting`.
- Wiring the other deferred concepts (Object/G16, narrative-structure layer, etc.);
  those are their own iterations.
