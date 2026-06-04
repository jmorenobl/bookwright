# Phase 0 Research: `bookwright-research` Skill + `bible/research/`

All Technical-Context unknowns resolved below. No `NEEDS CLARIFICATION` remained
after the spec's 2026-06-04 clarification session; the items here are the
codebase-grounded decisions that shape the design.

## R1 — Reuse the iteration-9 materialization pipeline (no parallel pipeline)

- **Decision**: Drop `bookwright-research.md` into
  `src/bookwright/resources/commands/` and add nothing to the materializer.
- **Rationale**: `integrations/materialize.py::iter_command_sources()` already
  enumerates *every* `*.md` at the top of `resources.commands` and
  `generate_skill_md()` materializes each into `<skills_dir>/<name>/SKILL.md`,
  copying any cited `references/<file>.md`, then linting. A new command file is
  picked up automatically by `init` for both `claude` and `generic`. FR-002 is
  satisfied by *placement*, not by code.
- **Constraint discovered**: the materializer enforces `frontmatter.name ==
  filename stem` (`name_frontmatter_mismatch`) → the file MUST be
  `bookwright-research.md` with `name: bookwright-research`.
- **Alternatives rejected**: a bespoke research materializer (violates FR-002
  and Principle V duplication ban); registering the command in a list (there is
  no list — enumeration is filesystem-driven).

## R2 — Description lives in two synced places (SC-009 gate)

- **Decision**: Put the authoritative bilingual `description` in the source
  command's front-matter **and** add an identical entry to
  `integrations/descriptions.py::SKILL_DESCRIPTIONS["bookwright-research"]`.
- **Rationale**: `get_description()` prefers the `SKILL_DESCRIPTIONS` table and
  falls back to front-matter; the existing SC-009 CI gate asserts the table
  mirrors the source front-matter verbatim. Omitting the table entry would
  either drift or fail that gate. Keep them byte-identical.
- **Cap**: `description` ≤ 1024 chars — enforced by `lint_skill_md` Rule 3 and
  the developer tripwire in `descriptions.py`. The bilingual ES+EN trigger text
  must fit (the existing descriptions sit comfortably under the cap).
- **Alternatives rejected**: front-matter only (fails the SC-009 equality gate
  once the table is the read seam); table only (the materializer reads
  front-matter for `name`, and the source file is the human-authored origin).

## R3 — Triggering on Spanish *and* English (FR-004)

- **Decision**: Author the `description` with explicit ES+EN trigger phrases and
  a "NO sirve para…/NOT for…" disambiguation, exactly like the ten shipped
  descriptions (see `bookwright-bible`/`bookwright-clarify`).
- **Rationale**: Agent skill selection keys off `description`. The shipped
  pattern bakes both languages and a negative boundary into one string; mirror
  it. The body `## Rol`/`## Procedimiento` prose is Spanish (project convention)
  but the triggers in `description` are bilingual.
- **Alternatives rejected**: two skills (one per language) — violates "one
  SKILL.md per command" and the user's bilingual-single-skill preference.

## R4 — The parse target is fixed by iteration 13 (`io/research.py` on `main`)

- **Decision**: The skill and templates emit **exactly** the front-matter
  `map_research()` parses; this iteration does not touch `io/research.py`,
  `golem.modules.provenance`, or `sources.ttl`.
- **Rationale**: `src/bookwright/io/research.py` and the
  `Source`/`Finding`/`Anchor` entities are already on `main` (iteration 13).
  `graph build` already runs the research pass
  (`commands/graph/build.py:101` calls `map_research(project_root,
  bible_dir/"research", …)`). The dependency is satisfied; our job is to
  *produce* conformant files. The reader's fault model is strict (any vocab
  miss, missing facet, non-open finding without claim/sources, anchor promoting
  an unknown finding, or translation-rule breach **aborts the build**), so the
  reference doc and templates must be precise.
- **Exact contract** (derived from `io/research.py` + `provenance.py`):
  - `sources.md` → `sources:` list; each item requires `name`, `reference`,
    `author`, `original_language`, `type`, `reliability`,
    `reliability_justification`, `access_date`, `original_quote`; `translation`
    required **iff** `original_language != book.language`, dropped when equal.
  - `<topic>.md` → `findings:` (each `id` + `claim` + `sources` unless `open`),
    optional `bears_on`; `anchors:` (each `promotes` an in-file finding `id`,
    `constrains` an entity name or the literal `timeline`, optional
    `begin`/`end`/`date` integer years).
  - `_index.md` → `open_questions:` (treated as open findings; `claim`/`sources`
    optional).
  - Vocabularies: `type` ∈ {primaria, secundaria, oficial, académica,
    periodística, testimonial}; `reliability` ∈ {alta, media, baja};
    `access_date` is an ISO date.
- **Alternatives rejected**: inventing a richer format (would not parse —
  reader is strict); redefining the entities here (out of scope; iteration 13
  owns the format, per spec Assumptions).

## R5 — `[research]` block shape, defaults, and validation home

- **Decision**: Add a `ResearchBlock(BaseModel)` with
  `enabled: bool = True`, `source_languages: list[str] = []`,
  `min_reliability_for_anchor: Literal["alta","media","baja"] = "media"`, wired
  as `research: ResearchBlock = Field(default_factory=ResearchBlock)` on
  `Manifest`. Validate `min_reliability_for_anchor` via the `Literal` (Pydantic
  names the field on a bad value → FR-013) and `source_languages` entries
  against `ISO_639_1_CODES` (mirrors `BookBlock.language`).
