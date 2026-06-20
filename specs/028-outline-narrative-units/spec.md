# Feature Specification: Outline ingestion — narrative units & functions (G9/G10)

**Feature Branch**: `028-outline-narrative-units`

**Created**: 2026-06-19

**Status**: Draft

**Input**: User description: "Open outline ingestion by wiring narrative units (G9) and their functions (G10) as first-class GOLEM entities built from `outline/units/*.md`, so plot structure is citable by SPARQL, and remove G9/G10 from the deferral registry."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plot structure becomes queryable from authored beat cards (Priority: P1)

An author breaks the plot into narrative beats and records each as a one-file
card under `outline/units/`, giving the unit a `name` and an optional list of
`functions` it performs (e.g. `interdiction`, `departure`). When the project
graph is built, each card becomes a `NarrativeUnit` entity and each named
function becomes a `NarrativeFunction` entity, deduplicated by slug across every
unit. A reference edge (`crm:P67_refers_to`) links each unit to the functions it
performs. The author (or a skill on their behalf) can now ask the graph "which
units perform function X" via SPARQL — the plot's structural layer that was
modelled-but-unfed is now alive.

**Why this priority**: This is the core value and the MVP. It is what takes G9
and G10 out of the deferral registry and makes the narrative-structure layer
citable. Everything else (role links, authoring surface) builds on units
existing as entities.

**Independent Test**: Create a project with two `outline/units/*.md` cards
sharing one function name; build the graph; confirm two `NarrativeUnit`
entities, exactly one `NarrativeFunction` for the shared name, and a unit→function
edge from each unit. Delivers a queryable plot structure with no other change.

**Acceptance Scenarios**:

1. **Given** `outline/units/opening.md` with frontmatter `name: Opening` and
   `functions: [interdiction, departure]`, **When** the graph is built, **Then**
   one `NarrativeUnit` for "Opening" and two `NarrativeFunction` entities
   (`interdiction`, `departure`) exist, each linked from the unit by
   `crm:P67_refers_to`.
2. **Given** two unit cards that both list the function `departure`, **When** the
   graph is built, **Then** exactly one `NarrativeFunction` entity for
   `departure` exists (deduplicated by slug) and both units refer to it.
3. **Given** a unit card with `name` but no `functions` key, **When** the graph
   is built, **Then** the `NarrativeUnit` exists and emits only its identity
   assertion (no function edges), with no error.
4. **Given** a unit card whose prose body describes the beat, **When** the graph
   is built, **Then** the body is not ingested — only the frontmatter informs the
   graph.

---

### User Story 2 - Units link to the narrative roles characters play (Priority: P2)

