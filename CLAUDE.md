# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state: v0.2.0 shipped, v0.3 / M5 in progress

Both released milestones are **fully implemented**: `v0.1.0` (2026-06-03,
the v0 toolkit, iterations 1–11) and `v0.2.0` (2026-06-05, the M4 research &
verification system, iterations 12–18). All of it is on `main` with a real
`src/bookwright/` package, ~200 Python files, the full test suite, docs, and CI
gates green. Current work is **v0.3 / M5 — context orchestration**
(design § 21), iterations 019–023 in `bookwright-implementation-plan.md`:
iteration 019 — authored focus (the `[focus]` manifest block +
`bookwright focus show|set|clear`) — is **merged on `main`** (unreleased). The
next planned iteration is **020 — `bookwright status`** (deterministic derived
state + `next_actions`), then skills consuming it (021–022) and the v0.3.0
release (023). No iteration branch is currently active. Vector search (ChromaDB
over rdflib) moved to v0.4.

The canonical references:

- `bookwright-design.md` (Spanish, ~74 KB) — canonical design spec. Section
  numbering is load-bearing; specs and iteration prompts cite it as
  `bookwright-design.md § N.M`. Section 16 lists axiomatic decisions that
  MUST NOT be reopened. § 20 covers the research system (shipped in v0.2);
  § 21 the context orchestration now being built.
- `bookwright-implementation-plan.md` (Spanish, ~45 KB) — ordered iteration
  plan. § 2 has the dependency map; § 3+ have one ready-to-paste
  `/speckit-specify` prompt per iteration.
- `.specify/memory/constitution.md` — ratified, currently **v1.4.0**.
  **Binding** on every PR. Three principles are explicitly NON-NEGOTIABLE:
  plain-text source of truth (I), Agent Skills only — no legacy `commands/`
  directories (VI), and test discipline with ≥ 80 % coverage (VIII).
- `specs/NNN-<name>/` — per-iteration `{spec,plan,tasks}.md` (plus
  `research.md`, `data-model.md`, `contracts/`, `quickstart.md`). The
  iteration's plan is the most precise statement of what its code does.
- `.claude/skills/speckit-*` — the Spec Kit slash-command skills that drive
  the workflow.

Every feature lands through a numbered iteration, not as a freehand commit.

## Common commands

```
uv sync                          # install deps + dev group into .venv
uv run bookwright <subcommand>   # run the CLI (version | check | init | validate | graph | integration)
uv run pytest                    # full suite (excludes `manual` marker, enforces ≥80% coverage)
uv run pytest tests/golem/test_triples.py::test_name   # single test
uv run pytest -m manual          # opt-in packaged-install / subprocess smoke (slow, networked)
uv run ruff check && uv run ruff format --check
uv run mypy --strict             # files = src + tests (configured in pyproject)
```

All four gates (`ruff check`, `ruff format --check`, `mypy --strict`,
`pytest`) run in CI on every push / PR. The coverage threshold is
single-sourced in `[tool.coverage.report]` (`fail_under = 80`,
`precision = 2`) — do **not** add `--cov-fail-under` anywhere; one source, no
drift.

## Code intelligence: use codegraph first

This repo has a **codegraph** index (a local SQLite knowledge graph of every
symbol, edge, and file, kept fresh by a file watcher in `.codegraph/`, not
committed). Before grepping/reading to understand the code, query it via the
`mcp__codegraph__*` tools — it's faster and already built:

- `codegraph_context` — primary entry point for "what's the deal with area X".
- `codegraph_trace` — full call path from X to Y (follows dynamic dispatch).
- `codegraph_callers` / `codegraph_callees` / `codegraph_impact` — who calls
  what, and what a change would break.
- `codegraph_explore` / `codegraph_node` — survey or read specific symbols.

Answer architecture/trace/where-is-X questions directly with 2–3 of these
calls; fall back to raw Read/Grep only to confirm a detail codegraph missed.

## How work is done here

Built **with** Spec Kit, **for** narrative authoring. Every iteration runs
this fixed sequence — do not skip steps, do not write code outside this flow:

```
/speckit-specify <iteration prompt from bookwright-implementation-plan.md>
/speckit-clarify          # mandatory; say "no clarifications" to unblock if truly none
/speckit-plan <technical hint, usually a pointer into bookwright-design.md §X.Y>
/speckit-tasks
/speckit-analyze          # cross-artifact consistency check
/speckit-implement
```

Each iteration is a branch `NNN-<short-name>` with its own `specs/` dir. Merge
to `main` only when tests are green and `/speckit-analyze` reports no issues;
later iterations assume earlier code is on `main`. The auto-git hooks in
`.specify/extensions.yml` offer to commit between phases.

## Iterations (shipped + planned)

`specs/` holds one directory per iteration. 001–011 are merged (v0.1.0),
012–018 are merged (v0.2.0), and 019 is merged on `main` (M5, unreleased).
There is no active iteration branch.

