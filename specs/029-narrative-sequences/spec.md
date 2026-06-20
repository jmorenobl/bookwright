# Feature Specification: Outline ingestion — narrative sequences (G7)

**Feature Branch**: `029-narrative-sequences`

**Created**: 2026-06-20

**Status**: Draft

**Input**: User description: "After wiring units (G9) and functions (G10) from
`outline/units/`, the last class of the narrative-structure layer —
NarrativeSequence (G7) — is still unfed. The model already exists
(`golem/modules/narrative.py`: emits `dlp:proper-part` per member unit in
declared order). Bring narrative sequences (fabula/syuzhet, plot lines) into the
graph so beat order is citable by SPARQL, and remove G7 from the deferral
registry. Sequences are assembled unit-driven, from two new optional unit
frontmatter keys (`sequence`, `order`) — no separate `outline/sequences/`
directory. After this, the narrative-structure layer is complete."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plot beat order becomes queryable from authored unit cards (Priority: P1)

An author who has already broken the plot into beats (one card per beat under
`outline/units/`, iteration 028) now groups those beats into named plot lines —
a fabula, a syuzhet, a subplot — by adding two optional keys to a unit's
frontmatter: `sequence` (the plot line's name) and `order` (the beat's position
in that line). When the project graph is built, each distinct `sequence` name
becomes a single `NarrativeSequence` entity (identity only, deduplicated by
slug), and the units that name it become its members, linked by `dlp:proper-part`
in ascending `order`. The author (or a skill on their behalf) can now ask the
graph "what beats make up sequence X, and in what order" via SPARQL — the last
piece of the narrative-structure layer that was modelled-but-unfed is now alive.

**Why this priority**: This is the core value and the MVP. It is what takes G7
out of the deferral registry and completes the narrative-structure layer
(G7/G9/G10). Everything else (the authoring-surface update, the tie-break edge
rules) builds on sequences existing as entities with ordered members.

**Independent Test**: Create a project with three `outline/units/*.md` cards, two
of which carry `sequence: Act I` with `order: 1` and `order: 2` and a third with
no `sequence`; build the graph; confirm exactly one `NarrativeSequence` for
"Act I" with two `dlp:proper-part` edges (to the two members, ordered 1 then 2)
and that the third unit belongs to no sequence. Delivers a queryable, ordered
plot structure with no other change.

**Acceptance Scenarios**:

