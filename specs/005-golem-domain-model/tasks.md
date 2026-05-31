---
description: "Task list for GOLEM Domain Model (iteration 5)"
---

# Tasks: GOLEM Domain Model

**Input**: Design documents from `/specs/005-golem-domain-model/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅,
contracts/golem_api.md ✅, quickstart.md ✅

**Tests**: INCLUDED. Constitution VIII makes test discipline a hard CI gate
(≥ 80 % coverage on `src/bookwright/golem/`), and plan.md § Project Structure
enumerates the `tests/golem/` suite. Each user story therefore carries its own
test tasks, written before / alongside its implementation.

**Organization**: Tasks are grouped by user story (US1–US5) so each story is
independently implementable and testable.

> **Scope note (US5 amendment, 2026-05-31).** Phases 1–7 below (T001–T039,
> User Stories 1–4) are **DONE and merged to `main`** — the identity-only model,
> serialization, provenance, and frozen ontology. They are kept here as the
> completed record; **do not re-plan or re-run them.** The new work is **User
> Story 5** (Phases 8–9, T040–T050): an **additive** extension that lets
> `Character` carry `born`/`died`/`features`/`narrative_roles` and emit them
> through frozen terms. US5 adds one module (`modules/feature.py`), fields on
> `Character`, and namespace/predicate constants — it changes no existing US1–US4
> behaviour and keeps every merged test green (a `Character` with no attributes
> still serializes to its identity assertion alone, US5-6).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: US1 / US2 / US3 / US4 / US5 (Setup, Foundational, Polish carry no label)
- Exact file paths are given in every task

## Path Conventions

Single-project src-layout (Constitution III): production code under
`src/bookwright/`, tests under `tests/` mirroring the package. Paths below are
absolute from the repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the empty `golem` package and test package skeleton so every
later module has a home.

- [X] T001 Create the `golem` package skeleton: empty `src/bookwright/golem/__init__.py`, `src/bookwright/golem/modules/__init__.py`, and `tests/golem/__init__.py` (the public re-exports in `golem/__init__.py` are filled incrementally by US1–US3).
- [X] T002 [P] Create the vendored-schema package markers so `importlib.resources` can address the resource: `src/bookwright/resources/schemas/__init__.py` and `src/bookwright/resources/schemas/golem-1.1/__init__.py`.
- [X] T003 [P] Create `tests/golem/conftest.py` with the shared `uri_base` fixture (`B = "https://example.org/my-book/"`); sample-entity fixtures are added by the story phases that introduce those classes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The base entity machinery (slug, URI, namespaces, frozen-type
triple) plus the vendored ontology resource. Every user story builds on these.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete. The
ontology resource (T008–T009) is vendored here — not under US4 — because US2's
term-closure test (a P1/MVP guarantee) and `namespaces.load_frozen_ontology()`
both depend on the resource existing. US4 then *verifies and exposes* it.

- [X] T004 Implement the error hierarchy in `src/bookwright/golem/errors.py`: `GolemError(Exception)` base and `EmptySlugError(GolemError)` carrying the offending name, with `.to_json()` returning `{"error": "golem_empty_slug", "name": <str>, "message": <str>}` (mirrors `src/bookwright/core/errors.py` shape — Principle IX).
- [X] T005 Implement `make_slug(name: str) -> str` in `src/bookwright/golem/slug.py` using `python-slugify` default mode (lowercase, ASCII transliteration, single-hyphen, trimmed); raise `EmptySlugError(name)` from `errors.py` when the result is empty (FR-005/006, D2). Depends on T004.
- [X] T006 Implement `src/bookwright/golem/namespaces.py`: `GOLEM`, `CRM`, `DLP`, `RDF`, `RDFS`, `XSD` `rdflib.Namespace` constants (IRIs per research D5), `bind_prefixes(graph: Graph) -> None` (FR-010), a `CLASS_IRI` map / per-class IRI access for the 13 concepts (FR-004 local names), and `load_frozen_ontology() -> Graph` + `frozen_terms() -> set[URIRef]` reading `resources/schemas/golem-1.1/golem.ttl` via `importlib.resources`. Hard-code IRIs; do not parse the TTL at import time (D5). `bind_prefixes` binds exactly one prefix per namespace — `golem` for `…/ontology#` (do **not** also rebind the TTL's native `gc:`/`:` alias) and `dlp` for the DOLCE-Lite-Plus layer — so serialized Turtle is deterministic (FR-010, US2-4).
- [X] T007 Implement the `GolemEntity` frozen Pydantic v2 base in `src/bookwright/golem/base.py`: `model_config = ConfigDict(frozen=True, extra="forbid", strict=True)`; fields `uri_base`, `name`; class-level `golem_class: URIRef` + `path_segment: str`; computed-once `slug` (via `make_slug`) and `uri = URIRef(f"{uri_base}{path_segment}/{slug}")` (FR-003/004/007, D1/D4); `to_triples() -> Iterable[tuple]` yielding at least `(self.uri, RDF.type, self.golem_class)` (FR-008). Depends on T004, T005, T006.
- [X] T008 Create the dev-only vendoring helper `scripts/update-golem-schema.py` that fetches `golem/golem_v1-1.ttl` from `github.com/GOLEM-lab/golem-ontology` at commit `f666128a9a29f39c9f23c96ae1c48023cc8e7898` and writes `golem.ttl`, `version.json`, and `VERSION` into the resource dir (deterministic generator over hand-copying — D9; runtime never fetches).
- [X] T009 Vendor the frozen ontology (run T008 or equivalent) into `src/bookwright/resources/schemas/golem-1.1/`: `golem.ttl` (frozen bytes), `version.json` (`{repository, commit, file, version_iri, version_info, retrieved}` per data-model.md), and `VERSION` containing `golem-1.1` (FR-011, D9). Depends on T008.

