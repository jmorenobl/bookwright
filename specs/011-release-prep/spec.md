# Feature Specification: Release Prep — Fixtures, E2E Tests & Documentation

**Feature Branch**: `011-release-prep`

**Created**: 2026-06-03

**Status**: Completed

**Input**: User description: "Bookwright v0.1 está cerca de listo. Antes del primer release necesitamos fixtures realistas para tests E2E, un sitio de documentación navegable, y un changelog que registre qué hay en esta versión." (Iteration 12 from `bookwright-implementation-plan.md`; references `bookwright-design.md` § 15.4 (M3) and § 15.5 (post-v0))

## Overview

This is the consolidation iteration that takes Bookwright from "feature-complete on `main`" to "shippable as v0.1.0". It adds nothing to the runtime feature set: instead it proves the existing system works end-to-end, makes it usable by people who have never seen the source code, and packages it for distribution. Three classes of deliverable: **realistic fixtures**, **end-to-end tests** that exercise the whole workflow over those fixtures, and **user- and contributor-facing documentation** (a navigable docs site, README quickstart, changelog, contributing guide, license).

## Clarifications

### Session 2026-06-03

- Q: What language should the v0.1.0 documentation site (MkDocs) and README quickstart be written in? → A: Spanish-only (docs site + quickstart in Spanish, aligning with the design corpus; the English-code/CLI surface stays English).
- Q: On a `claude`→`generic` integration swap, what happens to the stale `.claude/skills/` directory? → A: Leave it untouched; the swap test asserts skills are correctly materialized under `.agents/skills/` and does NOT assert removal of the old directory.

### Session 2026-06-03 (swap-mechanism correction)

- Finding: FR-008 originally specified the swap as "re-initialize with `--here --force`". That is impossible — iteration-4's ratified FR-028 makes `init` refuse any re-init of an existing project (`.bookwright/` present → `already_initialized`, *even with* `--force`), and `init` resolves the integration from the `--integration` flag, never from the manifest. Editing the manifest and re-running `init` therefore cannot perform a swap.
- Decision: the integration swap is its own intention-revealing command, **`bookwright integration use <key>`**, which re-materializes the new integration's skills (reusing the shared materializer + plugin registry), updates the manifest's `[integration]` block, and leaves the previously-materialized skills directory untouched. `init` and its protective FR-028 guard are unchanged. FR-008 and AS-3 below are restated against this command; the observable contract (skills under `.agents/skills/`, no claim on `.claude/skills/`) is unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Realistic fixture projects for end-to-end testing (Priority: P1)

A maintainer needs three small but internally coherent Bookwright projects, one per supported genre, that double as the input for automated tests and as worked examples. Each fixture is a fully valid Bookwright project: it can be initialized, its graph can be built, it can be queried, and it can be validated.

**Why this priority**: Every E2E test and several documentation examples depend on these fixtures existing first. Without them there is nothing to test the workflow against, so this slice unblocks everything else in the iteration.

**Independent Test**: Point `bookwright graph build`, `bookwright graph query`, and `bookwright validate` at each fixture directory and confirm each command succeeds and returns the expected entities/results — no E2E harness or docs required.

**Acceptance Scenarios**:

1. **Given** the `tiny-novel` fixture, **When** its graph is built and queried, **Then** the index contains exactly 3 characters, 2 settings, and 5 events, the bible and outline are fully populated, and one draft chapter is present.
2. **Given** the `tiny-essay` fixture (3 chapters, no fictional characters, with a bibliography), **When** it is built and validated, **Then** the build succeeds and validation reports no false-positive narrative violations for a non-fiction project.
3. **Given** the `tiny-memoir` fixture (single protagonist = author, autobiographical scenes), **When** it is built and queried, **Then** the single protagonist and the autobiographical scenes are present in the index.
4. **Given** any of the three fixtures, **When** `bookwright validate` runs against it in its shipped (clean) state, **Then** it exits 0 (zero `error`-severity violations) — heuristic `warning`-severity findings are permitted and non-gating, matching the validator contract (`ValidationReport.failed` keys on `error` only).

