---
description: "Task list for Propp/Greimas vocabularies as E55_Type + references"
---

# Tasks: Propp/Greimas vocabularies as `E55_Type` + references

**Input**: Design documents from `specs/030-narrative-vocabularies/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/vocabulary-typing.md, quickstart.md

**Tests**: Included — Constitution Principle VIII mandates ≥ 80 % coverage and the plan/contract enumerate explicit test clauses (C1–C14). Test tasks are first-class here.

**Organization**: Tasks are grouped by user story. The shared vocabulary loader and pipeline wiring are Foundational (both stories depend on them); each story then populates its own vocabulary, types its own entity, and adds its own tests.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete-task dependency)
- **[Story]**: US1 (Propp functions), US2 (Greimas roles), US3 (references)
- File paths are exact and relative to repository root.

## Path Conventions

Single project, src-layout: `src/bookwright/…`, tests under `tests/…` at repo root (Constitution III).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Locate the reuse points so no new predicate/class is introduced.

- [X] T001 Confirm the typing constants are importable for reuse (no new constant): `HAS_TYPE` (= `crm:P2_has_type`) and `CLASS_IRI["Type"]` (= `crm:E55_Type`) — find their definitions under `src/bookwright/golem/` (as already used by `Source` and `CharacterFeature`'s biographical variant) and note the import path for T007/T013. Run `uv sync` to ensure the dev env is current.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The vocabulary loader and the pipeline threading that BOTH user stories consume. Vocabulary-agnostic — it does not depend on any story's TTL being populated.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Create `src/bookwright/io/vocabularies.py` (new, ~70 lines) per data-model §2 / research D2,D6,D7: define `VocabularyDataError` (subclass `BookwrightError` from `src/bookwright/errors.py`, no per-class serializer); `VocabularyIndex` value object holding `_by_slug: dict[str, URIRef]` with `resolve(name) -> URIRef | None` (`make_slug(name)` via `golem.slug.make_slug`, dict lookup, `None` on no-match / `EmptySlugError`); `load_vocabulary(name) -> VocabularyIndex` (`@lru_cache`, read `bookwright.resources.vocabularies/{name}.ttl` via `importlib.resources`, parse with `rdflib`, build index from every `?t a crm:E55_Type ; rdfs:label ?l`, raise `VocabularyDataError` if two terms slug-collide — FR-011); `KNOWN_VOCABULARIES: frozenset[str] = {"propp", "greimas"}`; `ActiveVocabularies` frozen record exposing `propp` / `greimas` (each `VocabularyIndex | None`); `load_active_vocabularies(active: list[str]) -> ActiveVocabularies` loading only names in `KNOWN_VOCABULARIES`, ignoring the rest silently (D7). MUST do no `golem` → `io` coupling; depends only on `golem.slug` + `rdflib` + `importlib.resources`.
- [X] T003 Add keyword-only typing params to the two mappers (default `None` ⇒ no typing ⇒ FR-008): `*, propp: VocabularyIndex | None = None` on `map_outline` in `src/bookwright/io/outline.py`, threaded down to `_mint_functions`; `*, greimas: VocabularyIndex | None = None` on `map_bible` in `src/bookwright/io/bible.py`, threaded down to the character pass / `_build_character`. No resolution logic yet — just thread the param so every existing caller keeps working unchanged.
- [X] T004 Wire activation in `src/bookwright/commands/_graph.py::build_project_graph`: call `load_active_vocabularies(manifest.vocabularies.active)` once, pass `vocabs.propp` into `map_outline(...)` and `vocabs.greimas` into `map_bible(...)`. (depends on T002, T003)
- [X] T005 [P] Loader unit tests in `tests/io/test_vocabularies.py` (new) — vocabulary-agnostic clauses: C5 (`load_active_vocabularies` ignores an unknown active name with no error and types nothing); `resolve` returns `None` for a no-match name and for an unsluggable name; the disjointness guard raises `VocabularyDataError` on a constructed/fixture TTL with two terms colliding on one slug (FR-011). Use a small in-test fixture graph or a tmp TTL so this does not depend on T006/T012 content. (depends on T002)

**Checkpoint**: Loader + wiring exist; with no vocabulary active the graph is byte-for-byte unchanged (the default-`None` path).

---

## Phase 3: User Story 1 - Narrative functions become recognized Propp functions (Priority: P1) 🎯 MVP

**Goal**: A `NarrativeFunction` (G10) minted from a unit card's `functions:` name that matches a canonical Propp term carries a `crm:P2_has_type` link to that term, reified as an `E13_Attribute_Assignment`; non-matching names stay identity-only.

**Independent Test**: Build a Propp-active project with a unit card naming `departure` (and one custom name); confirm the *departure* function has `P2_has_type → propp#function/departure` (+ the term `a crm:E55_Type` + a matching E13), the custom function has none, and the same project with Propp inactive produces zero typing.