A unit card may also list `roles` — the narrative roles active in that beat
(e.g. `hero`, `villain`). These names resolve against the narrative roles already
materialized inline by characters (a character's `narrative_roles:`). When a name
resolves, a `crm:P67_refers_to` edge links the unit to that role; when it does
not resolve, it is a soft miss recorded as an unresolved reference, never a crash.

**Why this priority**: Adds the second structural dimension (who is active in a
beat) but depends on units existing first and on the character role layer that
already ships. The feature is still valuable as an MVP without it.

**Independent Test**: With a character declaring `narrative_roles: [hero]`, add a
unit card with `roles: [hero, ghost]`; build the graph; confirm a unit→role edge
to the resolved `hero` role and one unresolved-reference warning for `ghost`,
with the unit still built.

**Acceptance Scenarios**:

1. **Given** a character with `narrative_roles: [hero]` and a unit with
   `roles: [hero]`, **When** the graph is built, **Then** the unit has a
   `crm:P67_refers_to` edge to that narrative role.
2. **Given** a unit with `roles: [unknown-role]` that matches no character role,
   **When** the graph is built, **Then** the unit is still built, no role edge is
   emitted, and one unresolved-reference soft warning is recorded.
3. **Given** a unit with no `roles` key, **When** the graph is built, **Then** the
   unit is built with no role edges and no warning.

---

### User Story 3 - The authoring surface guides creating unit cards (Priority: P3)

An author invoking the `bookwright-outline` skill is instructed not only to
write the prose arcs/structure/synopsis but also to create one card per narrative
unit under `outline/units/` with `name`/`functions`/`roles` frontmatter. A new
project scaffolded by `bookwright init` already contains an `outline/units/`
directory with starter material, mirroring `bible/settings/`.

**Why this priority**: Without this, the ingestion works but authors have no
guided path to produce the cards. It is the discoverability layer; the engine
behaviour (US1/US2) is independently valuable and testable before it lands.

**Independent Test**: Materialize integrations and confirm the regenerated
`bookwright-outline` `SKILL.md` (in both `claude` and `generic`) instructs unit
cards with the documented frontmatter and preserves bilingual triggers; scaffold
a fresh project and confirm `outline/units/` exists.

**Acceptance Scenarios**:

1. **Given** the updated `bookwright-outline` source command, **When**
   integrations are materialized, **Then** the `claude` and `generic` `SKILL.md`
   both instruct creating `outline/units/` cards with `name`/`functions`/`roles`
   and still trigger on both Spanish and English author prompts.
2. **Given** a freshly initialized project, **When** the author lists the tree,
   **Then** `outline/units/` exists with starter material, like `bible/settings/`.

---

### Edge Cases

- **Unit card with no frontmatter at all** → treated as a non-ingestible file:
  skipped gracefully (like today's unusable-frontmatter handling), never a crash.
- **Unit card with malformed YAML or unreadable bytes** → skipped with a reason,
  build continues (consistent with the existing mapper contract).
- **Unit `name` missing, empty, or not a string** → the file is skipped (unusable
  frontmatter), build continues.
- **`functions` or `roles` present but not a list of strings** → unusable
  frontmatter for that file; it is skipped, build continues.
- **Two unit cards whose `name` slugs collide** → rejected as a slug collision,
  exactly as for characters/settings.
- **A function name and a role name that slug identically** → they live in
  separate identity spaces (function nodes vs. character-scoped role nodes); they
  do not collide or merge.
- **Project with no `outline/units/` directory** → behaves exactly as today; the
  build proceeds with no narrative units.
- **A unit role name that matches the same role played by several characters** →
  see Assumptions; resolves to every matching character role by slug.

## Clarifications

### Session 2026-06-19

*(Resolved non-interactively on the constitution's NON-NEGOTIABLE principles and
the zero-debt bar; rationale inline.)*

- Q: When a unit `roles` name matches a role slug played by several characters,
  how does it resolve — to every matching character-scoped role, to one canonical
  role node, or by minting a top-level role? → A: It resolves to **every**
  character-scoped role node whose slug matches, emitting one unit→role
  `crm:P67_refers_to` edge per match; the units pass mints nothing, and zero
  matches is a single soft miss. *Rationale*: faithful to the character-scoped
  role URIs that already exist (`{character}/role/{slug}`); the alternatives
  either add an identity space the frozen ontology does not need (Principle X) or
  pick a node non-deterministically — both incur debt. This rule mints nothing
  and is deterministic.
- Q: How are repeated `roles` names within a single unit card handled? → A:
  De-duplicated by slug within the card before resolution, exactly as `functions`
  are (SC-002); the edge set is therefore (distinct role-slug in the card) ×
  (characters whose role slug matches). *Rationale*: mirrors the function-dedup
  contract, makes the unit→role edge count deterministic and testable
  (Principle VIII), and forecloses duplicate-edge debt.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest `outline/units/*.md` as a one-entity-per-file
  directory, mirroring `bible/settings|locations|objects`, building one
  `NarrativeUnit` per card from its frontmatter.
- **FR-002**: A unit card's frontmatter MUST accept `name` (required, non-empty
  string), `functions` (optional list of strings), and `roles` (optional list of
  strings). No other unit attributes are ingested in this iteration.
- **FR-003**: The system MUST NOT ingest a unit card's prose body; only the
  frontmatter informs the graph.
- **FR-004**: For each name in a unit's `functions`, the system MUST materialize a
  `NarrativeFunction` entity (identity only), deduplicated by slug across all
  units, and emit the unit→function cross-reference (`crm:P67_refers_to`, already
  declared on the `NarrativeUnit` model).
- **FR-005**: For each **distinct** (slug-deduplicated within the card) name in a
  unit's `roles`, the system MUST resolve it against an index of the narrative
  roles that characters materialize inline from their `narrative_roles:` (no such
  index exists today — it MUST be populated during the character pass, before the
  units pass runs). The index is many-valued by slug: a name MUST resolve to
  **every** character-scoped role node whose slug matches, emitting one unit→role
  cross-reference (`crm:P67_refers_to`) per match; the units pass MUST mint no role
  entity. On zero matches it MUST record exactly one unresolved-reference soft
  warning and still build the unit (never crash). (Multiplicity and within-card
  dedup resolved in Clarifications, Session 2026-06-19.)
- **FR-006**: A unit card with no frontmatter, malformed YAML, unreadable bytes,
  or a missing/empty/non-string `name` MUST be skipped gracefully with a recorded
  reason; the build MUST continue.
- **FR-007**: `functions` or `roles` present but not a list of strings MUST render
  the card non-ingestible (skipped with a reason); the build MUST continue.
- **FR-008**: A slug collision between two unit `name`s MUST be rejected, exactly
  as for characters and settings.
- **FR-009**: A project with no `outline/units/` directory MUST build exactly as
  it does today (no units, no error).
- **FR-010**: The structural provenance for unit identity and for each unit→function
  / unit→role assertion MUST be emitted uniformly through the existing derived-
  assertion → `crm:E13_Attribute_Assignment` mechanism, resolving the originating
  frontmatter field to a `relpath:line` source where locatable.
- **FR-011**: The `bookwright-outline` source command MUST be updated to instruct,
  in addition to the prose arcs/structure/synopsis, creating one card per narrative
  unit under `outline/units/` with `name`/`functions`/`roles` frontmatter, and MUST
  be re-materialized as `SKILL.md` by the existing pipeline for both `claude` and
  `generic`, preserving bilingual (ES/EN) triggers. The added instructions MUST be
  written in the command's existing language (Spanish prose), matching the
  repository's language conventions for the source commands.
- **FR-012**: The project scaffold (`resources/project/outline/`) MUST include an
  `outline/units/` directory with starter material, mirroring `bible/settings/`.
- **FR-013**: The deferral registry MUST no longer list `NarrativeUnit` or
  `NarrativeFunction`; the ingestion-parity test MUST stay green with G9 and G10
  observed as alive (fed) and `NarrativeSequence` (G7) remaining the only narrative
  orphan. Both module docstrings' count prose — the registry's "Five of the
  thirteen" / "Exactly five entries", and the parity test's "Eight of the
  thirteen … the other five are orphans" — and every pinned constant in the
  parity test that encodes the orphan count — the reachable set
  (`EXPECTED_REACHABLE`, which gains `NarrativeUnit`/`NarrativeFunction`), the
  orphan-name set (`ORPHAN_NAMES`), the version-map (`EXPECTED_VERSIONS`), and the
  `len(DEFERRED_CONCEPTS) == 5` assertion (→ 3) — MUST be updated in lockstep so
  nothing still claims five orphans where there are now three. The three
  drift-simulation tests pick their probe concepts from the reachable/orphan sets
  (`Character`, `NarrativeEvent`, `PsychologicalState`); none names a removed
  concept, so they keep passing unchanged — the plan MUST confirm this rather than
  edit them. The `parity-exercise` fixture MUST gain at
  least one `outline/units/*.md` card declaring at least one `functions` name, so
  the live build actually observes `NarrativeUnit` and `NarrativeFunction` as
  reachable types (the parity test reads reachability from a real build, never a
  hand-list).
- **FR-014**: Every statement in the repository that documents `outline/` as
  wholly author-only MUST be amended so `outline/` reads as partially ingested
  (`units/` is ingested; `arcs`/`structure`/`synopsis`/`scenes` remain author-only
  prose) — this is a debt class to sweep in full, not a single edit. The known
  instances are: the iteration-024 note in `src/bookwright/io/manuscript.py`
  (English, code), the authoring-guide note in `docs/authoring.md` (Spanish, kept
  Spanish), and the deferral-registry docstring's "no builder over `bible/*.md`"
  framing. Additionally, the canonical design doc MUST be updated to match the
  precedent set when locations (§ 7.2) and objects (§ 7.3) were wired: add
  `outline/units/` to the project-tree listing in § 7 and add a new ingestion
  subsection (Spanish, mirroring § 7.2/§ 7.3) documenting the `outline/units/`
  surface. The design doc's skill-output table (the `Command | Input | Output`
  table) MUST also be brought current, since this is the same debt class — an
  authored-and-ingested surface missing from the table: add `outline/units/*.md`
  to the `/bookwright-outline` output row, and, sweeping the one pre-existing
  instance of the identical class, add the already-authored-and-ingested
  `bible/objects/*.md` (iteration 026) that the `/bookwright-bible` row still
  omits. Version-scoped *historical* statements that remain true are
  deliberately NOT swept — notably `bookwright-roadmap.md`'s record that `outline/`
  and `manuscript/` were author-only *en v0.3* (a past state it still describes
  accurately, and the roadmap is a durable ledger never emptied per milestone).
  The debt class is the *present-tense* claim that the engine ingests no
  `outline/`; SC-008's repository-wide search is therefore scoped to live source
  docstrings, the authoring guide, and the design doc, never the roadmap's
  historical ledger.