---

### User Story 2 - End-to-end tests proving the full workflow (Priority: P1)

A maintainer (and CI) needs automated tests that walk a brand-new user's path from an empty directory all the way to a validated project, plus tests that lock down the two riskiest cross-cutting behaviors (skill materialization correctness and integration swapping). These tests are the release gate: if they pass, the product demonstrably works as a whole.

**Why this priority**: Unit tests already cover components in isolation; what is unverified is that the pieces compose into a working product. This is the single strongest signal that v0.1.0 is safe to ship.

**Independent Test**: Run the E2E test suite (`tests/.../test_full_workflow.py`, `test_skills_materialization.py`, `test_integration_swap.py`) on a clean checkout and confirm all pass.

**Acceptance Scenarios**:

1. **Given** an empty working directory, **When** the full-workflow test runs `bookwright init`, edits the manifest and constitution, then runs `bookwright graph build`, `bookwright graph query`, and `bookwright validate` in sequence, **Then** each step produces its expected result and the final state is a valid project.
2. **Given** a project that has materialized its skills, **When** the materialization test runs the shipped linter (`integrations.lint.lint_skill_md`) over each generated `SKILL.md`, **Then** none raises — i.e. every file satisfies the agentskills.io standard (valid YAML frontmatter; `name` matching its parent directory and `< SKILL_NAME_MAX_LENGTH`; `description < SKILL_DESCRIPTION_MAX_LENGTH`).
3. **Given** a project initialized with `--integration claude`, **When** the project is switched to `generic` with `bookwright integration use generic`, **Then** the skills are correctly materialized under `.agents/skills/` and the manifest's `[integration]` records `generic`. The previous `.claude/skills/` directory is left untouched (the swap regenerates only the new integration's skills); the test asserts the new location is correct and does not assert removal of the old one.

---

### User Story 3 - A new user can self-serve from the docs (Priority: P2)

Someone who has never seen Bookwright lands on the repository, reads the README, follows a 5-minute quickstart, and browses a navigable documentation site to go deeper — all without reading source code.

**Why this priority**: Documentation determines whether anyone outside the maintainers can actually adopt v0.1.0. It depends on the workflow being real (US1/US2) so the quickstart steps are accurate, hence P2.

**Independent Test**: Build the docs site and confirm it generates with no warnings; have a person who has not touched the source follow only the README quickstart and reach a validated project.

**Acceptance Scenarios**:

1. **Given** the repository README, **When** a new user reads it, **Then** it explains what Bookwright is, how to install it quickly, a 5-minute quickstart, and links into the docs site.
2. **Given** the documentation site, **When** a user browses it, **Then** it contains pages for: index, getting-started, architecture (a summary of the design document with links to the full text), one page per command, validation, extending, and FAQ.
3. **Given** the docs source, **When** the site is built, **Then** the build completes with zero warnings.
4. **Given** only the published README quickstart and a locally built/installed distribution, **When** a new user follows it step by step without opening the source, **Then** they complete the entire workflow (init → edit → build → query → validate) successfully.

---

### User Story 4 - The release is packaged and gated for v0.1.0 (Priority: P3)

A maintainer can cut a v0.1.0 release with confidence: the changelog records exactly what ships, contributors have a guide that explains how to extend the system, the project carries an explicit open-source license, and every quality gate is green.

**Why this priority**: This is the final wrapper. It depends on all prior slices being done, and is the last step before tagging the release.

**Independent Test**: Verify CHANGELOG, CONTRIBUTING, and LICENSE exist and are accurate for v0.1.0; run the full quality-gate suite and confirm all pass; build a distribution artifact and install it into a clean environment.

**Acceptance Scenarios**:

1. **Given** the repository, **When** a maintainer reads `CHANGELOG.md`, **Then** it has a `v0.1.0` entry listing every feature included in this version.
2. **Given** a prospective contributor, **When** they read `CONTRIBUTING.md`, **Then** it explains how to contribute, how to create a new integration, how to create a custom validator, and how to create a vocabulary.
3. **Given** the repository, **When** anyone inspects it, **Then** an Apache-2.0 `LICENSE` is present and referenced from the project metadata.
4. **Given** a clean checkout, **When** the full quality suite runs (test suite with coverage, lint, format check, strict type check, pre-commit, CI), **Then** every gate passes and reported test coverage exceeds 80%.
5. **Given** a locally built distribution artifact, **When** it is installed into an isolated environment (e.g. via `pipx` from the local wheel), **Then** the `bookwright` CLI is runnable and the quickstart succeeds against it.

---

### Edge Cases

- **Non-fiction false positives**: the essay and memoir fixtures run the full built-in validator set, yet must report no `error`-severity violations — the fiction validators are inert off-genre (`character_presence` emits only `warning`s without a roster; `focalization` is silent without a third-person voice declaration), so no validator need be disabled. Validation against a clean fixture must exit 0.
- **Integration swap residue**: switching a project from `claude` to `generic` produces skills in the new location (`.agents/skills/`); stale skills in the previous location (`.claude/skills/`) are **left untouched** (no cleanup is performed). The swap test asserts the new location is correct and does not assert removal of the old one.
- **Docs drift**: if a documented command name or flag no longer matches the shipped CLI, the docs↔CLI drift test (DOC-2) fails closed; if a quickstart *step* drifts, the manual packaged-install walkthrough (MAN-2) surfaces it. Neither path silently ships stale docs.
- **Coverage just under threshold**: if the new E2E tests pull coverage measurement around the 80% line, the gate must fail closed (block release) rather than round up — enforced by `[tool.coverage.report] precision = 2` + `fail_under = 80`, so e.g. 79.99% reports as 79.99 and fails.
- **Existing draft artifacts**: README, CHANGELOG, and CONTRIBUTING already exist in partial form — this iteration finalizes/updates them rather than assuming a blank slate, and must not regress content already present.

## Requirements *(mandatory)*

### Functional Requirements

#### Fixtures

- **FR-001**: The project MUST provide a `tiny-novel` fixture that is a valid Bookwright project containing exactly 3 characters, 2 settings, 5 events, and 1 draft chapter, with the bible and outline fully populated, internally coherent enough to be a believable minimal novel.
- **FR-002**: The project MUST provide a `tiny-essay` fixture that is a valid Bookwright project with 3 chapters, no fictional characters, and a bibliography.
- **FR-003**: The project MUST provide a `tiny-memoir` fixture that is a valid Bookwright project with a single protagonist (the author) and autobiographical scenes.
- **FR-004**: Each fixture MUST be initializable, graph-buildable, queryable, and validatable by the shipped CLI, and MUST pass `bookwright validate` with **exit code 0** (zero `error`-severity violations) in its clean shipped state. Heuristic `warning`-severity findings are permitted and non-gating, consistent with the validator contract (`ValidationReport.failed` keys on `error` only).
- **FR-005**: Fixtures MUST live under `tests/fixtures/<name>/` so they are usable as input by the automated test suite.

#### End-to-end tests

- **FR-006**: An E2E test MUST exercise the full workflow — `bookwright init`, editing the manifest and constitution, `bookwright graph build`, `bookwright graph query`, `bookwright validate` — and assert the expected outcome at each step.
- **FR-007**: An E2E test MUST verify that every generated `SKILL.md` conforms to the agentskills.io standard by invoking the shipped linter `bookwright.integrations.lint.lint_skill_md` on each skill directory and asserting it does not raise (valid YAML frontmatter; `name` == parent directory and `< SKILL_NAME_MAX_LENGTH`; `description < SKILL_DESCRIPTION_MAX_LENGTH`). Re-implementing the bounds in the test is forbidden — the test MUST exercise the same gate the toolkit enforces at materialization (Principle VII).
- **FR-008**: An E2E test MUST verify the integration swap: after `bookwright init --integration claude`, running `bookwright integration use generic` materializes skills correctly under `.agents/skills/` and updates the manifest's `[integration]` block to `generic`. The test MUST assert only the new location; it MUST NOT require removal of the previous `.claude/skills/` directory (no cleanup behavior is performed). (The swap is a dedicated command, not an `init --here --force` re-init, which iteration-4's FR-028 guard refuses; see the 2026-06-03 swap-mechanism correction.)
- **FR-009**: The E2E tests MUST run as part of the standard test suite and contribute to the coverage measurement.

