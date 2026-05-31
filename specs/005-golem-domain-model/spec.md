# Feature Specification: GOLEM Domain Model

**Feature Branch**: `005-golem-domain-model`

**Created**: 2026-05-30

**Status**: Draft

**Input**: User description: "Bookwright necesita representar el modelo de dominio narrativo (personajes, eventos, settings, relaciones, etc.) como objetos Python tipados que sepan cómo serializarse a RDF/Turtle según la ontología GOLEM."

## Clarifications

### Session 2026-05-30

- Q: How should canonical names be normalized into URI slugs — casing and
  accents? → A: **Lowercase and ASCII-only.** Accented and non-ASCII characters
  are transliterated to their closest ASCII form (`José Peña` → `jose-pena`,
  `La caída` → `la-caida`); letters are lowercased; runs of whitespace and
  separators collapse to a single hyphen; leading/trailing hyphens are stripped;
  a name that yields an empty slug is rejected. Chosen for maximally portable,
  tool-safe identifiers; design § 4.5 has been updated to document this rule
  explicitly. The indexer (iteration 6) owns any disambiguation.
- Q: What URI path segment do the nine concepts not listed in § 4.5 use? → A: A
  fixed per-concept lowercase-hyphenated segment (full table in FR-004), so that
  two different-typed entities sharing a slug do **not** collapse to the same
  identifier.
- Q: How are reified concepts that may lack a natural name identified
  (relationships, roles, narrative functions/roles)? → A: **Uniform model** —
  every entity except Attribute Assignment is constructed from a caller-supplied
  canonical name that is slugged; only Attribute Assignment uses a time-ordered
  UUIDv7 token. The model never synthesizes names from participants.

### Session 2026-05-31

- Q: How are the generated intermediate nodes (each `G17_Character_Feature`, its
  `E54_Dimension`, and each `G11_Narrative_Role`) identified — blank nodes or
  deterministic URIs? → A: **Deterministic URIs nested under the owning
  character**, never blank nodes: `{character}/feature/{slug(text)}` for
  free-text features, `{character}/feature/birth` and `{character}/feature/death`
  for the biographical features, `{character}/role/{slug(text)}` for narrative
  roles, and `{feature}/dimension` for a biographical feature's dimension. Chosen
  for: (a) byte-identical reproducibility (SC-002) — blank-node labels are
  assigned nondeterministically by the RDF library; (b) provenance — an Attribute
  Assignment (User Story 3) can only target an attribute *by identifier*, so
  feature/role nodes must be addressable across batches; (c) correctly scoped
  dedup — repeated values on the *same* character resolve to one node, while the
  same value on two characters yields two distinct, character-scoped nodes
  (top-level/global URIs would wrongly collapse them). The FR-006 slug rule
  applies to the text-derived suffixes; a feature/role text that slugs to empty
  is rejected.
- Q: How does a `G11_Narrative_Role` carry its role text (FR-018 was silent)? →
  A: On `rdfs:label`, mirroring the free-text feature pattern of FR-017, so roles
  are queryable by name.

## User Scenarios & Testing *(mandatory)*

The consumers of this capability are downstream parts of the toolkit — the
graph indexer (iteration 6) that will build instances from the bible and
manuscript, the validators (iteration 10) that will check coherence, and the
`graph` commands that will query the resulting RDF. This iteration delivers
**only** the typed domain model and its ability to emit triples; nothing reads
the manuscript and nothing validates semantic coherence yet.

### User Story 1 - Represent narrative concepts as typed objects with stable identity (Priority: P1)

A downstream component needs to create an in-memory object for each narrative
concept GOLEM defines — a character, an event, a setting, a relationship, a
narrative unit — and have that object carry a stable, project-scoped identifier
derived from the project's namespace and the entity's canonical name.

**Why this priority**: This is the foundation. Without typed objects that carry
stable identity, nothing downstream (indexing, querying, validation) can refer
to narrative entities consistently. It is the minimum viable slice: a library
that can construct the thirteen GOLEM concepts and hand back their identifiers.

