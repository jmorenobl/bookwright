# Implementation Plan: Provenance Model — Source / Finding / Anchor

**Branch**: `012-research-provenance-model` | **Date**: 2026-06-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-research-provenance-model/spec.md`

## Summary

Make the research that sustains a book — sources, findings, anchors — first-class
nodes in the project graph, derived from plain-text `bible/research/` and emitted
into the same `bible/graph.ttl` as the narrative entities. The model reuses GOLEM's
**Inference** apparatus (`crm:E13_Attribute_Assignment`) to reify Findings and
Anchors and the `crm:E55_Type` pattern to type Sources; **no new GOLEM/ontology
class is introduced** (Constitution X; design § 20.1–20.8). Three new immutable
Pydantic entities live in `src/bookwright/golem/modules/provenance.py`
(`Source`, `Finding`, `Anchor`); a new reader `src/bookwright/io/research.py`
(analogous to `io/bible.py`) parses `bible/research/`; `bookwright graph build`
gains a research pass that feeds their triples through the existing
`RdflibIndexer`. The Bookwright (`bw:`) properties and the source-type /
reliability `E55_Type` individuals are declared in a new controlled vocabulary
`src/bookwright/resources/vocabularies/sources.ttl`.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II).

**Primary Dependencies**: `rdflib` (graph + Turtle), `pydantic` v2 (frozen entity
models), `pyyaml` (front-matter), `uuid-utils` (UUIDv7 tokens for finding/anchor),
`python-slugify` (source slugs via the existing `golem.slug.make_slug`). **No new
runtime dependency** (spec Assumptions; Constitution II).

**Storage**: plain text only. Input: `bible/research/*.md` (YAML front-matter +
Markdown prose), `bible/research/sources.md`, `bible/research/_index.md`. Output:
research triples merged into the derived `bible/graph.ttl`. The graph is never a
source of truth (FR-017; Constitution I).

**Testing**: `pytest`. New unit tests for the three entities and `io/research.py`;
integration tests for `graph build` + `graph query` over a `bible/research/`
fixture; ≥ 85 % line coverage on new code (spec SC; Constitution VIII ≥ 80 %).

**Target Platform**: CLI on Linux/macOS/Windows (the existing matrix).

**Project Type**: single Python package (`src/bookwright/…`, `tests/` at root —
Constitution III).

**Performance Goals**: not performance-sensitive; build stays a one-shot
in-memory rdflib pass over a handful of files.

**Constraints**: byte-stable Turtle output (deterministic prefixes); `--json`
build/query emit a single JSON document on stdout, prose to stderr (Constitution
IX); every source file ≤ 500 lines (Constitution IV); `mypy --strict` clean.

**Scale/Scope**: a project's research is tens of sources / findings / anchors, not
thousands. The agent reads the Markdown directly; no index, no cache, no vectors.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ PASS | Input is Markdown + YAML; output is Turtle. `graph.ttl` stays derived (FR-017). No binary store. |
| II. Modern Python stack | ✅ PASS | No new runtime dependency; reuses rdflib/pydantic/pyyaml/uuid-utils/python-slugify. |
| III. src-layout | ✅ PASS | Production code under `src/bookwright/`; tests under `tests/`. |
| IV. Modular command surface | ✅ PASS | New code goes in `golem/modules/provenance.py` and `io/research.py`; `graph build` gains a small research pass, not a god-module. Every file kept ≤ 500 lines. |
| V. Plugin-based integrations | ✅ N/A | No integration surface touched. |
| VI. Agent Skills only | ✅ N/A | No skill emitted this iteration (the `bookwright-research` skill is iteration 14). |
| VII. agentskills.io compliance | ✅ N/A | No SKILL.md generated. |
| VIII. Test discipline | ✅ PASS | Unit + integration tests; coverage gate honoured; ruff/mypy/pytest CI gates unchanged. |
| IX. JSON-over-stdout | ✅ PASS | `graph build`/`graph query` already honour `--json`; research errors flow through the existing error envelope. |
| X. Design-document axioms | ✅ PASS | **No new GOLEM/ontology class** (FR-001). `bw:` properties + `E55_Type` individuals live in `sources.ttl`, not in the frozen `golem.ttl`; the 17-class closure (`CLASS_IRI`) is untouched. rdflib not Grafeo; plain text; no shell scripts. Design § 20.10 confirms no axiom is reopened. |

**Scope discipline (Constitution "Scope & Release Discipline")**: this iteration
ships *only* the data model + parsing + emission. It deliberately omits the
`bookwright-research` skill (iter 14), the `factual_anchor` validator (iter 15),
the `bookwright-verify` LLM check (iter 16), vector search (v0.3), and the
`[research]` manifest block + `bible/research/` *templates* (iter 14). No plumbing
is added whose only justification is a later iteration. This is M4 / v0.2.0 work
landing in dependency order.

**Gate result: PASS — no violations, Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/012-research-provenance-model/
├── plan.md              # This file
├── research.md          # Phase 0 — design decisions resolved below
├── data-model.md        # Phase 1 — Source/Finding/Anchor + research-file schema
├── quickstart.md        # Phase 1 — end-to-end walk-through on a fixture
├── contracts/
│   ├── research-format.md   # bible/research/ plain-text contract (front-matter schema)
│   ├── provenance-graph.md  # emitted triples: bw: properties, E55 typing, E13 reification, URIs
│   └── research-io.md        # io/research.py public surface (map_research + result types)
└── tasks.md             # Phase 2 — created by /speckit-tasks, NOT here
```

### Source Code (repository root)

```text
src/bookwright/
├── golem/
│   ├── namespaces.py                 # + BW namespace, bw:/source-type/reliability IRIs, P2/P4/E52 refs, bind bw prefix
│   └── modules/
│       └── provenance.py             # NEW — Source, Finding, Anchor (frozen Pydantic GolemEntity subclasses)
├── io/
│   ├── bible.py                      # + entity_index on MapResult (name-slug → URI: characters+settings+events) for target resolution
│   ├── research.py                   # NEW — map_research(): bible/research/ → provenance entities
│   └── errors.py                     # + ResearchError (hard build-abort for invalid research front-matter)
├── commands/graph/
│   └── build.py                      # + research pass: map_research() → engine.add_triple(); catch ResearchError
├── core/manifest.py                  # (read-only use) book.language drives the translation-presence rule
└── resources/vocabularies/
    └── sources.ttl                   # NEW — bw: properties + 6 source-type + 3 reliability E55_Type individuals

tests/
├── golem/
│   └── test_provenance_entities.py   # NEW — Source/Finding/Anchor triples, URIs, open finding, time-span
├── io/
│   └── test_research.py              # NEW — map_research parsing, vocabulary rejection, translation rule, empty dir
└── commands/graph/
    ├── conftest.py                   # + with_research scaffolder (off by default): _index.md, sources.md, <topic>.md
    └── test_research_build.py        # NEW — graph build + graph query over the with_research tiny_novel (US1–US3)
```

**Structure Decision**: single Python package, src-layout (Constitution III). The
three provenance entities join the existing GOLEM module tree as a new
`modules/provenance.py` (mirroring `modules/inference.py`); the reader mirrors
`io/bible.py` as `io/research.py` exactly as the hint and design § 20.5 direct.
The build command grows a second mapping pass alongside the existing bible pass —
no new command, no new sub-package.

## Complexity Tracking

> No Constitution violations. Section intentionally empty.
