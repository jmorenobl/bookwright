# Feature Specification: `bookwright-verify` Skill (semantic verification vs. anchors)

**Feature Branch**: `015-bookwright-verify`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "Necesidad: tras escribir el borrador, el autor necesita saber si el texto contradice lo que investigó: anacronismos, errores de procedimiento (el detective hace algo ilegal o imposible en España), inexactitudes culturales o lingüísticas. Eso exige juicio, no solo código: lo resuelve un agente leyendo el manuscrito contra las anclas. […] Referencia: ver bookwright-design.md § 20.6 y el command bookwright-continuity como patrón análogo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify the manuscript against research anchors (Priority: P1)

An author who has finished drafting a historically-grounded novel needs to know
whether the prose contradicts what they researched: anachronisms, procedural
errors (the detective does something illegal or impossible in Spain), or cultural
and linguistic inaccuracies. This is a question of judgement, not code — it
requires an agent reading the manuscript *against the binding anchors*. The author
invokes `/bookwright-verify`. The skill guides the agent to load the project's
anchors from the graph (via `bookwright graph query`), read the manuscript, and
hunt for passages that contradict a researched fact. It produces a report — it
never edits the manuscript; the author decides what to fix.

**Why this priority**: This is the entire reason the iteration exists. It is the
**semantic** half of the two-layer verification design (§ 20.6): `factual_anchor`
(iteration 014, deterministic) checks that anchors are well-formed; this skill
checks whether the *text honours them*. It delivers value entirely on its own and
mirrors what `bookwright-continuity` is to the bible.

**Independent Test**: Run `bookwright init`, confirm a valid `bookwright-verify`
skill is materialized; then, in an agent, run the skill against a sample project
whose graph carries an anchor (e.g. "private detectives were not legally licensed
in Spain before 1957") and a manuscript scene that violates it (a 1950 scene with
a licensed PI). Confirm the agent loads the anchors via `bookwright graph query`,
reads the manuscript, and reports that passage as a contradiction — and that a
manuscript consistent with the anchors yields no contradiction for it.

**Acceptance Scenarios**:

1. **Given** a project whose graph contains anchors and a manuscript with a passage
   that contradicts one of them, **When** the author invokes `/bookwright-verify`,
   **Then** the skill instructs the agent to load anchors via `bookwright graph
   query` and to read `manuscript/`, and the agent reports the offending passage as
   a contradiction of that anchor.
2. **Given** a manuscript that is fully consistent with every anchor, **When**
   `/bookwright-verify` runs, **Then** the agent reports no contradictions (a clean
   verification), without inventing problems to "fill" the report.
3. **Given** the agent identifies a contradiction, **When** it writes the report,
   **Then** it makes no edit to `manuscript/` or `bible/` — the skill reports only;
   the author decides on the fix.
4. **Given** a project with no anchors (no `bible/research/`, or
   `[research].enabled = false`), **When** `/bookwright-verify` runs, **Then** the
   agent reports that there is nothing to verify (an absent prerequisite), not an
   opaque failure.
5. **Given** there is no manuscript yet, **When** `/bookwright-verify` runs, **Then**
   the agent reports the missing prerequisite and points the author to draft first,
   rather than failing opaquely.

---

### User Story 2 - A structured, sourced, human-readable report (Priority: P2)

The author needs the verification output to be *actionable*: organised by chapter
and scene, and for every flagged contradiction it must quote the offending
manuscript passage, name the anchor it violates, cite the **source** behind that
anchor (its provenance), and assign a **severity**. Where the underlying data
records a location, the report references the manuscript file and line so the
author can jump straight to the passage. The report is human-readable prose, not a
machine envelope.

**Why this priority**: A correct verification that the author cannot navigate is of
little use. The report structure is what turns "the text contradicts research" into
a list of concrete edits the author can triage. It rides just below the core
detection because it shapes how findings are presented rather than what is detected.

**Independent Test**: Run the skill on a manuscript with two distinct contradictions
in different scenes and confirm the report groups them by chapter/scene, and that
each entry carries the four required parts — the quoted passage, the violated
anchor, the anchor's source/provenance, and a severity — plus a `file:line`
reference for any passage whose location is known.

**Acceptance Scenarios**:

1. **Given** contradictions found in two different scenes, **When** the report is
   produced, **Then** it is organised by chapter/scene, each finding under the scene
   it occurs in.
2. **Given** a flagged passage, **When** it appears in the report, **Then** the entry
   quotes the passage, names the violated anchor, cites the anchor's source
   (provenance), and assigns a severity.
3. **Given** a flagged passage whose manuscript location is known, **When** it appears
   in the report, **Then** the entry references the manuscript **file and line**; when
   no precise location is available, the entry still identifies the scene/chapter
   without fabricating a line number.
