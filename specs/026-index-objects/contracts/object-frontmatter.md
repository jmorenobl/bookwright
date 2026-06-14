# Contract: `bible/objects/*.md` front-matter → mapper output

The ingestible front-matter of a `bible/objects/<slug>.md` file and the mapper's
observable output for every case. This is the `bible/settings/` contract applied
to `G16_Object`. Source of truth: [io/bible.py](../../../src/bookwright/io/bible.py)
`map_bible` (the objects `_DirSpec`) + `_map_single_dir`.

## Ingestible keys

| Key    | Type            | Required | Notes |
|--------|-----------------|----------|-------|
| `name` | non-empty `str` | yes      | Identity source; slug derives from it. The only ingested key. |

`OBJECT_KEYS = frozenset({"name"})`.

## Observable outputs per case

| # | Input | Output | FR / SC |
|---|---|---|---|
| C1 | `name: "Excalibur"` | One `G16_Object` node, URI `{uri_base}object/excalibur`; `file:line` provenance on identity pointing at the `name:` key line; slug `excalibur` enters `result.entity_index` | FR-001, FR-002, SC-001 |
| C2 | A research finding whose `bears_on:` / `constrains:` names `"Excalibur"`, that object having been mapped | The link resolves to the object URI — **no** soft-miss for that target | FR-003, SC-002 |
| C3 | `name:` missing / empty / whitespace / non-string | File recorded under `result.skipped` (reason "missing or empty `name`"); no node; build continues | FR-005, SC-004 |
| C4 | No `bible/objects/` directory at all | No object nodes; output identical to pre-iteration build | FR-006, SC-004 |
| C5 | Two object files slugging to the same identity | `SlugCollisionError` raised (per-concept scope: `("Object", slug)`) — same as characters/settings | FR-004 |
| C6 | Object file with an extra unknown front-matter key (and a valid `name`) | One node **plus** an `unknown_keys` soft warning (recorded only because the file produced an entity); no abort | Edge Cases |

## Non-participation guarantees

- Objects do **not** enter the participant `slug_index`: an event/relationship
  `participants:` naming an object does **not** resolve to it (FR-003).
- Objects do **not** enter the `settings_index`: a location `setting:` naming an
  object does **not** resolve to it.
- No object cross-ref and no object attribute beyond identity is emitted (FR-012).

## Ontology guarantee

No class or property is added to `golem.ttl` / `CLASS_IRI` / `CONCEPTS`;
`G16_Object` is reused as-is (FR-011, Principle X).