**Independent Test**: Construct one instance of each GOLEM concept from a
canonical name and a project namespace base, and assert each produces the
expected stable identifier following the documented URI patterns. Re-running the
construction with the same inputs yields byte-identical identifiers.

**Acceptance Scenarios**:

1. **Given** a project namespace base of `https://example.org/my-book/` and a
   character with canonical name `Aparici`, **When** the character is
   constructed, **Then** its identifier is
   `https://example.org/my-book/character/aparici`.
2. **Given** the same namespace base and an event named `La caída del puente`,
   **When** the event is constructed, **Then** its identifier is
   `https://example.org/my-book/event/la-caida-del-puente`.
3. **Given** the same namespace base and a narrative location named `El faro`,
   **When** the location is constructed, **Then** its identifier is
   `https://example.org/my-book/location/el-faro`.
4. **Given** any two constructions of the same concept with the same canonical
   name and namespace base, **When** their identifiers are compared, **Then**
   they are identical (deterministic generation).
5. **Given** a constructed entity, **When** an attempt is made to change its
   canonical name, **Then** its already-generated identifier does not change
   (identifiers are immutable for the lifetime of the object).

---

### User Story 2 - Serialize entities to GOLEM-compatible RDF triples (Priority: P1)

A downstream component needs to turn the in-memory objects into RDF triples (and
ultimately Turtle) that line up with the GOLEM ontology frozen inside the
toolkit, so the project's knowledge graph can be persisted and queried.

**Why this priority**: Identity without serialization is inert. Emitting triples
that conform to GOLEM is the second half of the MVP — together with Story 1 it
lets the indexer produce a real graph. It is testable on its own once Story 1
exists.

**Independent Test**: Serialize one instance of each concept and assert the
emitted triples (a) declare the instance as an instance of the correct GOLEM
class, (b) use only classes and properties that exist in the frozen GOLEM
ontology, and (c) parse as well-formed RDF.

**Acceptance Scenarios**:

1. **Given** a constructed character, **When** it is serialized, **Then** the
   triples include a type assertion binding its identifier to the GOLEM
   character class, and every predicate used is defined in the frozen ontology.
2. **Given** a constructed entity that references another entity (for example a
   social relationship that connects two characters), **When** it is serialized,
   **Then** the cross-references appear as triples linking the participants'
   identifiers.
3. **Given** the serialized output of any entity, **When** it is parsed as RDF,
   **Then** parsing succeeds with no malformed triples.
4. **Given** a set of constructed entities, **When** they are serialized
   together, **Then** the output uses the registered short prefixes (such as the
   GOLEM, RDF, RDFS, CIDOC-CRM, and DOLCE/DUL prefixes) rather than expanded
   full identifiers.

---

### User Story 3 - Trace the provenance of inferred attributes (Priority: P2)

When an attribute is assigned to an entity, a downstream component needs to
record *where that assertion came from* — a path into the bible or the
manuscript — and optionally which prior assertion it was premised on, so the
toolkit can later distinguish what the text states from what an agent inferred.

**Why this priority**: Provenance is what makes the model trustworthy, but the
graph is useful before provenance is wired in. It builds directly on Stories 1
and 2 and is independently demonstrable.

**Independent Test**: Construct an attribute assignment recording (a) the
asserted attribute and its target entity, (b) a source path, and (c) optionally
a premise assertion; serialize it; assert the triples capture all three and that
the assignment carries its own UUID-based identifier.

**Acceptance Scenarios**:

1. **Given** an attribute assignment with target entity, asserted attribute, and
   source path `bible/characters/aparici.md`, **When** it is serialized,
   **Then** the triples record the target, the attribute, and the source path.
2. **Given** an attribute assignment whose source is a specific manuscript line,
   expressed as `manuscript/cap-04.md:42`, **When** it is serialized, **Then**
   the source path is preserved verbatim including the line locator.
