# Feature Specification: v0.4 close — narrative-structure E2E fixture, workflow test, docs, honest deferrals, and the v0.4.0 release

**Feature Branch**: `032-v04-close`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Necesidad: la capa estructural narrativa está cableada (G9/G10/G7), tipada (Propp/Greimas) y validada. Falta cerrar el hito v0.4 como se cerraron M4 (v0.2.0) y M5 (v0.3.0): una fixture E2E que demuestre el flujo de punta a punta, un workflow test, docs actualizadas, dejar el contrato de diferidos honesto, y la release."

## Overview

This is the **closing iteration of milestone v0.4** — the narrative-structure
layer (Propp/Greimas: G7/G9/G10) plus `outline/units/` ingestion that closes
ingestion parity. The mechanism is already built and merged across the prior
iterations: `outline/units/*.md` ingestion into `G9_Narrative_Unit` +
`G10_Narrative_Function` entities and `G7_Narrative_Sequence` assembly
(iterations 028–029), the Propp/Greimas vocabularies as `crm:E55_Type` with
`crm:P2_has_type` typing of functions (G10) and roles (G11) when a vocabulary is
active (iteration 030), and the `narrative_structure` continuity validator
(iteration 031, the first consumer of the layer).

What is missing before the release can ship is **proof, explanation, an honest
deferral contract, and the release metadata** — exactly the shape of the M4
closing iteration 016 (`v0.2.0`) and the M5 closing iteration 023 (`v0.3.0`):

1. A **worked E2E fixture** with a populated `outline/units/` (units carrying
   `functions`, `roles`, `sequence`/`order`) and **Propp active**, that exercises
   the full flow ingest → `graph build` → `validate` and lets a reader *see* the
   narrative entities, their cross-refs, their `E55_Type` typings, and the
   `narrative_structure` validator findings appear as expected.
2. An automated **workflow test** that walks the authored path against the
   fixture, analogous to M4's `test_research_workflow.py` and M5's
   `test_orchestration_workflow.py`, asserting the deterministic outcomes.
3. **Documentation** (docs site + README), in Spanish per the docs language
   convention, covering `outline/units/` ingestion, a unit's frontmatter, the
   activation of Propp/Greimas, and the new validator.
4. An **honest deferral registry**: with G7/G9/G10 now wired, the only remaining
   deferred concepts are **G6 (RelationshipRole)** and **G3
   (PsychologicalState)**, whose `target_version` must be re-pointed away from the
   now-shipping `"v0.4"` to a concrete later version label (the deferral contract
   forbids a placeholder; the exact label is resolved in `/speckit-clarify`). The
   ingestion-parity test stays green.
5. The **v0.4.0 release** metadata: bump `__version__` to `0.4.0` (single
   source), a CHANGELOG `v0.4.0` section consolidating iterations 028–032
   (including a "Design decisions revised during implementation" subsection if any
   apply), and `CLAUDE.md` / `bookwright-design.md` brought current where the code
   diverged from them.

This iteration is **consolidation, validation, documentation, and release** — it
adds **no new product mechanism** (no new CLI verb, manifest field, validator, or
skill behavior, and no ontology change). It explicitly does **not** wire G6/G3.

## Clarifications

### Session 2026-06-21

- Q: G6 (RelationshipRole) and G3 (PsychologicalState) currently carry
  `target_version="v0.4"`, which is the version this iteration ships. The
  deferral contract requires a **concrete** version label, never a placeholder,
  yet the roadmap (§ 4) places their natural home in the "demand-pulled horizon
  *without an assigned version*". To what concrete label should their
  `target_version` be re-pointed? → A: [NEEDS CLARIFICATION: concrete post-v0.4
  version label for the G6/G3 re-target — e.g. `"v0.5"`, `"v1.0"`, or another
  firm label. The roadmap's demand-pulled horizon has no assigned version, but
  the deferral contract (and its parity test) require a concrete string, so a
  label must be chosen here rather than left as a placeholder.]

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A worked example that exercises the narrative-structure layer end to end (Priority: P1)

