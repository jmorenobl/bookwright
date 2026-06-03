---
description: "Task list for the validation system feature"
---

# Tasks: Validation System

**Input**: Design documents from `/specs/010-validation-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/validator-protocol.md, contracts/cli-validate.md, quickstart.md

**Tests**: REQUIRED. The spec's Success Criteria (SC-001..008), the plan's Testing
section, and Constitution Principle VIII (≥80% coverage, non-negotiable) all mandate
tests. Each validator gets a violation fixture + a clean fixture; the command gets
integration tests for `--json` / `--scope` / `--severity` / exit-code gating.

**Organization**: Tasks are grouped by user story (US1 P1 → US2 P2 → US3 P3) for
independent implementation and testing. The subsystem is one cohesive engine, so
US2/US3 extend files US1 created (incremental delivery), but each story stays
independently testable through the `bookwright validate` command.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (Setup, Foundational, Polish carry no story label)
- Exact file paths are given in every task

## Path Conventions

Single project, src-layout (Constitution III): production code under
`src/bookwright/`, tests under `tests/` at the repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package skeleton so subsequent modules import cleanly.

- [ ] T001 Create the validation package + test skeleton: `src/bookwright/validation/__init__.py` (placeholder), `src/bookwright/validation/validators/__init__.py`, `tests/validation/__init__.py`, and an empty `tests/validation/conftest.py` stub, per plan.md Project Structure.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core types, namespaces, graph helpers, discovery, and the runner that
EVERY user story depends on.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [ ] T002 Implement core finding types in `src/bookwright/validation/base.py`: `Severity` str-Enum with `_RANK` + `at_least()` (error>warning>info), frozen `Violation` (validator/severity/message/source/triples) with `source_file()`/`source_line()`/`to_json()`, frozen `ValidatorError` (validator/message/phase), the `@runtime_checkable` `Validator` Protocol (name, severity_default, `validate(project, indexer)`), and `UnknownValidatorError(names)` with `to_json()` — per data-model.md and contracts/validator-protocol.md.
- [ ] T003 Implement `ValidationContext` in `src/bookwright/validation/base.py` (depends on T002): `root` + `manifest` with lazily-cached accessors `bible()`, `character_names()`, `setting_names()`, `manuscript_files()` (glob `**/*.md` under manuscript dir, sorted, skip unreadable), `constitution_text()`; paths from `manifest.paths`, `uri_base` from `manifest.bookwright` — per data-model.md.
- [ ] T004 [P] Extend `src/bookwright/golem/namespaces.py`: add `TR` and `CSM` namespaces and the frozen constants `DURATION`, `TEMPORAL_LOCATION`, `FOLLOWS`, `PRECEDES`, `TEMPORALLY_OVERLAPS`, `TEMPORALLY_INCLUDES`, `TEMPORALLY_INCLUDED_IN`, plus `"TimeInterval": DLP["time-interval"]` in `CLASS_IRI`; verify every added term is in `frozen_terms()` (D11). Do NOT add `crm:P4_has_time-span` or CIDOC P82a/P82b/P81/P79/P80.
- [ ] T005 [P] Implement `src/bookwright/validation/queries.py` (depends on T002, T004): frozen `EventInterval(uri, begin, end)`, `load_intervals(indexer)` (gYear reachable via `(CSM:duration|TR:temporal-location)/TR:temporal-location/{boundary}` typed by `crm:P2_has_type` begin/end, then `(P90_has_value | P43_has_dimension/P90_has_value)`), `load_relations(indexer)` (the five `TR:*` edge sets keyed by localname), and `resolve_source(indexer, uri)` reading the CIDOC provenance edge (D6) → `relpath[:line]|None`.
- [ ] T006 Implement discovery in `src/bookwright/validation/registry.py` (depends on T002): `discover_validators(custom_dir)` → `(builtins, customs, list[ValidatorError])` — built-ins via `pkgutil.iter_modules` over `bookwright.validation.validators` collecting protocol-conforming instances (sorted, D8); customs via `importlib.util.spec_from_file_location` over sorted `*.py` under `<root>/.bookwright/validators/`, with import failure / no-conforming-object / duplicate-name surfaced as `ValidatorError(phase="load")` and skipped (FR-004/005, contract). A custom whose `name` collides with a built-in is skipped as `ValidatorError(load)` ("collides with a built-in; rename it") — **built-in wins, never silently shadowed** — so the returned built-in / custom dicts are disjoint by name (D2).
- [ ] T007 Implement `src/bookwright/validation/runner.py` (depends on T002, T003): `run_validators(active, project, indexer)` runs each validator under per-validator try/except isolation (FR-014, D9), collecting `list[Violation]` and `list[ValidatorError](phase="run")`; deduplicate identical `Violation` values and return the list sorted by the explicit total-order key `(validator, severity-rank descending, source or "", message, triples)` so SC-003 is byte-identical across runs/platforms (D8) — not a bare "stable sort".
- [ ] T008 [P] Write `tests/validation/test_base.py` (depends on T002, T003): `Severity` ordering + `at_least` threshold, `Violation` shape / `to_json` / `source_file`/`source_line` split, `ValidationContext` cached accessors over a scaffolded project.

**Checkpoint**: Engine primitives ready — user stories can begin.

---

## Phase 3: User Story 1 - Detect internal inconsistencies on demand (Priority: P1) 🎯 MVP

**Goal**: A single `bookwright validate` runs the four built-in validators and prints
a grouped, human-readable report naming each inconsistency (location, rule, why); a
clean project reports none. Exit 0/1 gates on error-severity findings.

**Independent Test**: On a project with one deliberately injected inconsistency of
each kind, the human report names each with its location, rule, and explanation
(SC-001); a fully consistent project reports zero and exits 0 (SC-002).

### Indexer-gap closure (gives `temporal` real graph data — D1/D11/D12)

- [ ] T009 [US1] Extend `NarrativeEvent` in `src/bookwright/golem/modules/event.py` (depends on T004): add optional `begin`/`end` int years and the five relation refs (`follows`/`precedes`/`overlaps`/`includes`/`included_in`) as multi `cross_refs` (one frozen `TR:*` predicate each), plus a custom `to_triples()` emitting the closure-safe typed-boundary interval (`CSM:duration` → `dlp:time-interval`; each present boundary self-labelled via `crm:P2_has_type` begin/end and carrying one `xsd:gYear` through the existing `Dimension`/`gyear_literal()` pattern). Open intervals emit only the known boundary.
- [ ] T010 [US1] Extend the timeline mapper in `src/bookwright/io/bible.py` (depends on T009): read optional `begin:`/`end:`/`date:` and the five relation keys from each `events:` item; coerce years via `_coerce_year`; enforce `date` ↔ `begin`/`end` mutual exclusivity (both → soft warning, `date` ignored); resolve relation lists through the existing `slug_index` (unresolved name → `UnresolvedParticipant`-style soft warning, no abort); add the new keys to `ITEM_KEYS`.

### Built-in validators

- [ ] T011 [P] [US1] Implement `src/bookwright/validation/validators/temporal.py` (depends on T005): pure graph consumer reading `load_intervals` + `load_relations`, emitting one `error` `Violation` per FR-015 contradiction — (a) `follows`/`precedes` cycle, (b) pair both strictly ordered and `temporally-overlaps`, (c) containment conflicting with strict order, (d) numeric begin/end contradicting a declared relation — with `triples` carrying the implicated edges and `source` via `resolve_source` or `None`; deduped, never consults document order (D12).
- [ ] T012 [P] [US1] Implement `src/bookwright/validation/validators/character_presence.py` (depends on T002, T003): roster from `project.character_names()`; word-boundary regex per name over `project.manuscript_files()`. Bible name never matched → orphan finding at **error**; conservative proper-noun candidate (pinned heuristic, D3: `\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b`, non-sentence-initial, not in the stop-set, no roster slug-match) → unknown-mention at **warning** (D3, FR-016). **Collapse unknown-mentions per distinct name** — one finding per name citing the first occurrence, not one per mention (edge case "not multiplied per mention"). `severity_default = error`.
- [ ] T013 [P] [US1] Implement `src/bookwright/validation/validators/setting_continuity.py` (depends on T002, T003): per `project.setting_names()`, scan manuscript for a descriptor from a small built-in contradiction lexicon (antonym groups, e.g. coastal/inland); same setting tagged with two terms from one group across different files → `warning` citing both `file:line` (D4, FR-017). `severity_default = warning`.
- [ ] T014 [P] [US1] Implement `src/bookwright/validation/validators/focalization.py` (depends on T002, T003): parse the constitution declaration line under **either** label (case-insensitive) — Spanish "Voz narrativa" or English "Narrative voice" — for declared person + focal character; flag first-person pronouns outside dialogue when third-person declared, and interiority verbs on a non-focal bible character (head-hopping) under third-person-limited; no parsable declaration → zero findings (D5, FR-018, edge case). `severity_default = warning`.

### Report, command wiring, package exports

- [ ] T015 [US1] Implement `src/bookwright/validation/report.py` ValidationReport (depends on T002): `violations`/`errors`/`ran`, the `failed` gate property (any `severity == error`, pre-filter, FR-013), and `render(console)` grouping findings by validator for a human reader (FR-012). (Filters + JSON land in US2.)
- [ ] T016 [US1] Fill `src/bookwright/validation/__init__.py` re-exports (depends on T002, T006, T007): `Severity`, `Violation`, `ValidatorError`, `Validator`, `ValidationContext`, `discover_validators`, `run_validators` (the quickstart imports `from bookwright.validation import Severity, Violation`).
- [ ] T017 [US1] Implement `src/bookwright/commands/validate.py` (depends on T006, T007, T015, T016): locate project root, load `manifest.toml`, resolve the indexer from `manifest.bookwright.indexer` loading `manifest.paths.graph` if present else an empty indexer (no-graph edge → zero graph findings), `discover_validators`, run all discovered built-ins via the runner, render the human report to stdout with progress on stderr, exit 0/1 per the gate. (Config resolution → US3; flags → US2.)
- [ ] T018 [US1] Register the command in `src/bookwright/cli.py` via `app.command("validate")(validate.run)` (depends on T017).

### Tests for User Story 1

- [ ] T019 [P] [US1] Build `tests/validation/conftest.py` (depends on T003): project-scaffold builder + per-validator violation and clean fixtures (timeline with a temporal contradiction, manuscript mention with no bible entry, orphan bible entry, coastal/inland setting, head-hopping prose, plus a fully clean project).
- [ ] T020 [P] [US1] Write `tests/validation/test_temporal.py` (depends on T011, T010): FR-015 rules a–d **each pinned to SC-009** (one fixture per rule → exactly one `error` finding carrying the implicated relation edge(s) in `triples`; a clean timeline → zero temporal findings), an open (begin-only/end-only) interval, and end-to-end (write `bible/timeline.md` → build graph → validate reports the contradiction with source location).
- [ ] T021 [P] [US1] Write `tests/validation/test_character_presence.py` (depends on T012): orphan-in-bible → error, unknown manuscript mention → warning, clean project → none; **an unknown name appearing on several lines yields exactly one warning citing the first occurrence** (dedup-per-name, "not multiplied per mention" edge case).
- [ ] T022 [P] [US1] Write `tests/validation/test_setting_continuity.py` (depends on T013): coastal/inland contradiction → warning citing both locations; consistent setting → none.
- [ ] T023 [P] [US1] Write `tests/validation/test_focalization.py` (depends on T014): head-hopping / first-person-in-third-person → warning; an English `Narrative voice: third person limited` declaration parses equivalently to the Spanish one (bilingual, E7/D5); no parsable "Voz narrativa"/"Narrative voice" line → zero findings (edge case).
- [ ] T024 [P] [US1] Write `tests/validation/test_runner.py` (depends on T007, T011-T014): per-validator isolation — a raising validator yields a `ValidatorError` while others still produce findings (FR-014); dedup of identical violations (D13.1).
- [ ] T025 [P] [US1] Extend `tests/golem/test_triples.py` (depends on T009): a `NarrativeEvent` with begin/end + a `follows` ref emits the typed-boundary interval (gYear via Dimension) and the frozen `TR:follows` edge.
- [ ] T026 [P] [US1] Extend `tests/golem/test_namespaces.py` (depends on T004): `FOLLOWS`, `TEMPORALLY_OVERLAPS`, `TEMPORAL_LOCATION`, `DURATION`, and `TimeInterval` are all in `frozen_terms()`.
- [ ] T027 [P] [US1] Extend `tests/io/test_bible.py` (depends on T010): timeline `begin`/`end`/`date` + the five relation keys map correctly; `date` + `begin`/`end` together warns; an unresolved relation name produces a soft warning.
- [ ] T028 [US1] Write `tests/validation/test_command.py` baseline (depends on T017, T018): a project with one injected inconsistency **per built-in validator** (temporal, character_presence, setting_continuity, focalization) → human report names each with validator/rule/why and a location **or** the implicated events, and exits 1 (SC-001); a **location-less** finding (a `follows` cycle) still renders its rule and implicated events (FR-003/FR-012); a clean project → "no violations found" and exit 0 (SC-002).

**Checkpoint**: `bookwright validate` delivers the core human-readable coherence report — MVP complete and independently demoable.

---

## Phase 4: User Story 2 - Machine-readable results for CI and editors (Priority: P2)

**Goal**: `--json` emits a single structured document on stdout (prose on stderr);
`--scope` and `--severity` narrow the displayed report; the exit code gates on the
unfiltered error set so a filter can never hide an error from CI.

**Independent Test**: `--json` on a mixed-severity project → one parseable document,
one entry per reported violation, nothing else on stdout (SC-004); `--scope file`
reduces findings to that file (SC-005); `--severity error` excludes warnings/info;
an error-severity run signals failure regardless of filters (SC-006).

### Implementation for User Story 2

- [ ] T029 [US2] Extend `src/bookwright/validation/report.py` (depends on T015): frozen `ScopeFilter(rel, is_dir, matches)` (False for `source=None` — location-less omitted under scope, FR-009), `reported(*, scope, severity)` applying scope then the `Severity.at_least` threshold (FR-010), and `to_json(*, scope, severity)` emitting the `status`/`failed`/`violations`/`errors`/`summary` shape (total vs reported, `by_severity` over the unfiltered set, **always emitting all three severity keys — 0 when absent — for a shape-stable document**) per data-model.md / contracts/cli-validate.md.
- [ ] T030 [US2] Extend `src/bookwright/commands/validate.py` (depends on T017, T029): add `--scope`/`--severity`/`--json` options; resolve `--scope` under the root (non-existent / outside project → `empty_scope`, exit 2, D10); under `--json` emit exactly one JSON document on stdout with all prose on stderr (Principle IX); add the exit-2 JSON/human error envelopes (`no_project`, `invalid_manifest`, `empty_scope`); keep the gate computed from the unfiltered set (FR-013).
- [ ] T031 [P] [US2] Write `tests/validation/test_report.py` (depends on T029): scope filtering (incl. location-less omission), severity threshold ordering, composed `--scope` ∧ `--severity` intersection with the gate unaffected (D13.3), and `to_json` summary counts.
- [ ] T032 [US2] Extend `tests/validation/test_command.py` (depends on T030): `--json` is a single parseable document with prose on stderr (SC-004); `--scope` and `--severity` narrow the report; exit 1 on any unfiltered error even when filtered out (SC-006); no-`graph.ttl` project → exit 0 / zero graph findings (D13.2); FR-020 — a full run (human and `--json`) leaves the project tree byte-identical (D13.4); a re-run yields byte-identical `violations[]` ordering (SC-003); a `--scope` that is absent or outside the project → exit 2 `empty_scope`, **while a valid in-project scope with no violations → exit 0 with an empty report** (the two branches MUST be distinguished, D10).

**Checkpoint**: Results are CI- and editor-consumable; US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Configure and extend which validators run (Priority: P3)

**Goal**: `[validators]` in the manifest (enabled/disabled/custom) governs the active
set, and custom `.py` validators dropped in `.bookwright/validators/` run alongside
built-ins; an unknown configured name is a clear exit-2 error.

**Independent Test**: Disabling a built-in removes its findings (SC-008); a custom
validator file is discovered, run, and reported (SC-007); a malformed custom file is
skipped with an attributed message and does not crash; an enabled name that does not
exist → exit 2 (FR-007).

### Implementation for User Story 3

- [ ] T033 [US3] Implement `resolve_active(builtins, customs, cfg)` in `src/bookwright/validation/registry.py` (depends on T006): apply the D7 algorithm — `custom` non-empty allow-lists customs; `candidates = builtins ∪ customs` minus `disabled`; non-empty `enabled` intersects; any `enabled`/`disabled`/`custom` name absent from `builtins ∪ customs` raises `UnknownValidatorError`; return the active list sorted by `name` (FR-006/007, D8).
- [ ] T034 [US3] Wire config into `src/bookwright/commands/validate.py` (depends on T030, T033): call `resolve_active` with `manifest.validators` so the run honors `[validators]`; surface `UnknownValidatorError` as the `unknown_validator` exit-2 envelope (JSON + human); custom load failures appear in the report's `errors[]` without aborting.
- [ ] T035 [P] [US3] Write `tests/validation/test_registry.py` (depends on T033, T006): built-in auto-discovery; empty `enabled` = all built-ins; non-empty `enabled` intersects; `disabled` subtracts; `custom` allow-list; unknown name → `UnknownValidatorError`; malformed custom file → `ValidatorError(load)` skip; a custom validator named like a built-in → skipped with an attributed load error while the built-in still runs (cross-tier collision, built-in wins); a conforming custom file is discovered and returned.
- [ ] T036 [US3] Extend `tests/validation/test_command.py` (depends on T034): disabling a built-in removes its findings (SC-008); a dropped-in custom validator's findings appear (SC-007); a malformed custom file → attributed `errors[]` entry, no crash; an unknown configured name → exit 2 with the `unknown_validator` envelope.

**Checkpoint**: All three stories independently functional; the subsystem is configurable and extensible.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates and docs across the whole feature.

- [ ] T037 [P] Run `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy --strict src tests` over the new `validation/` package, `commands/validate.py`, and the edited `golem`/`io` modules; fix all findings (CI gates, CLAUDE.md).
- [ ] T038 [P] Confirm ≥80% coverage for `src/bookwright/validation/` (Constitution VIII) via `uv run pytest --cov=bookwright.validation`; add targeted unit tests for any uncovered branch.
- [ ] T039 Execute quickstart.md end-to-end against a scaffolded project (run a validation, `--json`, `--scope`, `--severity`, configure `[validators]`, drop in the `no_todo` custom validator) and confirm each documented behavior matches.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; BLOCKS all user stories.
- **User Story 1 (Phase 3)**: depends on Foundational. The MVP.
- **User Story 2 (Phase 4)**: depends on US1 (extends report.py + validate.py).
- **User Story 3 (Phase 5)**: depends on US1 (extends registry.py + validate.py); independent of US2.
- **Polish (Phase 6)**: depends on all desired stories being complete.

### Within Each User Story

- Indexer-gap (T009→T010) before `temporal` end-to-end tests.
- Validators (T011-T014) before the runner test (T024) and command test (T028).
- `report.py`/`__init__.py` before the command; command before its tests.

### Parallel Opportunities

- Foundational: T004 (namespaces), T005 (queries), and T008 (test_base) run in parallel after T002/T003.
- US1 validators T011-T014 are four parallel files; test files T020-T027 are parallel once their targets exist.
- US2 T031 (test_report) parallel with command work once T029 lands.
- US3 T035 (test_registry) parallel once T033 lands.

---

## Parallel Example: User Story 1

```bash
# The four built-in validators are independent files:
Task: "Implement temporal.py validator (T011)"
Task: "Implement character_presence.py validator (T012)"
Task: "Implement setting_continuity.py validator (T013)"
Task: "Implement focalization.py validator (T014)"

# Then their tests, also parallel:
Task: "test_temporal.py (T020)"
Task: "test_character_presence.py (T021)"
Task: "test_setting_continuity.py (T022)"
Task: "test_focalization.py (T023)"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup (T001) → Foundational (T002-T008).
2. US1 (T009-T028): indexer-gap closure, four validators, runner, human report, command.
3. **STOP and VALIDATE**: inject one inconsistency of each kind, run `bookwright validate`, confirm the report (SC-001) and a clean project exits 0 (SC-002).

### Incremental Delivery

1. Foundation ready.
2. US1 → human coherence report (MVP).
3. US2 → `--json` / `--scope` / `--severity` + CI gate.
4. US3 → manifest config + custom validators.
5. Polish → lint/type/coverage gates + quickstart validation.

---

## Notes

- [P] = different files, no dependency on incomplete tasks.
- Tests are required (Constitution VIII); write them with each story and confirm they fail before implementing where practical.
- The subsystem writes nothing (FR-020); a full run must leave the project tree byte-identical (T032).
- Determinism (FR-019/SC-003): stable sort of discovery, file iteration, and emitted findings; dedup identical violations.
- Commit after each task or logical group; the `after_tasks` hook will offer a commit when this file lands.
