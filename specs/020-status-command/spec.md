# Feature Specification: Derived project status and next actions

**Feature Branch**: `020-status-command`

**Created**: 2026-06-11

**Status**: Draft

**Input**: User description: "Necesidad: el autor (y cada skill) necesita saber, sin re-derivarlo a mano, en qué estado está el proyecto y qué conviene hacer a continuación. Toda esa información ya existe estructuralmente en el grafo y en los validators; falta un comando que la agregue de forma determinista y proponga el siguiente paso. Por ejemplo, las anclas sin fuentes suficientes SON la cola de investigación; hoy nadie la consume. `bookwright status` computa el estado derivado del proyecto a partir del grafo, reporta HECHOS (fase, foco, preguntas abiertas, anclas sin fuente, hallazgos de baja fiabilidad, resumen de validación) y computa next_actions con una tabla de reglas estática. Determinista, sin LLM, sin red. Referencia: bookwright-design.md § 21.4–21.6, § 13, § 20. Principios I, IX, X."

## Overview

A Bookwright project already contains everything needed to know *where the
work stands*: the knowledge graph holds open research questions and anchors,
the validators detect continuity problems, and the manifest records the
project phase and the author's focus (iteration 019). But today nobody
aggregates that information — the author (or a skill) must re-derive it by
hand, and structurally meaningful queues like "anchors without sufficient
sources" go unconsumed.

This iteration adds `bookwright status`: a **deterministic** CLI verb that
computes the project's derived state from the graph (rebuilt from the corpus
on every run via the same pipeline `graph build` uses — recomputation is the
freshness mechanism), reports the resulting facts, and maps
them through a **static rule table** to a list of recommended next actions —
each one naming a skill to invoke, a paste-ready prompt, and a brief reason.
It is pure aggregation over the frozen ontology (no new classes, Principle X),
emits the standard single-document JSON envelope with `--json`
(Principle IX), and caches its report as a derived, reconstructible artifact
(Principle I). Skill consumption of this command is deferred to iterations
021–022.

## Clarifications

### Session 2026-06-11

- Q: In the `--json` report, what should the `state` object carry for the research/validation facts — counts only (as the design § 21.6 example shows) or also the items? → A: Counts + item lists — `state` carries both the aggregate counts and the identifying items (open question texts/IDs, anchor IDs, low-reliability finding IDs); the design's count-only example is a minimal illustration. Iteration 021's bottom-up consumption needs the actual queue without re-querying the graph.
- Q: What language do the paste-ready prompt templates in `next_actions` use? → A: Fixed English — one static template set, matching the CLI/code language convention (the design § 21.5 Spanish examples are illustrative). Skills must trigger on both ES and EN prompts anyway; no i18n machinery.
- Q: What does `status` do when the graph rebuild fails because a source file is malformed (vs. nothing to build)? → A: Hard error — the standard unified error envelope and non-zero exit, exactly as `graph build` / `validate` on the same corpus. Graceful degradation (FR-013) is reserved for *absent* information, never *corrupt* information.
- Q: How does `status` resolve graph staleness, given that `validate` has no staleness detection (it loads `graph.ttl` as-is) and only `graph build` rebuilds? → A: Unconditional rebuild — `status` always reconstructs the graph from the corpus by reusing the `graph build` pipeline (extracted to a shared helper) and refreshes the derived `graph.ttl` cache; recomputation is the freshness mechanism (plan research.md D1, owner-approved 2026-06-11).
- Q: How can repeated runs be byte-identical (SC-002) when `Finding`/`Anchor` mint fresh uuid7 URIs on every rebuild? → A: The report never contains minted URIs — items are identified by corpus-stable keys (authored finding `id`s, file relpaths, claim texts), carried by an additive extension of the research mapping result; anchor-gap detection reuses the `factual_anchor` predicates extracted as pure functions (plan research.md D2/D3, owner-approved 2026-06-11).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the project's derived state at a glance (Priority: P1)

As an author returning to my project, I want one command that tells me where
the project stands — its phase, my recorded focus, the open research
questions, the anchors lacking sufficient sources, the findings below my
reliability threshold, and a summary of validation problems — without
re-deriving any of it by hand.

