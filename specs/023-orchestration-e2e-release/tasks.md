---
description: "Task list for iteration 023 — orchestration loop fixture, E2E flow, docs, v0.3.0 release"
---

# Tasks: Orchestration loop fixture, E2E flow, docs, and v0.3.0 release

**Input**: Design documents from `specs/023-orchestration-e2e-release/`

**Prerequisites**: plan.md, spec.md, research.md (D1–D9), data-model.md, contracts/e2e-orchestration-contract.md

**Tests**: Test tasks ARE included — this iteration's *primary deliverable* is the
E2E regression (`test_orchestration_workflow.py`), per spec FR-007..FR-012 and the
contract Groups A–D. They are written against already-shipped CLI surface (019–020),
so they are not "write-then-fail" TDD scaffolding — the loop already works; the test
pins it.

**Hard constraint (FR-020)**: No task touches `src/` **except** the single
`__version__` line in `src/bookwright/__init__.py` (T020). Everything else lives in
`tests/fixtures/`, `tests/e2e/`, `docs/`, `CHANGELOG.md`, and `mkdocs.yml`.

**Discipline (user directive)**: Fixture **first**, then the oracle, then the tests
(the test reads both). Identifiers/counts in the test ALWAYS come from the oracle,
never hard-coded. `[P]` marks only tasks in **distinct files with no dependency**
(e.g. the docs page and the fixture may go in parallel; the test is **not** `[P]`
relative to fixture+oracle, and all `test_orchestration_workflow.py` tasks share one
file so none are `[P]` with each other).

## Path Conventions

Single-project src-layout: fixtures under `tests/fixtures/tiny-historical/`, the E2E
test under `tests/e2e/`, docs under `docs/`, the root changelog and `mkdocs.yml` at
repo root.

---

## Phase 1: Setup (baseline reference)

**Purpose**: Capture the pre-change green state so FR-006 non-regression is provable.

- [ ] T001 Capture the FR-006 baseline: run `uv run pytest tests/e2e/test_research_workflow.py -q` and note it green BEFORE any fixture edit, so the later gate (T017) proves the M4 `factual_anchor` `{error:1, warning:1}` counts are byte-stable across this iteration's fixture extension.

**Checkpoint**: Baseline recorded — fixture work can begin.

---

## Phase 2: Foundational

**Purpose**: None. This iteration adds no shared `src/` code; the fixture (US1) is the
substrate every other story consumes, so it stands as the first user story rather than
a separate foundational phase. Proceed directly to Phase 3.

---

## Phase 3: User Story 1 - A worked example the orchestration loop can reason over (Priority: P1) 🎯 MVP

**Goal**: Extend the committed `tiny-historical` so `bookwright status` has a defined
focus, real open work, and a deterministic, oracle-enumerated state to report — the
shared input the E2E test and the docs both consume (FR-001..FR-006).

**Independent Test**: `cp -r tests/fixtures/tiny-historical /tmp/orch`, run
`focus set` → `graph build` → `status --json`; exit 0 with a defined focus, a built
graph, `open_questions.count == 2`, and a non-empty `next_actions` whose first entry
is `bookwright-research` naming both open ids (quickstart §1).

### Implementation for User Story 1

- [ ] T002 [P] [US1] Add a fully-populated `[focus]` block to `tests/fixtures/tiny-historical/manifest.toml` (FR-002, data-model §1.1): `target` = `"Cerrar la investigación del libro de jornales para datar la huelga"`, a `notes` line referencing `q-libro-de-jornales`, and `updated_at = 2026-06-13`. Append it as a new block (e.g. after `[book]`). MUST NOT touch `[research]` / `[validators]` so `test_disabled_research_block_is_inert`'s `enabled = true → false` replace and every M4 assertion stay unaffected (FR-006).