3. **Given** an attribute assignment with no premise supplied, **When** it is
   serialized, **Then** the output is valid and simply omits the premise.
4. **Given** two attribute assignments constructed in sequence, **When** their
   identifiers are compared, **Then** both carry distinct identifiers under the
   `assertion/{uuid}` pattern and the identifiers sort in creation order.

---

### User Story 4 - Frozen, versioned GOLEM ontology bundled with the toolkit (Priority: P2)

The toolkit needs to carry a frozen copy of the GOLEM ontology so that
serialization targets a fixed, reproducible vocabulary, and so the exact
upstream provenance (which commit of the published ontology) is recorded.

**Why this priority**: Serialization in Story 2 has to validate against *some*
fixed vocabulary. Freezing it and recording its provenance is what makes runs
reproducible and auditable. It is a prerequisite of Story 2's "uses only terms
that exist in the frozen ontology" guarantee, but is called out separately
because it is its own deliverable (a vendored resource plus a version record).

**Independent Test**: Inspect the bundled ontology resource and assert it exists
at the documented location, that a version record accompanies it, and that the
version record names the upstream repository and the exact upstream commit
identifier it was taken from.

**Acceptance Scenarios**:

1. **Given** a fresh install of the toolkit, **When** the bundled schema
   directory is inspected, **Then** it contains the frozen GOLEM ontology for
   version 1.1.
2. **Given** the bundled ontology, **When** its accompanying version record is
   read, **Then** it names the upstream source repository and the exact upstream
   commit identifier the ontology was frozen from.
3. **Given** a future GOLEM release, **When** it is later vendored, **Then** it
   is added alongside the existing version without altering the frozen 1.1 copy.

---

### User Story 5 - Carry character attributes (born, died, features, narrative roles) as frozen-term triples (Priority: P1)

A downstream component (the indexer, iteration 6) needs to construct a Character
that carries its biographical years (`born`/`died`), its free-text `features`,
and its `narrative_roles`, and have the model emit those attributes as triples
that use **only** frozen GOLEM / CIDOC-CRM / DOLCE terms — so the knowledge graph
holds the narrative content of each character, not merely its identity.

**Why this priority**: An identity-only Character produces a near-empty graph
that cannot answer the toolkit's motivating queries (e.g. "characters born
before 1850") and blocks the temporal and character-presence validators
(iteration 10). The frozen ontology already defines a home for each of these
keys, so carrying them is the intended path, not an extension — and it is
foundational to iteration 6 having anything but bare identities to index. The
extension is additive: a Character constructed without these attributes still
serializes exactly as today.

**Independent Test**: Construct a Character with `born`, `died`, two free-text
features, and one narrative role; serialize it; assert each attribute is bound
through the documented frozen terms and that every predicate and class used is a
member of the frozen vocabulary. Construct a second Character with none of these
attributes and assert it still serializes to only its identity assertion.

**Acceptance Scenarios**:

1. **Given** a Character constructed with a free-text feature `ingeniero
   químico`, **When** it is serialized, **Then** the triples include a
   `G17_Character_Feature` instance linked from the character by
   `golem:GP0_has_feature`, carrying the text on `rdfs:label`.
2. **Given** a Character constructed with a narrative role `protagonist`,
   **When** it is serialized, **Then** the triples include a `G11_Narrative_Role`
   instance linked from the character by the `plays` property of the DOLCE
   **ExtendedDnS** namespace (`…/ExtendedDnS.owl#`) — distinct from the
   DOLCE-Lite namespace that carries `participant`.
3. **Given** a Character constructed with `born = 1828`, **When** it is
   serialized, **Then** the triples include a biographical
   `G17_Character_Feature` that is (a) typed via `crm:P2_has_type` to a stable
   `crm:E55_Type` individual denoting birth, and (b) bears a `crm:E54_Dimension`
   via `crm:P43_has_dimension` whose `crm:P90_has_value` is the literal
   `"1828"^^xsd:gYear`; the feature is linked from the character by
   `golem:GP0_has_feature`.
