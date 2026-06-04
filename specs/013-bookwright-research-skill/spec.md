# Feature Specification: `bookwright-research` Skill + `bible/research/`

**Feature Branch**: `013-bookwright-research-skill`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "Necesidad: investigar es parte del proceso de escritura. El autor necesita un command que, dado un tema (p. ej. «detectives privados en España» o «logística de la Wehrmacht en 1943»), guíe al agente para investigar con rigor y deje los hallazgos estructurados, con procedencia, anclados al grafo."

## Clarifications

### Session 2026-06-04

- Q: Default value of `[research].source_languages` in a freshly `init`-ed
  manifest? → A: Empty list `[]` — no declared provenance preference baked into
  the generic scaffold; the protocol's original-language rule still applies, and
  the author adds languages per topic.
- Q: Should `bookwright init` write an explicit `[research]` block into the
  generated `manifest.toml` or rely on model defaults? → A: Write the block with
  the documented defaults and explanatory comments (discoverable, self-documenting,
  consistent with the other scaffolded blocks); the loader still applies the same
  defaults when the block is absent.
- Q: After writing the research files, should the skill instruct the agent to run
  `bookwright graph build`? → A: Yes — the skill's final step instructs
  `bookwright graph build --json` so findings and anchors land in `bible/graph.ttl`
  immediately, consistent with the other content-producing commands.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guided rigorous research into structured, provenanced findings (Priority: P1)

An author working on a historically-grounded novel needs to research a topic
(e.g. "private detectives in Spain" or "Wehrmacht logistics in 1943"). Instead
of asking the agent to improvise, they invoke `/bookwright-research <topic>`. The
skill walks the agent through a disciplined protocol — decompose the topic into
verifiable sub-questions, prefer primary/official sources in their original
language, deliberately contrast multiple national provenances for charged topics,
record every finding with full provenance (including the original-language
quotation), keep conflicting versions side by side rather than collapsing them,
mark which findings are binding anchors and which narrative entity they constrain,
and leave unresolved questions open. The result is written to
`bible/research/<topic>.md` (with `_index.md` and `sources.md` updated) in the
exact plain-text shape the research reader can parse, and the skill finishes by
reindexing the graph so the findings and anchors are immediately queryable.

**Why this priority**: This is the heart of the feature — the whole iteration
exists to give the author a research command that produces graph-ready, provenance
-complete findings. Without it the other slices have nothing to configure or
scaffold around.

**Independent Test**: Run `bookwright init`, confirm a valid `bookwright-research`
skill is materialized; then run the skill manually inside an agent against a
sample topic and confirm it produces a `bible/research/<topic>.md` that
`bookwright graph build` parses without error and from which a SPARQL query
retrieves at least one anchor constraining a named entity. Delivers the complete
research-to-graph loop on its own.

**Acceptance Scenarios**:

1. **Given** a freshly `init`-ed project, **When** the author invokes
   `/bookwright-research "logística de la Wehrmacht en 1943"`, **Then** the agent
   is guided through the seven-step protocol and writes
   `bible/research/logistica-de-la-wehrmacht-en-1943.md` plus updated `_index.md`
   and `sources.md`, all in the format the research reader parses.
2. **Given** a topic with nationally-divergent accounts, **When** the agent
   records its findings, **Then** each conflicting version is preserved with its
   own source and provenance instead of being merged into a single "truth".
3. **Given** a finding the author wants binding, **When** the agent marks it as an
   anchor, **Then** the file records which narrative entity (character, setting,
   event, or timeline) the anchor constrains.
4. **Given** sub-questions the agent could not resolve, **When** it finishes,
   **Then** those questions are left explicitly open in the topic file and surface
   in `_index.md`.
5. **Given** the research files have been written, **When** the skill reaches its
   final step, **Then** it instructs the agent to run `bookwright graph build
   --json`, after which the new findings and anchors are present in
   `bible/graph.ttl` and retrievable by a SPARQL query.

---

### User Story 2 - Configure the research system per project (Priority: P2)

A project lead wants to control how research behaves: whether it is enabled at
all, which source provenances (languages) the protocol should deliberately seek,
and the minimum source reliability required before a finding may be promoted to a
binding anchor. They edit a `[research]` block in `manifest.toml`. A project that
does not research at all pays no cost: the block is optional and defaults are
safe.