1. **Given** two unit cards with `sequence: Act I` and `order: 1` / `order: 2`
   respectively, **When** the graph is built, **Then** exactly one
   `NarrativeSequence` for "Act I" exists, with two `dlp:proper-part` edges to the
   two member units, assembled in ascending `order` (unit-1 before unit-2 in the
   builder's member tuple).
2. **Given** two unit cards in different sequences (`sequence: Act I` and
   `sequence: Act II`), **When** the graph is built, **Then** two distinct
   `NarrativeSequence` entities exist, each with a `dlp:proper-part` edge only to
   its own member.
3. **Given** several unit cards all naming `sequence: Fabula`, **When** the graph
   is built, **Then** exactly one `NarrativeSequence` entity for "Fabula" exists
   (deduplicated by slug) and every member unit is linked from it by
   `dlp:proper-part`.
4. **Given** a unit card with `name` but no `sequence` key, **When** the graph is
   built, **Then** the unit is built exactly as in iteration 028 and belongs to no
   sequence; no `NarrativeSequence` is minted on its account.

---

### User Story 2 - Existing projects and unsequenced units keep working unchanged (Priority: P1)

A project authored before this feature — or any project whose unit cards declare
no `sequence` — produces no `NarrativeSequence` entities and builds exactly as it
did under iteration 028. Adding sequence membership is purely additive: a unit
that gains a `sequence`/`order` pair keeps all of its iteration-028 behaviour
(its `NarrativeUnit` identity, its `functions`/`roles` edges) and merely joins a
sequence on top.

**Why this priority**: Backward compatibility is a release gate, not a nicety: the
parity test and every existing fixture must stay green, and the narrative-unit
contract from 028 must be untouched. It is co-equal P1 with US1 because shipping
US1 without this guarantee would regress existing graphs.

**Independent Test**: Build a project whose `outline/units/` cards declare no
`sequence` key; confirm the built graph is byte-for-byte identical to the graph
the same project produced before this feature, with zero `NarrativeSequence`
entities.

**Acceptance Scenarios**:

1. **Given** a project where no unit card has a `sequence` key, **When** the graph
   is built, **Then** no `NarrativeSequence` entity exists and the graph is
   identical to the pre-feature build.
2. **Given** a unit card that already had `name`/`functions`/`roles` and now also
   has `sequence`/`order`, **When** the graph is built, **Then** all of its
   iteration-028 triples are unchanged and only the sequence membership is added.

---

### User Story 3 - The authoring surface guides sequence/order on unit cards (Priority: P2)

An author invoking the `bookwright-outline` skill is instructed, when creating one
card per narrative unit, that a card may additionally declare `sequence` (the plot
line it belongs to) and `order` (its position in that line), so that beats group
into citable fabula/syuzhet/subplot sequences. The instruction is bilingual-safe
and re-materialized as `SKILL.md` for both `claude` and `generic` by the existing
pipeline.

**Why this priority**: Without this, the ingestion works but authors have no
guided path to declare sequence membership. It is the discoverability layer; the
engine behaviour (US1/US2) is independently valuable and testable before it lands.

**Independent Test**: Materialize integrations and confirm the regenerated
`bookwright-outline` `SKILL.md` (in both `claude` and `generic`) instructs the
optional `sequence`/`order` unit keys and still triggers on both Spanish and
English author prompts (passes the existing skill lint gate).

**Acceptance Scenarios**:

1. **Given** the updated `bookwright-outline` source command, **When** integrations
   are materialized, **Then** the `claude` and `generic` `SKILL.md` both instruct
   the optional `sequence`/`order` keys on unit cards and still trigger on Spanish
   and English author prompts.

---

### Edge Cases

- **Unit with `sequence` but no `order`** → placed **last** within its sequence
  (after explicit-`order` members), order-less members tie-broken by slug; never
  rejected, never a crash (FR-005, resolved in Clarifications).
- **Two members of the same sequence sharing the same `order`** → deterministic
  tie-break by slug among the equal-`order` members; never rejected, never a
  crash (FR-006, resolved in Clarifications).
- **`sequence` present but not a string** → unusable frontmatter for that key; the
  card is skipped with a recorded reason, build continues (consistent with the
  existing `functions`/`roles` non-list contract).
- **`order` present but not an integer** (e.g. a string, a float, a list) → unusable
  frontmatter; the card is skipped with a recorded reason, build continues.
- **`order` present but `sequence` absent** → `order` is meaningless without a
  sequence to position within; the lone `order` is ignored (a soft note) and the
  unit belongs to no sequence — it is not a fatal error.
- **A sequence slug that collides with the slug of an entity of a different type**
  (e.g. a character or a narrative unit named the same) → no collapse: the
  `NarrativeSequence` lives at its own URI segment (`narrative-sequence/<slug>`),
  a distinct identity space (design § 4.5).
- **A sequence whose only member card is itself skipped** (unusable frontmatter)
  → the sequence simply has no member from that card; if no surviving card names
  the sequence, no `NarrativeSequence` is minted.
- **Project with no `outline/units/` directory, or with units but no `sequence`
  keys** → no `NarrativeSequence` entities; the build is identical to today
  (US2).

## Clarifications

### Session 2026-06-20

- Q: A unit declares `sequence` but omits `order` — where does it sit in the
  member tuple? → A: **Placed last** within its sequence, deterministically:
  after every member with an explicit `order`, and among such order-less members
  ordered by slug. Never a crash. *Rationale*: mirrors the iteration-028 mapper
  ethos (optional keys degrade softly, the build continues), keeps `order`
  genuinely optional, and adds no new fatal-error class — lowest tech-debt path
  consistent with Principle I robustness.
- Q: Two members of the same sequence share the same `order` value — reject, or
  deterministic tie-break? → A: **Deterministic tie-break by slug** among
  equal-`order` members. Never a crash. *Rationale*: consistent with the
  missing-`order` decision's no-crash determinism, satisfies SC-004 (identical
  member tuple across builds) without filesystem/dict-iteration dependence, and
  treats a duplicate `order` as a soft authoring nicety rather than a build-
  aborting conflict.