- **FR-015**: No new ontology class or property may be added; G9, G10, and
  `crm:P67_refers_to` already exist (Principle X). The 17-class closure and
  `golem.ttl` MUST remain frozen.

### Key Entities *(include if feature involves data)*

- **NarrativeUnit (G9)**: A narrative beat, one per `outline/units/*.md` card.
  Identity is a slug of its `name`. Carries reference edges to the functions it
  performs and the roles active in it. Prose body is not part of the entity.
- **NarrativeFunction (G10)**: A named narrative function (e.g. a Proppian
  function). Identity only, slug-deduplicated across all units; minted by the
  units pass from `functions` names. URI segment `narrative-function/<slug>`.
- **Narrative role (G11, character-scoped)**: Already materialized inline by
  characters from `narrative_roles:`. Units do not mint these; they resolve
  `roles` names against the roles characters already declared.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a project whose `outline/units/` holds N cards declaring M
  distinct function names total, a SPARQL query over the built graph returns
  exactly N `NarrativeUnit` entities and exactly M `NarrativeFunction` entities.
- **SC-002**: A unit declaring K function names produces exactly K unit→function
  `crm:P67_refers_to` edges (after slug dedup of repeats within the card).
- **SC-003**: 100% of malformed unit cards (no frontmatter, bad YAML, missing
  `name`, non-list `functions`/`roles`) are skipped without aborting the build,
  and every skip carries a recorded reason.