**Why this priority**: Configuration shapes the protocol's behavior and gates
anchor promotion, but the skill is usable with defaults, so this rides just below
the core skill.

**Independent Test**: Load a manifest with a `[research]` block and confirm the
parsed model exposes `enabled`, `source_languages`, and
`min_reliability_for_anchor`; load a manifest without the block and confirm it
parses with defaults applied; load a manifest with an invalid
`min_reliability_for_anchor` and confirm it is rejected with a clear error.

**Acceptance Scenarios**:

1. **Given** a `manifest.toml` with `[research] enabled = false`, **When** it is
   loaded, **Then** the research system is inert and no research behavior is
   expected of the skill.
2. **Given** a `manifest.toml` with no `[research]` block, **When** it is loaded,
   **Then** parsing succeeds and the documented defaults apply.
3. **Given** `min_reliability_for_anchor` set to a value outside the reliability
   scale, **When** the manifest is loaded, **Then** a validation error is raised
   naming the offending field.
4. **Given** a finding whose best supporting source falls below
   `min_reliability_for_anchor`, **When** the agent follows the protocol, **Then**
   it is recorded as a finding (and may stay open) but is **not** promoted to an
   anchor.

---

### User Story 3 - `bible/research/` scaffolding and bible integration (Priority: P3)

A new project should start with a `bible/research/` directory (an `_index.md` map
of topics and global open questions, plus a `sources.md` registry) instead of the
old single `bible/research.md` file. `/bookwright-bible` creates
`bible/research/_index.md`, and the per-topic / sources / index templates are
layer-resolvable (project override → packaged core) exactly like every other
project template. `/bookwright-clarify` keeps gathering the open research
questions.

**Why this priority**: This wires research into the existing bible workflow and
template machinery. It depends on the format from US1 and is the lowest-risk slice
to land last.

**Independent Test**: Run `bookwright init` and confirm `bible/research/` exists
with `_index.md` and `sources.md` rendered from templates (and no stray
`bible/research.md`); confirm an override template in the project's template dir
is preferred over the packaged one; run `/bookwright-bible` and confirm it writes
`bible/research/_index.md`; run `/bookwright-clarify` and confirm open research
questions are collected.

**Acceptance Scenarios**:

1. **Given** a freshly `init`-ed project, **When** the scaffold is inspected,
   **Then** `bible/research/_index.md` and `bible/research/sources.md` exist and
   the legacy `bible/research.md` does not.
2. **Given** a project that overrides the research index template, **When** the
   template is resolved, **Then** the override is used in preference to the
   packaged default.
3. **Given** an author runs `/bookwright-bible`, **When** it produces the bible,
   **Then** it creates `bible/research/_index.md` (not `bible/research.md`).

---

### Edge Cases

- **Topic name with spaces, accents, or punctuation**: the topic is reduced to a
  filesystem-safe slug for `<topic>.md` while the human-readable title is
  preserved inside the file and `_index.md`.
- **Re-running on an existing topic**: the skill updates the existing
  `bible/research/<topic>.md`, `_index.md`, and `sources.md` rather than silently
  clobbering prior findings and their provenance.
- **The agent cannot locate authoritative sources**: the corresponding
  sub-questions are left open rather than backfilled with unsourced claims.
- **Research disabled (`enabled = false`)**: the skill informs the author the
  research system is inert and does not produce graph-bound findings.
- **A finding supported only by a low-reliability source**: it is recorded but not
  promoted to an anchor (US2 scenario 4).
- **Conflicting sources of equal weight**: every version is retained with its own
  provenance; the protocol never picks a single winner silently.
- **Original-language quotation differs from the book's language**: both the
  original-language citation and (where applicable) a translation are recorded, as
  the research format requires.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A new source command `bookwright-research.md` MUST exist in the
  packaged `resources/commands/` directory, following the command-source format
  (design § 10.1) used by the existing ten v0.1 commands.
- **FR-002**: The command MUST be materialized as an Agent Skill (`SKILL.md`) for
  both the `claude` (`.claude/skills/`) and `generic` (`.agents/skills/`)
  integrations, **reusing the existing skill-materialization pipeline** (iteration
  9); no parallel pipeline is introduced.
