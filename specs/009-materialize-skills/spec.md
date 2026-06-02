# Feature Specification: Materialize commands as Agent Skills

**Feature Branch**: `009-materialize-skills`
**Created**: 2026-06-02
**Status**: Draft
**Input**: User description: "When the user runs `bookwright init`, integrations must transform the source commands into valid Agent Skills in the destination directory. Each generated `SKILL.md` must comply with the agentskills.io standard and, when the integration supports extended capabilities (such as Claude Code), take advantage of them."

## Context

Iteration 8 authored ten **integration-agnostic** command source prompts under
`resources/commands/*.md`, each carrying only `name` + `description` frontmatter
and a body that uses the neutral `{ARGS}` placeholder and inline `bookwright …`
CLI calls. Those sources are not yet usable by any agent.

Iteration 3 stood up the `SkillsIntegration` base class with a **stub** `setup()`
that only creates the resolved `skills_dir` and drops a placeholder marker; it
explicitly deferred real `SKILL.md` materialization to "iteration 9". The two v0
integrations (`ClaudeIntegration`, `GenericIntegration`) already declare their
`skills_dir` and their capability flags (`supports_dynamic_context`,
`supports_subagents`, `supports_tool_restrictions`).

This iteration replaces the stub with **real materialization**: every source
command becomes a per-skill directory containing a standard-compliant `SKILL.md`
(plus any referenced auxiliary files), the operation is idempotent, and each
generated artifact passes an agentskills.io-spec linter. Capability-aware
enrichment (Claude Code dynamic-context injection) is applied only where the
integration declares support for it.

Reference: `bookwright-design.md § 11.4` (Generating `SKILL.md` from commands)
and `§ 11.5` (progressive disclosure).

## Clarifications

### Session 2026-06-02

(none yet — `/speckit-clarify` pending)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Author gets working skills after `init` (Priority: P1)

An author runs `bookwright init` selecting the Claude Code integration. For every
source command shipped with Bookwright, the author finds a ready-to-invoke skill
under `.claude/skills/<command-name>/SKILL.md`. The author's agent can discover
each skill from its `name` + `description` and, when invoked, follow a body whose
argument placeholder and CLI calls are correctly wired for that agent.

**Why this priority**: This is the core deliverable. Without materialization the
ten authored commands are inert files; with it, the toolkit's whole authoring
workflow becomes usable. It is independently demonstrable end-to-end.

**Independent Test**: Run `init` against an empty project with the Claude
integration; assert one `<skills_dir>/<command>/SKILL.md` exists per source
command, each with valid frontmatter whose `name` equals its parent directory,
and a body containing `$ARGUMENTS` (not `{ARGS}`).

**Acceptance Scenarios**:

1. **Given** a fresh project and the Claude integration, **When** `init`
   materializes skills, **Then** exactly one directory per source command is
   created under `.claude/skills/`, each containing a single `SKILL.md`.
2. **Given** a source command whose body references files under `references/`,
   **When** its skill is materialized, **Then** those referenced files are copied
   into the skill's own `references/` subdirectory and the body's references still
   resolve.
3. **Given** a materialized `SKILL.md`, **When** its frontmatter is read, **Then**
   it contains `name` (identical to the parent directory), an enriched
   `description`, `license`, `metadata.author = "bookwright"`, and
   `metadata.version` equal to the CLI version that generated it.
4. **Given** a source command body containing the `{ARGS}` token, **When**
   materialized for any v0 integration, **Then** every `{ARGS}` occurrence is
   replaced by `$ARGUMENTS` and no `{ARGS}` token remains.

### User Story 2 - Re-running `init` preserves customizations (Priority: P2)

An author has edited a generated skill (tuned its description, added a step). They
re-run `init` (e.g., after upgrading Bookwright). Their edits survive: existing
skills are not overwritten.

**Why this priority**: Idempotency protects user work and makes `init` safe to
re-run, but the feature is still demonstrable without it (P1 covers first-run
generation). It is a distinct, independently testable guarantee.

**Independent Test**: Materialize skills, hand-edit one `SKILL.md`, re-run
materialization, and assert the edited file is byte-for-byte unchanged while any
genuinely missing skill is (re)created.

**Acceptance Scenarios**:

1. **Given** an existing `<skills_dir>/<command>/SKILL.md`, **When**
   materialization runs again, **Then** that file is left untouched (no
   overwrite, no duplicate).
2. **Given** a project where one skill directory was deleted, **When**
   materialization runs again, **Then** only the missing skill is regenerated and
   the others remain untouched.

### User Story 3 - Capability-aware output per integration (Priority: P3)

An author using a generic agentskills.io-compatible agent gets standard-only
skills (no Claude-specific syntax), while an author using Claude Code gets skills
that additionally exploit dynamic-context injection where it adds value.

**Why this priority**: Correct multi-integration behavior matters for the plugin
architecture, but both integrations still produce valid skills regardless; this
story refines *how* they differ. Independently testable per integration.

