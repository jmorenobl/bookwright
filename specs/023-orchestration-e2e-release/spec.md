# Feature Specification: Orchestration loop fixture, E2E flow, docs, and v0.3.0 release

**Feature Branch**: `023-orchestration-e2e-release`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "Necesidad: antes de release v0.3.0 necesitamos una fixture que ejercite el bucle de orquestación, tests E2E del flujo foco→status→siguiente paso, y documentación del nuevo sistema."

## Overview

This is the closing iteration of milestone **M5 / v0.3.0** — context
orchestration (design § 21). The mechanism is already built and merged across
the prior iterations: authored focus (the `[focus]` manifest block +
`bookwright focus show|set|clear`, iteration 019), `bookwright status` (the
deterministic derived-state engine + `next_actions`, iteration 020), the
`bookwright-research` skill consuming open questions / unsourced anchors
(iteration 021), and the whole skill suite reading `status` at start and
emitting a "Próximos pasos" block (iteration 022).

What is missing before the release can ship is **proof and explanation**: a
worked example that gives `bookwright status` something concrete to report and
recommend, an automated regression that walks the orchestration loop
(focus → status → resolve → status) and asserts the *deterministic* `status`
output shrinks by exactly one action, a non-regression guarantee that a project
which never opts into orchestration behaves exactly as before, and a
documentation set that teaches the "hilo conductor" model. This iteration is
consolidation and validation — it adds **no new product mechanism** (no new
CLI verb, no new manifest field, no validator or skill behavior change).

This follows the precedent of iterations 12 (the `tiny-historical` fixture) and
17 (consolidation/non-regression), and especially iteration 16 (the M4 closing
iteration: realistic fixture + E2E flow + docs + release).

## Clarifications

### Session 2026-06-13

- Q: How should the orchestration fixture be created (dedicated new fixture vs. extend an existing one)? → A: Extend `tiny-historical` — it already carries research/anchor scaffolding (including an under-sourced anchor `status` surfaces); add a populated `[focus]` block and one open research question. Additions stay additive and inert to the M4 `factual_anchor` exact-count test (FR-006), and the loop's resolve step mutates only a `tmp_path` copy, never the committed fixture.
- Q: How should the "resolve one open item" step be materialized in the E2E test? → A: An overlay file — the fixture ships an extra pre-baked research file the test copies into `bible/research/` (on the `tmp_path` copy) to supply the answering Finding, closing exactly one **open question**. No LLM step; additive; the resolved next action is the open-question action.
- Q: Does this iteration bump the package version to 0.3.0, or only add the CHANGELOG entry? → A: Bump the package version to 0.3.0 **and** add the CHANGELOG v0.3.0 entry, leaving the milestone "release ready" (matching the iteration 011/016 release-prep precedent). Actually tagging/publishing the release remains a separate manual step (Out of Scope).
- Q: The merged `status` engine aggregates `next_actions` per rule-category (one `research_queue` action bundles **all** open questions **and** all anchor gaps), so the action list cannot shrink when one open question is resolved while any other open question or anchor gap remains. How is the loop's "progress" guarantee made real and faithful? → A: **Replace the "next_actions length N → N−1" assertion with a deterministic *state-convergence* assertion.** The engine recommends *workstreams* (skills), not per-item entries: `research_queue` keeps firing while any open question OR anchor gap remains, and the extended `tiny-historical` permanently carries the `el-almacen-viejo` under-reliable anchor (which FR-006 forbids removing, since the M4 test pins `factual_anchor` at `{error:1, warning:1}`). The E2E therefore asserts that the resolved open question leaves `state.open_questions` (count K → K−1) and the `research_queue` action's prompt, while **every other `state` fact and every other action is byte-for-byte identical** across the two runs, and the whole asserted output is deterministic across repeated runs. (Rejected: forcing a literal action-count drop would require either a redundant second fixture or mutating the committed `tiny-historical` anchor set — both worse for quality/technical-debt.)
- Q: `tiny-historical` already declares open questions in `_index.md`, and "closing" one is not expressible by pure file-addition — how is the resolve step materialized? → A: The pre-baked resolution is applied to the `tmp_path` **copy** as a deterministic two-part edit: (1) author the answering finding (a real finding with a `claim` and sufficiently-reliable `sources`) in a new `bible/research/` topic file, and (2) drop the resolved question's id from `_index.md`'s `open_questions` on the copy. No LLM step; the committed fixture stays pristine; exactly one open question closes. FR-005's "overlay file" is generalized to this "pre-baked resolution applied to the working copy".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A worked example the orchestration loop can reason over (Priority: P1)