- [ ] T003 [P] [US1] Create `tests/fixtures/tiny-historical/_resolution/q-libro-de-jornales.md` — the pre-baked answering Finding (FR-005, D3/D4, data-model §1.3) — in a **top-level `_resolution/` directory OUTSIDE `bible/`/`manuscript/`/`outline/`** so build #1 never reads it. Front-matter declares ONE **closed** finding `id: libro-de-jornales-hallado` (NOT a `q-…` id, NOT `open`) with a real `claim`, `asserted_by: author`, `bears_on: "La Real Fábrica de Paños"` (resolvable in the bible → no `ResearchWarning`), and `sources: ["Memoria de la Real Fábrica de Paños"]` (the already-registered `alta` source → not low-reliability). It MUST declare **no `anchors:` block** (adds no `AnchorGap`, no `factual_anchor` change). Ship no `graph.ttl` / `SKILL.md` / `[PENDING:]` sentinel so committed-tree invariants still hold (D4).

- [ ] T004 [US1] Create `tests/fixtures/tiny-historical/expected-status.md` — the orchestration oracle (FR-004, D5, data-model §1.4) — as a NEW co-located file (do **not** extend `expected-findings.md`; FR-006 keeps it byte-stable). Front-matter records: `focus.target` (matching T002); `phase: drafting` (== manifest `[book].status`, so A3 reads it from the oracle, not hard-coded); `open_questions.ids: [q-libro-de-jornales, q-origen-telares]` + `file: bible/research/_index.md`; `resolution.{resolved_id: q-libro-de-jornales, answering_file: _resolution/q-libro-de-jornales.md, remaining_id: q-origen-telares}`; `unresolved_anchors` (`rumor-incendio → "El almacén viejo"`, `problems: [under_reliable]`); `low_reliability_findings` (`rumor-incendio`, `best_reliability: baja`); `validation.counts: {error: 1, warning: 1, info: 0}`; and `next_actions.skills: [bookwright-research, bookwright-verify, bookwright-continuity]` in firing order. Depends on T002/T003 (must reflect their target/ids).

- [ ] T005 [US1] Manually validate the worked example (quickstart §1–2, SC-001) on a throwaway copy: `focus set` → `graph build` → `status --json` gives exit 0, defined focus, `open_questions.count == 2`, first action `bookwright-research` naming both ids; then apply the resolution (copy `_resolution/q-libro-de-jornales.md` into `bible/research/`, drop `q-libro-de-jornales` from `_index.md`), rebuild, and confirm `open_questions.count == 1`, the research prompt drops the resolved id, and `len(next_actions)` stays **3**. Confirms the oracle's expectations match live behavior before any test is written. (No file committed; verifies T002–T004.)

**Checkpoint**: The fixture is a standalone, demonstrable orchestration example with a deterministic oracle — US2/US4 can now consume it.

---

## Phase 4: User Story 2 - The orchestration loop proven end to end (Priority: P1)

**Goal**: An automated regression that walks focus → status → resolve → status over the
extended fixture and asserts deterministic **state convergence** (FR-007..FR-010), plus
the committed-tree invariants and the FR-006 non-regression gate.

**Independent Test**: `uv run pytest tests/e2e/test_orchestration_workflow.py -v` —
Group A (loop convergence) and Group D (committed-tree) green; the resolved open
question deterministically leaves `state.open_questions` and the `research_queue`
prompt while everything else is byte-identical.

> **Note**: All tasks below write to the single file
> `tests/e2e/test_orchestration_workflow.py`, so **none are `[P]`** with each other or
> with the fixture/oracle (the test reads both). Watch the ≤500-line ceiling
> (Principle IV) — extract helpers if it grows (T013).

### Implementation for User Story 2

