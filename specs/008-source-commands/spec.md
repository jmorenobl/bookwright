# Feature Specification: The 10 Bookwright Command Source Prompts

**Feature Branch**: `008-source-commands`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: Iteration 8 of `bookwright-implementation-plan.md` — author the 10 `.md` command sources under `src/bookwright/resources/commands/` (constitution, bible, outline, scenes, draft, synopsis, clarify, analyze, continuity, checklist). Each is a structured prompt the AI agent executes when the author invokes it; they are the project's primary creative interface and must be written with care. See `bookwright-design.md` § 10 (Sistema de Commands), including the annotated `bookwright-constitution.md` example in § 10.1.

## Context & Scope Decision *(read first)*

This iteration is **prompt authoring**, not code. It produces 10 Markdown documents — the intellectual core of how an author drives Bookwright. Each document is a self-contained instruction set an AI coding agent follows verbatim. Quality is judged by whether a competent agent can execute the prompt against a real Bookwright project without ambiguity, and whether the right command activates from natural-language author intent.

The 10 commands form the creative pipeline already enumerated in design § 10.4. They consume the project skeleton stamped by `bookwright init` (iteration 4) — `bible/`, `outline/`, `manuscript/` — and the re-instanceable molds authored in iteration 7 (`resources/templates/bible/character.md.tmpl`, `setting.md.tmpl`, `location.md.tmpl`, `scenes/scene.md.tmpl`, `manuscript/chapter.md.tmpl`). They invoke the `bookwright` CLI subcommands that already exist (notably `bookwright graph build --json` from iteration 6) by writing the call **inline in the prompt body** — there is no `scripts:` frontmatter block and no shell/Python wrapper.

What this iteration delivers is **source-of-truth prompts only**. It explicitly does **not** materialize them into per-integration `SKILL.md` files, and does **not** author the auxiliary Python helpers a materialized skill might call — both are iteration 9.

This spec inherits two project-wide conventions settled in iteration 7 that supersede the wording in the design/plan:

- The fill-marker token is **`[PENDING: <question>]`** (English token, Spanish question), **not** `[PENDIENTE]`. The iteration-8 prompts must instruct the agent to emit this exact token so the iteration-7 templates, the sentinel sweep, and these commands all agree on one marker. (See Assumptions.)
- Human-facing prose in the authored artifacts is **Spanish**; frontmatter **keys** and the fill-marker token stay **English**.

## Clarifications

### Session 2026-06-01

- Q: Should the command source files carry a `handoffs:` frontmatter block, as shown in the § 10.1 example? → A: No. v0 command sources stay **integration-agnostic**. The only frontmatter required is `name` and `description` (plus other agentskills.io-valid keys if needed). Agent-specific affordances (Claude Code `handoffs`, dynamic-context injection) are the concern of per-integration materialization in iteration 9, consistent with Constitution Principles V–VII. The § 10.1 `handoffs` block is treated as illustrative of the eventual materialized skill, not a requirement of the source.
- Q: What language are the command **bodies** written in? → A: Spanish prose (matching the § 10.1 example and the iteration-7 templates). Frontmatter keys are English; each `description` embeds **both** Spanish and English trigger phrases so implicit activation fires regardless of the language the author writes their request in.
- Q: Heavy domain context (GOLEM ontology, Propp functions, Greimas actants)? → A: Lives in `src/bookwright/resources/commands/references/*.md` (tier-3 progressive disclosure). Command bodies link to those files rather than inlining the material, keeping each body under the 5000-token tier-2 budget.
- Q: How much does a single `bookwright-bible` invocation produce? → A: A complete first pass over **every** bible artifact in one run, but the prompt directs the agent to work in a fixed order (constitution-derived entities first), write each file as it goes, and mark thin entries `[PENDING: …]` rather than over-inventing canon. This honors the § 10.4 "full bible set" contract while keeping every file grounded and the author's command count low.
- Q: Re-invoking a generative command on already-populated targets? → A: Update-in-place, preserving authored content. The prompt directs the agent to read the existing file, treat human-authored prose and resolved `[PENDING]` answers as authoritative, fill only gaps and still-open `[PENDING: …]` markers, and never overwrite or duplicate authored content. Re-running is therefore safe and additive.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The generative pipeline is executable end-to-end (Priority: P1)