**Why this priority**: The facts are the foundation of the feature. Without
the derived state there is nothing to recommend actions from, nothing to
cache, and nothing for skills to consume later. It is the minimum viable
slice and already delivers standalone value.

**Independent Test**: In a project with a bible, research findings (some
open, some below the reliability threshold), anchors, and at least one
validation problem, run `bookwright status` and confirm the report shows the
project phase, the focus echo, the count and identification of open research
questions, anchors without sufficient sources, low-reliability findings, and
validation counts per severity — all matching what `graph query` and
`validate` would independently reveal.

**Acceptance Scenarios**:

1. **Given** a project with research findings marked open, **When** the
   author runs `bookwright status`, **Then** the report lists those open
   research questions as facts (the "bottom-up" research queue).
2. **Given** a project whose graph cache is stale relative to the bible and
   research sources, **When** the author runs `bookwright status`, **Then**
   the graph is rebuilt from the corpus first (the `graph build` pipeline,
   run unconditionally) and the reported facts reflect the current corpus.
3. **Given** a project with anchors whose findings lack sufficient supporting
   sources, **When** the author runs `status`, **Then** those anchors are
   reported, reusing the same detection logic as the existing
   `factual_anchor` validator (no divergent re-implementation).
4. **Given** a project with findings whose reliability is below the
   manifest's `research.min_reliability_for_anchor`, **When** the author runs
   `status`, **Then** those findings are reported as a distinct fact.
5. **Given** a project where validators report problems, **When** the author
   runs `status`, **Then** the report includes a validation summary with
   counts per severity, consistent with what `bookwright validate` reports.
6. **Given** a project with a `[focus]` block and a manifest `status` field,
   **When** the author runs `status`, **Then** the report echoes the focus
   (target, notes, last-updated date) and the project phase.

---

### User Story 2 - Get deterministic next-action recommendations (Priority: P2)

As an author (and, in later iterations, a skill), I want the status report to
end with concrete recommended next steps — which skill or command to invoke,
with a prompt I can paste as-is, and a one-line reason — derived purely from
the reported facts by a fixed rule table.

**Why this priority**: This is the "what should I do next" half of the
feature's purpose, but it depends entirely on the facts of US1 existing
first. It turns the report from a diagnosis into a usable thread.

**Independent Test**: Construct a known derived state (e.g., 3 open research
questions, no focus defined) and confirm the rule table produces exactly the
expected actions, in the same order, every time — testable as a pure
state-to-actions function with no graph or project on disk.

**Acceptance Scenarios**:

1. **Given** a state with N unresolved anchors / open research questions,
   **When** next actions are computed, **Then** they include a
   `bookwright-research` recommendation whose prompt lists those questions
   and whose reason cites the count.
2. **Given** a state with findings below the reliability threshold, **When**
   next actions are computed, **Then** they include a `bookwright-verify`
   recommendation.
3. **Given** a state with continuity violations, **When** next actions are
   computed, **Then** they include a recommendation to review the bible.
4. **Given** a state with no focus defined, **When** next actions are
   computed, **Then** they include a recommendation to run
   `bookwright focus set`.
5. **Given** the same state presented twice, **When** next actions are
   computed both times, **Then** the resulting action lists are identical,
   byte for byte, in content and order.

---

### User Story 3 - Consume the report as machine-readable JSON (Priority: P3)

As tooling (and, in iterations 021–022, the skills), I want
`bookwright status --json` to emit exactly one JSON success document on
stdout — focus, state facts, and next actions — and I want the same report
persisted to a derived cache file so it can be inspected without re-running
the command.

**Why this priority**: The JSON contract and the cache are what make the
feature consumable by agents, but a human author already gets full value from
US1+US2 without them.

**Independent Test**: Run `bookwright status --json` and confirm stdout
contains a single JSON document of the form
`{"status":"ok","focus":…,"state":…,"next_actions":[…]}` and nothing else,
that any human prose went to stderr, and that
`.bookwright/cache/status.json` now contains the same report.

