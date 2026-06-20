# Implementation Plan: Narrative-structure continuity validator

**Branch**: `031-narrative-structure-validator` | **Date**: 2026-06-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/031-narrative-structure-validator/spec.md`

## Summary

Add the **first consumer** of the v0.4 narrative-structure layer: a built-in
continuity validator named `narrative_structure` that flags structural
incoherencies the author has lost track of. Two rules ship:

- **US1 / Rule a — orphan beat (firm core, P1)**: a `G9_Narrative_Unit` that is
  the member of **no** `G7_Narrative_Sequence`, answered purely by **SPARQL over
  the derived graph** (`FILTER NOT EXISTS { ?seq dlp:proper-part ?unit }`). This
  is the clean demonstration that the structural layer is SPARQL-citable.
- **US2 / Rule c — unresolved role (P2)**: a unit card whose `roles:` names a slug
  that resolves to no character role. The graph carries **no** edge for this, so
  the finding is re-surfaced from the structured `UnresolvedReference` records the
  outline ingestion **already** emits, reached through a new cached
  `ValidationContext.outline()` accessor (sibling of the existing `bible()`).

The validator plugs into the existing seam unchanged: it is **auto-discovered**
(no hand-registration), runs through `runner.py` with per-validator isolation,
recovers each `file:line` locator through the existing `E13`→source provenance
path (`queries.resolve_source`), emits the existing `Violation` shape through the
existing `--json` envelope, defaults to `warning` (advisory, never gates CI), and
adds **no** class or property to the frozen ontology. Rules (b) order-gap/duplicate
and (d) empty-sequence are intentionally not implemented (non-citable / structurally
unreachable — see spec Clarifications & Out of Scope).

## Technical Context

**Language/Version**: Python 3.11+ (src-layout, `uv`).

**Primary Dependencies**: `rdflib` (SPARQL over the `Indexer` seam), `pydantic` v2
(`MapResult`/`UnresolvedReference`), `typer`/`rich` (the `validate` verb). No new
runtime dependency.

**Storage**: none added. Reads the derived `bible/graph.ttl` cache (already built
to include the outline pass, iterations 028–029) via the `Indexer`; reads
plain-text source through the existing `map_bible`→`map_outline` pipeline. Writes
nothing (read-only validator contract, FR-008).

**Testing**: `pytest`. New `tests/validation/test_narrative_structure.py` (unit
fixtures: one incoherence of each kind fires; a clean fixture fires nothing; a
project with no `outline/units/` is inert) plus a `--json` envelope assertion in
the `validate` command test path. Coverage gate ≥ 80 % (single-sourced in
`pyproject`).

**Target Platform**: CLI, local/CI (cross-platform; deterministic byte-stable
output via the runner's total-order sort).

**Project Type**: single project (`src/bookwright/`).

**Performance Goals**: not perf-sensitive — one SPARQL `NOT EXISTS` over the
narrative layer plus one re-read of source through the cached `outline()` accessor
(read-once-per-run). No new hot path.

**Constraints**: Constitution I (graph is a derived cache, never source of truth),
IV (≤ 500 lines/file, one CLI subcommand per module — this adds no subcommand),
IX (`--json`, no new top-level keys), X (frozen ontology — no class/predicate
added). Findings are deterministic (FR-008) and advisory (`warning`, FR-013).

**Scale/Scope**: ~1 new validator module, 1 new `queries.py` helper + a `dlp`
prefix, 1 new `ValidationContext` accessor, 1 new test module + a `--json`
assertion. No changes to existing validators (FR-011).

## Constitution Check

*GATE: must pass before Phase 0 and re-checked after Phase 1.*

| Principle | Status | Note |
|---|---|---|
| I — plain-text source of truth | ✅ | Graph stays a derived cache; the validator only **reads** it and the source mappers; writes nothing (FR-008). Locators point at the authored card via existing provenance. |
| II — locked stack | ✅ | No new dependency; `rdflib`/`pydantic`/`typer` only. |
| IV — file size / one subcommand per module | ✅ | New `narrative_structure.py` is small; helpers live in `queries.py`; no new CLI subcommand (rides the existing `validate` verb). |
| V — plugin shapes, no monolith dispatcher | ✅ | Validator is auto-discovered by the existing `pkgutil` registry; no hand-registration, no new dispatcher (FR-002). |
| VI — Agent Skills only | ✅ | N/A — no integration output. |
| VIII — test discipline ≥ 80 % | ✅ | New test module covers both rules, the clean case, the inert case, the order-gap non-finding (FR-007), disable-by-name (US3), and the `--json` envelope. |
| IX — `--json` over stdout | ✅ | Reuses `Violation.to_json()` / `ValidationReport.to_json()`; **no** new top-level key (FR-003). |
| X — frozen ontology | ✅ | Queries/reads `G7/G9/G10/G11` + `dlp:proper-part` / `crm:P67_refers_to` only; adds **no** class or property (FR-012, SC-007). |

**No violations — Complexity Tracking is empty.** The one structural addition
(the `outline()` accessor) reuses the established cached-accessor pattern rather
than introducing a new mechanism (spec Clarifications, FR-006).

## Project Structure

### Documentation (this feature)

```text
specs/031-narrative-structure-validator/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions & rationale
├── data-model.md        # Phase 1 — entities, finding shapes, query
├── quickstart.md        # Phase 1 — runnable validation scenarios
├── contracts/
│   └── narrative-structure-validator.md   # the validator's behavioural contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/validation/
├── base.py                        # EDIT: add cached `ValidationContext.outline()` + `_outline` field
├── queries.py                     # EDIT: add `dlp` prefix + `load_orphan_units()` helper (reuse `resolve_source`)
├── registry.py                    # UNCHANGED — auto-discovers the new validator (FR-002)
├── runner.py                      # UNCHANGED — runs/dedups/sorts as-is
├── report.py                      # UNCHANGED — existing envelope (FR-003)
└── validators/
    └── narrative_structure.py     # NEW: the `narrative_structure` validator (US1 + US2)

tests/validation/
├── conftest.py                    # EDIT (additive): `units=` knob on `write_project` + an outline-aware graph builder
├── test_narrative_structure.py    # NEW: unit + behavioural tests for both rules, clean, inert, order-gap, disable
└── test_command.py                # EDIT (additive): a `--json` envelope assertion for an orphan-beat project
```

**Structure Decision**: single project, no new top-level layout. The validator
is one module in the existing `validation/validators/` package (auto-discovered),
its SPARQL lives in `validation/queries.py`, and its US2 data source is a new
cached accessor on the existing `ValidationContext` — every seam already exists.

## Complexity Tracking

*No Constitution violations — section intentionally empty.*
