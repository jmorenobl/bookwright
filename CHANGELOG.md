# Changelog

All notable changes to Bookwright are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project aims to follow semantic versioning.

## [0.3.2] — 2026-06-14

Second patch of the **v0.3.x hardening track** (iteration 025). It wires the
first orphaned GOLEM concept into the ingestion pipeline: `bible/locations/*.md`
files — ignored entirely in v0 — now become first-class
`G13_Narrative_Location` nodes, mirroring how `bible/settings/` already feeds
`G12_Setting`. This shrinks the deferral registry from seven orphans to six and
turns the ingestion-parity guard's reachable set from six fed concepts to seven.
No new CLI surface, no new runtime dependency, no ontology change (G13 and
`dlp:generic-location` already exist in the frozen closure) — pure hardening.

### Added

- **Location ingestion** (`src/bookwright/io/_bible_builders.py`,
  `src/bookwright/io/bible.py`): the bible mapper now processes
  `bible/locations/*.md` as a one-entity-per-file directory. Each file builds a
  `NarrativeLocation` (G13) from `name:` front-matter (identity source) plus an
  optional `setting:` that resolves against the sibling settings index and emits
  the already-modelled `dlp:generic-location` cross-ref. An unresolvable
  `setting:` is surfaced through the existing `unresolved_participants` channel
  (no new warning category); the node is still built, the build never aborts.
  Built locations feed the research target index, so a `bears_on:` / `constrains:`
  link to a location now resolves instead of degrading to a soft-miss.

### Changed

- **`io/bible.py` split** (behavior-preserving): the concrete builders, coercers,
  resolution helpers, and the context/result dataclasses moved to the new sibling
  module `src/bookwright/io/_bible_builders.py`, bringing `bible.py` back under the
  500-line Principle IV ceiling (it was exactly at 500). `bible.py` re-exports the
  moved public names, so every `from bookwright.io.bible import …` keeps resolving;
  the existing mapper tests pass unchanged.
- **`NarrativeLocation` removed from the deferral registry**
  (`src/bookwright/golem/deferrals.py`, 7 → 6 entries); the ingestion-parity test
  (`tests/golem/test_ingestion_parity.py`) now pins seven reachable concepts.
- **`/bookwright-bible` source command** teaches authoring each concrete location
  as `bible/locations/<slug>.md` with `name:` (required) and `setting:` (optional)
  front-matter; the "no se indexa en v0" shortcut wording is retired. The skill
  re-materializes for both `claude` and `generic` integrations with its bilingual
  (ES/EN) triggers preserved.
- Recorded G13 as wired in `bookwright-design.md` § 7.2 (the v0 shortcut text is
  retired; no axiom reopened).

## [0.3.1] — 2026-06-13

First patch of the **v0.3.x hardening track** (iteration 024). It makes
*ingestion parity* — the gap between GOLEM concepts that are **modelled** (a
frozen class with a `CLASS_IRI` entry) and those actually **fed** from authored
`bible/*.md` — an explicit, tested contract instead of tribal knowledge. Of the
thirteen `CONCEPTS`, seven have no ingestion path today; this release names them
and guards the set so it can only shrink deliberately. No new CLI surface, no new
runtime dependency, no ontology change — pure hardening.

### Added

- **Deferral registry** (`src/bookwright/golem/deferrals.py`): `DEFERRED_CONCEPTS`,
  a pure-data map of the seven orphaned concepts (`NarrativeLocation`, `Object`,
  `NarrativeUnit`, `NarrativeFunction`, `NarrativeSequence`, `RelationshipRole`,
  `PsychologicalState`) to a `DeferralNote` recording *why* each is unfed and its
  `target_version` (`v0.3.x`, `v0.4`, or `undecided`). The module imports only
  `typing` — no I/O, no `CONCEPTS` import — so the gap is recorded independently of
  the code that fills it.
- **Ingestion-parity guard** (`tests/golem/test_ingestion_parity.py`): derives the
  orphan set from a *real* pipeline build over the new `parity-exercise` fixture and
  asserts it equals exactly `DEFERRED_CONCEPTS`'s keys. Wiring a concept later
  (iteration 025+) means **removing its registry entry**; the test stays green only
  if the registry no longer claims it deferred. Backed by the
  `parity-exercise` bible/manuscript fixture exercising every fed concept.

### Changed

- Documented the parity contract in `docs/authoring.md`; the `manuscript.py`
  reader gained a clarifying docstring (no behavior change).

## [0.3.0] — 2026-06-13

Context-orchestration milestone (M5, design § 21). This release adds the
**hilo conductor** — a three-layer work thread that answers "what am I working on
and what should I do next?" without a hand-written TODO that rots. The layers never
overlap: an **authored** `[focus]` block (your declared intent), a **derived**
`bookwright status` (the project state recomputed from the corpus, with
deterministic `next_actions`), and the **judgment** of the Agent Skills each action
invokes. Like the rest of Bookwright, the plan is a *function* of the plain text:
delete the graph, rebuild, get the same state. The system is **inert** for projects
that don't use it: no `[focus]` and no `bible/research/` means identical v0.2.0
behavior. This entry consolidates iterations 19–23.

