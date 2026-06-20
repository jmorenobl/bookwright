# Implementation Plan: Propp/Greimas vocabularies as `E55_Type` + references

**Branch**: `030-narrative-vocabularies` | **Date**: 2026-06-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/030-narrative-vocabularies/spec.md`

## Summary

The narrative-structure layer already enters the graph (G9/G10/G7, iterations
028–029) but its functions and roles are **identity-only** nodes: a function
named *departure* is not recognized as Propp's *departure*. GOLEM's `E55_Type`
controlled-vocabulary pattern (design § 4.4), already used by `sources.ttl`
(iteration 012) and by `CharacterFeature`'s biographical types, lets us type
those nodes **without touching the frozen ontology**.

Technical approach, in one breath: **populate** the two stub vocabulary files
(`propp.ttl` = Propp's 31 functions, `greimas.ttl` = the 6 actants) as
`crm:E55_Type` individuals carrying ES+EN `rdfs:label`s, exactly mirroring
`sources.ttl`; add a tiny **build-time loader** (`io/vocabularies.py`) that
parses the bundled TTL of each *active* vocabulary (read from the existing
`manifest.vocabularies.active` list) and builds a `slug → term-URI` index from
the labels — so the TTL is the single source of truth and Python hardcodes no
term URI; give `NarrativeFunction` (G10) and `CharacterRole` (G11) an optional
`type_uri` that, when set, emits `crm:P2_has_type <term>` (+ `<term> a
crm:E55_Type`) and a matching `DerivedAssertion` so the link is reified as a
`crm:E13_Attribute_Assignment` like every other GOLEM triple (FR-013); resolve
that `type_uri` in the IO builders — Propp for functions in `io/outline.py`,
Greimas for roles in the character pass — gated on activation; and rewrite the
two `references/*.md` so their canonical match-names agree with the populated
terms (SC-005). `golem.ttl` is untouched (FR-002/SC-006).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II).

**Primary Dependencies**: `rdflib` (parse the bundled vocab TTL + emit triples),
`pydantic` v2 (the frozen entity fields), `python-slugify` via
`golem.slug.make_slug` (the match key), `importlib.resources` (read the packaged
`resources/vocabularies/*.ttl`). No new runtime dependency — all are already in
the locked set (Constitution II / Technical Constraints).

**Storage**: plain text. Vocabulary terms live in `resources/vocabularies/{propp,greimas}.ttl`
(Turtle); the typing links land in the derived `bible/graph.ttl` cache, always
rebuildable from source (Principle I). No binary store.

**Testing**: `pytest` (≥ 80 % coverage gate). New unit tests in `tests/io/`
(vocabulary loader + function/role typing), `tests/golem/` (entity emission +
derived assertions), and `tests/resources/` (the populated TTLs parse; the two
references agree with the terms — SC-005).

**Target Platform**: CLI / library (POSIX + Windows), offline.

**Project Type**: single project (src-layout, `src/bookwright/`).

**Performance Goals**: build-time only; parsing two small TTLs (≤ 31 terms) once
per build is negligible. The loader is `lru_cache`d by vocabulary name.

**Constraints**: deterministic, byte-for-byte stable output (SC-004); zero
change when no vocabulary is active (FR-008/SC-003); no class added to the frozen
17-class ontology (Principle X / FR-002); every touched source file ≤ 500 lines
(Principle IV).

**Scale/Scope**: 31 Propp terms + 6 Greimas terms; two reference docs; one new
~70-line module; small, additive edits to four existing modules + the pipeline.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I — Plain text as source of truth | ✅ | Terms are Turtle; typing lands only in the derived `graph.ttl` cache; the TTL is the single source the loader reads (no hardcoded term URIs in Python). |
| II — Modern Python stack | ✅ | No new dependency; rdflib/pydantic/slugify/importlib.resources only. |
| III — src-layout | ✅ | New module under `src/bookwright/io/`; tests under `tests/`. |
| IV — Modular command surface / ≤ 500 lines | ✅ | New `io/vocabularies.py` is small; edits to existing modules stay well under 500 lines (largest, `io/bible.py`, is 421). No new CLI verb. |
| V — Plugin-based integrations | ✅ | Untouched. |
| VI — Agent Skills only | ✅ | Only `references/*.md` (skill resources) change; no command directory written. |
| VII — agentskills.io compliance | ✅ | References are offloaded reference material (the standard's `references/` tier); SKILL bodies unchanged. |
| VIII — Test discipline (≥ 80 %) | ✅ | New behavior is fully unit-tested; coverage gate enforced in CI. |
| IX — JSON-over-stdout | ✅ | No CLI output shape changes; `graph build`/`status` envelopes unchanged. |
| X — Design document axioms / frozen ontology | ✅ | **No class added to `golem.ttl`** (FR-002/SC-006); terms are `E55_Type` individuals in the separate vocab files, reusing `CLASS_IRI["Type"]` (already bound). Pattern is design § 4.4, an axiom we *follow*, not reopen. |

**Scope & Release Discipline**: this is v0.4 iteration 030 — the real
"Propp/Greimas" payoff named in the milestone. It adds no deferred/cancelled
capability and no speculative plumbing (FR-007 explicitly declines a `type:`
authoring surface). Activation reuses the existing `[vocabularies] active`
mechanism (FR-003) rather than inventing one. **No gate violation; Complexity
Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/030-narrative-vocabularies/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (loader location, term URIs, provenance granularity, canonical sets)
├── data-model.md        # Phase 1 — vocab terms, entity field additions, derived-assertion shape
├── quickstart.md        # Phase 1 — runnable validation of typing on a Propp/Greimas project
├── contracts/
│   └── vocabulary-typing.md   # Phase 1 — the C1–C10 behavioral contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── resources/
│   ├── vocabularies/
│   │   ├── propp.ttl            # POPULATE: 31 E55_Type function terms (ES+EN labels)
│   │   └── greimas.ttl          # POPULATE: 6 E55_Type actant terms (ES+EN labels)
│   └── commands/references/
│       ├── propp-functions.md   # REWRITE: enumerate the 31 by canonical match-name (SC-005)
│       └── greimas-actants.md   # UPDATE: surface each actant's ES+EN match-names (SC-005)
├── io/
│   ├── vocabularies.py          # NEW: load active vocab TTL → slug→term-URI index
│   ├── bible.py                 # EDIT: thread the Greimas index into the character pass
│   ├── _bible_builders.py       # EDIT: _build_character resolves role types from the Greimas index
│   └── outline.py               # EDIT: _mint_functions resolves Propp types
├── golem/modules/
│   ├── narrative.py             # EDIT: NarrativeFunction gains optional type_uri (+ to_triples/derived_assertions)
│   ├── feature.py               # EDIT: CharacterRole gains optional type_uri (+ to_triples)
│   └── character.py             # EDIT: Character.role_types map → typed CharacterRole; derived_assertions yields role-type E13
└── commands/_graph.py           # EDIT: load active vocabs from manifest, pass to map_bible/map_outline

tests/
├── io/
│   ├── test_vocabularies.py     # NEW: loader parse/resolve/disjointness, unknown-name handling
│   ├── test_outline.py          # EXTEND: Propp typing (match/no-match/inactive/ES form), E13 reification
│   └── test_bible.py (or new test_character_roles)  # EXTEND: Greimas role typing
├── golem/
│   └── test_triples.py / test_derived_assertions.py  # EXTEND: type_uri emission + provenance
└── resources/
    └── test_vocabulary_references.py  # NEW: TTLs parse; references ↔ terms agree (SC-005)
```

**Structure Decision**: single project, src-layout (Constitution III). The one
new module is `io/vocabularies.py` — placed in `io/` because it reads packaged
resources with rdflib (file IO), which the `golem/` layer is forbidden to do
(`tests/golem/test_no_io.py`). It depends only on `golem.slug` + rdflib +
`importlib.resources`, so it introduces no cycle.

## Complexity Tracking

> No Constitution Check violations. Section intentionally empty.