- [X] T006 [P] [US1] Populate `src/bookwright/resources/vocabularies/propp.ttl` with the **31** `crm:E55_Type` function terms from research D9 — URI `<https://bookwright.dev/vocab/propp#function/{en-slug}>`, each `a crm:E55_Type ; rdfs:label "<EN>"@en, "<ES>"@es`; term #8 carries four labels (`"villainy"@en, "lack"@en, "fechoría"@es, "carencia"@es`). Remove the stub `propp:Function a owl:Class` line; keep the `propp:` prefix, add `crm:`/`rdfs:` prefixes, and add the `sources.ttl`-style header comment (terms are Bookwright's, outside the frozen `CLASS_IRI` closure). FR-001/FR-002.
- [X] T007 [P] [US1] Add the optional type field to `NarrativeFunction` (G10) in `src/bookwright/golem/modules/narrative.py` per data-model §3: `type_uri: URIRef | None = None`; override `to_triples()` to `yield from super().to_triples()` then, if `type_uri`, emit `(self.uri, HAS_TYPE, type_uri)` and `(type_uri, RDF.type, CLASS_IRI["Type"])`; override `derived_assertions()` to keep the identity assertion and, if `type_uri`, `yield DerivedAssertion(self.uri, type_uri, "functions")`. Entity stays frozen; `None` default ⇒ unchanged behavior. (uses constants from T001)
- [X] T008 [US1] Resolve the Propp type in `src/bookwright/io/outline.py::_mint_functions`: when the threaded `propp` index is not `None`, compute `type_uri = propp.resolve(raw_name)` and pass it into `NarrativeFunction(...)`. Slug-dedup of functions is unchanged — the first card to introduce a slug fixes the (deterministic) `type_uri`. (depends on T003, T007)
- [X] T009 [P] [US1] Golem-layer emission tests: in `tests/golem/test_triples.py` assert a `NarrativeFunction` with `type_uri` set emits both `(fn, P2_has_type, term)` and `(term, rdf:type, E55_Type)` and that `type_uri=None` emits neither; in `tests/golem/test_derived_assertions.py` assert the typed function yields the extra `DerivedAssertion` with `source_field="functions"`. (depends on T007)
- [X] T010 [US1] Outline typing tests in `tests/io/test_outline.py` (extend): C6 (Propp active + matching `functions:` name ⇒ typed), C7 (Spanish form `partida` types to the same term as `departure`), C8 (no-match ⇒ untyped, build succeeds, no error), C10 function-side (the typing link has a matching `E13_Attribute_Assignment` with target=function, attribute=term, source=unit-card path — minted functions carry `key_lines={}`), C11 (Propp inactive ⇒ a would-match name is not typed), C13 (two builds ⇒ identical links). (depends on T006, T008)
- [X] T011 [P] [US1] Propp loader/data test in `tests/io/test_vocabularies.py` (extend): `load_vocabulary("propp")` loads with no slug collision and yields exactly 31 terms (C1 Propp side), and `resolve("departure")`, `resolve("partida")`, `resolve("LACK")`, `resolve("carencia")` all return the single term #8 / matching term (C2/C4). (depends on T006)

**Checkpoint**: US1 fully functional — Propp functions are typed end to end and independently demonstrable (this is the MVP).

---

## Phase 4: User Story 2 - Narrative roles become recognized Greimas actants (Priority: P2)

**Goal**: A character-scoped `CharacterRole` (G11) minted from a character card's `narrative_roles:` name that matches a Greimas actant carries a `crm:P2_has_type` link to that actant term, reified as an E13 with a real `relpath:line` locator; non-matching roles stay identity-only.

**Independent Test**: Build a Greimas-active project whose character card has `narrative_roles: [sujeto]`; confirm that character's role node has `P2_has_type → greimas#actant/subject` (+ term `a crm:E55_Type` + an E13 pointing at the `narrative_roles:` line), and that without Greimas active the role node is untyped.