A novelist (or a maintainer evaluating Bookwright) needs to *see* the
orchestration loop working on something realistic: a project with an authored
focus and genuine open work, so that `bookwright status` has something concrete
to report (facts) and recommend (`next_actions`). They open a packaged example
whose `manifest.toml` carries a filled-in `[focus]` block and whose
`bible/research/` holds at least one open research question and at least one
anchor without sufficiently-reliable support — exactly the derived-state inputs
that drive `status`'s `open_questions`, `unresolved_anchors`, and
`low_reliability_findings`, and therefore its recommended next actions.

**Why this priority**: Everything else in this iteration consumes this fixture —
the E2E test runs against it and the documentation references it. Without a
coherent example that produces a non-empty, *deterministic* `status` report
there is nothing to test or teach, so it is the foundational deliverable.

**Independent Test**: The fixture can be initialized/loaded as a valid
Bookwright project; `bookwright status` against it succeeds (exit 0) and emits a
report with a defined focus, a built graph, and a non-empty `next_actions` list
— verifiable as a standalone demonstration before any test or doc is written.

**Acceptance Scenarios**:

1. **Given** the orchestration example project, **When** a reader inspects its
   `manifest.toml`, **Then** it contains a fully-populated `[focus]` block (a
   target and the fields `bookwright focus set` records).
2. **Given** the same project, **When** `bookwright graph build` runs, **Then**
   the build succeeds and the research entities (Findings, Anchors) are emitted
   into the derived graph alongside the narrative entities.
3. **Given** the built project, **When** `bookwright status --json` runs,
   **Then** it exits 0 and reports a defined focus, an available graph, at least
   one open question and/or one unresolved/under-sourced anchor, and a non-empty
   `next_actions` list whose entries each name a skill, a reason, and a prompt.

---

### User Story 2 - The orchestration loop proven end to end (Priority: P1)

A maintainer preparing the release needs confidence that the loop
focus → status → resolve → status actually composes on a real project and stays
true as the code evolves. An automated regression walks the example through the
loop: initialize the project, set focus, build the graph, run `status` and
assert its deterministic facts and `next_actions`; then apply a **pre-baked
resolution** for exactly one open question (content authored into the fixture,
so no LLM judgment is exercised), rebuild, run `status` again, and assert the
report now shows progress — the resolved question gone from `state.open_questions`
and from the `research_queue` prompt, with **every other state fact and action
byte-for-byte unchanged**. All assertions are on the deterministic `status`
output (facts and `next_actions`); the LLM/judgment steps the loop normally
involves are represented by the fixed pre-baked content, never invoked.

**Why this priority**: A worked example that isn't guarded by a test rots
silently. This regression is what lets the team claim "the orchestration loop
works" at release and keep claiming it; it is co-equal P1 with the fixture it
depends on.

**Independent Test**: Running the workflow test against the fixture exercises
init → focus set → build → status → resolve → status and asserts the resolved
open question deterministically leaves `state.open_questions` and the
`research_queue` prompt while everything else is byte-for-byte unchanged,
delivering a green-or-red signal on the whole deterministic loop in one run.

**Acceptance Scenarios**:

1. **Given** the example project initialized in a working copy, **When**
   `bookwright focus set` is run with the fixture's focus, **Then** the
   `[focus]` block is recorded and a subsequent `status` reports
   `focus` as defined.
