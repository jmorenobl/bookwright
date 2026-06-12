# Tasks: Derived project status and next actions

**Input**: Design documents from `/specs/020-status-command/`

**Prerequisites**: plan.md, spec.md, research.md (D1–D8), data-model.md, contracts/cli-status.md, quickstart.md

**Tests**: INCLUDED — Constitution Principle VIII (NON-NEGOTIABLE) and the plan's Testing
section mandate unit, integration, byte-identity, and parity-guard tests for this feature.

**Organization**: Tasks are grouped by user story (US1 facts → US2 rule table → US3
JSON/cache) so each story is an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1, US2, US3) — user-story phases only
- Every task names exact file paths

## Path Conventions

Single project, src-layout (Constitution III): `src/bookwright/`, `tests/` at repository
root. All paths below are relative to the repository root.

---

## Phase 1: Setup

**Purpose**: Skeleton for the new subpackage and its test package — no project
initialization needed (the repo, toolchain, and CI gates already exist).

- [X] T001 Create `src/bookwright/status/__init__.py` (docstring-only placeholder; public re-exports land in T012) and `tests/status/__init__.py`, per the plan.md project structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The three behavior-preserving refactors and the envelope helper that every
user story builds on — pipeline extraction (research.md D1), authored-identity records
(D2), pure anchor predicates (D3), and `ok_payload` (D6) — each pinned by tests.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Create `src/bookwright/commands/_graph.py` with a frozen `BuildOutcome` dataclass (`engine: Indexer`, `report: BuildReport`, `research: ResearchResult`) and `build_project_graph(root, manifest) -> BuildOutcome`, extracting the pipeline body of `_build()` from `src/bookwright/commands/graph/build.py` (research.md D1, data-model.md §5)
- [X] T003 Refactor `src/bookwright/commands/graph/build.py` into a thin wrapper over `_graph.build_project_graph`, preserving exact observable behavior — same `BuildReport`, same `bible/graph.ttl` write, same fault model and exit codes; the existing `tests/commands/graph/` suite (test_build.py, test_json_contract.py, test_provenance.py, test_query.py, test_research_build.py) must pass unchanged (depends on T002)
- [X] T004 [P] Extend `src/bookwright/io/research.py` additively: add frozen `FindingIdentity` (`id`, `relpath`, `uri`) and `AnchorIdentity` (`promotes_id`, `constrains: str | None` — authored name / `"timeline"` / `None`, `relpath`, `uri`); `ResearchResult` gains `finding_identities: tuple[FindingIdentity, ...]` and `anchor_identities: tuple[AnchorIdentity, ...]` populated during mapping; existing fields, entity models, and emitted triples untouched (research.md D2, data-model.md §4)
- [X] T005 [P] Extract pure module-level predicates in `src/bookwright/validation/validators/factual_anchor.py`: `anchor_unsourced(...)` and `anchor_under_reliable(...)` (returning the under-reliable/unrated distinction), with the reliability order/rank (`_RELIABILITY_ORDER`/`_RANK`) promoted alongside them; validator methods call the predicates and keep owning message construction and `Violation` assembly (research.md D3)
- [X] T006 [P] Add `ok_payload(**fields) -> dict` returning `{"status": "ok", **fields}` to `src/bookwright/commands/_envelope.py` as the success-side complement of `BookwrightError.to_json()`; do NOT migrate existing `check`/`focus`/`graph` call sites (research.md D6 — scope discipline)
- [X] T007 [P] Extend `tests/io/test_research.py` to cover the new records: authored ids and relpaths captured for every finding/anchor, `constrains` normalization (authored name / `"timeline"` / `None` for dropped links), minted `uri` present as in-process join key, existing `ResearchResult` behavior unchanged (depends on T004)
- [X] T008 [P] Add parity guards in `tests/validation/test_factual_anchor.py`: the extracted predicates' verdicts agree with the validator's R1/R3/R4 violations across the existing case matrix (behavior-preserving refactor pin); full existing suite stays green (depends on T005)
- [X] T009 [P] Add `ok_payload` unit tests in `tests/commands/test_envelope.py`: `"status": "ok"` literal, field passthrough, no mutation of inputs (depends on T006)

**Checkpoint**: Shared pipeline, records, predicates, and envelope helper in place, all
pinned by green tests — user story implementation can begin.

---

## Phase 3: User Story 1 - See the project's derived state at a glance (Priority: P1) 🎯 MVP

**Goal**: `bookwright status` rebuilds the graph from the corpus (refreshing
`bible/graph.ttl`), aggregates the state facts — phase, focus echo, open research
questions, anchor gaps, low-reliability findings, validation summary — and prints a
human-readable report, degrading gracefully on absent information and failing like
`graph build` on corrupt corpora.