A novelist (or a maintainer evaluating Bookwright) needs to *see* the v0.4
narrative-structure layer working on something realistic: a project whose
`outline/units/` describes narrative beats with Propp functions, character
roles, and an ordered sequence, with a Propp vocabulary active — so that
`bookwright graph build` produces the structural entities (G9 units, G10
functions, G7 sequence), their cross-refs (role resolution, sequence membership),
and their `E55_Type` typings, and `bookwright validate` then reports the
`narrative_structure` findings (an orphan beat and an unresolved role).

**Why this priority**: Everything else in this iteration consumes this fixture —
the workflow test runs against it and the documentation references it. Without a
coherent example that produces deterministic structural entities, typings, and
validator findings, there is nothing to test or teach, so it is the foundational
deliverable.

**Independent Test**: The fixture can be loaded as a valid Bookwright project;
`bookwright graph build` against it succeeds (exit 0) and the derived graph
contains the expected G9/G10/G7 entities with their `E55_Type` typings;
`bookwright validate` succeeds and emits the expected `narrative_structure`
warnings — verifiable as a standalone demonstration before any test or doc is
written.

**Acceptance Scenarios**:

1. **Given** the v0.4 example project, **When** a reader inspects its
   `outline/units/`, **Then** it contains unit cards carrying `functions`,
   `roles`, and `sequence`/`order` keys, and its `manifest.toml` has a
   `[vocabularies]` block with Propp active.
2. **Given** the same project, **When** `bookwright graph build` runs, **Then**
   the build succeeds and the derived graph carries the `G9_Narrative_Unit`,
   `G10_Narrative_Function`, and `G7_Narrative_Sequence` entities, the sequence's
   ordered membership (`dlp:proper-part`), the resolved character-role cross-refs,
   and the `crm:P2_has_type` → `crm:E55_Type` typings for functions (and roles)
   that the active Propp vocabulary supplies.
3. **Given** the built project, **When** `bookwright validate --json` runs,
   **Then** it succeeds and reports the `narrative_structure` validator's expected
   findings — at least one orphan beat (a G9 unit in no G7 sequence) and at least
   one unresolved role — each as a `warning` with a `file:line` source.

---

### User Story 2 - The v0.4 flow proven end to end by an automated workflow test (Priority: P1)

