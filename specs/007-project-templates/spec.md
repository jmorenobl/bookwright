# Feature Specification: Bible / Outline / Constitution Templates

**Feature Branch**: `007-project-templates`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: Iteration 7 of `bookwright-implementation-plan.md` — author the Markdown templates that guide the human author and the AI agent on what to fill in and in what format, across `bible/`, `outline/`, the narrative `constitution.md`, and the project shell. See `bookwright-design.md` § 9 (constitution), § 6 (template layout), § 17.2 (preset analysis).

## Context & Layout Decision *(read first)*

This iteration is **document authoring**, not code. It writes the intellectual artifacts an author and the AI agent see first in any new Bookwright project.

A layout decision was settled with the project owner before writing this spec. The design doc § 6 envisions a single `resources/templates/*.tmpl` directory resolved through a 4-layer `resolve_template()` (overrides → presets → extensions → core). That resolver only ever existed to serve **presets (v0.2)** and **extensions (v0.5)**, which the project owner does not expect to implement. The 4-layer resolver therefore has no future use, and § 6's unified layout is treated as obsolete for v0.

Templates are instead organized by **lifecycle**, matching what the already-shipped iteration-4 `init` actually does:

- **`src/bookwright/resources/project/`** — the project skeleton `bookwright init` stamps **once** per project (its walker renders `.j2` via Jinja2 and byte-copies everything else, recursively). Today these files are placeholder stubs that literally say *"Placeholder — iteration 7 lands the full template."* This iteration replaces those stubs with the real authored content.
- **`src/bookwright/resources/templates/`** — re-instanceable **molds** that the agent commands (iterations 8-9) stamp **many** times (one per character, per setting, per location, per scene, per chapter). These must live outside `project/` precisely because `init`'s walker would otherwise stamp a literal `*.tmpl` file into every new project. In v0 they are read directly (no layering).

This split is the permanent v0 architecture, not a temporary compromise. (`§ 6` of the design is now superseded; the divergence is recorded in the CHANGELOG per FR-021.)

## Clarifications

### Session 2026-06-01

- Q: What language should the templates' human-facing prose use? → A: Spanish for all human-facing scaffolding prose (section headings, HTML-comment guidance, `[PENDIENTE]` questions), including the authored `README.md.j2` guidance; frontmatter **keys** and the `[PENDIENTE]` token stay English (parser contract). The verify-only `manifest.template.toml` (FR-025) keeps its existing English comments.
- Q: Should templates ship blank, or with a worked example? → A: Blank scaffold plus a short worked example tucked inside HTML `<!-- -->` comments — invisible when read as plain Markdown, never indexed, never tripping the stub-sentinel check. For the indexer-ingested collection files (`timeline.md`, `relationships.md`), the example entries live in HTML comments so the shipped frontmatter list stays empty.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A new project ships a complete, fill-in-ready narrative skeleton (Priority: P1)

An author runs `bookwright init my-book` and immediately finds, under `bible/` and `outline/`, a full set of structured documents — the narrative constitution, timeline, relationships, themes, glossary, research log, subplots, POV structure, and the four outline documents — each laid out with clear sections, instructions, and `[PENDIENTE: <question>]` prompts that tell the author and the agent exactly what to fill in. No file contains a leftover "placeholder, coming later" stub.

**Why this priority**: This is the headline value of the iteration — the templates are the most visible intellectual surface of the product. Without it, every freshly-initialized project ships broken stubs.

**Independent Test**: Run `bookwright init` into a temp dir; assert every stamped `bible/*.md`, `bible/constitution.md`, and `outline/*.md` is non-empty real content, carries section headings and HTML-comment guidance, and contains no stub sentinel (`Placeholder — iteration 7`, `{{TODO}}`, etc.).

**Acceptance Scenarios**:

1. **Given** a clean directory, **When** `bookwright init` runs, **Then** `bible/constitution.md` contains all § 9.2 sections (voice/register, reader pact, historical-fictional pact, red lines, coherence invariants, active vocabularies, agent notes) with `[PENDIENTE: …]` prompts.
2. **Given** the same project, **When** the author opens any `bible/` or `outline/` document in a plain text editor, **Then** it reads as clean, sensible Markdown without needing a renderer.
3. **Given** any shipped template, **When** scanned for sentinel strings, **Then** no `Placeholder — iteration 7`, `{{TODO}}`, or unresolved scaffolding marker remains.