| # | Iteration | Milestone | Status |
|---|---|---|---|
| 001 | Repo bootstrap + empty CLI | M0 | ✅ merged |
| 002 | Manifest model (`pydantic` + `tomlkit`) | M0 | ✅ merged |
| 003 | Integration architecture (plugin registry) | M0 | ✅ merged |
| 004 | `bookwright init` command | M0 | ✅ merged |
| 005 | GOLEM domain model (`rdflib`) | M1 | ✅ merged |
| 006 | Graph indexer + `graph build`/`query` | M1 | ✅ merged |
| 007 | Bible / outline / constitution templates | M2 | ✅ merged |
| 008 | The 10 source commands (Markdown) | M2 | ✅ merged |
| 009 | Materialize commands as Agent Skills | M2 | ✅ merged |
| 010 | Validation system | M3 | ✅ merged |
| 011 | Release prep (fixtures, E2E, docs, v0.1.0) | M3 | ✅ merged |
| 012 | Research provenance model (Source/Finding/Anchor) | M4 | ✅ merged |
| 013 | `bookwright-research` skill + `[research]` manifest block | M4 | ✅ merged |
| 014 | `factual_anchor` validator | M4 | ✅ merged |
| 015 | `bookwright-verify` LLM check | M4 | ✅ merged |
| 016 | Research E2E fixture, workflow test, docs | M4 | ✅ merged |
| 017 | Traceability-tag cleanup + non-regression gate | — | ✅ merged |
| 018 | Unified `--json` error envelope | — | ✅ merged |
| 019 | Authored focus state: `[focus]` block + `bookwright focus` | M5 | ✅ merged |

M4/v0.2 is **complete and released** (`v0.2.0`, 2026-06-05): the provenance
model (012), the `bookwright-research` skill + `[research]` manifest block (013),
the `factual_anchor` validator (014), the `bookwright-verify` LLM check (015),
and the research E2E fixture/tests/docs (016) all merged, plus two maintenance
iterations — traceability-tag cleanup (017) and the unified error envelope
(018). v0.3 / M5 — context orchestration (design § 21) — is underway: 019
(authored focus) is merged; the next planned iteration is **020 —
`bookwright status`** (deterministic derived state + `next_actions`), followed
by 021–023. Vector search (ChromaDB over rdflib) moved to v0.4.

When a spec or prompt references `§ 6`, `§ 20.5`, etc., that's a section in
`bookwright-design.md`. Open it.

## Architecture (the big picture)

`bookwright` is a CLI (`src/bookwright/cli.py`) that assembles a `typer` app
from per-command modules. The layers, in dependency order:

- **`errors.py`** (package root) — `BookwrightError`, the **single** shared base
  that owns the canonical `--json` error envelope (`{status, code, message
  [, details]}`) and its one `to_json()`. Every serializable error across the
  codebase (eight origins: `core`, `golem`, `io`, `indexers`, `validation`,
  `commands.validate`, `integrations`, `commands.init`) subclasses it and defines
  **no** per-class serializer. The module imports nothing from the other layers,
  so it sits below all of them with no cycle (Principle IX, iteration 018).
- **`core/`** — the manifest (`manifest.py`, `pydantic` model round-tripped
  through `tomlkit` so author comments survive), the manifest error hierarchy
  (`errors.py`, `ManifestError(BookwrightError)` + the `ManifestWarning` payload),
  and language helpers (`iso639_1.py`).
- **`golem/`** — the GOLEM narrative domain model serialized to Turtle/RDF.
  Each concept is an **immutable Pydantic v2 model** subclassing `GolemEntity`
  (`base.py`): identity (its `URIRef`) is computed once in `model_post_init`
  from a slug. Concepts live in `golem/modules/*` (character, event, setting,
  narrative, relationship, inference, feature) and register in the `CONCEPTS`
  name→class map. **Provenance is structural**: an entity declares
  `DerivedAssertion`s and `CrossRef` edges; the base emits triples uniformly,
  and the indexer reifies each assertion as a CIDOC-CRM
  `crm:E13_Attribute_Assignment` resolving the originating *field* (never a
  file path) to a `file:line` locator. The ontology is **frozen** — the
  17-class closure (`CLASS_IRI`) and `golem.ttl` must not gain classes
  (Constitution X); new vocabulary goes in separate `.ttl` files.
- **`indexers/`** — the `Indexer` `Protocol` (`base.py`) is the only seam the
  `graph` verbs depend on; `RdflibIndexer` is the one concrete engine.
  `rdflib` is permanent; `Grafeo`/`GrafeoIndexer` is **cancelled**.
- **`io/`** — plain-text readers/writers. `frontmatter.py` parses YAML
  front-matter + Markdown body **with line tracking** (`key_lines`) so the
  indexer can build `file:line` provenance. `bible.py` maps `bible/*.md` into
  GOLEM entities; `project.py`, `manuscript.py`, `fs.py`, `report.py` round
  it out, plus `research.py` (iteration 012), an analogue of `bible.py`.
- **`integrations/`** — materializes the 10 source commands as **Agent
  Skills**. `SkillsIntegration` is the plugin base; `INTEGRATION_REGISTRY`
  (populated on import via `_register_builtins`) holds `claude` and `generic`.
  No monolithic dispatcher (Constitution V).
