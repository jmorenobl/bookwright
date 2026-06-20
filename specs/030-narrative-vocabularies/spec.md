# Feature Specification: Propp/Greimas vocabularies as `E55_Type` + references

**Feature Branch**: `030-narrative-vocabularies`

**Created**: 2026-06-20

**Status**: Draft

**Input**: User description: "Necesidad: la capa estructural narrativa ya entra al
grafo (G9/G10/G7), pero sus funciones y roles son entidades identity-only sin
semántica: una función llamada \"departure\" no se reconoce como la función
Proppiana correspondiente. GOLEM provee el patrón `E55_Type` para enchufar
vocabularios controlados sin extender el esquema (design § 4.4). Los TTL
`propp.ttl` y `greimas.ttl` existen como stubs (una sola clase cada uno).
Queremos poblarlos y enlazar funciones/roles a sus términos cuando la
constitución del proyecto active Propp o Greimas, dando a v0.4 su payoff
\"Propp/Greimas\" real."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Narrative functions become recognized Propp functions (Priority: P1)

An author writing a Propp-structured book has already broken the plot into beats
(`outline/units/*.md`, iteration 028), and several beats name structural
functions in their `functions:` list — `departure`, `interdiction`, `the
struggle`, or their Spanish equivalents. The author has declared, where the
project already records active narrative vocabularies, that **Propp** is in use.
When the project graph is built, each narrative function whose name matches a
canonical Propp function is no longer an opaque identity node: it carries a
"has type" link to the corresponding Propp term in the controlled vocabulary. A
skill, validator, or SPARQL query can now ask "which beats realize the
*departure* function?" and get an answer grounded in the shared vocabulary
rather than in fragile string comparison.

**Why this priority**: This is the core payoff of v0.4 and of this iteration —
turning the already-ingested-but-semantically-blank narrative-structure layer
into a *typed* one. Without it, the modelled functions stay inert. It is the
minimum that makes "Propp/Greimas" real and is independently demonstrable on a
single Propp project.

**Independent Test**: Build the graph for a project that (a) declares Propp
active and (b) has a unit card naming a function that matches a Propp term;
confirm the resulting narrative-function entity has a "has type" link to that
Propp term, and that the same project with Propp *not* declared produces the
function with no such link.

**Acceptance Scenarios**:

1. **Given** a project that declares Propp active and a unit card whose
   `functions:` includes a name matching a canonical Propp function, **When** the
   graph is built, **Then** the resulting narrative-function entity carries a
   "has type" link to that Propp vocabulary term.
2. **Given** the same project but with a function name that matches no Propp
   term, **When** the graph is built, **Then** that narrative function is created
   exactly as before (identity only, no "has type" link) and the build reports no
   error.
3. **Given** a unit card written with the Spanish form of a Propp function name,
   **When** the graph is built in a Propp-active project, **Then** the function is
   typed to the same Propp term as its English form would be (matching ignores
   case, accents, and ES/EN spelling).

---

### User Story 2 - Narrative roles become recognized Greimas actants (Priority: P2)

An author analyzing the conflict engine of their story assigns actantial roles to
their characters (`narrative_roles:` on a **character** card, `bible/characters/*.md`)
— *subject*, *object*, *sender*, *opponent*, or their Spanish forms — and has
declared **Greimas** active where the project already records active vocabularies.
When the graph is built, each character-scoped narrative-role node
(`golem:G11_Narrative_Role`, materialized once per distinct role a character
plays) whose name matches a Greimas actant gains a "has type" link to the
corresponding actant term, so the actantial structure of the book is queryable
rather than buried in identity-only nodes. (A unit card's `roles:` list only
*references* these nodes by slug; it mints no role entity, so it is the character
card's `narrative_roles:` that is the typed entity's source — see Assumptions.)

**Why this priority**: It is the second half of the Propp/Greimas payoff and
exercises the same typing mechanism on the role side. It is genuinely
independent — a project can activate Greimas without Propp — but functions
(US1) are the more common entry point, so it is P2.

**Independent Test**: Build the graph for a Greimas-active project whose character
card declares a `narrative_roles:` entry matching a Greimas actant; confirm the
resulting character-scoped role node has a "has type" link to that actant term,
and that without Greimas declared the role node stays untyped.

