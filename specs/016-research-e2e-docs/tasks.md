---
description: "Task list for 016 — Historical fixture, research E2E flow, and v0.2.0 documentation"
---

# Tasks: Historical fixture, research E2E flow, and v0.2.0 documentation

**Input**: Design documents from `/specs/016-research-e2e-docs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (all present)

**Branch**: `016-research-e2e-docs`

**Tests**: This iteration's *product* is tests + a fixture + docs. The E2E module
(`tests/e2e/test_research_workflow.py`) is a deliverable, not a TDD scaffold — it is authored
**after** the fixture it asserts on exists, so no separate "write failing test first" sub-phase
applies. No new `src/` production code is added (plan.md §Summary).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: can run in parallel (different files, no incomplete dependency)
- **[Story]**: which user story the task serves (US1–US4); Setup/Foundational/Polish carry none
- Paths are exact and relative to repo root (`/Users/jorge/Projects/bookwright/`)

## Path Conventions

Single project, src-layout. This iteration touches only `tests/fixtures/`, `tests/e2e/`,
`docs/`, and `mkdocs.yml` — never `src/` (Constitution III, plan.md §Project Structure).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: stand up the empty fixture tree and its manifest so all subsequent authoring has a
home. Mirrors `tests/fixtures/tiny-novel/` exactly.

- [ ] T001 Create the `tests/fixtures/tiny-historical/` directory tree (empty dirs):
  `bible/`, `bible/characters/`, `bible/settings/`, `bible/research/`, `outline/`, `manuscript/`
  — per `contracts/fixture-layout.md`.
- [ ] T002 [P] Author `tests/fixtures/tiny-historical/manifest.toml` per
  `contracts/fixture-layout.md`: `[bookwright]` (schema `golem-1.1`, `uri_base`, `indexer="rdflib"`),
  `[book]` (`type="novel"`, `language="es"`), `[research]` (`enabled=true`,
  `source_languages=[…foreign ISO-639-1…]`, `min_reliability_for_anchor="media"`),
  `[validators]` all-built-in (`enabled=[]`/`disabled=[]`/`custom=[]`), `[integration] key="claude"`,
  `[paths]`. Try the **minimal** config first: omit `[vocabularies] active` unless a real
  `graph build`/`validate` fails without it; if `sources` proves required, add it **and record
  why in a manifest comment** so the decision isn't re-litigated later (D8).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: ground every fixture-authoring and test task in the *real* strict reader and the
*real* validator rules, so the three planted defects fire **exactly** (1 warning + 1 error) and
nothing in the corpus accidentally aborts the build. No file output — these are confirmation reads.

**⚠️ CRITICAL**: do these before authoring the research corpus (T010–T014); a wrong facet name
aborts `graph build` and a wrong year-span makes the deterministic test flaky.

- [ ] T003 Confirm the strict reader's contract by reading `src/bookwright/io/research.py` and
  `tests/io/test_research.py`: the 9 required `Source` facets, the controlled `type` vocab
  ({primaria, secundaria, oficial, académica, periodística, testimonial}), `reliability`
  ∈ {alta, media, baja}, the `translation`-iff-`original_language≠"es"` rule, and which faults are
  **fatal** (abort build) vs. tolerated — so defect #1 stays *parseable* (validation-malformed, not
  parse-malformed; data-model.md E2).
- [ ] T004 Confirm `factual_anchor` firing conditions by reading
  `src/bookwright/validation/validators/factual_anchor.py` (rules R3 `_under_reliable`,
  R5 `_anachronism`) and `tests/validation/test_factual_anchor.py`: exact threshold comparison for
  R3 (`baja` < `media` floor) and the disjoint-interval logic for R5 (`date` vs `begin`/`end`), so
  defects #1 and #2 each emit one finding and no other anchor trips a rule.

**Checkpoint**: reader + validator semantics are pinned. Fixture authoring can begin.

---

## Phase 3: User Story 1 - A worked historical example with real provenance (Priority: P1) 🎯 MVP

**Goal**: ship `tests/fixtures/tiny-historical/` — a short, coherent, historically-set novel that
is a valid Bookwright project with a fully-attributed `bible/research/` corpus, exactly three
planted defects, and a co-located expected-findings oracle (FR-001..FR-007, FR-012).

**Independent Test**: `cp -r tests/fixtures/tiny-historical /tmp/th && cd /tmp/th &&
uv run bookwright graph build --json` exits 0 and the derived graph holds Source/Finding/Anchor
triples; a reader opening `bible/research/` finds the topic, the Source registry, and the anchors.

- [ ] T005 [P] [US1] Author `tests/fixtures/tiny-historical/bible/constitution.md` — short Spanish
  premise/voice/rules for the historical novel (mirror `tiny-novel/bible/constitution.md`).
- [ ] T006 [P] [US1] Author `tests/fixtures/tiny-historical/bible/timeline.md` with **≥1 event
  carrying a year** (`date` or `begin`/`end`). This dated event is the *target* defect #2's
  anachronistic anchor will contradict (FR-004/FR-006; data-model.md E1).
- [ ] T007 [P] [US1] Author `tests/fixtures/tiny-historical/bible/characters/<slug>.md` (≥1
  character; one is the entity a **clean** anchor `constrains`, exercising FR-005's
  character-link variety). **Do NOT make this character the target of the anachronistic anchor
  (defect #2)**: `factual_anchor` R5 only yields a comparable interval for an **event/timeline**
  target — `_target_interval` returns `None` for a character, so an anchor constraining a
  character can never trip R5. Defect #2's anchor must constrain the **dated timeline event**
  from T006 (owned by T011), not this character (FR-005).
- [ ] T008 [P] [US1] Author `tests/fixtures/tiny-historical/bible/settings/<slug>.md` (≥1 setting)
  consistent with the historical period.
- [ ] T009 [P] [US1] Author the outline skeleton
  `tests/fixtures/tiny-historical/outline/{synopsis,structure,arcs,scenes}.md` (enough to be a
  valid project; mirror `tiny-novel/outline/`).
- [ ] T010 [US1] Author `tests/fixtures/tiny-historical/bible/research/sources.md` — several
  `Source`s, each with all 9 facets (FR-003); **≥1 foreign-language** source with `translation`
  (multilingual provenance); **≥1 source with `reliability: baja`** reserved for defect #1. Depends
  on T003.
- [ ] T011 [US1] Author `tests/fixtures/tiny-historical/bible/research/<topic>.md` — Findings citing
  the Sources plus the Anchors: the **clean** anchors (fully-sourced ≥`media`, present
  finding+entity, temporally consistent), **defect #1** (an anchor promoting a finding whose only
  source is the `baja` one → R3 **warning**), and **defect #2** (a *different* anchor `constrains`-ing
  the dated timeline event from T006 with a **disjoint year-span** → R5 **error**). Keep #1 and #2 on
  separate anchors so the mapping is 1:1 (data-model.md E2). Depends on T004, T006, T007, T010.
- [ ] T012 [P] [US1] Author `tests/fixtures/tiny-historical/bible/research/_index.md` — ≥1 open
  question + topic map (prose body, not indexed) (contracts/fixture-layout.md).
- [ ] T013 [US1] Author `tests/fixtures/tiny-historical/manuscript/NN-<slug>.md` — a chapter whose
  Spanish prose contains **defect #3**: one unambiguous anachronism (object/tech/event impossible in
  the story's year) that contradicts a **dated anchor** from T011 (FR-006; for the verify layer).
  Depends on T011.
- [ ] T014 [US1] Author `tests/fixtures/tiny-historical/expected-findings.md` — the co-located oracle
  at the fixture **root** (NOT under `bible/research/`). YAML front-matter per
  `contracts/expected-findings.md`: `factual_anchor.expected_counts {error: 1, warning: 1}`,
  `warning_anchor` (defect #1 id), `error_anchor` (defect #2 id); `verify.manuscript_file`,
  `verify.contradicted_anchor`, `verify.prose_anachronism`. Spanish body stating the three expected
  findings and that no verbatim LLM report is committed (FR-012). Depends on T011, T013.

**Checkpoint**: the fixture builds, research parses, and `validate` already reports the planted
1 warning + 1 error by hand. US1 deliverable complete — this is the MVP.

---

## Phase 4: User Story 2 - The research flow proven end to end (Priority: P1)

**Goal**: `tests/e2e/test_research_workflow.py` — an in-process-CLI regression that walks
build → query → validate over the fixture, asserts the planted findings against the oracle, and
confirms the verify-step preconditions (FR-008..FR-012). Mirrors `tests/e2e/test_full_workflow.py`
+ `tests/fixtures/test_fixtures.py`; uses `tests/conftest.py::copy_fixture` + `CliRunner`; every
command invoked with `--json`. Stays ≤ 500 lines (Constitution IV) — split into helper-grouped
sections if it approaches the limit.

**Independent Test**: `uv run pytest tests/e2e/test_research_workflow.py` is green; flipping any
planted defect in the fixture turns it red.

- [ ] T015 [US2] Create `tests/e2e/test_research_workflow.py` scaffold: an oracle-loader helper that
  reads `tiny-historical/expected-findings.md` front-matter **once** (single source of truth, no
  hard-coded counts), plus the `copy_fixture("tiny-historical", tmp_path)` + `monkeypatch.chdir` +
  `CliRunner` harness (real signature `copy_fixture(name, dest_parent)`, `tests/conftest.py`).
  Keep the module single-file (it is expected to land ~250–300 lines, well under the 500-line
  Constitution-IV ceiling — do **not** pre-split into helper modules: that is speculative
  structure). **Contingency only if it later exceeds 500 lines**: first lift the oracle-loader +
  harness into module-level `pytest` fixtures; only if still over, move Group C inertness
  (T019/T020) into a sibling `tests/e2e/test_research_inertness.py`.
- [ ] T016 [US2] **Group A** (deterministic flow) in `tests/e2e/test_research_workflow.py`:
  (a) `graph build --json` exit 0 and the derived graph holds Sources/Findings/Anchors (`bw:`
  triples; an anchor `E13` with `bw:promotes`; a `bw:supportedBy` source) — FR-008/009;
  (b) `graph query --json` with the payoff SPARQL returns the anchors with claims/sources
  **including the dated anchor**, and a span query returns its `begin`/`end` — FR-010;
  (c) `validate --json` → `factual_anchor` emits **exactly** the oracle counts `{warning:1, error:1}`,
  warning on `warning_anchor`, error on `error_anchor`, **no other** `factual_anchor` finding, and
  non-zero exit (error gate fires) — FR-011. Scope the count assertion to
  `validator == "factual_anchor"`.
- [ ] T017 [US2] **Group B** (verify preconditions) in `tests/e2e/test_research_workflow.py`:
  the payoff query returns the `contradicted_anchor` with claim+source; `integration use claude` in
  the tmp copy writes `.claude/skills/bookwright-verify/SKILL.md` **and**
  `.claude/skills/bookwright-research/SKILL.md`; `expected-findings.md` exists at the fixture root and
  its front-matter parses (FR-012). No LLM invoked.
- [ ] T018 [US2] **Group D** (fixture hygiene, E1 invariants) in
  `tests/e2e/test_research_workflow.py`: the committed `tiny-historical` tree ships **no**
  `bible/graph.ttl`, **no** `.claude/`/`.agents/`, **no** `SKILL.md`, and **no** `[PENDING:` sentinel
  in any `*.md`.

**Checkpoint**: the whole deterministic research flow is guarded; US1 + US2 together prove the
release's headline claim.

---

## Phase 5: User Story 3 - The system is inert when unused (Priority: P2)

**Goal**: prove research machinery imposes zero cost on projects that don't opt in — the
no-directory case (reuse `tiny-novel`) and the disabled-block case (toggle a tmp copy)
(FR-013/FR-014). Added as **Group C** in the same `tests/e2e/test_research_workflow.py` module.

**Independent Test**: the two inertness tests pass against an unchanged `tiny-novel` and a
`enabled=false` copy of `tiny-historical`, each showing zero research entities and zero
`factual_anchor` findings.

- [ ] T019 [US3] **Group C / no-directory** in `tests/e2e/test_research_workflow.py`: copy
  `tiny-novel`, run build → query → validate; assert derived `graph.ttl` has **no** `bw:` prefix,
  `E13` count equals the bible baseline, **zero** `factual_anchor` findings, `validate` exit 0 and
  `failed is False` (FR-013).
- [ ] T020 [US3] **Group C / disabled-block** in `tests/e2e/test_research_workflow.py`: copy
  `tiny-historical` to `tmp_path`, set `[research].enabled = false` in its `manifest.toml`, run
  build → validate; assert **zero** `factual_anchor` findings and no `error` from the research layer
  (overall validation behaves like a clean v0.1 project) (FR-014). Depends on T015 (shared module);
  reuses the fixture from US1.

**Checkpoint**: non-regression for the entire v0.1 user base is guarded.

---

## Phase 6: User Story 4 - The new system is documented for release (Priority: P2)

**Goal**: teach the research system on the MkDocs-Material Spanish site and record the release —
a research page, reference updates, and a v0.2.0 changelog, all under `strict: true`
(FR-015..FR-018, FR-021). Prose in Spanish; identifiers/command names as-is.

**Independent Test**: `uv run mkdocs build` completes with zero warnings; the research page is
reachable from the nav and covers the five required topics; the reference and changelog show the
new surface.

- [ ] T021 [P] [US4] Author `docs/research.md` (new): the five required topics — what research is in
  Bookwright, the Source/Finding/Anchor model, the `bookwright-research` skill protocol, the
  two-layer verification (`factual_anchor` validator + `bookwright-verify` LLM skill, incl.
  `bookwright-verify`/`bookwright-research`), and multilingualism + provenance; reference the
  `tiny-historical` worked example and quote/link its `expected-findings.md` (FR-015/FR-016/FR-017).
- [ ] T022 [P] [US4] Edit `docs/validation.md`: add the `factual_anchor` row to "Validadores
  integrados" (rules R1–R5, warning/error severities) (FR-016).
- [ ] T023 [P] [US4] Edit `docs/authoring.md`: note `bookwright-research` and `bookwright-verify` in
  the skills reference (trigger on ES + EN prompts) (FR-016).
- [ ] T024 [P] [US4] Author `docs/changelog.md` (new): a v0.2.0 entry describing the research &
  verification system, plus a retroactive v0.1.0 entry (FR-018).
- [ ] T025 [US4] Edit `mkdocs.yml` `nav`: add "Investigación: research.md" and "Cambios:
  changelog.md"; keep `strict: true` (FR-017/FR-021). Run after T021 + T024 so strict-mode link
  resolution succeeds.

**Checkpoint**: the system is learnable and the release is recorded.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: run every release gate green (FR-019..FR-022, SC-005..SC-007).

- [ ] T026 [P] Run `uv run pytest tests/e2e/test_research_workflow.py` — the new regression is green.
- [ ] T027 Run the full `uv run pytest` — overall coverage ≥ 80 % (the single enforced gate) and
  confirm new M4 code is ≥ 85 % as a **report-only** quality target (no second `fail_under`)
  (FR-019/SC-005).
- [ ] T028 [P] Run `uv run ruff check && uv run ruff format --check && uv run mypy --strict`
  (FR-020/SC-006).
- [ ] T029 Run `uv run mkdocs build` — strict mode, **zero warnings** (FR-021/SC-006).
- [ ] T030 Walk `specs/016-research-e2e-docs/quickstart.md` end-to-end (incl. the documented manual
  verify step's preconditions) and confirm no ChromaDB/vector or other v0.3+ mechanism, no new CLI
  command, no new manifest field were introduced (FR-022/SC-007).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (P1)** → no deps; start immediately.
- **Foundational (P2)** → after Setup; **blocks** the research-corpus tasks (T010–T014).
- **US1 (P3)** → after Foundational. The fixture is the foundation US2/US3-disabled consume.
- **US2 (P4)** → after **US1** (the test asserts on the fixture + its oracle).
- **US3 (P5)** → no-directory half (T019) only needs `tiny-novel` (always present) + the test
  module scaffold (T015); disabled half (T020) needs US1's fixture. Practically: after T015.
- **US4 (P6)** → independent of the tests; can run any time after the mechanism is understood, but
  references the `tiny-historical` worked example (US1) for accuracy.
- **Polish (P7)** → after all desired stories.

### Critical Path (MVP = US1 + US2)

```
T001 → T002 → T003/T004 → T005..T009 → T010 → T011 → T013 → T014 → T015 → T016/T017/T018
```

### Within stories

- **US1**: skeleton (T005–T009) before research (T010–T012); `sources.md` (T010) before
  `<topic>.md` (T011); `<topic>.md` before the anachronistic `manuscript` (T013); both before the
  oracle (T014).
- **US2/US3**: all live in `tests/e2e/test_research_workflow.py` — T015 (scaffold) first, then
  T016–T020 edit the same module **sequentially** (no `[P]` among them; same file).
- **US4**: T021–T024 are independent files (`[P]`); T025 (`mkdocs.yml`) after the new pages exist.

### Parallel Opportunities

- T002 runs alongside T001's follow-on work (different file).
- **US1 skeleton**: T005, T006, T007, T008, T009 are all different files → fully parallel.
- T012 (`_index.md`) parallel with T011 (different file, both after T010).
- **US4**: T021, T022, T023, T024 are four independent docs files → fully parallel.
- **Polish**: T026 and T028 parallel (read-only gates on different toolchains).

---

## Parallel Example: User Story 1 skeleton

```bash
# After T002 (manifest) and T003/T004 (grounding), author the non-research skeleton in parallel:
Task: "Author bible/constitution.md"                         # T005
Task: "Author bible/timeline.md with ≥1 dated event"         # T006
Task: "Author bible/characters/<slug>.md"                    # T007
Task: "Author bible/settings/<slug>.md"                      # T008
Task: "Author outline/{synopsis,structure,arcs,scenes}.md"   # T009
```

## Parallel Example: User Story 4 docs

```bash
Task: "Author docs/research.md"            # T021
Task: "Edit docs/validation.md"            # T022
Task: "Edit docs/authoring.md"             # T023
Task: "Author docs/changelog.md"           # T024
# then T025: edit mkdocs.yml nav (after research.md + changelog.md exist)
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Setup (T001–T002) + Foundational (T003–T004).
2. US1 (T005–T014) — the worked fixture. **STOP & VALIDATE**: build/validate by hand show 1
   warning + 1 error.
3. US2 (T015–T018) — the regression that locks it in. This pair is the release's headline proof.

### Incremental Delivery

1. Setup + Foundational → ready.
2. US1 → the fixture stands alone as a demonstration (MVP demo).
3. US2 → the deterministic flow is guarded.
4. US3 → non-regression for non-research projects.
5. US4 → the system is documented.
6. Polish → all gates green; release-ready.

---

## Notes

- `[P]` = different files, no incomplete dependency.
- The E2E module is the **deliverable** (not a TDD scaffold); it is authored after the fixture and
  must stay ≤ 500 lines — split into helper-grouped sections if it grows.
- The oracle (`expected-findings.md`) is the single source of truth for counts + anchor ids — never
  hard-code them in the test.
- Keep `tiny-historical` **out of** `tests/fixtures/test_fixtures.py`'s clean-fixtures
  parametrization (it validates with 1 warning + 1 error by design).
- No `src/` change, no new CLI command, no new manifest field, no vectors (FR-022).
- Commit after each logical group; the auto-git hooks offer commits between phases.