---

### User Story 2 - Templates round-trip cleanly through the graph indexer (Priority: P1)

The documents whose frontmatter the iteration-6 indexer ingests — the `character` and `setting` molds, and the `timeline.md` / `relationships.md` collection files — use exactly the frontmatter keys the mapper recognizes, so a freshly-initialized project indexes with zero errors and zero spurious warnings, and a filled-in character/setting maps to a GOLEM entity.

**Why this priority**: The frontmatter contract is the only machine-verifiable part of the deliverable and the project's stated validation gate. A template that the indexer chokes on or floods with `unknown_keys` warnings is a defect, however good its prose.

**Independent Test**: Build the graph (`bookwright graph build`) on (a) a freshly-`init`-ed project and (b) a fixture where the character/setting molds have been stamped and filled; assert zero `invalid_frontmatter` skips, zero `unknown_keys` warnings on canonical fields, zero `unresolved_participants`, and that filled instances produce the expected Character/Setting/NarrativeEvent/SocialRelationship entities.

**Acceptance Scenarios**:

1. **Given** the shipped `bible/timeline.md` and `bible/relationships.md`, **When** a fresh project is indexed, **Then** their frontmatter parses as valid YAML with empty `events: []` / `relationships: []` lists, producing zero entities and zero warnings.
2. **Given** the `character.md.tmpl` mold, **When** its frontmatter is inspected, **Then** it uses only keys in `{name, born, died, features, narrative_roles}`, with `born`/`died` left null or omitted (never a non-integer placeholder) and `features`/`narrative_roles` as YAML string lists.
3. **Given** a filled character file stamped from the mold into `bible/characters/`, **When** indexed, **Then** it maps to one `Character` entity with the declared name, optional birth/death years, features, and narrative roles.
4. **Given** the `setting.md.tmpl` mold, **When** inspected, **Then** its frontmatter carries `name` and no other indexer-ingested key.

---

### User Story 3 - Re-instanceable molds are ready for the authoring commands (Priority: P2)

The repeated-instance documents — `character`, `setting`, `location`, `scene`, and `chapter` — exist as `.tmpl` molds under `resources/templates/`, each with the structure the agent needs to stamp a fresh, well-formed instance: required GOLEM-aligned frontmatter where the indexer reads it, and rich prose sections (with HTML-comment craft guidance) where it does not.

**Why this priority**: These molds are consumed by iterations 8-9. They are not stamped by `init`, so they don't affect a fresh project, but they must be authored now so the command work can build on them. Lower than P1 because nothing reads them yet (no defect ships if they lag), but they are core scope.

**Independent Test**: For each `.tmpl` under `resources/templates/`, assert it parses without `yaml.YAMLError`, contains its required named sections, and (for `character`/`setting`) uses indexer-recognized frontmatter keys.

**Acceptance Scenarios**:

1. **Given** `character.md.tmpl`, **When** opened, **Then** it has prose sections for biographical, psychological, and physical features, narrative role, sample dialogue, and body-language patterns, plus the indexer-significant frontmatter.
2. **Given** `location.md.tmpl`, **When** opened, **Then** it has sensory-anchor sections (sight, sound, smell, touch, dominant atmosphere); its frontmatter (if any) is valid YAML and — since v0's indexer has no `locations/` handler — is documented as not ingested.
3. **Given** `scene.md.tmpl` and `chapter.md.tmpl`, **When** opened, **Then** each carries a scene/chapter structure usable as a starting point for drafting.

---

### User Story 4 - Every template guides both a human and an AI agent (Priority: P3)

Each authored document carries HTML `<!-- -->` comments with instructions for the human author or the AI agent, `[PENDIENTE: <question>]` placeholders for content the agent must elicit and fill, and minimal YAML frontmatter only where it carries meaning. The result is legible as plain Markdown and is original Bookwright prose adapted to the GOLEM model — inspired by, but not copied from, the MIT-licensed `fiction-book-writing` preset, with that inspiration credited in the CHANGELOG.

