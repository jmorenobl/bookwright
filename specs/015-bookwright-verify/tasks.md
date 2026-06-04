---
description: "Task list for the bookwright-verify skill (iteration 015)"
---

# Tasks: `bookwright-verify` Skill (semantic verification vs. anchors)

**Input**: Design documents from `specs/015-bookwright-verify/`
**Prerequisites**: plan.md, spec.md, research.md (D1–D8), data-model.md (E1–E4),
contracts/bookwright-verify-skill.md (C1–C8), quickstart.md

**Tests**: This iteration adds **no new test files**. The new command is *data*
exercised by the existing data-driven sweeps (frontmatter / activation / body /
materialization) that parametrize over `command_files()` and `iter_command_sources()`.
The only test edits are roster-literal additions and one parametrize extension so the
already-shipped gates admit, describe, and report-only-check the new command. Those
edits are listed as ordinary tasks (not a separate "tests" sub-section) because they
are wiring, not new test logic.

**Organization**: Grouped by the three user stories from spec.md (P1 → P2 → P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task).
- **[Story]**: `US1` / `US2` / `US3`; omitted for Setup / Foundational / Polish.
- Every task names an exact file path.

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repository root.

---

## ⚠️ Reality of this iteration (read before executing)

The deliverable is **one packaged Markdown command-source file** plus **four
hand-maintained roster edits** — there is *no new Python behaviour* (research D1).
Consequences that shape the task graph and the "zero technical debt" bar:

- **One file, many sections.** All US1/US2 body tasks edit the *same* file
  (`bookwright-verify.md`); they are therefore **sequential** (no `[P]`), each adding a
  distinct section. The test-roster edits live in *different* files and so are `[P]`.
- **The four roster sites are the whole risk surface** (research D2). Missing any one
  turns a CI gate red. They are enumerated as explicit tasks so none is skipped.
- **No-edit / auto-derived sites — do NOT touch them** (plan "No-edit" note):
  `integrations/materialize.py::iter_command_sources` (globs the dir),
  `tests/integrations/test_setup_materialize.py::_ROSTER` and
  `tests/commands/init/test_e2e_materialize.py::_ROSTER` (derived from
  `iter_command_sources()`), and the parametrized frontmatter/activation/body sweeps
  over `command_files()`. Editing them would be redundant and is a code-smell here.
- **`test_graph_build_is_inline` asserts the literal string `bookwright graph build
  --json`** (verified in `tests/resources/test_command_body.py:87`). The body must
  contain that exact inline call (mirroring `bookwright-continuity`) **and then** the
  `bookwright graph query <SPARQL>` step (FR-005). Using a different phrasing would
  pass the human eye but fail the gate — no shortcut.
- **SC-009 is a byte-equality gate.** The `description` in the source frontmatter and
  in `SKILL_DESCRIPTIONS["bookwright-verify"]` must be **byte-identical**. Draft it
  once (T003), paste it verbatim in both places (T004, T015).

---

## Phase 1: Setup (verify ground truth before authoring)

**Purpose**: Confirm the dependencies the skill *reads against* actually exist on this
branch, and internalise the structural template — so the source is authored against
real vocabulary, not assumptions.

- [X] T001 Confirm the branch is `015-bookwright-verify` and that the prerequisite
  iterations are present on `main`/this branch, reading the **actual graph shape** the
  SPARQL must target (research **D5** — there is **no** `bw:Anchor`/`bw:Source`
  `rdf:type`): in `src/bookwright/golem/modules/provenance.py` confirm an **Anchor** is
  a `crm:E13_Attribute_Assignment` discriminated by `bw:promotes` (findings share the
  class but never carry it), a **Finding** carries `bw:claim` + `bw:supportedBy`, and a
  **Source** emits no `rdf:type` (typed via `crm:P2_has_type → crm:E55_Type`) with
  `bw:reference`/`bw:author`/`bw:reliability`/`bw:originalQuote`/`bw:translation`
  facets (predicates declared in `src/bookwright/resources/vocabularies/sources.ttl`
  and `src/bookwright/golem/namespaces.py`). Confirm the `factual_anchor` validator the
  skill is the complement to (`src/bookwright/validation/validators/`) and the
  `Severity` enum whose `error`/`warning`/`info` vocabulary the report reuses
  (`src/bookwright/validation/base.py`). Validate the read surface empirically — build a
  minimal Anchor→Finding→Source chain through the real classes + `RdflibIndexer` and run
  research D5's reference query, confirming it returns rows while `?a a bw:Anchor`
  returns none. Record any gap as a blocker — do **not** author the SPARQL/severity
  references against vocabulary that is not on the branch (research D5/D6, spec
  Dependencies).
