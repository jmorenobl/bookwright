---
description: "Task list for iteration 012 — Provenance Model (Source / Finding / Anchor)"
---

# Tasks: Provenance Model — Source / Finding / Anchor

**Input**: Design documents from `/specs/012-research-provenance-model/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓,
contracts/ ✓ (`research-format.md`, `provenance-graph.md`, `research-io.md`),
quickstart.md ✓

**Tests**: INCLUDED. The plan mandates unit + integration tests and a ≥ 85 % line
coverage gate on new code (Constitution VIII; spec SC). Tests are written
**first** within each story and must FAIL before the matching implementation.

**Quality bar (user criterion — zero technical debt, highest standards)**: every
task lands `ruff check` + `ruff format --check` clean, `mypy --strict src tests`
clean, every new source file ≤ 500 lines (Constitution IV), and **no new GOLEM
class / no new runtime dependency** (Constitution X / II). The frozen-ontology
closure (`len(CLASS_IRI) == 17`) and byte-stable research-free Turtle output are
treated as regression invariants, not afterthoughts.

**Organization**: Tasks are grouped by user story (US1 P1, US2 P1, US3 P2) so each
story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependency)
- **[Story]**: `[US1]` / `[US2]` / `[US3]` — Setup, Foundational and Polish carry no story label
- Each task names exact file paths

## Path Conventions

Single Python package, src-layout (Constitution III): production code under
`src/bookwright/`, tests under `tests/` at the repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a clean, green starting point before touching anything.

- [X] T001 Sync and record a clean baseline: run `uv sync` then the full gate
  (`uv run pytest`, `uv run ruff check`, `uv run ruff format --check`,
  `uv run mypy --strict src tests`) on branch `012-research-provenance-model`;
  confirm all green so every later regression is attributable to this iteration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The `bw:` vocabulary surface, the error type, the reader skeleton and
the `graph build` wiring — shared by all three stories. Designed so that, once
complete, **a research-free build still works and emits zero research triples**
(FR-015 / SC-005): foundational is itself an independently valuable, testable
increment.

**⚠️ CRITICAL**: No user-story work begins until this phase is complete.

- [X] T002 Add the Bookwright namespace and prefix binding in
  [src/bookwright/golem/namespaces.py](src/bookwright/golem/namespaces.py):
  `BW = Namespace("https://bookwright.dev/vocab/bw#")` and append `("bw", BW)` to
  `_PREFIXES` so `bind_prefixes` binds it deterministically. Do **not** add `BW`
  to `CLASS_IRI` or any frozen-closure list (Constitution X; research D3).
- [X] T003 In the same [src/bookwright/golem/namespaces.py](src/bookwright/golem/namespaces.py)
  add the `bw:` property `URIRef` constants (`BW_REFERENCE`, `BW_AUTHOR`,
  `BW_ORIGINAL_LANGUAGE`, `BW_RELIABILITY`, `BW_RELIABILITY_JUSTIFICATION`,
  `BW_ACCESS_DATE`, `BW_ORIGINAL_QUOTE`, `BW_TRANSLATION`, `BW_CLAIM`,
  `BW_ASSERTED_BY`, `BW_SUPPORTED_BY`, `BW_OPEN`, `BW_PROMOTES`, `BW_CONSTRAINS`),
  the `SOURCE_TYPE_IRI` / `RELIABILITY_IRI` value→E55-individual maps, and the
  reused/new CRM constants `HAS_TIME_SPAN` (`crm:P4_has_time-span`), `E52_TIME_SPAN`
  (`crm:E52_Time-Span`), `BEGIN_OF_BEGIN` (`crm:P82a_begin_of_the_begin`),
  `END_OF_END` (`crm:P82b_end_of_the_end`), and a `timeline_uri(uri_base) -> URIRef`
  helper returning `URIRef(f"{uri_base}timeline")` — the untyped well-known IRI that is
  the `constrains: timeline` target (research D10; no new class). None of these are added
  to `CLASS_IRI`/closure (research D3). Depends on T002 (same file).
- [X] T004 [P] Author the controlled vocabulary
  [src/bookwright/resources/vocabularies/sources.ttl](src/bookwright/resources/vocabularies/sources.ttl):
  six source-type individuals (`bw:source-type/primaria|secundaria|oficial|academica|periodistica|testimonial`)
  and three reliability individuals (`bw:reliability/alta|media|baja`), each
  `a crm:E55_Type ; rdfs:label "<accented Spanish word>"@es`; the `bw:` property
  declarations (`a rdf:Property` + `rdfs:label` + one-line `rdfs:comment`, per the
  table in `contracts/provenance-graph.md`); and a top provenance note that these
  terms are Bookwright's own, outside the frozen `golem.ttl`/`CLASS_IRI` closure
  (data-model §2; research D4). File must parse as well-formed Turtle.
- [X] T005 [P] Add `ResearchError(IOError_)` to
  [src/bookwright/io/errors.py](src/bookwright/io/errors.py): subclass the existing
  `io.errors.IOError_` base — the same base the bible reader's errors use (there is
  no `BookwrightError` type). Give it a `code` (e.g. `"invalid_research"`), `relpath`,
  the offending value/key, a human `message`, and a `.to_json()` returning the
  `{status, code, message, details}` shape its siblings emit (`MissingDirectoryError` /
  `SlugCollisionError`); `build.py` renders it at exit code 2 (contract
  `research-io.md`; research D7).
- [X] T006 Create the reader skeleton
  [src/bookwright/io/research.py](src/bookwright/io/research.py): the frozen
  `ResearchResult` dataclass (`sources`/`findings`/`anchors` tuples,
  `files_processed`, a `warnings` tuple of frozen `ResearchWarning`
  (`relpath`/`field`/`name`) for soft unresolved targets — D12, and `entities`
  property = sources+findings+anchors) and the
  `map_research(project_root, research_dir, uri_base, book_language, bible_index,
  timeline_uri) -> ResearchResult` signature. Implement only the **absent/empty
  `research_dir`** path now → empty tuples, `files_processed == 0`, never raises
  (FR-015 / SC-005), with deterministic sorted globbing and `sources.md`-first
  ordering scaffolded. Reuse `io/frontmatter.py` / `io/bible.py` machinery.
  Depends on T005.
- [X] T007 Wire the research pass into
  [src/bookwright/commands/graph/build.py](src/bookwright/commands/graph/build.py)`._build()`.
  (a) First extend [src/bookwright/io/bible.py](src/bookwright/io/bible.py): add an
  `entity_index: dict[str, URIRef]` field to `MapResult`, populated with
  `make_slug(name) → URI` for **every character, setting and event** (the kinds an
  anchor/finding may target, FR-009), leaving the participant-only `slug_index`
  untouched so existing resolution is unchanged (research D11).
  (b) After the bible pass, derive `research_dir = bible_dir / "research"`, take the
  bible `entity_index` and the well-known `timeline_uri(uri_base)` (= `{uri_base}timeline`,
  research D10), call `map_research(..., manifest.book.language, entity_index, timeline_uri)`, then
  `for entity in result.entities: for t in entity.to_triples(): engine.add_triple(*t)`
  before `engine.save(...)`; do **not** route research entities through
  `build_provenance`. Add `ResearchError` to the build command's existing
  `except (ProjectNotFoundError, MissingDirectoryError, UnknownIndexerError)` tuple so
  it renders through the existing error envelope at `EXIT_CONFIG` (exit 2). Extend `BuildReport`
  ([src/bookwright/io/report.py](src/bookwright/io/report.py) or build module) with
  **optional** `sources`/`findings`/`anchors` counters and a `ResearchWarning` list
  (surfaced human + `--json`, **exit code unchanged** — D12); leave existing fields
  unchanged so current build/`--json` tests pass (research D8). Depends on T006.
- [X] T008 Foundational regression test in
  [tests/commands/graph/test_research_build.py](tests/commands/graph/test_research_build.py):
  building a project with **no** `bible/research/` (and one with an empty
  `research/`) succeeds, adds zero research triples, leaves the existing bible E13
  count unchanged, and keeps the Turtle byte-stable (no stray `@prefix bw:`)
  (FR-015 / SC-005; research D9/closure check). Depends on T007.

**Checkpoint**: research-free build is provably unchanged; full gate green. User
stories can now begin.

---

## Phase 3: User Story 1 — Record sources with full provenance (Priority: P1) 🎯 MVP

**Goal**: Each declared Source becomes a typed, fully-provenanced node in
`bible/graph.ttl`, queryable like any other entity.

**Independent Test**: build the `tiny-novel` fixture and query
`<…/source/registro-tip> ?p ?o`; assert every provenance facet (reference, author,
original language, `P2_has_type`→E55, reliability+justification, access date,
original quote) is present, the URI is `{uri_base}source/{slug}`, translation is
absent when source language == book language, and a bad `type`/`reliability`
aborts the build naming the value.

### Tests for User Story 1 (write first — must FAIL before implementation) ⚠️

- [X] T009 [P] [US1] Unit tests for `Source` in
  [tests/golem/test_provenance_entities.py](tests/golem/test_provenance_entities.py):
  `to_triples()` emits all provenance facets, emits **no** `rdf:type`,
  types via `crm:P2_has_type → SOURCE_TYPE_IRI[type]` and `bw:reliability →
  RELIABILITY_IRI[reliability]`, URI == `{uri_base}source/{slug}`; `bw:translation`
  emitted only when `translation` is set; out-of-vocabulary `type`/`reliability`
  and empty `reliability_justification` are rejected by the model
  (FR-002/003/004/016; SC-003).
- [X] T010 [P] [US1] Reader tests for `sources.md` in
  [tests/io/test_research.py](tests/io/test_research.py): valid source parses;
  out-of-vocab `type`/`reliability` → `ResearchError` naming the value; missing
  required facet → `ResearchError`; translation rule — required (else error) when
  `original_language != book_language`, dropped (not emitted, not an error) when
  equal (FR-016; SC-004/006; research D6).
- [X] T011 [US1] Integration test in
  [tests/commands/graph/test_research_build.py](tests/commands/graph/test_research_build.py):
  `graph build` over the `with_research=True` `tiny_novel` scaffold writes the Source
  node; `graph query` returns its facets; a fixture variant with a bad `type` aborts
  with exit 2 and writes no graph (US1 acceptance 1–3; SC-001).

### Implementation for User Story 1

- [X] T012 [US1] Create the `Source` entity in
  [src/bookwright/golem/modules/provenance.py](src/bookwright/golem/modules/provenance.py):
  frozen Pydantic `SluggedEntity` subclass (`frozen=True`, `extra="forbid"`,
  `strict=True`), fields per data-model §1.1, `type: Literal[…6…]`,
  `reliability: Literal[…3…]`, non-empty `reliability_justification`,
  `path_segment="source"`, `golem_class` ClassVar as documented unemitted
  placeholder; override `to_triples()` to emit the facets and **no** `rdf:type`
  (research D2). Keep the file ≤ 500 lines.
- [X] T013 [US1] Implement `sources.md` parsing in
  [src/bookwright/io/research.py](src/bookwright/io/research.py): front-matter
  `sources:` list → `Source` entities, build the name/slug→`Source` index (needed
  later by findings), enforce the translation rule against `book_language`, and
  raise `ResearchError` (naming file + value) on vocab violation, missing facet,
  or translation-rule violation (research D6/D7). Depends on T012.
- [X] T014 [US1] Add the research fixture to the graph-test scaffolder
  [tests/commands/graph/conftest.py](tests/commands/graph/conftest.py): a
  `RESEARCH_SOURCES_MD` constant plus a `with_research: bool = False` parameter on
  `scaffold_project` that, when set, writes `bible/research/sources.md` — one
  `oficial` / `alta` Spanish source (book `language = "es"`, so no translation), per
  `contracts/research-format.md` / quickstart §0. `with_research` defaults **off** so
  the existing research-free `tiny_novel` (and the 10-E13 count in
  `test_provenance.py`) is byte-stable and unchanged. Do **not** touch the committed
  `tests/fixtures/tiny-novel/` (a different project the graph tests do not read).
- [X] T015 [US1] Verify US1 end to end: `graph build` emits the Source triples and
  the `BuildReport` source counter; run the per-story gate
  (`uv run pytest tests/golem/test_provenance_entities.py tests/io/test_research.py
  tests/commands/graph/test_research_build.py`, then `ruff`/`mypy --strict`).

**Checkpoint**: A project's source registry is structured, queryable graph data.
US1 is the shippable MVP on its own.

---

## Phase 4: User Story 2 — Sources into findings linked to the narrative (Priority: P1)

**Goal**: Each Finding reifies on `E13_Attribute_Assignment` recording what is
claimed, who asserts it, which entity it bears on, and its supporting source(s);
an *open* finding is recorded without a resolved claim/source.

**Independent Test**: in the fixture, a finding citing the source and bearing on
`Manuel de Aparici` appears as an `E13` with claim + asserter + `P140` target +
`bw:supportedBy`, at a `{uri_base}finding/{uuid7}` URI; the `_index.md` open
question appears as `E13 ; bw:open true` with no claim/source; both are
distinguishable from the bible's inferred assertions.

### Tests for User Story 2 (write first — must FAIL before implementation) ⚠️

- [X] T016 [P] [US2] Unit tests for `Finding` in
  [tests/golem/test_provenance_entities.py](tests/golem/test_provenance_entities.py):
  emits `rdf:type crm:E13_Attribute_Assignment`, `bw:claim`, `bw:assertedBy`
  (default `"author"`), `crm:P140_assigned_attribute_to` for `bears_on`, one
  `bw:supportedBy` per source, `bw:open` **only** when `True`; an open finding with
  empty claim/sources/target is valid and emits just `rdf:type` + `bw:open true`
  (FR-006/007/008; segment `finding`).
- [X] T017 [P] [US2] Reader tests in
  [tests/io/test_research.py](tests/io/test_research.py): topic-file `findings:`
  and `_index.md` `open_questions:` parse; a non-open finding missing `claim` or
  `sources` → `ResearchError`; an open finding is accepted; `sources` resolve via
  the source index and `bears_on` via `bible_index`; a `bears_on` name absent from
  `bible_index` yields a `ResearchWarning` and no `P140`, the build not aborting
  (FR-008; research D7/D12).
- [X] T018 [US2] Integration test in
  [tests/commands/graph/test_research_build.py](tests/commands/graph/test_research_build.py):
  the built graph contains the finding `E13` with claim/asserter/`P140`/source(s),
  the open question as `bw:open true`, and findings are distinguishable from bible
  inferred assertions with no false matches (US2 acceptance 1–3; SC-007).

### Implementation for User Story 2

- [X] T019 [US2] Create the `Finding` entity in
  [src/bookwright/golem/modules/provenance.py](src/bookwright/golem/modules/provenance.py):
  frozen `GolemEntity` subclass, `uuid_utils.uuid7()` token minted once in
  `model_post_init`, `path_segment="finding"`,
  `golem_class = CLASS_IRI["AttributeAssignment"]`, fields per data-model §1.2,
  open-state emission invariant (research D2). File stays ≤ 500 lines.
- [X] T020 [US2] Implement `findings:` + `_index.md` `open_questions:` parsing in
  [src/bookwright/io/research.py](src/bookwright/io/research.py): build `Finding`
  entities, resolve `sources` via the source index and `bears_on` via
  `bible_index` (an unresolved `bears_on` name → omit `P140` and append a
  `ResearchWarning`, not an error — D12), enforce the non-open invariant
  (claim + ≥ 1 source) else `ResearchError` (FR-007/008; research D7). Depends on T019, T013.
- [X] T021 [US2] Extend the research fixture in
  [tests/commands/graph/conftest.py](tests/commands/graph/conftest.py): under the
  `with_research` branch, write `bible/research/detective-licencia.md` (a finding
  citing the source and bearing on `Manuel de Aparici`) and `bible/research/_index.md`
  (one open question), per `contracts/research-format.md`.
- [X] T022 [US2] Verify US2 end to end and run the per-story gate (pytest for the
  three test modules + `ruff` + `mypy --strict`).

**Checkpoint**: Findings participate in the same graph and queries as characters,
settings and events. US1 + US2 both work independently.

---

## Phase 5: User Story 3 — Promote findings to anchors that constrain the fiction (Priority: P2)

**Goal**: An Anchor promotes a Finding into a binding constraint linked
(`bw:constrains`) to the narrative entity (or the timeline) it constrains, with an
optional time-span for downstream anachronism detection; the payoff SPARQL query
returns every anchor constraining a given entity with its claim and sources.

**Independent Test**: in the fixture, an anchor promoting the finding and
constraining `Manuel de Aparici` (with a time-span) is returned by the worked
SPARQL query together with the promoted claim and source; the time-span query
returns its begin/end years; an anchor with no time-span returns none; an anchor
with `constrains: timeline` links the timeline URI.

### Tests for User Story 3 (write first — must FAIL before implementation) ⚠️

- [X] T023 [P] [US3] Unit tests for `Anchor` in
  [tests/golem/test_provenance_entities.py](tests/golem/test_provenance_entities.py):
  emits `rdf:type crm:E13_Attribute_Assignment`, `bw:promotes`, `bw:constrains`;
  with `begin`/`end` emits `crm:P4_has_time-span` + the `{anchor}/time-span`
  sub-node (`E52_Time-Span`, `P82a`/`P82b` `xsd:gYear`); with neither emits **no**
  time-span; a single `date` shorthand sets `begin == end`; URI segment `anchor`
  (FR-009/010; research D5).
- [X] T024 [P] [US3] Reader tests in
  [tests/io/test_research.py](tests/io/test_research.py): `anchors:` parse;
  `promotes` resolves to the in-file finding id (unknown id → `ResearchError`);
  `constrains` resolves via `bible_index` or to `timeline_uri` for the literal
  `timeline`; a `constrains` target absent from `bible_index` yields a
  `ResearchWarning` and **no** `bw:constrains` triple, the build not aborting (D12);
  `begin`/`end`/`date` map correctly (FR-009/010; research D7).
- [X] T025 [US3] Integration test in
  [tests/commands/graph/test_research_build.py](tests/commands/graph/test_research_build.py):
  the worked SPARQL query (provenance-graph.md / quickstart §3) returns the anchor
  with its promoted claim and source (SC-002); the time-span query returns
  begin/end; a no-time-span anchor returns no row; a `constrains: timeline` anchor
  links the timeline URI (US3 acceptance 1–4).

### Implementation for User Story 3

- [X] T026 [US3] Create the `Anchor` entity in
  [src/bookwright/golem/modules/provenance.py](src/bookwright/golem/modules/provenance.py):
  frozen `GolemEntity` subclass, `uuid7` token, `path_segment="anchor"`,
  `golem_class = CLASS_IRI["AttributeAssignment"]`, fields `promotes`/`constrains`/
  `begin`/`end` per data-model §1.3, time-span emission per research D5. Keep file
  ≤ 500 lines.
- [X] T027 [US3] Implement `anchors:` parsing in
  [src/bookwright/io/research.py](src/bookwright/io/research.py): resolve
  `promotes`→finding URI (unknown id → `ResearchError`), `constrains`→`bible_index`
  (narrative entity) or the well-known `timeline_uri` for the literal `timeline`
  (research D10) — a `constrains` name absent from the index → omit `bw:constrains`
  and append a `ResearchWarning`, not an error (D12) — and
  `begin`/`end`/`date`→time-span (FR-009/010; research D7).
  Depends on T026, T020.
- [X] T028 [US3] Extend the `detective-licencia.md` research fixture in
  [tests/commands/graph/conftest.py](tests/commands/graph/conftest.py) with an anchor
  (promotes the finding, constrains `Manuel de Aparici`, carries a `begin`/`end`
  time-span), per `contracts/research-format.md`.
- [X] T029 [US3] Verify US3 end to end and run the per-story gate (pytest + `ruff`
  + `mypy --strict`).

**Checkpoint**: recorded research is now an enforceable constraint surface; all
three stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Lock in the zero-tech-debt, highest-standards bar before merge.

- [X] T030 [P] Confirm the frozen-ontology closure is intact:
  [tests/golem/test_namespaces.py](tests/golem/test_namespaces.py) still asserts
  `len(CLASS_IRI) == 17` and the `bw:`/CRM additions are outside every frozen
  closure list; add explicit assertions if any are missing (Constitution X;
  research closure check).
- [X] T031 [P] Verify the research-free `tiny-novel` Turtle output is byte-stable
  (no stray `@prefix bw:`) and that the pre-existing `E13` count in
  [tests/commands/graph/test_provenance.py](tests/commands/graph/test_provenance.py)
  is unchanged (research D9).
- [X] T032 Verify ≥ 85 % line coverage on the new code
  (`provenance.py`, `io/research.py`, the `build.py` research pass) via
  `uv run pytest --cov=bookwright --cov-report=term-missing`; add focused tests for
  any uncovered branch (spec SC; Constitution VIII).
- [X] T033 Confirm every touched/new source file is ≤ 500 lines (Constitution IV) —
  in particular `golem/modules/provenance.py` and `io/research.py`; split if
  exceeded.
- [X] T034 Run the quickstart end to end on the fixture (quickstart.md §1–§4:
  US1 facets, US2 finding + open question, US3 payoff + time-span queries, and the
  research-free regression).
- [X] T035 Full gate: `uv run pytest && uv run ruff check && uv run ruff format
  --check && uv run mypy --strict src tests` — all green before merge.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; **blocks all user stories**.
  Internal order: T002 → T003 (same file), T004/T005 [P], T006 (needs T005),
  T007 (needs T006), T008 (needs T007).
- **User Stories (Phase 3–5)**: each depends on Foundational. US1 is the MVP. US2
  builds on US1's source index (T020 needs T013). US3 builds on US2's findings
  (T027 needs T020). Priority order US1 (P1) → US2 (P1) → US3 (P2).
- **Polish (Phase 6)**: depends on all desired stories.

### User Story Dependencies

- **US1 (P1)**: starts after Foundational. No dependency on other stories —
  shippable alone.
- **US2 (P1)**: starts after Foundational; reuses US1's source index (parsing
  dependency T020→T013) but is independently testable (its own findings + open
  questions).
- **US3 (P2)**: starts after Foundational; reuses US2's findings (T027→T020) but is
  independently testable (its own anchors + SPARQL payoff).

### Within Each User Story

- Tests are written first and must FAIL before implementation.
- Entity model → reader parsing → fixture → end-to-end verify.
- The three entities share `golem/modules/provenance.py` and the three reader
  passes share `io/research.py`, so entity tasks across stories (T012/T019/T026)
  and reader tasks (T013/T020/T027) are **sequential on the same file**, not [P].

### Parallel Opportunities

- Foundational: T004 (`sources.ttl`) and T005 (`errors.py`) run in parallel.
- US1 tests T009 (golem) + T010 (io) run in parallel (different files); within US2
  T016 + T017; within US3 T023 + T024.
- Polish: T030 + T031 run in parallel.
- Integration tests (T008/T011/T018/T025) all live in
  `tests/commands/graph/test_research_build.py` → sequential, not [P].

---

## Parallel Example: User Story 1

```bash
# Write the two failing test modules together (different files):
Task: "Unit tests for Source in tests/golem/test_provenance_entities.py"   # T009
Task: "Reader tests for sources.md in tests/io/test_research.py"           # T010
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → clean baseline.
2. Phase 2 Foundational → research-free build provably unchanged (CRITICAL).
3. Phase 3 US1 → typed, fully-provenanced Source nodes.
4. **STOP & VALIDATE**: query the source's facets; run the gate. Ship if ready.

### Incremental Delivery

1. Setup + Foundational → foundation ready (zero-triple research-free build).
2. US1 → source registry as graph data → validate → ship (MVP).
3. US2 → findings reified on E13, open questions preserved → validate.
4. US3 → anchors constraining the fiction + payoff SPARQL → validate.
5. Polish → coverage, closure, byte-stability, file-size, full gate.

---

## Notes

- [P] = different files, no incomplete dependency. [Story] maps a task to its user
  story for traceability.
- **No new GOLEM class, no new runtime dependency** (Constitution X / II): `bw:`
  terms live in `sources.ttl`, never in `golem.ttl`; nothing enters `CLASS_IRI`.
- Research is the *derived* side: triples come from `bible/research/`, never the
  reverse (FR-017).
- Verify each test FAILS before its implementation; commit after each task or
  logical group; stop at any checkpoint to validate a story independently.
