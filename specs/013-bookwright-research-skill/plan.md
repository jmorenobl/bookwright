# Implementation Plan: `bookwright-research` Skill + `bible/research/`

**Branch**: `013-bookwright-research-skill` | **Date**: 2026-06-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-bookwright-research-skill/spec.md`

## Summary

Ship the author-facing research command for M4/v0.2. A new packaged source
command `resources/commands/bookwright-research.md` encodes the **seven-step
research protocol** (design § 20) and is materialized as an Agent Skill through
the **existing iteration-9 pipeline** — no new pipeline, no new plumbing. The
skill instructs the agent to write findings, sources, and anchors into
`bible/research/<topic>.md` / `sources.md` / `_index.md` in **exactly the
front-matter shape the iteration-13 reader (`io/research.py`, already on `main`)
parses**, then run `bookwright graph build --json`.

Three supporting slices land alongside it:

1. **`[research]` manifest block** — extend the iteration-2 Pydantic model with
   an optional `ResearchBlock` (`enabled`, `source_languages`,
   `min_reliability_for_anchor`), defaults applied when the block is absent,
   field-naming validation errors, and the block written (with comments) into
   the scaffolded `manifest.template.toml`.
2. **`bible/research/` scaffolding** — replace the legacy single
   `bible/research.md` starter with a `bible/research/` directory
   (`_index.md` + `sources.md`), plus layer-resolvable packaged templates under
   `resources/templates/bible/research/` (mirroring the iteration-7 entity
   templates).
3. **Bible/clarify wiring** — `bookwright-bible.md` writes
   `bible/research/_index.md` (not `bible/research.md`); `bookwright-clarify.md`
   keeps gathering the open research questions.

The CLI/runtime adds **no fetching, no search engine, no network dependency**
(Constitution II): the skill instructs; the agent's own tools search. The
parse-target format is **fixed by iteration 13** — this iteration emits it and
does not redefine it.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II/III).

**Primary Dependencies**: Existing locked stack only — `pydantic` v2,
`tomlkit`, `pyyaml`, `jinja2`, `typer`, `rdflib`, `python-slugify`. **No new
runtime dependency** (Constitution II; the skill bundles no fetcher — FR-007).

**Storage**: Plain text — `manifest.toml` (TOML round-tripped through tomlkit),
`bible/research/*.md` (YAML front-matter + Markdown body), `SKILL.md`
(YAML front-matter + Markdown), packaged `.tmpl`/`.j2` templates. The graph
(`bible/graph.ttl`) remains a derived cache (Constitution I).

**Testing**: pytest with ≥ 80 % line coverage (the spec asks > 85 % on new
code, SC-007); `ruff check`, `ruff format --check`, `mypy --strict`; the
shipped `lint_skill_md` gate over the generated skill (SC-001); the existing
SC-009 description equality gate over `descriptions.py`.

**Target Platform**: Cross-platform CLI (developer + CI, macOS/Linux/Windows).

**Project Type**: Single project, src-layout CLI (`src/bookwright/`).

**Performance Goals**: N/A — `init` and `graph build` are interactive,
sub-second on fixture-scale projects; no perf-sensitive path is added.

**Constraints**: Every source file ≤ 500 lines (Principle IV); `SKILL.md`
satisfies agentskills.io (`name` ≤ 64 and == parent dir, `description` ≤ 1024,
valid YAML — Principle VII); JSON-over-stdout preserved where touched
(Principle IX); ontology stays frozen — no new GOLEM class (Constitution X);
research vocabulary already lives in `sources.ttl` (iteration 13).

**Scale/Scope**: One new source command + one reference doc; one new Pydantic
block + validators + template edit; one new scaffold dir (2 files) + 3 packaged
templates; two source-command edits (bible, clarify); one `descriptions.py`
entry. No new CLI verb.

## Constitution Check

*GATE: evaluated against constitution v1.3.0 before Phase 0 and re-checked after Phase 1.*

| Principle | Gate | Verdict |
|---|---|---|
| I. Plain text as source of truth | All artifacts are MD/TOML/Turtle; graph stays a rebuildable cache | ✅ PASS |
| II. Modern Python stack | No new runtime dep; skill bundles no fetcher/search engine (FR-007) | ✅ PASS |
| III. src-layout | Model/validators under `src/bookwright/core/`; tests under `tests/` | ✅ PASS |
| IV. Modular command surface | No new CLI verb; `manifest.py` is already 535 lines, so `ResearchBlock` goes in a new `core/_research_block.py` (≤500) imported by `manifest.py` | ✅ PASS |
| V. Plugin-based integrations | Reuses `SkillsIntegration`/`INTEGRATION_REGISTRY`; only `claude`+`generic` (FR-002) | ✅ PASS |
| VI. Agent Skills only | One `SKILL.md` per integration via the iter-9 materializer; nothing under `commands/` | ✅ PASS |
| VII. agentskills.io compliance | Generated skill passes `lint_skill_md`; description ≤ 1024 (SC-001) | ✅ PASS |
| VIII. Test discipline | Unit (block load/validate, format-conformance), integration (`init` scaffold + materialize + `graph build`), materialization-compliance E2E for the new authoring skill; ≥ 80 % (target > 85 %) | ✅ PASS |
| IX. JSON-over-stdout | `init` / `graph build --json` contracts unchanged; the skill's final step calls `graph build --json` | ✅ PASS |
| X. Design axioms | rdflib, GOLEM, plain text, Agent-Skills-only all honoured; **ontology frozen** — no new class, research vocab already in `sources.ttl` | ✅ PASS |

**Scope discipline**: This is iteration 014 of the plan (spec dir `013-…`),
the M4 research-skill slice. It deliberately **omits** the `factual_anchor`
validator (iter 15), `bookwright-verify` (iter 16), and vector search (v0.3).
No speculative plumbing is added — every line traces to an FR (design § 20.10,
Scope & Release Discipline). ✅ PASS.

No violations → Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/013-bookwright-research-skill/
├── spec.md              # Feature spec (already written + clarified)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output — ResearchBlock + research-file format
├── quickstart.md        # Phase 1 output — manual end-to-end walkthrough
├── contracts/           # Phase 1 output
│   ├── research-block.md         # [research] TOML ⇄ Pydantic contract
│   ├── research-file-format.md   # YAML front-matter the io/research.py reader parses
│   └── research-skill.md         # SKILL.md authoring contract (7 steps, ES+EN triggers)
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── core/
│   ├── _research_block.py          # NEW — ResearchBlock model + ISO/reliability validators
│   ├── manifest.py                 # EDIT — import + research field on Manifest (manifest.py is already 535 lines)
│   ├── __init__.py                 # EDIT — re-export ResearchBlock from bookwright.core
│   └── _build.py                   # unchanged (defaults flow from the template block)
├── resources/
│   ├── commands/
│   │   ├── bookwright-research.md   # NEW source command — 7-step protocol, ES+EN
│   │   ├── bookwright-bible.md      # EDIT — writes bible/research/_index.md
│   │   ├── bookwright-clarify.md    # EDIT — gathers open research questions
│   │   └── references/
│   │       └── research-format.md   # NEW reference — exact front-matter contract
│   ├── templates/
│   │   ├── manifest.template.toml   # EDIT — add [research] block + comments
│   │   └── bible/research/          # NEW layer-resolvable templates
│   │       ├── _index.md.tmpl
│   │       ├── sources.md.tmpl
│   │       └── tema.md.tmpl         # per-<topic> skeleton
│   └── project/bible/
│       ├── research.md              # DELETE legacy single file
│       └── research/                # NEW scaffold dir
│           ├── _index.md
│           └── sources.md
└── integrations/
    └── descriptions.py             # EDIT — add bookwright-research description (SC-009 mirror)

tests/
├── core/
│   └── test_research_block.py       # load with/without block, defaults, bad reliability/language
├── integrations/
│   └── test_research_skill.py       # materializes + passes lint_skill_md (both integrations)
├── resources/ (or io/)
│   └── test_research_format.py      # a fixture topic/sources/_index round-trips through map_research
└── commands/init/
    └── test_init_research_scaffold.py  # bible/research/ scaffolded, no stray research.md, [research] in manifest
```

**Structure Decision**: Single project, src-layout. The feature is almost
entirely **packaged-resource + one Pydantic block**: no new CLI module, no new
indexer, no new integration. The only Python touched is `core/manifest.py`
(the block) and `integrations/descriptions.py` (the SC-009 mirror entry). All
new behavior is data (Markdown/TOML/templates) consumed by machinery that
already exists on `main`.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