**Acceptance Scenarios**:

1. **Given** any project, **When** the author runs `status --json`, **Then**
   stdout carries exactly one JSON document with top-level keys `status`
   (value `"ok"`), `focus`, `state`, and `next_actions`, and nothing else on
   stdout.
2. **Given** any successful run (with or without `--json`), **When** the
   command completes, **Then** `.bookwright/cache/status.json` has been
   regenerated with the computed report.
3. **Given** a failure (e.g., not a Bookwright project), **When** the author
   runs `status --json`, **Then** the unified error envelope of iteration 018
   is emitted, consistent with every other agent-facing command.
4. **Given** an unchanged corpus, **When** `status --json` is run twice,
   **Then** the two stdout documents and the two cache files are
   byte-identical.

---

### Edge Cases

- **No graph and nothing to build it from**: in a project where there is
  nothing to build the graph from (e.g., no bible content), `status` does
  not fail — it reports the facts it can (phase, focus echo) and emits
  either no next actions or a single bootstrap action (e.g., "build the
  graph" / "define a focus").
- **Graph rebuild fails on malformed sources**: a corpus that `graph build`
  / `validate` would reject (e.g., broken front-matter) makes `status` fail
  the same way — standard error reporting, unified `--json` error envelope,
  non-zero exit. Corrupt information is an error; only *absent* information
  degrades gracefully.
- **v0.2-era project**: a project with no `[focus]` block and no
  `bible/research/` directory runs `status` successfully; missing areas are
  reported as absent/empty, never as errors.
- **No focus defined**: `focus` is reported as null/absent (consistent with
  `focus show`), and the rule table contributes the "define a focus"
  recommendation.
- **Nothing to recommend**: a healthy project (no open questions, no
  violations, focus defined) yields an empty `next_actions` list — an empty
  list is a valid, meaningful answer.
- **Stale graph cache**: `status` rebuilds the graph from the corpus on every
  run (and refreshes the derived `graph.ttl`), so it never reports facts from
  a stale graph.
- **Cache directory missing**: `.bookwright/cache/` is created if absent;
  the scaffold's `.gitignore` already excludes it (no project file changes
  needed).
- **Stale or corrupt previous `status.json`**: irrelevant — the cache is
  write-only output for this command, regenerated on every run, and never
  read as input.
- **Not a Bookwright project**: `status` fails with the same clear
  "not a project" error other manifest-reading commands produce, using the
  unified error envelope under `--json`.
- **Determinism boundary**: the report contains no run timestamps, no random
  identifiers, and no environment-dependent data; only facts derived from
  the corpus (the focus echo's `updated_at` comes from the manifest, not
  from the clock).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST provide a `bookwright status` command that
  computes the project's derived state from the knowledge graph, rebuilding
  the graph from the corpus on every run by reusing the `graph build`
  pipeline (single shared implementation, no fork) and refreshing the
  derived `graph.ttl` cache, so the facts always reflect the current
  corpus (see Clarifications: recomputation is the freshness mechanism).
- **FR-002**: `status` MUST be exclusively read-only aggregation over the
  frozen ontology: it MUST NOT add classes or properties to the ontology
  (Principle X), MUST NOT mutate the graph beyond the existing
  rebuild-the-derived-cache behavior, and MUST NOT modify the manifest,
  bible, research, or manuscript files.
- **FR-003**: The report MUST include the project phase (the manifest's
  `status` field) and an echo of the authored focus (`[focus]` block from
  iteration 019), with the focus reported as null/absent when no block
  exists.
- **FR-004**: The report MUST include the open research questions: the
  findings marked open in the graph (the bottom-up research queue,
  design § 20.3).
- **FR-005**: The report MUST include the anchors lacking sufficient
  supporting sources or with unresolvable targets, reusing the detection
  logic of the existing `factual_anchor` validator (iteration 015) rather
  than duplicating it.
- **FR-006**: The report MUST include the findings whose reliability is
  below the manifest's `research.min_reliability_for_anchor` threshold
  (design § 20.9).