#### Documentation

- **FR-010**: The repository MUST have a canonical README (Spanish — `README.es.md`) covering what Bookwright is, quick installation, a 5-minute quickstart, and links to the documentation site. `README.md` (English) MAY remain as a short pointer to the canonical README and the docs.
- **FR-011**: The project MUST provide a documentation site built with MkDocs (mkdocs-material theme) containing pages for: index, getting-started, architecture, commands, validation, extending, and FAQ.
- **FR-012**: The commands documentation MUST include one page (or clearly delineated section) per shipped **executable CLI** command — the Typer leaf-command set (`init`, `check`, `version`, `validate`, `graph build`, `graph query`, `integration use`). The 10 authoring Agent-Skill commands (`bible`, `outline`, `synopsis`, `scenes`, `draft`, `clarify`, `analyze`, `checklist`, `constitution`, `continuity`) are LLM-driven `SKILL.md` prompts, not executable CLI commands; they are documented conceptually under getting-started / validation / extending rather than as per-command pages, and the docs↔CLI drift test (FR-015) enforces parity against this executable leaf set (DOC-2).
- **FR-013**: The architecture page MAY be a summary of the design document and MUST link to the full design document rather than duplicating it wholesale.
- **FR-014**: The documentation site MUST build with zero warnings.
- **FR-015**: Documentation content MUST match the behavior of the shipped CLI. **Command names** and **per-command flags** are guarded automatically by the docs↔CLI drift test (DOC-2): the documented command set equals the registered Typer leaf set, and every CLI option a leaf command exposes appears in that command's documentation page (no undocumented flag, no documented-but-removed flag). **Quickstart step accuracy** — the semantic correctness of the worked example — is verified by the manual packaged-install walkthrough (SC-003, MAN-2), since step-level correctness cannot be asserted structurally.

#### Release metadata & quality gates

- **FR-016**: `CHANGELOG.md` MUST contain a `v0.1.0` entry enumerating every feature included in this release.
- **FR-017**: `CONTRIBUTING.md` MUST explain how to contribute and specifically how to create: a new integration, a custom validator, and a vocabulary.
- **FR-018**: The repository MUST carry an Apache-2.0 `LICENSE` referenced from project metadata.
- **FR-019**: The full test suite MUST pass with reported coverage **at least 80%** (Constitution VIII minimum), measured without rounding up: a run that would round to 80% but is below it MUST fail the gate (`[tool.coverage.report] precision = 2`, `fail_under = 80`).
- **FR-020**: Lint (`ruff check`), format check (`ruff format --check`), strict type check (`mypy --strict`), and pre-commit MUST all pass.
- **FR-021**: CI MUST run the test, lint, type, and docs-build gates and report green on the release branch.
- **FR-022**: A distribution artifact (wheel + sdist) MUST be buildable and installable into an isolated environment, after which the quickstart succeeds without touching the source tree.

### Key Entities *(include if feature involves data)*

