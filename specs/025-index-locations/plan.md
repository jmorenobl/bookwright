# Implementation Plan: Index locations (G13) + `bible.py` split

**Branch**: `025-index-locations` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/025-index-locations/spec.md`

## Summary

Feed `bible/locations/*.md` into the GOLEM graph as first-class
`G13_Narrative_Location` nodes, mirroring `bible/settings/`: one entity per file,
identity from `name`, plus an optional `setting:` that resolves against the
sibling settings index and emits the already-modelled `dlp:generic-location`
cross-ref. The class, the cross-ref and the `CONCEPTS` registration already exist
([golem/modules/setting.py](../../src/bookwright/golem/modules/setting.py)) — this
iteration adds **only the ingestion path** (a `_DirSpec` + builder in
[io/bible.py](../../src/bookwright/io/bible.py)), feeds locations into the research
`entity_index` so research links resolve, drops `NarrativeLocation` from the
iteration-024 deferral registry, teaches the `/bookwright-bible` source command to
write location front-matter, and retires the v0 shortcut text in design § 7.2.

Because [io/bible.py](../../src/bookwright/io/bible.py) is already at the 500-line
Principle IV ceiling, the locations builder ships **with** a behavior-preserving
extraction of the concrete builders/coercers/resolution helpers and the
context/result dataclasses into a sibling module
`io/_bible_builders.py`, leaving `bible.py` (the orchestration + spec wiring)
comfortably under the limit. The split is invisible to every caller and verified
by the existing bible tests staying green unchanged.

The ontology is untouched (Principle X): G13 and `dlp:generic-location` are reused
as-is. No CLI surface, no `--json` envelope, no validator behavior changes.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `rdflib` (graph/URIRef), `pydantic` v2 (frozen GOLEM
entities), `pyyaml` (front-matter), `python-slugify` (identity slugs). No new
dependency (Constitution II — none added).

**Storage**: plain text in/out. Source: `bible/locations/*.md`. Derived cache:
`bible/graph.ttl` (Turtle), reconstructible (Constitution I).

**Testing**: `pytest` with ≥ 80 % coverage; unit tests for the mapper
([tests/io/test_bible.py](../../tests/io/test_bible.py)), the parity guard
([tests/golem/test_ingestion_parity.py](../../tests/golem/test_ingestion_parity.py)),
and the materialization pipeline ([tests/integrations/](../../tests/integrations/)).

**Target Platform**: local CLI / library (`src/bookwright/`).

**Project Type**: single project, src-layout (Constitution III).

**Performance Goals**: N/A — one extra one-entity-per-file directory pass over the
bible; same order as the existing settings pass.

**Constraints**: every source file ≤ 500 lines (Principle IV); frozen ontology, no
class/property added (Principle X); behavior-preserving refactor (no observable
mapper-output change for existing inputs).

**Scale/Scope**: ~13 GOLEM concepts; this turns one orphan (G13) into a fed
concept. Touches one mapper module (split in two), one source command, one design
section, the deferral registry, the parity test pins, and one test fixture.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Notes |
|---|---|---|
| I. Plain Text as Source of Truth | ✅ PASS | Locations are `bible/locations/*.md`; the graph stays a derived `graph.ttl` cache, reconstructible from text. |
| II. Modern Python Stack | ✅ PASS | No new runtime dependency; reuses `rdflib`/`pydantic`/`pyyaml`/`python-slugify`. |
| III. src-layout | ✅ PASS | New module `src/bookwright/io/_bible_builders.py`; tests under `tests/`. |
| IV. Modular Command Surface (≤ 500 lines) | ✅ PASS (the point) | `bible.py` is at 500; the split drops it well under the ceiling and the new module is created under it. |
| V. Plugin-Based Integrations | ✅ PASS | No new integration; `claude`/`generic` only, materialized through the existing pipeline. |
| VI. Agent Skills Only | ✅ PASS | The `/bookwright-bible` change re-materializes as `SKILL.md`; no `commands/` directory written. |
| VII. agentskills.io Compliance | ✅ PASS | Source-command edit re-lints through `generate_skill_md` → `lint_skill_md`; bilingual triggers preserved. |
| VIII. Test Discipline (≥ 80 %) | ✅ PASS | New unit/parity tests; existing suite stays green; coverage threshold single-sourced, untouched. |
| IX. JSON-over-stdout | ✅ PASS | No CLI/envelope change; the soft-miss reuses the existing `unresolved_participants` channel (no new category). |
| X. Design Document Axioms (frozen ontology) | ✅ PASS | `G13_Narrative_Location` + `dlp:generic-location` already in the frozen closure; no class/property added. § 16 untouched. Design § 7.2 edit only **records** the shortcut's removal — it reopens no axiom. |

**Scope & Release Discipline**: this is iteration 025 of the v0.3.x hardening
track (patch `v0.3.2`), exactly as planned in `bookwright-implementation-plan.md`.
No deferred-but-not-due or cancelled capability is pulled in; the `bible.py` split
is internal plumbing riding inside the patch it enables (the observable delta is
locations being indexed), not a speculative-generality addition.

**Result**: PASS — no violations, Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/025-index-locations/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (split shape, settings-scoped index, soft-miss channel)
├── data-model.md        # Phase 1 — Location front-matter + module split map
├── quickstart.md        # Phase 1 — runnable validation scenarios
├── contracts/
│   └── location-frontmatter.md   # Phase 1 — the ingestible front-matter + observable mapper outputs
├── spec.md              # /speckit-specify output
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── io/
│   ├── bible.py                # Orchestration: map_bible, _map_single_dir/_map_collection,
│   │                           #   _DirSpec/_CollectionSpec, build_provenance, KEYS, _safe_parse.
│   │                           #   Adds the locations _DirSpec + LOCATION_KEYS; drops below 500 lines.
│   ├── _bible_builders.py      # NEW — concrete builders + coercers + resolution helpers + the
│   │                           #   context/result dataclasses (behavior-preserving extraction);
│   │                           #   adds _build_location + _resolve_setting + settings_index.
│   ├── report.py               # UnresolvedParticipant (reused as-is for the setting soft-miss)
│   └── research.py             # consumes result.entity_index (now also holds locations) — UNCHANGED
├── golem/
│   ├── modules/setting.py      # NarrativeLocation + dlp:generic-location cross-ref — UNCHANGED
│   ├── deferrals.py            # DROP the NarrativeLocation entry (7 → 6); docstring "Seven" → "Six"
│   └── __init__.py             # CONCEPTS already registers NarrativeLocation — UNCHANGED
├── commands/_graph.py          # iterates result.mapped → triples + provenance — UNCHANGED
└── resources/commands/bookwright-bible.md   # location authoring: name:/setting: front-matter; drop "no se indexa en v0"

tests/
├── io/test_bible.py            # NEW location cases (round-trip ±setting, soft-miss, skip, collision)
├── golem/test_ingestion_parity.py   # update EXPECTED_REACHABLE(+G13)/ORPHAN_NAMES(−G13)/EXPECTED_VERSIONS/len; docstring
└── fixtures/parity-exercise/bible/locations/   # NEW — harbor.md (with setting), + a no-setting location

bookwright-design.md            # § 7.2 rewritten to record G13 wired (shortcut retired); tree (opcional) note updated
```

**Structure Decision**: single project, src-layout. The only structural change is
the new sibling module `io/_bible_builders.py` (leading underscore = package
-internal, mirroring the existing private helpers convention). `bible.py` keeps the
public surface (`map_bible`, `build_provenance`, `MapResult`, `MappedEntity` —
re-exported from the builders module so every `from bookwright.io.bible import …`
keeps working).

## Phase 0 — Research

See [research.md](research.md). Decisions resolved:

- **Split shape** — extract the concrete builders/coercers/resolution helpers
  **and** the context/result dataclasses (`_MapContext`, `_ItemContext`,
  `MapResult`, `MappedEntity`, `_Collisions`) into `io/_bible_builders.py`; keep
  the orchestration + `_DirSpec`/`_CollectionSpec` + KEYS in `bible.py`. Direction
  is one-way (builders import nothing from `bible.py`), so there is no cycle.
  `bible.py` re-exports the moved public names. Chosen over moving only the
  `_DirSpec`/`_CollectionSpec` dataclasses (insufficient line relief and splits a
  builder from its coercers) and over a third "types" module (more files than the
  one-sibling instruction warrants).
- **Settings-scoped resolution index** — add `settings_index: dict[str, URIRef]`
  to `_MapContext` and an `into_settings_index: bool` flag to `_DirSpec`; the
  settings dir feeds it (in addition to its existing `into_entity_index`), and the
  locations builder resolves `setting:` against it. Chosen over reusing the
  participant `slug_index` (characters only) or the research `entity_index`
  (characters + settings + events) — both would resolve a `setting:` naming a
  character/event, violating the "scoped to settings" requirement (Edge Cases,
  Assumptions).
- **Soft-miss channel** — an unresolvable `setting:` reuses
  `UnresolvedParticipant` via `result.unresolved_participants` (one record:
  `path` = location file, `entity` = location name, `name` = the unresolved
  setting), per the 2026-06-14 clarification. No new warning category; the neutral
  rename of the type is deferred to iteration 027.
- **`setting:` value handling** — `None`/absent → no edge; blank/whitespace string
  → treated as absent (no edge, no warning); non-string → `InvalidFrontmatterError`
  → file skipped (Edge Cases); present resolvable string → `dlp:generic-location`
  edge; present unresolvable string → soft-miss + node still built.
- **Materialization** — the `SKILL.md` is generated from the packaged source
  command by `generate_skill_md`; editing
  `resources/commands/bookwright-bible.md` is the only authoring edit, and the
  existing integration tests regenerate + re-lint it for both `claude` and
  `generic`. No committed `SKILL.md` to hand-edit; locations stay inline (no new
  `references/` file, mirroring settings).

## Phase 1 — Design & Contracts

- [data-model.md](data-model.md) — the Location front-matter shape, the
  `NarrativeLocation` reuse, the `dlp:generic-location` edge, and the exact
  module-split map (what moves, what stays, the re-export list, the new
  `settings_index`/`into_settings_index`/`_build_location`/`_resolve_setting`).
- [contracts/location-frontmatter.md](contracts/location-frontmatter.md) — the
  ingestible front-matter contract and the mapper's observable outputs per case
  (node, edge, soft-miss, skip, collision), tied to FR/SC IDs.
- [quickstart.md](quickstart.md) — runnable validation scenarios (build a fixture,
  assert G13 nodes, the cross-ref edge, research resolution, the skip/absent
  cases, the parity test green, `bible.py` ≤ 500 lines, all four gates).

**Agent context update**: the `<!-- SPECKIT START/END -->` block in `CLAUDE.md` is
repointed to this plan.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
