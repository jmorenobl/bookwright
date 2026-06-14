# Phase 1 — Data Model: Index objects (G16)

This iteration adds **no** class or property to the frozen ontology (Principle X,
FR-011). It reuses the existing `Object` entity and adds one ingestion path. The
"data model" here is the object front-matter contract plus the exact `_DirSpec`
wiring.

## Entity (reused as-is)

### `Object` — `golem:G16_Object`

Defined in [golem/modules/character.py](../../src/bookwright/golem/modules/character.py):

```python
class Object(SluggedEntity):
    """A storyworld object (``golem:G16_Object``). Identity only in v0."""
    golem_class: ClassVar[URIRef] = CLASS_IRI["Object"]
    path_segment: ClassVar[str] = "object"
```

- **Identity-only**, exactly like `Setting`: its sole attribute is its identity
  (a slug derived from `name`). No attributes, no cross-refs (FR-012).
- Already registered in `CONCEPTS` and `CLASS_IRI` (and `namespaces.py` maps
  `"Object" → GOLEM["G16_Object"]`). Constructor signature:
  `Object(uri_base=<str>, name=<str>)` → URI `{uri_base}object/{slug(name)}`.
- `derived_assertions()` (from the base) yields exactly one identity assertion
  (`source_field=None`), so provenance is file-level on identity — the indexer
  resolves it to a `file:line` locator off the `name:` key line.

## Object front-matter contract

A `bible/objects/<slug>.md` file's YAML front-matter:

| Key    | Type            | Required | Meaning |
|--------|-----------------|----------|---------|
| `name` | non-empty `str` | **yes**  | Identity source; the slug derives from it. The **only** ingestible key. |

- Any prose body is human prose, not ingested.
- Any front-matter key other than `name` is an `unknown_keys` soft warning
  (recorded only once the file has produced an entity), never an abort.
- `name` missing / empty / not-a-string → unusable front-matter → the file is
  recorded under `skipped`, never a crash.

This is byte-for-byte the `SETTING_KEYS` contract.

## Mapper wiring (`io/bible.py`)

### New constant

```python
OBJECT_KEYS = frozenset({"name"})
```

placed beside `SETTING_KEYS` / `LOCATION_KEYS`; added to `__all__`.

### Import

`Object` added to the existing `from bookwright.golem import (...)` block (which
already imports `Setting`, `SocialRelationship`). `_require_name` is already
imported from `._bible_builders`.

### New `_DirSpec` in `map_bible`

Added after the locations pass (mapping order is immaterial — objects carry no
cross-ref, D3):

```python
_map_single_dir(
    ctx,
    _DirSpec(
        directory=bible_dir / "objects",
        concept="Object",
        builder=lambda meta, rp: Object(uri_base=uri_base, name=_require_name(meta)),
        allowed_keys=OBJECT_KEYS,
        index=False,
        into_entity_index=True,
    ),
)
```

`into_settings_index` is left at its default `False`.

### What stays unchanged

- `_bible_builders.py` — no `_build_object`; `_require_name` reused as-is.
- `_DirSpec` / `_map_single_dir` — the concept-agnostic single-dir machinery
  already handles skip (`InvalidFrontmatterError` / `EmptySlugError`), absent dir
  (`is_dir()` guard), collision (`_Collisions.record`), unknown keys, the
  participant index (`index`), the research index (`into_entity_index`), and
  `file:line` provenance via `MappedEntity.key_lines` + `build_provenance`.
- `commands/_graph.py` — iterates `result.mapped` → triples + provenance; objects
  flow through identically.
- `io/research.py` — consumes `result.entity_index` (now also holding objects);
  an object-targeted `bears_on:` / `constrains:` resolves with no soft-miss.

## Index participation (the `Setting` profile)

| Index | Object joins? | Effect |
|---|---|---|
| `slug_index` (participants) | ❌ (`index=False`) | objects are not event/relationship participants in v0 |
| `entity_index` (research targets) | ✅ (`into_entity_index=True`) | research `bears_on:` / `constrains:` to an object resolves (no soft-miss) |
| `settings_index` (location `setting:` targets) | ❌ (default `False`) | objects are not a `setting:` resolution target |

## Deferral registry (`golem/deferrals.py`)

Remove the `"Object"` entry; `DEFERRED_CONCEPTS` drops 6 → 5:

| Remaining key | `target_version` |
|---|---|
| `NarrativeUnit` | `v0.4` |
| `NarrativeFunction` | `v0.4` |
| `NarrativeSequence` | `v0.4` |
| `RelationshipRole` | `undecided` |
| `PsychologicalState` | `undecided` |

Module docstring counts "Six … six" → "Five … five" (the "(iteration 025+)"
wire-later note stays).

## Scaffold

`resources/project/bible/objects/.gitkeep` — one empty placeholder mirroring
`bible/settings/.gitkeep` and `bible/locations/.gitkeep`. No `.tmpl`, no sample.

## Parity test pins (`tests/golem/test_ingestion_parity.py`)

| Pin | Before | After |
|---|---|---|
| `EXPECTED_REACHABLE` | 7 entries | + `"Object"` → 8 |
| `ORPHAN_NAMES` | 6 entries | − `"Object"` → 5 |
| `EXPECTED_VERSIONS` | 6 entries | − `"Object"` → 5 |
| `len(DEFERRED_CONCEPTS) == 6` | 6 | `== 5` |
| `test_drift_undeclared_orphan` subject | `"Object"` | `"PsychologicalState"` |
| module/test docstrings | "Seven … six" | "Eight … five" |