**Checkpoint**: Base entity + slug + namespaces + frozen ontology in place — user stories can begin.

---

## Phase 3: User Story 1 - Typed objects with stable identity (Priority: P1) 🎯 MVP

**Goal**: Construct one typed object per GOLEM concept, each carrying a
deterministic, immutable, project-scoped URI.

**Independent Test**: Construct one instance of each concept from a canonical
name + `uri_base` and assert each `.uri` matches the FR-004 segment table;
re-construction yields byte-identical URIs; reassigning `name` raises
`ValidationError` (identifier unchanged).

### Tests for User Story 1

- [X] T010 [P] [US1] Slug tests in `tests/golem/test_slug.py`: worked examples (`José Peña`→`jose-pena`, `La caída`→`la-caida`), determinism/idempotence, lowercase+ASCII, and a punctuation-only name raising `EmptySlugError` (FR-005/006, SC-002 edge case).
- [X] T011 [P] [US1] URI/identity tests in `tests/golem/test_uri.py`: the per-concept segment table for all 12 slugged concepts (FR-004), the US1 worked examples (`character/aparici`, `event/la-caida-del-puente`, `location/el-faro`), byte-identical re-construction (SC-002), and frozen-immutability — reassigning `name` raises `pydantic.ValidationError` and `.uri` is unchanged (FR-007, US1-5).

### Implementation for User Story 1