- **FR-007**: The report MUST include a validation summary with problem
  counts per severity, obtained by reusing the existing validation runner
  (iteration 010/011) — not by re-implementing validator logic.
- **FR-008**: `status` MUST compute `next_actions` via a static rule table:
  a pure, deterministic mapping from state predicates to recommended
  actions, where each action carries the skill or command to invoke, a
  paste-ready prompt (a fixed English template parameterized only by state
  facts), and a brief reason. Given the same state it MUST
  always produce the same actions, and it MUST be unit-testable without a
  graph or a project on disk.
- **FR-009**: The rule table MUST cover at least these mappings: unresolved
  anchors / open research questions → recommend `bookwright-research` with a
  prompt listing them; findings below the reliability threshold → recommend
  `bookwright-verify`; continuity violations → recommend reviewing the
  bible; no focus defined → recommend `bookwright focus set`.
- **FR-010**: The order of `next_actions` MUST be stable and fully
  determined by the state (e.g., by fixed rule priority, then a fixed key),
  so that repeated runs produce byte-identical output.
- **FR-011**: With `--json`, `status` MUST emit exactly one JSON success
  document on stdout and only that document, of the shape
  `{"status":"ok","focus":…,"state":…,"next_actions":[{"skill":…,"prompt":…,"reason":…},…]}`,
  with human prose going to stderr (Principle IX). Without `--json`, a
  readable human report goes to stdout. Failures use the unified `--json`
  error envelope (iteration 018).
- **FR-011a**: For each research/validation fact, the `state` object MUST
  carry both the aggregate count and the identifying items themselves (open
  question texts/identifiers, anchor identifiers, low-reliability finding
  identifiers), so consumers can act on the queue without re-querying the
  graph. Item lists MUST be deterministically ordered (FR-010/FR-014).
  Identifiers MUST be corpus-stable (authored ids, file paths, claim texts)
  — never minted entity URIs, which change on every rebuild (see
  Clarifications).
- **FR-012**: Every successful run MUST regenerate the computed report at
  `.bookwright/cache/status.json`. This cache is a derived, reconstructible
  artifact — never read back as a source of truth, and excluded from
  version control (the project scaffold's `.gitignore` already covers
  `.bookwright/cache/`).
- **FR-013**: `status` MUST degrade gracefully when information is *absent*:
  with nothing to build the graph from, no research content, or no focus, it
  MUST report the facts it can compute, leave `next_actions` empty or with a
  single bootstrap action (e.g., "build the graph" / "define a focus"), and
  exit successfully. A v0.2-era project with no `[focus]` block and no
  `bible/research/` MUST NOT fail. Graceful degradation does NOT extend to
  *corrupt* information: a graph rebuild failure on malformed sources MUST
  fail with the project's standard error reporting (unified error envelope,
  non-zero exit), exactly as `graph build` / `validate` would on the same
  corpus.
- **FR-014**: The computation MUST be fully deterministic: the same input
  corpus MUST yield byte-identical facts and `next_actions`, with no LLM
  calls, no network access, and no run-dependent data (timestamps, random
  values, environment details) in the report.
- **FR-015**: A successful `status` run MUST exit with code 0 even when the
  reported state contains problems (open questions, violations): `status`
  is a report, not a quality gate. Errors in computing the report itself
  (e.g., not a project) MUST fail with the project's standard error
  reporting.

### Key Entities *(include if feature involves data)*

- **Status report**: the full derived snapshot of a project at a point in
  the corpus's history. Composed of the focus echo, the state facts, and
  the recommended next actions. Serialized as the `--json` document and as
  the cache file; both are derived artifacts.
- **State facts**: the deterministic observations aggregated from existing
  sources — project phase, open research questions, anchors without
  sufficient sources, findings below the reliability threshold, and
  validation counts per severity. Each research/validation fact carries both
  its aggregate count and the identifying items (see Clarifications). Facts
  only; no judgment.
- **Next action**: one recommendation produced by the rule table. Attributes:
  the **skill** (or CLI command) to invoke, a **prompt** ready to paste
  without editing, and a **reason** briefly justifying the recommendation
  (e.g., citing the triggering count). Ordered deterministically.
