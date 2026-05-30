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

**Organization**: Tasks are grouped by user story (US1–US4) so each story is
independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: US1 / US2 / US3 / US4 (Setup, Foundational, Polish carry no label)
- Exact file paths are given in every task

## Path Conventions

Single-project src-layout (Constitution III): production code under
`src/bookwright/`, tests under `tests/` mirroring the package. Paths below are
absolute from the repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the empty `golem` package and test package skeleton so every
later module has a home.

- [ ] T001 Create the `golem` package skeleton: empty `src/bookwright/golem/__init__.py`, `src/bookwright/golem/modules/__init__.py`, and `tests/golem/__init__.py` (the public re-exports in `golem/__init__.py` are filled incrementally by US1–US3).
- [ ] T002 [P] Create the vendored-schema package markers so `importlib.resources` can address the resource: `src/bookwright/resources/schemas/__init__.py` and `src/bookwright/resources/schemas/golem-1.1/__init__.py`.
- [ ] T003 [P] Create `tests/golem/conftest.py` with the shared `uri_base` fixture (`B = "https://example.org/my-book/"`); sample-entity fixtures are added by the story phases that introduce those classes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The base entity machinery (slug, URI, namespaces, frozen-type
triple) plus the vendored ontology resource. Every user story builds on these.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete. The
ontology resource (T008–T009) is vendored here — not under US4 — because US2's
term-closure test (a P1/MVP guarantee) and `namespaces.load_frozen_ontology()`
both depend on the resource existing. US4 then *verifies and exposes* it.