- [X] T012 [P] [US1] `src/bookwright/golem/modules/character.py`: `Character` (`golem:G1_Character`, segment `character`) and `Object` (`golem:G16_Object`, segment `object`), each subclassing `GolemEntity` with `golem_class` + `path_segment` constants (identity only in v0).
- [X] T013 [P] [US1] `src/bookwright/golem/modules/relationship.py`: `SocialRelationship` (`golem:G4_Social_Relationship`, segment `relationship`, field `participants: tuple[GolemEntity | URIRef, ...]`) and `RelationshipRole` (`golem:G6_Relationship_Role`, segment `relationship-role`, optional `relationship`). Define fields + constants here; linking-triple emission is added in US2.
- [X] T014 [P] [US1] `src/bookwright/golem/modules/event.py`: `NarrativeEvent` (`golem:G5_Narrative_Event`, segment `event`, optional `participants`) and `PsychologicalState` (`golem:G3_Psychological_State`, segment `psychological-state`, optional `bearer`). Fields + constants; linking added in US2.
- [X] T015 [P] [US1] `src/bookwright/golem/modules/setting.py`: `Setting` (`golem:G12_Setting`, segment `setting`) and `NarrativeLocation` (`golem:G13_Narrative_Location`, segment `location`, optional `setting`). Fields + constants; linking added in US2.
- [X] T016 [P] [US1] `src/bookwright/golem/modules/narrative.py`: `NarrativeUnit` (`golem:G9_Narrative_Unit`, segment `narrative-unit`, optional `functions`/`roles`), `NarrativeFunction` (`golem:G10_Narrative_Function`, segment `narrative-function`), `NarrativeRole` (`golem:G11_Narrative_Role`, segment `narrative-role`), `NarrativeSequence` (`golem:G7_Narrative_Sequence`, segment `narrative-sequence`, ordered `units`). Fields + constants; linking added in US2.
- [X] T017 [US1] Populate `src/bookwright/golem/__init__.py` re-exports for the 12 slugged classes, `GolemError`, `EmptySlugError`, and the `CONCEPTS` registry (concept name → class) for downstream introspection (contract § Importable surface). `to_turtle` and `AttributeAssignment` are appended in US2/US3. Depends on T012–T016.

**Checkpoint**: All 12 slugged concepts construct with correct, deterministic, immutable URIs — US1 fully testable.

---

## Phase 4: User Story 2 - Serialize to GOLEM-compatible RDF (Priority: P1)

**Goal**: Emit RDF triples (type assertion + cross-references) using only frozen-
ontology terms, serialize a collection to prefixed Turtle, and round-trip it.

**Independent Test**: Serialize one instance of each concept; assert (a) the
`rdf:type` triple binds it to the correct GOLEM class, (b) every predicate/class
used is in `frozen_terms()` (term closure), (c) the output parses as well-formed
RDF and round-trips isomorphically, and (d) `to_turtle` uses short prefixes.

### Tests for User Story 2

- [X] T018 [P] [US2] `tests/golem/test_namespaces.py`: assert `bind_prefixes` binds `golem`, `crm`, the DOLCE (`dlp`) prefix, `rdf`, `rdfs`, `xsd` (FR-010), and that every IRI in the `CLASS_IRI` map is present in `frozen_terms()` (closure backstop).
- [X] T019 [P] [US2] `tests/golem/test_triples.py`: for each concept, assert the `rdf:type` triple (FR-008); assert cross-reference triples link participants/units/bearer/setting by `.uri` (FR-015); assert **term closure** — every class/predicate emitted by `to_triples()` ∈ `frozen_terms()` (SC-003).
- [X] T020 [P] [US2] `tests/golem/test_turtle_roundtrip.py`: `to_turtle([...])` parses back via `rdflib.Graph().parse(format="turtle")` with no malformed triples and is isomorphic to the source graph (FR-012, SC-004); output uses short prefixes not expanded IRIs (US2-4).

### Implementation for User Story 2