The two `[NEEDS CLARIFICATION]` markers below (FR-005, FR-006) are hereby
resolved by these answers; the recommended defaults are adopted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A unit card's frontmatter MUST additionally accept two optional
  keys: `sequence` (a string naming the sequence the unit belongs to) and `order`
  (an integer giving the unit's position within that sequence). The recognised
  unit keys become `name`/`functions`/`roles`/`sequence`/`order`; any other key
  remains a soft `unknown_keys` warning as today.
- **FR-002**: For each distinct `sequence` name appearing across all unit cards,
  the system MUST materialize exactly one `NarrativeSequence` entity (identity
  only — no attributes beyond identity), deduplicated by slug across all units,
  with URI segment `narrative-sequence/<slug>`.
- **FR-003**: Each `NarrativeSequence` MUST emit one `dlp:proper-part`
  cross-reference (already declared on the `NarrativeSequence` model's
  `units` cross-ref) to each unit that names it, and to **only** those units. The
  members MUST be assembled in ascending `order`; the ordering is the builder's
  member-tuple order. RDF triples are unordered — the contract is the tuple the
  builder passes to the model, exactly as the existing `NarrativeSequence`
  contract specifies, not any triple ordering.
- **FR-004**: A unit card without a `sequence` key MUST belong to no sequence and
  MUST NOT cause any `NarrativeSequence` to be minted; its iteration-028 behaviour
  (identity, `functions`, `roles`) MUST be unchanged.
- **FR-005**: A unit that declares `sequence` but omits `order` MUST NOT be
  rejected and MUST NOT crash the build; it MUST be placed **last** within its
  sequence — after every member that has an explicit `order` — and, among the
  order-less members of the same sequence, ordered deterministically by slug. The
  result MUST be deterministic across builds. (Resolved in Clarifications,
  Session 2026-06-20.)
- **FR-006**: When two members of the same sequence share the same `order` value,
  the system MUST resolve the tie **deterministically by slug** (the equal-`order`
  members are ordered among themselves by slug) and MUST NOT reject the build or
  produce a member ordering that depends on filesystem or dict iteration order.
  (Resolved in Clarifications, Session 2026-06-20.)
- **FR-007**: `sequence` present but not a string, or `order` present but not an
  integer, MUST render the card non-ingestible (skipped with a recorded reason);
  the build MUST continue. (Booleans MUST NOT be accepted as integers for `order`.)
- **FR-008**: An `order` present without a `sequence` MUST NOT be a fatal error:
  the lone `order` is ignored and the unit belongs to no sequence (optionally a
  soft note records the ignored key).
- **FR-009**: A `NarrativeSequence` whose slug collides with the slug of an entity
  of a different type MUST NOT collapse into it — the sequence keeps its own
  `narrative-sequence/<slug>` URI segment, a distinct identity space (design § 4.5).
- **FR-010**: The structural provenance for each `NarrativeSequence` identity and
  for each sequence→unit `dlp:proper-part` assertion MUST be emitted uniformly
  through the existing derived-assertion → `crm:E13_Attribute_Assignment`
  mechanism, resolving the originating frontmatter field to a `relpath:line` source
  where locatable (consistent with iteration 028's unit/function provenance).
- **FR-011**: A project with no `outline/units/` directory, or whose unit cards
  declare no `sequence` key, MUST build byte-for-byte the same graph it produced
  before this feature, with zero `NarrativeSequence` entities (backward
  compatibility, US2).
- **FR-012**: The `bookwright-outline` source command MUST be updated to instruct,
  on a unit card, the two additional optional keys `sequence` (the plot line a unit
  belongs to) and `order` (its position in that line), and MUST be re-materialized
  as `SKILL.md` by the existing pipeline for both `claude` and `generic`, preserving
  bilingual (ES/EN) triggers. The added instructions MUST be written in the
  command's existing language (Spanish prose), matching the repository's language
  conventions for the source commands. **Every** in-file enumeration of the unit
  card's ingested keys MUST gain `sequence`/`order`, not just one — the command
  today lists the keys in two places (the per-unit instruction under "what to
  create" and the "Archivos a escribir" summary that reads
  `name`/`functions`/`roles`); both MUST be swept so neither still claims only the
  iteration-028 trio.
- **FR-013**: The deferral registry (`golem/deferrals.py`) MUST no longer list
  `NarrativeSequence`; the ingestion-parity test MUST stay green with G7 observed
  as alive (fed) and the orphan set reduced to exactly `{RelationshipRole (G6),
  PsychologicalState (G3)}`. Every count-bearing statement and pinned constant in
  the deferral module and the parity test MUST be updated in lockstep so nothing
  still claims three orphans where there are now two: the registry docstring's
  count prose ("Three of the thirteen" / "Exactly three entries"), the parity
  test's count prose ("Ten of the thirteen … the other three"), the reachable-set
  pin (`EXPECTED_REACHABLE`, which gains `NarrativeSequence`), the orphan-name set
  (`ORPHAN_NAMES`, which loses it), the version map (`EXPECTED_VERSIONS`), and the
  `len(DEFERRED_CONCEPTS) == 3` assertion (→ 2). The drift-simulation probes
  (`Character`, `NarrativeEvent`, `PsychologicalState`) name no now-fed concept, so
  they keep passing unchanged — the plan MUST confirm this rather than edit them.
- **FR-014**: The `parity-exercise` fixture MUST gain at least one
  `outline/units/*.md` card declaring a `sequence` (and `order`), so the live build
  actually observes `NarrativeSequence` as a reachable type — the parity test reads
  reachability from a real build, never a hand-list.
- **FR-015**: Every present-tense statement in the repository that documents the
  narrative-structure layer as having an unfed/orphan `NarrativeSequence` (G7), or
  that lists `outline/units/` as carrying only `name`/`functions`/`roles` (or as
  feeding only `NarrativeUnit`/`NarrativeFunction`), MUST be amended so G7 reads as
  alive and the unit card's `sequence`/`order` keys are documented — this is a debt
  class to sweep in full, not a single edit. The known surfaces, all of which
  iteration 028 maintained *per-iteration* (not at a milestone-close docs pass), are:
  (a) the deferral-registry docstring (`golem/deferrals.py`); (b) the parity-test
  docstring (`tests/golem/test_ingestion_parity.py`); (c) the canonical design doc
  (`bookwright-design.md` § 7.4 — which today reads "las secuencias narrativas G7
  … siguen aplazadas" and lists the unit frontmatter as `name`/`functions`/`roles`),
  which MUST gain the `sequence`/`order` unit keys and a note that G7 ingests
  unit-driven from `outline/units/` (no separate directory), mirroring how § 7.2/
  § 7.3 documented the locations/objects precedents; (d) the `io/manuscript.py`
  module docstring, which today states `outline/units/` cards "feed `NarrativeUnit`
  / `NarrativeFunction` entities" and MUST add that they also drive
  `NarrativeSequence`; (e) the authoring guide (`docs/authoring.md`), whose
  "desde v0.4 … alimentan unidades y funciones narrativas" note MUST add sequences;
  and (f) this pass's own engine module (`io/outline.py`), whose module-level and
  `map_outline` docstrings today describe the pass as mapping only
  `NarrativeUnit` / `NarrativeFunction` (G9/G10) and MUST add that the same pass now
  assembles `NarrativeSequence` (G7) from the unit cards' `sequence`/`order` keys
  (this surface is enumerated by SC-009 and swept by the engine module's own edit,
  not a separate docs pass).
  Version-scoped *historical / planning* statements that remain true — the roadmap's
  record of what was deferred *en v0.3*, the `README.md` "Planificado: v0.4" roadmap
  line (true until `v0.4.0` ships at iteration 032), and the
  `bookwright-implementation-plan.md` iteration ledger — are NOT swept; the debt
  class is only the *present-tense factual* claim that G7 is unfed.
- **FR-016**: No new ontology class or property may be added; `G7_Narrative_Sequence`
  and `dlp:proper-part` already exist (Principle X). The 17-class closure and
  `golem.ttl` MUST remain frozen. No separate `outline/sequences/` directory is
  introduced — sequences are assembled unit-driven from `outline/units/` (the
  dir-driven option is explicitly rejected, Out of Scope).

### Key Entities *(include if feature involves data)*

- **NarrativeSequence (G7)**: A narrative sequence — a fabula, a syuzhet, a plot
  line / subplot. Identity only (a slug of its `sequence` name); URI segment
  `narrative-sequence/<slug>`. Assembled, not authored as its own card: it is
  materialized from the set of unit cards that name it, and carries one
  `dlp:proper-part` edge to each member unit, members ordered ascending by `order`.
- **NarrativeUnit (G9)**: Unchanged from iteration 028 as an entity; its card's
  frontmatter now additionally recognises optional `sequence` (string) and `order`
  (integer) keys, which drive sequence assembly but add no attribute to the unit
  entity itself.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a project whose `outline/units/` cards reference S distinct
  `sequence` names total, a SPARQL query over the built graph returns exactly S
  `NarrativeSequence` entities.
- **SC-002**: A sequence named by exactly K surviving unit cards has exactly K
  `dlp:proper-part` edges, one to each member unit and to no other unit.
- **SC-003**: The members of a sequence are assembled in strictly ascending `order`
  (with the chosen FR-005/FR-006 rule applied to missing/duplicate `order`); the
  member tuple is identical across two independent builds of the same project.
- **SC-004**: A second, independent build of the same project yields byte-for-byte
  the same `NarrativeSequence` set and the same member ordering (determinism).
- **SC-005**: The ingestion-parity test passes with the orphan set reduced to
  exactly `{RelationshipRole, PsychologicalState}` and the reachable set extended
  with `NarrativeSequence`; `len(DEFERRED_CONCEPTS) == 2`.
- **SC-006**: A project that declares no `sequence` key on any unit card builds
  byte-for-byte the same graph it produced before this feature, with zero
  `NarrativeSequence` entities.
- **SC-007**: 100% of unit cards with an unusable `sequence` (non-string) or `order`
  (non-integer) value are skipped without aborting the build, and every skip carries
  a recorded reason.
- **SC-008**: The regenerated `bookwright-outline` `SKILL.md` for both `claude` and
  `generic` documents the optional `sequence`/`order` unit keys and still triggers
  on Spanish and English author prompts (passes the existing skill lint gate).
- **SC-009**: After the change, no present-tense source docstring (including
  `golem/deferrals.py`, `io/outline.py`, and `io/manuscript.py`), parity-test
  docstring, design-doc (§ 7.4), or authoring-guide (`docs/authoring.md`) statement
  still describes `NarrativeSequence` (G7) as an unfed orphan or lists `outline/units/`
  as carrying/feeding only the iteration-028 trio; a search of those surfaces returns
  only statements naming G7 as ingested and the unit card's `sequence`/`order` keys as
  recognised. Version-scoped historical/planning records (the roadmap, the `README.md`
  "Planificado: v0.4" line, the implementation-plan iteration ledger) are out of this
  search by design and remain unchanged.

## Assumptions

- **Sequence ingestion reuses the iteration-028 unit pass.** Sequences are
  assembled inside the same `outline/units/` one-entity-per-file pass that already
  builds `NarrativeUnit`/`NarrativeFunction` (`io/outline.py`), reading the two new
  keys off each unit card and assembling sequences after all cards are read.
  Whether the assembly is a second sweep over collected `(sequence, order, unit)`
  triples or an accumulating index is an implementation choice for `/speckit-plan`;
  the observable behaviour is identical.
- **Sequences are assembled, never authored as their own cards.** There is no
  `outline/sequences/` directory and no per-sequence card; a `NarrativeSequence`
  exists iff at least one surviving unit card names it. This is the unit-driven
  design the prompt chose over the dir-driven alternative.
- **`order` is a plain integer.** Positions are integers (booleans are not integers
  here); gaps and arbitrary starting values are allowed — only relative ascending
  order matters. Non-integer `order` makes the card non-ingestible (FR-007).
- **The `NarrativeSequence` model's `dlp:proper-part` contract is reused as-is.**
  The model already emits one `dlp:proper-part` per member in caller-tuple order
  (`golem/modules/narrative.py`); this feature only supplies the ordered member
  tuple — it adds no ontology and no new triple shape (Principle X / Principle IX).
- **Units already map after characters.** The character→role index ordering from
  iteration 028 is untouched; sequence assembly happens within/after the units pass
  and depends on no new pass ordering.
- **Source files stay within the per-file size limit.** Any code added to
  `io/outline.py` (or split out of it) respects the ≤ 500-line rule (Principle IV),
  continuing the `bible.py` / `_bible_builders.py` split established in iteration
  025.
- **Starter/fixture material is illustrative, not load-bearing.** The
  `parity-exercise` card(s) that exercise `sequence`/`order` are test scaffolding;
  their exact contents are a testing nicety, not ingested truth.

## Out of Scope

- A separate `outline/sequences/` directory or per-sequence authored cards — the
  dir-driven option is explicitly rejected in favour of unit-driven assembly.
- `E55_Type` tagging of functions/roles to Propp/Greimas vocabularies — iteration 030.
- New validators over the narrative structure (e.g. sequence continuity) —
  iteration 031.
- Any new ontology class or property (Principle X) — G7 and `dlp:proper-part`
  already exist.
- The two remaining orphans `RelationshipRole` (G6) and `PsychologicalState` (G3) —
  re-targeted/closed in iteration 032; they stay in the deferral registry after
  this iteration.
- Unit attributes beyond `name`/`functions`/`roles`/`sequence`/`order`; ingestion
  of `outline/arcs.md`, `outline/structure.md`, `outline/synopsis.md`, or
  `outline/scenes.md` (these remain author-only prose).

## References

- `bookwright-design.md` § 4.2 (Narrative module: G7 fabula/syuzhet, the
  `dlp:proper-part` member contract), § 4.5 (URI generation for
  `narrative-sequence`), § 7 (project structure, `outline/`; § 7.2/§ 7.3 are the
  locations/objects ingestion precedents for documenting a newly-fed surface).
- Constitution: Principle I (plain-text source of truth), Principle IV (≤ 500 lines
  per file), Principle X (frozen ontology).
- Direct precedent in code: the iteration-028 unit builder (`io/outline.py`,
  `_build_unit` / `_map_single_dir`) and the existing `NarrativeSequence`
  `dlp:proper-part` contract in `golem/modules/narrative.py`.
