# Implementation Plan: Outline ingestion — narrative units & functions (G9/G10)

**Branch**: `028-outline-narrative-units` | **Date**: 2026-06-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/028-outline-narrative-units/spec.md`

## Summary

Wire `outline/units/*.md` ingestion so plot beats become first-class `NarrativeUnit`
(G9) entities and their named `functions` become slug-deduplicated `NarrativeFunction`
(G10) entities, both citable by SPARQL — taking G9/G10 out of the deferral registry.
A unit's `roles` resolve by slug against the character-scoped narrative-role nodes
characters already materialize inline (soft-miss `UnresolvedReference` on no match,
never a mint). The engine reuses the iteration-025 `_DirSpec` / `_map_single_dir`
machinery and `io/_bible_builders.py` coercers verbatim; the outline-specific builder
and orchestration live in a **new sibling module `io/outline.py`** (`map_outline`),
imported one-way from `io.bible` / `io._bible_builders` so no cycle forms. `map_bible`
gains a small post-character pass that publishes a `roles_index` on `MapResult`; the
shared `_graph` pipeline calls `map_outline` right after `map_bible`, appending into the
same `MapResult` so there is no second result to merge. No `golem/` change (classes,
cross-refs, `CONCEPTS` registration all exist); no ontology growth (Principle X). The
authoring surface (`bookwright-outline` source command, project scaffold) and the
present-tense "outline is author-only" documentation are amended to match.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `rdflib`, `pydantic` v2, `pyyaml`, `python-slugify`, `typer`
(all already in the locked runtime set — no new dependency)

**Storage**: Plain text — `outline/units/*.md` (YAML front-matter) → GOLEM entities →
derived `bible/graph.ttl` cache (Turtle). No binary store (Principle I).

**Testing**: `pytest` (≥ 80 % coverage gate), `ruff check`/`format --check`,
`mypy --strict`

**Target Platform**: CLI / library, cross-platform

**Project Type**: Single project (src-layout `src/bookwright/`, `tests/` at root)

**Performance Goals**: N/A (deterministic one-pass build over a small authored corpus)

**Constraints**: Every source file ≤ 500 lines (Principle IV); JSON-over-stdout
contract for `graph build` unchanged (Principle IX); frozen 17-class ontology — no new
class/property (Principle X); Agent Skills only (Principles VI/VII).

**Scale/Scope**: A handful of unit cards per project; one new I/O module
(`io/outline.py`), one helper added to `io/bible.py`, two fields on `_MapContext`,
registry/parity/test/scaffold/docs edits. No `golem/` edit.

## Constitution Check

*GATE: re-checked after Phase 1 design — still passing.*

- **I. Plain Text as Source of Truth** — PASS. `outline/units/*.md` is Markdown +
  YAML front-matter; the graph stays a derived, reconstructible Turtle cache.
- **II. Modern Python Stack** — PASS. No new runtime dependency; reuses `rdflib` /
  `pydantic` / `pyyaml` / `python-slugify`.
- **III. src-layout** — PASS. New module under `src/bookwright/io/`; tests under
  `tests/`.
- **IV. Modular Command Surface / ≤ 500 lines** — PASS. New `io/outline.py` (~140 lines)
  holds the outline builder + orchestration; `io/bible.py` (399 → ~420) and
  `io/_bible_builders.py` (269 → ~275) stay well under 500. No new CLI subcommand —
  ingestion rides the existing `graph build` / `status` pipeline.
- **V. Plugin-Based Integrations** — PASS. No integration change beyond the
  `bookwright-outline` source-command text the existing materializer consumes.
- **VI/VII. Agent Skills Only / agentskills.io** — PASS. The updated source command is
  re-materialized as one `SKILL.md` per integration through the iteration-9 pipeline;
  the `lint_skill_md` gate keeps `name`/`description`/front-matter valid; bilingual
  triggers preserved.
- **VIII. Test Discipline** — PASS. Unit/integration tests cover round-trip, dedupe,
  role resolution, soft-miss, no-frontmatter skip, slug collision, absent directory;
  the parity test stays green with G9/G10 alive; coverage stays ≥ 80 %.
- **IX. JSON-over-stdout** — PASS. `graph build --json` envelope is unchanged; the new
  entities flow through the existing `BuildReport` counters.
- **X. Design Document Axioms / frozen ontology** — PASS. No `golem/` edit: `NarrativeUnit`,
  `NarrativeFunction`, both `crm:P67_refers_to` cross-refs, and the `CONCEPTS` entries
  already exist. `golem.ttl` and the 17-class closure are untouched.

**No violations — Complexity Tracking is empty.**

## Project Structure

### Documentation (this feature)

```text
specs/028-outline-narrative-units/
├── plan.md              # This file
├── research.md          # Phase 0 — the two design decisions
├── data-model.md        # Phase 1 — entities, indices, provenance, failure modes
├── quickstart.md        # Phase 1 — runnable validation walkthrough
├── contracts/
│   └── outline-units-ingestion.md   # the units-pass behavioural contract
├── checklists/
│   └── requirements.md  # (from /speckit-specify)
└── tasks.md             # Phase 2 — /speckit-tasks (NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── io/
│   ├── bible.py             # + _index_character_roles pass; roles_index on MapResult
│   ├── _bible_builders.py   # + roles_index / functions_index fields on _MapContext
│   ├── outline.py           # NEW — map_outline + _build_unit (units pass)
│   └── manuscript.py         # amend the iteration-024 "author-only" note (FR-014)
├── commands/
│   └── _graph.py            # call map_outline after map_bible, same MapResult
├── golem/
│   └── deferrals.py         # remove NarrativeUnit / NarrativeFunction; "Five"→"Three"
└── resources/
    ├── commands/
    │   └── bookwright-outline.md   # instruct outline/units/ cards (Spanish prose)
    └── project/outline/units/      # NEW scaffold dir (.gitkeep, mirrors bible/settings/)

tests/
├── io/
│   └── test_outline.py      # NEW — round-trip, dedupe, role resolve, soft-miss,
│                            #       no-frontmatter skip, slug collision, absent dir
├── golem/
│   └── test_ingestion_parity.py   # EXPECTED_REACHABLE/ORPHAN_NAMES/EXPECTED_VERSIONS
│                                   # + len==3; drift probes confirmed unchanged
├── commands/init/           # scaffold test asserts outline/units/ present
└── fixtures/parity-exercise/outline/units/   # NEW card with ≥1 functions name

docs/authoring.md            # amend the v0.3 "outline author-only" note (Spanish)
bookwright-design.md         # § 7 tree + new § 7.4 ingestion subsection +
#                              skill-output table sweep: /bookwright-outline gains
#                              outline/units/*.md; /bookwright-bible gains the
#                              omitted bible/objects/*.md (same class) (Spanish)
```

**Structure Decision**: Single project, src-layout. The new ingestion lives in a
sibling I/O module `io/outline.py` (the spec's blessed alternative), because `map_bible`
walks **named** per-concept directories under `bible_dir` rather than generic ones, and
`outline/` is a sibling tree resolved via `manifest.paths.outline`. The sibling imports
the generic dir-walking engine (`_DirSpec`, `_map_single_dir`) and the coercers one-way
from `io.bible` / `io._bible_builders`; nothing in those imports `io.outline`, so the
acyclic-layer invariant (Principle IX) holds.

## Complexity Tracking

*No Constitution violations — no entries.*
