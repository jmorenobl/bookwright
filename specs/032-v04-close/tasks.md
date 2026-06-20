---
description: "Task list for iteration 032 — v0.4 close"
---

# Tasks: v0.4 close — narrative-structure E2E fixture, workflow test, docs, honest deferrals, release

**Input**: Design documents from `/specs/032-v04-close/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: REQUIRED here — the automated workflow test (`tests/e2e/test_narrative_workflow.py`)
is itself a named deliverable (User Story 2, FR-007..011), so its tasks are first-class,
not optional.

**Branch vs. release split** (plan.md §"Branch scope vs. release step"): the version
bump (`__version__`→`0.4.0`), the `v0.4.0` CHANGELOG section, the `CLAUDE.md` status-table
flip, and `bookwright-design.md` status edits are **NOT** committed on this branch — the
`bookwright-release` skill produces them after the branch is green and merged. Tasks below
cover only the **branch** deliverables (fixture, oracle, test, docs, deferral re-target,
`DEBT.md` + roadmap edits) plus a release-readiness handoff task.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US5 maps to the spec's user stories
- All paths are repo-relative to `/Users/jorge/Projects/bookwright`

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repo root, `docs/` for the
mkdocs site. The only `src/` touch is a data edit to `src/bookwright/golem/deferrals.py`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lay down the fixture directory skeleton everything else fills in.

- [X] T001 Create the source-only fixture skeleton `tests/fixtures/tiny-quest/` with empty subdirs `bible/`, `bible/characters/`, `outline/units/`, `manuscript/` (mirror the `tests/fixtures/tiny-historical/` layout; **no** `bible/graph.ttl`, **no** `.claude/`/`.agents/`, **no** `SKILL.md` — source-only per FR-001/Group D2)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None beyond Setup — this iteration adds no shared `src/` mechanism. The
fixture (US1) is the foundational artifact every later story consumes; it lives in its
own phase so it can be demonstrated standalone (SC-001) before any test/doc is written.

**Checkpoint**: Fixture skeleton exists — User Story 1 can begin.

---

## Phase 3: User Story 1 - A worked example that exercises the narrative-structure layer end to end (Priority: P1) 🎯 MVP

**Goal**: A valid, loadable `tiny-quest` Bookwright project whose `outline/units/` describes
Propp-typed beats with roles and an ordered sequence (Propp active), producing — deterministically
— the G9/G10/G7 entities + `E55_Type` typings and exactly one orphan beat + one unresolved role,
recorded in a co-located oracle.

**Independent Test**: `cp -r tests/fixtures/tiny-quest /tmp/tq && cd /tmp/tq && bookwright graph build --json` (exit 0) then `bookwright validate --json` → the two `narrative_structure` warnings with `file:line` sources (quickstart §1, SC-001).

- [X] T002 [P] [US1] Write `tests/fixtures/tiny-quest/manifest.toml` with the standard `[bookwright]`/`[book]`/`[validators]`/`[paths]` blocks **and** `[vocabularies] active = ["propp"]` (data-model §1.1; FR-003) — `language = "es"`, `uri_base = "https://example.org/tiny-quest/"`, `indexer = "rdflib"`
- [X] T003 [P] [US1] Write `tests/fixtures/tiny-quest/bible/constitution.md` (minimal valid constitution, Spanish prose; copy the shape of `tiny-historical/bible/constitution.md`)
- [X] T004 [P] [US1] Write the three role-target characters under `tests/fixtures/tiny-quest/bible/characters/` — hero (`narrative_roles: [protagonist]`), villain (`[villain]`), helper (`[helper]`); **no** character declares the `dragon` slug (the deliberate Rule-c miss, data-model §1.2; FR-004)
- [X] T005 [P] [US1] Write `tests/fixtures/tiny-quest/manuscript/01-*.md` (one short Spanish scene so the project is complete; identifiers English)
- [X] T006 [US1] Write the six unit cards under `tests/fixtures/tiny-quest/outline/units/` (`01-interdiction.md` … `05-return.md` sequenced into `"Quest"` with `order` 1–5; `06-omen.md` with **no `sequence` key** = the orphan beat **and** `roles: [dragon]` = the unresolved role) per data-model §1.3; all `functions` slugs must be canonical Propp terms so each resolves to a `propp.ttl` `E55_Type`; hold the invariants: exactly one `sequence`-less card, exactly one unresolved `roles:` slug, every other role resolves (FR-002/FR-004/FR-005)
- [X] T007 [US1] Build the fixture for real to discover the deterministic facts and pin provenance: `cp -r tests/fixtures/tiny-quest /tmp/tq && cd /tmp/tq && uv run --project <repo> bookwright graph build --json` then `bookwright validate --json` — capture the exact G9 unit slugs, distinct G10 function count + Propp `typed` map, the ordered G7 members, the resolved role cross-refs, and the two findings' `E13`-resolved `source` (`file` or `file:line`, data-model D3 / contracts/fixture-oracle.md "Determinism")
- [X] T008 [US1] Author the co-located oracle `tests/fixtures/tiny-quest/expected-narrative.md` — YAML front-matter = single source of truth (`units`, `functions.count`/`typed`, `sequence.name`/`members`, `roles_resolved`, `narrative_structure.orphan_beats`/`unresolved_roles`/`counts`), body = Spanish explanation; every value taken **from the real build in T007**, exact sets not lower bounds (contracts/fixture-oracle.md; FR-005)

**Checkpoint**: `tiny-quest` builds + validates standalone with the exact oracle facts — SC-001 demonstrable.

---

## Phase 4: User Story 2 - The v0.4 flow proven end to end by an automated workflow test (Priority: P1)

**Goal**: `tests/e2e/test_narrative_workflow.py` walks build → validate on a `tmp_path` copy,
every count/identifier sourced from the oracle, asserting graph facts, exact validator findings,
the no-vocabulary-active non-regression, determinism, and source-only.

**Independent Test**: `uv run pytest tests/e2e/test_narrative_workflow.py -q` → green; Groups A–D all pass (quickstart §2, SC-002).

- [X] T009 [US2] Scaffold `tests/e2e/test_narrative_workflow.py` reusing the `test_orchestration_workflow.py` (023) harness verbatim where possible — `copy_fixture`/`tmp_path` copy, `monkeypatch.chdir`, in-process `CliRunner`, `_payload`/`_build` helpers, and an oracle loader `parse_frontmatter(path.read_text(encoding="utf-8")).metadata` (contracts/e2e-narrative-workflow.md preamble; FR-007)
- [X] T010 [US2] Implement **Group A** (build graph facts) in `tests/e2e/test_narrative_workflow.py`: A1 G9 unit count/slugs, A2 distinct G10 function count, A3 Propp `crm:P2_has_type`→`E55_Type` typings (and untyped functions carry none), A4 the single G7 `"Quest"` with ordered `dlp:proper-part` members, A5 resolved role cross-refs (orphan card's `dragon` yields no edge) — query the loaded engine directly (`outcome.engine.query(...)` / `build_project_graph`, the `test_ingestion_parity::_observed_types` pattern) for triple-level facts; all expected values from the oracle (FR-008)
- [X] T011 [US2] Implement **Group B** (exact validator findings) in `tests/e2e/test_narrative_workflow.py`: filter `validate --json` `violations[]` to `validator == "narrative_structure"`, match each oracle `orphan_beats`/`unresolved_roles` entry by (`unit`/`role`, `source`), assert `severity == "warning"` and the message phrases (`orphan beat`; `resolves to no character role`), assert the scoped warning/error counts equal `oracle…counts`, and assert no `error`-severity finding overall (`failed == false`) (FR-009)
- [X] T012 [US2] Implement **Group C** (non-regression) in `tests/e2e/test_narrative_workflow.py`: rewrite the `tmp_path` copy's `manifest.toml` to `[vocabularies] active = []` at runtime, rebuild, assert **no** `crm:P2_has_type`/vocabulary `E55_Type` triple appears (C1), every other Group-A fact is byte-for-byte identical (C2), and `validate` still reports the same `narrative_structure` findings (C3) (FR-010)
- [X] T013 [US2] Implement **Group D** (determinism + source-only) in `tests/e2e/test_narrative_workflow.py`: D1 repeat build→validate on an unchanged copy and assert byte-identical asserted JSON/graph facts; D2 assert the committed `tests/fixtures/tiny-quest/` ships no `bible/graph.ttl`, no `.claude/`/`.agents/`, no `SKILL.md`, and `expected-narrative.md` is present-but-inert (mirror `test_orchestration_workflow.py::test_committed_fixture_is_source_only`) (FR-011)

**Checkpoint**: SC-002 met — the whole deterministic flow has a green-or-red regression.

---

## Phase 5: User Story 3 - The v0.4 layer is documented for release (Priority: P2)

**Goal**: A Spanish docs page + README touch covering `outline/units/` ingestion, unit
frontmatter, Propp/Greimas activation, and the validator; reachable from nav; site builds clean.

**Independent Test**: `uv run mkdocs build --strict` (zero warnings) + the page is nav-reachable and covers the four topics (quickstart §4, SC-004).

- [ ] T014 [P] [US3] Write `docs/narrative-structure.md` (Spanish prose, English identifiers/keys) covering: `outline/units/` ingestion → G9/G10/G7; a unit card's frontmatter (`functions`/`roles`/`sequence`/`order`); activating **both** Propp **and** Greimas via `[vocabularies] active` (edge case "Greimas as well as Propp"); and the `narrative_structure` validator's two rules (orphan beat, unresolved role) (FR-012)
- [ ] T015 [P] [US3] Add the nav entry for `narrative-structure.md` to `mkdocs.yml` (place near `Validación`/`Orquestación`, e.g. `- Estructura narrativa: narrative-structure.md`) (FR-013)
- [ ] T016 [P] [US3] Update `README.md` to reflect the v0.4 narrative-structure layer in the feature list / project surface (FR-014)

**Checkpoint**: SC-004 met (the `v0.4.0` CHANGELOG entry, FR-015, is produced by the release skill — see Phase 7 note).

---

## Phase 6: User Story 4 - The deferral registry is left honest (Priority: P2)

**Goal**: `deferrals.py` lists exactly `{RelationshipRole, PsychologicalState}` with the
first-class `target_version="demand-pulled"` sentinel; the same value is mirrored in the
parity test's `EXPECTED_VERSIONS`; `DEBT.md` stale targets corrected; parity stays green.

**Independent Test**: `uv run pytest tests/golem/test_ingestion_parity.py -q` green **and** `rg '"v0\.4"' src/bookwright/golem/deferrals.py tests/golem/test_ingestion_parity.py` + `rg 'Target: v0\.4' DEBT.md` find nothing (quickstart §3, SC-003).

- [X] T017 [US4] Edit `src/bookwright/golem/deferrals.py`: re-point both `DEFERRED_CONCEPTS` entries' `target_version` from `"v0.4"` to `"demand-pulled"` (lines ~42, ~46) **and** extend the `DeferralNote` docstring (line ~29) to admit `"demand-pulled"` as a documented first-class "no version until an activation trigger" state, distinct from the banned `"undecided"` placeholder (FR-017/FR-018; data-model §3)
- [X] T018 [US4] Edit `tests/golem/test_ingestion_parity.py`: change `EXPECTED_VERSIONS` (lines ~56–58) to `{"RelationshipRole": "demand-pulled", "PsychologicalState": "demand-pulled"}` so the registry-version assertion and the no-`"undecided"` assertion both stay green (FR-019/FR-019a) — depends on T017
- [X] T019 [P] [US4] Edit `DEBT.md`: re-point DEBT-001's `Target: v0.4` (line ~69) to a concrete later structural iteration / demand-pulled horizon, and DEBT-002's `Target: v0.4 (cierre)` (line ~96) to the manual `v0.4.0` release/amendment step that owns the MINOR amendment — both entries stay **abierta**, only the stale target strings change (FR-019b)

**Checkpoint**: SC-003 met — no `"v0.4"` deferral-target string remains repo-wide, parity green.

---

## Phase 7: User Story 5 - The v0.4.0 release metadata is in place (Priority: P2)

**Goal**: The branch is release-ready and the roadmap reflects v0.4 delivered. The actual
version bump / CHANGELOG / `CLAUDE.md` flip / design status edits / tag are produced by the
`bookwright-release` skill **after merge** (plan.md branch-vs-release table; quickstart §7).

**Independent Test**: roadmap §1 says v0.4 delivered and §2 `← AQUÍ` advanced past v0.4 (quickstart §5); post-release `bookwright version` → `0.4.0` (SC-005, release-skill step).

- [ ] T020 [P] [US5] Edit `bookwright-roadmap.md`: § 1 record v0.4 as entregada, and advance the § 2 `← AQUÍ` marker past the `v0.4` line (to the demand-pulled horizon) (quickstart §5; user request)
- [ ] T021 [US5] Verify release readiness and record the handoff: confirm all four gates green on the branch and that `__version__` (still `0.3.4`), the `v0.4.0` CHANGELOG section, the `CLAUDE.md` status-table flip + milestone prose, and `bookwright-design.md` status edits are **deliberately deferred to the `bookwright-release` skill** post-merge (FR-015/FR-016/FR-020 are satisfied at the release step, not in branch commits) — no branch edit to those files

**Checkpoint**: SC-005 ready — branch green, roadmap current, release handoff documented.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Run the full gate battery and the quickstart proofs over the whole change.

- [ ] T022 [P] Run `uv run mkdocs build --strict` and confirm zero warnings (FR-024/SC-006)
- [ ] T023 Run the gate battery: `uv run ruff check && uv run ruff format --check`, `uv run mypy --strict`, `uv run pytest` (full suite, coverage ≥ 80 % single enforced gate) — all green (FR-023/FR-024/SC-006)
- [ ] T024 Run the quickstart honesty proofs: `rg -n '"v0\.4"' src/bookwright/golem/deferrals.py tests/golem/test_ingestion_parity.py` and `rg -n 'Target: v0\.4' DEBT.md` both return nothing; `rg -n "v0.4 entregada|← AQUÍ" bookwright-roadmap.md` confirms §1/§2 (quickstart §3/§5; SC-003/SC-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: empty (no shared `src/` mechanism this iteration).
- **US1 (Phase 3)**: depends on Setup. **Blocks US2 and US3** (the test runs against the
  fixture/oracle; the docs reference it). T008 (oracle) depends on T007 (real build), which
  depends on T002–T006 (fixture content).
- **US2 (Phase 4)**: depends on US1 complete (fixture + oracle exist). T010–T013 all edit
  the same file (`test_narrative_workflow.py`) so they run **sequentially**, after T009.
- **US3 (Phase 5)**: depends on US1 (references the worked example) — but its three tasks are
  independent files, fully parallel.
- **US4 (Phase 6)**: **independent of US1–US3** — pure registry/test/ledger edits; can run
  any time after Setup. T018 depends on T017 (mirror the same value); T019 is independent.
- **US5 (Phase 7)**: roadmap edit (T020) independent; T021 (readiness) depends on US1–US4 +
  US2 tests existing.
- **Polish (Phase 8)**: depends on all desired stories complete.

### Parallel Opportunities

- **US1 content**: T002, T003, T004, T005 are different files → all `[P]` together. T006
  (units) then T007 (build) then T008 (oracle) are sequential.
- **US3**: T014, T015, T016 are different files → all `[P]`.
- **US4 ∥ US1/US2/US3**: the deferral re-target (T017–T019) shares no file with the fixture,
  test, or docs work — a second worker can do it in parallel from the start.
- **US5 roadmap** (T020) is `[P]` with everything.
- **Polish**: T022 `[P]` with T024; T023 (full suite) last.

---

## Parallel Example: User Story 1 fixture content

```bash
# After T001 (skeleton), launch the independent fixture files together:
Task: "Write tests/fixtures/tiny-quest/manifest.toml ([vocabularies] active=['propp'])"
Task: "Write tests/fixtures/tiny-quest/bible/constitution.md"
Task: "Write the three role-target characters under bible/characters/"
Task: "Write tests/fixtures/tiny-quest/manuscript/01-*.md"
# Then sequentially: T006 (units) → T007 (real build) → T008 (oracle from the build)
```

## Parallel Example: independent tracks

```bash
# US4 (deferral honesty) shares no files with the fixture/test/docs — run it alongside US1:
Track A: T002–T008  (US1 fixture + oracle)
Track B: T017 → T018, T019  (US4 deferral re-target + DEBT.md)
Track C: T020  (US5 roadmap)
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup (T001).
2. Phase 3 US1 (T002–T008) → **STOP and VALIDATE**: build + validate `tiny-quest` standalone
   (quickstart §1) — the worked example is the MVP and the foundation for everything else.

### Incremental Delivery

1. Setup → US1 (fixture + oracle) → demonstrable layer (SC-001).
2. US2 (workflow test) → the flow is guarded (SC-002).
3. US3 (docs) + US4 (deferral honesty) — independent, parallelizable (SC-004/SC-003).
4. US5 (roadmap + release readiness) → branch ready for `bookwright-release` (SC-005).
5. Polish: gates + quickstart proofs (SC-006/SC-007).

### What this iteration deliberately does NOT do (FR-021/FR-022/SC-007)

No new CLI verb, manifest field, validator, or skill behavior; **no ontology change**; G6/G3
stay unwired (only their stale target strings are corrected). The version bump, CHANGELOG,
`CLAUDE.md` flip, design status edits, and tag are the separate `bookwright-release` step.

---

## Notes

- `[P]` = different files, no dependencies.
- The oracle (T008) MUST be authored from the **real build** (T007), never hand-guessed —
  it is the single source of truth the test reads (FR-005).
- The fixture is **source-only**: never commit `bible/graph.ttl` or any materialized skill
  (asserted by Group D2).
- T010–T013 edit one test module → keep them sequential despite the same `[US2]` label.
- Commit after each task or logical group (the auto-git hooks are unreliable in headless
  flows — commit explicitly).