- [ ] T006 [US2] Scaffold `tests/e2e/test_orchestration_workflow.py` by cloning the EXACT harness of `tests/e2e/test_research_workflow.py` (FR-007, data-model §5): same imports (`app`, `parse_frontmatter`, `FIXTURES_DIR`, `copy_fixture`, in-process `CliRunner` `cli` fixture from `conftest`), `_load_oracle()` reading `tiny-historical/expected-status.md` once + an `oracle` fixture, a `historical` fixture (`copy_fixture("tiny-historical", tmp_path)` + `monkeypatch.chdir`), `_payload`/`_status(cli)` (run `status --json`, assert exit 0, return parsed payload), `_build(cli)`, `_apply_resolution(project, oracle)` (copy `_resolution/<answering_file>` → `bible/research/`; drop `resolved_id` from `_index.md` `open_questions`), and `_research_action(payload)` (locate the `next_actions` entry whose `skill == "bookwright-research"`). All identifiers/counts read from `oracle`, never hard-coded.

- [ ] T007 [US2] Add Group A tests (contract A1–A8, FR-002/003/005/008/009/010) to the file: A1 `focus set --target <oracle.target>` exit 0 → `status.focus` non-null with matching target; A2 `graph build` exit 0 → `state.graph.available == true`, `entities`/`triples` present; A3 first `status` deterministic facts per data-model §2.1 (open_questions ids/count, the `el-almacen-viejo`/`rumor-incendio` anchor gap, the `rumor-incendio` low-reliability finding `baja`, `validation.counts {error:1,warning:1,info:0}`), oracle-sourced; A4 `next_actions` == 3 in skill order, each carrying `skill`+`reason`+`prompt`, `research_queue.prompt` containing both open ids; A5 after `_apply_resolution`+rebuild `open_questions.count == 1`, remaining `q-origen-telares`, resolved id absent; A6 second-`status` convergence — `research_queue.prompt` drops the resolved id, `reason` reflects the new count, and the **invariant set (data-model §4)** is byte-identical with `len(next_actions) == 3`; A7 `state.graph` asserted available+counts-present per run but **excluded from the cross-run byte-identity** (D2 carve-out); A8 a repeated `status` on an unchanged corpus is byte-identical (no timestamp / minted-URI in asserted fields).

- [ ] T008 [US2] Add Group D committed-tree invariants (contract D1 and D3, FR-005/006 — contract D2 is the FR-006 non-regression gate in T017) to the file: D1 committed `tiny-historical` ships no `graph.ttl`, no `.claude/`/`.agents/`, no `SKILL.md`, while `_resolution/` and `expected-status.md` are present-but-inert; D3 prove `_resolution/` is outside the corpus dirs by asserting the FIRST `status` reports `open_questions.count == 2` (the answering finding was not read).

**Checkpoint**: The orchestration loop is proven end to end and the fixture tree is guarded as source-only.

---

## Phase 5: User Story 3 - The system is inert when orchestration is unused (Priority: P2)

**Goal**: Prove a focus-free / research-free project (and an unbuildable corpus) behave
exactly as pre-M5 — `status` succeeds and recommends nothing (FR-011, FR-012).

**Independent Test**: The Group B/C tests in `test_orchestration_workflow.py` pass:
`status` on `tiny-novel` exits 0 with `focus: null` and `next_actions: []`, and a
build-prerequisite-absent copy degrades to `state.graph.available == false` at exit 0.

> **Note**: Same file as US2 (`test_orchestration_workflow.py`) — sequential, not `[P]`.
> Reuses the existing `tiny-novel` fixture; **no new fixture is authored** (FR-011, D7).

### Implementation for User Story 3

- [ ] T009 [US3] Add Group B inertness tests (contract B1–B2, FR-011, SC-003) to `tests/e2e/test_orchestration_workflow.py` reusing `tiny-novel` via `copy_fixture`: `status --json` exit 0 with `focus == null`, `next_actions == []`, and no open questions / unresolved anchors / low-reliability findings; `graph build` and `validate` exit/behave as pre-M5 (no orchestration output, no new required input).

