# Implementation Plan: Graph Indexer + `graph` Commands

**Branch**: `006-graph-indexer` | **Date**: 2026-05-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-graph-indexer/spec.md`

## Summary

Turn a project's plain-text bible into a queryable Turtle graph and expose two
read-only CLI verbs on top of a pluggable engine seam:

- `bookwright graph build` discovers bible source files, converts each file's
  YAML frontmatter into iteration-5 GOLEM entities, attaches CIDOC provenance,
  detects identifier collisions, and serializes every triple to
  `bible/graph.ttl`.
- `bookwright graph query "<SPARQL>"` loads that graph and runs a SPARQL query,
  rendering a table for humans or a single JSON document under `--json`.

Both verbs depend only on an `Indexer` Protocol (design § 12.1); the concrete
`RdflibIndexer` is selected through a name→class registry keyed on
`manifest.toml > [bookwright] indexer` (default `rdflib`). Adding a future
engine touches the registry only, never the command code.

**Two clarifications were resolved during planning** (the user delegated both
decisions; see [research.md](research.md) R1/R1a/R2 and the Clarifications
section of [spec.md](spec.md)):

1. **Frontmatter → triples, with frozen terms (R1).** Every documented character
   key maps to the term the frozen GOLEM/CIDOC ontology already defines for it:
   `narrative_roles[]` → `edns:plays → G11_Narrative_Role`; `features[]` →
   `golem:GP0_has_feature → G17_Character_Feature`; `born`/`died` → biographical
   `G17_Character_Feature` (`crm:P2_has_type` birth/death) with the year via
   `crm:P43_has_dimension → E54_Dimension —crm:P90_has_value→ xsd:gYear` (`edns:`
   = ExtendedDnS ns, distinct from DOLCE-Lite `dlp:`). Nothing is dropped and
   nothing new is minted, so FR-010 and SC-001 hold as written.
   **Consequence (R1a) — DONE:** iteration-5's identity-only model was extended
   to construct/emit these and **merged to `main`** (it also unblocks iteration
   10's validators). This iteration *consumes that model as-is*; see R1a in
   [research.md](research.md) and §0 of [data-model.md](data-model.md).
2. **Bible layout (R2).** The parser matches what `bookwright init` already
   scaffolds (design § 7): `bible/characters/*.md` and `bible/settings/*.md` are
   one-entity-per-file; `bible/timeline.md` and `bible/relationships.md` are
   single collection files. FR-009 is corrected to match.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution Principle II / Technical Constraints).

**Primary Dependencies**: `rdflib` (graph + Turtle + SPARQL), `typer` (CLI),
`rich` (human rendering on stderr), `tomlkit`/`pydantic` via the iteration-2
`Manifest`, the iteration-5 `bookwright.golem` package (now on `main` with the
character-attribute extension — `Character(born/died/features/narrative_roles)`,
`CharacterFeature`/`Dimension`, `AttributeAssignment`, `to_triples`, and the R1b
provenance seam `DerivedAssertion` + `derived_assertions()`), consumed
as-is; `python-slugify` (collision detection re-uses iter-5 slugs). **New runtime
dependency**: `pyyaml` for frontmatter — see Constitution Check Gate II.

**Storage**: Plain text only. Canonical output is Turtle at `bible/graph.ttl`.
No cache is written in v0 (Principle I — a cache may exist later only if
deterministically rebuildable; v0 always does a full rebuild).

**Testing**: `pytest` with `--cov-fail-under=80`. Unit tests for `indexers/` and
`io/`; integration tests for the `graph build` / `graph query` flows against a
`tiny-novel` fixture.

**Target Platform**: POSIX / macOS terminal CLI (matches existing classifiers).

**Project Type**: Single project (CLI), `src/bookwright/…` + `tests/`.

**Performance Goals**: rdflib is acceptable for graphs < 10k triples (design
§ 12.2) — the realistic ceiling for a single book. No specific latency target.

**Constraints**: Principle IX (single JSON doc on stdout under `--json`, human
prose to stderr); Principle IV (per-subcommand modules ≤ 500 lines); SC-001
(zero classes/predicates outside the frozen GOLEM vocabulary).

**Scale/Scope**: Two CLI verbs, one engine, one registry, a bible parser, a
frontmatter reader, provenance emission, a build report. No write-back, no
validators, no `GrafeoIndexer`, no manuscript prose mining (all out of scope).

## Constitution Check

*GATE: evaluated pre-Phase-0 and re-checked post-Phase-1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ PASS | Output is Turtle. No binary store. v0 writes no cache. |
| II. Modern Python stack | ⚠️ AMENDMENT REQUIRED | Adds `pyyaml` to runtime deps. See gate note below. |
| III. src-layout | ✅ PASS | New code under `src/bookwright/{indexers,io}/` + `commands/graph/`; tests under `tests/`. |
| IV. Modular command surface | ✅ PASS | `commands/graph/` package, one module per subcommand (`build.py`, `query.py`), all ≤ 500 lines. |
| V. Plugin-based integrations | ✅ PASS | `INDEXER_REGISTRY` name→class + `resolve_indexer()` factory mirrors the `INTEGRATION_REGISTRY` shape; no monolithic dispatcher (FR-005/008). |
| VI. Agent Skills only | ✅ N/A | This iteration emits no skills. |
| VII. agentskills.io compliance | ✅ N/A | No `SKILL.md` generated here. |
| VIII. Test discipline | ✅ PASS | ≥ 80% coverage; unit (`indexers/`, `io/`) + integration (`graph build`/`query`) per the pyramid. |
| IX. JSON-over-stdout contract | ✅ PASS | `build` and `query` accept `--json`; single JSON doc on stdout, human/progress on stderr; non-zero exit on error even with `--json`. |
| X. Design document axioms | ✅ PASS | No axiom is reopened: GOLEM stays the (frozen) ontology, rdflib stays the v0 engine, SC-001 is honored as written. The R1a model extension (now on `main`) used only terms already in `frozen_terms()` and did not change the frozen `golem.ttl` itself. |

**Gate II — `pyyaml` amendment (must clear before implementation).** Bible
frontmatter is YAML; no declared runtime dependency parses YAML. Hand-rolling a
YAML parser is rejected (fragile, unsafe with author-authored prose — fails the
spirit of Principles VIII/I). PyYAML 6.0.3 is already resolved transitively in
`uv.lock` but is **not** a declared direct dependency, so importing it in
production code requires adding `pyyaml>=6.0` to `[project].dependencies`.
Principle II makes that a **MINOR** constitution amendment (1.1.0 → 1.2.0) plus a
matching update to design § 14.1. This is a tracked prerequisite task (T0xx) and
is *not* a violation once the amendment lands — it is the sanctioned path the
constitution itself defines. No other new runtime dependency is introduced.

**Iteration-5 model extension (R1a) — DONE.** The `bookwright.golem` extension
(`CharacterFeature`/`CharacterRole`/`Dimension`, `Character.born/died/features/
narrative_roles`, the `EDNS` namespace + frozen-term predicate constants) was
implemented as a **completion of iteration 5** and merged to `main`. It is
additive (identity-only behaviour + tests preserved) and the iteration-5
closure test (SC-003) was extended to guard every new term. This iteration
consumes it as a dependency — no GOLEM-model work remains here.

**Iteration-5 provenance seam (R1b) — DONE.** A second additive completion of
iteration 5, also on `main`: `DerivedAssertion(target, attribute, source_field)`
+ `GolemEntity.derived_assertions()` (declarative default from `cross_refs`;
`Character` overrides to tag `born`/`died`/`features`/`narrative_roles`). This is
the source-agnostic seam US3 consumes to mint one `crm:E13` per derived assertion
(FR-011/SC-006) without reading the model's private node tuples or recomputing its
URI scheme — the model names the originating field, the indexer resolves the line.
Additive, backward-compatible, frozen terms only; `to_triples()` unchanged. All
four gates green on `main` (`pytest` 446 passed, 98% coverage).

**Result**: PASS, conditional only on the Gate II amendment task (`pyyaml`)
completing before any frontmatter-parsing code is written. No entries in
Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/006-graph-indexer/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions R1–R8
├── data-model.md        # Phase 1 — entities, mappings, report shape
├── quickstart.md        # Phase 1 — build/query walkthrough
├── contracts/
│   ├── cli-graph.md     # `graph build` / `graph query` CLI + JSON contract
│   ├── indexer.md       # `Indexer` Protocol + registry contract
│   └── bible-format.md  # Directory layout + frontmatter → GOLEM mapping
├── checklists/          # (already present)
└── tasks.md             # Phase 2 — created by /speckit-tasks (NOT here)
```

### Source Code (repository root)

```text
src/bookwright/
├── cli.py                       # + app.add_typer(graph.app, name="graph")
├── golem/                       # DEPENDENCY (on main) — consumed as-is, no edits this iteration
│   │                            #   Character(born/died/features/narrative_roles) materializes
│   │                            #   CharacterFeature/CharacterRole/Dimension (data-model §0)
├── indexers/                    # NEW — the pluggable graph-engine seam
│   ├── __init__.py              # INDEXER_REGISTRY, resolve_indexer(), re-exports
│   ├── base.py                  # Indexer Protocol (load/save/add_triple/query/construct/count) + Triple
│   ├── rdflib_indexer.py        # RdflibIndexer (the v0 default engine)
│   └── errors.py                # UnknownIndexerError, GraphNotBuiltError, InvalidQueryError
├── io/                          # NEW — plain-text → model parsing
│   ├── __init__.py
│   ├── project.py               # find_project_root() + ProjectNotFoundError
│   ├── frontmatter.py           # split `---` fences + yaml.safe_load → (meta, body, line_index)
│   ├── bible.py                 # discover + parse bible files → entities + provenance + BuildReport
│   ├── manuscript.py            # v0 presence check only (no prose mining)
│   ├── report.py                # BuildReport / SkippedFile pydantic models
│   └── errors.py                # MissingDirectoryError, InvalidFrontmatterError, SlugCollisionError
└── commands/
    └── graph/                   # NEW — per-subcommand modules (Principle IV)
        ├── __init__.py          # graph Typer sub-app; wires build + query
        ├── build.py             # `graph build` orchestration
        ├── query.py             # `graph query` orchestration
        └── envelope.py          # graph-command JSON success/error envelopes

tests/
│   # (tests/golem/* for the model extension already landed with iteration 5 on main)
├── indexers/
│   ├── test_registry.py         # default, explicit, unknown-name error (US4)
│   ├── test_rdflib_indexer.py   # load/save/add/query/construct/count round-trip
│   └── test_query_errors.py     # invalid SPARQL, empty result (US2)
├── io/
│   ├── test_frontmatter.py      # fence edge cases, line indexing
│   ├── test_bible.py            # type-by-location, mapping, collisions, skips (US1/US5)
│   └── test_project.py          # find_project_root / not-a-project
└── commands/
    └── graph/
        ├── conftest.py          # tiny-novel fixture builder
        ├── test_build.py        # build happy path, --force, missing dirs, report (US1/US5)
        ├── test_query.py        # SELECT rows, --json shape, empty, invalid (US2)
        ├── test_provenance.py   # E13 assignment names source path/line (US3)
        └── test_json_contract.py # stdout-only-JSON / stderr-prose invariant (Principle IX)
```

**Structure Decision**: Single-project CLI, extending the existing
`src/bookwright/` tree. The `golem/` package (with the R1a character-attribute
extension) is already on `main` and is consumed unchanged. Three new packages —
`indexers/` (engine seam),
`io/` (plain-text parsing), and `commands/graph/` (the two verbs) — keep the
engine, the parser, and the CLI surface independently testable and each module
under the 500-line ceiling. The engine owns Turtle serialization (binding the
short prefixes from `golem.namespaces.bind_prefixes`), so no separate
`io/turtle.py` is introduced; the iteration-5 `to_triples()` output is fed into
the engine via `add_triple`.

## Complexity Tracking

> No constitutional violations require justification. The `pyyaml` addition is a
> sanctioned MINOR amendment (Gate II), not a violation, and is tracked as a
> prerequisite task rather than here.