A maintainer preparing the release needs confidence that the authored path
ingest → `graph build` → `validate` actually composes on a real project and stays
true as the code evolves. An automated workflow test (analogous to M4's
`test_research_workflow.py` and M5's `test_orchestration_workflow.py`) walks the
example through the flow on a `tmp_path` copy and asserts the deterministic
outcomes: the narrative entities and their cross-refs are present in the graph,
their `E55_Type` typings appear, and the `narrative_structure` validator findings
match a co-located oracle. It also asserts the non-regression guarantee — with no
vocabulary active, no `E55_Type` typings are emitted and the rest of the flow is
unchanged.

**Why this priority**: A worked example that isn't guarded by a test rots
silently. This regression is what lets the team claim "the v0.4 narrative layer
works" at release and keep claiming it; it is co-equal P1 with the fixture it
depends on.

**Independent Test**: Running the workflow test against the fixture exercises
build → validate and asserts the expected G9/G10/G7 entities, cross-refs,
`E55_Type` typings, and the exact `narrative_structure` findings (sourced from a
co-located oracle), delivering a green-or-red signal on the whole deterministic
flow in one run.

**Acceptance Scenarios**:

1. **Given** the example project initialized in a working copy, **When**
   `bookwright graph build` runs, **Then** the test can assert specific
   deterministic facts: the expected count of G9 units, G10 functions, and the G7
   sequence with its ordered members; the resolved role cross-refs; and the
   `crm:P2_has_type`/`crm:E55_Type` typings supplied by the active Propp
   vocabulary — with expected counts/identifiers sourced from a co-located oracle,
   not hard-coded.
2. **Given** the built project, **When** `bookwright validate --json` runs,
   **Then** the test asserts the exact, enumerated `narrative_structure` findings
   (the orphan beat(s) and unresolved role(s), each with validator name, `warning`
   severity, and a `file:line` source), sourced from the oracle.
3. **Given** the same fixture but with the `[vocabularies] active` list emptied
   (or a no-vocabulary variant), **When** `graph build` runs, **Then** no
   `crm:P2_has_type`/`crm:E55_Type` typings are emitted and every other graph fact
   is unchanged — proving vocabulary activation is the only thing that adds the
   typings (zero regression when inactive).
4. **Given** repeated runs of build → validate, **When** the asserted JSON/graph
   facts are compared, **Then** every asserted field is byte-for-byte
   deterministic (no timestamps or minted-URI / ordering nondeterminism in the
   asserted fields).

---

### User Story 3 - The v0.4 layer is documented for release (Priority: P2)

A reader of the documentation needs to understand the narrative-structure layer
well enough to use it: how `outline/units/` is ingested, the frontmatter of a
unit card (`functions`, `roles`, `sequence`/`order`), how to activate Propp /
Greimas via the `[vocabularies]` block, and what the new `narrative_structure`
validator checks. The README and the docs site must cover this, in Spanish (the
docs language convention), and the changelog must record the `v0.4.0` release.

**Why this priority**: A shipped system nobody can learn is half-shipped, but the
mechanism and its tests must exist first; documentation is the final layer over a
proven system, hence P2.

**Independent Test**: Building the documentation site produces a navigable
narrative-structure page covering ingestion, unit frontmatter, vocabulary
activation, and the validator, plus a `v0.4.0` changelog entry, with no build
warnings — verifiable by building the docs (`mkdocs build` under strict) and
reading them.

**Acceptance Scenarios**:

1. **Given** the documentation site, **When** a reader opens the
   narrative-structure documentation, **Then** it explains (in Spanish) the
   ingestion of `outline/units/`, a unit's frontmatter keys
   (`functions`/`roles`/`sequence`/`order`), the activation of Propp/Greimas via
   `[vocabularies] active`, and the `narrative_structure` validator's two rules;
   and it is reachable from the site navigation.
2. **Given** the README, **When** a reader scans the feature list / project
   surface, **Then** it reflects the v0.4 narrative-structure layer.
3. **Given** the changelog, **When** a reader looks for the latest release,
   **Then** there is a `v0.4.0` entry describing the narrative-structure layer
   (consolidating iterations 028–032), including a "Design decisions revised
   during implementation" subsection if any design divergences were recorded.
4. **Given** the documentation sources, **When** the site is built with the
   project's strict settings, **Then** the build completes with no warnings.

---

### User Story 4 - The deferral registry is left honest (Priority: P2)

A maintainer reading `deferrals.py` must find a truthful contract: now that
G7/G9/G10 are wired, the **only** deferred concepts are G6 (RelationshipRole) and
G3 (PsychologicalState), and their `target_version` no longer points at the
just-shipped `"v0.4"`. The value is re-pointed to a concrete later label (the
contract forbids a placeholder), and the ingestion-parity test — which asserts the
orphan set derived from a real build equals exactly the deferred set — stays
green.

**Why this priority**: A dishonest deferral contract (claiming work targets a
version that already shipped) is exactly the silent debt the registry exists to
prevent; correcting it is part of closing the milestone, but it depends on the
wiring (028–031) already being merged, hence P2.

**Independent Test**: `deferrals.py` lists exactly `{RelationshipRole,
PsychologicalState}` with a concrete post-v0.4 `target_version`, and
`tests/golem/test_ingestion_parity.py` passes (the orphan set from a live build
equals the deferred set) — provable by running that test.

**Acceptance Scenarios**:

1. **Given** `deferrals.py`, **When** a maintainer reads `DEFERRED_CONCEPTS`,
   **Then** it contains exactly two entries (`RelationshipRole`,
   `PsychologicalState`), each with a concrete `target_version` that is **not**
   `"v0.4"` and is **not** a placeholder.
2. **Given** the re-targeted registry, **When** `tests/golem/test_ingestion_parity.py`
   runs against a real graph build, **Then** the orphan set it derives equals
   exactly the keys of `DEFERRED_CONCEPTS` and the test passes.
3. **Given** the `DeferralNote` docstring (which today cites `"v0.4"` as the
   example label), **When** a maintainer reads it after this iteration, **Then**
   any example/explanatory text is consistent with the new concrete label and the
   fact that v0.4 has shipped.

---

### User Story 5 - The v0.4.0 release metadata is in place (Priority: P2)

A maintainer cutting the release needs the version single-sourced and the release
record complete: `__version__` reads `0.4.0`, the CHANGELOG carries a `v0.4.0`
section, and the living documents (`CLAUDE.md`, `bookwright-design.md`) are
current where the implemented code diverged from them. Actually tagging/publishing
the release (merge to `main`, annotated tag) remains the separate manual step the
`bookwright-release` skill drives.

**Why this priority**: The release record is the last layer over a proven,
documented, honestly-deferred milestone; it depends on all the above being done,
hence P2.

**Independent Test**: `bookwright version` (and `__version__`) reports `0.4.0`;
the CHANGELOG has a `v0.4.0` section; `CLAUDE.md` and `bookwright-design.md`
reflect the shipped v0.4 state — verifiable by inspection and by the version gate.

**Acceptance Scenarios**:

1. **Given** the package, **When** `__version__` (single source) is read, **Then**
   it is `0.4.0`, and `bookwright version` reports the same.
2. **Given** the CHANGELOG, **When** a reader looks for the latest release,
   **Then** there is a `v0.4.0` section consolidating iterations 028–032 (with a
   "Design decisions revised during implementation" subsection if applicable).
3. **Given** `CLAUDE.md` and `bookwright-design.md`, **When** a maintainer reviews
   them post-iteration, **Then** the milestone prose / status table and any design
   sections where the code diverged are brought current for the shipped v0.4.

---

### Edge Cases

- **A fixture that is both realistic and produces an *exact*, unambiguous set of
  validator findings.** The example must read as a genuine outline while the set
  of orphan beats and unresolved roles it produces is exactly what the test
  asserts — so the test asserts the exact `narrative_structure` findings (recorded
  in a co-located oracle), not lower bounds. The orphan beat must be a genuine G9
  unit in no G7 sequence; the unresolved role must name a slug resolving to no
  character role.
- **`E55_Type` typings appear only when a vocabulary is active.** With Propp
  active the function/role typings are present; with `[vocabularies] active`
  empty they must be entirely absent and every other graph fact unchanged — the
  non-regression guarantee from iteration 030.
- **Mutating a packaged fixture in tests.** The flow rebuilds `bible/graph.ttl`;
  the test must operate on a `tmp_path` copy so the committed fixture stays
  pristine and the run is repeatable.
- **The re-targeted deferral label must keep the parity test green.** Re-pointing
  G6/G3's `target_version` must not change the *set* of deferred keys — only the
  version string — so the parity test (which reconciles keys against the live
  orphan set) stays green; the orphan set is `{RelationshipRole,
  PsychologicalState}` because G7/G9/G10 are now fed.
- **Greimas as well as Propp.** Activation is documented for both vocabularies;
  the fixture activates Propp (the functions vocabulary). The documentation must
  still explain Greimas (actant) activation even though the worked fixture leads
  with Propp.

## Requirements *(mandatory)*

### Functional Requirements

**Fixture**

- **FR-001**: A v0.4 narrative-structure example fixture (under
  `tests/fixtures/`) MUST be provided that is a valid, loadable Bibliowright
  project with the standard bible/outline/manuscript skeleton plus a populated
  `outline/units/`. It MUST be source-only (the derived `bible/graph.ttl` is
  rebuilt in a `tmp_path` copy, never committed).
- **FR-002**: The fixture's `outline/units/` MUST contain unit cards exercising
  the full v0.4 frontmatter: `functions` (Propp functions), `roles` (character
  role references), and `sequence`/`order` keys assembling at least one
  `G7_Narrative_Sequence` with ordered members.
- **FR-003**: The fixture's `manifest.toml` MUST declare a `[vocabularies]` block
  with **Propp active**, so `graph build` emits the `crm:P2_has_type` →
  `crm:E55_Type` typings for narrative functions (and character roles where
  applicable).
- **FR-004**: The fixture MUST deliberately produce the `narrative_structure`
  validator's two findings: at least one **orphan beat** (a G9 unit belonging to
  no G7 sequence) and at least one **unresolved role** (a unit `roles:` reference
  resolving to no character role).
