# Implementation Plan: GOLEM Domain Model

**Branch**: `005-golem-domain-model` | **Date**: 2026-05-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-golem-domain-model/spec.md`

## Summary

Deliver a typed, in-memory domain model for the thirteen in-scope GOLEM
concepts (Character, Object, Event, Psychological State, Setting, Narrative
Location, Social Relationship, Relationship Role, Narrative Unit, Narrative
Function, Narrative Role, Narrative Sequence, Attribute Assignment). Each
concept is a frozen Pydantic v2 model that carries a deterministic,
project-scoped, immutable URI (`{uri_base}{segment}/{token}`) and knows how to
emit RDF triples that use only terms defined in a **frozen, vendored copy of
the GOLEM 1.1 ontology** (Turtle). A shared namespace/prefix registry lets a
collection of entities serialize together to compact Turtle and round-trip back
through `rdflib`.

Technical approach: a `GolemEntity` base in `golem/base.py` computes the slug
(via `python-slugify`, ASCII-only) and URI once at construction and yields the
`rdf:type` triple plus its own predicates; named concepts subclass it with a
class-level GOLEM class IRI and path segment; `AttributeAssignment` overrides
the identity token to a time-ordered `uuid_utils.uuid7()`. `golem/namespaces.py`
centralizes every prefix (GOLEM, RDF, RDFS, CIDOC-CRM, DOLCE) and the per-concept
class IRIs, and loads the frozen ontology so tests can assert term-closure
(SC-003). The ontology TTL is fetched once from upstream and committed under
`resources/schemas/golem-1.1/` with a `version.json` provenance record. No new
runtime dependencies are introduced.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II / III).

**Primary Dependencies**: `pydantic` v2 (frozen models), `rdflib` (triples +
Turtle serialization/parsing), `python-slugify` (ASCII slug, default mode),
`uuid-utils` (`uuid7()` for assertions). All already pinned in `pyproject.toml`
— **no new dependency**, so no constitutional amendment is required.

**Storage**: Plain text only. The frozen GOLEM ontology is vendored as Turtle
under `src/bookwright/resources/schemas/golem-1.1/golem.ttl`; its provenance is
`version.json` (JSON). No binary stores (Constitution I).

**Testing**: `pytest` with package-mirrored layout under `tests/golem/`
(matching the existing `tests/core/`, `tests/integrations/`, `tests/commands/`
convention — note this supersedes the `tests/unit/` sketch in design § 6).
Coverage ≥ 80 % on `src/bookwright/golem/` (Constitution VIII).

**Target Platform**: Library consumed in-process by later iterations (6 indexer,
10 validators); no standalone runtime.

**Project Type**: Internal Python library (single project, src-layout).

**Performance Goals**: N/A for v0 — construction and serialization are O(entities);
no throughput target. Determinism and correctness dominate.

**Constraints**: Identifiers MUST be byte-identical across runs (SC-002);
serialized output MUST use only frozen-ontology terms (SC-003) and MUST parse as
well-formed RDF (SC-004); identifiers MUST be immutable after construction
(FR-007); the model MUST NOT read the bible/manuscript or validate semantic
coherence (FR-014).

**Scale/Scope**: 13 concept classes across 6 module files, 1 base, 1 namespaces
module, 1 error module, 1 frozen-ontology resource + provenance record.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain Text as Source of Truth | ✅ PASS | Ontology vendored as Turtle; provenance as JSON. No binary/embedded store. |
| II. Modern Python Stack | ✅ PASS | Uses only already-approved deps (pydantic v2, rdflib, python-slugify, uuid-utils). No additions → no amendment. |
| III. src-layout | ✅ PASS | Code under `src/bookwright/golem/`; tests under `tests/golem/`. No test beside source. |
| IV. Modular Command Surface | ✅ PASS | 13 concepts split across 6 module files + base/namespaces/errors; every file budgeted ≤ 500 lines. Not a CLI command, but the ≤500-line ceiling is honored. |
| V. Plugin-Based Integrations | ✅ N/A | No integration code in this iteration. |
| VI. Agent Skills Only | ✅ N/A | No skills/commands emitted. |
| VII. agentskills.io Compliance | ✅ N/A | No SKILL.md generated. |
| VIII. Test Discipline | ✅ PASS | Unit tests for `golem/`; ≥ 80 % coverage; pytest/ruff/mypy-strict gates apply. |
| IX. JSON-over-stdout | ✅ PASS | Library, not a CLI command. Error types expose `to_json()` mirroring `core/errors.py` so downstream commands keep the contract. The only CLI touch — wiring `version.py` to the now-present ontology — already emits a single JSON doc. |
| X. Design Document Axioms | ✅ PASS | GOLEM as ontology, `rdflib` (not Grafeo) in v0, plain text — all consistent with § 16. No axiom reopened. |

**Result: PASS — no violations. Complexity Tracking section left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/005-golem-domain-model/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (slug, immutability, predicates, vendoring)
├── data-model.md        # Phase 1 — the 13 concepts, fields, URI patterns, triple shapes
├── quickstart.md        # Phase 1 — how a downstream caller uses the model
├── contracts/
│   └── golem_api.md     # Phase 1 — public Python API contract for iterations 6 & 10
└── tasks.md             # Phase 2 — created by /speckit-tasks (NOT here)
```