4. **Given** contradictions of differing gravity (e.g. a hard anachronism vs. a soft
   cultural nuance), **When** the report assigns severities, **Then** more definite,
   factual contradictions are rated more severe than soft stylistic/cultural ones, so
   the author can triage.

---

### User Story 3 - Materialized in both integrations, post-draft, cost-free when unused (Priority: P3)

A project lead expects `bookwright-verify` to behave like the other commands: a
source command that materializes as an Agent Skill in **both** the `claude` and
`generic` integrations through the existing pipeline, triggerable from Spanish and
English prompts, positioned as a **post-draft** check (run after phase 5, Draft,
exactly like `bookwright-continuity`), and inert on projects that do no research.

**Why this priority**: Frictionless adoption and correct placement in the workflow
are required by the project's conventions, but they are properties of how the skill
plugs in rather than what it detects, so this lands last.

**Independent Test**: Run `bookwright init` and confirm a `bookwright-verify` skill
is materialized in both `.claude/skills/` and `.agents/skills/`, each passing the
`lint_skill_md` gate; confirm the skill's `description` triggers on both an ES
("verifica si mi manuscrito contradice lo investigado") and an EN ("check my
manuscript against my research") prompt; and confirm its body positions it as a
post-draft check distinct from `bookwright-continuity` (research anchors, not the
bible) and from `factual_anchor` (semantic judgement, not structural integrity).

**Acceptance Scenarios**:

1. **Given** a freshly `init`-ed project, **When** the skills are inspected, **Then**
   a valid `bookwright-verify` `SKILL.md` exists under both the `claude` and
   `generic` integrations, each passing skill validation.
2. **Given** the materialized skill, **When** its front-matter is linted, **Then** it
   satisfies agentskills.io limits (`name` < 64 chars matching its parent directory,
   `description` < 1024 chars, valid YAML).
3. **Given** an author prompt in Spanish or in English asking to verify the
   manuscript against the research, **When** the agent matches skills, **Then**
   `bookwright-verify` is a valid trigger for both.
4. **Given** the skill body, **When** read, **Then** it places the command in the
   post-draft phase (after Draft, like `bookwright-continuity`) and explicitly scopes
   itself to research anchors, deferring structural anchor integrity to the
   deterministic `factual_anchor` validator.

---

### Edge Cases

- **No manuscript yet**: nothing to verify; the skill reports an absent prerequisite
  and points to `bookwright-draft`, matching the `bookwright-continuity` "prerequisite
  ausente" pattern — it does not fail opaquely (US1 scenario 5).
- **No anchors / research disabled**: a project with no `bible/research/`, no promoted
  anchors, or `[research].enabled = false` has nothing to verify; the skill says so
  and produces no contradictions (US1 scenario 4).
- **Anchor with a foreign-language source**: the report cites the source's provenance
  as the graph records it (including the original-language reference), so the author
  can trace the basis of the contradiction even when the source is not in the book's
  language.
- **A passage contradicts more than one anchor**: each violated anchor is reported, so
  the author sees every researched fact the passage breaks.
- **An anchor with no contradicting passage**: not reported — the skill lists only
  passages that *clash* with an anchor, never every anchor.
- **Overlap with `factual_anchor` (iteration 014)**: this skill does **not** re-audit
  whether anchors are well-formed (sourced, reliable, non-dangling, anachronism-free
  in the graph); that is the deterministic validator's job. It assumes the anchors and
  reasons about whether the *prose* honours them.
- **Overlap with `bookwright-continuity`**: continuity checks the manuscript against
  the **bible** (character facts, arcs, timeline); verify checks it against **research
  anchors**. They are complementary post-draft passes, not duplicates.
- **A contradiction that is arguable, not definite**: the agent records it with a lower
  severity and the source it would clash with, rather than suppressing it or
  overstating it as a hard error.
- **Focus argument supplied** (e.g. a chapter or topic): the verification is narrowed
  to that focus, while the base remains the manuscript read against the anchors.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A new source command `bookwright-verify.md` MUST exist in the packaged
  `resources/commands/` directory, following the command-source format (design § 10.1)
  used by the existing commands (it is the v0.2 entry in the § 10.4 command list).
- **FR-002**: The command MUST be materialized as an Agent Skill (`SKILL.md`) for both
  the `claude` (`.claude/skills/`) and `generic` (`.agents/skills/`) integrations,
  **reusing the existing skill-materialization pipeline** (iteration 9); no parallel
  pipeline is introduced.
- **FR-003**: The generated `SKILL.md` MUST satisfy agentskills.io limits — `name`
  < 64 chars matching its parent directory, `description` < 1024 chars, valid YAML
  front-matter — i.e. pass the existing `lint_skill_md` gate.
- **FR-004**: The skill MUST be triggerable from both Spanish and English author
  prompts (e.g. "verifica si mi manuscrito contradice lo investigado" / "check my
  manuscript against my research").
- **FR-005**: The `SKILL.md` MUST instruct the agent to load the project's anchors
  (and the sources behind them) from the graph via `bookwright graph query` — the
  derived graph is the read surface, consistent with how `bookwright-continuity`
  consumes the graph.
- **FR-006**: The `SKILL.md` MUST instruct the agent to read the manuscript
  (`manuscript/`) and identify passages that **contradict** an anchor, across the
  contradiction kinds named by the design § 20.6: anachronisms, procedural errors
  (something illegal or impossible in the story's setting), and cultural or linguistic
  inaccuracies.
- **FR-007**: The produced report MUST be **structured by chapter/scene**, and each
  flagged contradiction MUST carry: (a) a quotation of the offending manuscript
  passage, (b) the **anchor** it violates, (c) the **source** behind that anchor (its
  provenance), and (d) a **severity**.
- **FR-008**: Where the manuscript location of a flagged passage is available, the
  report MUST reference the manuscript **file and line**; when no precise location is
  available it MUST still identify the chapter/scene without fabricating a line number.
- **FR-009**: The report MUST be **human-readable** prose. (This command is a
  read-only LLM check like `bookwright-continuity`; it is not an agent-consumed
  `--json` subcommand and adds no JSON envelope of its own.)
- **FR-010**: The skill MUST be **read-only**: it MUST NOT edit, correct, or write the
  manuscript, the bible, the research files, or any project file. It reports; the
  author decides. (Out of scope: auto-correction of the manuscript.)
- **FR-011**: The skill MUST position the command in the **post-draft** phase (run
  after phase 5, Draft), exactly like `bookwright-continuity`.
- **FR-012**: The skill MUST scope itself to **research anchors** and MUST NOT re-audit
  the *structural integrity* of anchors (sourcing, reliability, dangling targets,
  graph-level anachronism) — that is the deterministic `factual_anchor` validator
  (iteration 014). The two layers are complementary (§ 20.6); the skill assumes the
  anchors and judges whether the prose honours them.
- **FR-013**: The skill MUST be distinguishable from `bookwright-continuity`: verify
  checks the manuscript against **research anchors**, whereas continuity checks it
  against the **bible** (character facts, arcs, timeline). The skill body MUST make
  this boundary explicit so the agent invokes the right command.
- **FR-014**: The skill MUST NOT implement source fetching, bundle a search engine, or
  introduce any network or runtime dependency; the reasoning is performed by the agent
  reading the graph and the manuscript. The skill **instructs**; it does not fetch.
- **FR-015**: When there is **no manuscript** to verify, the skill MUST report it as an
  absent prerequisite (pointing to `bookwright-draft`) rather than failing opaquely,
  matching the `bookwright-continuity` pattern.
- **FR-016**: When there are **no anchors** to verify against (no research, no promoted
  anchors, or `[research].enabled = false`), the skill MUST report that there is
  nothing to verify and produce no contradictions.
- **FR-017**: `bookwright init` MUST scaffold a valid `bookwright-verify` skill in both
  integrations, alongside the existing commands, through the same materialization the
  other commands use (no special-casing).
- **FR-018**: When a focus argument is supplied (e.g. a chapter or topic), the skill
  MUST narrow the verification to that focus while keeping the manuscript-vs-anchors
  reading as its base.

### Key Entities *(include if feature involves data)*

- **`bookwright-verify` source command / skill**: the Markdown command source in
  `resources/commands/` and the `SKILL.md` it materializes into per integration.
  Carries the verification protocol, the report shape, and trigger phrasing (ES + EN).
- **Anchor** *(graph entity from iteration 012, not redefined here)*: the binding
  researched fact the manuscript is verified against; promotes a finding, constrains a
  narrative entity, and is backed by one or more sources. Loaded from the graph.
- **Source** *(graph entity from iteration 012)*: the provenance behind an anchor,
  cited in the report so the author can trace the basis of each contradiction.
- **Manuscript (`manuscript/cap-NN.md`)**: the drafted prose the skill reads and quotes
  from; the report references its file and line where the location is known.
- **Verification report**: the human-readable output — organised by chapter/scene, each
  contradiction carrying the quoted passage, violated anchor, anchor source, and
  severity. Emitted, never persisted to the project (read-only command).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `bookwright init` generates a `bookwright-verify` skill that passes skill
  validation (agentskills.io limits) in **both** the `claude` and `generic`
  integrations — 100 % of generated skills valid.
- **SC-002**: Running the skill in an agent against a project whose graph carries an
  anchor and a manuscript passage that violates it produces a report that (a) names the
  violated anchor, (b) quotes the offending passage, (c) cites the anchor's source, and
  (d) assigns a severity — verifiable on the produced report.
- **SC-003**: Against a manuscript fully consistent with its anchors, the skill reports
  **zero** contradictions — 0 false positives on a clean manuscript.
- **SC-004**: The report is organised by chapter/scene and references the manuscript
  file and line for every flagged passage whose location is known — verifiable on a
  report containing at least two findings in different scenes.
- **SC-005**: The skill performs **no** writes to the project on any run (read-only) —
  verifiable by confirming the working tree is unchanged after a verification run.
- **SC-006**: The skill triggers on both a Spanish and an English author prompt asking
  to verify the manuscript against the research — both phrasings match the skill.
- **SC-007**: On a project with no manuscript, and on a project with no anchors /
  `[research].enabled = false`, the skill reports the absent prerequisite and produces
  zero contradictions rather than failing — verifiable on both project states.
- **SC-008**: The full `pytest` suite passes the single-sourced project coverage gate
  (≥ 80 %, `fail_under = 80`; Constitution VIII); the Markdown command the iteration
  adds is data (materialized and lint-checked by the existing pipeline), not
  line-coverage-measured, and any wiring it touches is exercised by tests.

## Assumptions

- **Read surface is the derived graph plus the manuscript.** The skill instructs the
  agent to load anchors and their sources via `bookwright graph query` (SPARQL over the
  `bw:`/CIDOC triples iteration 012 emits) and to read `manuscript/` directly, exactly
  as `bookwright-continuity` consumes the graph and reads the manuscript. It does not
  re-parse `bible/research/` by hand, re-fetch sources, or call any external service.
- **Severity is the agent's judgement on a small, human-meaningful scale.** Definite,
  factual contradictions (a hard anachronism, an illegal/impossible procedure) are
  rated more severe than soft cultural or stylistic nuances. The exact label set is the
  skill author's choice (e.g. high/medium/low or error/warning/note); the requirement
  is that gravity is conveyed so the author can triage (FR-007, US2 scenario 4). The
  precise scale can be settled in `/speckit-clarify`.
- **Report is emitted, not persisted.** Like `bookwright-continuity`, this command is
  read-only and writes nothing to the project; the report is the agent's response
  (FR-009, FR-010). If a future iteration wants a persisted report artifact, that is
  out of scope here.
- **No new Python module is required.** Materialization, linting, and `init`
  scaffolding already iterate over every command source in `resources/commands/`
  (iteration 9), so adding `bookwright-verify.md` flows through the existing pipeline;
  the iteration is primarily a command-source (data) addition plus tests, with code
  changes only if wiring is found to need them.
- **Two-layer verification (§ 20.6).** `factual_anchor` (iteration 014, deterministic)
  audits anchor *integrity*; `bookwright-verify` (this iteration, semantic) audits
  whether the *prose honours* the anchors. The two are complementary and the skill does
  not duplicate the validator (FR-012).
- **Bilingual conventions.** The command/`SKILL.md` body and trigger phrasing are
  authored to fire on both Spanish and English prompts (user's bilingual convention);
  the design docs stay Spanish, the command body follows the precedent set by the other
  command sources.
- **Scope discipline (M4 / v0.2).** This iteration deliberately omits any auto-fix of
  the manuscript, any structural re-audit of anchors (that is iteration 014), and vector
  search (v0.3, design § 20.10). It adds no GOLEM ontology classes (Constitution X) and
  introduces no new integrations beyond `claude` / `generic` (Constitution V).

## Dependencies

- **Iteration 012 (research provenance model)**: the `Source` / `Finding` / `Anchor`
  graph entities and their `bw:` predicates — the anchors and sources this skill loads
  from the graph and cites. Must be on `main`.
- **Iteration 013 (research skill + `[research]` block)**: the `[research].enabled`
  switch that makes verification inert on non-research projects, and the
  `bible/research/` content that produces anchors. Must be on `main`.
- **Iteration 014 (`factual_anchor` validator)**: the deterministic structural-integrity
  layer this skill is the semantic complement to (§ 20.6); the boundary between them is
  defined here. Must be on `main`.
- **Iterations 008 & 009 (source commands + skill materialization)**: the command-source
  format and the `SKILL.md` materialization / `lint_skill_md` pipeline reused here.
- **Iteration 006 (graph indexer)**: `bookwright graph build` / `bookwright graph query`
  — the derived graph the skill queries for anchors and sources.
- **`bookwright-continuity` (iteration 008)**: the analogous read-only post-draft report
  command this skill is modelled on (design § 20.6, § 10.4).
