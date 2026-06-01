---
description: "Task list for iteration 6 — Graph Indexer + `graph` commands"
---

# Tasks: Graph Indexer + `graph` Commands

**Input**: Design documents from `/specs/006-graph-indexer/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅,
contracts/ ✅ (`cli-graph.md`, `indexer.md`, `bible-format.md`), quickstart.md ✅

**Tests**: INCLUDED. Constitution Principle VIII mandates test discipline with
≥ 80 % coverage; the plan enumerates the unit + integration test files. Test
tasks are therefore first-class, not optional, for this iteration.

**Organization**: Tasks are grouped by user story. The engine seam (Indexer
Protocol, `RdflibIndexer`, registry, errors) and the cross-cutting helpers
(`io/project.py`, `commands/graph/envelope.py`, the `graph` sub-app skeleton)
are **Foundational** because both P1 stories sit directly on them.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: US1–US5 (Foundational/Setup/Polish carry no story label)
- All paths are relative to the repo root.

## Path Conventions

Single-project CLI: production code under `src/bookwright/`, tests under
`tests/`. New packages this iteration: `src/bookwright/indexers/`,
`src/bookwright/io/`, `src/bookwright/commands/graph/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Land the Gate II `pyyaml` amendment package and create the new
package skeletons before any code imports them.