### Source Code (repository root)

```text
src/bookwright/golem/
├── __init__.py                 # public re-exports: the 13 classes, to_turtle(), errors, CONCEPTS registry
├── namespaces.py               # GOLEM/RDF/RDFS/CRM/DOLCE Namespaces, class-IRI map, bind_prefixes(), frozen-ontology loader + term set
├── base.py                     # GolemEntity (frozen Pydantic), slug/uri computation, to_triples(); SluggedEntity vs assertion token
├── slug.py                     # make_slug(name) -> str (python-slugify, ASCII), EmptySlugError on empty
├── errors.py                   # GolemError hierarchy with .to_json() (mirrors core/errors.py)
├── serialize.py                # to_turtle(entities, *) -> str via rdflib Graph + bound prefixes
└── modules/
    ├── __init__.py
    ├── character.py            # Character (G1_Character), Object (G16_Object)
    ├── relationship.py         # SocialRelationship (G4), RelationshipRole (G6)
    ├── event.py                # NarrativeEvent (G5), PsychologicalState (G3)
    ├── setting.py              # Setting (G12), NarrativeLocation (G13)
    ├── narrative.py            # NarrativeUnit (G9), NarrativeFunction (G10), NarrativeRole (G11), NarrativeSequence (G7)
    └── inference.py            # AttributeAssignment (E13_Attribute_Assignment)

src/bookwright/resources/schemas/golem-1.1/
├── __init__.py                 # package marker so importlib.resources can address it
├── golem.ttl                   # frozen ontology (vendored from upstream golem/golem_v1-1.ttl)
├── version.json                # provenance: repo + exact commit + file + versionIRI + retrieved date
└── VERSION                     # short label read by `bookwright version` (e.g. "golem-1.1")

# Touched (small integration), not new:
src/bookwright/commands/version.py                       # point _read_golem_schema_version() at resources/schemas/golem-1.1/VERSION
src/bookwright/resources/templates/manifest.template.toml # schema_version default golem-1.0 → golem-1.1 (D11)

scripts/
└── update-golem-schema.py      # dev-only: re-fetch + re-pin the ontology (one-time vendoring helper)

tests/golem/
├── __init__.py
├── conftest.py                 # uri_base + sample-entity fixtures
├── test_slug.py                # determinism, ASCII transliteration, empty-name rejection (FR-005/006)
├── test_uri.py                 # per-concept segment table + immutability (FR-003/004/007, US1)
├── test_namespaces.py          # prefixes bound, class-IRI map matches ontology (FR-010)
├── test_triples.py             # rdf:type assertion, cross-references, term-closure SC-003 (FR-008/015, US2)
├── test_turtle_roundtrip.py    # serialize → parse → isomorphic; well-formed RDF (FR-012, SC-004)
├── test_inference.py           # AttributeAssignment: verbatim source path, optional premise, uuid7 ordering (FR-009/013, US3)
└── test_frozen_ontology.py     # resource exists, version.json names repo + commit (FR-011, US4)

# Touched tests (iteration-2 artifacts, golem-1.0 → golem-1.1; D11):
tests/test_cli_version.py, tests/test_cli_subprocess.py  # update expected golem_schema_version
tests/core/test_load_valid.py, tests/core/test_build.py  # assert == "golem-1.1"
tests/core/fixtures/*.toml                               # schema_version filler golem-1.0 → golem-1.1
```

**Structure Decision**: Single-project src-layout exactly as design § 6 prescribes
for `golem/`, with one deviation made explicit: the 13 concepts are grouped into
the six GOLEM-module files (per the user's plan input and design § 4.2), and two
thin helpers (`slug.py`, `serialize.py`, `errors.py`) are split out of `base.py`
to keep every file well under the 500-line ceiling (Principle IV). Tests live in
`tests/golem/` mirroring the package, consistent with the repo's actual test
layout rather than the `tests/unit/` sketch in design § 6.

## Complexity Tracking

> No Constitution Check violations. This section is intentionally empty.