- **FR-003**: The generated `SKILL.md` MUST satisfy agentskills.io limits — `name`
  < 64 chars matching its parent directory, `description` < 1024 chars, valid YAML
  front-matter — i.e. pass the existing `lint_skill_md` gate.
- **FR-004**: The skill MUST be triggerable from both Spanish and English author
  prompts.
- **FR-005**: The `SKILL.md` MUST encode the seven-step research protocol: (1)
  decompose the topic into concrete, verifiable sub-questions; (2) seek
  authoritative sources with explicit preference for **primary and official
  sources in their original language**; (3) for nationally-charged topics,
  deliberately consult sources of **several provenances** rather than one; (4)
  record each finding with **complete provenance**, including the original-language
  quotation; (5) when sources disagree, record **each version with its provenance**
  instead of collapsing them; (6) mark which findings are **anchors** and to which
  narrative entity they link; (7) leave unresolved questions **open**.
- **FR-006**: The skill MUST instruct the agent to write results to
  `bible/research/<topic>.md` and to update `bible/research/_index.md` and
  `bible/research/sources.md`, in the exact plain-text format the research reader
  (`io/research.py`, iteration 13) parses.
- **FR-007**: The skill MUST NOT implement source fetching, bundle a search
  engine, or introduce any network/runtime dependency; the search capability is
  supplied by the agent. The skill **instructs**; it does not fetch.
- **FR-008**: Templates for `bible/research/` (`_index.md`, `sources.md`,
  per-`<topic>` skeleton) MUST be added to the packaged resources and be
  layer-resolvable (project override → packaged core), like the iteration-7
  templates.
- **FR-009**: `/bookwright-bible` MUST create `bible/research/_index.md` instead of
  the legacy single `bible/research.md`.
- **FR-010**: `/bookwright-clarify` MUST continue to collect open research
  questions.
- **FR-011**: The manifest model (iteration 2) MUST be extended with an optional
  `[research]` block exposing `enabled` (default `true`), `source_languages`
  (default `[]`, the empty list), and `min_reliability_for_anchor` (default
  `"media"`).
- **FR-012**: A manifest with no `[research]` block MUST load successfully with the
  documented defaults applied; with `enabled = false` the research system MUST be
  inert.
- **FR-013**: The `[research]` block MUST validate `min_reliability_for_anchor`
  against the controlled reliability scale and reject unknown values with a clear,
  field-naming error.
- **FR-014**: `bookwright init` MUST scaffold (a) a valid `bookwright-research`
  skill in both integrations and (b) a `bible/research/` directory containing
  `_index.md` and `sources.md` rendered from the templates.
- **FR-014a**: `bookwright init` MUST write an explicit `[research]` block — with
  the documented defaults (`enabled = true`, `source_languages = []`,
  `min_reliability_for_anchor = "media"`) and explanatory comments — into the
  generated `manifest.toml`, while the loader MUST still apply those same defaults
  when the block is absent (FR-012). The written comments MUST survive the
  `tomlkit` round-trip.
- **FR-015**: The protocol MUST honour `min_reliability_for_anchor`: a finding
  whose best supporting source is below the configured threshold MUST NOT be
  promoted to an anchor (it stays a finding, possibly open).
- **FR-016**: The protocol MUST consult `[research].source_languages` as
  informative guidance for the multilingual-provenance step (steps 2–3).
- **FR-017**: Re-invoking the skill on an existing topic MUST update the topic
  file, `_index.md`, and `sources.md` without discarding previously recorded
  findings or their provenance.