- **FR-005**: The fixture's outcome MUST be **exact and unambiguous**: the set of
  narrative entities, cross-refs, `E55_Type` typings, and `narrative_structure`
  findings it produces MUST be exactly enumerable, recorded in a co-located oracle
  (per the `tiny-historical/expected-findings.md` / `expected-status.md`
  precedent), so the test asserts precise facts rather than lower bounds.
- **FR-006**: Any new fixture MUST NOT break existing fixtures' tests; in
  particular it MUST NOT alter the `parity-exercise`-driven
  `test_ingestion_parity.py` assertions or the M4/M5 fixture oracles.

**Workflow / E2E test**

- **FR-007**: An automated end-to-end workflow test (under `tests/e2e/`,
  analogous to `test_research_workflow.py` / `test_orchestration_workflow.py`)
  MUST walk the authored path against the fixture on a `tmp_path` copy:
  load/init the project, run `bookwright graph build`, and run
  `bookwright validate`.
- **FR-008**: The test MUST assert the build's deterministic graph facts — the
  expected G9 units, G10 functions, and G7 sequence with ordered membership; the
  resolved role cross-refs; and the `crm:P2_has_type`/`crm:E55_Type` typings the
  active Propp vocabulary supplies — with expected counts/identifiers sourced from
  the co-located oracle (FR-005), not hard-coded.