- [ ] T001 Add `"pyyaml>=6.0"` to `[project].dependencies` in [pyproject.toml](pyproject.toml) (insert alphabetically) and run `uv sync` so the direct dependency is recorded in [uv.lock](uv.lock). (Gate II prerequisite — the constitution was already amended to v1.2.0 in commit `caaedf6`; this records the runtime dep itself.)
- [ ] T002 Add `"yaml"` to `RUNTIME_MODULES` in [src/bookwright/commands/check.py](src/bookwright/commands/check.py#L11) so `bookwright check` verifies the new runtime import. Also add `"packaging"` in the same tuple: it was promoted to a runtime dependency in constitution v1.1.0 (iteration 2) but `RUNTIME_MODULES` never started verifying it — close that gap while editing this tuple.
- [ ] T003 Verify design § 14.1 in [bookwright-design.md](bookwright-design.md) (Spanish) lists `pyyaml` among the runtime dependencies — this propagation already landed with the v1.2.0 constitution amendment (commit `caaedf6`); this is a confirmation gate, not a re-edit. Fail only if the entry is missing or out of order.
- [ ] T004 [P] Create the `indexers` package skeleton: empty [src/bookwright/indexers/__init__.py](src/bookwright/indexers/__init__.py) (re-exports filled in T009/T015).
- [ ] T005 [P] Create the `io` package skeleton: empty [src/bookwright/io/__init__.py](src/bookwright/io/__init__.py).
- [ ] T006 [P] Create the `commands/graph` package skeleton: empty [src/bookwright/commands/graph/__init__.py](src/bookwright/commands/graph/__init__.py) (Typer wiring filled in T016).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The engine seam + cross-cutting helpers that BOTH P1 stories
require. No user-story work can begin until this phase is complete.

**⚠️ CRITICAL**: Build (US1) and Query (US2) both depend on the Indexer
Protocol, the concrete `RdflibIndexer`, the registry, the error types, the
project locator, the JSON envelopes, and the `graph` sub-app skeleton.

### Errors & engine seam

- [ ] T007 [P] Implement indexer error types in [src/bookwright/indexers/errors.py](src/bookwright/indexers/errors.py): `UnknownIndexerError` (`unknown_indexer`, carries `name` + `available`), `GraphNotBuiltError` (`graph_not_built`), `InvalidQueryError` (`invalid_query`) — each with `.to_json()` mirroring [src/bookwright/golem/errors.py](src/bookwright/golem/errors.py).
- [ ] T008 [P] Implement io error types in [src/bookwright/io/errors.py](src/bookwright/io/errors.py): `ProjectNotFoundError` (`not_a_project`), `MissingDirectoryError` (`missing_directory`), `InvalidFrontmatterError` (`invalid_frontmatter`, carries `path` + `reason`), `SlugCollisionError` (`slug_collision`, carries `identifier` + both paths) — each with `.to_json()` (data-model § 6).
- [ ] T009 Define the `Indexer` Protocol + `Triple` type alias in [src/bookwright/indexers/base.py](src/bookwright/indexers/base.py): `typing.Protocol` with `load`/`save`/`add_triple`/`query`/`construct`/`count` per [contracts/indexer.md](specs/006-graph-indexer/contracts/indexer.md) (data-model § 1).
- [ ] T010 Implement `RdflibIndexer` in [src/bookwright/indexers/rdflib_indexer.py](src/bookwright/indexers/rdflib_indexer.py): wraps `rdflib.Graph`, binds short prefixes via `golem.namespaces.bind_prefixes` in `__init__`; `add_triple` coerces IRI-like `str` subjects/predicates to `URIRef`; `query` maps each `ResultRow` → `{var: str(value)}` and raises `InvalidQueryError` on malformed SPARQL; `save` serializes Turtle (short prefixes) creating parent dirs; `count → len(graph)`; `construct` returns a fresh `RdflibIndexer` over the sub-graph (FR-005/006/015, R5).
- [ ] T011 Implement the registry in [src/bookwright/indexers/__init__.py](src/bookwright/indexers/__init__.py): `INDEXER_REGISTRY = {"rdflib": RdflibIndexer}`, `resolve_indexer(name)` raising `UnknownIndexerError(name, available=sorted(INDEXER_REGISTRY))`; re-export `Indexer`, `RdflibIndexer`, the errors. **No `GrafeoIndexer`** (deferred, Principle X). (FR-007/008, R4)

### Cross-cutting helpers

- [ ] T012 [P] Implement `find_project_root()` + `ProjectNotFoundError` use in [src/bookwright/io/project.py](src/bookwright/io/project.py): walk up from cwd for `manifest.toml`; none → `ProjectNotFoundError` (R8).
- [ ] T013 [P] Implement the graph-command JSON envelopes in [src/bookwright/commands/graph/envelope.py](src/bookwright/commands/graph/envelope.py): single-line `json.dumps(payload, separators=(",", ":")) + "\n"` to stdout success/error helpers, reusing the pattern from [src/bookwright/commands/version.py](src/bookwright/commands/version.py#L31) (Principle IX, R8/contracts cli-graph.md).
- [ ] T014 Create the `graph` Typer sub-app + wire it into the CLI: define `app = typer.Typer()` in [src/bookwright/commands/graph/__init__.py](src/bookwright/commands/graph/__init__.py) and register it with `app.add_typer(graph.app, name="graph")` in [src/bookwright/cli.py](src/bookwright/cli.py) (build/query callbacks attached in their story phases) (contracts cli-graph.md "Wiring").

### Foundational tests

- [ ] T015 [P] Unit-test `RdflibIndexer` in [tests/indexers/test_rdflib_indexer.py](tests/indexers/test_rdflib_indexer.py): `count()==0` on construction, `add_triple`/`count`, save→load isomorphic round-trip, serialized Turtle uses short prefixes (FR-015), `construct` returns a populated engine (contracts indexer.md invariants).
- [ ] T016 [P] Unit-test `find_project_root` in [tests/io/test_project.py](tests/io/test_project.py): found from nested cwd, and `ProjectNotFoundError` when no `manifest.toml` in any ancestor (R8).

**Checkpoint**: Engine seam + helpers ready and tested — user stories can begin.

---

## Phase 3: User Story 1 - Build the project graph from the bible (Priority: P1) 🎯 MVP

**Goal**: `bookwright graph build` reads `bible/` markdown, turns each file's
frontmatter into GOLEM instances via the iteration-5 constructors, and writes a
well-formed `bible/graph.ttl` using short prefixes; reports files/entities/triples.

**Independent Test**: In a fixture project with one valid character file, run
`graph build` and assert `bible/graph.ttl` is created, parses as RDF, and
contains the type assertion plus the triples for each recognised frontmatter key.

### Tests for User Story 1 ⚠️

> Write these FIRST; ensure they FAIL before implementation.

- [ ] T017 [P] [US1] Create the `tiny-novel` fixture builder in [tests/commands/graph/conftest.py](tests/commands/graph/conftest.py): a pytest fixture scaffolding a project (`manifest.toml` with `uri_base`, `bible/characters/*.md`, `bible/settings/*.md`, `bible/timeline.md`, `manuscript/`) — reused by US2–US5 command tests.
- [ ] T018 [P] [US1] Unit-test the frontmatter reader in [tests/io/test_frontmatter.py](tests/io/test_frontmatter.py): valid fence → `(metadata, body, key_lines)`, no-fence → `{}` metadata, 1-based `key_lines` correctness, malformed YAML surfaces for the caller to wrap (data-model § 2).
- [ ] T019 [P] [US1] Unit-test the bible mapper happy path in [tests/io/test_bible.py](tests/io/test_bible.py): type-by-location (`characters/`→Character, `settings/`→Setting, `timeline.md`→events, `relationships.md`→relationships), character frontmatter → expected `Character(...)` construction, unknown keys recorded in `unknown_keys`, and a `participants:` name with no matching character recorded in `unresolved_participants` with its `dlp:participant` edge omitted while the event/relationship is still constructed (US1 portions of FR-009/010/019, bible-format.md).
- [ ] T020 [P] [US1] Integration-test `graph build` happy path in [tests/commands/graph/test_build.py](tests/commands/graph/test_build.py): `bible/graph.ttl` created + parses as RDF + uses short prefixes; `--force` rebuilds idempotently (v0 has no cache to bypass — same output, no error); summary reports files/entities/triples (stderr) and the `--json` report shape includes `skipped`/`unknown_keys`/`unresolved_participants`/`graph_path` (FR-001/002/015/018, SC-001).
- [ ] T020b [P] [US1] Directly assert SC-001's frozen-vocabulary closure in [tests/commands/graph/test_build.py](tests/commands/graph/test_build.py): after a real `graph build`, parse `bible/graph.ttl` and assert every predicate and every `rdf:type` object is a member of `golem.namespaces.frozen_terms()` — i.e. `used_terms <= frozen_terms()`. This guards SC-001 at the iteration-6 build level rather than relying transitively on iteration-5's closure test, catching any out-of-vocabulary term the mapper could introduce (FR-010, SC-001).
- [ ] T020c [P] [US1] Assert the empty-bible edge case in [tests/commands/graph/test_build.py](tests/commands/graph/test_build.py): a project whose recognised bible dirs/files exist but contain no entities builds successfully (exit 0), writes a `bible/graph.ttl` that parses as well-formed RDF (prefix-only / empty), and reports `entities == 0` in both the stderr summary and the `--json` report (spec edge case "Empty bible", bible-format.md:100).
- [ ] T021 [P] [US1] Assert the JSON-over-stdout invariant for `build` in [tests/commands/graph/test_json_contract.py](tests/commands/graph/test_json_contract.py): under `--json`, stdout is exactly one JSON document and nothing else; human prose goes to stderr (Principle IX, SC-003).

### Implementation for User Story 1

- [ ] T022 [P] [US1] Implement `parse_frontmatter` in [src/bookwright/io/frontmatter.py](src/bookwright/io/frontmatter.py): split the leading `---\n…\n---\n` fence, `yaml.safe_load` the block (`{}` if none), record each top-level key's 1-based line in `key_lines`; expose a `Frontmatter` result (data-model § 2, R3).
- [ ] T023 [P] [US1] Implement the build report models in [src/bookwright/io/report.py](src/bookwright/io/report.py): frozen pydantic `BuildReport` (`files_processed`, `entities`, `triples`, `skipped`, `unknown_keys`, `unresolved_participants`, `graph_path`), `SkippedFile{path,reason}`, `UnknownKey{path,key}`, `UnresolvedParticipant{path,entity,name}` (data-model § 5; `unknown_keys`/`unresolved_participants` are soft warnings that never change the exit code).
- [ ] T024 [US1] Implement the bible mapper in [src/bookwright/io/bible.py](src/bookwright/io/bible.py): discover recognised paths by location (R2), read frontmatter, and call the iteration-5 constructors — `Character(uri_base, name, born?, died?, features=…, narrative_roles=…)`, `Setting(uri_base, name)`, `NarrativeEvent`/`SocialRelationship` per `events:`/`relationships:` item. Build characters first into a `slug → Character URI` index, then resolve each item's participants against it: a name with no match is omitted from `participants=` and collected as an `UnresolvedParticipant{path, entity, name}` (FR-019), not a skip. Collect `unknown_keys` likewise; return the constructed entities plus the `unknown_keys`/`unresolved_participants` lists for the build command to thread into the `BuildReport`. The mapper never assembles feature/role/dimension nodes (the model does). (FR-009/010/019, data-model § 0/§ 3, bible-format.md) (depends on T022, T023)
- [ ] T025 [US1] Implement `graph build` orchestration in [src/bookwright/commands/graph/build.py](src/bookwright/commands/graph/build.py): locate project (T012), read the `[bookwright] uri_base`/`indexer` via `Manifest.load` + `resolve_indexer` (default `rdflib`), feed each `entity.to_triples()` into the engine, `engine.save(graph_path)` (path from `manifest.toml > [paths] graph`, default `bible/graph.ttl`), build the `BuildReport`, accept `--force`/`--json`, emit human summary to stderr and JSON report on stdout under `--json`; register the callback on the `graph` sub-app (FR-001/002/018, R5, contracts cli-graph.md). (depends on T024)

**Checkpoint**: `graph build` produces a queryable `bible/graph.ttl` — MVP works
and is independently testable.

---

## Phase 4: User Story 2 - Query the graph with SPARQL (Priority: P1)

**Goal**: `bookwright graph query "<SPARQL>"` loads `bible/graph.ttl`, runs the
query, and returns rows as a `rich` table or, under `--json`, a single
`{"status":"ok","results":[...],"count":N}` document.

**Independent Test**: Against a fixture `bible/graph.ttl`, run a `SELECT` and
assert the rows; rerun with `--json` and assert stdout is one valid JSON doc.

### Tests for User Story 2 ⚠️

- [ ] T026 [P] [US2] Integration-test `graph query` in [tests/commands/graph/test_query.py](tests/commands/graph/test_query.py): `SELECT ?c WHERE {?c a golem:G1_Character}` returns exactly the expected identifiers (SC-002); `--json` yields `{"status":"ok","results":[...],"count":N}` and nothing else on stdout; table form on stdout without `--json`; querying a project with no `bible/graph.ttl` yet exits 2 with a `graph_not_built` error doc whose message tells the user to run `graph build` first, and emits no partial rows (FR-016 edge / cli-graph.md); extend [tests/commands/graph/test_json_contract.py](tests/commands/graph/test_json_contract.py) for query success/empty/error (Principle IX, SC-003).
- [ ] T027 [P] [US2] Unit-test query error/empty behaviour in [tests/indexers/test_query_errors.py](tests/indexers/test_query_errors.py): malformed SPARQL → `InvalidQueryError` with no partial yield; zero-match query → empty iterable (FR-016, R8).

### Implementation for User Story 2

- [ ] T028 [US2] Implement `graph query` orchestration in [src/bookwright/commands/graph/query.py](src/bookwright/commands/graph/query.py): locate project + resolve engine, `engine.load(graph_path)` (missing file → `GraphNotBuiltError` "run `graph build` first"), run the SPARQL string, render a `rich` table to stdout (human) or one JSON doc under `--json`; empty match → `{"status":"ok","results":[],"count":0}` exit 0; invalid SPARQL → `invalid_query` error doc, exit 3, no partial rows; register the callback on the `graph` sub-app (FR-003/004/016, R8, contracts cli-graph.md). (depends on T011, T013, T014)

**Checkpoint**: Both P1 stories work — build then query is a complete loop.

---

## Phase 5: User Story 3 - Provenance for every derived assertion (Priority: P2)

**Goal**: Every derived assertion carries a GOLEM/CIDOC `AttributeAssignment`
naming its source file (and line when locatable).

**Independent Test**: Build from a single character file; assert the graph
contains an `AttributeAssignment` whose source reference is
`bible/characters/<f>.md` (and `…:<line>` where a value is line-locatable).

### Tests for User Story 3 ⚠️

- [ ] T029 [P] [US3] Integration-test provenance in [tests/commands/graph/test_provenance.py](tests/commands/graph/test_provenance.py): each derived attribute has an `AttributeAssignment` whose source reference is the relative source path; a line-locatable value includes the `…:N` locator; provenance is retrievable via SPARQL (FR-011, SC-006, R6, quickstart § 3).

### Implementation for User Story 3

- [ ] T030 [US3] Emit provenance in the build path — extend [src/bookwright/io/bible.py](src/bookwright/io/bible.py) (and the build wiring in [src/bookwright/commands/graph/build.py](src/bookwright/commands/graph/build.py) if needed) to iterate `entity.derived_assertions()` (the R1b seam on `main`, data-model § 0) and construct **one iteration-5 `AttributeAssignment` per yielded `DerivedAssertion`** — identity (file-level) plus each feature, role, birth/death, and participation — setting `target`/`attribute` from the descriptor and `source = "<relpath>"` (identity / no locatable line) or `"<relpath>:<line>"` by resolving `DerivedAssertion.source_field` against the file's `key_lines`; feed each assignment's triples into the engine. Do **not** read the model's private `_feature_nodes`/`_role_nodes` nor recompute node URIs — enumerate through the API. Because `derived_assertions()` yields exactly one descriptor per materialized node, this satisfies SC-006 per assertion (FR-011, SC-006, data-model § 0/§ 4, R6). (depends on T024, T025)

**Checkpoint**: The graph is auditable — every derived triple traces to its source.

---

## Phase 6: User Story 4 - Pluggable indexer engine selected from the manifest (Priority: P2)

**Goal**: Lock the architectural guarantee — engine resolved from
`manifest.toml > [bookwright] indexer` (default `rdflib`), unknown name fails
clearly, and adding an engine needs zero command-code change.

**Independent Test**: With `indexer = "rdflib"` (or absent) the rdflib engine is
selected; an unknown name fails naming the unknown engine and the available set.

### Tests for User Story 4 ⚠️

- [ ] T031 [P] [US4] Unit-test the registry in [tests/indexers/test_registry.py](tests/indexers/test_registry.py): `resolve_indexer("rdflib")` → `RdflibIndexer`; default selection when the manifest key is absent; unknown name → `UnknownIndexerError` whose message names the engine and lists `sorted(INDEXER_REGISTRY)`; assert a hypothetical new registry entry is selectable without touching `build.py`/`query.py` (FR-007/008, SC-007).
- [ ] T032 [P] [US4] Integration-test the command path in [tests/commands/graph/test_build.py](tests/commands/graph/test_build.py) (and query): a manifest with an unregistered `indexer` makes `graph build`/`query` exit non-zero (code 2) with an `unknown_indexer` error doc under `--json` that lists the available engines (FR-007, contracts cli-graph.md).

### Implementation for User Story 4

- [ ] T033 [US4] Verify/confirm the manifest-driven selection in [src/bookwright/commands/graph/build.py](src/bookwright/commands/graph/build.py) and [src/bookwright/commands/graph/query.py](src/bookwright/commands/graph/query.py): both read `[bookwright] indexer` (default `rdflib`) and route through `resolve_indexer`, mapping `UnknownIndexerError` to the `unknown_indexer` envelope (exit 2). No engine name is hard-coded in command code (FR-005/007/008, SC-007). (depends on T025, T028 — refactor only if those hard-coded the engine)

**Checkpoint**: Engine pluggability is verified and guarded by tests.

---

## Phase 7: User Story 5 - Clear, fault-tolerant build reporting (Priority: P3)

**Goal**: Missing directories fail fast; a single malformed file is skipped,
recorded, and reported (exit 4) without aborting; a slug collision is a hard
error (exit 3) that names the identifier and both files.

**Independent Test**: Run `graph build` against (a) a project missing `bible/`,
(b) one malformed file among valid ones, (c) a slug collision; assert each
specified outcome.

### Tests for User Story 5 ⚠️

- [ ] T034 [P] [US5] Integration-test fault paths in [tests/commands/graph/test_build.py](tests/commands/graph/test_build.py): running `graph build` outside any project (no `manifest.toml` in cwd/ancestors) → `not_a_project` error doc, exit 2, no graph written (FR-012 sibling / cli-graph.md); missing `bible/` and missing `manuscript/` → `missing_directory` error, exit 2, no graph written (FR-012); one malformed file among valid ones → valid files processed, file listed in `skipped` with reason, exit 4, `status:"ok"` (FR-013, SC-004); slug collision → `slug_collision` error naming the identifier + both paths, exit 3, no graph written (FR-014, SC-005).
- [ ] T035 [P] [US5] Extend [tests/io/test_bible.py](tests/io/test_bible.py): per-file skip on invalid frontmatter (malformed YAML, missing/empty `name`, non-integer `born`/`died`) records `(path, reason)` and continues; `(concept, slug)` collision raises `SlugCollisionError` (FR-013/014, bible-format.md).

### Implementation for User Story 5

- [ ] T036 [P] [US5] Add the manuscript presence check in [src/bookwright/io/manuscript.py](src/bookwright/io/manuscript.py): v0 presence-only check (no prose mining) used by `build` to enforce `manuscript/` existence (FR-012, research cross-cutting confirmations).
- [ ] T037 [US5] Harden the mapper in [src/bookwright/io/bible.py](src/bookwright/io/bible.py): wrap per-file frontmatter failures as `InvalidFrontmatterError`, skip and collect `(path, reason)` instead of aborting; detect `(concept, slug)` collisions via a `dict[(concept,slug)] -> path` and raise `SlugCollisionError(identifier, first_path, second_path)` (FR-013/014, data-model § 3, R7). (depends on T024)
- [ ] T038 [US5] Wire the fault model into [src/bookwright/commands/graph/build.py](src/bookwright/commands/graph/build.py): fail before writing on missing `bible/`/`manuscript/` (`missing_directory`, exit 2) and on `slug_collision` (exit 3, no graph); on ≥ 1 skipped file write the graph but exit 4 with the populated `skipped` array; clean build exits 0 (FR-012/013/014, R7, contracts cli-graph.md). (depends on T036, T037)

**Checkpoint**: All five stories independently functional; the build is trustworthy.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Gate-clean the iteration and validate the end-to-end walkthrough.

- [ ] T039 [P] Run the quickstart walkthrough in [specs/006-graph-indexer/quickstart.md](specs/006-graph-indexer/quickstart.md) end-to-end against a real `bookwright init` project; confirm build + the three example queries (characters, born-before-1850, protagonists) + provenance behave as documented.
- [ ] T040 Confirm module sizes: every new module under `indexers/`, `io/`, `commands/graph/` is ≤ 500 lines (Principle IV); split if any approaches the ceiling. Enforce the FR-017 read-only boundary with an automated assertion in [tests/commands/graph/test_json_contract.py](tests/commands/graph/test_json_contract.py): `graph query` against a pre-built fixture leaves `bible/graph.ttl` byte-for-byte unchanged (no write-back), and `graph` exposes no mutation verb beyond `build`. Also confirm by inspection that neither verb imports a validator (semantic coherence is iteration 10).
- [ ] T041 Run `uv run ruff check && uv run ruff format --check` and fix any findings across new code.
- [ ] T042 Run `uv run mypy --strict src tests` and resolve all type errors (the `Indexer` Protocol must type-check structurally).
- [ ] T043 Run `uv run pytest --cov-fail-under=80` (at least `tests/golem tests/indexers tests/io tests/commands/graph`) and confirm green with ≥ 80 % coverage (Principle VIII).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately. T001 (pyyaml) must precede any code importing `yaml` (T022).
- **Foundational (Phase 2)**: depends on Setup — **BLOCKS all user stories**.
- **User Stories (Phases 3–7)**: all depend on Foundational. US1 (P1) is the MVP.
  - US2 (P1) depends only on Foundational (engine load/query) — independently testable against any graph fixture, but reuses the US1 `conftest.py` builder (T017) in practice.
  - US3 (P2) builds on US1's mapper/build (T024/T025).
  - US4 (P2) verifies the Foundational registry; its command-path test (T032) needs build/query (US1/US2) present.
  - US5 (P3) hardens US1's mapper/build (T024/T025/T036).
- **Polish (Phase 8)**: depends on all desired stories.

### Within Each User Story

- Tests are written first and must FAIL before implementation.
- Models/readers (`frontmatter`, `report`) before the mapper (`bible`); mapper before the `build` command; engine before the `query` command.

### Parallel Opportunities

- Setup: T004/T005/T006 (distinct `__init__.py` files) in parallel after T001–T003.
- Foundational: T007/T008 (distinct error files), then T012/T013 in parallel; T015/T016 (distinct test files) in parallel once their targets exist.
- US1: T017/T018/T019/T020/T021 (distinct test files) in parallel; T022/T023 (distinct source files) in parallel before T024.
- US3/US4/US5 test files are independent of one another and can be authored in parallel once their phase opens.

---

## Parallel Example: User Story 1

```bash
# Author all US1 test files together (write them FIRST, expect FAIL):
Task: "tiny-novel fixture in tests/commands/graph/conftest.py"
Task: "frontmatter unit tests in tests/io/test_frontmatter.py"
Task: "bible mapper happy-path tests in tests/io/test_bible.py"
Task: "graph build integration tests in tests/commands/graph/test_build.py"
Task: "JSON-contract test in tests/commands/graph/test_json_contract.py"

# Then the independent source modules together:
Task: "parse_frontmatter in src/bookwright/io/frontmatter.py"
Task: "BuildReport models in src/bookwright/io/report.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup (land `pyyaml`, create skeletons).
2. Phase 2 Foundational (engine seam + helpers) — CRITICAL, blocks everything.
3. Phase 3 US1 — `graph build` writing a valid `bible/graph.ttl`.
4. **STOP and VALIDATE**: build a fixture project, inspect the Turtle.

### Incremental Delivery

1. Setup + Foundational → seam ready.
2. US1 (build) → MVP: a graph exists.
3. US2 (query) → the read half; build+query is a full loop.
4. US3 (provenance) → auditability.
5. US4 (pluggability) → guarantee locked.
6. US5 (fault tolerance) → trustworthy in daily use.
7. Polish → gates green, quickstart validated.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- The iteration-5 `golem` package is **on `main` and consumed as-is** — this
  iteration constructs no feature/role/dimension nodes itself; it passes
  frontmatter to the constructors and feeds `to_triples()` into the engine.
- No `GrafeoIndexer`, no cache file, no write-back, no validators, no prose
  mining — all out of v0 scope (Principle X).
- Commit after each task or logical group; verify tests fail before implementing.