- [X] T002 Study the structural template `src/bookwright/resources/commands/bookwright-continuity.md`
  (the analogous read-only post-draft report, plan "Structure Decision"): note its
  YAML frontmatter shape, the eight ES section headings, the explicit "solo lectura"
  statement, the inline `bookwright graph build --json` call, and the
  "Información faltante / prerrequisito ausente" phrasing. This is the shape
  `bookwright-verify.md` must mirror.

---

## Phase 2: Foundational (blocking prerequisites — BLOCKS all user stories)

**Purpose**: Produce the two shared artifacts every story depends on: the single
authoritative description string, and the source file skeleton that the body tasks
fill and the rosters point at.

**⚠️ CRITICAL**: No user-story body content or roster edit is meaningful until the file
exists and the canonical description is fixed.

- [X] T003 Finalise the **authoritative bilingual ES/EN `description`** string from
  research D3 (verbatim ES + EN triggers, the word `post-draft`, "solo lectura", and
  the explicit repulsion of `bookwright-continuity` and the `factual_anchor` validator),
  verifying it is `< 1024` chars (FR-003). Record it as the single source of truth to be
  pasted byte-identically into both the frontmatter (T004) and `SKILL_DESCRIPTIONS`
  (T015) — this is what the SC-009 equality gate checks (research D3, contract C2/C5).
- [X] T004 Create `src/bookwright/resources/commands/bookwright-verify.md` with valid
  YAML frontmatter (`name: bookwright-verify` equal to the filename stem; `description:`
  = the T003 string verbatim; **no** `license`, `scripts`, or `handoffs` keys) and the
  eight Spanish section-heading skeleton in order: **Rol, Input, Procedimiento, Output,
  Archivos a leer, Archivos a escribir, Información faltante, Qué NO hacer**
  (data-model E1, contract C1/C2/C3). File ≤ 500 lines; `{ARGS}` is the only
  transformable token used anywhere in the body (no other `{…}`/`{SCRIPT}` token).

**Checkpoint**: The file exists and is admitted by `iter_command_sources()`; the
canonical description is fixed. The body sweeps will now *fail loudly* until the
sections are authored (T005–T013) and the rosters updated — that is expected.

---

## Phase 3: User Story 1 — Verify the manuscript against research anchors (Priority: P1) 🎯 MVP

**Goal**: Author the body that makes the agent build+query the graph for anchors and
their sources, read the manuscript, and report passages that **contradict** an anchor —
read-only, never failing opaquely.