- **FR-009**: The test MUST assert the validate step's exact, enumerated
  `narrative_structure` findings (the orphan beat(s) and unresolved role(s), each
  with validator name, `warning` severity, and a `file:line` source), sourced from
  the oracle.
- **FR-010**: The test MUST assert the **non-regression** guarantee: with
  `[vocabularies] active` empty (a no-vocabulary variant or a toggled copy), no
  `crm:P2_has_type`/`crm:E55_Type` typings are emitted and every other graph fact
  is unchanged.
- **FR-011**: All test assertions MUST be on **deterministic** output (the graph
  facts and the validator JSON); the test MUST NOT depend on any LLM / judgment
  step.

**Documentation & living documents**

- **FR-012**: The documentation site MUST cover the v0.4 narrative-structure
  layer (in Spanish): the ingestion of `outline/units/`, a unit card's frontmatter
  (`functions`/`roles`/`sequence`/`order`), the activation of Propp/Greimas via
  `[vocabularies] active`, and the `narrative_structure` validator's two rules.
- **FR-013**: The new/updated documentation MUST be reachable from the
  documentation site navigation.
- **FR-014**: The README MUST be updated to reflect the v0.4 narrative-structure
  layer.
- **FR-015**: The CHANGELOG MUST gain a `v0.4.0` section describing the
  narrative-structure layer and consolidating iterations 028–032, including a
  "Design decisions revised during implementation" subsection **if** any design
  divergences were recorded during 028–032.
- **FR-016**: `CLAUDE.md` and `bookwright-design.md` MUST be brought current where
  the implemented code diverged from them (status table / milestone prose in
  CLAUDE.md; design sections where behavior differs).

**Deferral contract**

- **FR-017**: `deferrals.py` MUST be left honest: `DEFERRED_CONCEPTS` MUST contain
  **exactly** `RelationshipRole` (G6) and `PsychologicalState` (G3), and their
  `target_version` MUST be re-pointed from `"v0.4"` to a concrete later version
  label (resolved in `/speckit-clarify`) — **not** a placeholder.