- [X] T021 [US2] From the vendored `golem.ttl`, confirm the exact object-property IRIs for each cross-reference (participation, role↔relationship, location↔setting, state↔bearer, unit↔function/role, sequence↔units) **and the AttributeAssignment `source`/"used" property and `premise` property** per research D6/D7; record the chosen IRIs in `specs/005-golem-domain-model/data-model.md` and add any missing predicate constants to `src/bookwright/golem/namespaces.py`. Never coin a predicate. Depends on T009.
- [X] T022 [US2] Implement `to_turtle(entities: Iterable[GolemEntity]) -> str` in `src/bookwright/golem/serialize.py`: build a fresh `rdflib.Graph`, call `bind_prefixes`, add every entity's `to_triples()`, `serialize(format="turtle")` (D8); then export `to_turtle` from `src/bookwright/golem/__init__.py`. Depends on T021.
- [X] T023 [P] [US2] Add linking-triple emission to `src/bookwright/golem/modules/relationship.py`: `SocialRelationship.to_triples` yields one participation triple per participant (object = participant `.uri`); `RelationshipRole` links role→relationship — using the predicates confirmed in T021 (FR-015).
- [X] T024 [P] [US2] Add linking-triple emission to `src/bookwright/golem/modules/event.py`: `NarrativeEvent` participation triples; `PsychologicalState` links state→bearer (predicates from T021).
- [X] T025 [P] [US2] Add linking-triple emission to `src/bookwright/golem/modules/setting.py`: `NarrativeLocation` links location→setting (predicate from T021).
- [X] T026 [P] [US2] Add linking-triple emission to `src/bookwright/golem/modules/narrative.py`: `NarrativeUnit` links to functions/roles; `NarrativeSequence` yields one ordered part triple per unit (predicates from T021).

**Checkpoint**: Every entity serializes to closed, well-formed, prefixed Turtle — US1 + US2 (the MVP) work independently.

---

## Phase 5: User Story 3 - Provenance of inferred attributes (Priority: P2)

**Goal**: An `AttributeAssignment` that records target, asserted attribute, a
verbatim source path, an optional premise, and carries a time-ordered UUIDv7 id.

**Independent Test**: Construct an assignment with target + attribute + source
(`bible/characters/aparici.md` and `manuscript/cap-04.md:42`); serialize it;
assert the triples capture target/attribute/source verbatim, omit the premise
when `None`, and that two sequential assignments carry distinct, creation-ordered
`assertion/{uuid}` ids.

### Tests for User Story 3

- [X] T027 [US3] `tests/golem/test_inference.py`: source path preserved verbatim incl. line locator `:42` (US3-1/2); premise omitted when `None` (US3-3); `assertion/{uuid}` token shape; two sequential assignments produce distinct ids that sort in creation order (FR-013, SC-006, US3-4); target/attribute/source triples present (FR-009).

### Implementation for User Story 3

- [X] T028 [US3] Implement `AttributeAssignment` in `src/bookwright/golem/modules/inference.py` (`crm:E13_Attribute_Assignment`, segment `assertion`): override token generation to `uuid_utils.uuid7()` (frozen once at construction — D3); fields `target`, `attribute` (required), `source: str` (verbatim, required), `premise` (optional); `to_triples` emits `P140_assigned_attribute_to`, `P141_assigned`, the source as an `xsd:string` literal via the ontology's source property, and the premise link only when present (FR-009/013, D7). Constructed without `name`.
- [X] T029 [US3] Export `AttributeAssignment` from `src/bookwright/golem/__init__.py` and add it to the `CONCEPTS` registry (13/13 — SC-001). Depends on T028.

**Checkpoint**: Provenance records serialize correctly; all 13 concepts present.

---

## Phase 6: User Story 4 - Frozen, versioned ontology made observable (Priority: P2)

**Goal**: Verify the vendored ontology + provenance record (produced in
Foundational T008–T009) and expose the schema label through `bookwright version`,
renaming the iteration-2 `golem-1.0` default to `golem-1.1`.

**Independent Test**: Inspect `resources/schemas/golem-1.1/`; assert `golem.ttl`
exists and `version.json` names the upstream repository and the exact commit
(SC-005); `bookwright version --json` reports `golem-1.1`.

### Tests for User Story 4