**Independent Test**: On `tests/fixtures/tiny-historical` (open questions, anchors,
validation findings), run `bookwright status` and confirm every reported fact matches
what `graph query` / `validate` / `focus show` independently reveal (spec US1
Independent Test, quickstart Scenario 1).

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `src/bookwright/status/model.py`: frozen `GraphFacts`, `OpenQuestion`, `AnchorGap`, `LowReliabilityFinding`, `ValidationSummary`, and `StatusState` with `to_payload() -> dict` emitting `{"count": N, "items": [...]}` per fact (FR-011a), item ordering by corpus-stable keys exactly per data-model.md §2 (`(file, id)` / `(file, promotes, constrains or "")`), no minted URIs, no timestamps
- [X] T011 [US1] Implement `src/bookwright/status/queries.py`: SPARQL aggregations through the `Indexer` protocol (IRIs from `golem.namespaces`, no rdflib import) for open findings (with optional claim) and findings with below-threshold best support; join to authored identity via the D2 identity maps sorted by `(relpath, id)`; anchor gaps via `validation/anchor_queries.load_anchors` / `load_sources_by_anchor` + the extracted `factual_anchor` predicates (problems as sorted subset of `{"unsourced", "under_reliable", "unrated", "missing_finding", "missing_target"}`); validation summary via `discover_validators` / `resolve_active` / `run_validators` — counts per severity zero-filled + sorted `ran`, no violation messages (research.md D3/D8, depends on T010)
- [X] T012 [US1] Re-export the public surface (`StatusState`, fact records, query entry points) from `src/bookwright/status/__init__.py` (depends on T010, T011)
- [X] T013 [US1] Implement the facts leg of `src/bookwright/commands/status.py`: resolve project + manifest; degraded path per research.md D5 (bible dir absent or manuscript signal false ⇒ skip pipeline, `GraphFacts(available=False, 0, 0)`, empty research facts, empty validation summary, exit 0; empty-but-present bible builds normally as degraded); otherwise call `build_project_graph` (refreshing `bible/graph.ttl`) and aggregate `StatusState`; fault mapping per research.md D4 (project/manifest/indexer/research errors propagate as `graph build` — exits 2/3; ≥1 skipped bible file ⇒ `skipped_sources` `BookwrightError` with `details` listing `{path, reason}`, exit 4); human-readable report (phase, focus echo, facts) on stdout, prose/progress on stderr (FR-001–FR-007, FR-013, FR-015)
- [X] T014 [US1] Register the verb in `src/bookwright/cli.py` as `app.command("status")` per contracts/cli-status.md (depends on T013)
- [X] T015 [P] [US1] Unit tests in `tests/status/test_model.py`: payload shapes, `count == len(items)` invariant, deterministic ordering, fixed `counts` key order (`error`/`warning`/`info`), serialized output contains no URIs / timestamps / environment data (depends on T010)
- [X] T016 [P] [US1] Unit tests in `tests/status/test_queries.py` against an in-memory `RdflibIndexer`: open-findings projection, low-reliability membership (unrated ranks below every threshold; only findings with ≥1 source qualify — data-model.md §2.4), anchor-gap problem sets (one row per anchor, all problems aggregated), validation summary counts/ran (depends on T011)
- [X] T017 [US1] Command tests in `tests/commands/test_status.py` (facts leg, fixture copies in tmp_path): tiny-historical known state — phase, focus echo, open questions, anchor gaps, low-reliability findings, validation counts all match the owning tools; tiny-novel v0.2-era (no `[focus]`, no `bible/research/`) succeeds with empty research facts (SC-006); stale `graph.ttl` is refreshed from the corpus (US1-AS2); degraded no-bible state exits 0 with `available: false` (depends on T013, T014)
- [X] T018 [US1] Error-path tests in `tests/commands/test_status_errors.py` (human mode; `--json` envelope assertions extended in T025): not a project ⇒ exit 2; malformed research corpus ⇒ exit 2; skipped bible file (broken front-matter) ⇒ exit 4; slug collision ⇒ exit 3 — exit parity with `graph build` on the same corpus (research.md D4, depends on T013, T014)

**Checkpoint**: `bookwright status` reports correct facts on real fixtures, degrades on
absence, fails on corruption — User Story 1 fully functional and independently testable.

---

## Phase 4: User Story 2 - Get deterministic next-action recommendations (Priority: P2)