**Acceptance Scenarios**:

1. **Given** a project that declares Greimas active and a character card whose
   `narrative_roles:` includes a name matching a canonical Greimas actant,
   **When** the graph is built, **Then** the resulting character-scoped
   narrative-role node carries a "has type" link to that Greimas vocabulary term.
2. **Given** a Greimas-active project and a role name that matches no actant,
   **When** the graph is built, **Then** the role node is created as before with
   no "has type" link and no error.

---

### User Story 3 - The author knows which names produce a typed entity (Priority: P3)

Before writing function/role names, the author consults the bundled domain
references (`references/propp-functions.md`, `references/greimas-actants.md`,
already cited by the `bookwright-outline` skill). Those references enumerate the
exact canonical names that the typing step recognizes, so the author can choose
names that will be typed rather than guessing and silently producing untyped
nodes.

**Why this priority**: Discoverability closes the loop — typing is only useful if
authors know which names hit a term. It is a documentation deliverable that
depends on US1/US2 being defined first, hence P3.

**Independent Test**: Open each reference and confirm it lists the canonical
vocabulary names (the same set populated into the vocabulary files), so an author
following the reference produces typed entities.

**Acceptance Scenarios**:

1. **Given** the updated `references/propp-functions.md`, **When** an author uses
   a function name exactly as the reference enumerates it, **Then** the resulting
   narrative function is typed to the corresponding Propp term.
2. **Given** the updated `references/greimas-actants.md`, **When** an author uses
   an actant name exactly as the reference enumerates it, **Then** the resulting
   narrative role is typed to the corresponding Greimas term.

---

### Edge Cases

- **Neither vocabulary active (the default, and the iteration-028/029 baseline)**:
  every narrative function and role is produced identity-only, byte-for-byte as
  before this feature. No regression. (FR-008)
- **One vocabulary active, the other not**: only the active vocabulary types
  entities; a name that matches a term of the *inactive* vocabulary is never
  typed. (FR-011)
- **A name matches no term in any active vocabulary**: the entity is left
  untyped. This is normal authoring (custom functions, non-canonical roles), not
  an error, and produces no failure. (FR-006)
- **The same canonical function/role recurs**: typing is consistent. A function
  named on several unit cards is deduplicated into one `NarrativeFunction` entity
  (by slug, across all units) and so is typed exactly once. A role name played by
  several characters yields one role node per character; each node is typed
  independently to the same single vocabulary term.
- **A declared-active vocabulary name that is unknown** (neither `propp` nor
  `greimas`): handled by the project's existing active-vocabularies declaration
  semantics; this feature adds no new failure mode for it and simply types
  nothing for the unknown name. (FR-003)
- **Author writes an ambiguous/partial name** (e.g. a near-match or typo): it is
  treated as no-match → untyped, exactly like any other unrecognized name.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Propp vocabulary file MUST be populated with the canonical set
  of Propp narrative functions, each declared as a controlled-vocabulary type
  term (the `E55_Type` pattern), and the Greimas vocabulary file MUST be
  populated with the six actants of the actantial model as such terms.
- **FR-002**: All new vocabulary terms MUST live only in the separate Propp and
  Greimas vocabulary files (`propp.ttl` / `greimas.ttl`), never in the frozen
  GOLEM ontology (`golem.ttl`); this feature MUST NOT add any class to the
  frozen 17-class closure (Constitution Principle X).
- **FR-003**: Vocabulary activation MUST be read from where the project already
  declares it; this feature MUST NOT invent a new activation mechanism. (The
  exact existing source is captured as an assumption below and confirmed during
  clarify/plan.)
- **FR-004**: When Propp is active for the project, a narrative function whose
  resolved name matches a Propp function term MUST receive a "has type"
  (`crm:P2_has_type`) link to that term.