- [X] T030 [US4] `tests/golem/test_frozen_ontology.py`: assert `golem.ttl` exists at `resources/schemas/golem-1.1/` and parses; assert `version.json` names `repository` and the exact `commit` it was frozen from, plus `version_iri`/`version_info` (FR-011, SC-005, US4-1/2).

### Implementation for User Story 4

- [X] T031 [US4] Update `_read_golem_schema_version()` in `src/bookwright/commands/version.py` to read `resources/schemas/golem-1.1/VERSION` (today it reads the non-existent `schemas/golem/VERSION` and returns `"unknown"`) — D10. Still emits a single JSON document (Principle IX).
- [X] T032 [P] [US4] Update expected value in `tests/test_cli_version.py` and `tests/test_cli_subprocess.py`: `golem_schema_version` `"unknown"` → `"golem-1.1"` (D10).
- [X] T033 [P] [US4] Update `schema_version` default in `src/bookwright/resources/templates/manifest.template.toml`: `golem-1.0` → `golem-1.1` (D11).
- [X] T034 [P] [US4] Update `tests/core/test_load_valid.py` (assert at line ~21 + the inline TOML `schema_version` strings) and `tests/core/test_build.py` (assert at line ~38) to expect `golem-1.1` (D11).
- [X] T035 [P] [US4] Mechanically replace `schema_version = "golem-1.0"` → `"golem-1.1"` in the `tests/core/fixtures/*.toml` filler fixtures for repo-wide consistency (unvalidated free-text stamp — D11).

**Checkpoint**: Bundled ontology verified and reported; no `golem-1.0` ↔ `golem-1.1` mismatch remains.

---

## Phase 7: Polish & Cross-Cutting Concerns (US1–US4)

**Purpose**: Enforce the four CI gates and validate the quickstart for the merged
iteration-5 MVP.

- [X] T036 Confirm coverage ≥ 80 % on `src/bookwright/golem/`: `uv run pytest --cov=bookwright.golem --cov-report=term-missing`; add focused tests for any uncovered branch (Constitution VIII). Also add a guard test (e.g. `tests/golem/test_no_io.py`) asserting FR-014: constructing entities and calling `to_triples()`/`to_turtle()` performs no bible/manuscript or filesystem reads — the only resource the package opens is the vendored `golem.ttl` (via the term-closure/frozen-ontology helpers), and `bookwright.golem` imports no manuscript/bible reader.
- [X] T037 [P] `uv run ruff check` and `uv run ruff format --check` clean across the new modules, scripts, and tests.
- [X] T038 [P] `uv run mypy --strict src tests` clean (typed `to_triples` signatures, `URIRef` annotations, frozen-model configs).
- [X] T039 Walk `specs/005-golem-domain-model/quickstart.md` end-to-end (construct, link+serialize, provenance, error, `bookwright version --json`) and confirm each snippet behaves as documented.

---

## Phase 8: User Story 5 - Carry character attributes as frozen-term triples (Priority: P1)

> **ADDITIVE — US1–US4 are done and merged.** This phase extends the existing
> `Character` and `namespaces.py` and adds one new module (`modules/feature.py`).
> It must not change US1–US4 behaviour; every merged test stays green and a
> `Character` built with none of the four attributes still emits only its
> `rdf:type` triple (US5-6).

**Goal**: A `Character` accepts optional `born`/`died` (years), `features`
(free text), and `narrative_roles`, and emits each through **only** frozen
GOLEM / CIDOC-CRM / DOLCE ExtendedDnS terms, with every intermediate node carrying
a deterministic, character-scoped URI (never a blank node).

**Independent Test**: Construct a `Character` with `born`, `died`, two free-text
features, and one narrative role; serialize it; assert each attribute is reachable
through the documented frozen chain (`golem:GP0_has_feature`/`rdfs:label` for
features; `edns:plays`/`rdfs:label` for roles; `crm:P2_has_type` →
`crm:P43_has_dimension → crm:E54_Dimension → crm:P90_has_value "YYYY"^^xsd:gYear`
for years) and that every emitted term ∈ `frozen_terms()` (SC-007). Construct a
second `Character` with none of these attributes and assert it serializes to only
its identity assertion (US5-6).

