# Implementation Plan: Index objects (G16) + `bible/objects/` scaffold + skill

**Branch**: `026-index-objects` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/026-index-objects/spec.md`

## Summary

Feed `bible/objects/*.md` into the GOLEM graph as first-class `G16_Object` nodes,
an exact mirror of `bible/settings/`: one identity-only entity per file, identity
from a required `name:`, fed into the research `entity_index` (so a research
`bears_on:` / `constrains:` link to an object resolves instead of degrading to a
soft-miss) but **not** into the participant `slug_index`. The `Object` class, its
`CLASS_IRI["Object"]` / `CONCEPTS` registration and its `path_segment` (`object`)
already exist ([golem/modules/character.py](../../src/bookwright/golem/modules/character.py))
— this iteration adds **only the ingestion path**: one `_DirSpec` + `OBJECT_KEYS`
in [io/bible.py](../../src/bookwright/io/bible.py), reusing the existing inline
`Setting`-style builder (`lambda meta, rp: Object(uri_base=uri_base,
name=_require_name(meta))`) with **no** dedicated builder in `_bible_builders.py`.

Around the ingestion path: add `bible/objects/.gitkeep` to the scaffold (mirroring
`settings/` and `locations/` — a placeholder, not a `.tmpl` or sample sheet);
teach the `/bookwright-bible` source command to write object front-matter and
re-materialize it through the existing iteration-9 pipeline for both `claude` and
`generic` (bilingual triggers preserved); drop `Object` from the iteration-024
deferral registry; and repin the ingestion-parity test so G16 is now observed as
a reachable concept.

There is **no module split** (done in iteration 025) and **no ontology change**
(Principle X): `G16_Object` is reused as-is. No CLI surface, no `--json` envelope,
no validator behavior changes. No object cross-refs and no object attribute beyond
identity (FR-012) — the v0 class is identity-only, exactly like `Setting`.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `rdflib` (graph/URIRef), `pydantic` v2 (frozen GOLEM
entities), `pyyaml` (front-matter), `python-slugify` (identity slugs). No new
dependency (Constitution II — none added).

**Storage**: plain text in/out. Source: `bible/objects/*.md`. Derived cache:
`bible/graph.ttl` (Turtle), reconstructible (Constitution I).

**Testing**: `pytest` with ≥ 80 % coverage; unit tests for the mapper
([tests/io/test_bible.py](../../tests/io/test_bible.py)), the parity guard
([tests/golem/test_ingestion_parity.py](../../tests/golem/test_ingestion_parity.py)),
the scaffold ([tests/commands/test_init_default.py](../../tests/commands/test_init_default.py)),
and the materialization pipeline ([tests/integrations/](../../tests/integrations/)).

**Target Platform**: local CLI / library (`src/bookwright/`).

**Project Type**: single project, src-layout (Constitution III).

**Performance Goals**: N/A — one extra one-entity-per-file directory pass over the
bible; same order as the existing settings pass.

**Constraints**: every source file ≤ 500 lines (Principle IV); frozen ontology, no
class/property added (Principle X); additive change with no observable
mapper-output change for existing inputs.

**Scale/Scope**: ~13 GOLEM concepts; this turns one orphan (G16) into a fed
concept. Touches one mapper module (one `_DirSpec` + one `frozenset`), one source
command, the scaffold tree, the deferral registry, the parity test pins, and one
test fixture.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Notes |
|---|---|---|
| I. Plain Text as Source of Truth | ✅ PASS | Objects are `bible/objects/*.md`; the graph stays a derived `graph.ttl` cache, reconstructible from text. |
| II. Modern Python Stack | ✅ PASS | No new runtime dependency; reuses `rdflib`/`pydantic`/`pyyaml`/`python-slugify`. |
| III. src-layout | ✅ PASS | No new module; edits live under `src/bookwright/`, tests under `tests/`. |
| IV. Modular Command Surface (≤ 500 lines) | ✅ PASS | `bible.py` (385 lines post-025 split) gains one `_DirSpec` + one `frozenset`; stays well under 500. No new builder in `_bible_builders.py`. |
| V. Plugin-Based Integrations | ✅ PASS | No new integration; `claude`/`generic` only, materialized through the existing pipeline. |
| VI. Agent Skills Only | ✅ PASS | The `/bookwright-bible` change re-materializes as `SKILL.md`; no `commands/` directory written. |
| VII. agentskills.io Compliance | ✅ PASS | Source-command edit re-lints through `generate_skill_md` → `lint_skill_md`; bilingual triggers preserved. |
| VIII. Test Discipline (≥ 80 %) | ✅ PASS | New unit/parity/scaffold tests; existing suite stays green; coverage threshold single-sourced, untouched. |
| IX. JSON-over-stdout | ✅ PASS | No CLI/envelope change. Objects feed the research `entity_index`, so a research link to an object resolves — *removing* a soft-miss, adding no new channel. |
| X. Design Document Axioms (frozen ontology) | ✅ PASS | `G16_Object` already in the frozen closure (`CLASS_IRI`, `CONCEPTS`); no class/property added. § 16 untouched. FR-011/FR-012 forbid any ontology or cross-ref addition. |

**Scope & Release Discipline**: this is iteration 026 of the v0.3.x hardening
track (patch `v0.3.3`), exactly as planned in `bookwright-implementation-plan.md`.
The single observable delta is objects being indexed; no deferred-but-not-due or
cancelled capability is pulled in, and FR-012 explicitly fences out the
future-only object cross-refs/attributes that would be speculative generality.

**Result**: PASS — no violations, Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/026-index-objects/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (mirror-settings shape, inline builder, no split, fixture/parity)
├── data-model.md        # Phase 1 — Object front-matter + the exact _DirSpec wiring
├── quickstart.md        # Phase 1 — runnable validation scenarios
├── contracts/
│   └── object-frontmatter.md   # Phase 1 — the ingestible front-matter + observable mapper outputs
├── spec.md              # /speckit-specify output
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── io/
│   ├── bible.py                # Add OBJECT_KEYS = frozenset({"name"}); add the objects _DirSpec
│   │                           #   (concept="Object", inline Setting-style builder, index=False,
│   │                           #   into_entity_index=True); import Object from bookwright.golem;
│   │                           #   add "OBJECT_KEYS" to __all__. ~5 lines net.
│   ├── _bible_builders.py      # UNCHANGED — reuses _require_name; no dedicated object builder.
│   └── research.py             # consumes result.entity_index (now also holds objects) — UNCHANGED
├── golem/
│   ├── modules/character.py    # Object class (G16, identity-only) — UNCHANGED
│   ├── deferrals.py            # DROP the Object entry (6 → 5); docstring "Six" → "Five", "(iteration 025+)" stays
│   ├── namespaces.py           # CLASS_IRI["Object"] already present — UNCHANGED
│   └── __init__.py             # CONCEPTS already registers Object — UNCHANGED
├── commands/_graph.py          # iterates result.mapped → triples + provenance — UNCHANGED
└── resources/
    ├── project/bible/objects/.gitkeep          # NEW — placeholder mirroring settings/ & locations/
    └── commands/bookwright-bible.md            # object authoring: name: front-matter; dirs to ensure; files-to-write

tests/
├── io/test_bible.py            # NEW object cases (round-trip + file:line provenance, skip, absent dir,
│                               #   collision, enters entity_index → research resolution, no soft-miss)
├── golem/test_ingestion_parity.py   # EXPECTED_REACHABLE(+Object)/ORPHAN_NAMES(−Object)/
│                               #   EXPECTED_VERSIONS(−Object)/len 6→5; repoint test_drift_undeclared_orphan
│                               #   to a still-deferred concept (PsychologicalState); docstrings 7→8 / 6→5
├── commands/test_init_default.py    # assert bible/objects/.gitkeep is scaffolded
└── fixtures/parity-exercise/bible/objects/   # NEW — one well-formed object .md so G16 is observed reachable
```

**Structure Decision**: single project, src-layout. No structural change at all —
this is the narrowest possible mirror of the iteration-025 settings/locations
shape: one `_DirSpec`, one `frozenset`, one inline builder reusing `_require_name`
and `Object`. The module split that 025 carried is already done, so `bible.py`
stays the single orchestration module and `_bible_builders.py` is untouched.

## Phase 0 — Research

See [research.md](research.md). Decisions resolved:

- **Builder shape — inline, no dedicated builder.** The objects `_DirSpec` uses
  the same inline lambda as settings (`lambda meta, rp: Object(uri_base=uri_base,
  name=_require_name(meta))`); `Object` is identity-only, so it needs no coercers
  and no `_build_object` in `_bible_builders.py`. Chosen over adding a dedicated
  builder (no logic to host — would be a one-line passthrough mirroring the
  already-inline settings builder) per the user's explicit instruction.
- **Index wiring.** `index=False` (objects are not event/relationship
  participants in v0) and `into_entity_index=True` (so research `bears_on:` /
  `constrains:` resolves) — identical to `Setting`. `into_settings_index` stays
  default `False` (objects are not a `setting:` resolution target). Chosen over
  feeding the participant `slug_index`, which would let an event/relationship
  resolve a participant to an object (out of scope, FR-003).
- **Mapping order is immaterial.** Objects carry no cross-ref to another concept
  (FR-012), so the objects pass may sit anywhere among the one-entity-per-file
  passes. Placed after the locations pass for readability (the entity dirs in
  source order: characters → settings → locations → objects).
- **Skip / absent / collision reuse the shared `_map_single_dir` contract.** A
  missing/empty/non-string `name` raises `InvalidFrontmatterError` via
  `_require_name` → the file is recorded under `skipped`, never a crash (FR-005);
  no `bible/objects/` directory → the `is_dir()` guard returns early (FR-006); two
  files slugging to the same identity → `_Collisions.record("Object", …)` raises
  the existing collision error (FR-004). No object-specific code paths are added.
- **Scaffold placeholder.** `bible/objects/.gitkeep` mirrors the existing
  `bible/settings/.gitkeep` and `bible/locations/.gitkeep` — a single empty
  keep-file, **not** a `.tmpl` mold or an example object sheet (FR-007,
  Assumptions). The scaffold has no object `.j2`, so the strict-undefined render
  test is unaffected.
- **Materialization.** The `SKILL.md` is generated from the packaged source
  command by `generate_skill_md`; editing
  `resources/commands/bookwright-bible.md` is the only authoring edit, and the
  existing integration tests regenerate + re-lint it for both `claude` and
  `generic` (FR-009). No committed `SKILL.md` to hand-edit; objects stay inline in
  the command body (no new `references/` file, mirroring settings/locations).
- **Parity fixture.** `parity-exercise` currently has no `bible/objects/`; add one
  well-formed object file so a real build observes `G16_Object` as a reachable
  `rdf:type` (FR-010, SC-003). The research-resolution assertion lives as a focused
  `test_bible.py` unit (object enters `entity_index`; `map_research` over that
  index yields no soft-miss for the object target), mirroring 025's
  `test_location_enters_entity_index_for_research_resolution`.

## Phase 1 — Design & Contracts

- [data-model.md](data-model.md) — the Object front-matter shape, the `Object`
  reuse, and the exact `_DirSpec` wiring (`OBJECT_KEYS`, the inline builder, the
  index flags, the `__all__` addition).
- [contracts/object-frontmatter.md](contracts/object-frontmatter.md) — the
  ingestible front-matter contract and the mapper's observable outputs per case
  (node + `file:line` provenance, entity-index entry, skip, absent, collision),
  tied to FR/SC IDs.
- [quickstart.md](quickstart.md) — runnable validation scenarios (build a fixture,
  assert G16 nodes with provenance, research resolution with no soft-miss, the
  skip/absent cases, the scaffold includes `bible/objects/`, the parity test green
  with G16 reachable, all four gates).

**Agent context update**: the `<!-- SPECKIT START/END -->` block in `CLAUDE.md` is
repointed to this plan.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