4. **Given** a Character constructed with `died = 1900`, **When** it is
   serialized, **Then** it produces the analogous death-typed
   feature → dimension → value chain with `"1900"^^xsd:gYear`.
5. **Given** any character-attribute serialization, **When** the emitted
   predicates and classes are checked against the frozen ontology, **Then** every
   one is a member of the frozen GOLEM closure — no term is minted outside it.
6. **Given** a Character constructed with none of these optional attributes,
   **When** it is serialized, **Then** only its identity assertion is emitted,
   preserving the identity-only behaviour of User Stories 1 and 2.

---

### Edge Cases

- **Canonical name that slugifies to empty** (e.g., a name made only of
  punctuation or symbols that carry no sluggable characters): construction must
  fail with a clear error rather than emit an identifier with an empty slug.
- **Two distinct entities sharing a canonical name within the same type**: they
  produce the *same* identifier by design. De-duplication and disambiguation are
  the caller's responsibility (the indexer, iteration 6); the model does not
  silently merge or silently diverge.
- **Canonical name with internal whitespace, mixed case, or accents**: spaces
  always collapse to single hyphens; accents and other non-ASCII characters are
  transliterated to ASCII and letters are lowercased; the rule must be
  deterministic so the same name always yields the same slug.
- **Renaming after construction**: produces a *new* identifier on a *new*
  object; reconciling old and new identifiers (migration) is explicitly out of
  scope for v0.
- **Entity types without a pattern listed in § 4.5** (object, psychological
  state, setting, relationship, relationship role, narrative unit, narrative
  function, narrative role, narrative sequence): each receives a fixed
  per-concept path segment, following the same `{segment}/{slug}` shape as the
  documented patterns (see the segment table in FR-004).
- **Attribute assignment referencing an entity that has no triples yet**: the
  assignment still serializes; it references the target by identifier and does
  not require the target to be materialized in the same batch.
- **Character with no optional attributes**: a Character constructed with neither
  `born`/`died`, nor `features`, nor `narrative_roles` serializes to its identity
  assertion alone; the attribute machinery is purely additive and emits nothing
  when the inputs are empty.
- **`plays` vs. `participant` namespace collision**: the `plays` property used
  for narrative roles lives in DOLCE **ExtendedDnS** (`…/ExtendedDnS.owl#`),
  which is a *different* namespace from the DOLCE-Lite (`…/DOLCE-Lite.owl#`)
  source of `participant`. The distinction is load-bearing — both MUST bind to
  distinct registered short prefixes, and `plays` MUST resolve to the ExtendedDnS
  term, not a DOLCE-Lite one.
- **`born`/`died` literal typing**: birth/death years serialize as
  `xsd:gYear`-typed literals on the dimension, never as plain strings or
  `xsd:integer`; this is what makes the iteration-10 temporal queries answerable.
- **Feature/role text that slugifies to empty**: a `features` or
  `narrative_roles` item made only of unsluggable characters has no valid URI
  suffix and MUST be rejected with a clear error (same rule as canonical names,
  FR-006/FR-021) rather than emitting a node with an empty suffix.
- **Duplicate feature/role values on one character**: identical `features` (or
  `narrative_roles`) entries on the *same* character resolve to a single shared
  node by construction (identity is derived from the slugged text, FR-021); the
  model does not emit duplicate nodes and does not need caller-side de-duplication.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The model MUST provide a distinct typed class for each of the
  thirteen GOLEM concepts in scope: Character, Object, Event, Psychological
  State, Setting, Narrative Location, Social Relationship, Relationship Role,
  Narrative Unit, Narrative Function, Narrative Role, Narrative Sequence, and
  Attribute Assignment (the inference concept). It MUST additionally provide the
  attribute-support carriers that the character-attribute mapping (FR-016–FR-020)
  requires — the constructible classes Character Feature
  (`G17_Character_Feature`, with its `G2_Feature` superclass) and Dimension
  (CIDOC-CRM `E54_Dimension`), plus stable `crm:E55_Type` **individuals**
  (birth/death) registered in the class-IRI map purely for the `rdf:type`
  assertion — which exist to *carry* attributes of the thirteen concepts, not as
  additional narrative concepts in their own right. Type is a controlled
  individual, **not** a constructible/exported class.