- **Rationale**: A typed block with a `default_factory` makes a *missing* block
  load with documented defaults (FR-012) while a *present* block is validated
  (FR-013). `extra="forbid", strict=True` matches every sibling block. The
  reliability values are duplicated from `golem.namespaces.RELIABILITY_IRI`
  intentionally: `core/` must not import `golem/` (layering). Guard the
  duplication with a unit test asserting the `Literal` args equal
  `set(RELIABILITY_IRI)` — the same anti-drift discipline as SC-009.
- **Line budget — extract, don't grow**: `core/manifest.py` is already **535
  lines** (`wc -l`). Adding the block inline would push it further past the
  Principle IV 500-line ceiling, so `ResearchBlock` MUST live in a new
  `core/_research_block.py`, imported into `manifest.py` and re-exported from
  `bookwright.core` — exactly as `_build.py`/`_translate.py` were split out. The
  `Manifest.research` field and the `default_factory` wiring stay in
  `manifest.py` (one short import + one field line). Put the ISO-639-1 /
  reliability validators in the new module with the class.
- **Alternatives rejected**: free-form `extra="allow"` block (no validation →
  fails FR-013); importing `RELIABILITY_IRI` into core (wrong layer direction,
  risks an import cycle since the registry late-imports already).

## R6 — Defaults written into the scaffold *and* applied on absence (FR-014a vs FR-012)

- **Decision**: Add a commented `[research]` block to
  `resources/templates/manifest.template.toml` carrying `enabled = true`,
  `source_languages = []`, `min_reliability_for_anchor = "media"`. `_build.py`
  re-parses the template through Pydantic, so the block round-trips with its
  comments (FR-014a). The model's `default_factory` covers absent blocks
  (FR-012) — both paths converge on the same values.
- **Rationale**: `Manifest.build()` loads `manifest.template.toml` via tomlkit,
  overlays overrides, re-validates. A block already in the template needs **no**
  `_BUILD_OVERRIDE_ALLOWLIST_TABLE` entry because `init` writes the defaults,
  not overrides. Comments survive because tomlkit is the dump source of truth.
- **Verification**: a round-trip test loads the scaffolded manifest, re-dumps,
  and asserts the `[research]` comment lines persist (SC-002).
- **Alternatives rejected**: omit the block and rely on defaults (fails
  FR-014a's "discoverable, self-documenting" requirement); add allowlist
  entries for research overrides (no init override exists → dead plumbing,
  Scope discipline).

## R7 — Two template homes: scaffold (`resources/project/`) vs layered (`resources/templates/`)

- **Decision**: Put the **starter** `bible/research/_index.md` and `sources.md`
  under `resources/project/bible/research/` (rendered by
  `scaffold.py::render_resource_tree`, which walks the whole `project/` tree),
  and delete the legacy `resources/project/bible/research.md`. Put the
  **layer-resolvable** templates (`_index.md.tmpl`, `sources.md.tmpl`,
  `tema.md.tmpl`) under `resources/templates/bible/research/`, mirroring the
  iteration-7 `character.md.tmpl`/`setting.md.tmpl`/`location.md.tmpl`.
- **Rationale**: `init` materializes `bible/research/` from `project/` (FR-014,
  US3). The `templates/bible/` `.tmpl` files are the canonical per-entity
  skeletons the authoring skills point at and that a project's
  `.bookwright/templates/` override shadows (FR-008's "project override →
  packaged core"); the research per-topic skeleton joins them as `tema.md.tmpl`.
  The starter scaffold files MUST themselves parse cleanly through
  `map_research()` (empty/placeholder but valid — open questions only, no
  half-formed findings), since `init` users may run `graph build` immediately.
- **Empty-dir caveat**: `render_resource_tree` preserves empty dirs only via
  `.gitkeep`; `bible/research/` ships two real files so no keep file is needed.
- **Alternatives rejected**: a single home (the codebase already separates
  scaffold from layered templates — follow it); a `.j2` starter needing render
  context (no per-project tokens belong in a research starter — plain `.md`).

## R8 — Bible & clarify edits (FR-009, FR-010)

- **Decision**: In `bookwright-bible.md`, change step 6 and the
  "Archivos a escribir" list so it creates `bible/research/_index.md` instead of
  `bible/research.md`. In `bookwright-clarify.md`, ensure the open-questions
  sweep names `bible/research/_index.md` (`open_questions:`).
- **Rationale**: The legacy single file is gone (R7); the bible builder must not
  reference a path that no longer scaffolds. Clarify "continues to" collect open
  research questions — make that target explicit now that they live in
  `_index.md` front-matter.
- **Gate impact**: both files are source commands → their front-matter
  `description` is under the SC-009 mirror. Editing only the **body** leaves the
  description untouched, so the gate is unaffected; if a description changes,
  update `descriptions.py` in lockstep.
- **Alternatives rejected**: leaving bible pointing at `research.md` (would
  recreate the legacy file the scaffold no longer ships, and `map_research`
  ignores a top-level `bible/research.md` anyway — silent data loss).

## R9 — No fetch, no network (FR-007, Constitution II)

- **Decision**: The skill body is pure instruction prose; it tells the agent to
  use *its own* search/browse tools, never bundles a fetcher, never adds a dep.
- **Rationale**: Constitution II locks the dependency set; FR-007 forbids a
  search engine in the skill. The "search capability" is the agent's. The skill
  emits text files and calls the existing `bookwright graph build --json`.
- **Alternatives rejected**: any HTTP/scraping helper (constitutional
  violation + out of scope).