**Independent Test**: After `bookwright init`, in an agent run `/bookwright-verify`
against a project whose graph carries an anchor ("private detectives were not legally
licensed in Spain before 1957") and a 1950 manuscript scene with a licensed PI; confirm
the agent loads anchors via `bookwright graph query`, reads `manuscript/`, and reports
that passage as a contradiction — while a consistent manuscript yields none
(spec US1 Independent Test, SC-002/SC-003).

> All body tasks below edit the same file (`bookwright-verify.md`) → sequential, no `[P]`.

- [X] T005 [US1] Author the **Rol** and **Input** sections in
  `src/bookwright/resources/commands/bookwright-verify.md`: agent is a verifier of
  factual fidelity comparing the drafted manuscript against the research anchors,
  touching nothing; `{ARGS}` = optional focus (a chapter or topic), base = the
  manuscript read against the anchors (data-model E1 §1–§2, FR-018).
- [X] T006 [US1] Author the **Procedimiento** section: (i) run `bookwright graph build
  --json` **inline** (exact string — gate at `tests/resources/test_command_body.py:87`)
  to refresh the derived cache, then `bookwright graph query <SPARQL>` that selects
  anchors as the `crm:E13_Attribute_Assignment` nodes carrying `bw:promotes` and
  traverses the **anchor → finding → source** chain (`bw:promotes` then `bw:supportedBy`,
  reading `bw:claim` + the source provenance facets) — **not** a non-existent
  `bw:Anchor`/`bw:Source` class; embed research D5's verified reference query as the
  worked example (FR-005, research D4/D5); (ii) read `manuscript/`; (iii) hunt passages that **contradict** an
  anchor across the three § 20.6 kinds — **anachronisms, procedural errors (illegal or
  impossible in the setting), cultural/linguistic inaccuracies** (FR-006); (iv) branch
  on the two absent prerequisites (→ §7); (v) emit the report shape (→ §4). Reuse the
  `bw:` vocabulary only — add no class/predicate (Constitution X, contract C8).
- [X] T007 [US1] Author the **Archivos a leer** and **Archivos a escribir** sections:
  reads `manuscript/`, the graph (anchors + sources via `graph query`), and the
  `[research]` block of `manifest.toml` (to detect `enabled = false`); writes
  **Ninguno** with the explicit "solo lectura / no escribe nada" statement (FR-010,
  data-model E1 §5–§6; satisfies `test_report_only_states_no_writes`).
- [X] T008 [US1] Author the **Información faltante** section with both
  absent-prerequisite branches and **no** `[PENDING:]` marker (read-only): no
  manuscript → report the absent prerequisite, point to `bookwright-draft`; no anchors /
  `[research].enabled = false` → "nothing to verify", zero contradictions (FR-015,
  FR-016, research D7, contract C3).
- [X] T009 [US1] Author the **Qué NO hacer** section: no editing/correcting any file
  (FR-010); no re-auditing anchor *structural integrity* — defer to the `factual_anchor`
  validator (FR-012); no fetching/scraping/new deps (FR-014); no inventing
  contradictions to fill the report (US1 scenario 2, SC-003); no checking against the
  **bible** — that is `bookwright-continuity` (FR-013). (data-model E1 §8, contract C3/C8)
- [X] T010 [P] [US1] Add `"bookwright-verify"` to `REPORT_ONLY_COMMANDS` in
  `tests/resources/helpers.py` so `test_command_body.test_report_only_states_no_writes`
  asserts the "no escribe nada" guard for verify (research D2, data-model E4).
- [X] T011 [P] [US1] Extend the `test_graph_build_is_inline` parametrize in
  `tests/resources/test_command_body.py` to include `"bookwright-verify"` (the test
  already covers `bookwright-constitution` and `bookwright-continuity`, so verify is the
  **third** entry; the inline-build guard must cover it — research D4, plan Scale/Scope,
  contract C3).
- [X] T012 [US1] Run the US1 gates and confirm green:
  `uv run pytest tests/resources/test_command_body.py -q` (sections, report-only,
  inline-build) and `uv run ruff check && uv run ruff format --check && uv run mypy --strict`.

**Checkpoint**: The detection/read-only/prerequisite behaviour is fully authored and
the body+report-only+inline-build gates pass for `bookwright-verify`.

---

## Phase 4: User Story 2 — A structured, sourced, human-readable report (Priority: P2)

**Goal**: Author the **Output** section so every finding is navigable and provenanced:
grouped by chapter/scene; each finding carries the quoted passage, the violated anchor,
the anchor's source, a severity, and a `file:line` where known.

**Independent Test**: Run the skill on a manuscript with two distinct contradictions in
different scenes; confirm the report groups them by chapter/scene and each entry carries
the four required parts plus a `file:line` for any passage whose location is known
(spec US2 Independent Test, SC-004).

- [X] T013 [US2] Author the **Output** section in
  `src/bookwright/resources/commands/bookwright-verify.md` (data-model E2, FR-007/FR-008):
  human-readable prose (no JSON envelope, FR-009), grouped by **chapter/scene**; each
  finding = (a) quoted manuscript passage, (b) the violated anchor (its `bw:claim`),
  (c) the source behind it (reached via `bw:supportedBy`; `bw:reference`/`bw:author`/
  `bw:reliability`/`bw:originalQuote`) cited as the graph records it (incl.
  original-language refs), (d) a
  **severity** from `error`/`warning`/`info` (`error > warning > info`); plus a
  `file:line` where the location is known, else chapter/scene **without a fabricated
  line number**. State the severity rubric (hard anachronism / illegal-impossible
  procedure → `error`; soft cultural/stylistic nuance → `warning`/`info`; arguable →
  lower severity, not suppressed/overstated) and that a passage breaking N anchors lists
  all N. A clean manuscript yields **zero** findings, nothing fabricated.
- [X] T014 [US2] Review the authored **Output** section against data-model E2 (the
  four-part-finding + location table and severity rubric) and re-run
  `uv run pytest tests/resources/test_command_body.py -q` to confirm the body still
  satisfies the eight-section/language sweep with the Output content present.

**Checkpoint**: Report shape is authored and contract-conformant; US1 + US2 together
make the body complete.

---

## Phase 5: User Story 3 — Materialized in both integrations, post-draft, cost-free when unused (Priority: P3)

**Goal**: Wire the command into the inventory so the existing iteration-9 pipeline
materializes it into **both** integrations, with the description table and inventory
gates green.

**Independent Test**: Run `bookwright init` and confirm a valid `bookwright-verify`
`SKILL.md` is materialized under both `.claude/skills/` and `.agents/skills/`, each
passing `lint_skill_md`; confirm the description triggers on ES and EN prompts
(spec US3 Independent Test, SC-001/SC-006).

> Roster edits are in distinct files → `[P]`. `descriptions.py` is the production source;
> the three test rosters are expectations.

- [X] T015 [P] [US3] Add `"bookwright-verify": "<T003 description verbatim>"` to
  `SKILL_DESCRIPTIONS` in `src/bookwright/integrations/descriptions.py` — **byte-identical**
  to the source frontmatter (SC-009; gate
  `test_descriptions.test_v0_equality_gate_mirrors_source_frontmatter`), `< 1024` chars
  (`test_every_description_under_cap`). (research D2/D3, data-model E4, contract C5)
- [X] T016 [P] [US3] Add `"bookwright-verify"` to `EXPECTED_COMMANDS` in
  `tests/resources/helpers.py` so the inventory is exactly the 12 expected names
  (`test_command_frontmatter.test_exactly_the_expected_commands_exist`; research D2,
  contract C1). *(Same file as T010, different tuple — keep both additions.)*
- [X] T017 [P] [US3] Add `"bookwright-verify"` to `_ROSTER` in
  `tests/integrations/test_descriptions.py` (gates `test_all_roster_keys_present`,
  `test_get_description_returns_table_value_when_keyed`,
  `test_v0_equality_gate_mirrors_source_frontmatter`; research D2, contract C5).
- [X] T018 [P] [US3] Add `"bookwright-verify"` to `_ROSTER` in
  `tests/integrations/test_materialize.py` (gate
  `test_iter_command_sources_is_exactly_the_roster`; research D2, contract C4).
- [X] T019 [US3] Run the inventory/description/materialization gates and confirm green:
  `uv run pytest tests/resources/test_command_frontmatter.py tests/resources/test_command_activation.py tests/integrations/test_descriptions.py tests/integrations/test_materialize.py tests/integrations/test_setup_materialize.py -q`.
  Confirm the auto-derived rosters (`test_setup_materialize`, `test_e2e_materialize`)
  picked up the new command **without edits** (research D2 / plan "No-edit" note).
- [X] T020 [US3] Materialize via `bookwright init` in both integrations and inspect the
  output (quickstart §4, contract C4, SC-001): `uv run bookwright init demo-novel
  --integration claude` and `uv run bookwright init demo-generic --integration generic`;
  confirm `demo-novel/.claude/skills/bookwright-verify/SKILL.md` and
  `demo-generic/.agents/skills/bookwright-verify/SKILL.md` each exist, have
  `name: bookwright-verify` matching the parent dir, the default `Apache-2.0` license,
  `$ARGUMENTS` (not `{ARGS}`) and **no** residual `{…}` token, and pass `lint_skill_md`.

**Checkpoint**: All three stories complete; the command is admitted, described,
report-only, and materialized in both integrations.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-suite green, cross-artifact consistency, scope discipline, and the
behavioural acceptance the unit sweeps cannot cover.

- [X] T021 Run the full suite and all four CI gates green:
  `uv run pytest` (≥ 80 % single-sourced coverage gate, SC-008) and
  `uv run ruff check && uv run ruff format --check && uv run mypy --strict`.
- [X] T022 Run `/speckit-analyze` and confirm no cross-artifact inconsistency; verify
  **scope discipline** held — no `bookwright verify` CLI verb / verifier module / JSON
  envelope, no GOLEM class or predicate, no new integration, and **no** `docs/` edit or
  `tiny-historical/` fixture (those are iteration 17 — research D8, contract C8).
- [X] T023 Behavioural acceptance per quickstart §5 (manual/agent run): against a
  graph with a violating anchor → report names the anchor, quotes the passage, cites the
  source, assigns a severity (SC-002); against a consistent manuscript → zero
  contradictions (SC-003); no-manuscript and no-anchors/`enabled=false` → absent
  prerequisite, zero contradictions, no opaque failure (SC-007); triggers on the ES and
  EN prompts (SC-006); and the working tree is **unchanged** after the run (SC-005). Then
  remove the throwaway `demo-novel/` and `demo-generic/` projects from T020.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup. **Blocks all user stories** (the file
  and the canonical description must exist first).
- **US1 (Phase 3)**: depends on Foundational. The MVP and the only story that delivers
  standalone value.
- **US2 (Phase 4)**: depends on Foundational; in practice authored after US1 because it
  adds the **Output** section to the same file US1 is authoring (shared-file ordering,
  not a logical dependency).
- **US3 (Phase 5)**: depends on Foundational (the file must exist for the rosters to
  point at and for `init` to materialize). Its roster edits are independent of the body
  content, so US3 *could* proceed in parallel with US1/US2, but the gates in T019/T020
  only go green once the body sweeps (US1/US2) also pass.
- **Polish (Phase 6)**: depends on US1–US3 complete.

### Within each story

- US1/US2 body tasks edit one shared file → strictly sequential (T005→T006→T007→T008→
  T009, then T013); the test-wiring tasks T010/T011 are `[P]` (distinct files).
- US3 roster tasks T015/T016/T017/T018 are all `[P]` (four distinct files), then T019/T020.

### Parallel opportunities

- T010 ∥ T011 (helpers.py REPORT_ONLY vs test_command_body.py parametrize).
- T015 ∥ T016 ∥ T017 ∥ T018 (descriptions.py, helpers.py EXPECTED, two test `_ROSTER`s).
- Note: T010 and T016 both edit `tests/resources/helpers.py` (different tuples) — they
  are in different phases and run sequentially, so no conflict; do not lose either edit.

---

## Parallel Example: User Story 3 roster edits

```bash
# Four distinct files, no inter-dependency — apply together:
Task: 'Add "bookwright-verify" to SKILL_DESCRIPTIONS in src/bookwright/integrations/descriptions.py'
Task: 'Add "bookwright-verify" to EXPECTED_COMMANDS in tests/resources/helpers.py'
Task: 'Add "bookwright-verify" to _ROSTER in tests/integrations/test_descriptions.py'
Task: 'Add "bookwright-verify" to _ROSTER in tests/integrations/test_materialize.py'
```

---

## Implementation Strategy

### MVP first (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational (file skeleton + canonical description).
2. Phase 3 US1: author Rol/Input/Procedimiento/Archivos/Información faltante/Qué NO
   hacer + the two test-wiring edits; gates green.
3. **STOP and VALIDATE**: the body detects contradictions, is read-only, and never fails
   opaquely (the semantic half of § 20.6). This is the smallest shippable increment.

### Incremental delivery

1. Foundational → US1 (MVP) → validate.
2. US2 (Output section) → the report is navigable and provenanced → validate.
3. US3 (rosters + `init` materialization) → the skill ships in both integrations →
   validate.
4. Polish: full suite, `/speckit-analyze`, behavioural acceptance.

---

## Notes

- **No new test files, no new Python module, no CLI verb** — by design (research D1,
  contract C8). Any task that proposes one is out of scope and must be rejected.
- **No-edit sites** (do not touch): `integrations/materialize.py::iter_command_sources`,
  `tests/integrations/test_setup_materialize.py::_ROSTER`,
  `tests/commands/init/test_e2e_materialize.py::_ROSTER`, and the parametrized
  `command_files()` sweeps — all extend automatically.
- The single most error-prone step is **SC-009 byte-equality** (T003→T004→T015): draft
  the description once, paste verbatim, never re-type.
- Commit after each logical group; the `after_tasks` git hook offers a commit for this
  artifact.