### Tests for User Story 5 (write first — must FAIL before implementation)

- [X] T040 [P] [US5] Create `tests/golem/test_character_attributes.py` covering the US5 acceptance matrix: free-text feature → `golem:G17_Character_Feature` linked by `golem:GP0_has_feature` with text on `rdfs:label` (US5-1, FR-017); narrative role → `golem:G11_Narrative_Role` linked by `edns:plays` with text on `rdfs:label` (US5-2, FR-018); `born=1828` → biographical `G17` typed `crm:P2_has_type` an `crm:E55_Type` birth individual + `crm:P43_has_dimension → crm:E54_Dimension` whose `crm:P90_has_value` is `Literal("1828", datatype=XSD.gYear)` (US5-3, FR-019); `died=1900` analogous (US5-4); deterministic character-scoped URIs `{c.uri}/feature/{slug|birth|death}`, `{feature}/dimension`, `{c.uri}/role/{slug}` with dedup of identical values on one character (FR-021); a feature/role text that slugs to empty raises `EmptySlugError` (FR-021); a `Character` with no attributes emits only its `rdf:type` triple (US5-6).
- [X] T041 [P] [US5] Extend `tests/golem/test_namespaces.py` (additive assertions only): `bind_prefixes` binds `edns`, **distinct from `dlp`** (FR-010/FR-018); the new `CLASS_IRI` entries (`CharacterFeature`→`golem:G17_Character_Feature`, `Dimension`→`crm:E54_Dimension`, `Type`→`crm:E55_Type`) and the new predicate constants (`HAS_FEATURE`=`golem:GP0_has_feature`, `PLAYS`=`edns:plays`, `HAS_TYPE`=`crm:P2_has_type`, `HAS_DIMENSION`=`crm:P43_has_dimension`, `HAS_VALUE`=`crm:P90_has_value`) are all ∈ `frozen_terms()` (FR-020).
- [X] T042 [P] [US5] Extend `tests/golem/test_uri.py` (additive assertions only): the nested character-scoped URI patterns for feature/dimension/role nodes are correct and immutable (FR-021); the birth/death `crm:E55_Type` individuals carry the stable project-scoped URIs `{uri_base}type/birth` / `{uri_base}type/death` and are shared (deduped) across characters (FR-019); and re-serializing the same attributed `Character` is byte-identical (SC-007 extends SC-002).
- [X] T043 [P] [US5] Extend `tests/golem/test_triples.py` (additive assertions only): add an attributed `Character` to the closure loop so SC-003 covers `G17`/`E54`/`E55`/`golem:GP0_has_feature`/`edns:plays`/`crm:P2_has_type`/`crm:P43_has_dimension`/`crm:P90_has_value`/`rdfs:label` (US5-5, FR-020).
- [X] T044 [P] [US5] Extend `tests/golem/test_turtle_roundtrip.py` (additive assertions only): an attributed `Character` round-trips isomorphically through `to_turtle` → `rdflib.parse` with no malformed triples and the `xsd:gYear` literal preserved (FR-012, SC-004/SC-007).

### Implementation for User Story 5