**Why this priority**: This is a cross-cutting quality bar over Stories 1-3 rather than a separable slice; it is verifiable but does not, on its own, deliver a runnable artifact.

**Independent Test**: Lint every authored template for: presence of at least one HTML-comment instruction block, `[PENDIENTE: …]` prompts in author-fill sections, valid YAML frontmatter where present, and absence of verbatim preset text.

**Acceptance Scenarios**:

1. **Given** any authored template, **When** scanned, **Then** it contains author/agent guidance in HTML comments that do not render as visible prose.
2. **Given** the CHANGELOG, **When** read, **Then** it credits the `fiction-book-writing` preset (adaumann, MIT) as structural inspiration and notes the redaction is original to Bookwright (Apache-2.0).

### Edge Cases

- **Unfilled parser-significant frontmatter**: A shipped `timeline.md` / `relationships.md` must index to zero entities (empty lists), never raise on a `[PENDIENTE]` string sitting in a typed field. Typed fields (`born`, `died`) must be null/omitted, never a placeholder string, or `_coerce_year` rejects the file.
- **Placeholder text vs. machine fields**: `[PENDIENTE: …]` prompts belong in prose or in string-typed frontmatter values, never in integer/list-typed frontmatter values that the indexer coerces.
- **`init` walker semantics**: Skeleton files under `project/` must keep `.md` / `.j2` extensions (never `.tmpl`), because the walker byte-copies any non-`.j2` file verbatim — a `.tmpl` extension would be stamped literally into the project.
- **Jinja2 rendering**: Files under `project/` ending in `.j2` are rendered with `StrictUndefined`; any `{{ variable }}` they use must be one the scaffold context provides (`title`, `project_slug`, `author`, `language`, `integration_key`) or `init` aborts.
- **Locations not indexed in v0**: `location.md.tmpl` frontmatter is not mapped to a GOLEM entity (no `locations/` handler in iteration 6); this is intended, and the template must not imply otherwise.
- **Multi-POV optionality**: `pov-structure.md` ships in every project but is only meaningful for multi-POV works; its guidance must say so rather than forcing single-POV authors to fill it.

## Requirements *(mandatory)*

### Functional Requirements

**Project skeleton (stamped once by `init`, authored in `resources/project/`)**

- **FR-001**: `bible/constitution.md.j2` MUST be a full narrative-contract template covering all `bookwright-design.md` § 9.2 sections: narrative voice, register, reader pact, historical-fictional pact (clearly marked optional), red lines, coherence invariants, active vocabularies, and agent notes — each with `[PENDIENTE: <question>]` prompts and HTML-comment guidance.
- **FR-002**: `bible/timeline.md` MUST ship with YAML frontmatter whose top-level key is `events`, set to an empty list, so a fresh project indexes to zero `NarrativeEvent`s with zero warnings; the body MUST document the per-event shape (`name`, optional `participants` referencing character slugs).
- **FR-003**: `bible/relationships.md` MUST ship with frontmatter whose top-level key is `relationships`, set to an empty list; the body MUST document the per-relationship shape (`name`, `participants`).
- **FR-004**: `bible/themes.md` MUST provide a motif registry, a symbol tracker, and a chapter thematic map.
- **FR-005**: `bible/glossary.md` MUST provide an invented-terms register, capitalization rules, and a consistency log.
- **FR-006**: `bible/research.md` MUST provide open questions, source notes, and resolved findings.
- **FR-007**: `bible/subplots.md` MUST provide subplot beat sheets and intersection points with the main plot.
- **FR-008**: `bible/pov-structure.md` MUST cover narrative mode, POV schedule, voice differentiation, and an information-asymmetry map, and MUST state that it applies only to multi-POV works.
- **FR-009**: `outline/arcs.md`, `outline/structure.md`, `outline/scenes.md` MUST each provide a usable structural template; `outline/synopsis.md` MUST provide both a short synopsis (250–350 words) and a long synopsis (1000–2000 words) section.
- **FR-010**: `README.md.j2` MUST be a brief human guide explaining how to work with Bookwright and this project (where to start, what each directory holds, key commands), rendering correctly with the scaffold's Jinja2 context.
- **FR-011**: `.gitignore` MUST be appropriate for a Bookwright project (cache, Python artifacts, virtualenv, env files); the existing content MUST be reviewed and kept or extended, not regressed.