**Goal**: A static, pure rule table maps `StatusState` to ordered `next_actions`
(skill + paste-ready English prompt + reason), unit-testable with no graph or project
on disk.

**Independent Test**: Construct synthetic `StatusState` values (e.g., 3 open questions,
no focus) and confirm `next_actions(state)` produces exactly the expected actions, in
the same order, on every call (spec US2 Independent Test, quickstart Scenario 8).

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `src/bookwright/status/rules.py`: frozen `Action` (`skill`, `prompt`, `reason`) and `Rule` (`name`, `applies`, `build`) types; module-level `RULES: tuple[Rule, ...]` in fixed priority order — ① `bootstrap_graph` (graph unavailable or zero entities), ② `research_queue` (open questions ∪ unresolved anchors → `bookwright-research`, prompt listing the queue ids/texts, reason citing the count), ③ `verify_findings` (low-reliability findings → `bookwright-verify`), ④ `review_continuity` (`validation.counts["error"] > 0` → review the bible, `bookwright validate` pointer), ⑤ `define_focus` (no focus → `bookwright focus set`); fixed English prompt templates parameterized only by state facts; `next_actions(state: StatusState) -> list[Action]` walks the tuple with the D5 short-circuit (degraded graph ⇒ at most the bootstrap action per data-model.md §3.2) (FR-008–FR-010, research.md D7)
- [X] T020 [US2] Wire `next_actions` into `src/bookwright/commands/status.py`: compute from the aggregated `StatusState` and render in the human report (empty list is a valid, meaningful answer) (depends on T019)
- [X] T021 [P] [US2] Unit tests in `tests/status/test_rules.py`: iterate `RULES` — every rule exercised by a synthetic `StatusState` with no graph, disk, or project (SC-005); exact actions with exact-match prompt/reason strings, exact order; repeat-call equality (US2-AS5); healthy + focused state ⇒ `[]`; degraded state ⇒ at most the bootstrap action; every emitted action carries all three components (SC-004) (depends on T019)
- [X] T022 [US2] Extend `tests/commands/test_status.py`: known-state fixture yields the exact `next_actions` — `bookwright-research` recommendation whose prompt lists the queue and whose reason cites the count (US2-AS1); focus-less fixture includes the `define_focus` recommendation (US2-AS4) (depends on T020)

**Checkpoint**: Facts + deterministic recommendations work end-to-end — User Stories 1
and 2 independently verifiable.

---

## Phase 5: User Story 3 - Consume the report as machine-readable JSON (Priority: P3)

**Goal**: `status --json` emits exactly one success document
(`{"status":"ok","focus":…,"state":…,"next_actions":…}`) on stdout; every successful
run (both modes) regenerates `.bookwright/cache/status.json` with byte-identical
content; failures use the iteration-018 error envelope.

**Independent Test**: Run `bookwright status --json` — stdout is a single JSON document
of the contracted shape, prose went to stderr, and the cache file holds the same bytes
(spec US3 Independent Test, quickstart Scenarios 2 and 6).

### Implementation for User Story 3

