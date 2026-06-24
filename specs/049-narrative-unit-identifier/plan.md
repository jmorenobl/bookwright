# Implementation Plan: Unify the narrative-unit identifier across `narrative_structure`'s two rules

**Branch**: `049-narrative-unit-identifier` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/049-narrative-unit-identifier/spec.md`

## Summary

`narrative_structure` names the **same** entity kind — a `G9_Narrative_Unit` —
two different ways: the orphan-beat rule (`_orphan_beats`) prints the opaque URI
**slug** (`'el-recuerdo-de-la-primera-marea'`), while the unresolved-role rule
(`_unresolved_roles`) prints the **human authored name** (`'La fechoría en el
muelle'`). DEBT-017. This iteration converges both onto the human authored name,
**alone** (no parenthetical slug — Clarifications 2026-06-24).

Technical approach: the `G9` unit already emits `(uri, rdfs:label, name)` (iteration
035, `golem/modules/narrative.py:50`), so the human name is SPARQL-queryable from the
already-loaded derived graph (FR-003) — no outline cross-reference, no rebuild.
Extend `queries.load_orphan_units` to return `(uri, label)` pairs via an `OPTIONAL
rdfs:label`, and render the identifier in **both** rules through one shared
module-level helper `_unit_identifier(name, slug)` that returns the human `name` when
present else the `slug` (FR-004/FR-005) — so the two surfaces cannot drift by
construction (the iteration-048 `anchor_handle` precedent). Only the printed
identifier changes; locator, severity, gate, and what each rule detects are untouched
(FR-006).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II, locked)

**Primary Dependencies**: `rdflib` (SPARQL through the `Indexer` seam), `pydantic`
v2 — no new dependency (FR-007 / Constitution II)

**Storage**: derived `bible/graph.ttl` (read-only here; a reconstructible cache,
Constitution I). The orphan rule already depends on a built graph to detect orphans;
label resolution rides the **same** already-loaded graph.

**Testing**: `pytest` (unit `tests/validation/test_narrative_structure.py` +
E2E `tests/e2e/test_narrative_workflow.py` over the `tiny-quest` fixture oracle)

**Target Platform**: CLI (`bookwright validate`)

**Project Type**: single project (src-layout `src/bookwright/`)

**Performance Goals**: N/A — one extra `OPTIONAL` clause on an existing query, no
new round trip per unit

**Constraints**: each changed source file ≤ 500 lines (Principle IV); frozen
ontology untouched (Principle X); deterministic, read-only validator (no graph
writes); a single observable delta (only the orphan-beat rule's printed identifier
changes)

**Scale/Scope**: ~2 source files (`validation/queries.py`,
`validation/validators/narrative_structure.py`) + oracle/test updates
(`test_narrative_structure.py`, `test_narrative_workflow.py`,
`tiny-quest/expected-narrative.md`) + `DEBT.md` + `bookwright-design.md § 13` note
+ the CLAUDE.md track-B index/table reconciliation. No new module, no new dependency.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I — plain-text source of truth**: PASS. The graph stays a derived, read-only
  cache; the human name comes from an `rdfs:label` triple already in the graph. No
  source-of-truth move; DEBT-017 closure is recorded in plain text (`DEBT.md`).
- **II — locked stack / no new dependency**: PASS. No new library; only existing
  `rdflib`/SPARQL through the `Indexer` seam.
- **IV — ≤ 500 lines per file, one CLI verb per module**: PASS. Both touched files
  stay well under 500 lines (`queries.py` ~225, `narrative_structure.py` ~107; the
  delta is a few lines each).
- **V/VI/VII — integrations / Agent Skills**: N/A (no integration or skill surface
  touched).
- **VIII — test discipline, ≥ 80 % coverage**: PASS. Oracles updated empirically with
  `uv run pytest`; the new helper + the extended query are exercised by the existing
  unit and E2E suites (a defensive missing-label test is added for FR-004).
- **IX — JSON envelope / errors below layers**: N/A (no envelope or error path
  changes; the message text inside an existing `Violation` is all that differs).
- **X — frozen ontology**: PASS. No class/property added; the `rdfs:label` triple is
  the one iteration 035 already emits.

**Result**: no violations. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/049-narrative-unit-identifier/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (validator message contract)
├── spec.md              # /speckit-specify output (already present)
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
└── validation/
    ├── queries.py                       # load_orphan_units: return (uri, label) pairs
    └── validators/
        └── narrative_structure.py       # _unit_identifier helper; both rules call it

tests/
├── validation/
│   └── test_narrative_structure.py      # orphan oracle: slug → human name; FR-004 floor
├── e2e/
│   └── test_narrative_workflow.py       # Group B B1 oracle assertion (rides the fixture)
└── fixtures/tiny-quest/
    └── expected-narrative.md            # orphan_beats[0].unit: omen-beat → "Omen Beat"

DEBT.md                                  # remove DEBT-017 (+ reconcile the closed-list line)
bookwright-design.md                     # § 13: both rules name the unit by its human name
CLAUDE.md                                # track-B prose + iteration table row 049
```

**Structure Decision**: Single project, src-layout. The change is confined to the
`validation/` layer (`queries.py` projection + the `narrative_structure` validator)
plus its oracles and the plain-text debt/design/index reconciliation. No new module
is introduced — FR-005's "single shared point" is a module-level function inside
`narrative_structure.py`, where **both** call sites already live, so a separate
helper module would be unjustified plumbing (Scope discipline).

## Complexity Tracking

> No Constitution violations — table intentionally empty.