### Added

- **Authored focus** (iteration 19): the optional `[focus]` manifest block
  (`target`, `notes`, CLI-stamped `updated_at`) and the `bookwright focus
  set`/`show`/`clear` commands. Plain-text authored state (Principle I); `focus
  set` preserves the rest of the manifest byte-for-byte (comments and order
  included).
- **`bookwright status`** (iteration 20): the derived-state command. Rebuilds the
  graph from the corpus on every run (recomputation *is* the freshness mechanism),
  aggregates the facts (phase, focus, open research questions, under-supported
  anchors, low-reliability findings, validation summary), and maps them through a
  pure, ordered rule table into `next_actions` — each carrying the skill to invoke,
  a paste-ready prompt, and the reason it fired. No LLM, no network: the same corpus
  yields byte-identical output. The rules recommend **per workstream, not per item**,
  so resolving one open question does not shorten the list — only its prompt/reason
  converge.
- **Status-consuming skills** (iterations 21–22): the authoring skills now read
  `bookwright status` at start, anchoring the judgment layer in the derived state
  rather than asking the author to restate it.
- **Orchestration fixture, E2E & docs** (iteration 23): the `tiny-historical`
  fixture extended into a worked orchestration example (a populated `[focus]`, a
  co-located `expected-status.md` oracle, and a pre-baked `_resolution/` answering
  finding outside the corpus dirs); `tests/e2e/test_orchestration_workflow.py`,
  which walks `focus → build → status → resolve → build → status` and asserts
  deterministic **state convergence** plus the inertness/degraded paths; and the
  Spanish `docs/orchestration.md` page wired into the nav. The M4
  `factual_anchor` expectations stay byte-stable (FR-006).

## [0.2.0] — 2026-06-05

Research & verification milestone (M4). This release adds a provenance-backed
research system on top of the v0.1.0 narrative graph: authors can record
external **Sources**, the **Findings** drawn from them, and the **Anchors** that
bind manuscript claims to evidence — all in plain text, all reconstructible into
the graph. Two new Agent Skills drive the loop, a new validator guards anchor
integrity, and an LLM-driven fidelity check flags claims the manuscript can't
support. The system is **inert** for projects that don't use it: no `[research]`
block or `bible/research/` means identical v0.1.0 behavior. This entry
consolidates iterations 12–18.

### Added

- **Research provenance model** (iteration 12): `Source`, `Finding`, and
  `Anchor` GOLEM-adjacent entities serialized through a new `sources.ttl`
  vocabulary (the frozen GOLEM ontology is untouched — Constitution X), with an
  `io/research.py` reader analogous to `bible.py` that maps `bible/research/*.md`
  into entities with `file:line` provenance.
- **`bookwright-research` Agent Skill** + **`[research]` manifest block**
  (iteration 13): the author-facing loop for gathering sources and recording
  findings, plus the `bible/research/` scaffold stamped by `init`. Triggers on
  both ES and EN prompts.
- **`factual_anchor` validator** (iteration 14): a continuity check that flags
  malformed anchors and time-span anachronisms against the graph, wired into the
  same error-only CI gate as the v0.1.0 validators.
- **`bookwright-verify` Agent Skill** (iteration 15): a post-draft LLM fidelity
  check that reads the manuscript against its anchored evidence and reports
  claims the sources don't support.
- **End-to-end research coverage & docs** (iteration 16): the `tiny-historical`
  fixture (a documented mini-novel with real anchors and a deliberate
  anachronism), `tests/e2e/test_research_workflow.py` exercising
  build → query → validate → verify, the Spanish `docs/research.md` page, and
  CHANGELOG/release metadata for this milestone.

### Changed

- **Unified error envelope** (iteration 18): every serializable error across the
  eight origins (`core`, `golem`, `io`, `indexers`, `validation`,
  `commands.validate`, `integrations`, `commands.init`) now subclasses the single
  `BookwrightError` base in `errors.py`, which owns the one canonical `--json`
  envelope (`{status, code, message[, details]}`) and its single `to_json()`.
  Per-class serializers were removed; the base imports nothing from other layers,
  so it sits below them with no cycle (Principle IX).

### Removed

- **Forbidden traceability tags** (iteration 17): purged all `T0xx` task IDs and
  `US-x`/`+USx` user-story tags from `src/` and `tests/` (~57 occurrences across
  ~40 files), converting each to a durable `FR`/`SC`/`D` or `bookwright-design.md
  § N.M` reference or to neutral prose. Added a non-regression test gate
  (`tests/meta/test_no_traceability_tags.py`) that fails CI if any reappear.
  Comments/docstrings only — no logic, signature, or behavior changes.

## [0.1.0] — 2026-06-03