- **FR-002**: Each entity MUST be constructible from, at minimum, a project
  namespace base and a canonical name (Attribute Assignment excepted — see
  FR-009/FR-013).
- **FR-003**: Each entity MUST carry a stable identifier composed of the project
  namespace base, a type-specific path segment, and an identity token (a slug
  for named entities, a time-ordered unique token for attribute assignments).
- **FR-004**: The model MUST generate identifiers as `{base}{segment}/{token}`,
  using a fixed per-concept path segment and identity token:

  | Concept | Path segment | Identity token |
  |---|---|---|
  | Character | `character` | slug |
  | Object | `object` | slug |
  | Event | `event` | slug |
  | Psychological State | `psychological-state` | slug |
  | Setting | `setting` | slug |
  | Narrative Location | `location` | slug |
  | Social Relationship | `relationship` | slug |
  | Relationship Role | `relationship-role` | slug |
  | Narrative Unit | `narrative-unit` | slug |
  | Narrative Function | `narrative-function` | slug |
  | Narrative Role | `narrative-role` | slug |
  | Narrative Sequence | `narrative-sequence` | slug |
  | Attribute Assignment | `assertion` | UUIDv7 |

  The segments `character`, `event`, `location`, and `assertion` MUST match
  § 4.5 exactly; the remaining segments follow the same lowercase-hyphenated
  shape and MUST be stable across runs and releases.
- **FR-005**: Slug generation MUST be deterministic: the same canonical name and
  type always produce the same slug, and therefore the same identifier.
- **FR-006**: Slug generation MUST be lowercase and ASCII-only: accented and
  non-ASCII characters are transliterated to their closest ASCII form (`José` →
  `jose`, `caída` → `caida`), letters are lowercased, runs of whitespace and
  separators collapse to a single hyphen, and leading/trailing hyphens are
  stripped. A canonical name that yields an empty slug MUST be rejected with a
  clear error.
- **FR-007**: An entity's identifier MUST be immutable once generated: changing
  the canonical name of a constructed object MUST NOT mutate its existing
  identifier.
- **FR-008**: Each entity MUST be serializable to RDF triples that (a) assert
  the entity as an instance of its corresponding GOLEM class and (b) use only
  classes and properties defined in the frozen GOLEM ontology.
- **FR-009**: An Attribute Assignment MUST record the asserted attribute and its
  target entity, MUST record a source reference as a path (for example
  `bible/characters/aparici.md` or `manuscript/cap-04.md:42`), and MUST allow an
  optional premise assertion that, when present, is captured in the triples.
- **FR-010**: Serialized output across multiple entities MUST use a shared set
  of registered short prefixes covering at least the GOLEM base namespace and
  the common RDF, RDFS, CIDOC-CRM, DOLCE/DUL (DOLCE-Lite), DOLCE ExtendedDnS, and
  XSD prefixes (XSD for typed literals such as source paths and `xsd:gYear`
  values; ExtendedDnS as a prefix distinct from DOLCE-Lite — see FR-018).
- **FR-011**: The toolkit MUST bundle a frozen copy of the GOLEM 1.1 ontology as
  an internal resource and MUST accompany it with a version record that names
  the upstream repository and the exact upstream commit identifier it was frozen
  from.
- **FR-012**: Serialized triples for any entity MUST parse as well-formed RDF.
- **FR-013**: Attribute Assignment identifiers MUST use time-ordered unique
  tokens so that assignments created later sort after those created earlier and
  collisions do not occur.
- **FR-014**: The model MUST NOT read the bible or manuscript, and MUST NOT
  perform semantic coherence validation between instances; those are the
  responsibilities of later iterations (6 and 10 respectively).