- [X] T012 [P] [US2] Populate `src/bookwright/resources/vocabularies/greimas.ttl` with the **6** `crm:E55_Type` actant terms from research D9 — URI `<https://bookwright.dev/vocab/greimas#actant/{slug}>` for subject/object/sender/receiver/helper/opponent, each `a crm:E55_Type ; rdfs:label "<EN>"@en, "<ES>"@es` (subject/sujeto, object/objeto, sender/destinador, receiver/destinatario, helper/ayudante, opponent/oponente). Remove the stub `greimas:Actant a owl:Class` line; keep the `greimas:` prefix, add `crm:`/`rdfs:` prefixes + the header comment. FR-001/FR-002.
- [X] T013 [P] [US2] Add the optional type field to `CharacterRole` (G11) in `src/bookwright/golem/modules/feature.py` per data-model §3: `type_uri: URIRef | None = None`; in `to_triples()` keep `rdf:type` + `rdfs:label` and, if `type_uri`, add `(self.uri, HAS_TYPE, type_uri)` and `(type_uri, RDF.type, CLASS_IRI["Type"])`. No `derived_assertions` on `CharacterRole` itself — its type E13 is emitted by its owner (T014). (uses constants from T001)
- [X] T014 [US2] Type the role nodes from the owning `Character` (G1) in `src/bookwright/golem/modules/character.py` per data-model §3 / research D5: add `role_types: dict[str, URIRef] = Field(default_factory=dict)` (role-slug → Greimas term, construction input only — emits no triples itself); in `model_post_init` build each `CharacterRole` with `type_uri=self.role_types.get(make_slug(text))`; in `derived_assertions()` keep the existing identity/feature/role assertions and, for each role with `role.type_uri`, `yield DerivedAssertion(role.uri, role.type_uri, "narrative_roles")`. (depends on T013)
- [X] T015 [US2] Resolve Greimas in `src/bookwright/io/_bible_builders.py::_build_character`: when the threaded `greimas` index is not `None`, compute `role_types = {make_slug(label): uri for label in roles if (uri := greimas.resolve(label))}` and pass it into `Character(...)`. (depends on T003, T014)
- [X] T016 [P] [US2] Greimas role-typing tests in `tests/io/test_bible.py` (extend) or new `tests/io/test_character_roles.py`: C9 (Greimas active + matching `narrative_roles:` name ⇒ role node typed; a non-matching role left untyped, no error), C10 role-side (the role typing link has a matching E13 with target=role node, attribute=term, source=`character-card:narrative_roles-line`), C11 (Greimas inactive ⇒ would-match role not typed). Verify typing attaches at materialization independent of any unit card's `roles:` reference (FR-005). (depends on T012, T015)
- [X] T017 [P] [US2] Greimas loader/data test in `tests/io/test_vocabularies.py` (extend): `load_vocabulary("greimas")` loads with no collision and yields exactly 6 terms (C1 Greimas side); `resolve("sender")` and `resolve("destinador")` return the same actant term (C2/C4). (depends on T012)

**Checkpoint**: US1 AND US2 both work independently — functions type against Propp, roles against Greimas; a project may activate either alone.

---

## Phase 5: User Story 3 - The author knows which names produce a typed entity (Priority: P3)

**Goal**: The two bundled references enumerate exactly the canonical match-names the typing step recognizes, so authors choose names that type rather than guessing — and that agreement is machine-checked in both directions (SC-005).

**Independent Test**: Open each reference; every "Canonical match-names" entry, used verbatim, yields a typed entity, and no term is present in one side but absent from the other.