- [ ] T010 [US3] Add Group C degraded-path test (contract C1, FR-012, SC-003) to the same file: on a `tmp_path` `tiny-novel` copy with build prerequisites absent (e.g. bible removed), `status --json` exits 0 with `state.graph.available == false` and a present report — never a failure (the merged `status` `_aggregate` degraded branch).

**Checkpoint**: Non-regression for the existing user base is guaranteed.

---

## Phase 6: User Story 4 - The orchestration system is documented for release (Priority: P2)

**Goal**: A navigable orchestration page, verified `status`/`focus` command reference,
a v0.3.0 entry in both changelogs, and the version bump — building cleanly under
`strict: true` (FR-013..FR-016, FR-019, FR-022).

**Independent Test**: `uv run --group docs mkdocs build --strict` completes with zero
warnings; `docs/orchestration.md` is reachable from nav; both changelogs carry v0.3.0;
`bookwright version --json` reports `0.3.0`.

### Implementation for User Story 4

- [ ] T011 [P] [US4] Create `docs/orchestration.md` — a NEW **top-level** Spanish page (sibling of `docs/research.md`, NOT under `docs/commands/`) (FR-013, D9): the three-layer "hilo conductor" model (autoral `[focus]` vs. derivado `status` vs. juicio de las skills, design § 21.2); what `bookwright status` reports and how `next_actions` derive from the 5-rule per-workstream table (§ 21.5); the work loop focus → status → act → repeat; and how the skills consume `status` at start (021–022). (No dependency on the fixture/test — may run parallel to Phase 3.)

- [ ] T012 [US4] Add the nav entry to `mkdocs.yml` (FR-014): `- Orquestación: orchestration.md`, placed alongside `- Investigación: research.md`. Depends on T011 (target must exist for `strict` build).

- [ ] T013 [P] [US4] Verify-and-finalize the existing command-reference pages `docs/commands/status.md`, `docs/commands/focus-set.md`, `docs/commands/focus-show.md`, `docs/commands/focus-clear.md` against the live CLI (FR-015): correct flags, `--json` envelope, and examples — bring current for the release, do NOT duplicate or create new pages.

- [ ] T014 [P] [US4] Add a Spanish v0.3.0 entry to the root `CHANGELOG.md` (FR-016, E3) consolidating iterations 019–023: authored focus (`[focus]` + `bookwright focus`), `bookwright status` (derived state + `next_actions`), status-consuming skills, and this iteration's fixture/E2E/docs.

- [ ] T015 [P] [US4] Add the matching Spanish v0.3.0 entry to `docs/changelog.md` (FR-016, E3) — the mkdocs nav target — consistent with the root `CHANGELOG.md` entry (the two files are maintained in parallel).

- [ ] T016 [US4] Bump `__version__` from `"0.2.0"` to `"0.3.0"` in `src/bookwright/__init__.py` (FR-022, D8) — the SINGLE authoritative version source (`pyproject.toml` is `dynamic`). This is the ONLY permitted `src/` edit in this iteration. `tests/test_smoke_import.py` / `tests/test_cli_version.py` read `__version__` dynamically and stay green.

**Checkpoint**: The orchestration system is documented and the package reads `0.3.0`, release-ready.

---

## Phase 7: Polish & Release Gates

**Purpose**: The non-negotiable green bar and the FR-006 regression gate.

- [ ] T017 [US2] FR-006 gate (explicit): re-run `uv run pytest tests/e2e/test_research_workflow.py -v` with NO edits to that test and confirm it is green and `factual_anchor` still reports exactly `{error: 1, warning: 1}` (contract D2). Confirm `expected-findings.md` is byte-unchanged vs. the T001 baseline.

- [ ] T018 Verify the new E2E module is ≤ 500 lines (Principle IV); if it exceeds, extract the SPARQL-free helpers (e.g. `_apply_resolution`, the comparison-set partitioner) into a private helper section or module, keeping behavior identical.