First public release. Bookwright is a spec-driven authoring toolkit that turns a
small set of canonical plain-text documents into a validatable narrative graph.
This entry consolidates iterations 1–11.

### Added

- **CLI** (`typer` + `rich`, Python 3.11+): `bookwright init` (project
  scaffolding with conflict matrix, rollback ledger, and optional git init),
  `bookwright check`, `bookwright version`, `bookwright validate`,
  `bookwright graph build`, `bookwright graph query` (SPARQL over the GOLEM
  graph), and `bookwright integration use` (switch a project's active agent
  integration). Every agent-facing command accepts `--json` and emits a single
  JSON document on stdout (Principle IX).
- **GOLEM domain model** (`rdflib`): characters, settings, narrative events with
  temporal intervals and the five qualitative temporal relations, social
  relationships, and CIDOC-CRM provenance for every derived assertion, serialized
  to Turtle.
- **Graph indexer**: maps the project bible to GOLEM entities and answers SPARQL
  queries with the `golem:` prefix bound.
- **Bible / outline / constitution templates**: the Spanish narrative skeleton
  stamped by `init`, plus re-instanceable molds for the authoring commands.
- **10 authoring commands** materialized as agentskills.io-compliant Agent Skills
  (`bookwright-constitution`, `-bible`, `-outline`, `-synopsis`, `-scenes`,
  `-draft`, `-clarify`, `-analyze`, `-checklist`, `-continuity`).
- **Integrations**: `claude` (`.claude/skills/`) and `generic` (`.agents/skills/`)
  via a plugin registry — no monolithic dispatcher (Principle V).
- **Validation system**: four built-in validators — `character_presence`,
  `focalization`, `setting_continuity`, `temporal` — with an error-only CI gate.
- **Release layer (this iteration)**: three fully-valid fixture projects
  (`tiny-novel`, `tiny-essay`, `tiny-memoir`) under `tests/fixtures/`; an
  in-process E2E suite (`tests/e2e/`) covering the full workflow, skills
  materialization, the integration swap, and docs↔CLI drift; a Spanish MkDocs
  (`material`) documentation site that builds `--strict`; and finalized release
  metadata.

### Changed

- The integration swap is performed by the dedicated `bookwright integration use`
  command. The original plan (re-init with `init --here --force`) was incompatible
  with `init`'s ratified guard that refuses to re-initialize an existing project
  (`.bookwright/` present), so the swap is its own intention-revealing command;
  `init` is unchanged.
- The coverage gate threshold is single-sourced in `[tool.coverage.report]`
  (`fail_under = 80`, `precision = 2`) so it fails closed with no round-up.

### Added — Bible / Outline / Constitution templates

- Authored the real narrative skeleton stamped by `bookwright init`: the
  `bible/` documents (constitution, timeline, relationships, themes, glossary,
  research, subplots, POV structure) and the `outline/` documents (synopsis,
  structure, arcs, scenes), replacing the iteration-4 placeholder stubs. Each is
  Spanish literary-technical prose with HTML-comment craft guidance, worked
  examples inside comments, and `[PENDING: …]` prompts in author-fill sections.
- Authored the re-instanceable molds under `resources/templates/`
  (`character`, `setting`, `location`, `chapter`, `scene`) for the upcoming
  authoring commands (iterations 8–9). The `character` and `setting` molds carry
  frontmatter aligned exactly to the iteration-6 GOLEM mapper's recognized keys,
  so a fresh project indexes with zero skips and zero `unknown_keys`.
- Added a `tests/resources/` format / round-trip validation suite (sentinel
  sweep, frontmatter-contract round-trip via `map_bible`, filled-instance →
  GOLEM entity, Jinja2 `StrictUndefined` render, mold-structure and
  authoring-guidance lint).

### Attribution

- The template **structure** (the document inventory: short + long synopsis,
  themes with a motif registry, locations with sensory anchors, glossary,
  research, subplots, POV structure) is inspired by the
  [`fiction-book-writing`](https://github.com/adaumann/fiction-book-writing)
  preset by **adaumann** (MIT-licensed), whose license permits structural reuse
  with attribution. Bookwright's redaction is **original** prose under
  **Apache-2.0**, rewritten in Spanish and adapted to the **GOLEM** narrative
  model — no verbatim preset text is included.

### Changed — supersedes design § 6

- This iteration **supersedes** `bookwright-design.md` § 6's single unified
  `resources/templates/*.tmpl` layout with a four-layer `resolve_template()`
  resolver, in favor of a **lifecycle split**: stamped-once skeleton singletons
  live under `resources/project/` (rendered/byte-copied by the iteration-4
  walker) and re-instanceable molds live under `resources/templates/` (stamped
  many times by commands). The § 6 resolver only ever existed to serve presets
  (v0.2) and extensions (v0.5), which are out of v0 scope; building it now would
  be forbidden plumbing. § 6 is structural guidance, not a § 16 axiom, so the
  divergence is recorded here rather than litigated as a constitutional
  amendment.