- **FR-018**: The `DeferralNote` docstring / explanatory text MUST be made
  consistent with the new label and the fact that v0.4 has shipped (it currently
  cites `"v0.4"` as the example concrete label).
- **FR-019**: `tests/golem/test_ingestion_parity.py` MUST stay green: the orphan
  set derived from a live build MUST equal exactly the keys of `DEFERRED_CONCEPTS`
  (`{RelationshipRole, PsychologicalState}`).

**Release**

- **FR-020**: The package version MUST be bumped to `0.4.0` at its single
  authoritative source (`src/bookwright/__init__.py` `__version__`); no second
  version string may drift.

**Scope & quality gates**

- **FR-021**: This iteration MUST introduce **no new product mechanism**: no new
  CLI verb, manifest field, validator, or skill behavior change, and **no ontology
  change** — only a fixture, a test, documentation, the deferral re-target, and
  the release metadata.
- **FR-022**: This iteration MUST NOT wire G6 (RelationshipRole) or G3
  (PsychologicalState); they remain deferred.
- **FR-023**: The full test suite MUST keep overall coverage above the project
  threshold (≥ 80 %), which remains the **single enforced** gate (one source, no
  drift — see CLAUDE.md / Constitution VIII).
- **FR-024**: Lint (`ruff check`), format (`ruff format --check`), type-check
  (`mypy --strict`), pre-commit, and CI MUST all pass, and the documentation site
  MUST build with no warnings.

### Key Entities *(include if data involved)*

- **v0.4 narrative-structure example fixture**: A source-only Bookwright project
  under `tests/fixtures/` with a populated `outline/units/` (units carrying
  `functions`, `roles`, `sequence`/`order`), a `[vocabularies]` block with Propp
  active, and a deliberate orphan beat + unresolved role — the shared input for
  the workflow test and the documentation. Accompanied by a co-located oracle
  enumerating its expected entities, typings, and validator findings.
- **v0.4 workflow test**: The automated regression (under `tests/e2e/`) walking
  build → validate against the fixture (on a `tmp_path` copy) and asserting the
  deterministic graph facts (G9/G10/G7 entities, cross-refs, `E55_Type` typings)
  and the exact `narrative_structure` findings, plus the no-vocabulary-active
  non-regression assertion.
- **Deferral registry (`deferrals.py`)**: The `DEFERRED_CONCEPTS` map, left with
  exactly G6/G3 and a concrete post-v0.4 `target_version`, reconciled against the
  live orphan set by `test_ingestion_parity.py`.
- **v0.4 documentation set**: The narrative-structure documentation page(s)
  (ingestion, unit frontmatter, vocabulary activation, the validator), the updated
  README, and the `v0.4.0` CHANGELOG section.