2. **Given** the project after `graph build`, **When** `status --json` runs,
   **Then** the test can assert specific deterministic facts (focus defined,
   graph available with entity/triple counts present, the expected
   open-question / anchor-gap / low-reliability-finding items) and the exact,
   enumerated `next_actions` set the fixture's state produces (each entry
   carrying a skill, a reason, and a prompt), recorded in a co-located oracle
   rather than hard-coded.
3. **Given** the first `status`, **When** the pre-baked resolution for exactly
   one open question is applied to the working copy and the graph is rebuilt,
   **Then** a second `status --json` shows that one open question resolved: the
   resolved question is absent from `state.open_questions` (count K → K − 1) and
   from the `research_queue` action's prompt, while every other `state` fact and
   every other `next_actions` entry is **byte-for-byte identical** to the first
   run. (The `next_actions` *list length* is unchanged: `research_queue` still
   fires for the remaining open question / anchor gap — the engine recommends
   workstreams, not per-item entries.)
4. **Given** both `status` runs, **When** their JSON documents are compared,
   **Then** every asserted field is byte-for-byte deterministic across repeated
   runs (no timestamps or minted-URI / ordering nondeterminism in the asserted
   fields).

---

### User Story 3 - The system is inert when orchestration is unused (Priority: P2)

An author who never opts into orchestration — no `[focus]` block and no
`bible/research/` directory — must be able to run the project exactly as before
the orchestration system existed. `bookwright status` must still succeed,
degrading gracefully to a "nothing here yet / nothing to recommend" report, and
`build`/`validate` must behave identically to a pre-M5 project. Orchestration
imposes zero cost, zero new required files, and zero behavioral change on
projects that never use it.

**Why this priority**: This is the non-regression guarantee for the existing
user base and the milestone's core promise (design § 21: the thread is opt-in
and inert when unused). It is high-value but ranks just below the
worked-example/E2E pair because it guards existing behavior rather than
demonstrating the new one.

**Independent Test**: Running `status`, `build`, and `validate` against an
existing focus-free, research-free fixture (e.g. `tiny-novel`) yields a
successful, unchanged result — `status` exits 0 with `focus` undefined and an
empty `next_actions`, and `build`/`validate` match pre-M5 behavior — provable on
its own.

**Acceptance Scenarios**:

1. **Given** a project with no `[focus]` block and no `bible/research/`
   directory, **When** `bookwright status --json` runs, **Then** it exits 0 and
   reports `focus` as undefined, no open questions / unresolved anchors /
   low-reliability findings, and an empty `next_actions` list — no error or
   warning about the missing focus or research.
2. **Given** the same project, **When** `build` and `validate` run, **Then**
   their outcomes are unchanged from pre-M5 behavior (no new required inputs, no
   altered exit behavior, no orchestration-related output).
3. **Given** a project whose corpus prerequisites are absent (no bible to build
   from), **When** `status` runs, **Then** it degrades to a successful exit-0
   report stating the graph is unavailable, rather than failing.

---

### User Story 4 - The orchestration system is documented for release (Priority: P2)

A reader of the documentation site needs to understand the orchestration system
well enough to use it: the "hilo conductor" model that distinguishes **authored
focus** (what the author declares) from **derived state** (what `status`
computes from the corpus) from **judgment** (the LLM steps the skills perform);
what `bookwright status` reports and how `next_actions` are derived; the work
loop (focus → status → act → repeat); and how the skills consume `status` at
start. The command reference must cover `bookwright status` and
`bookwright focus`, and the changelog must record the v0.3.0 release.

**Why this priority**: A shipped system nobody can learn is half-shipped, but the
mechanism and its tests must exist first; documentation is the final layer over a
proven system, hence P2 alongside inertness.

**Independent Test**: Building the documentation site produces a navigable
orchestration page, complete command-reference coverage for `status`/`focus`,
and a v0.3.0 changelog entry, with no build warnings — verifiable by building the
docs (`mkdocs build --strict`) and reading them.

**Acceptance Scenarios**:

