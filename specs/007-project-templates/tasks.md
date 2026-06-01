---
description: "Task list for Bible / Outline / Constitution Templates (iteration 7)"
---

# Tasks: Bible / Outline / Constitution Templates

**Input**: Design documents from `/specs/007-project-templates/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: INCLUDED. The plan explicitly specifies a `pytest` format/round-trip
validation suite under `tests/resources/` as the gate for this prose iteration
(SC-002/003/004/005, plan §Testing). Coverage line-gates do **not** apply
(SC-007), but the validation tests are real `pytest` and run in CI.

**Organization**: Tasks are grouped by user story (P1 → P3) so each slice is
independently authorable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Every task gives an exact file path.

## Path Conventions

- Skeleton singletons (stamped once by `init`): `src/bookwright/resources/project/`
- Re-instanceable molds (stamped many times by commands): `src/bookwright/resources/templates/`
- Validation tests: `tests/resources/`
- Repo-root artifact: `CHANGELOG.md`

## Conformance anchors (frozen upstream, FR-023 — do NOT modify)

- Walker (iter-4): `src/bookwright/commands/init/scaffold.py` — `.j2` rendered
  with `StrictUndefined` under the 5-key context `{title, project_slug, author,
  language, integration_key}`; **every other file byte-copied** (so no `.tmpl`
  under `project/`). Contract: [skeleton-walker-contract.md](contracts/skeleton-walker-contract.md).
- Mapper (iter-6): `src/bookwright/io/bible.py` + `io/frontmatter.py` — allowed
  top-level keys: Character `{name, born, died, features, narrative_roles}`,
  Setting `{name}`, Timeline `{events}`, Relationships `{relationships}`;
  `born`/`died` int-or-omitted, `features`/`narrative_roles` `list[str]`.
  Contract: [frontmatter-contract.md](contracts/frontmatter-contract.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the test package and a green baseline.

- [ ] T001 Verify baseline per quickstart prerequisites: iterations 1–6 merged on `main`, `uv sync` succeeds, and `uv run pytest -q` is green before authoring begins.
- [ ] T002 [P] Create the test package marker `tests/resources/__init__.py` (empty file) so the new validation suite is importable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared test fixture every story's validation suite imports.

**⚠️ CRITICAL**: No user-story test can run until this fixture exists.

- [ ] T003 Create `tests/resources/conftest.py` with a `pytest` fixture that stamps a fresh project into `tmp_path` via the real iter-4 scaffold (`bookwright.commands.init` / `render_resource_tree` with a representative 5-key context: `title`, `project_slug`, `author`, `language`, `integration_key`) and exposes (a) the stamped project root and (b) a helper that runs the iter-6 `map_bible` over it returning `skipped`/`unknown_keys`/`unresolved_participants`. Imports only the already-shipped iter-4/iter-6 modules — adds no production code (FR-023).

**Checkpoint**: Fixture ready — US1 and US2 tests can be written against it.

---

## Phase 3: User Story 1 - New project ships a complete, fill-in-ready narrative skeleton (Priority: P1) 🎯 MVP

**Goal**: Replace every placeholder stub under `resources/project/` with real
authored Spanish content so a fresh `bookwright init` yields a complete,
fill-in-ready `bible/` + `outline/` skeleton with zero stub sentinels.

**Independent Test**: `bookwright init` into a temp dir; assert every stamped
`bible/*.md`, `bible/constitution.md`, and `outline/*.md` is non-empty real
content with section headings + an HTML-comment guidance block and no stub
sentinel (`Placeholder — iteration 7`, `{{TODO}}`, …).

### Implementation for User Story 1

> All authoring tasks below touch distinct files → fully parallel `[P]`. Each
> file: Spanish prose/headings, ≥1 `<!-- -->` HTML-comment guidance block, a
> worked example **inside** an HTML comment (F3), `[PENDING: <pregunta>]`
> prompts in author-fill sections (F4, English token + Spanish question), no
> stub sentinel (F5), legible as plain Markdown (F1).

- [ ] T004 [P] [US1] Author `src/bookwright/resources/project/bible/constitution.md.j2` (FR-001): all `bookwright-design.md` § 9.2 sections — voz narrativa, registro, pacto con el lector, pacto histórico-ficcional *(marcado opcional)*, líneas rojas, invariantes de coherencia, vocabularios activos, notas para el agente — each with `[PENDING: …]` prompts + HTML-comment guidance. Jinja2 may reference **only** the 5 context keys (use `{{ title }}`, never `{{ book.title }}`); must render under `StrictUndefined` (W2).
- [ ] T005 [P] [US1] Author `src/bookwright/resources/project/bible/timeline.md` (FR-002): frontmatter fence on line 1, top-level key **exactly** `events: []` and nothing else (C2/C4); body documents the per-event shape `{name, participants: [<character-slug>]}`; a populated worked example lives **inside** an HTML comment so the shipped list stays empty (F3).
- [ ] T006 [P] [US1] Author `src/bookwright/resources/project/bible/relationships.md` (FR-003): frontmatter top-level key **exactly** `relationships: []` (C2/C4); body documents the per-relationship shape `{name, participants}`; worked example inside an HTML comment.
- [ ] T007 [P] [US1] Author `src/bookwright/resources/project/bible/themes.md` (FR-004): registro de motivos · rastreador de símbolos · mapa temático por capítulo. No frontmatter.
- [ ] T008 [P] [US1] Author `src/bookwright/resources/project/bible/glossary.md` (FR-005): registro de términos inventados · reglas de capitalización · bitácora de consistencia. No frontmatter.
- [ ] T009 [P] [US1] Author `src/bookwright/resources/project/bible/research.md` (FR-006): preguntas abiertas · notas de fuentes · hallazgos resueltos. No frontmatter.
- [ ] T010 [P] [US1] Author `src/bookwright/resources/project/bible/subplots.md` (FR-007): beat sheets de subtramas · puntos de intersección con la trama principal. No frontmatter.
- [ ] T011 [P] [US1] Author `src/bookwright/resources/project/bible/pov-structure.md` (FR-008): modo narrativo · calendario de POV · diferenciación de voz · mapa de asimetría de información; MUST state it applies only to multi-POV works (spec edge). No frontmatter.
- [ ] T012 [P] [US1] Author `src/bookwright/resources/project/outline/arcs.md` (FR-009): usable plantilla de arcos. No frontmatter.
- [ ] T013 [P] [US1] Author `src/bookwright/resources/project/outline/structure.md` (FR-009): usable plantilla estructural. No frontmatter.
- [ ] T014 [P] [US1] Author `src/bookwright/resources/project/outline/scenes.md` (FR-009): usable plantilla de escenas. No frontmatter.
- [ ] T015 [P] [US1] Author `src/bookwright/resources/project/outline/synopsis.md` (FR-009): a sinopsis corta (250–350 palabras) section **and** a sinopsis larga (1000–2000 palabras) section. No frontmatter.
- [ ] T016 [P] [US1] Author `src/bookwright/resources/project/README.md.j2` (FR-010): brief Spanish guide (dónde empezar, qué contiene cada directorio, comandos clave); renders under `StrictUndefined` using only the 5 context keys (W2).
- [ ] T017 [P] [US1] Review and extend `src/bookwright/resources/project/.gitignore` (FR-011): ensure cache (`.bookwright/cache`), Python artifacts, virtualenv, and env files are covered; keep/extend existing entries, do not regress.

### Tests for User Story 1

- [ ] T018 [P] [US1] Create `tests/resources/test_no_stub_sentinels.py` (SC-001/FR-022/F5): sweep both `src/bookwright/resources/project/`, `src/bookwright/resources/templates/`, and a freshly-stamped temp project (via the T003 fixture); assert no file contains `Placeholder — iteration 7`, `{{TODO}}`, or equivalent scaffolding marker.
- [ ] T019 [P] [US1] Create `tests/resources/test_skeleton_renders.py` (FR-010/W5): render every `.j2` under `resources/project/` with a representative W2 context (same `jinja2.Environment` settings, or by invoking `render_resource_tree` into a temp dir); assert no `UndefinedError` / `StrictUndefined` failure.

**Checkpoint**: A fresh `bookwright init` produces a complete, sentinel-free,
cleanly-rendering skeleton. US1 is independently demoable (the MVP).

---

## Phase 4: User Story 2 - Templates round-trip cleanly through the graph indexer (Priority: P1)

**Goal**: Author the two indexer-significant molds (`character`, `setting`) and
prove that they — plus the US1 `timeline.md`/`relationships.md` — round-trip
through the iter-6 mapper with zero skips and zero spurious warnings, and that a
filled instance maps to exactly one GOLEM entity.

**Independent Test**: Build the graph on (a) a fresh `init`-ed project and (b) a
fixture where the character/setting molds are stamped + filled; assert zero
`invalid_frontmatter` skips, zero `unknown_keys`, zero `unresolved_participants`,
and that filled instances produce the expected `Character`/`Setting`.

> Depends on US1 (the stamped skeleton, esp. `timeline.md`/`relationships.md`)
> being authored before the round-trip test (T022) can pass.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Author `src/bookwright/resources/templates/bible/character.md.tmpl` (FR-012/C2/C3/C5): frontmatter restricted to `⊆ {name, born, died, features, narrative_roles}`; `name` a string field (a `[PENDING: …]` value is legal **only quoted** — `name: "[PENDING: …]"`; bare brackets parse as a YAML list, C3); `born`/`died` left **commented or omitted** (never a non-int placeholder string); `features`/`narrative_roles` empty `list[str]`. Prose sections: rasgos biográficos · psicológicos · físicos · rol narrativo · diálogo de muestra · patrones de lenguaje corporal. "Edad" expressed only via `born`/`died` or prose (FR-012).
- [ ] T021 [P] [US2] Author `src/bookwright/resources/templates/bible/setting.md.tmpl` (FR-013/C2): frontmatter carries `name` and **no other** indexer-ingested key; prose sections for the broad narrative universe (cultura · sistema/era · geografía amplia).
- [ ] T022 [US2] Create `tests/resources/test_frontmatter_contract.py` (C6/SC-002/SC-003/FR-020): for every shipped template (skeleton + molds) assert it parses through `parse_frontmatter` without raising; then run `map_bible` over the T003 fresh temp project and assert `skipped == []`, `unknown_keys == []`, `unresolved_participants == []`. (Depends on T004–T017, T020, T021.)
- [ ] T023 [US2] Create `tests/resources/test_filled_instance_maps.py` (C5/SC-004): stamp `character.md.tmpl` → `bible/characters/<slug>.md` filled with `name` + int `born`/`died` + `features`/`narrative_roles` lists, and `setting.md.tmpl` → `bible/settings/<slug>.md` filled with `name`; index via `map_bible`; assert exactly one `Character` (carrying the declared attributes) and exactly one `Setting`.

**Checkpoint**: Indexed templates conform to the frozen mapper contract; SC-002
and SC-004 pass.

---

## Phase 5: User Story 3 - Re-instanceable molds ready for the authoring commands (Priority: P2)

**Goal**: Author the remaining non-indexed molds (`location`, `chapter`,
`scene`) under `resources/templates/` and verify the pre-existing manifest mold,
so iterations 8–9 have well-formed structures to stamp.

**Independent Test**: For each `.tmpl` under `resources/templates/`, assert it
parses without `yaml.YAMLError`, contains its required named sections, and (for
`character`/`setting`) uses indexer-recognized frontmatter keys.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Author `src/bookwright/resources/templates/bible/location.md.tmpl` (FR-014/spec edge): sensory-anchor sections — qué se ve · oye · huele · toca · atmósfera dominante; any frontmatter MUST be valid YAML and the template MUST NOT imply it is indexed (v0 has no `locations/` handler) — state "no indexado en v0" in an HTML comment.
- [ ] T025 [P] [US3] Author `src/bookwright/resources/templates/manuscript/chapter.md.tmpl` (FR-015): chapter drafting structure (estructura de capítulo) usable as a starting point; no indexer-ingested frontmatter.
- [ ] T026 [P] [US3] Author `src/bookwright/resources/templates/scenes/scene.md.tmpl` (FR-016): scene drafting structure (estructura de escena); no indexer-ingested frontmatter.
- [ ] T027 [US3] Verify (do NOT re-author) `src/bookwright/resources/templates/manifest.template.toml` (FR-025): confirm it covers all `Manifest.build` fields with English comments; record the verification outcome, leave the file unchanged.
- [ ] T028 [US3] Create `tests/resources/test_mold_structure.py` (US3 independent test): for each `.tmpl` under `resources/templates/`, assert (a) `parse_frontmatter` raises no `yaml.YAMLError`, (b) the mold's required Spanish section headings are present, (c) `character.md.tmpl`/`setting.md.tmpl` carry only indexer-recognized keys, and (d) `character.md.tmpl`'s `name` is a **non-empty `str`** after parse (i.e. any `[PENDING: …]` prompt is quoted, not a bare-bracket YAML list — catches the C3 quoting trap that `parse_frontmatter` alone would not raise on).

**Checkpoint**: All five molds exist and are well-formed; the manifest mold is
verified. US1, US2, US3 all independently testable.

---

## Phase 6: User Story 4 - Every template guides both a human and an AI agent (Priority: P3)

**Goal**: Lock the cross-cutting quality bar (HTML-comment guidance, `[PENDING]`
prompts, valid YAML, Spanish prose, originality) over every authored template,
and ship the CHANGELOG crediting the preset inspiration + recording the § 6
supersession.

**Independent Test**: Lint every authored template for ≥1 HTML-comment
instruction block, `[PENDING: …]` prompts in author-fill sections, valid YAML
where present, and absence of verbatim preset text; assert the CHANGELOG credit +
supersession note exist.

- [ ] T029 [P] [US4] Create `CHANGELOG.md` at repo root (FR-021/SC-006/F6): credit `fiction-book-writing` (adaumann, MIT) as structural inspiration, state Bookwright's redaction is original (Apache-2.0) and adapted to the GOLEM model, and record that this iteration supersedes design § 6's unified-template layout in favor of the lifecycle split.
- [ ] T030 [US4] Create `tests/resources/test_authoring_guidance.py` (SC-005/FR-017/FR-018/FR-019/F7): per authored template assert ≥1 `<!-- -->` HTML-comment block, presence of `[PENDING:` in author-fill sections, valid YAML where a fence is present, and Spanish-prose heuristics where applicable; plus assert `CHANGELOG.md` contains the preset credit and the § 6 supersession note (F6).

**Checkpoint**: Every authored template meets the cross-cutting bar; CHANGELOG
records attribution + supersession (SC-005/SC-006).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final gate + manual round-trip confirmation per quickstart.

- [ ] T031 Run the full CI gate (quickstart § 6): `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict src tests` — all four green (ruff/mypy apply to the new test modules; templates are not Python).
- [ ] T032 [P] Manual round-trip validation (quickstart § 4–5): `bookwright init /tmp/qt-book --integration generic`; `bookwright graph build --json` → assert `skipped == []` and `unknown_keys == []` (SC-002); stamp a filled `character.md.tmpl` into `bible/characters/` and re-index → exactly one `Character` (SC-004).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2, T003)**: depends on Setup — **blocks** every story's tests.
- **US1 (Phase 3)**: depends on Foundational. The MVP. No dependency on other stories.
- **US2 (Phase 4)**: depends on Foundational; its round-trip test (T022) additionally depends on US1 skeleton authoring (esp. T005/T006 `timeline.md`/`relationships.md`).
- **US3 (Phase 5)**: depends on Foundational. Independent of US1/US2 content.
- **US4 (Phase 6)**: its lint (T030) covers every authored template, so it is most meaningful **after** US1–US3 author their files; the CHANGELOG (T029) is independent and can land anytime.
- **Polish (Phase 7)**: depends on all desired stories complete.

### Within Each User Story

- US1: authoring tasks (T004–T017) are mutually parallel; tests (T018/T019) after the files exist.
- US2: molds (T020/T021) before the tests; T022 also needs US1 done; T023 needs T020/T021.
- US3: molds (T024–T026) + verify (T027) before the structure test (T028).
- US4: CHANGELOG (T029) anytime; lint (T030) after authored templates exist.

### Parallel Opportunities

- T002 (Setup) is `[P]`.
- **All 14 US1 authoring tasks T004–T017 run in parallel** (distinct files); T018/T019 in parallel after them.
- US2 molds T020/T021 in parallel.
- US3 molds T024/T025/T026 in parallel.
- T029 (CHANGELOG) parallel with anything.
- Across stories: once Foundational is done, US1/US2-molds/US3-molds/CHANGELOG authoring can proceed concurrently; only the round-trip/lint tests gate on their inputs.

---

## Parallel Example: User Story 1

```bash
# Author all 14 skeleton singletons together (distinct files, no deps):
Task: "Author bible/constitution.md.j2 (T004)"
Task: "Author bible/timeline.md (T005)"
Task: "Author bible/relationships.md (T006)"
Task: "Author bible/themes.md (T007)"
Task: "Author bible/glossary.md (T008)"
Task: "Author bible/research.md (T009)"
Task: "Author bible/subplots.md (T010)"
Task: "Author bible/pov-structure.md (T011)"
Task: "Author outline/arcs.md (T012)"
Task: "Author outline/structure.md (T013)"
Task: "Author outline/scenes.md (T014)"
Task: "Author outline/synopsis.md (T015)"
Task: "Author README.md.j2 (T016)"
Task: "Review/extend .gitignore (T017)"

# Then both US1 validation tests together:
Task: "test_no_stub_sentinels.py (T018)"
Task: "test_skeleton_renders.py (T019)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup → Phase 2 Foundational (T003 fixture).
2. Phase 3 US1: author all skeleton singletons + sentinel/render tests.
3. **STOP & VALIDATE**: `bookwright init` into a temp dir reads as a complete,
   sentinel-free skeleton (SC-001). This alone fixes the broken-stub defect and
   is demoable.

### Incremental Delivery

1. Setup + Foundational → fixture ready.
2. US1 → fresh project ships a real skeleton (MVP, SC-001) → demo.
3. US2 → indexed templates + molds round-trip cleanly (SC-002/003/004) → demo.
4. US3 → all molds ready for iter 8–9 → demo.
5. US4 → cross-cutting bar locked + CHANGELOG (SC-005/006).
6. Polish → full CI gate + manual round-trip.

---

## Notes

- This iteration writes **no production Python** — deliverables are
  Markdown/`.j2`/`.tmpl` documents + `CHANGELOG.md`. The only Python authored is
  the `tests/resources/` validation suite (T003, T018, T019, T022, T023, T028,
  T030), which imports the frozen iter-4/iter-6 modules and re-implements nothing
  (FR-023).
- Line-coverage gates are N/A for prose (SC-007); the format/round-trip/lint
  tests are the real gate.
- `[P]` = different files, no dependencies.
- Keep human-facing prose Spanish; frontmatter keys + the `[PENDING]` token
  English (Clarification Q1 / F2).
- Commit after each logical group; stop at any checkpoint to validate a story.