- **Fixture project**: a self-contained, version-controlled minimal Bookwright project (manifest, constitution, bible, outline, chapters/scenes, vocabulary) used both as test input and as a worked example. Three exist: `tiny-novel`, `tiny-essay`, `tiny-memoir`.
- **E2E test**: an automated test that drives the real CLI over a fixture or a freshly initialized project and asserts cross-component behavior, as opposed to a unit test exercising one component in isolation.
- **Documentation site**: the rendered, navigable set of pages generated from `docs/` describing usage, architecture, commands, validation, and extension points.
- **Release artifact**: the distributable wheel and sdist plus the metadata (changelog, license, contributing guide) that constitute the publishable v0.1.0.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three fixtures pass `bookwright validate` with exit 0 (zero `error`-severity violations; heuristic warnings allowed) in their shipped state, and the `tiny-novel` graph query returns exactly the expected 3 characters / 2 settings / 5 events.
- **SC-002**: The E2E suite (full workflow, skills materialization, integration swap) passes on a clean checkout with a 100% pass rate.
- **SC-003**: A person who has never read the source completes the entire init → edit → build → query → validate workflow using only the README quickstart and an installed distribution, in 5 minutes or less.
- **SC-004**: The documentation site builds with zero warnings and exposes all seven required page areas (index, getting-started, architecture, commands, validation, extending, FAQ), with one page/section per shipped executable CLI command (the Typer leaf set; see FR-012).
- **SC-005**: Reported automated-test coverage is **at least 80%** (Constitution VIII), enforced fail-closed with no round-up (`[tool.coverage.report] precision = 2`, `fail_under = 80`).
- **SC-006**: Every quality gate — tests, `ruff check`, `ruff format --check`, `mypy --strict`, pre-commit, and CI — reports green on the release branch.
- **SC-007**: A wheel built locally installs into a clean isolated environment and the `bookwright` CLI runs the quickstart end-to-end without access to the source tree.
- **SC-008**: `CHANGELOG.md` (v0.1.0 entry), `CONTRIBUTING.md` (contribute + new integration + custom validator + vocabulary), and the Apache-2.0 `LICENSE` are all present and accurate.

## Assumptions

- **Documentation language** (clarified 2026-06-03): the documentation site and the canonical quickstart are written in **Spanish**, aligning with the project's Spanish design corpus and the bilingual author. Code, identifiers, CLI surface, command names, flags, and commit messages remain in English. A fully bilingual docs site is out of scope for v0.1.0; the existing `README.es.md` becomes the canonical user-facing README, and `README.md` may remain as a short English pointer to it but is not required to carry the full quickstart.
- **Existing draft files**: `README.md`, `CHANGELOG.md`, and `CONTRIBUTING.md` already exist in partial form and an Apache-2.0 `LICENSE` is already present; this iteration finalizes/updates them to the v0.1.0 state rather than creating them from scratch.
- **Shipped command set**: the documented and tested commands are those present on `main` after iterations 1–11 — the executable Typer **leaf** commands (`init`, `check`, `version`, `validate`, `graph build`, `graph query`, `integration use`; `graph` and `integration` are groups, not leaves, and are not documented as command pages) and the 10 source/Agent-Skill commands (`bible`, `outline`, `synopsis`, `scenes`, `draft`, `clarify`, `analyze`, `checklist`, `constitution`, `continuity`). The only command introduced this iteration is `integration use`, the corrective swap mechanism that makes FR-008 achievable (see the 2026-06-03 swap-mechanism correction); it switches between the existing `claude`/`generic` integrations and adds no new integration (v0 scope unchanged).
- **Integration scope**: only `claude` and `generic` integrations are exercised, matching v0 scope; no Copilot/Gemini/Cursor-specific behavior is documented or tested.
- **Fixture coherence over richness**: fixtures are deliberately minimal; "coherent" means internally consistent and validatable, not literarily rich.
- **Distribution name**: the installable distribution is referenced as `bookwright-cli` (the name used in the manual-validation step), exposing a `bookwright` console command.
- **Integration-swap mechanism & residue policy** (clarified 2026-06-03): the swap is performed by the dedicated `bookwright integration use <key>` command (not an `init` re-init, which FR-028 refuses). It re-materializes the new integration's skills, updates the manifest's `[integration]` block, and leaves the previously-active integration's directory (`.claude/skills/`) untouched (no cleanup). The swap test asserts the new location (`.agents/skills/`) is correct and does not assert removal of the old directory.

## Out of Scope

- Indexer performance optimization (deferred to post-v0 should rdflib prove slow).
- Preset / genre-package system (v0.2).
- Vector search / `GrafeoIndexer` (v0.3).
- Integrations beyond `claude` and `generic` (v0.4).
- Export to EPUB/PDF/print (v1.0).
- Publishing the release to a public package index or hosting the docs site externally (this iteration produces buildable/installable artifacts and a buildable site; the actual GitHub release publication is the final manual step after all gates are green).