- **Release metadata**: `__version__` = `0.4.0`, the CHANGELOG `v0.4.0` section,
  and the updated `CLAUDE.md` / `bookwright-design.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can load the v0.4 example fixture and run
  `bookwright graph build` then `bookwright validate` to get a successful build
  whose graph carries the G9/G10/G7 entities with their `E55_Type` typings, and a
  validate run that reports the expected `narrative_structure` warnings — a
  standalone demonstration of the layer working end to end.
- **SC-002**: The v0.4 workflow test passes, asserting the deterministic graph
  facts (G9/G10/G7 entities, cross-refs, Propp `E55_Type` typings) and the exact
  enumerated `narrative_structure` findings sourced from the co-located oracle,
  plus the no-vocabulary-active non-regression (no typings, everything else
  unchanged).
- **SC-003**: `deferrals.py` lists exactly `{RelationshipRole, PsychologicalState}`
  with a concrete post-v0.4 `target_version` (no placeholder), and
  `test_ingestion_parity.py` is green.
- **SC-004**: A reader can reach the narrative-structure documentation from the
  site navigation and it covers `outline/units/` ingestion, the unit frontmatter,
  Propp/Greimas activation, and the validator; the README reflects v0.4; and the
  CHANGELOG has a `v0.4.0` section.
- **SC-005**: `__version__` reads `0.4.0` (single source) and `bookwright version`
  reports the same; `CLAUDE.md` and `bookwright-design.md` reflect the shipped
  v0.4 state.
- **SC-006**: Overall test coverage stays ≥ 80 % (the single enforced CI gate);
  lint, format, strict type-check, pre-commit, and CI are green; and the
  documentation site builds with zero warnings.
- **SC-007**: No new product mechanism is added, no ontology change is made, and
  G6/G3 remain unwired — this iteration is fixture, test, docs, deferral
  re-target, and release only.

## Assumptions

- This is plan iteration 032 (spec directory `032`), the closing iteration of
  v0.4. It assumes iterations 028–031 (outline/units + G9/G10 ingestion, G7
  sequence assembly, Propp/Greimas `E55_Type` typing, the `narrative_structure`
  validator) are already merged on `main`. This iteration adds a fixture, a test,
  documentation, the deferral re-target, and the release metadata — not new `src/`
  mechanism.
- "E2E / workflow test" here means the deterministic CLI stages (build → validate)
  are automated against the fixture; no LLM/judgment step is invoked in CI. The
  assertions are on the deterministic graph and validator JSON output only,
  mirroring M4's `test_research_workflow.py` and M5's
  `test_orchestration_workflow.py`.
- The fixture is assumed to be a **new dedicated fixture** rather than an extension
  of `parity-exercise` (which is single-purpose and pinned by
  `test_ingestion_parity.py`) or `tiny-historical` (which carries the M4/M5
  oracles). A new fixture keeps the v0.4 demonstration — Propp active, a
  deliberate orphan beat, a deliberate unresolved role — from polluting those
  pinned oracles. `/speckit-clarify` may revisit this if extending an existing
  fixture is preferred.
- The fixture and tests follow existing conventions: `tests/fixtures/tiny-*`
  (short-but-coherent narrative, Spanish prose, English identifiers/structure) and
  `tests/e2e/` (fixtures-as-input, `tmp_path` where the project is mutated), with a
  co-located oracle for exact assertions.
- Documentation prose is written in **Spanish** to match the existing docs site and
  design documents; identifiers, command names, and frontmatter keys stay as-is.
- The G6/G3 `target_version` re-target is a string-only change to the existing two
  deferral entries; the *set* of deferred keys is unchanged (G7/G9/G10 already left
  the set when 028–029 wired them), so `test_ingestion_parity.py` stays green by
  construction. The concrete label is resolved in `/speckit-clarify`.
- v0.4 is a **minor** milestone released **once** as `v0.4.0` at this closing
  iteration (like M4→`v0.2.0` and M5→`v0.3.0`); iterations 028–031 carried no
  version bump, so `__version__` moves from `0.3.4` straight to `0.4.0` here.
- Actually publishing/tagging the release (merge to `main`, annotated tag, the
  CLAUDE.md table flip) is the separate manual step the `bookwright-release` skill
  drives, not part of this iteration's branch work (Out of Scope).

## Out of Scope

- Wiring G6 (RelationshipRole) or G3 (PsychologicalState) — they remain deferred,
  re-pointed to a concrete later version.
- Any new product mechanism: this iteration adds a fixture, a test, docs, the
  deferral re-target, and the release metadata only; it changes no CLI verb,
  manifest field, validator, skill behavior, or the frozen ontology.
- Vector search over the corpus (ChromaDB / semantic retrieval) and export to
  EPUB / PDF / print — both on the demand-pulled horizon with no assigned version.
- Automating any LLM/judgment step in CI; the assertions are on deterministic
  graph and validator output.
- Actually publishing/tagging the `v0.4.0` release (merge to `main`, annotated
  tag); this iteration makes it *ready*, the release/tag action is a separate
  manual step (`bookwright-release`).