- [ ] T004 Implement the error hierarchy in `src/bookwright/golem/errors.py`: `GolemError(Exception)` base and `EmptySlugError(GolemError)` carrying the offending name, with `.to_json()` returning `{"error": "golem_empty_slug", "name": <str>, "message": <str>}` (mirrors `src/bookwright/core/errors.py` shape — Principle IX).
- [ ] T005 Implement `make_slug(name: str) -> str` in `src/bookwright/golem/slug.py` using `python-slugify` default mode (lowercase, ASCII transliteration, single-hyphen, trimmed); raise `EmptySlugError(name)` from `errors.py` when the result is empty (FR-005/006, D2). Depends on T004.
- [ ] T006 Implement `src/bookwright/golem/namespaces.py`: `GOLEM`, `CRM`, `DLP`, `RDF`, `RDFS`, `XSD` `rdflib.Namespace` constants (IRIs per research D5), `bind_prefixes(graph: Graph) -> None` (FR-010), a `CLASS_IRI` map / per-class IRI access for the 13 concepts (FR-004 local names), and `load_frozen_ontology() -> Graph` + `frozen_terms() -> set[URIRef]` reading `resources/schemas/golem-1.1/golem.ttl` via `importlib.resources`. Hard-code IRIs; do not parse the TTL at import time (D5). `bind_prefixes` binds exactly one prefix per namespace — `golem` for `…/ontology#` (do **not** also rebind the TTL's native `gc:`/`:` alias) and `dlp` for the DOLCE-Lite-Plus layer — so serialized Turtle is deterministic (FR-010, US2-4).
- [ ] T007 Implement the `GolemEntity` frozen Pydantic v2 base in `src/bookwright/golem/base.py`: `model_config = ConfigDict(frozen=True, extra="forbid", strict=True)`; fields `uri_base`, `name`; class-level `golem_class: URIRef` + `path_segment: str`; computed-once `slug` (via `make_slug`) and `uri = URIRef(f"{uri_base}{path_segment}/{slug}")` (FR-003/004/007, D1/D4); `to_triples() -> Iterable[tuple]` yielding at least `(self.uri, RDF.type, self.golem_class)` (FR-008). Depends on T004, T005, T006.
- [ ] T008 Create the dev-only vendoring helper `scripts/update-golem-schema.py` that fetches `golem/golem_v1-1.ttl` from `github.com/GOLEM-lab/golem-ontology` at commit `f666128a9a29f39c9f23c96ae1c48023cc8e7898` and writes `golem.ttl`, `version.json`, and `VERSION` into the resource dir (deterministic generator over hand-copying — D9; runtime never fetches).
- [ ] T009 Vendor the frozen ontology (run T008 or equivalent) into `src/bookwright/resources/schemas/golem-1.1/`: `golem.ttl` (frozen bytes), `version.json` (`{repository, commit, file, version_iri, version_info, retrieved}` per data-model.md), and `VERSION` containing `golem-1.1` (FR-011, D9). Depends on T008.

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

- [ ] T010 [P] [US1] Slug tests in `tests/golem/test_slug.py`: worked examples (`José Peña`→`jose-pena`, `La caída`→`la-caida`), determinism/idempotence, lowercase+ASCII, and a punctuation-only name raising `EmptySlugError` (FR-005/006, SC-002 edge case).
- [ ] T011 [P] [US1] URI/identity tests in `tests/golem/test_uri.py`: the per-concept segment table for all 12 slugged concepts (FR-004), the US1 worked examples (`character/aparici`, `event/la-caida-del-puente`, `location/el-faro`), byte-identical re-construction (SC-002), and frozen-immutability — reassigning `name` raises `pydantic.ValidationError` and `.uri` is unchanged (FR-007, US1-5).

### Implementation for User Story 1

- [ ] T012 [P] [US1] `src/bookwright/golem/modules/character.py`: `Character` (`golem:G1_Character`, segment `character`) and `Object` (`golem:G16_Object`, segment `object`), each subclassing `GolemEntity` with `golem_class` + `path_segment` constants (identity only in v0).
- [ ] T013 [P] [US1] `src/bookwright/golem/modules/relationship.py`: `SocialRelationship` (`golem:G4_Social_Relationship`, segment `relationship`, field `participants: tuple[GolemEntity | URIRef, ...]`) and `RelationshipRole` (`golem:G6_Relationship_Role`, segment `relationship-role`, optional `relationship`). Define fields + constants here; linking-triple emission is added in US2.
- [ ] T014 [P] [US1] `src/bookwright/golem/modules/event.py`: `NarrativeEvent` (`golem:G5_Narrative_Event`, segment `event`, optional `participants`) and `PsychologicalState` (`golem:G3_Psychological_State`, segment `psychological-state`, optional `bearer`). Fields + constants; linking added in US2.
- [ ] T015 [P] [US1] `src/bookwright/golem/modules/setting.py`: `Setting` (`golem:G12_Setting`, segment `setting`) and `NarrativeLocation` (`golem:G13_Narrative_Location`, segment `location`, optional `setting`). Fields + constants; linking added in US2.
- [ ] T016 [P] [US1] `src/bookwright/golem/modules/narrative.py`: `NarrativeUnit` (`golem:G9_Narrative_Unit`, segment `narrative-unit`, optional `functions`/`roles`), `NarrativeFunction` (`golem:G10_Narrative_Function`, segment `narrative-function`), `NarrativeRole` (`golem:G11_Narrative_Role`, segment `narrative-role`), `NarrativeSequence` (`golem:G7_Narrative_Sequence`, segment `narrative-sequence`, ordered `units`). Fields + constants; linking added in US2.
- [ ] T017 [US1] Populate `src/bookwright/golem/__init__.py` re-exports for the 12 slugged classes, `GolemError`, `EmptySlugError`, and the `CONCEPTS` registry (concept name → class) for downstream introspection (contract § Importable surface). `to_turtle` and `AttributeAssignment` are appended in US2/US3. Depends on T012–T016.

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

- [ ] T018 [P] [US2] `tests/golem/test_namespaces.py`: assert `bind_prefixes` binds `golem`, `crm`, the DOLCE (`dlp`) prefix, `rdf`, `rdfs`, `xsd` (FR-010), and that every IRI in the `CLASS_IRI` map is present in `frozen_terms()` (closure backstop).
- [ ] T019 [P] [US2] `tests/golem/test_triples.py`: for each concept, assert the `rdf:type` triple (FR-008); assert cross-reference triples link participants/units/bearer/setting by `.uri` (FR-015); assert **term closure** — every class/predicate emitted by `to_triples()` ∈ `frozen_terms()` (SC-003).
- [ ] T020 [P] [US2] `tests/golem/test_turtle_roundtrip.py`: `to_turtle([...])` parses back via `rdflib.Graph().parse(format="turtle")` with no malformed triples and is isomorphic to the source graph (FR-012, SC-004); output uses short prefixes not expanded IRIs (US2-4).

### Implementation for User Story 2

- [ ] T021 [US2] From the vendored `golem.ttl`, confirm the exact object-property IRIs for each cross-reference (participation, role↔relationship, location↔setting, state↔bearer, unit↔function/role, sequence↔units) **and the AttributeAssignment `source`/"used" property and `premise` property** per research D6/D7; record the chosen IRIs in `specs/005-golem-domain-model/data-model.md` and add any missing predicate constants to `src/bookwright/golem/namespaces.py`. Never coin a predicate. Depends on T009.
- [ ] T022 [US2] Implement `to_turtle(entities: Iterable[GolemEntity]) -> str` in `src/bookwright/golem/serialize.py`: build a fresh `rdflib.Graph`, call `bind_prefixes`, add every entity's `to_triples()`, `serialize(format="turtle")` (D8); then export `to_turtle` from `src/bookwright/golem/__init__.py`. Depends on T021.
- [ ] T023 [P] [US2] Add linking-triple emission to `src/bookwright/golem/modules/relationship.py`: `SocialRelationship.to_triples` yields one participation triple per participant (object = participant `.uri`); `RelationshipRole` links role→relationship — using the predicates confirmed in T021 (FR-015).
- [ ] T024 [P] [US2] Add linking-triple emission to `src/bookwright/golem/modules/event.py`: `NarrativeEvent` participation triples; `PsychologicalState` links state→bearer (predicates from T021).
- [ ] T025 [P] [US2] Add linking-triple emission to `src/bookwright/golem/modules/setting.py`: `NarrativeLocation` links location→setting (predicate from T021).
- [ ] T026 [P] [US2] Add linking-triple emission to `src/bookwright/golem/modules/narrative.py`: `NarrativeUnit` links to functions/roles; `NarrativeSequence` yields one ordered part triple per unit (predicates from T021).

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

- [ ] T027 [US3] `tests/golem/test_inference.py`: source path preserved verbatim incl. line locator `:42` (US3-1/2); premise omitted when `None` (US3-3); `assertion/{uuid}` token shape; two sequential assignments produce distinct ids that sort in creation order (FR-013, SC-006, US3-4); target/attribute/source triples present (FR-009).

### Implementation for User Story 3

- [ ] T028 [US3] Implement `AttributeAssignment` in `src/bookwright/golem/modules/inference.py` (`crm:E13_Attribute_Assignment`, segment `assertion`): override token generation to `uuid_utils.uuid7()` (frozen once at construction — D3); fields `target`, `attribute` (required), `source: str` (verbatim, required), `premise` (optional); `to_triples` emits `P140_assigned_attribute_to`, `P141_assigned`, the source as an `xsd:string` literal via the ontology's source property, and the premise link only when present (FR-009/013, D7). Constructed without `name`.
- [ ] T029 [US3] Export `AttributeAssignment` from `src/bookwright/golem/__init__.py` and add it to the `CONCEPTS` registry (13/13 — SC-001). Depends on T028.

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

- [ ] T030 [US4] `tests/golem/test_frozen_ontology.py`: assert `golem.ttl` exists at `resources/schemas/golem-1.1/` and parses; assert `version.json` names `repository` and the exact `commit` it was frozen from, plus `version_iri`/`version_info` (FR-011, SC-005, US4-1/2).

### Implementation for User Story 4

- [ ] T031 [US4] Update `_read_golem_schema_version()` in `src/bookwright/commands/version.py` to read `resources/schemas/golem-1.1/VERSION` (today it reads the non-existent `schemas/golem/VERSION` and returns `"unknown"`) — D10. Still emits a single JSON document (Principle IX).
- [ ] T032 [P] [US4] Update expected value in `tests/test_cli_version.py` and `tests/test_cli_subprocess.py`: `golem_schema_version` `"unknown"` → `"golem-1.1"` (D10).
- [ ] T033 [P] [US4] Update `schema_version` default in `src/bookwright/resources/templates/manifest.template.toml`: `golem-1.0` → `golem-1.1` (D11).
- [ ] T034 [P] [US4] Update `tests/core/test_load_valid.py` (assert at line ~21 + the inline TOML `schema_version` strings) and `tests/core/test_build.py` (assert at line ~38) to expect `golem-1.1` (D11).
- [ ] T035 [P] [US4] Mechanically replace `schema_version = "golem-1.0"` → `"golem-1.1"` in the `tests/core/fixtures/*.toml` filler fixtures for repo-wide consistency (unvalidated free-text stamp — D11).

**Checkpoint**: Bundled ontology verified and reported; no `golem-1.0` ↔ `golem-1.1` mismatch remains.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Enforce the four CI gates and validate the quickstart.

- [ ] T036 Confirm coverage ≥ 80 % on `src/bookwright/golem/`: `uv run pytest --cov=bookwright.golem --cov-report=term-missing`; add focused tests for any uncovered branch (Constitution VIII). Also add a guard test (e.g. `tests/golem/test_no_io.py`) asserting FR-014: constructing entities and calling `to_triples()`/`to_turtle()` performs no bible/manuscript or filesystem reads — the only resource the package opens is the vendored `golem.ttl` (via the term-closure/frozen-ontology helpers), and `bookwright.golem` imports no manuscript/bible reader.
- [ ] T037 [P] `uv run ruff check` and `uv run ruff format --check` clean across the new modules, scripts, and tests.
- [ ] T038 [P] `uv run mypy --strict src tests` clean (typed `to_triples` signatures, `URIRef` annotations, frozen-model configs).
- [ ] T039 Walk `specs/005-golem-domain-model/quickstart.md` end-to-end (construct, link+serialize, provenance, error, `bookwright version --json`) and confirm each snippet behaves as documented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; **blocks all user stories**. T004→T005→T007; T006→T007; T008→T009.
- **US1 (Phase 3, P1)**: depends on Foundational. The MVP slice (identity).
- **US2 (Phase 4, P1)**: depends on Foundational + US1 (extends the concept classes with linking triples). Completes the MVP. T021→T022, T021→T023–T026.
- **US3 (Phase 5, P2)**: depends on Foundational (base, namespaces, serialize). Independent of US1/US2 class internals.
- **US4 (Phase 6, P2)**: depends on Foundational T009 (resource present). Independent of US1–US3.
- **Polish (Phase 7)**: depends on all desired stories being complete.

### Within Each User Story

- Tests are written before / alongside implementation and must fail first.
- Foundational base + namespaces before any concept class.
- US1 concept classes before US2 linking triples (US2 edits the same module files).
- T021 (confirm predicate IRIs) before any US2 linking-triple task.

### Parallel Opportunities

- Setup: T002, T003 in parallel.
- US1 tests T010, T011 in parallel; US1 modules T012–T016 in parallel (distinct files), then T017.
- US2 tests T018–T020 in parallel; after T021/T022, linking tasks T023–T026 in parallel (distinct module files).
- US4: T032, T033, T034, T035 in parallel (distinct files); T030 independent; T031 before T032.
- Polish: T037, T038 in parallel.

---

## Parallel Example: User Story 1

```bash
# Tests for US1 together:
Task: "Slug tests in tests/golem/test_slug.py"
Task: "URI/identity tests in tests/golem/test_uri.py"

# Concept-class modules for US1 together (distinct files):
Task: "character.py — Character, Object"
Task: "relationship.py — SocialRelationship, RelationshipRole"
Task: "event.py — NarrativeEvent, PsychologicalState"
Task: "setting.py — Setting, NarrativeLocation"
Task: "narrative.py — NarrativeUnit, NarrativeFunction, NarrativeRole, NarrativeSequence"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

Both US1 and US2 are P1 — together they are the minimum viable model (construct
13 concepts, hand back identifiers, serialize to closed Turtle).

1. Phase 1 Setup → Phase 2 Foundational (incl. vendoring the ontology).
2. Phase 3 US1 → validate identity independently.
3. Phase 4 US2 → validate serialization + term closure + round-trip.
4. **STOP and VALIDATE**: the indexer (iteration 6) can now build a real graph.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. + US1 (identity) → test → demo.
3. + US2 (serialization) → test → demo (MVP complete).
4. + US3 (provenance) → test → demo.
5. + US4 (ontology observability + golem-1.1 rename) → test → demo.
6. Polish → all four CI gates green → merge to `main`.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- The ontology resource is vendored in Foundational (not US4) because US2's
  term-closure guarantee (P1/MVP) depends on it; US4 verifies and exposes it.
- The model never reads the bible/manuscript and never validates semantic
  coherence (FR-014) — those are iterations 6 and 10.
- Commit after each task or logical group (optional auto-commit hooks apply).
