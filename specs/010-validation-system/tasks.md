---
description: "Task list for the Validation System feature (iteration 11)"
---

# Tasks: Validation System

**Input**: Design documents from `/specs/010-validation-system/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓ (D1–D11), data-model.md ✓,
contracts/ ✓ (`validator-protocol.md`, `cli-validate.md`), quickstart.md ✓

**Tests**: REQUIRED. Constitution Principle VIII mandates ≥80 % coverage and test
discipline; the plan's Testing section pins one violation + one clean fixture per
validator and integration tests for the command. Test tasks are therefore included.

**Organization**: Tasks are grouped by user story. Foundational phase builds the
shared engine (base types, context, queries, runner, report, registry) and the
deliberate indexer-gap closure (research D1/D11); the three user stories layer the
validators, the command surface, and the configuration/extension behaviour on top.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (omitted for Setup, Foundational, Polish)
- All paths are repository-relative (single project, src-layout — Constitution III)

## Path Conventions

- Production code: `src/bookwright/…`
- Tests: `tests/…` at repository root
- Custom validators (runtime, user-authored): `<project>/.bookwright/validators/*.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package skeleton so every later task has a home.

- [ ] T001 Create the `validation` package skeleton: empty `src/bookwright/validation/__init__.py`, `src/bookwright/validation/validators/__init__.py`, and `tests/validation/__init__.py` (placeholders, filled in later phases)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared engine and the indexer-gap closure. **No user story can
begin until this phase completes** — every validator and the command depend on the
base types, context, runner, report, and registry, and `temporal` depends on the
graph signals emitted by the closure.

**⚠️ CRITICAL**: Blocks all of US1/US2/US3.

### Core types and context (`base.py`)

- [ ] T002 Implement `Severity` (str Enum: error/warning/info), module-level `_RANK` ordinal, and `Severity.at_least(threshold)` in `src/bookwright/validation/base.py` (data-model.md "Severity"; FR-010 threshold, FR-013 gate)
- [ ] T003 Implement the frozen `Violation` dataclass (validator, severity, message, source, triples) with `source_file()` / `source_line()` helpers and `to_json()` in `src/bookwright/validation/base.py` (data-model.md "Violation"; FR-002/003, SC-004)
- [ ] T004 Implement `ValidatorError` (validator, message, phase=load|run), the `@runtime_checkable` `Validator` Protocol (name, severity_default, `validate(project, indexer)`), and `UnknownValidatorError(names)` with `to_json()` in `src/bookwright/validation/base.py` (data-model.md; contracts/validator-protocol.md; FR-001, FR-007, FR-014)
- [ ] T005 Implement `ValidationContext` (root, manifest + lazily-cached `bible()`, `character_names()`, `setting_names()`, `manuscript_files()`, `constitution_text()` accessors, sorted/deduped per D8) in `src/bookwright/validation/base.py`, reading paths from `manifest.paths` and `uri_base` from `manifest.bookwright`, defensively skipping unreadable files (data-model.md "ValidationContext")
- [ ] T006 Re-export `Severity, Violation, ValidatorError, Validator, ValidationContext, UnknownValidatorError, discover_validators, resolve_active, run_validators` from `src/bookwright/validation/__init__.py` (plan Source Code map; supports the quickstart custom-validator import surface)

### Indexer-gap closure (research D1/D11 — extends existing iter-5/6 modules)

- [ ] T007 [P] Add the temporal namespace + predicate constants to `src/bookwright/golem/namespaces.py`: `TR` namespace, `FOLLOWS`, `TEMPORALLY_OVERLAPS`, `TEMPORAL_LOCATION`; add them to `__all__`; confirm each resolves inside `frozen_terms()` (do NOT add `crm:P4_has_time-span` — not frozen, D11)
- [ ] T008 Extend `NarrativeEvent` in `src/bookwright/golem/modules/event.py` with optional `date: int | None`, `follows`, `overlaps` fields and emit closure-safe triples: `event TR:temporal-location {uri}/time-span`, `{uri}/time-span crm:P90_has_value "<year>"^^xsd:gYear` (reuse `gyear_literal()`/`HAS_VALUE`), and one `TR:follows` / `TR:temporally-overlaps` edge per relation (data-model.md "NarrativeEvent"; depends on T007)
- [ ] T009 Extend the `timeline.md` mapper in `src/bookwright/io/bible.py` to read optional `date:` / `follows:` / `overlaps:` keys (widen `ITEM_KEYS`), resolve `follows`/`overlaps` event names through the existing slug index, and emit `UnresolvedParticipant`-style soft warnings for unresolved refs (no abort) (data-model.md; D1; depends on T007, T008)

### Engine (`queries.py`, `runner.py`, `report.py`, `registry.py`)

- [ ] T010 [P] Implement `src/bookwright/validation/queries.py`: read-only import of the temporal predicates, `resolve_source(indexer, uri) -> str | None` via the CIDOC provenance edge (`crm:P140_assigned_attribute_to` ← `crm:P16_used_specific_object`, prefer line-bearing, D6), and helpers to read each event's gYear (via `temporal-location → P90_has_value`) and its `follows`/`temporally-overlaps` edges (depends on T002–T004, T007)
- [ ] T011 [P] Implement `src/bookwright/validation/runner.py`: `run_validators(active, context, indexer)` running each validator under per-validator try/except (raises → `ValidatorError(phase="run")`, never abort — FR-014/D9), then dedupe identical `Violation`s and stable-sort by `(validator, source, message)` (D8) (depends on T002–T004)
- [ ] T012 [P] Implement `src/bookwright/validation/report.py`: `ScopeFilter(rel, is_dir, matches())` (None → False, D10) and `ValidationReport` (`violations`, `errors`, `ran`; `failed` gate = any pre-filter error-severity violation; `reported(scope, severity)` = scope then severity threshold; `to_json(scope, severity)`; `render(console, scope, severity)` grouped by validator) (data-model.md "ValidationReport"/"ScopeFilter"; FR-009/010/012/013, SC-004; depends on T002–T004)
- [ ] T013 [P] Implement `src/bookwright/validation/registry.py`: `discover_validators(custom_dir)` (built-ins via `pkgutil.iter_modules` over `validation.validators`; customs via `importlib.util.spec_from_file_location` over sorted `*.py`; duplicate-name and malformed/non-conforming files → attributed `ValidatorError(phase="load")`, skipped — D2/D9, SC-007) and `resolve_active(builtins, customs, cfg)` implementing the D7 config algorithm, sorted by name (D8), raising `UnknownValidatorError` for any referenced name ∉ discovered set (FR-004/005/006/007; depends on T002–T004)

### Foundational unit tests

- [ ] T014 [P] Unit-test Severity ordering/`at_least`, `Violation` shape + `to_json` + dedupe hashability, and `ValidationContext` accessors in `tests/validation/test_base.py` (depends on T002–T005)
- [ ] T015 [P] Extend `tests/golem/test_namespaces.py` to assert `FOLLOWS`, `TEMPORALLY_OVERLAPS`, `TEMPORAL_LOCATION` ∈ `frozen_terms()` (D11; depends on T007)
- [ ] T016 [P] Extend `tests/golem/test_triples.py` to assert a dated `NarrativeEvent` emits `temporal-location`/time-span/`gYear` and one `follows`/`temporally-overlaps` edge per relation (depends on T008)
- [ ] T017 [P] Extend `tests/io/test_bible.py` to cover `timeline.md` `date:`/`follows:`/`overlaps:` mapping and the unresolved-ref soft warning (depends on T009)

**Checkpoint**: Engine + closure complete and unit-tested. User stories can begin.

---

## Phase 3: User Story 1 — Detect internal inconsistencies on demand (Priority: P1) 🎯 MVP

**Goal**: A writer runs one command and gets a clear, grouped, human-readable report
naming every inconsistency (location, rule, why); a clean project reports none.

**Independent Test**: On a project with one deliberately injected inconsistency of
each of the four kinds, `bookwright validate` (default human mode) reports all four
with correct locations and explanations; a clean project prints "no violations
found" and exits 0 (spec US1; SC-001/SC-002).

### The four built-in validators

- [ ] T018 [P] [US1] Implement `temporal` (severity_default=error) in `src/bookwright/validation/validators/temporal.py`: pure graph consumer using `queries.py` — flag an event whose declared year is earlier than an event it is asserted to `follows`, and cycles in `follows`; attach source via `resolve_source` (FR-015; D11; contract table)
- [ ] T019 [P] [US1] Implement `character_presence` (severity_default=error) in `src/bookwright/validation/validators/character_presence.py`: word-boundary regex per bible roster name over manuscript prose; orphan bible entry → **error**, unknown proper-noun mention (non-sentence-initial, stop-set excluded) → **warning**; dedupe per candidate (FR-016; D3)
- [ ] T020 [P] [US1] Implement `setting_continuity` (severity_default=warning) in `src/bookwright/validation/validators/setting_continuity.py`: built-in ES+EN contradiction lexicon (antonym frozensets); same setting tagged with ≥2 terms from one group across different files → one warning per pair citing both `file:line` (FR-017; D4)
- [ ] T021 [P] [US1] Implement `focalization` (severity_default=warning) in `src/bookwright/validation/validators/focalization.py`: parse constitution "Voz narrativa" line for declared person + optional focal bible character; flag first-person pronouns outside quoted dialogue under declared third person, and interiority verbs attached to a non-focal character under third-limited (FR-018; D5)

### The command

- [ ] T022 [US1] Implement `bookwright validate` (default human mode) in `src/bookwright/commands/validate.py`: locate project root, load manifest, resolve indexer + load `paths.graph` (empty engine if absent — "no graph" edge case), discover built-ins + `resolve_active`, build `ValidationContext`, `run_validators`, `report.render(...)` to stdout, exit via the `failed` gate (0/1) (FR-008/012; cli-validate.md Behaviour; depends on T010–T013, T018–T021)
- [ ] T023 [US1] Register the command in `src/bookwright/cli.py` via `app.command("validate")(validate.run)` (cli-validate.md; depends on T022)

### US1 tests

- [ ] T024 [US1] Add project scaffolds + per-validator violation/clean fixtures (including a `timeline.md` with `date:`/`follows:` driving a real `graph build` for `temporal`) in `tests/validation/conftest.py` (plan Testing; D1 end-to-end; depends on T018–T021)
- [ ] T025 [P] [US1] Test `temporal` end-to-end (timeline.md → graph build → validate): injected earlier-follows-later + `follows` cycle, plus clean fixture, in `tests/validation/test_temporal.py` (SC-001/003; depends on T018, T024)
- [ ] T026 [P] [US1] Test `character_presence`: orphan→error + unknown-mention→warning + clean, in `tests/validation/test_character_presence.py` (SC-001; depends on T019, T024)
- [ ] T027 [P] [US1] Test `setting_continuity`: coastal/inland contradiction across files + clean, in `tests/validation/test_setting_continuity.py` (SC-001; depends on T020, T024)
- [ ] T028 [P] [US1] Test `focalization`: head-hopping / person-mismatch + clean, in `tests/validation/test_focalization.py` (SC-001; depends on T021, T024)
- [ ] T029 [US1] Integration test: full human report names all four injected findings with locations; clean project → "no violations" + exit 0; one raising validator is surfaced as an error without aborting the run (FR-014 edge case), in `tests/validation/test_command.py` (SC-001/002; depends on T022, T024)

**Checkpoint**: MVP. A writer can run validation and act on a real, deterministic
human report. Independently testable end-to-end.

---

## Phase 4: User Story 2 — Machine-readable results for CI and editors (Priority: P2)

**Goal**: Structured output plus scope/severity narrowing and a CI-gating exit code.

**Independent Test**: With mixed-severity findings, `--json` emits a single parseable
document (one entry per reported violation, no prose on stdout); `--scope FILE`
limits reported findings to that file; `--severity error` excludes warnings/info;
an error-severity run exits 1, a warning-only run exits 0 (spec US2; SC-004/005/006).

### Implementation

- [ ] T030 [US2] Extend `src/bookwright/commands/validate.py` with `--json`, `--scope PATH`, `--severity LEVEL` options: route prose to stderr and one JSON doc to stdout under `--json` (Principle IX), build/validate the `ScopeFilter` (non-existent/outside-project scope → `empty_scope`, exit 2 — D10), pass scope+severity to `report.to_json`/`render`, and keep the exit gate computed from the **unfiltered** set (FR-009/010/011/013; cli-validate.md envelopes; depends on T022)

### US2 tests

- [ ] T031 [P] [US2] Unit-test `ValidationReport` scope filtering (location-less omitted under scope), severity threshold, and the pre-filter `failed` gate in `tests/validation/test_report.py` (FR-013, SC-005; depends on T012)
- [ ] T032 [US2] Extend `tests/validation/test_command.py`: `--json` single-document/stderr-purity contract, `--scope` file+dir narrowing, `--severity` threshold, exit-code matrix (0/1), byte-identical re-run ordering, and `empty_scope` exit 2 (SC-003/004/005/006; depends on T030)

**Checkpoint**: US1 + US2 work. Results are CI- and editor-consumable.

---

## Phase 5: User Story 3 — Configure and extend which validators run (Priority: P3)

**Goal**: Manifest `[validators]` selection (enabled/disabled/custom) and drop-in
custom validators discovered from `.bookwright/validators/`.

**Independent Test**: Disabling a built-in in the manifest removes its findings;
dropping a custom validator file into the project's validators folder makes its
findings appear; naming a non-existent validator exits 2; a malformed custom file is
skipped with an attributed message and does not crash the run (spec US3; SC-007/008).

### Implementation

- [ ] T033 [US3] Wire configuration + extension into `src/bookwright/commands/validate.py`: pass `manifest.validators` and the `<root>/.bookwright/validators/` custom dir through `discover_validators` + `resolve_active`, surface `discover_validators` load errors in the report's `errors[]`, and map `UnknownValidatorError` to the `unknown_validator` exit-2 envelope (FR-005/006/007; cli-validate.md error envelope; depends on T022, T013)

### US3 tests

- [ ] T034 [US3] Extend `tests/validation/conftest.py` with a working custom-validator fixture and a malformed/non-conforming custom-file fixture under `.bookwright/validators/` (SC-007; depends on T024)
- [ ] T035 [P] [US3] Unit-test `discover_validators` + `resolve_active`: built-in discovery, empty-enabled=all, enabled intersect, disabled subtract, custom allow-list, unknown-name → `UnknownValidatorError`, duplicate-name + malformed-skip load errors, in `tests/validation/test_registry.py` (FR-004/005/006/007, SC-007; depends on T013, T034)
- [ ] T036 [US3] Extend `tests/validation/test_command.py`: disabling a built-in removes its findings, a custom validator's findings appear, an unknown enabled name exits 2, a malformed custom is reported under `errors` without crashing (SC-007/008; depends on T033, T034)

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Determinism, gates, and docs across the whole feature.

- [ ] T037 [P] Walk the quickstart.md scenarios end-to-end (run, `--json`, `--scope`, `--severity`, configure `[validators]`, drop in a custom validator) and reconcile any drift between docs and behaviour
- [ ] T038 [P] Run `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy --strict src tests`; fix findings (CI gates)
- [ ] T039 Run `uv run pytest --cov`; confirm ≥80 % coverage (Constitution VIII) and fill any gaps (notably runner isolation and report edge cases)
- [ ] T040 [P] Verify every new/edited module stays <500 lines (Principle IV) and confirm no new runtime dependency was introduced (Constitution II, plan Technical Context)

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (P1)**: no dependencies.
- **Foundational (P2)**: depends on Setup. **Blocks US1/US2/US3.**
- **US1 (P3)**: depends on Foundational. Delivers the MVP.
- **US2 (P4)**: depends on Foundational; its command work (T030) extends the US1 command (T022) and its tests extend `test_command.py` — so US2 lands after US1 in practice.
- **US3 (P5)**: depends on Foundational; T033 extends the US1 command and uses the foundational registry (T013); tests extend `test_command.py`. Lands after US1.
- **Polish (P6)**: depends on all targeted stories.

### Critical-path notes within Foundational

- `base.py` tasks T002→T003→T004→T005 are the **same file** — sequential.
- Closure: T007 → T008 → T009 (namespaces before event before bible mapper).
- T010–T013 are different files, all depend only on `base.py` (and T010 also on T007) → parallelizable once base + namespaces exist.

### Cross-story file contention (intentional, incremental)

`src/bookwright/commands/validate.py` and `tests/validation/test_command.py` and
`tests/validation/conftest.py` are each touched in more than one story (US1 builds,
US2/US3 extend). This follows the incremental-delivery model (P1→P2→P3); these files
are **not** parallel-safe across stories.

---

## Parallel Opportunities

- **Foundational engine** (after T002–T006 land): T010, T011, T012, T013 in parallel (distinct files).
- **Closure** runs alongside base work: T007 is `[P]` vs the base-file tasks.
- **Foundational tests**: T014, T015, T016, T017 in parallel.
- **US1 validators**: T018, T019, T020, T021 in parallel (one file each).
- **US1 validator tests**: T025, T026, T027, T028 in parallel (after fixtures T024).
- **Polish**: T037, T038, T040 in parallel.

### Parallel Example — Foundational engine

```bash
# After base.py (T002–T006) and namespaces (T007) are in place:
Task: "Implement validation/queries.py"   # T010
Task: "Implement validation/runner.py"     # T011
Task: "Implement validation/report.py"     # T012
Task: "Implement validation/registry.py"   # T013
```

### Parallel Example — US1 validators

```bash
Task: "Implement validators/temporal.py"            # T018
Task: "Implement validators/character_presence.py"  # T019
Task: "Implement validators/setting_continuity.py"  # T020
Task: "Implement validators/focalization.py"        # T021
```

---

## Implementation Strategy

### MVP first (US1 only)

1. Phase 1 Setup → Phase 2 Foundational (engine + closure, fully tested).
2. Phase 3 US1: four validators + `validate` command (human mode) + fixtures + tests.
3. **STOP and VALIDATE**: run against the seeded violation/clean fixtures (SC-001/002).

### Incremental delivery

1. Foundational ready (engine + closure green).
2. US1 → human report MVP → demo.
3. US2 → `--json`/`--scope`/`--severity` + CI exit gate → demo.
4. US3 → manifest config + custom validators → demo.
5. Polish → lint/type/coverage/docs → merge when `/speckit-analyze` is clean.

---

## Notes

- Determinism (FR-019/SC-003) is load-bearing: stable discovery order, `sorted(glob)`
  for manuscript files, finding sort `(validator, source, message)`, and dedupe — all
  in Foundational, exercised by the re-run test in T032.
- The gate (FR-013) is always computed from the **unfiltered** error-severity set; a
  `--scope`/`--severity` filter can never mask a CI failure.
- The closure (T007–T009, T015–T017) crosses into iteration-5/6 territory by design
  (research D1/D11); `/speckit-analyze` must confirm cross-artifact consistency.
- Commit after each task or logical group. The feature writes nothing to the project
  (FR-020) beyond what tests scaffold in temp dirs.