- **FR-015**: Cross-references between entities (for example a relationship that
  connects two characters, or a narrative unit that participates in a sequence)
  MUST serialize as triples linking the referenced entities by their
  identifiers.
- **FR-016**: The Character class MUST be constructible, in addition to its
  canonical name, with these optional attributes — the same keys the documented
  character frontmatter exposes (`born`, `died`, `features`, `narrative_roles`):
  optional biographical years `born` and `died`, an optional collection of
  free-text features, and an optional collection of narrative roles. Supplying
  none of them MUST preserve identity-only serialization (FR-008 unchanged). The
  model does **not** read frontmatter (FR-014 stands); it provides the typed
  capability that iteration 6 populates from those keys.
- **FR-017**: Each free-text `features` item MUST serialize as a
  `G17_Character_Feature` instance, linked from the character by
  `golem:GP0_has_feature`, with the item text carried on `rdfs:label`. The instance
  MUST be identified by the deterministic URI `{character}/feature/{slug(text)}`
  (see FR-021); two identical feature texts on the same character therefore
  resolve to a single shared feature node.
- **FR-018**: Each `narrative_roles` item MUST serialize as a
  `G11_Narrative_Role` instance, linked from the character by the `plays`
  property of the DOLCE **ExtendedDnS** namespace
  (`http://www.ontologydesignpatterns.org/ont/dlp/ExtendedDnS.owl#`), which is
  distinct from the DOLCE-Lite namespace that supplies `participant`. The
  serializer MUST bind a registered short prefix for ExtendedDnS separate from
  the DOLCE-Lite prefix. The role instance MUST carry its role text on
  `rdfs:label` (mirroring FR-017) and MUST be identified by the deterministic URI
  `{character}/role/{slug(text)}` (see FR-021); identical roles on the same
  character resolve to a single shared role node.
- **FR-019**: `born` and `died` MUST each serialize as a biographical
  `G17_Character_Feature`, linked from the character by `golem:GP0_has_feature`,
  that (a) is typed via `crm:P2_has_type` to a stable `crm:E55_Type` individual
  denoting birth or death respectively, and (b) carries its year via
  `crm:P43_has_dimension → crm:E54_Dimension`, whose `crm:P90_has_value` is a
  literal typed `xsd:gYear`. The birth and death `E55_Type` individuals MUST have
  stable, reproducible identifiers (e.g. `{base}type/birth`, `{base}type/death`).
  The biographical features themselves MUST be identified by the deterministic
  URIs `{character}/feature/birth` and `{character}/feature/death`, and each
  feature's dimension by `{feature}/dimension` (see FR-021).
- **FR-020**: Every class and property the character-attribute mapping
  introduces — `G2_Feature`/`G17_Character_Feature`, `E54_Dimension`,
  `E55_Type`, `golem:GP0_has_feature`, ExtendedDnS `plays`, `crm:P2_has_type`,
  `crm:P43_has_dimension`, `crm:P90_has_value`, and `rdfs:label` — MUST be a
  member of the frozen GOLEM ontology closure; none may be minted outside it
  (this is the FR-008 / SC-003 guarantee extended to the new terms). Birth/death
  `E55_Type` individuals are individuals of a frozen class, not new vocabulary.
- **FR-021**: Every intermediate node introduced by the character-attribute
  mapping (each `G17_Character_Feature`, each `E54_Dimension`, each
  `G11_Narrative_Role`) MUST be identified by a deterministic, reproducible URI
  scoped under its owning character — **never** an anonymous blank node — using
  these patterns: free-text feature `{character}/feature/{slug(text)}`;
  biographical features `{character}/feature/birth` and
  `{character}/feature/death`; narrative role `{character}/role/{slug(text)}`; a
  biographical feature's dimension `{feature}/dimension`. The FR-006 slug rule
  applies to every text-derived suffix, and a feature/role text that slugs to
  empty MUST be rejected with a clear error. Because identity is derived from the
  text, two identical feature (or role) values on the *same* character resolve to
  a single shared node, while the same value on two *different* characters yields
  two distinct, character-scoped nodes (no cross-character collapse). This
  reproducible identity is what extends SC-002 to the generated nodes and what
  makes each attribute an addressable target for an Attribute Assignment
  (FR-009).

