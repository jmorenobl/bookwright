# Data Model: Unify the narrative-unit identifier (iteration 049)

No GOLEM entity, ontology class, or property is added or modified (FR-007 /
Principle X). The feature is a presentation-layer change over data the derived graph
**already** carries. This document records the in-memory shapes the validator
reasons over and the one new helper.

## Entities (unchanged, for reference)

### `G9_Narrative_Unit` (the reported entity)

| Aspect | Value | Source |
|---|---|---|
| identity | `URIRef` (path segment `narrative-unit` + name slug) | `golem/modules/narrative.py` (`SluggedEntity`) |
| human name | authored `name` string | `NarrativeUnit.name` |
| `rdfs:label` | `(uri, RDFS.label, Literal(name))` — one triple | iteration 035, `golem/modules/narrative.py:50` |
| slug | URI tail (`uri.rsplit("/", 1)[-1]`) | derived in the validator |
| provenance | `relpath:line` via the existing `E13` path | `queries.resolve_source` |

The feature concerns **only** which of `name` / `slug` is printed — never the entity.

## Projection change: `queries.load_orphan_units`

| | Before | After |
|---|---|---|
| Signature | `load_orphan_units(indexer) -> list[str]` | `load_orphan_units(indexer) -> list[tuple[str, str \| None]]` |
| Element | `unit_uri` | `(unit_uri, label_or_None)` |
| Query | `SELECT ?unit … FILTER NOT EXISTS {…}` | `+ OPTIONAL { ?unit rdfs:label ?label }`, `SELECT ?unit ?label` |
| Order | sorted set of URIs | sorted by URI; smallest label per URI when (defensively) >1 |
| Empty graph | `[]` | `[]` (unchanged — rule stays inert, FR-006) |

`label` is `None` ⇔ the unit carries no `rdfs:label` (the FR-004 floor; impossible by
construction in the normal path since iteration 035 emits exactly one label per `G9`).

**Determinism**: results sorted by URI; per URI the lexicographically smallest label
is chosen, so two consecutive builds produce byte-identical pairs (SC-003).

**Sole caller**: `narrative_structure._orphan_beats` (verified by grep across `src/`
and `tests/`). Widening the return type is safe and local.

## New helper: `_unit_identifier(name, slug)`

A module-level pure function in `validation/validators/narrative_structure.py` — the
**single shared formatting point** (FR-005):

| Field | Type | Meaning |
|---|---|---|
| `name` | `str \| None` | the human authored name (graph `rdfs:label`, or `ref.entity`) |
| `slug` | `str` | the URI-tail fallback identifier |
| **returns** | `str` | `name` when truthy, else `slug` |

Validation rule: `return name if name else slug` — an empty-string label is treated
as missing (D4), so the floor never prints `''`.

### Call sites (two, by construction the only two)

| Rule | name arg | slug arg | result in normal path |
|---|---|---|---|
| `_orphan_beats` | `label` (from `load_orphan_units` pair) | `unit_uri.rsplit("/", 1)[-1]` | human name (was: slug) |
| `_unresolved_roles` | `ref.entity` | `unit_uri.rsplit("/", 1)[-1]` | `ref.entity` (unchanged) |

`_unresolved_roles`'s output is byte-identical to today's (FR-002): `ref.entity` is
always present, so the helper returns it; the only change is that it now flows
through the shared point (FR-005 / SC-006).

## What does NOT change

- `Violation` shape, severity (`warning`), `resolve_source` / `relpath:line` locator,
  the gate/exit-code contract, and **what each rule detects** (FR-006).
- The frozen ontology and `golem.ttl` (FR-007 / Principle X).
- The authored outline fixture cards (FR-008) — only expected oracle values move.