- [X] T018 [P] [US3] Rewrite `src/bookwright/resources/commands/references/propp-functions.md` (FR-012 / research D10): replace the condensed 6-movement digest with a clearly delimited **"Canonical match-names"** section listing one `- <EN> / <ES>` line per the 31 terms (term #8 surfaces all four: villainy/lack · fechoría/carencia). Keep the dramatis-personae prose only as context, explicitly flagged "typed via Greimas actants, not a Propp match-name here" so it is not read as a match-name.
- [X] T019 [P] [US3] Update `src/bookwright/resources/commands/references/greimas-actants.md` (FR-012 / research D10): keep the existing prose and add a "Canonical match-names" section with the 6 `- <EN> / <ES>` lines (subject/sujeto … opponent/oponente).
- [X] T020 [US3] Reference↔vocabulary agreement test `tests/resources/test_vocabulary_references.py` (new): assert both TTLs parse and contain exactly 31 / 6 `crm:E55_Type` terms (C1) with ≥ 1 `@en` and ≥ 1 `@es` label each (C3); parse each reference's "Canonical match-names" section and assert **set-equality** (by `make_slug`) with the slugs the loader derives from the matching TTL — no name in the reference absent from the TTL and none in the TTL absent from the reference, both directions (C14 / SC-005). (depends on T006, T012, T018, T019)

**Checkpoint**: All three stories independently functional; references and vocabularies provably agree.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T021 No-regression proof (C12 / SC-003 / FR-008): add/extend a test (reuse the 028/029 no-vocab path) asserting that with `manifest.vocabularies.active = []` the narrative-function and narrative-role graph — triples and E13 reifications — is byte-for-byte the pre-feature output (zero `P2_has_type`, zero added E13s). Place alongside the relevant ingestion test in `tests/io/`.
- [X] T022 [P] Run the `quickstart.md` end-to-end check manually (scaffold a Propp+Greimas project, author one beat + one role, `graph build`, confirm C6/C7/C8/C9/C10 via `graph query` and by inspecting `bible/graph.ttl`); confirm no bare typing triple.
- [X] T023 Run all four CI gates green: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (full suite, ≥ 80 % coverage). Confirm every touched source file stays ≤ 500 lines (Principle IV) and `golem.ttl` is unchanged (SC-006).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup — BLOCKS both user stories. (T002 → T003 → T004; T005 after T002.)
- **US1 (Phase 3)** and **US2 (Phase 4)**: each depends only on Foundational. They are genuinely independent (a project can activate Propp or Greimas alone) and can proceed in parallel.
- **US3 (Phase 5)**: T020 depends on the populated TTLs (T006, T012) and the rewritten references (T018, T019); the reference rewrites (T018/T019) can begin as soon as the term sets are fixed (research D9, already decided).
- **Polish (Phase 6)**: after the stories whose behavior it validates.

### Within Each User Story

- US1: T006 ∥ T007 → T008 → (T009 ∥ T011) , T010.
- US2: T012 ∥ T013 → T014 → T015 → (T016 ∥ T017).
- US3: (T018 ∥ T019) → T020.

### Parallel Opportunities

- T006 ∥ T007 (TTL data vs. golem field — different files).
- T012 ∥ T013 (same shape on the Greimas side).
- T009 ∥ T011 within US1; T016 ∥ T017 within US2 (different files).
- T018 ∥ T019 (two independent reference files).
- Across stories: once Foundational is done, all of US1 and all of US2 can run concurrently.
- ⚠️ `tests/io/test_vocabularies.py` is appended by T005, T011, T017 — these are in sequential phases, so no in-file contention; do not run them as a single parallel batch.

---

## Parallel Example: User Story 1

```bash
# After Foundational completes, launch the two independent US1 starters together:
Task: "Populate src/bookwright/resources/vocabularies/propp.ttl with 31 E55_Type terms"   # T006
Task: "Add type_uri to NarrativeFunction in src/bookwright/golem/modules/narrative.py"     # T007

# After T008, launch the independent US1 test tasks together:
Task: "Golem emission/derived-assertion tests in tests/golem/test_triples.py + test_derived_assertions.py"  # T009
Task: "Propp loader/data test in tests/io/test_vocabularies.py"                              # T011
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → Phase 2 Foundational (loader + wiring; CRITICAL, blocks both stories).
2. Phase 3 US1 — Propp function typing end to end.
3. **STOP and VALIDATE**: build a Propp-active project, confirm typing + E13, confirm no-vocab no-regression. This alone delivers the named v0.4 "Propp" payoff.

### Incremental Delivery

1. Setup + Foundational → loader ready, default-`None` path proves zero regression.
2. US1 (Propp) → test independently → MVP.
3. US2 (Greimas roles) → test independently — adds the actant half on the same mechanism.
4. US3 (references) → machine-checked discoverability (SC-005).
5. Polish → no-regression proof, quickstart, all gates green.

---

## Notes

- [P] = different files, no incomplete-task dependency.
- The frozen ontology (`golem.ttl`, 17-class `CLASS_IRI`) MUST NOT change — terms are `E55_Type` individuals in `propp.ttl` / `greimas.ttl` only (Principle X / SC-006). T023 re-verifies.
- No new predicate or class: reuse `HAS_TYPE` (`crm:P2_has_type`) and `CLASS_IRI["Type"]` (`crm:E55_Type`), exactly as `Source`/`CharacterFeature` do (research D4).
- No `type:` authoring surface, no warning on no-match — both are deliberate negative requirements (FR-007, D8); do not add plumbing for them.
- A duplicate alias under `make_slug` is a vocabulary-data bug surfaced by the load-time guard — fix the label, never add tie-break logic (FR-011).
- Commit after each task or logical group (the `after_tasks` git hook will offer to commit this file).