### Key Entities

- **Character**: A narrative agent (GOLEM `G1_Character`). Carries a canonical
  name and identity; participates in relationships and events. Optionally carries
  biographical years (`born`/`died`), free-text features, and narrative roles,
  each emitted through frozen terms (FR-016–FR-020).
- **Character Feature**: A biographical, physical, or psychological trait of a
  character (GOLEM `G17_Character_Feature`, a `G2_Feature`). Holds free text on
  `rdfs:label`, or — for biographical years — a `crm:E55_Type` (birth/death) and
  a `crm:E54_Dimension` value. Identified by a deterministic, character-scoped URI
  (`{character}/feature/{slug}` or `{character}/feature/{birth,death}`), never a
  blank node (FR-021).
- **Dimension**: A literal value carrier (CIDOC-CRM `E54_Dimension`) holding a
  typed value via `crm:P90_has_value` — e.g. a birth/death year as `xsd:gYear`.
- **Type**: A controlled type individual (CIDOC-CRM `E55_Type`) used to classify
  a feature, e.g. the stable `birth` and `death` individuals referenced by
  biographical features.
- **Object**: A narrative object (`G16_Object`) — an inanimate or non-agent
  entity that figures in the story.
- **Event**: A narrative event (`G5_Narrative_Event`) — a perduring happening in
  the story.
- **Psychological State**: A stative inner condition (`G3_Psychological_State`),
  distinguished from events by being non-perduring.
- **Setting**: The narrative universe (`G12_Setting`).
- **Narrative Location**: A place within the setting (`G13_Narrative_Location`).
- **Social Relationship**: A reified relationship between participants
  (`G4_Social_Relationship`).
- **Relationship Role**: A role a participant plays within a relationship
  (`G6_Relationship_Role`).
- **Narrative Unit**: A unit of narrative (`G9_Narrative_Unit`).
- **Narrative Function**: A function a unit performs (`G10_Narrative_Function`),
  e.g. Proppian functions, pluggable via controlled vocabularies.
- **Narrative Role**: A narrative role (`G11_Narrative_Role`). When attached to a
  character it carries its text on `rdfs:label` and is identified by the
  deterministic, character-scoped URI `{character}/role/{slug}` (FR-018/FR-021).
- **Narrative Sequence**: An ordering of narrative units (`G7_Narrative_Sequence`)
  — fabula/syuzhet.
- **Attribute Assignment**: A provenance record (CIDOC-CRM
  `E13_Attribute_Assignment`) tying an asserted attribute to a target entity,
  with a source path and an optional premise. Identified by a time-ordered token
  under `assertion/{uuid}`.
- **Namespace Registry**: The central catalogue of short prefixes (GOLEM base
  plus RDF, RDFS, CIDOC-CRM, DOLCE/DUL DOLCE-Lite, DOLCE ExtendedDnS, and XSD)
  used when serializing. DOLCE-Lite and ExtendedDnS are bound as distinct
  prefixes (FR-018).
- **Frozen Ontology Resource**: The vendored GOLEM 1.1 ontology plus its version
  record (upstream repository + commit identifier).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All thirteen GOLEM concepts in scope have a corresponding typed
  class — coverage is 13/13, with no concept missing and no *narrative concept*
  beyond scope added. The only additional classes are the attribute-support
  carriers Character Feature and Dimension (FR-001, FR-016–FR-020); birth/death
  are classified with stable `crm:E55_Type` **individuals**, not a new class.
  These carry attributes of those concepts rather than introducing new narrative
  concepts.
- **SC-002**: Identifier generation is 100% reproducible: constructing the same
  concept with the same canonical name and namespace base in independent runs
  yields byte-identical identifiers every time.