- **FR-018**: The skill's final step MUST instruct the agent to run `bookwright
  graph build --json` after writing the research files, so the new findings and
  anchors are reflected in `bible/graph.ttl`. This mirrors the persistence step of
  the other content-producing commands; the skill itself still adds no fetch logic
  or network dependency (FR-007).

### Key Entities *(include if feature involves data)*

- **`bookwright-research` source command / skill**: the Markdown command source in
  `resources/commands/` and the `SKILL.md` it materializes into per integration.
  Carries the seven-step protocol and trigger phrasing (ES + EN).
- **Research topic file (`bible/research/<topic>.md`)**: per-topic plain-text file
  with structured front-matter (findings + anchors, parseable by the research
  reader) and human-readable prose below.
- **Research index (`bible/research/_index.md`)**: map of research topics plus the
  global list of open questions.
- **Sources registry (`bible/research/sources.md`)**: consolidated provenance
  record of all sources cited across topics.
- **`[research]` manifest block**: project configuration — `enabled`,
  `source_languages`, `min_reliability_for_anchor`.
- **Finding / Anchor / Source** *(defined in iteration 13, not redefined here)*:
  the provenance entities the produced files encode and the reader emits into the
  graph. This iteration depends on their format; it does not change it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `bookwright init` generates a `bookwright-research` skill that passes
  skill validation (agentskills.io limits) in **both** the `claude` and `generic`
  integrations — 100 % of generated skills valid.
- **SC-002**: A project manifest with a `[research]` block loads with zero errors,
  and a manifest without one loads with defaults applied — both verifiable without
  inspecting implementation. A freshly `init`-ed `manifest.toml` contains a
  `[research]` block carrying the documented defaults, and its explanatory comments
  survive a load-and-save round-trip.
- **SC-003**: Running the skill manually in an agent against a sample topic
  produces a `bible/research/<topic>.md` that `bookwright graph build` parses
  without error and from which a SPARQL query retrieves at least one anchor
  constraining a named narrative entity.
- **SC-004**: 100 % of findings recorded by the protocol carry complete provenance
  (source reference and original-language quotation) as required by the research
  format — verifiable on the produced file against the reader's required fields.
- **SC-005**: For a topic with conflicting sources, both versions appear in the
  produced file, each with its own provenance — no silent collapse to a single
  account.
- **SC-006**: A finding whose best source is below `min_reliability_for_anchor` is
  never emitted as an anchor — 0 such promotions in the produced file.
- **SC-007**: The full `pytest` suite passes the single-sourced project coverage
  gate (≥ 80 %, `fail_under = 80`; Constitution VIII), and the one new Python
  module (`core/_research_block.py`) is fully exercised by its unit suite (the
  Markdown command, templates, and TOML it adds are data, not line-coverage
  -measured).

## Assumptions

- The research file format and the `Source` / `Finding` / `Anchor` provenance
  model, the `io/research.py` reader, and `sources.ttl` land in **iteration 13**
  (spec `012-research-provenance-model`). This iteration **depends on** that format
  and does not redefine it; the skill and templates must emit exactly what that
  reader parses.
- The reliability scale is **`alta` / `media` / `baja`** (high / medium / low) per
  design § 20.3, used by `min_reliability_for_anchor`.
- `[research]` defaults (resolved in Clarifications, Session 2026-06-04):
  `enabled = true`, `min_reliability_for_anchor = "media"`, and
  `source_languages = []` (no declared provenance preference — the protocol's
  original-language rule still applies). The design § 20.9 example
  `["de","pl","en","fr"]` is illustrative of a specific book, not a generic
  scaffold default. `bookwright init` writes the block explicitly with these
  defaults and comments (FR-014a); the loader also applies them when the block is
  absent (FR-012).
- The search engine / fetching is supplied by the agent's own tools, not by
  Bookwright; no network or runtime dependency is added (Constitution II).
- Skill materialization reuses the iteration-9 `SkillsIntegration` pipeline; only
  `claude` and `generic` integrations ship (Constitution V).
- The topic string is reduced to a filename via the existing slug helper
  (`golem.slug.make_slug`), preserving the human title inside the file.
- Source code, identifiers, and the `SKILL.md`/command bodies are authored to
  trigger on both Spanish and English prompts (user's bilingual convention); the
  design docs stay Spanish.
- This is **M4 / v0.2** work landing in dependency order; it deliberately omits the
  `factual_anchor` validator (iter 15), the `bookwright-verify` LLM check (iter
  16), and vector search (v0.3) — design § 20.10.

## Dependencies

- **Iteration 13 (spec `012-research-provenance-model`)**: `io/research.py`, the
  provenance entities, and `sources.ttl` — the parse target for this iteration's
  output. Must be on `main` first.
- **Iteration 2 (manifest model)**: extended here with the `[research]` block.
- **Iteration 7 (project templates)**: the layered (override → core) template
  resolution reused for `bible/research/` templates.
- **Iterations 8 & 9 (source commands + skill materialization)**: the command
  -source format and the `SKILL.md` materialization pipeline reused here.