- **Rule table**: the static, exhaustive mapping from state predicates to
  next actions. Fixed at design time, pure (state in, actions out), and
  unit-testable in isolation.
- **Status cache** (`.bookwright/cache/status.json`): the persisted copy of
  the latest report. Regenerated on every run; write-only output, never an
  input.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An author (or agent) can learn the project's phase, focus,
  research queue, reliability gaps, and validation health — and what to do
  next — from a single command invocation, with zero manual queries against
  the graph or validators.
- **SC-002**: Two consecutive runs over an unchanged corpus produce
  byte-identical stdout (`--json`) and byte-identical cache files, in 100%
  of cases.
- **SC-003**: Every fact in the report agrees with the tool that owns it:
  validation counts match `bookwright validate`, anchor gaps match the
  `factual_anchor` validator, and the focus echo matches `focus show`, in
  100% of cases.
- **SC-004**: 100% of emitted next actions include all three components —
  a skill/command, a paste-ready prompt, and a reason.
- **SC-005**: The rule table is verifiable in isolation: for every rule, a
  synthetic state exercises it and yields the expected actions without a
  graph or project on disk.
- **SC-006**: A v0.2-era project (no `[focus]`, no `bible/research/`) runs
  `status` to successful completion in 100% of cases, reporting what exists
  and recommending at most a single bootstrap action.
- **SC-007**: Running `status` never modifies any source file: the corpus
  (manifest, bible, research, manuscript) is byte-identical before and
  after, with only derived caches (`graph.ttl`, `status.json`) changing.

## Assumptions

- **Exit semantics**: `status` is a report, not a gate — it exits 0 whenever
  the report is computed, regardless of how unhealthy the reported state is
  (FR-015). Gating remains `bookwright validate`'s job.
- **Reliability threshold source**: the threshold for "low-reliability
  findings" is the existing `research.min_reliability_for_anchor` manifest
  knob (default `media`); no new configuration is introduced.
- **Prompt templates** (resolved — see Clarifications): the prompts in
  `next_actions` are fixed static **English** templates parameterized only by
  state facts (counts, identifiers); exact wording is settled at planning
  time. Determinism only requires that they are fixed.
- **Cache freshness model**: the status cache is regenerated on *every* run
  rather than invalidated on demand — the command is cheap enough that
  recomputation is the freshness mechanism, mirroring how `graph.ttl` is a
  rebuildable cache.
- **`.gitignore` coverage**: the project scaffold already excludes
  `.bookwright/cache/`, so no scaffold change is required for the new cache
  file.
- **Graph staleness resolution** (resolved — see Clarifications): `validate`
  has no staleness detection (it loads the on-disk `graph.ttl` as-is), so
  there is no existing mechanism to reuse; `status` rebuilds unconditionally
  via the shared `graph build` pipeline instead of defining new staleness
  machinery.

## Out of Scope

- **Skills consuming this command** (start-up context injection, "next
  steps" sections in `SKILL.md`) — deferred to iterations 021–022.
- **Any judgment or "intelligent" prioritization** beyond the static rule
  table — weighing actions, nuanced phrasing, and executing research live in
  the skills, not in the CLI.
- **New ontology classes or properties** (Principle X) — `status` only
  queries the frozen schema.
- **Mutating the graph or the manuscript** — the only writes are the
  existing derived-graph refresh and the new derived status cache.
- **An append-only history/journal of status snapshots** — only the latest
  report is cached.
- **Vector search** (v0.4) — `status` neither requires nor anticipates it.

## Dependencies

- The knowledge graph build pipeline of `bookwright graph build`
  (iteration 006; design § 13), extracted to a helper shared by both verbs.
- The validation runner and its severity model (iterations 010–011), and
  the `factual_anchor` validator (iteration 015) — both reused, not
  duplicated.
- The research provenance model and vocabulary — open findings, anchor
  support/constraint edges, reliability levels (iterations 012–014;
  design § 20).
- The `[focus]` manifest block and `focus show` semantics (iteration 019).
- The unified `--json` success/error envelope (iteration 018; Principle IX).