- [ ] T019 Docs gate (FR-019, SC-006): `uv run --group docs mkdocs build --strict` → zero warnings; orchestration page reachable from nav, command pages render, both changelogs present.

- [ ] T020 Full quality gate (FR-017, FR-018, SC-005, SC-006): `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (≥ 80 % overall coverage — the single enforced gate). Report (not enforce) new-M5 coverage ≥ 85 % at review.

- [ ] T021 Run the full quickstart.md end to end (SC-001..SC-006) as the release smoke: fixture demo (§1–2), the orchestration test (§3), the M4 test unaffected (§4), docs build (§5), version `0.3.0` (§6), and the four gates (§7).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: none — run first to pin the FR-006 baseline.
- **US1 / Fixture (T002–T005)**: after T001. **Blocks US2** (the test reads the fixture + oracle).
- **US2 / E2E (T006–T008)**: after US1 (fixture + oracle exist). All in one file → sequential.
- **US3 / Inertness (T009–T010)**: after T006 (same file as US2; needs the harness). Independent of the fixture extension (uses `tiny-novel`).
- **US4 / Docs+release (T011–T016)**: independent of US1–US3 — **may run in parallel** (different files), except T012 depends on T011.
- **Polish (T017–T021)**: after all of the above; T019 needs US4, T020/T021 need everything.

### Critical path

T001 → T002/T003 → T004 → T006 → T007 → T008 → T020 → T021.
(US4 docs and US3 inertness hang off this path but do not lengthen it.)

### Within stories

- US1: T002 ∥ T003 (different files) → T004 (oracle reflects both) → T005 (manual demo).
- US2/US3: strictly sequential — one shared file.
- US4: T011 → T012; T013, T014, T015, T016 mutually independent.

### Parallel Opportunities

- **T002 ∥ T003** — `manifest.toml` vs. `_resolution/q-libro-de-jornales.md`.
- **T011 (docs page) ∥ Phase 3 fixture** — distinct files, no dependency (user-noted).
- **T013 ∥ T014 ∥ T015 ∥ T016** — four distinct files (command pages, root changelog, docs changelog, `__init__.py`).

---

## Parallel Example: User Story 1 + docs kickoff

```bash
# Fixture's two independent files, plus the docs page — all distinct files:
Task T002: "Add [focus] block to tests/fixtures/tiny-historical/manifest.toml"
Task T003: "Create tests/fixtures/tiny-historical/_resolution/q-libro-de-jornales.md"
Task T011: "Create docs/orchestration.md (top-level Spanish page)"
# Then, sequentially: T004 (oracle, reads T002/T003) → T005 (manual demo).
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. T001 baseline → T002–T005 fixture+oracle → **STOP, validate the worked example by hand**.
2. T006–T008 E2E loop → green Group A/D.
3. T017 FR-006 gate green → the orchestration loop is proven and non-regressing — the milestone's core claim.

### Incremental Delivery

1. US1 → demonstrable fixture (SC-001).
2. US2 → proven loop (SC-002).
3. US3 → inertness/degraded guard (SC-003).
4. US4 → docs + version (SC-004) → T019/T020/T021 gates → **release-ready v0.3.0**.

---

## Notes

- `[P]` = different files, no dependency. The whole `test_orchestration_workflow.py`
  is one file → its tasks are never `[P]` with each other.
- The test ALWAYS sources identifiers/counts from `expected-status.md` (the oracle) —
  never hard-coded (FR-008, D5).
- The progress assertion is **state convergence**, NOT a `next_actions` length drop
  (D2): `research_queue` keeps firing for the remaining open question + the permanent
  `el-almacen-viejo` anchor, so `len(next_actions)` stays 3.
- `state.graph` is asserted present-per-run but **carved out** of the cross-run
  byte-identity comparison (D2) — a closed finding legitimately emits different triples.
- Only T016 touches `src/` (the `__version__` line); every other task is fixture /
  test / docs / changelog / nav (FR-020).