**Acceptance Scenarios**:

1. **Given** the Claude integration (`supports_dynamic_context = true`), **When** a
   skill is materialized, **Then** dynamic-context injection (the `!`​`shell`​`​`
   syntax) may appear in the body, and every such injection either reads a project
   file or invokes the `bookwright` CLI — never a non-existent Python wrapper.
2. **Given** the generic integration (`supports_dynamic_context = false`), **When**
   a skill is materialized, **Then** no dynamic-context (`!`​`shell`​`​`) syntax
   appears anywhere in the body.

### Edge Cases

- **Description over the cap**: enrichment that would push `description` past 1024
  characters MUST be prevented (the materializer keeps it within the cap rather
  than emitting a non-compliant skill).
- **Body over the size budget**: a materialized body exceeding the ~5000-token
  Tier-2 budget is a lint failure and MUST be surfaced, not silently shipped.
- **Missing referenced file**: a source body referencing a `references/<file>` that
  does not exist in the source tree MUST be reported clearly rather than producing
  a skill with a dangling reference.
- **`name` ≠ directory**: a source `name` that would not match its destination
  directory MUST be caught by the linter before the skill is considered valid.
- **No source commands present**: materialization over an empty `commands/` set
  completes without error and produces no skill directories.
- **Generic integration with a re-targeted `--skills-dir`**: skills materialize
  under the user-chosen directory, never outside the project root.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `ClaudeIntegration.setup()` and `GenericIntegration.setup()` MUST
  perform real materialization, replacing the iteration-3 stub that only wrote a
  placeholder marker.
- **FR-002**: For each source command (`resources/commands/<command>.md`), the
  system MUST create a directory `<skills_dir>/<command-name>/` containing exactly
  one `SKILL.md` (e.g., `.claude/skills/bookwright-constitution/SKILL.md`).
- **FR-003**: The generated `SKILL.md` frontmatter MUST include `name` identical to
  the parent directory name.
- **FR-004**: The generated `description` MUST be the source command's description
  enriched with explicit triggers drawn from a `SKILL_DESCRIPTIONS` mapping, and
  MUST remain under 1024 characters.
- **FR-005**: The frontmatter MUST include a `license` field, inherited from the
  Bookwright design default (`Apache-2.0`) when the source does not specify one.
- **FR-006**: The frontmatter MUST include `metadata.author = "bookwright"` and
  `metadata.version` set to the version of the CLI performing the materialization.
- **FR-007**: For all v0 integrations, every `{ARGS}` token in the source body MUST
  be substituted with `$ARGUMENTS`, and no `{ARGS}` token may remain in the output.
- **FR-008**: `bookwright` CLI calls in the body MUST be written inline (e.g.,
  `bookwright graph build --json`); there MUST be no `{SCRIPT}` token and no
  reference to helper scripts under `.bookwright/scripts/`.
- **FR-009**: Agent-facing subcommands invoked from skill bodies MUST use their
  JSON output mode (e.g., `--json`) so the agent can parse the result.
- **FR-010**: When a source body references files under `references/` (e.g.,
  `references/golem-character.md`), those files MUST be copied into the skill's own
  `references/` subdirectory (e.g.,
  `.claude/skills/bookwright-constitution/references/golem-character.md`).
- **FR-011**: When an integration declares `supports_dynamic_context = true` (Claude
  Code), the materializer MAY emit dynamic-context injection (`!`​`shell`​`​`
  syntax) in the body for capability-aware enrichment.
- **FR-012**: When an integration declares `supports_dynamic_context = false`
  (generic), the materializer MUST NOT emit any dynamic-context (`!`​`shell`​`​`)
  syntax; output stays within the agentskills.io standard.
- **FR-013**: Any dynamic-context injection that is emitted MUST only read a project
  file (e.g., `!`​`cat bible/constitution.md`​`​`) or invoke the `bookwright` CLI;
  it MUST NOT point at a non-existent Python wrapper or other absent executable.
- **FR-014**: Materialization MUST be idempotent at the `SKILL.md` granularity: if
  `<skills_dir>/<command>/SKILL.md` already exists, it MUST NOT be overwritten,
  preserving user customizations.
- **FR-015**: Each generated `SKILL.md` MUST pass an agentskills.io-spec linter that
  verifies: `name` matches the parent directory, `description` < 1024 characters,
  body within the ~5000-token Tier-2 budget, and valid YAML frontmatter.
- **FR-016**: A skill that fails linting MUST be surfaced as an error (the failure
  is reported, not silently shipped), so init does not leave an invalid skill on
  disk as if it were valid.
- **FR-017**: Materialization MUST NOT write outside the integration's resolved
  `skills_dir` (which itself is constrained to the project root, per iteration 3).
- **FR-018**: The body MUST preserve the source command's instructional content
  (role, procedure, outputs, "what not to do") apart from the token substitutions
  and capability-aware enrichment defined above.

### Key Entities *(include if feature involves data)*