- **FR-005**: When Greimas is active for the project, a character-scoped
  narrative-role node (`golem:G11_Narrative_Role`, materialized from a character
  card's `narrative_roles:` list) whose resolved name matches a Greimas actant
  term MUST receive a "has type" (`crm:P2_has_type`) link to that term. The typing
  attaches to the role node at materialization and is independent of whether any
  unit card references it.
- **FR-006**: A narrative function or role whose name matches no term in any
  active vocabulary MUST be left untyped. This MUST NOT raise an error or abort
  the build.
- **FR-007**: Matching MUST be name-based only. Narrative functions
  (`functions:`) and character roles (`narrative_roles:`) are authored as bare
  strings with no per-item front-matter, so the entity's authored name is the
  sole match key; this iteration introduces **no** `type:` (or other) explicit
  type-override authoring surface (Scope discipline — no plumbing for a
  hypothetical future affordance).
- **FR-008**: When no vocabulary is active, the graph for narrative functions and
  roles MUST be identical to the iteration-028/029 output — no "has type" links,
  no other change (no regression).
- **FR-009**: An inactive vocabulary MUST NOT type any entity, even when an
  entity name would match one of its terms.
- **FR-010**: Name matching MUST be tolerant of case, accents, and ES/EN
  spelling so that the same conceptual function/role resolves to the same term
  regardless of the author's surface spelling.
- **FR-011**: Typing MUST be deterministic and stable across rebuilds: the same
  source + same active vocabularies produce the same set of "has type" links
  every time.
- **FR-012**: `references/propp-functions.md` and `references/greimas-actants.md`
  MUST be provided/updated so that the canonical names an author can use to
  obtain a typed entity are discoverable and consistent with the populated
  vocabulary terms.

### Key Entities *(include if feature involves data)*

- **Propp function term**: one controlled-vocabulary type term per canonical
  Propp narrative function, living in the Propp vocabulary file. Identified by a
  stable identifier and carrying the name(s) an author writes to match it.
- **Greimas actant term**: one controlled-vocabulary type term per actant of the
  actantial model (subject, object, sender, receiver, helper, opponent), living
  in the Greimas vocabulary file.
- **"Has type" link**: the relationship attached to a narrative function entity
  (G10) or character-scoped role node (G11) when its name matches an active
  vocabulary term, pointing the entity at that term. Absent when there is no match
  or the vocabulary is inactive.
- **Active-vocabularies declaration** *(existing, not introduced here)*: the
  project's existing statement of which narrative vocabularies are in use; read,
  not redefined, by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a Propp-active project, 100% of narrative functions whose names
  match a canonical Propp function are typed to the matching term, and 0% of
  non-matching functions are typed.
- **SC-002**: In a Greimas-active project, 100% of narrative roles whose names
  match a canonical Greimas actant are typed to the matching term, and 0% of
  non-matching roles are typed.
- **SC-003**: A project with no active vocabulary produces a narrative-function /
  narrative-role graph identical to the pre-feature (iteration 028/029) output —
  zero added links, zero changed entities.
- **SC-004**: Repeated builds of the same source with the same active
  vocabularies produce identical "has type" links every time (byte-for-byte
  stable output).
- **SC-005**: Every canonical name enumerated in the two reference documents, when
  used verbatim as a function/role name in an active project, yields a typed
  entity — the references and the populated terms agree with no orphan on either
  side.
- **SC-006**: The frozen ontology's class closure is unchanged by this feature
  (no class added to `golem.ttl`); all new terms reside in the separate
  vocabulary files.

## Assumptions

- **Activation source**: The machine-readable source of vocabulary activation is
  the project manifest's active-vocabularies list (the `[vocabularies] active`
  block already modelled by `VocabulariesBlock`), with the names `propp` and/or
  `greimas`. The constitution's prose "Vocabularios activos" section is the
  human-facing mirror of the same intent and is not machine-parsed. This is the
  only existing machine-readable mechanism, so FR-003 reuses it; the exact source
  is confirmed in `/speckit-clarify` / `/speckit-plan` per the iteration prompt.