1. **Given** the documentation site, **When** a reader opens the orchestration
   page (`orchestration.md`), **Then** it explains the three-layer model
   (authored focus vs derived state vs judgment), `bookwright status` and how
   `next_actions` are derived, the work loop, and how the skills use `status`;
   and it is reachable from the site navigation.
2. **Given** the command reference, **When** a reader looks for the new CLI
   surface, **Then** `bookwright status` and the `bookwright focus`
   sub-commands are documented there and accurate against the live CLI.
3. **Given** the changelog, **When** a reader looks for the latest release,
   **Then** there is a v0.3.0 entry describing the context-orchestration system
   (consolidating iterations 019–023).
4. **Given** the documentation sources, **When** the site is built with the
   project's strict settings, **Then** the build completes with no warnings.

---

### Edge Cases

- **A fixture that is both "realistic/coherent" and produces an *exact*,
  unambiguous open state.** The example must read as a genuine documented
  project while the set of open questions, anchor gaps, and low-reliability
  findings it produces is exactly what the test asserts — so the test asserts
  exact `state` facts and the exact `next_actions` set, not lower bounds. The
  open state must be unambiguous under the fixture's own
  `min_reliability_for_anchor`.
- **Resolving exactly one open question must change exactly one `state` fact.**
  The pre-baked resolution must close precisely one open question without
  incidentally closing or opening any other open question, anchor gap, or
  low-reliability finding, and without changing the focus, validation counts, or
  narrative facts the other actions depend on — so that exactly one item leaves
  `state.open_questions` and the `research_queue` prompt while everything else is
  byte-identical. (The `next_actions` *list length* does not change: the engine
  aggregates per workstream, so `research_queue` keeps firing while any open
  question or anchor gap remains.)