- **Source command**: an integration-agnostic `.md` under `resources/commands/`,
  with `name` + `description` frontmatter and a body using `{ARGS}` and inline
  `bookwright …` calls. Read-only input to materialization.
- **Materialized skill**: a `<skills_dir>/<command>/` directory holding one
  `SKILL.md` (Tier 1 + Tier 2) and an optional `references/` subdirectory (Tier 3).
- **`SKILL.md` frontmatter**: `name`, enriched `description`, `license`,
  `metadata.author`, `metadata.version`.
- **`SKILL_DESCRIPTIONS` mapping**: per-command trigger text used to enrich the
  source description into the materialized `description`.
- **Integration capability flags**: `supports_dynamic_context` (and the existing
  `supports_subagents`, `supports_tool_restrictions`) that gate capability-aware
  enrichment.
- **Reference file**: an auxiliary `references/<file>.md` shipped alongside source
  commands, copied per-skill on demand (progressive-disclosure Tier 3).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After `init` with any v0 integration, 100% of source commands have a
  corresponding `<skills_dir>/<command>/SKILL.md`.
- **SC-002**: 100% of generated `SKILL.md` files pass the agentskills.io linter
  (name-matches-directory, description < 1024 chars, body within the Tier-2 token
  budget, valid YAML frontmatter).
- **SC-003**: Zero `{ARGS}` (and zero `{SCRIPT}`) tokens remain in any generated
  body; every argument placeholder reads `$ARGUMENTS`.
- **SC-004**: 100% of `references/` files cited by a materialized body are present
  in that skill's own `references/` subdirectory.
- **SC-005**: Re-running materialization over already-materialized skills changes
  zero existing `SKILL.md` files (byte-for-byte identical), while regenerating any
  skill whose directory is missing.
- **SC-006**: For the generic integration, zero generated bodies contain
  dynamic-context (`!`​`shell`​`​`) syntax; for the Claude integration, every
  dynamic-context injection that appears targets a project file or the `bookwright`
  CLI (zero target a non-existent wrapper).
- **SC-007**: No artifacts are written outside the resolved `skills_dir`.

## Assumptions

- **A-001 (Description enrichment)**: `SKILL_DESCRIPTIONS` lives in the integrations
  layer (per design § 11.4, alongside the Spec Kit precedent) and supplies the
  trigger text merged into each command's source description. Because iteration 8
  already authored rich, bilingual descriptions with explicit triggers, the
  materializer treats the source description as the base and merges
  `SKILL_DESCRIPTIONS` triggers without duplication, truncating/omitting as needed
  to stay under the 1024-char cap. (Exact merge semantics to be confirmed in
  `/speckit-clarify`.)
- **A-002 (License default)**: The Bookwright design default license is `Apache-2.0`;
  source commands carry no `license`, so all materialized skills inherit
  `Apache-2.0` in v0.
- **A-003 (Version source)**: `metadata.version` is read from the installed CLI
  version (`bookwright.__version__`), not hard-coded per skill.
- **A-004 (`{ARGS}` → `$ARGUMENTS` for all v0 integrations)**: Both `claude` and
  `generic` map `{ARGS}` to `$ARGUMENTS`, the majority convention; no
  per-integration argument-token divergence exists in v0.
- **A-005 (Idempotency granularity)**: The existence check is per-`SKILL.md`. When a
  skill is (re)generated, its `references/` files are written as part of that
  generation; when the `SKILL.md` already exists, the whole skill directory is left
  untouched.
- **A-006 (Lint failure handling)**: A lint failure aborts that integration's
  materialization with a reported error rather than skipping the offending skill
  silently. (Init's overall error-envelope behavior is iteration 10; this iteration
  only surfaces the failure.)
- **A-007 (Dynamic-context scope in v0)**: Claude dynamic-context injection, where
  used, is limited to reading project files (e.g., `bible/constitution.md`) or
  invoking the `bookwright` CLI — consistent with the "no Python wrappers" rule.

## Out of Scope

- Implementing new validators / the consolidated validation system — that is
  iteration 10/11. This iteration only adds the agentskills.io lint check needed to
  guarantee generated skills are spec-compliant.
- Preset / genre-package generation (post-v0).
- Authoring auxiliary helper scripts under `.bookwright/scripts/` — none exist;
  skills call the `bookwright` CLI directly.
- Integrations beyond `claude` / `generic` (Copilot, Gemini, Cursor-specific) — v0.4.
- Anything other than materializing the `SKILL.md` artifacts (and their referenced
  files) from existing source commands.

## Dependencies

- **Iteration 3** (`SkillsIntegration`, `INTEGRATION_REGISTRY`, capability flags,
  `resolve_skills_dir`, project-root containment) — extended here.
- **Iteration 8** (the ten source commands and their `references/` files) — consumed
  as input.
- **Iteration 6** (`bookwright graph …` JSON subcommands) and the broader CLI —
  referenced inline by materialized bodies (no new CLI behavior added here).