**Re-instanceable molds (stamped many times by commands, authored in `resources/templates/`)**

- **FR-012**: `bible/character.md.tmpl` MUST carry indexer-significant frontmatter restricted to `{name, born, died, features, narrative_roles}` and prose sections for biographical, psychological, and physical features, narrative role, sample dialogue, and body-language patterns. The user-facing concept of "age" MUST be expressed via `born`/`died` years (the indexer's model) and/or prose, never as a non-integer frontmatter value.
- **FR-013**: `bible/setting.md.tmpl` MUST carry frontmatter with `name` (the only indexer-ingested key) and prose sections for the broad narrative universe (culture, system/era, wide geography).
- **FR-014**: `bible/location.md.tmpl` MUST provide sensory-anchor sections (what is seen, heard, smelled, touched, and the dominant atmosphere); its frontmatter, if present, MUST be valid YAML and the template MUST NOT imply it is indexed in v0.
- **FR-015**: `manuscript/chapter.md.tmpl` MUST provide a chapter structure suitable as a drafting starting point.
- **FR-016**: A scene mold MUST be authored under `resources/templates/scenes/scene.md.tmpl` with a usable scene structure.

**Cross-cutting authoring rules**

- **FR-017**: Every authored template MUST be readable directly as plain Markdown without rendering. Human-facing scaffolding prose (section headings, body labels, HTML-comment guidance, and `[PENDIENTE]` questions) MUST be written in Spanish; frontmatter keys and the `[PENDIENTE]` token itself MUST remain in English (parser contract). The already-shipped English `README.md.j2` and `manifest.template.toml` are unaffected, but the README's authored guidance prose follows the Spanish rule.
- **FR-018**: Every authored template MUST include HTML `<!-- -->` comments carrying instructions for the human author or AI agent; these MUST NOT render as visible body prose. Each template MUST also include a short worked example demonstrating the expected shape, placed **inside** HTML comments so it never renders, never indexes, and never trips the stub-sentinel check (FR-022). For `timeline.md` / `relationships.md`, example entries MUST live in HTML comments while the shipped frontmatter `events:` / `relationships:` lists stay empty (FR-002, FR-003).
- **FR-019**: Sections the agent must populate from a narrative brief MUST use `[PENDIENTE: <question>]` placeholders phrased as the question to answer.
- **FR-020**: YAML frontmatter MUST appear only where it carries meaning, MUST be parseable by the iteration-6 frontmatter reader without `yaml.YAMLError`, and — for the four indexer-ingested concepts (character, setting, timeline, relationships) — MUST use only mapper-recognized keys so a stamped, filled instance produces zero `unknown_keys` warnings on canonical fields.
- **FR-021**: The CHANGELOG MUST credit the `fiction-book-writing` preset (adaumann, MIT) as structural inspiration, state that Bookwright's redaction is original (Apache-2.0) and adapted to the GOLEM model, and note that this iteration supersedes the unified-template layout described in design § 6 in favor of the lifecycle split.
- **FR-022**: No shipped or authored file may retain a stub/scaffolding sentinel (`Placeholder — iteration 7 lands the full template`, `{{TODO}}`, or equivalent).

**Explicitly out of scope**

- **FR-023**: This iteration MUST NOT modify `init` copy logic (iteration 4) or the frontmatter/bible parser (iteration 6); it MUST conform templates to their existing contracts.
- **FR-024**: This iteration MUST NOT author or build `resolve_template()`, presets, extensions, or any 4-layer resolution plumbing.
- **FR-025**: `manifest.toml.tmpl` is already satisfied by the shipped, commented `resources/templates/manifest.template.toml` (wired into `Manifest.build`); this iteration MUST only verify it covers all manifest fields with comments, not re-author it.

### Key Entities

- **Project skeleton template**: A `.md` / `.j2` document under `resources/project/`, stamped once per project by `init`. Examples: constitution, timeline, relationships, themes, glossary, research, subplots, pov-structure, the four outline docs, README, `.gitignore`.
- **Re-instanceable mold**: A `.tmpl` document under `resources/templates/`, stamped repeatedly by agent commands. Examples: character, setting, location, scene, chapter.
- **Indexer-significant frontmatter**: The YAML keys the iteration-6 mapper ingests — `{name, born, died, features, narrative_roles}` for a character (in `bible/characters/`), `{name}` for a setting (in `bible/settings/`), an `events:` list for `timeline.md`, a `relationships:` list for `relationships.md`. All other frontmatter is valid YAML but not mapped to a GOLEM entity in v0.
- **Authoring guidance**: The HTML-comment instructions and `[PENDIENTE: <question>]` placeholders that direct the human author and AI agent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A freshly `bookwright init`-ed project contains zero files bearing a stub sentinel; every `bible/` and `outline/` document is real, non-empty authored content. (100% of stamped documents.)
- **SC-002**: Building the graph on a freshly-initialized project yields zero `invalid_frontmatter` skips, zero `unknown_keys` warnings, and zero `unresolved_participants`.
- **SC-003**: Every authored template file — both skeleton and molds — parses through the iteration-6 frontmatter reader without raising; 100% pass a format smoke test.
- **SC-004**: A character file stamped from `character.md.tmpl` and filled with a name, years, features, and roles maps to exactly one `Character` GOLEM entity carrying those attributes; the equivalent holds for `setting.md.tmpl` → `Setting`.
- **SC-005**: Every authored template contains at least one HTML-comment guidance block and renders/reads sensibly as plain Markdown (verified by inspection of all files).
- **SC-006**: The CHANGELOG credits the preset inspiration and records the § 6 layout supersession.
- **SC-007**: Test coverage gates do not apply to this iteration's prose deliverables (per the implementation plan); validation is by format/completeness/round-trip tests rather than line coverage.

## Assumptions

- **Lifecycle split is authoritative**: Skeleton documents go in `resources/project/` (filling iteration-4 placeholders); re-instanceable molds go in `resources/templates/`. This was confirmed with the project owner and supersedes design § 6's single-directory layout, on the basis that presets/extensions (the resolver's only justification) are not expected to ship.
- **Skeleton file extensions are fixed by the walker**: Files in `project/` keep `.md` (byte-copied) or `.j2` (Jinja2-rendered). The user prompt's generic `.tmpl` naming maps to: `.md`/`.j2` for skeleton singletons, `.tmpl` only for re-instanceable molds in `resources/templates/`.
- **Constitution stays `.j2`**: `constitution.md.j2` keeps its Jinja2 extension because it interpolates `{{ title }}` from the scaffold context; the expanded template continues to use only context-provided variables.
- **Locations are not indexed in v0**: Iteration 6 has no `bible/locations/` handler, so `location.md.tmpl` frontmatter is for human/agent use only.
- **`pov-structure.md` ships unconditionally**: `init` does not branch on multi-POV, so the document ships in every project with guidance that it applies only to multi-POV works.
- **Manifest template is pre-existing**: `resources/templates/manifest.template.toml` already satisfies the "commented manifest" need and is wired into `Manifest.build`; only verification is in scope.
- **Template prose is Spanish; keys and spec are English** (per Clarification Q1): human-facing scaffolding prose in the templates (headings, HTML-comment guidance, `[PENDIENTE]` questions, authored README guidance) is Spanish; frontmatter keys, the `[PENDIENTE]` token, this spec, and the verify-only `manifest.template.toml` comments stay English.
- **Preset is studied, not fetched as a dependency**: the `fiction-book-writing` document inventory is taken from design § 17.2 (which already enumerates what to adopt); optionally consulting adaumann's MIT repo read-only for structure is allowed but not a build/runtime dependency, and no preset text is copied verbatim (FR-021).
- **Dependencies**: Iteration 4 (`init` scaffold walker) and iteration 6 (frontmatter reader + bible mapper) are merged on `main` and define the contracts this iteration conforms to.