- **SC-003**: Every entity serializes to triples that use only terms present in
  the frozen GOLEM ontology — zero predicates or classes that are absent from
  the frozen vocabulary appear in any serialized output.
- **SC-004**: 100% of serialized entity outputs parse as well-formed RDF with no
  malformed triples.
- **SC-005**: The frozen ontology's version record uniquely and unambiguously
  identifies the upstream commit it was taken from, so any reviewer can
  reproduce the exact source bytes from that record alone.
- **SC-006**: 100% of attribute assignments record a source path, and any two
  assignments created in sequence carry distinct, creation-ordered identifiers.
- **SC-007**: A Character carrying `born`, `died`, free-text features, and
  narrative roles serializes so that every one of those attributes is reachable
  through the frozen terms named in FR-017–FR-019 (feature via
  `golem:GP0_has_feature`/`rdfs:label`; role via ExtendedDnS `plays`; year via the
  `crm:P2_has_type` + `crm:P43_has_dimension → E54_Dimension → crm:P90_has_value`
  `xsd:gYear` chain), and zero of the emitted predicates or classes fall outside
  the frozen ontology closure. Every generated feature/dimension/role node is a
  deterministic, character-scoped URI (never a blank node), so re-serializing the
  same Character yields byte-identical output (FR-021 extends SC-002). A Character
  with none of these attributes emits only its identity assertion.

## Assumptions

- **uri_base shape**: The project namespace base (`manifest.toml >
  bookwright.uri_base`) is, per iteration 2, guaranteed to be an absolute
  `http`/`https` URI ending in `/`. This model relies on that guarantee and does
  not re-validate it; identifiers are built by direct concatenation after the
  trailing slash.
- **Path segments for the nine concepts not enumerated in § 4.5**: resolved in
  Clarifications — each gets a fixed lowercase-hyphenated segment per the table
  in FR-004; cross-type slug collisions are thereby avoided by construction.
- **Slug rule precision**: resolved in Clarifications — slugs are lowercase and
  ASCII-only (accents transliterated, e.g. `José` → `jose`), spaces and
  separators collapse to single hyphens, empty results are rejected. Design
  § 4.5 in `bookwright-design.md` has been updated to document this ASCII-only
  rule (and the full per-concept segment table) explicitly.
- **Reified entities still take a canonical name**: resolved in Clarifications —
  relationships, roles, narrative units, etc. are constructed with a
  caller-supplied canonical name from which a slug is derived; the model does
  not synthesize names from participants. Only Attribute Assignment uses a
  generated time-ordered UUIDv7 token instead of a slug.
- **Serialization granularity**: "serialize to triples" means each entity can
  emit its own triples and a collection of entities can be emitted together as
  Turtle using the shared prefix registry; persisting to disk and querying are
  not part of this iteration.
- **No collision resolution**: identical canonical-name-plus-type collisions are
  surfaced as identical identifiers by design; resolving them belongs to the
  indexer (iteration 6).
- **Ontology acquisition is a one-time vendoring step**: the GOLEM TTL is
  fetched from the upstream repository and committed into the toolkit's
  resources during this iteration; the toolkit does not fetch it at runtime.

## Dependencies

- **Iteration 2 (Manifest model)**: supplies and validates `bookwright.uri_base`
  and `bookwright.schema_version`, which this model consumes as the namespace
  base and ontology version selector.
- **Upstream GOLEM ontology** (`github.com/GOLEM-lab/golem-ontology`): the source
  of the frozen 1.1 TTL; its commit identifier is recorded in the version record.

## Out of Scope

- Reading the bible or manuscript to build instances (iteration 6 — indexer).
- Semantic coherence validation between instances (iteration 10 — validators).
- Identifier migration when a canonical name changes (acknowledged future
  problem; not solved in v0).
- Controlled-vocabulary content (Propp, Greimas, Booker, essay structures): the
  model supports the pluggable-type pattern conceptually, but vendoring those
  vocabulary files is not part of this iteration.
- Persisting the graph to disk, building it, or querying it (later `graph`
  commands).