An author with an initialized Bookwright project invokes the generative commands in sequence — `bookwright-constitution`, then `bookwright-bible`, `bookwright-outline`, `bookwright-scenes`, and `bookwright-draft <scene_id>` — to go from a raw brief to a drafted scene. Each command's prompt tells the executing agent exactly what project files to read, what to write, what to mark `[PENDING: …]`, and what not to do.

**Why this priority**: These five commands (plus `synopsis`) are the reason the toolkit exists; without them there is no creative interface. They are the MVP.

**Independent Test**: For each of the six generative commands, confirm the `.md` exists at `src/bookwright/resources/commands/<name>.md`, has valid YAML frontmatter with a `description` under 1024 characters, has a non-empty body under the 5000-token budget, and that the body names concrete read targets (e.g. `bible/constitution.md`), concrete write targets (e.g. `bible/characters/<slug>.md`), a step-by-step procedure, and the `[PENDING: …]`-vs-ask rule. A human read of `bookwright-constitution.md` confirms an agent could execute it against a fresh project with no ambiguity.

**Acceptance Scenarios**:

1. **Given** a project containing a free-text brief, **When** the agent executes `bookwright-constitution`, **Then** the prompt directs it to read the constitution mold, fill every field from the brief, mark unsupplied fields `[PENDING: <pregunta>]`, write `bible/constitution.md`, run `bookwright graph build --json`, and report which fields were left pending and which narrative vocabularies were activated.
2. **Given** a filled `bible/constitution.md` and the brief, **When** the agent executes `bookwright-bible`, **Then** the prompt directs it to populate the bible artifacts (`bible/characters/*`, `bible/settings/*`, `bible/locations/*`, `bible/timeline.md`, `bible/relationships.md`, `bible/themes.md`, `bible/glossary.md`, `bible/research.md`, `bible/subplots.md`, and `bible/pov-structure.md` only when the work is multi-POV) by stamping the iteration-7 molds once per entity.
3. **Given** a constitution and bible, **When** the agent executes `bookwright-outline`, **Then** it writes `outline/arcs.md`, `outline/structure.md`, and an initial `outline/synopsis.md`.
4. **Given** an outline and bible, **When** the agent executes `bookwright-scenes`, **Then** it writes `outline/scenes.md` as a concrete scene list where each scene carries narrative function, characters present, location, and beats.
5. **Given** an outline, bible, and a target `scene_id`, **When** the agent executes `bookwright-draft <scene_id>`, **Then** it writes the scene's prose into the correct `manuscript/cap-NN.md` section while respecting the voice, focalization, and constraints declared in the constitution and bible.
6. **Given** a project at any stage, **When** the agent executes `bookwright-synopsis`, **Then** it updates `outline/synopsis.md` with a short version (250–350 words) and a long version (1000–2000 words) reflecting current project state.

---

### User Story 2 - Quality and consistency commands report without mutating (Priority: P2)

At any point the author invokes a read-only checking command — `bookwright-clarify`, `bookwright-analyze`, `bookwright-continuity`, or `bookwright-checklist <artifact>` — to surface gaps, contradictions, and incompleteness before committing more effort. These commands emit a report and write nothing to the project.

**Why this priority**: They protect the integrity of the work but are not required to produce a first draft; they layer on top of US1.

**Independent Test**: For each of the four commands, confirm the `.md` exists, validates, and that its body explicitly frames the command as **report-only** (no project file writes), names the artifacts it reads, and defines the report's shape. `bookwright-continuity` additionally instructs the agent to run `bookwright graph build --json` and reason over the resulting graph.

**Acceptance Scenarios**:

1. **Given** any project artifact, **When** the agent executes `bookwright-clarify`, **Then** it returns a list of questions the author must answer before proceeding, and writes nothing.
2. **Given** a constitution, bible, outline, and scenes, **When** the agent executes `bookwright-analyze` (pre-draft), **Then** it reports cross-artifact inconsistencies among those four and writes nothing.
3. **Given** a manuscript plus bible, **When** the agent executes `bookwright-continuity` (post-draft), **Then** the prompt directs it to build the graph via `bookwright graph build --json` and report bible-compliance, character-arc consistency, and timeline-coherence findings.
4. **Given** a named artifact, **When** the agent executes `bookwright-checklist <artifact>`, **Then** it reports whether that artifact is complete — all sections present, no unfilled `[PENDING: …]` markers, no empty placeholders.

---

### User Story 3 - Implicit activation is precise across languages (Priority: P1)

When the author writes a natural-language request, the *right* command activates and premature or unrelated commands stay silent — in both Spanish and English. The discriminating signal lives entirely in each command's `description`.

**Why this priority**: A creative interface that fires the wrong tool (or fires `bible` when the author only wanted to discuss tone) is worse than no tool. Activation precision is a first-class quality bar of this iteration, not a nicety.

**Independent Test**: Run a mental A/B battery of author phrasings against the 10 descriptions and confirm the intended command is the unambiguous top match while sibling commands do not over-trigger.

**Acceptance Scenarios**:

1. **Given** the request "ayúdame a definir el tono de mi libro" / "help me define the tone of my book", **When** matched against descriptions, **Then** `bookwright-constitution` activates and `bookwright-bible` does **not** (it would be premature).
2. **Given** "necesito fichas de mis personajes y localizaciones" / "I need character and location sheets", **When** matched, **Then** `bookwright-bible` activates and `bookwright-constitution` does not.
3. **Given** "revisa si mi manuscrito es coherente con la biblia" / "check my manuscript against the bible", **When** matched, **Then** `bookwright-continuity` activates and `bookwright-analyze` (the pre-draft sibling) does not.
4. **Given** "¿qué me falta por aclarar antes de seguir?" / "what's still unclear before I continue?", **When** matched, **Then** `bookwright-clarify` activates and `bookwright-checklist` (artifact-completeness, a different question) does not.

---

### User Story 4 - Heavy domain context is offloaded to references (Priority: P3)

Where a command needs extended domain material — the GOLEM character ontology, Propp's narrative functions, Greimas's actantial model — the body links to a file under `references/` instead of inlining the explanation, keeping every body within the tier-2 token budget while preserving access to the depth via tier-3 progressive disclosure.

**Why this priority**: It keeps prompts lean and maintainable, but the pipeline would function (less elegantly) even if every body were self-contained.

**Independent Test**: Confirm `src/bookwright/resources/commands/references/` exists with the auxiliary `.md` files the commands cite, that every body stays under 5000 tokens, and that each `references/…` path referenced by a body actually exists.

**Acceptance Scenarios**:

1. **Given** `bookwright-bible` needs to explain the GOLEM character fields, **When** read, **Then** its body links to a `references/` file rather than embedding the ontology inline.
2. **Given** `bookwright-scenes` or `bookwright-outline` invokes structural vocabulary (Propp / Greimas), **When** read, **Then** it links to the corresponding `references/` file.

---

### Edge Cases