- [X] T045 [US5] Extend `src/bookwright/golem/namespaces.py` (append only — keep existing constants/bindings): add the `EDNS` `rdflib.Namespace` (`http://www.ontologydesignpatterns.org/ont/dlp/ExtendedDnS.owl#`) and bind the short prefix `edns` in `bind_prefixes` **distinct from `dlp`** (FR-018); add predicate constants `HAS_FEATURE` (`golem:GP0_has_feature`), `PLAYS` (`EDNS.plays`), `HAS_TYPE` (`crm:P2_has_type`), `HAS_DIMENSION` (`crm:P43_has_dimension`), `HAS_VALUE` (`crm:P90_has_value`); extend the `CLASS_IRI` map with `CharacterFeature`→`golem:G17_Character_Feature`, `Dimension`→`crm:E54_Dimension`, `Type`→`crm:E55_Type` (FR-020). Hard-code IRIs; closure is asserted by T041/T043.
- [X] T046 [US5] Create `src/bookwright/golem/modules/feature.py` (≤500 lines, Principle IV) with the character-scoped attribute carriers, each subclassing `GolemEntity`, building `self._uri` from the owner URI + fixed suffix in `model_post_init` (not the `{base}{segment}/{slug}` triad), and owning its `to_triples()` (data-model.md § feature.py): `CharacterFeature` free-text variant (`{character.uri}/feature/{slug(label)}`, emits `rdf:type G17` + `rdfs:label`); `CharacterFeature` biographical variant (`{character.uri}/feature/{birth|death}`, emits `rdf:type G17`, `crm:P2_has_type {uri_base}type/{kind}`, the `{uri_base}type/{kind}` `rdf:type crm:E55_Type` assertion, `crm:P43_has_dimension` to its `Dimension`, plus the `Dimension`'s triples); `Dimension` (`{feature.uri}/dimension`, emits `rdf:type E54` + `crm:P90_has_value Literal(str(year), datatype=XSD.gYear)`); and the character-scoped narrative-role node (`{character.uri}/role/{slug(text)}`, emits `rdf:type G11` + `rdfs:label`). Reuse `make_slug` for text-derived suffixes (empty → `EmptySlugError`, FR-021). Depends on T045.
- [X] T047 [US5] Extend `Character` in `src/bookwright/golem/modules/character.py` (additive — keep identity-only path intact): add optional fields `born: int | None = None`, `died: int | None = None`, `features: tuple[str, ...] = ()`, `narrative_roles: tuple[str, ...] = ()`; in `model_post_init` (after the identity URI is fixed) build, once and deterministically, one biographical `CharacterFeature` per non-`None` `born`/`died`, one free-text `CharacterFeature` per `features` item (deduped by slug), and one role node per `narrative_roles` item (deduped by slug); declare `cross_refs` for `golem:GP0_has_feature` → every feature node and `edns:plays` → every role node; `Character.to_triples()` chains `super().to_triples()` (rdf:type + those edges) with each nested node's own `to_triples()`. Empty attributes → empty node tuples → identity-only output (US5-6, FR-016/021). Depends on T045, T046.
- [X] T048 [US5] Export `CharacterFeature` and `Dimension` from `src/bookwright/golem/__init__.py` (contract § Importable surface) — **do not** add them to the `CONCEPTS` registry; they are character-scoped attribute carriers, not one of the 13 concepts (SC-001). Depends on T046.

**Checkpoint**: An attributed `Character` serializes every attribute through closed, well-formed, character-scoped triples; an attribute-free `Character` is byte-identical to the merged US1/US2 output.

---

## Phase 9: Polish & Cross-Cutting Concerns (US5)

**Purpose**: Re-green every gate after the additive extension and validate the
new quickstart snippet.

- [X] T049 [US5] Validate `specs/005-golem-domain-model/quickstart.md` §2b (the born/died/features/roles example) executes and produces the documented Turtle shape (`golem:GP0_has_feature`, `edns:plays`, the `xsd:gYear` dimension chain, character-scoped node URIs).
- [X] T050 Re-run all four CI gates on the extended tree and resolve any finding: `uv run pytest` (incl. coverage ≥ 80 % on `src/bookwright/golem/`, exercising the new `feature.py` and `Character` branches, and the FR-014 `tests/golem/test_no_io.py` guard still holding — `feature.py` opens no manuscript/bible), `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict src tests` (typed `to_triples`/`URIRef`/frozen-model configs on the new module).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies. ✅ done.
- **Foundational (Phase 2)**: depends on Setup; **blocks all user stories**. T004→T005→T007; T006→T007; T008→T009. ✅ done.
- **US1 (Phase 3, P1)**: depends on Foundational. The MVP slice (identity). ✅ done.
- **US2 (Phase 4, P1)**: depends on Foundational + US1. Completes the MVP. T021→T022, T021→T023–T026. ✅ done.
- **US3 (Phase 5, P2)**: depends on Foundational. ✅ done.
- **US4 (Phase 6, P2)**: depends on Foundational T009. ✅ done.
- **Polish US1–US4 (Phase 7)**: depends on US1–US4. ✅ done.
- **US5 (Phase 8, P1 — additive)**: depends on the merged Foundational + US1/US2 (it extends `Character`, `namespaces.py`, and the closure/round-trip suites). Internal order: T045 → T046 → T047; T046 → T048; tests T040–T044 are written first and fail until T045–T048 land.
- **Polish US5 (Phase 9)**: depends on Phase 8 complete.

### Within User Story 5

- Tests (T040–T044) are written first and must FAIL before implementation.
- T045 (namespace + predicate constants) before the new module and the `Character` extension.
- T046 (`feature.py` carriers) before T047 (`Character` builds them) and before T048 (exports).
- Never coin a term: every new IRI in T045 is an existing member of `frozen_terms()`.

### Parallel Opportunities

- US5 tests T040, T041, T042, T043, T044 in parallel (distinct files).
- US5 implementation is mostly sequential (T045 → T046 → T047) because T047 imports the constants from T045 and the carriers from T046; T048 can run as soon as T046 exists.

---

## Parallel Example: User Story 5

```bash
# Tests for US5 together (distinct files):
Task: "tests/golem/test_character_attributes.py — full US5 acceptance matrix"
Task: "extend tests/golem/test_namespaces.py — edns + new CLASS_IRI/predicate closure"
Task: "extend tests/golem/test_uri.py — nested character-scoped URI patterns"
Task: "extend tests/golem/test_triples.py — attributed Character in closure loop"
Task: "extend tests/golem/test_turtle_roundtrip.py — attributed Character round-trip"
```

---

## Implementation Strategy

### MVP (US1 + US2) — DONE and merged

US1 + US2 (both P1) are the minimum viable model (construct 13 concepts, hand back
identifiers, serialize to closed Turtle). US3, US4, and their polish are also
merged.

### US5 increment (this amendment)

US5 is also P1 but lands as a separate additive increment because iteration 5 was
under-scoped: the identity-only `Character` cannot carry the documented
frontmatter that iteration 6 (indexer) and iteration 10 (validators) need.

1. Write US5 tests (T040–T044) → confirm they fail.
2. Add namespace/predicate constants (T045).
3. Add the `feature.py` attribute carriers (T046).
4. Extend `Character` to build + link them (T047) and export the carriers (T048).
5. **STOP and VALIDATE**: attributed `Character` round-trips through frozen terms;
   attribute-free `Character` is byte-identical to the merged output.
6. Polish (Phase 9): validate quickstart §2b, re-green all four gates → merge to
   `main`, then rebase iteration 6 onto it.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- US1–US4 (T001–T039) are **merged**; they are kept as the completed record, not
  re-run. The live work is **US5** (T040–T050).
- US5 is strictly **additive**: it mints no new vocabulary (every term ∈
  `frozen_terms()`, FR-020), adds no runtime dependency, and preserves
  identity-only serialization for an attribute-free `Character` (US5-6). If any
  merged US1–US4 test regresses, stop and revert — that behaviour is frozen.
- The model never reads the bible/manuscript and never validates semantic
  coherence (FR-014) — those are iterations 6 and 10. The `edns:plays` namespace
  trap (ExtendedDnS, **not** the DOLCE-Lite `dlp`) is load-bearing (FR-018).
- Commit after each task or logical group (optional auto-commit hooks apply).