- **SC-004**: A unit `roles` name that matches the role slug declared by exactly C
  characters yields exactly C unit→role `crm:P67_refers_to` edges (one per matching
  character-scoped role node); an unmatched name yields exactly one
  unresolved-reference warning and no edge — with the unit still present in the
  graph in both cases. Repeated role names within a single card are
  slug-deduplicated before resolution, so they do not inflate the edge count.
- **SC-005**: The ingestion-parity test passes with the orphan set reduced to
  exactly `{NarrativeSequence, RelationshipRole, PsychologicalState}` and the
  reachable set extended with `NarrativeUnit` and `NarrativeFunction`.
- **SC-006**: A project that has no `outline/units/` directory builds with byte-for-
  byte the same graph it produced before this feature.
- **SC-007**: The regenerated `bookwright-outline` `SKILL.md` for both `claude` and
  `generic` documents the `outline/units/` card format and still triggers on
  Spanish and English author prompts (passes the existing skill lint gate).
- **SC-008**: After the change, no source docstring, authoring doc, or design-doc
  statement still describes `outline/` as *presently* wholly author-only: a search
  of those surfaces for the old framing returns only statements that name
  `outline/units/` as ingested, the design doc's § 7 tree lists
  `outline/units/`, and the design-doc skill-output table's `/bookwright-outline`
  row lists `outline/units/*.md` (with the same-class `/bookwright-bible`
  `bible/objects/*.md` omission also closed). Version-scoped historical records (the roadmap's "author-only
  *en v0.3*") are out of this search by design (FR-014) and remain unchanged.

## Assumptions

- **Outline ingestion reuses the bible mapper's machinery.** `outline/units/` is
  ingested by the same one-entity-per-file directory pass used for
  `bible/settings|locations|objects` (the precedent builders in
  `io/_bible_builders.py`, iterations 025–026). Whether the public entry point is
  an extended `map_bible` or a sibling `map_outline` is an implementation choice
  for `/speckit-plan`; the observable behaviour is identical.
- **Functions are minted; roles are resolved.** Mirroring the prompt: each
  `functions` name creates a deduplicated top-level `NarrativeFunction`
  (`narrative-function/<slug>`), while each `roles` name resolves against existing
  character-declared narrative roles and never mints a new entity.
- **Role resolution is by slug against character-scoped role nodes (multiplicity
  resolved — see Clarifications, Session 2026-06-19).** Character roles have
  character-scoped URIs (`{character}/role/{slug}`) and are emitted inline by the
  `Character` model, but they are exposed to **no** resolution index today — one
  must be built during the character pass (FR-005). Because one role slug may be
  played by several characters, a unit `roles` name resolves to **every** character
  role whose slug matches, emitting one unit→role edge per match; zero matches is a
  soft miss. The rejected alternatives — resolve to a single (necessarily minted or
  arbitrarily chosen) canonical role node, or mint a top-level role — were declined
  because each either adds an identity space the frozen ontology does not need
  (Principle X) or resolves non-deterministically; the chosen rule mints nothing
  and is deterministic. SC-004 now pins the resulting edge count.
- **Units are mapped after characters.** The role-resolution index must be
  populated by the character pass before the units pass runs, analogous to
  settings-before-locations.
- **Starter material is illustrative, not load-bearing.** The `outline/units/`
  scaffold seed mirrors `bible/settings/` (e.g. a `.gitkeep` and/or a sample
  card); its exact contents are an authoring nicety, not ingested truth.
- **Source files stay within the per-file size limit.** Any code added or split
  respects the ≤ 500-line rule (Principle IV), continuing the `bible.py` /
  `_bible_builders.py` split established in iteration 025.

## Out of Scope

- Narrative sequences (G7) and their ordering — iteration 029.
- `E55_Type` tagging of functions/roles to Propp/Greimas vocabularies —
  iteration 030.
- New validators over the narrative structure — iteration 031.
- Any new ontology class or property (Principle X) — G9/G10/P67 already exist.
- Unit attributes beyond `name`/`functions`/`roles`; ingestion of
  `outline/arcs.md`, `outline/structure.md`, `outline/synopsis.md`, or
  `outline/scenes.md` (these remain author-only prose).

## References

- `bookwright-design.md` § 4.2 (Narrative module: G9/G10/G11/G7), § 4.5 (URI
  generation for `narrative-unit` / `narrative-function`), § 7 (project structure,
  `outline/`; § 7.2/§ 7.3 are the locations/objects ingestion precedents).
- Constitution: Principle I (plain-text source of truth), Principle IV (≤ 500
  lines per file), Principle X (frozen ontology).
- Direct precedent in code: the settings/locations/objects builders in
  `io/_bible_builders.py` (iterations 025–026) and the inline materialization of
  `NarrativeRole` from a character's `narrative_roles:`.