- **The resolution is pre-baked content, not an LLM step.** The "resolve an open
  question" step is materialized by fixed content shipped beside the fixture and
  applied by the test to the working copy (a pre-authored answering-Finding file
  copied into `bible/research/` **plus** dropping the resolved id from
  `_index.md`'s `open_questions`); no agent/LLM judgment runs in CI. The
  assertions are only on the deterministic `status` output.
- **Inert: absent vs present-but-empty.** A project with no `[focus]` and no
  `bible/research/` must yield an empty `next_actions`; a project with a bible
  but no research must also yield no research-derived actions. Both are inert,
  successful exits — not errors.
- **`status` over an unbuildable corpus.** When build prerequisites are absent,
  `status` degrades to a successful "graph unavailable" report (it must not be
  asserted to fail); a genuinely corrupt corpus fails exactly as `graph build`
  would, per the existing `status` fault model.
- **Mutating a packaged fixture in tests.** The loop's resolve step mutates the
  project; the test must operate on a `tmp_path` copy so the committed fixture
  stays pristine and the run is repeatable.

## Requirements *(mandatory)*

### Functional Requirements

**Fixture**

- **FR-001**: The orchestration example fixture MUST be created by **extending
  the existing `tiny-historical` fixture** (under `tests/fixtures/`): a short,
  coherent narrative that is a valid Bookwright project (initializable/loadable,
  with the standard bible/outline/manuscript skeleton). The extension reuses
  `tiny-historical`'s existing research/anchor scaffolding and adds only the
  orchestration inputs (FR-002, FR-003) plus the pre-baked resolution (FR-005).
- **FR-002**: The fixture's `manifest.toml` MUST contain a fully-populated
  `[focus]` block — a focus target plus the fields `bookwright focus set`
  records — so `status` reports a defined focus.
- **FR-003**: The fixture MUST contain open work that `status` surfaces as
  derived state, so `status` produces a non-empty `next_actions`: at least one
  **open research question** (a Finding flagged open in `_index.md` —
  `tiny-historical` already declares two; this iteration MUST pin the exact set,
  not assume it adds the only one) and at least one **anchor without
  sufficiently-reliable support** (the existing `el-almacen-viejo` under-reliable
  anchor) under the fixture's own configured `min_reliability_for_anchor`. The
  open question and the under-reliable anchor both feed the single aggregating
  `research_queue` rule; the existing under-reliable anchor is **permanent**
  (FR-006 forbids removing it), so `research_queue` fires throughout the loop.
- **FR-004**: The fixture's open state MUST be **exact and unambiguous**: the set
  of open questions, anchor gaps, and low-reliability findings it produces MUST
  be exactly enumerable (recorded in a co-located oracle, per the
  `tiny-historical/expected-findings.md` precedent), so the test asserts the
  precise `state` facts and the precise `next_actions` set rather than lower
  bounds, and no other unexpected open items appear.
- **FR-005**: The fixture MUST ship a **pre-baked resolution** (no LLM step) that
  the test applies to the `tmp_path` working copy as a deterministic two-part
  edit: (1) a pre-authored research file supplying the **answering Finding** (a
  real finding with a `claim` and sufficiently-reliable `sources`), copied into
  `bible/research/`, and (2) dropping the resolved question's id from
  `_index.md`'s `open_questions` on the copy. Rebuilding the graph afterward MUST
  close precisely the one targeted **open question**, and no other item, leaving
  the focus, the under-reliable anchor, the low-reliability finding, the
  validation counts, and every remaining open question unchanged. The pre-baked
  resolution material MUST live beside the fixture and MUST NOT be present in the
  corpus the first `status` reads.
- **FR-006**: Any new fixture or fixture extension MUST NOT break the existing
  fixtures' tests; in particular it MUST NOT alter the exact-count assertions of
  the M4 research workflow test (if `tiny-historical` is extended rather than a
  new fixture authored, the extension must be additive and inert to those
  assertions).

**E2E tests**

- **FR-007**: An automated end-to-end test (`test_orchestration_workflow.py`)
  MUST walk the orchestration loop against the fixture (on a `tmp_path` copy):
  initialize/load the project, run `bookwright focus set`, run
  `bookwright graph build`, run `bookwright status`, apply the pre-baked
  resolution for one open item, rebuild, and run `bookwright status` again.
- **FR-008**: The test MUST assert the **first** `status` reports deterministic
  facts — focus defined, graph available (entity/triple counts present), and the
  expected open question(s) / anchor gap(s) / low-reliability finding(s) — and
  the exact, enumerated `next_actions` set (each entry carrying a skill, a
  reason, and a prompt), with the expected counts/identifiers sourced from the
  co-located oracle (FR-004), not hard-coded.
- **FR-009**: The test MUST assert the **second** `status` shows deterministic
  progress: the resolved open question is absent from `state.open_questions`
  (count K → K − 1) and from the `research_queue` action's prompt, while **every
  other `state` fact and every other `next_actions` entry is byte-for-byte
  identical** to the first run. The `next_actions` list length is unchanged
  because `research_queue` still fires for the remaining open question / anchor
  gap; asserting a shorter list would contradict the merged engine's
  per-category aggregation and is explicitly NOT required.
- **FR-010**: All E2E assertions MUST be on the **deterministic** `status` output
  (the JSON facts and `next_actions`); the test MUST NOT depend on any LLM /
  judgment step — those are represented by the fixture's pre-baked content.
- **FR-011**: An automated test MUST prove **inertness** for a project with no
  `[focus]` block and no `bible/research/` (reusing an existing focus-free,
  research-free fixture such as `tiny-novel`): `bookwright status` exits 0 with
  `focus` undefined and an empty `next_actions`, and `build`/`validate` behave
  identically to pre-M5 behavior. No new permanent fixture is authored for this
  case.
- **FR-012**: The inertness test MUST also cover the **degraded** path: a project
  whose build prerequisites are absent yields a successful exit-0 `status` report
  stating the graph is unavailable, not a failure.

**Documentation & release**

- **FR-013**: The documentation site MUST gain an orchestration page
  (`docs/orchestration.md`) covering: the "hilo conductor" three-layer model
  (authored focus vs derived state vs judgment); `bookwright status` and how
  `next_actions` are derived; the work loop (focus → status → act → repeat); and
  how the skills consume `status` at start.
- **FR-014**: The orchestration page MUST be reachable from the documentation
  site navigation.
- **FR-015**: The command reference MUST document `bookwright status` and the
  `bookwright focus` sub-commands (`set`/`show`/`clear`), accurate against the
  live CLI; where these reference pages already exist they MUST be verified and
  brought current for the release rather than duplicated.
- **FR-016**: The changelog MUST gain a v0.3.0 entry describing the
  context-orchestration system, consolidating iterations 019–023.
- **FR-022**: The package version MUST be bumped to `0.3.0` (the single
  authoritative version source), leaving the milestone "release ready". Actually
  tagging/publishing the release is a separate manual step (Out of Scope).

**Quality gates**

- **FR-017**: The full test suite MUST keep overall coverage above the project
  threshold (≥ 80 %), which remains the **single enforced** gate (one source, no
  drift — see CLAUDE.md / Constitution VIII). New M5 code being covered above
  85 % is a **verified-at-review** quality target — measured and reported, but
  NOT a second enforced per-package `fail_under` in CI.
- **FR-018**: Lint (`ruff check`), format (`ruff format --check`), type-check
  (`mypy --strict`), pre-commit, and CI MUST all pass.
- **FR-019**: The documentation site MUST build with no warnings
  (`mkdocs build` under the existing `strict: true` setting).
- **FR-020**: This iteration MUST introduce no new product mechanism: no new CLI
  verb, manifest field, validator, or skill behavior change — only a fixture,
  tests, documentation, and the release entry.
- **FR-021**: The fixture and tests MUST NOT introduce vector search (v0.4) or
  export (v1.0) or any other post-v0.3 mechanism.

### Key Entities *(include if data involved)*

- **Orchestration example fixture**: The **extended `tiny-historical`** project —
  its existing research/anchor scaffolding plus a filled `[focus]` block, giving
  a deliberately open state (its declared open questions, the existing
  `el-almacen-viejo` under-reliable anchor, and the `rumor-incendio`
  low-reliability finding) with an exact, oracle-recorded enumeration. The
  shared input for the E2E test and the documentation.
- **Pre-baked resolution**: Fixed, pre-authored content shipped beside the
  fixture — an answering-Finding research file (with a `claim` and reliable
  `sources`) the test copies into `bible/research/` on the working copy, plus the
  `_index.md` edit dropping the resolved question's id — closing exactly the one
  open question. The deterministic stand-in for the LLM "resolve a question"
  step.
- **Orchestration workflow test**: The automated regression
  (`test_orchestration_workflow.py`) walking focus → status → resolve → status
  and asserting the resolved open question leaves `state.open_questions` and the
  `research_queue` prompt while everything else stays byte-identical, plus the
  inertness/degraded assertions for focus-free, research-free, and unbuildable
  projects.
- **`status` report**: The deterministic `{status, focus, state, next_actions}`
  document the test asserts on — `state` carrying focus-defined, graph facts,
  open questions, unresolved anchors, low-reliability findings, and validation;
  `next_actions` carrying `{skill, reason, prompt}` entries.
- **Orchestration documentation set**: The new `docs/orchestration.md` page, the
  verified `status`/`focus` command reference, and the v0.3.0 changelog entry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can open the orchestration fixture and run
  `bookwright status` on it to get a successful report with a defined focus, a
  built graph, and a non-empty `next_actions` list — a standalone demonstration
  of the loop having something concrete to recommend.
- **SC-002**: The orchestration E2E test passes, asserting the deterministic
  outcomes: the first `status` reports the expected facts and the exact
  enumerated `next_actions` set (each with skill/reason/prompt); after the
  pre-baked resolution of one open question the second `status` shows the
  resolved question gone from `state.open_questions` (K → K − 1) and from the
  `research_queue` prompt, with every other state fact and action byte-for-byte
  unchanged.
- **SC-003**: Running `status`/`build`/`validate` on a focus-free, research-free
  project produces results identical to pre-M5 behavior — `status` exits 0 with
  no focus and an empty `next_actions`; the unbuildable-corpus case degrades to a
  successful "graph unavailable" report rather than failing.
- **SC-004**: A reader can reach the orchestration page from the site navigation
  and it covers the three-layer model, `status`/`next_actions`, the work loop,
  and skill consumption; `bookwright status` and `bookwright focus` are
  documented in the command reference; the changelog has a v0.3.0 entry; and the
  package version reads `0.3.0`.
- **SC-005**: Overall test coverage stays ≥ 80 % (the single enforced CI gate)
  and new M5 code is ≥ 85 % (report-only, verified at review — not a second CI
  gate; see FR-017).
- **SC-006**: Lint, format, strict type-check, pre-commit, and CI are green, and
  the documentation site builds with zero warnings.
- **SC-007**: No vector-search, export, or other post-v0.3 capability is
  introduced by this iteration, and no new product mechanism is added.

## Assumptions

- This is plan iteration 023 (spec directory `023`), the final iteration of
  M5 / v0.3.0. It assumes iterations 019–022 (authored focus, `bookwright
  status`, `bookwright-research` consuming open items, skills reading `status`)
  are already merged on `main`. This iteration adds fixtures, tests, and docs —
  not new `src/` mechanism.
- "E2E" here means the deterministic CLI stages (focus set → build → status →
  resolve → status) are automated; the LLM/judgment steps the loop normally
  involves are represented by fixed pre-baked fixture content and are NOT invoked
  in CI. The assertions are on the deterministic `status` JSON output only.
- The fixture follows the existing `tests/fixtures/tiny-*` conventions
  (short-but-coherent, Spanish narrative prose, English identifiers/structure)
  and the existing E2E test conventions (`tests/e2e/`, fixtures-as-input,
  `tmp_path` where a project is mutated). Per the Session 2026-06-13
  clarification, the fixture is the **extended `tiny-historical`** (not a new
  fixture); FR-006's non-regression constraint against the M4 research-workflow
  test holds.
- The "resolve an open question" step is materialized as **pre-baked content
  applied to the `tmp_path` copy**: an answering-Finding research file copied
  into `bible/research/` plus dropping the resolved id from `_index.md`'s
  `open_questions`, so exactly one open question closes — mirroring iteration
  16's fixture-as-input + `tmp_path`-copy approach. No LLM judgment runs in CI.
- The merged `bookwright status` engine (iteration 020) recommends *workstreams*
  per rule-category, not per open item: a single `research_queue` action bundles
  all open questions **and** all anchor gaps, so `len(next_actions)` is the count
  of applicable rule categories, never the count of open items. Progress from
  resolving one open question therefore shows in the deterministic `state` facts
  and the action's prompt, not in the list length — which is what the E2E test
  asserts. This is the engine's intended contract, not a workaround.
- `docs/commands/status.md` and `docs/commands/focus-*.md` already exist (added
  in iterations 019–020) and are wired into the mkdocs nav; FR-015 is therefore
  verify-and-finalize for those pages, while `docs/orchestration.md` is genuinely
  new (a top-level page like `research.md`, not under the CLI-gated
  `docs/commands/` directory).
- Documentation prose (the orchestration page, narrative parts of the changelog)
  is written in Spanish to match the existing docs site and design documents;
  identifiers and command names stay as-is.
- "New M5 code" for the ≥ 85 % coverage target refers to the source added across
  M5 (focus, `status`, status-consuming skill plumbing) as it stands at release,
  measured by the existing coverage tooling; this iteration mostly adds
  fixtures/tests/docs rather than new `src/` code.

## Out of Scope

- Vector search over the corpus (ChromaDB / semantic retrieval) — that is v0.4.
- Export to EPUB / PDF / print — that is v1.0.
- Any new product mechanism: this iteration adds a fixture, tests, and docs only;
  it changes no CLI verb, manifest field, validator, or skill behavior.
- Automating any LLM/judgment step in CI; those remain represented by the
  fixture's pre-baked content. The deterministic `status` output is what the
  test asserts.
- Actually publishing/tagging the v0.3.0 release (this iteration makes it
  *ready*; the release/tag action itself is a separate step).
