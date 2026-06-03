---
description: "Task list for Release Prep — Fixtures, E2E Tests & Documentation"
---

# Tasks: Release Prep — Fixtures, E2E Tests & Documentation

**Input**: Design documents from `/specs/011-release-prep/`

**Prerequisites**: plan.md, spec.md, research.md (D1–D9), data-model.md (E1–E4),
contracts/ (e2e-tests.md C1–C3, fixture-shape.md F1–F6, docs-site.md DOC/CI/MAN)

**Tests**: This iteration *is* the test/docs/release layer — the fixtures and
E2E tests are the deliverables themselves (FR-006…FR-009, SC-002), so the
"implementation" tasks below produce test code by design.

**Organization**: Tasks are grouped by user story (US1–US4, priorities P1→P3)
to enable independent implementation and validation. No `src/bookwright/`
runtime code is modified — this is consolidation, not feature work.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3, US4 (setup/foundational/polish carry no label)
- Exact file paths are included in each task

## Path Conventions

Single project, src-layout (Principle III). New artifacts only under
`tests/fixtures/`, `tests/e2e/`, `docs/`, plus root files (`mkdocs.yml`,
`pyproject.toml`, root metadata, `.github/workflows/tests.yml`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Wire the new dependency group and create the empty package/dir scaffold.

- [ ] T001 Add a `docs` dependency group (`mkdocs`, `mkdocs-material`) under `[dependency-groups]` in `pyproject.toml` — NOT in `[project.dependencies]` (D6, DOC-3; no constitutional amendment). In the same file, add a `[tool.coverage.report]` block with `precision = 2` and `fail_under = 80` so the coverage gate fails closed without rounding up (Amendment B; FR-019, SC-005, edge case "coverage just under threshold")
- [ ] T002 [P] Create the E2E test package: `tests/e2e/__init__.py` (empty) and the `tests/fixtures/` directory root
- [ ] T003 Run `uv sync` (and `uv lock` if needed) so the `docs` group resolves into `.venv`; confirm `uv run --group docs mkdocs --version` works (depends on T001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared fixture-copy + in-process `CliRunner` helper that BOTH
US1 (fixture-validity test) and US2 (E2E suite) consume. Nothing in US1/US2 can
run until this exists.

**⚠️ CRITICAL**: No user-story test work can begin until this phase is complete.

- [ ] T004 Implement the shared E2E harness in `tests/conftest.py` (root): a `copy_fixture(name, tmp_path)` helper using `shutil.copytree` (D2, R1 — never writes outside `tmp_path`) and a `cli` fixture returning a `typer.testing.CliRunner` bound to `bookwright.cli:app` (D1). Add `tests/e2e/conftest.py` re-exporting/extending these for the `tests/e2e/` package.

**Checkpoint**: Harness ready — US1 and US2 can proceed (in parallel if staffed).

---

## Phase 3: User Story 1 - Realistic fixture projects (Priority: P1) 🎯 MVP

**Goal**: Three small, internally coherent, fully-valid Bookwright projects
(`tiny-novel`, `tiny-essay`, `tiny-memoir`) that double as test input and
worked examples.

**Independent Test**: Point `graph build`, `graph query`, and `validate` at each
fixture (copied to `tmp_path`) and confirm each succeeds with the expected
counts and zero `error`-severity violations (exit 0) — no E2E harness or docs needed.

### Implementation for User Story 1

- [ ] T005 [P] [US1] Author the `tiny-novel` fixture under `tests/fixtures/tiny-novel/`: `manifest.toml` (`[book] type = novel`, all built-in validators active), `bible/constitution.md` (narrative-voice declaration matching the chapter), exactly 3 `bible/characters/<slug>.md` (frontmatter `name` + optional `born`/`features`/`narrative_roles`), exactly 2 `bible/settings/<slug>.md` (`name`), `bible/timeline.md` with an `events:` list of exactly 5 items `{name, participants:[<char-slug>…]}` (every slug resolves to a character file — VR-6), fully-populated `outline/{synopsis,structure,arcs,scenes}.md`, and 1 draft chapter under `manuscript/` mentioning every character by name. No `[PENDING:]` sentinels, no `graph.ttl`, no skills dir (F4, F5; D9; fixture-shape contract)
- [ ] T006 [P] [US1] Author the `tiny-essay` fixture under `tests/fixtures/tiny-essay/`: `manifest.toml` (`[book] type = "essay"`, **all built-in validators active — `[validators] disabled = []`**, per revised D3), NO `bible/characters/` entries, 3 chapters under `manuscript/`, and a bibliography document (e.g. `bible/research.md`). It stays clean because `character_presence` emits only `warning`s without a roster and `focalization` is silent without a third-person voice declaration, so no validator is disabled and no `error`-severity finding occurs (fixture-shape contract; edge case "non-fiction false positives")
- [ ] T007 [P] [US1] Author the `tiny-memoir` fixture under `tests/fixtures/tiny-memoir/`: `manifest.toml` (`[book] type = "memoir"`, **all built-in validators active — `[validators] disabled = []`**), exactly 1 protagonist `bible/characters/<author>.md` (the author), and autobiographical scenes/chapters under `manuscript/` that mention the author by name (so `character_presence` finds no orphan). A first-person voice declaration in `bible/constitution.md` keeps `focalization` silent (its third-person branch never fires). No validator is disabled; the fixture passes with zero `error`-severity findings (fixture-shape contract)
- [ ] T008 [US1] Implement `tests/fixtures/test_fixtures.py` — for each fixture: copy to `tmp_path` (via T004 helper), run `graph build` (assert exit 0, 0 skips, 0 unknown_keys — VR-1/F2), run `graph query --json` (assert `tiny-novel` returns exactly 3 `Character`, 2 `Setting`, 5 `NarrativeEvent` — VR-2/SC-001; `tiny-memoir` single protagonist present), run `validate --json` (assert `result.exit_code == 0` **and** `payload["failed"] is False` **and** `payload["summary"]["by_severity"]["error"] == 0` for all three — VR-3/F3; assert against the **error** gate, NOT `status == "ok"`, since heuristic `warning`s are permitted and non-gating); plus a committed-tree guard asserting no `graph.ttl`/skills dir and no `[PENDING:]` sentinels in the shipped fixtures (VR-4, VR-5). Depends on T004–T007.

**Checkpoint**: All three fixtures validate clean; `tiny-novel` counts = 3/2/5. MVP increment complete.

---

## Phase 4: User Story 2 - End-to-end tests proving the full workflow (Priority: P1)

**Goal**: Automated, in-process E2E tests that walk the full new-user path and
lock down the two riskiest cross-cutting behaviors (skill materialization,
integration swap). These are the release gate and count toward coverage.

**Independent Test**: Run `uv run pytest tests/e2e -v` on a clean checkout and
confirm `test_full_workflow`, `test_skills_materialization`,
`test_integration_swap` all pass.

### Implementation for User Story 2

- [ ] T009 [P] [US2] Implement `tests/e2e/test_full_workflow.py` (C1, FR-006): empty `tmp_path` → `init <name> --integration claude` (assert manifest/bible/outline/manuscript/skills dir exist) → edit `manifest.toml` + `bible/constitution.md` (assert persistence) → `graph build` (exit 0; 0 skips/0 unknown_keys; `bible/graph.ttl` written) → `graph query "<counting SPARQL>" --json` (assert `json.loads(stdout)` is a single doc with expected counts) → `validate` and `validate --json` (exit 0 / zero `error`-severity, JSON body on stdout only — VR-9/Principle IX). Include ≥1 negative case: malformed SPARQL → non-zero exit + structured JSON error (exit 3). ≤ 500 lines (VR-8)
- [ ] T010 [P] [US2] Implement `tests/e2e/test_skills_materialization.py` (C2, FR-007): parametrized over `claude` (`.claude/skills/`) and `generic` (`.agents/skills/`); fresh `init` in `tmp_path`; for every `<skills_dir>/<name>/` call the shipped linter `bookwright.integrations.lint.lint_skill_md(skill_dir)` and assert it does not raise — this exercises the exact agentskills.io gate the toolkit enforces (valid YAML, `name == dir` & `< SKILL_NAME_MAX_LENGTH`, `description < SKILL_DESCRIPTION_MAX_LENGTH`, Principle VII). Do NOT re-encode the 64/1024 bounds in the test (single source of truth — Amendment A). Assert materialized-skill count == 10 source commands; negative assertion that no `*/commands/` directory is ever created (Principle VI). ≤ 500 lines
- [ ] T011 [P] [US2] Implement `tests/e2e/test_integration_swap.py` (C3, FR-008): `init --integration claude` in `tmp_path` (skills under `.claude/skills/`) → edit `manifest.toml` `[integration]` → `generic` → `init --here --force` (exit 0) → assert a valid `SKILL.md` set under `.agents/skills/`. Explicitly make NO assertion about removal of the old `.claude/skills/` dir (clarified 2026-06-03; spec Assumptions). ≤ 500 lines

**Checkpoint**: E2E suite green and contributing to `--cov` (VR-7/R2). US1 + US2 together satisfy SC-001 and SC-002.

---

## Phase 5: User Story 3 - A new user can self-serve from the docs (Priority: P2)

**Goal**: A Spanish MkDocs (`material`) site that builds `--strict` with zero
warnings, plus a finalized canonical README, so a newcomer can self-serve.

**Independent Test**: `uv run --group docs mkdocs build --strict` → exit 0, zero
warnings; the seven page areas exist with one page/section per shipped command;
the drift test passes.

### Implementation for User Story 3

- [ ] T012 [US3] Create `mkdocs.yml` at the repo root: `site_name`, `theme: {name: material}`, `strict: true`, and `nav` covering Inicio/Primeros pasos/Arquitectura/Comandos/Validación/Extender/FAQ (D5, docs-site contract). (Authored alongside the pages — keep nav targets in sync with T013–T019.)
- [ ] T013 [P] [US3] Write `docs/index.md` — qué es Bookwright + value prop (Spanish)
- [ ] T014 [P] [US3] Write `docs/getting-started.md` — install + 5-minute quickstart whose commands/flags match the shipped CLI (FR-015; mirrors `README.es.md`)
- [ ] T015 [P] [US3] Write `docs/architecture.md` — curated Spanish summary that LINKS `bookwright-design.md § N.M` and does NOT duplicate it wholesale (FR-013, VR-12)
- [ ] T016 [P] [US3] Write `docs/commands/` — one page or clearly delineated section per shipped command: `init`, `check`, `version`, `validate`, `graph build`, `graph query` (FR-012, DOC-2)
- [ ] T017 [P] [US3] Write `docs/validation.md` — the 4 built-in validators (`character_presence`, `focalization`, `setting_continuity`, `temporal`) + how to add a custom validator
- [ ] T018 [P] [US3] Write `docs/extending.md` — new integration / custom validator / vocabulary (mirrors CONTRIBUTING)
- [ ] T019 [P] [US3] Write `docs/faq.md` — common questions
- [ ] T020 [US3] Finalize `README.es.md` (canonical: qué es / install / 5-min quickstart / docs links; status updated to v0.1.0) and trim `README.md` to a short English pointer to `README.es.md` + docs (FR-010, VR-15; do not regress existing content)
- [ ] T021 [US3] Implement the docs↔CLI drift test (D4, VR-11, DOC-2) in `tests/e2e/test_docs_commands_match.py`: introspect `bookwright.cli:app`, **descending into registered sub-`Typer` groups to yield leaf command paths** (`init`, `check`, `version`, `validate`, `graph build`, `graph query` — not the top-level `graph` group), and assert the documented command set under `docs/commands/` equals that leaf set (no missing, no extra). Depends on T016
- [ ] T022 [US3] Run `uv run --group docs mkdocs build --strict` and confirm exit 0 with zero warnings (DOC-1, FR-014, SC-004). Depends on T012–T020

**Checkpoint**: Docs build clean; all seven page areas present; drift guard green (SC-004).

---

## Phase 6: User Story 4 - The release is packaged and gated for v0.1.0 (Priority: P3)

**Goal**: Finalized release metadata, CI gates for docs-build and artifact-build,
and a documented manual packaged-install validation — the last wrapper before tagging.

**Independent Test**: CHANGELOG/CONTRIBUTING/LICENSE present and accurate;
full quality suite green with coverage ≥ 80%; a locally built wheel installs into
a clean env and runs the quickstart.

### Implementation for User Story 4

- [ ] T023 [P] [US4] Finalize `CHANGELOG.md` — add a `## [0.1.0]` entry (Keep-a-Changelog) enumerating every shipped feature, consolidating `[Unreleased]` + iterations 1–11 (CLI: `init`, `graph build/query`, `validate`, `check`, `version`; the 10 authoring commands; GOLEM model; indexer; integrations; validation system) (FR-016, VR-14, SC-008)
- [ ] T024 [P] [US4] Finalize `CONTRIBUTING.md` — add sections for: create a new integration, create a custom validator, create a vocabulary (current draft lacks these) (FR-017, SC-008)
- [ ] T025 [P] [US4] Verify `LICENSE` is Apache-2.0 and referenced from `pyproject.toml` (`license = "Apache-2.0"` already set) (FR-018, SC-008)
- [ ] T026 [US4] Extend `.github/workflows/tests.yml`: add a docs-build gate `uv run --group docs mkdocs build --strict` (CI-5, FR-021) and an artifact-build step `uv build` producing wheel + sdist (CI-6, FR-022); leave the existing pytest/ruff/mypy matrix gates intact (CI-1…CI-4)
- [ ] T027 [US4] Document the manual packaged-install validation in this iteration's flow (D7, MAN-1…MAN-3): `uv build` → `pipx install ./dist/bookwright_cli-*.whl` → run the README quickstart against the installed CLI without touching the source tree; optionally add a `@pytest.mark.manual` test (deselected by default, exempt from coverage — R3) capturing the steps
- [ ] T028 [US4] Run the full quality-gate suite locally and confirm all green (VR-13, SC-005, SC-006): `uv run pytest` (coverage **≥ 80%**, fail-closed with no round-up via `[tool.coverage.report] precision = 2` set in T001), `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pre-commit run --all-files`, `uv run --group docs mkdocs build --strict`, `uv build`

**Checkpoint**: All metadata accurate, all gates green on the release branch (SC-006, SC-008).

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T029 [P] Confirm every new test file (`tests/fixtures/test_fixtures.py`, `tests/e2e/*.py`) is ≤ 500 lines (Principle IV, VR-8); split if any exceeds
- [ ] T030 Execute the maintainer `quickstart.md` walkthrough end-to-end and tick every "Done criteria" box (fixtures valid & counts 3/2/5; E2E green & counted; docs strict-clean with 7 areas; CHANGELOG/CONTRIBUTING/LICENSE; all gates green & coverage ≥ 80%; wheel installs and quickstart runs)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 → T003 (sync needs the group); T002 independent.
- **Foundational (Phase 2)**: T004 depends on T002; **blocks US1 test (T008) and all of US2**.
- **US1 (Phase 3)**: fixture authoring (T005–T007) needs no harness; T008 depends on T004 + T005–T007.
- **US2 (Phase 4)**: T009–T011 depend on T004. They drive fresh `init` (not the fixtures), so they do **not** strictly depend on US1 — but US1 is the higher-value MVP and is sequenced first.
- **US3 (Phase 5)**: T012–T020 depend only on Setup; T021 depends on T016; T022 depends on T012–T020. Content accuracy assumes the CLI behavior locked by US1/US2.
- **US4 (Phase 6)**: T023–T025 independent; T026 depends on the `docs` group (T001); T028 depends on US1–US3 (it runs every gate including `mkdocs build --strict`).
- **Polish (Phase 7)**: after all desired stories complete.

### User Story Dependencies

- **US1 (P1)**: depends only on Foundational. Independently testable.
- **US2 (P1)**: depends only on Foundational. Independently testable.
- **US3 (P2)**: depends on Foundational + a real CLI surface (US1/US2) for accurate docs/drift test.
- **US4 (P3)**: final wrapper — depends on US1–US3 for the green-gate run.

### Within Each User Story

- US1: author fixtures (T005–T007, parallel) → fixture-validity test (T008).
- US2: three independent test files, all parallel (T009–T011).
- US3: `mkdocs.yml` + pages (mostly parallel) → drift test (T021) → strict build (T022).
- US4: metadata (parallel) → CI wiring (T026) → full gate run (T028).

### Parallel Opportunities

- Setup: T002 ∥ T001.
- US1 authoring: **T005 ∥ T006 ∥ T007** (different fixture dirs).
- US2: **T009 ∥ T010 ∥ T011** (different test files).
- US3 pages: **T013 ∥ T014 ∥ T015 ∥ T016 ∥ T017 ∥ T018 ∥ T019** (different files).
- US4 metadata: **T023 ∥ T024 ∥ T025** (different files).
- Cross-story: once Foundational (T004) is done, US1 and US2 can proceed fully in parallel by different developers.

---

## Parallel Example: User Story 1 (fixtures)

```bash
# Author all three fixtures together (different directories, no shared files):
Task: "Author tiny-novel fixture under tests/fixtures/tiny-novel/"
Task: "Author tiny-essay fixture under tests/fixtures/tiny-essay/"
Task: "Author tiny-memoir fixture under tests/fixtures/tiny-memoir/"
# Then, once all three exist + T004 harness is ready:
Task: "Implement tests/fixtures/test_fixtures.py (build/query/validate each)"
```

## Parallel Example: User Story 2 (E2E)

```bash
# All three E2E files are independent — run in parallel after T004:
Task: "tests/e2e/test_full_workflow.py (init→edit→build→query→validate, C1)"
Task: "tests/e2e/test_skills_materialization.py (SKILL.md agentskills.io, C2)"
Task: "tests/e2e/test_integration_swap.py (claude→generic re-init, C3)"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 — both P1)

1. Phase 1 Setup → Phase 2 Foundational (T004 harness).
2. **US1** (fixtures + validity test) — STOP & VALIDATE: `uv run pytest tests/fixtures -v`, counts 3/2/5, exit 0 / zero `error`-severity.
3. **US2** (E2E suite) — STOP & VALIDATE: `uv run pytest tests/e2e -v` green, coverage contribution confirmed.
4. At this point the product is *demonstrably working end-to-end* (SC-001, SC-002) — the strongest "safe to ship" signal.

### Incremental Delivery

1. Setup + Foundational → harness ready.
2. US1 → fixtures validate → demo.
3. US2 → E2E green & counted → demo.
4. US3 → docs build strict-clean → demo.
5. US4 → metadata + CI gates + manual packaged validation → ready to tag v0.1.0.

### Parallel Team Strategy

After T004: Dev A takes US1, Dev B takes US2 (both P1, fully independent).
Once a real CLI surface is locked, Dev C takes US3 docs; US4 is the final
single-owner wrapper that runs all gates.

---

## Notes

- **No `src/bookwright/` runtime change** — this iteration is consolidation
  (fixtures, tests, docs, metadata, CI). Any source edit is out of scope.
- `[P]` tasks = different files, no dependencies.
- Fixtures ship **source only**; `bible/graph.ttl` is rebuilt in `tmp_path`
  (D2) — never commit it or a materialized skills dir (Principle I, F5).
- All three fixtures run the **full** built-in validator set (`disabled = []`);
  non-fiction stays clean because the fiction validators are inert off-genre
  (revised D3) — **no validator code change, no masking config**.
- E2E tests run in the default pytest selection (no `manual` marker) so they
  count toward the `≥80%` fail-closed (no round-up) coverage gate; only the
  packaged-wheel subprocess smoke is exempt (R2, R3).
- Keep each new test file ≤ 500 lines (Principle IV / VR-8).
- Commit after each task or logical group; the auto-git hook will offer.