- **`validation/`** — continuity checks (`validators/*`: character presence,
  focalization, setting continuity, temporal) run by `runner.py` against the
  graph via SPARQL (`queries.py`), registered in `registry.py`.
- **`commands/`** — one sub-package/module per CLI verb. Each agent-facing
  command pairs its logic with an `envelope.py` that emits the `--json`
  contract. `init/` is the largest (conflict matrix, rollback ledger,
  optional git init, scaffold from `resources/project/`).
- **`resources/`** — packaged data read at runtime via `importlib.resources`:
  `project/` (the scaffold tree, `.j2` / `.tmpl` templates), `commands/`
  (the 10 source-command Markdown + `references/`), `schemas/golem-1.1/`
  (frozen ontology + VERSION), `vocabularies/` (`propp.ttl`, `greimas.ttl`,
  and the new `sources.ttl`).

**Data flow**: `bible/*.md` → `map_bible` → GOLEM entities → `RdflibIndexer`
→ derived cache `bible/graph.ttl` → `bookwright validate` (SPARQL). The graph
is **always a derived cache**, reconstructible from plain text, never the
source of truth (Constitution I).

## Stack (locked by Constitution II — substituting any requires an amendment)

- **Python 3.11+** only. **`uv`** + committed `uv.lock`. **`hatchling`** build
  backend. **src-layout** (`src/bookwright/`, `tests/` at root), no exceptions.
- Runtime deps: `typer`, `rich`, `rdflib`, `pydantic` v2, `tomlkit`, `jinja2`,
  `python-slugify`, `platformdirs`, `uuid-utils` (**not** `uuid7`), plus
  `pyyaml` and `packaging`. Dev group: `mypy`, `ruff`, `pytest`,
  `pytest-cov`, `pre-commit`, `types-pyyaml`. Docs group (never imported by
  `src/`): `mkdocs` + `mkdocs-material`.
- Every source file ≤ 500 lines, one CLI subcommand per module (Principle IV).

## Domain knobs / non-negotiable behaviors

- **Agent Skills, never legacy commands**: emit one `SKILL.md` per command
  under the integration's `skills_dir`. Writing to `.claude/commands/` or
  analogues is a Principle VI violation that blocks merge. Principle VII
  enforces agentskills.io limits: `name` ≤ 64 chars matching its parent
  directory, `description` ≤ 1024 chars, valid YAML front-matter (the
  `lint_skill_md` gate checks this).
- **JSON-over-stdout (Principle IX)**: any agent-consumed subcommand accepts
  `--json` and then emits a single JSON document on stdout and *only* that.
  Human prose / progress goes to stderr.
- **Integrations**: only `claude` (writes `.claude/skills/`) and `generic`
  (writes `.agents/skills/`) ship. Use the `SkillsIntegration` +
  `INTEGRATION_REGISTRY` plugin shape (Principle V).

## Scope discipline — do NOT implement ahead of the plan

A PR that adds plumbing whose only justification is "future X" MUST be
rejected (Constitution "Scope & Release Discipline").

- v0.2 / M4 (design § 20) — research & verification: shipped in `v0.2.0`
  (iterations 012–016). Don't pull v0.3+ work below into it.
- v0.3 / M5 — context orchestration (design § 21), iterations 019–023:
  `[focus]` block + `bookwright focus` (019, ✅ merged); `bookwright status`
  (deterministic derived state + `next_actions`, 020 — next); skills
  consuming it (021–022); v0.3.0 release (023).
- v0.4 — vector search (ChromaDB over rdflib, decoupled from Grafeo).
- v1.0 — export to EPUB / PDF / print via pandoc.

**Cancelled — never implement (owner decision):** preset / genre-package
system (template resolution is 2 layers, overrides → core); `GrafeoIndexer` /
Grafeo engine; multi-integration beyond `claude` / `generic` and the
`bookwright integrate` command; extension system. See design § 15.5, § 20.12.

## Language conventions

- `bookwright-design.md`, `bookwright-implementation-plan.md`, the README, and
  the `docs/` site are **Spanish** — the user authored them deliberately so.
  Keep edits to them in Spanish.
- Source code, identifiers, commit messages, the constitution, and per-spec
  artifacts are **English**.
- Agent Skills must trigger on both ES and EN author prompts.

## Spec Kit specifics

- Pinned at `v0.10.1` (upgraded from `v0.8.16` on 2026-06-11). Don't upgrade
  without a reason worth chasing template churn.
- Don't modify Spec Kit *core* (templates, scripts, manifests). Per-project
  *copies* (`.specify/extensions.yml`, `git-config.yml`) are editable.
- Skill names are hyphenated (`speckit-plan`). `extensions.yml` hook entries
  use dot form (`speckit.git.commit`); the dispatcher converts dots to
  hyphens when invoking.
- `auto_execute_hooks: true`. Mandatory hooks (`before_constitution`,
  `before_specify`) execute without prompting; optional commit hooks ask
  first.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/020-status-command/plan.md` (iteration 020 — `bookwright status`,
with `research.md`, `data-model.md`, `contracts/cli-status.md`, and
`quickstart.md` alongside it).
<!-- SPECKIT END -->