- **Vocabulary → entity-kind binding**: `propp.ttl` is populated with Propp's
  narrative *functions* and matches the **`NarrativeFunction` (G10)** entities
  minted from unit cards' `functions:` lists (`io/outline.py::_mint_functions`).
  `greimas.ttl` is populated with the six *actants* and matches the
  **character-scoped `CharacterRole` (G11)** nodes minted from a character card's
  `narrative_roles:` list (`golem/modules/character.py` →
  `golem/modules/feature.py::CharacterRole`). A unit card's `roles:` list does
  **not** mint role entities — it only resolves to those existing character role
  nodes by slug (`io/outline.py::_resolve_roles`), so the role typing happens in
  the character pass, not the outline pass. (The top-level `NarrativeRole`
  *concept* in `CONCEPTS` is never instantiated by ingestion and is out of scope
  here — see DEBT.md DEBT-001.) Propp's seven spheres of action / dramatis
  personae are *not* populated as terms in this iteration (the prompt scopes
  propp.ttl to "las funciones Proppianas"); roles type against Greimas actants.
  Confirmed in clarify/plan.
- **Match key**: An entity's authored name is normalized via the project's
  existing slug rule (`golem/slug.py::make_slug`, `python-slugify` default:
  lowercase + ASCII transliteration, so case and accents fold away) and compared
  against the slug of each active term's identifier and its listed alias names.
  Case/accent tolerance comes from `make_slug`; ES/EN tolerance (FR-010) comes
  from each term carrying both an ES and an EN alias (as the existing references
  already pair them, e.g. *Destinador*/*sender*). The reference documents list
  the alias names that resolve.
- **No explicit `type:` field (FR-007)**: Narrative functions are authored as
  bare strings in a unit card's `functions:` list, and character roles as bare
  strings in a character card's `narrative_roles:` list — neither carries
  per-item front-matter. Name-based matching is therefore the **only** path, and
  this iteration adds no `type:` override surface. (FR-007 is a deliberate
  negative requirement, not an unbuilt affordance: adding a `type:` field would be
  plumbing for a hypothetical future, which Scope discipline forbids.)
- **No warning on no-match**: An unmatched name produces an untyped entity
  silently (no soft warning), consistent with "queda sin tipar (no es error)".
  Whether to emit an advisory note is a possible clarify item but defaults to
  silence to avoid noise on intentional custom names.
- **Provenance of the typing link**: How (and whether) the "has type" link is
  reified with the codebase's structural-provenance machinery is an
  implementation concern deferred to `/speckit-plan`; the spec requires only that
  the link exist.
- **Canonical Propp function set**: "The canonical set" is taken as Propp's
  standard 31 functions; the precise term inventory and their alias names are
  fixed during plan, consistent with the condensed repertoire already in
  `references/propp-functions.md`.

## Out of Scope

- **Other vocabularies** (e.g. Booker's seven basic plots, essay structures): not
  part of v0.4 and not addressed here.
- **Any new class in the frozen ontology** (Principle X): terms live in
  `propp.ttl` / `greimas.ttl`, never in `golem.ttl`.
- **Validators that consume the typing** (e.g. structural-continuity checks): that
  is iteration 031; this feature only produces the typing, it does not validate
  against it.
- **Populating Propp's dramatis personae / spheres of action as terms**: only the
  Propp functions and Greimas actants are populated this iteration.
- **Removing the vestigial top-level `NarrativeRole` concept**: the
  `NarrativeRole` entry in `golem.CONCEPTS` (`golem/modules/narrative.py`) is
  never instantiated by ingestion — only the inlined `CharacterRole` materializes
  the G11 class — yet it escapes the deferral registry because both share the same
  `CLASS_IRI`. Cleaning that up is a separate "modelled-but-dead concept" debt
  class, not the typing work of this iteration; it is recorded in DEBT.md
  (DEBT-001), not addressed here.

## Dependencies

- The narrative-structure ingestion of iterations 028 (units G9 / functions G10)
  and 029 (sequences G7) is on `main`; narrative functions and roles already
  enter the graph as identity-only entities. This feature types them.
- The `E55_Type` controlled-vocabulary pattern and the precedent of a separate
  `.ttl` vocabulary (`sources.ttl`, iteration 012) are reused as-is.
- Reference: `bookwright-design.md § 4.4` (controlled vocabularies via
  `E55_Type`), `§ 4.2` (Narrative module). Constitution Principle I (plain-text
  source of truth) and Principle X (frozen ontology).