- [X] T023 [US3] Implement the JSON + cache leg in `src/bookwright/commands/status.py`: build the document once via `ok_payload(focus=manifest.focus.model_dump() | None, state=state.to_payload(), next_actions=[...])`; serialize once with `json.dumps(payload, separators=(",", ":")) + "\n"`; write those bytes to `.bookwright/cache/status.json` (`mkdir(parents=True, exist_ok=True)`, plain `Path.write_text`, every successful run in both output modes); under `--json` write the identical bytes to stdout and nothing else (one serialization, two sinks — research.md D6); failures emit the iteration-018 error envelope under `--json` and leave any previous cache file untouched (FR-011, FR-012, FR-014)
- [X] T024 [P] [US3] Extend `tests/commands/test_status.py`: `--json` stdout parses as a single document with exactly the top-level keys `status`/`focus`/`state`/`next_actions` and nothing else on stdout (US3-AS1); double run on an unchanged corpus ⇒ byte-identical stdout across runs, byte-identical cache files, and stdout ≡ cache (SC-002, US3-AS4); human-mode run also regenerates the cache (US3-AS2); missing `.bookwright/cache/` directory is created (depends on T023)
- [X] T025 [P] [US3] Extend `tests/commands/test_status_errors.py`: every contract error row under `--json` emits exactly one `BookwrightError.to_json()` envelope on stdout with the contracted code (`no_project`, `invalid_manifest`, `unknown_indexer` via a manifest naming an unknown engine, the research error's own code, `skipped_sources` with per-file `details`) and the contracted exit (2/2/2/2/4); slug collision exits 3; previous cache file untouched on failure (US3-AS3, contracts/cli-status.md, depends on T023)

**Checkpoint**: All three user stories complete — the command is human-usable,
deterministic, and agent-consumable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cross-tool conformance, corpus-safety proof, end-to-end validation, and
the four CI gates.

- [X] T026 [P] SC-003 parity tests in `tests/commands/test_status.py`: after a `status` run, `state.validation.counts` equals `bookwright validate --json`'s by-severity counts on the same corpus, and the top-level `focus` equals `focus show --json`'s `focus` (contracts conformance test 6)
- [X] T027 [P] SC-007 corpus-untouched test in `tests/commands/test_status.py`: every file under the manifest, `bible/`, `bible/research/`, and `manuscript/` is byte-identical before and after a run — only `bible/graph.ttl` and `.bookwright/cache/status.json` change (contracts conformance test 7)
- [X] T028 Execute quickstart.md Scenarios 1–8 end-to-end on scratch fixture copies (`/tmp/qs-*`) and confirm every stated expectation, including the three silent `cmp`s of Scenario 2
- [X] T029 Run all four gates and fix any fallout: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥ 80 % coverage); verify every new/modified source file stays well under 500 lines (Constitution IV, VIII)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately
- **Foundational (Phase 2)**: depends on Setup; **blocks all user stories**. Within it: T003 depends on T002; T007/T008/T009 depend on T004/T005/T006 respectively
- **US1 (Phase 3)**: depends on Phase 2 (T013 consumes T002's `build_project_graph`, T011 consumes T004's identity tuples and T005's predicates)
- **US2 (Phase 4)**: depends on US1's `StatusState` (T010) and command module (T013); independently testable via synthetic states (T021 needs only T019 + T010)
- **US3 (Phase 5)**: depends on US1 + US2 (the document embeds state and next_actions) and Phase 2's T006 (`ok_payload`)
- **Polish (Phase 6)**: depends on all three stories

### Within Each User Story

- Models before queries before command orchestration (T010 → T011 → T013)
- Command registered (T014) before command-level tests (T017, T018)
- Pure rule table (T019) before wiring (T020); its unit tests (T021) need only the table

### Parallel Opportunities

- Phase 2: T004, T005, T006 touch disjoint files — fully parallel after T001; T007, T008, T009 parallel once their counterparts land
- US1: T010 starts immediately after Phase 2; T015 ∥ T016 once T010/T011 land; T017 ∥ T018 once T014 lands (different test files)
- US2: T019 ∥ anything in US1 test work (new file); T021 ∥ T020
- US3: T024 ∥ T025 (different test files)
- Polish: T026 ∥ T027

---

## Parallel Example: Phase 2 (Foundational)

```bash
# After T001, launch the three disjoint refactors together:
Task: "Extend src/bookwright/io/research.py with FindingIdentity/AnchorIdentity"  # T004
Task: "Extract pure predicates in validation/validators/factual_anchor.py"        # T005
Task: "Add ok_payload() to src/bookwright/commands/_envelope.py"                  # T006

# Then their test pins together:
Task: "Record coverage in tests/io/test_research.py"                              # T007
Task: "Parity guards in tests/validation/test_factual_anchor.py"                  # T008
Task: "ok_payload tests in tests/commands/test_envelope.py"                       # T009
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (T001) + Phase 2 (T002–T009) — the shared refactors, each pinned green
2. Phase 3 (T010–T018) — `bookwright status` reports correct facts
3. **STOP and VALIDATE**: quickstart Scenario 1 facts (minus next_actions), Scenario 5 degraded, Scenario 7 corpus-untouched
4. MVP delivers standalone value: the derived state at a glance

### Incremental Delivery

1. Setup + Foundational → all existing suites still green (refactors are behavior-preserving)
2. US1 → facts report (MVP)
3. US2 → deterministic recommendations (the "what next" half)
4. US3 → `--json` contract + cache (agent-consumable; unblocks iterations 021–022)
5. Polish → conformance, quickstart, four gates → ready for `/speckit-analyze` and merge

---

## Notes

- Tests are mandatory here (Constitution VIII); the refactor tasks (T002–T006) are
  behavior-preserving and pinned by existing suites plus the new guards (T007–T009)
- Exact prompt wording for the rule table is fixed at implementation time (T019) and
  pinned by exact-match tests (T021) — determinism requires *fixed* templates, not any
  particular wording (data-model.md §3.2)
- The report must never contain minted URIs, timestamps, or environment data
  (research.md D2); T015/T024 enforce this
- Commit after each task or logical group (the auto-git hooks offer this between phases)