- **Missing input information**: every generative command must distinguish *fill-with-marker* from *stop-and-ask*. The rule: when the brief simply lacks a field, mark `[PENDING: <pregunta en español>]` and continue; only halt to ask the author when proceeding would require inventing load-bearing canon (e.g. a protagonist's core motivation) that contradicts or cannot be derived from existing artifacts.
- **`[PENDING]` inside a string-typed frontmatter field** of a stamped mold (e.g. a character's `name`) must be quoted — `name: "[PENDING: …]"` — because bare `[…]` is YAML-parsed as a list.
- **Multi-POV vs single-POV**: `bookwright-bible` writes `bible/pov-structure.md` only when the constitution declares multiple POVs; the prompt states this condition.
- **Re-invocation / idempotency**: a generative command run twice on the same project MUST update in place — read the existing target, treat human-authored content and resolved `[PENDING]` answers as authoritative, fill only gaps and still-open `[PENDING: …]` markers, and never overwrite or duplicate authored prose. Each generative prompt states this explicitly.
- **Unknown `scene_id` / `artifact` argument**: `bookwright-draft` and `bookwright-checklist` must define what the agent does when the argument names something that does not exist (report and ask, not fabricate).
- **Empty or near-empty project**: a checking command (`analyze`, `continuity`, `checklist`) run before the relevant artifacts exist should report "nothing to check / prerequisite missing", not error opaquely.

## Requirements *(mandatory)*

### Functional Requirements

**Inventory & location**

- **FR-001**: The feature MUST deliver exactly 10 command source files at `src/bookwright/resources/commands/<name>.md`, one per command in design § 10.4: `bookwright-constitution`, `bookwright-bible`, `bookwright-outline`, `bookwright-scenes`, `bookwright-draft`, `bookwright-synopsis`, `bookwright-clarify`, `bookwright-analyze`, `bookwright-continuity`, `bookwright-checklist`.
- **FR-002**: Each file's base name MUST equal its command name (the future skill/parent-directory name), satisfying the agentskills.io constraint that `name` matches the parent directory (Constitution Principle VII).

**Frontmatter**

- **FR-003**: Each file MUST open with valid YAML frontmatter containing at minimum a `name` (= the command name) and a `description`.
- **FR-004**: Each `description` MUST be under 1024 characters and MUST contain explicit trigger phrasing for implicit activation, in **both Spanish and English**.
- **FR-005**: Frontmatter MUST NOT contain a `scripts:` block. CLI invocations are written inline in the body.
- **FR-006**: Frontmatter MUST remain integration-agnostic — no `handoffs:` block or other agent-specific keys in the source (those are injected during iteration-9 materialization).

**Body structure** — each body MUST contain these sections (Spanish prose):

- **FR-007**: Agent role/context — who the agent is for this command (e.g. "editor narrativo experimentado").
- **FR-008**: Expected input — what the command consumes, including any positional argument (`<scene_id>`, `<artifact>`). The source references the argument via the neutral placeholder `{ARGS}` and MUST NOT hard-code an agent-specific token (e.g. `$ARGUMENTS`); iteration-9 materialization maps `{ARGS}` to each agent's substitution syntax (FR-006). `{ARGS}` (single brace) is chosen so it survives Jinja-based materialization, unlike `{{…}}`.
- **FR-009**: A numbered step-by-step procedure.
- **FR-010**: Expected output — the report shape and/or the files produced.
- **FR-011**: "Files to read" — the concrete project paths the command consumes.
- **FR-012**: "Files to write" — the concrete project paths the command produces (or an explicit statement that the command is **report-only** and writes nothing).
- **FR-013**: The missing-information rule — when to mark `[PENDING: <pregunta>]` and continue vs when to stop and ask the author.
- **FR-014**: An explicit "do NOT" section listing the command's anti-goals.

**Token & marker conventions**

*Command classification (single source of truth, referenced throughout):* **generative** commands = `bookwright-constitution`, `bookwright-bible`, `bookwright-outline`, `bookwright-scenes`, `bookwright-draft`, `bookwright-synopsis` (they write project files); **report-only** commands = `bookwright-clarify`, `bookwright-analyze`, `bookwright-continuity`, `bookwright-checklist` (they write nothing). The marker and update-in-place rules below apply per this classification.

- **FR-015**: Each body MUST stay under 5000 tokens (agentskills.io tier-2 limit), measured with `tiktoken` when available, otherwise by a character-based approximation.
- **FR-016**: Generative commands MUST instruct the agent to emit the fill-marker as the exact token `[PENDING: <question>]` (English token, Spanish question), and to quote it when it lands in a string-typed YAML field.
- **FR-016a**: Each generative command MUST state an update-in-place rule: read any already-populated target, preserve human-authored content and resolved `[PENDING]` answers, fill only gaps and still-open `[PENDING: …]` markers, and never overwrite or duplicate authored prose. (`bookwright-synopsis` additionally regenerates its short/long version blocks to track current state while preserving any human content outside them — see FR-023.)

**CLI integration**

- **FR-017**: Any command that needs the project graph (at minimum `bookwright-constitution` and `bookwright-continuity`) MUST invoke `bookwright graph build --json` written inline in the body, and consume the JSON it returns. No command may assume a wrapper script.

**Per-command behavior** (each command's body MUST encode the contract from § 10.4):

- **FR-018**: `bookwright-constitution` reads the brief/conversation + constitution mold, writes `bible/constitution.md`, runs the graph build, and reports pending fields + activated vocabularies + the suggestion to run `bookwright-clarify` before `bookwright-bible`.
- **FR-019**: `bookwright-bible` reads constitution + brief and, in a **single invocation**, does a complete first pass over the full bible set — stamping the iteration-7 molds once per entity in a fixed order (constitution-derived entities first), writing each file as it goes, and marking thin entries `[PENDING: …]` rather than inventing canon. It ensures the entity directories `bible/characters/`, `bible/settings/`, and `bible/locations/` exist (creating any that are absent) before stamping. `bible/pov-structure.md` is *populated* only when the constitution declares multiple POVs; otherwise the command leaves a brief `POV único — no aplica` note (the file pre-exists from `init`).
- **FR-020**: `bookwright-outline` reads constitution + bible and writes `outline/arcs.md`, `outline/structure.md`, `outline/synopsis.md`.
- **FR-021**: `bookwright-scenes` reads outline + bible and writes `outline/scenes.md` with per-scene narrative function, characters present, location, and beats.
- **FR-022**: `bookwright-draft <scene_id>` reads outline + scene + bible and writes the scene into the correct `manuscript/cap-NN.md` section, honoring voice/focalization/constraints.
- **FR-023**: `bookwright-synopsis` (generative) updates `outline/synopsis.md` with a 250–350-word short version and a 1000–2000-word long version reflecting current project state. It regenerates those two version blocks on each run, preserves any human-authored content outside them, and marks `[PENDING: …]` where source material is missing rather than inventing plot.
- **FR-024**: `bookwright-clarify` reads any artifact and returns a question list; report-only.
- **FR-025**: `bookwright-analyze` reads constitution + bible + outline + scenes and reports pre-draft cross-artifact inconsistencies; report-only.
- **FR-026**: `bookwright-continuity` reads manuscript + bible, builds the graph, and reports bible-compliance + character-arc consistency + timeline coherence; report-only.
- **FR-027**: `bookwright-checklist <artifact>` reads one named artifact and reports completeness (sections present, no unfilled `[PENDING: …]`, no empty placeholders); report-only.

**Progressive disclosure**

- **FR-028**: A `src/bookwright/resources/commands/references/` directory MUST exist containing the auxiliary `.md` files the bodies cite for heavy domain context (e.g. GOLEM character fields, Propp functions, Greimas actants).
- **FR-029**: Every `references/…` path cited by a body MUST resolve to a file that exists in this iteration; no body may cite a missing reference.

**Validation (acceptance gating)**

- **FR-030**: Automated validation MUST confirm, for all 10 files: parseable frontmatter, `description` < 1024 chars, non-empty body, body < 5000 tokens, base name = command name, no `scripts:` block, and presence of the required body sections (FR-007–FR-014).

**Out of scope (must NOT appear in this iteration)**

- **FR-031**: This iteration MUST NOT produce any per-integration `SKILL.md`, MUST NOT write to `.claude/skills/` or `.agents/skills/`, and MUST NOT author the Python helper scripts a materialized skill might call — all deferred to iteration 9.

### Key Entities

- **Command source**: one authored `.md` under `resources/commands/` = YAML frontmatter (`name`, `description`) + structured Spanish body (role, input, procedure, output, read-files, write-files, missing-info rule, do-NOT). The source-of-truth for one slash command's logic.
- **Description**: the activation surface — a < 1024-char bilingual string whose phrasing both invites the correct request and disambiguates against sibling commands.
- **Reference file**: an auxiliary `.md` under `resources/commands/references/` holding extended domain context, linked from bodies for tier-3 progressive disclosure.
- **Fill-marker `[PENDING: <question>]`**: the stable English token (Spanish question) a generative command writes wherever the brief left a field unsupplied.
- **Project artifacts**: the read/write targets in an initialized project — `bible/`, `outline/`, `manuscript/` — produced by `init` (iter 4) and the iteration-7 molds.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 10 command source files exist at the prescribed paths and 10/10 pass the automated format validation (FR-030).
- **SC-002**: Every `description` is < 1024 characters and every body is < 5000 tokens (10/10).
- **SC-003**: In a hand-run activation A/B battery of at least the four scenarios in User Story 3, the intended command is the unambiguous top match and the named sibling does not over-trigger, in both Spanish and English (8/8 phrasings, ES+EN).
- **SC-004**: A competent reviewer reading `bookwright-constitution.md` end-to-end confirms it is executable against a fresh project with no ambiguity (the iteration's stated acceptance criterion), and the same holds for a spot-check of one report-only command (`bookwright-continuity`).
- **SC-005**: 100% of `references/…` paths cited across the 10 bodies resolve to files shipped in this iteration (no dangling references).
- **SC-006**: Each of the 10 bodies contains all eight required sections (role, input, procedure, output, read-files, write-files, missing-info rule, do-NOT) — verifiable by section presence.
- **SC-007**: Zero out-of-scope artifacts are introduced — no `SKILL.md`, no writes under any `skills_dir`, no helper Python — confirmed by inspection of the diff.

## Assumptions

- **Fill-marker spelling**: the prompt text (and design § 10.1) says `[PENDIENTE]`, but iteration 7 standardized the project on `[PENDING: <question>]` (English token, Spanish question). This spec adopts `[PENDING: …]` so all artifacts share one marker; `[PENDIENTE]` is treated as superseded.
- **Body language**: command bodies are written in **Spanish** prose (matching the § 10.1 example and iteration-7 templates); frontmatter keys are English; descriptions are bilingual to drive activation in both languages. This follows the project's bilingual convention (Spanish prose, English code/identifiers).
- **No `handoffs:` in source**: the § 10.1 `handoffs` block illustrates an eventual *materialized* Claude skill, not the integration-agnostic source. Per-integration affordances are injected in iteration 9. (Confirmed in `/speckit-clarify`, Session 2026-06-01; "next step" hints may still appear as body prose, not frontmatter.)
- **Molds already exist**: the re-instanceable templates the generative commands stamp (`character.md.tmpl`, `setting.md.tmpl`, `location.md.tmpl`, `scene.md.tmpl`, `chapter.md.tmpl`) and the project skeleton (`bible/`, `outline/`, `manuscript/`) were authored in iterations 4 and 7 and are consumed, not re-created, here.
- **CLI subcommands already exist**: `bookwright graph build --json` (iteration 6) and the `init` skeleton (iteration 4) are present on `main`; this iteration only references them, it does not implement them.
- **Reference file set**: the exact roster under `references/` (e.g. `golem-character.md`, `propp-functions.md`, `greimas-actants.md`) is finalized during planning/implementation from what the bodies actually cite; the binding rule is FR-029 (no dangling references), not a fixed list.
- **`manuscript/cap-NN.md` granularity**: `bookwright-draft` writes the scene into the chapter file/section implied by the scene's `scene_id` and the outline's structure; the precise filename mapping follows the iteration-7 chapter mold and the scenes list, not a new numbering scheme invented here.
- **Skeleton `bible/locations/`**: the iteration-4 `init` skeleton on `main` ships `bible/characters/` and `bible/settings/` but not `bible/locations/`, despite a `location.md.tmpl` mold existing. `bookwright-bible` creates `bible/locations/` defensively (FR-019); restoring skeleton symmetry (`bible/locations/.gitkeep`) is a separate iteration-4 hygiene fix, tracked outside this iteration's diff.
