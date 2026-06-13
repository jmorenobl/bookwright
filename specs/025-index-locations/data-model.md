# Phase 1 Data Model: Index locations (G13) + `bible.py` split

This feature adds **no** ontology classes or properties (Principle X). It adds one
ingestion path over an existing frozen class and splits one module. Two views
follow: the **domain** view (what enters the graph) and the **module-split** view
(what moves where).

## 1. Domain entities

### NarrativeLocation (G13) — existing frozen class, now fed

Defined in [golem/modules/setting.py](../../src/bookwright/golem/modules/setting.py),
**unchanged**:

| Aspect | Value |
|---|---|
| `golem_class` | `golem:G13_Narrative_Location` (`CLASS_IRI["NarrativeLocation"]`) |
| `path_segment` | `location` → URI `…/location/<slug>` |
| Identity | slug of `name` (`SluggedEntity`), computed once in `model_post_init` |
| `cross_refs` | `(CrossRef("setting", GENERIC_LOCATION),)` |
| `setting` field | `GolemEntity \| URIRef \| None = None` |
| Attributes (v0) | identity + optional `setting` only — **identity-only like Setting** |

Emitted triples (via the inherited `to_triples`):
1. `<location> rdf:type golem:G13_Narrative_Location` — always.
2. `<location> dlp:generic-location <setting>` — **iff** `setting is not None`.

Provenance (via `derived_assertions` → `build_provenance`):
- identity assertion → file-level provenance (`relpath`).
- the `setting` cross-ref → `relpath:line` of the `setting:` front-matter key
  (the model field name equals the front-matter key, so `key_lines["setting"]`
  resolves automatically).

### Location front-matter (the ingestible contract)

| Key | Required | Type | Meaning |
|---|---|---|---|
| `name` | yes | non-empty string | identity source; slug derives from it |
| `setting` | no | string | names a sibling `bible/settings/` setting |

Sensory prose sections (*Qué se ve / oye / huele / toca*, *Atmósfera dominante*)
remain human prose, **not** ingested. Unknown extra keys produce the existing
`unknown_keys` soft warning (only once an entity is produced).

### `dlp:generic-location` cross-ref — existing

`GENERIC_LOCATION` in [golem/namespaces.py](../../src/bookwright/golem/namespaces.py),
reused as-is. The edge runs location → setting.

## 2. Resolution & validation rules

| Rule | Source | Behavior |
|---|---|---|
| `name` missing/empty/non-string | FR-002, FR-007 | `InvalidFrontmatterError` → file **skipped** (`SkippedFile`) |
| `setting` absent / `null` | FR-002 | no edge, no warning |
| `setting` blank/whitespace string | D4 | treated as absent — no edge, no warning |
| `setting` non-string | FR-007, Edge Cases | `InvalidFrontmatterError` → file **skipped** |
| `setting` resolves in settings index | FR-003 | `dlp:generic-location` edge emitted |
| `setting` present, unresolved | FR-004 | one `UnresolvedParticipant`; node built, no edge, no abort |
| two locations → same slug | FR-006 | `SlugCollisionError` (concept `"NarrativeLocation"`) |
| no `bible/locations/` directory | FR-008 | no-op (`_map_single_dir` early-returns) |
| frontmatter-less v0 location file | FR-009 | unusable front-matter → **skipped** gracefully |

Ordering invariant: **settings are mapped before locations**, so the
settings-scoped index is fully populated when a location's `setting:` resolves.

## 3. Indices (mapper state)

| Index | Holds | Fed by | Consumed by | Change |
|---|---|---|---|---|
| `slug_index` (participants) | characters | `index=True` dirs | event/relationship participants | none — locations have `index=False` |
| `entity_index` (research targets) | characters, settings, events, **+ locations** | `into_entity_index=True` | research `bears_on:`/`constrains:` resolution (FR-005) | locations now added |
| `settings_index` (**new**) | settings | `into_settings_index=True` | location `setting:` resolution (FR-003/004) | new field on `_MapContext` |

## 4. Module-split map (behavior-preserving — FR-013)

New module **`src/bookwright/io/_bible_builders.py`** (imports only `golem`,
`io.errors`, `io.report`, stdlib — no import from `bible.py`):

| Moves to `_bible_builders.py` | Kind |
|---|---|
| `_Builder`, `_ItemBuilder` | type aliases |
| `MappedEntity`, `MapResult` | result dataclasses (public — re-exported by `bible.py`) |
| `_Collisions`, `_MapContext`, `_ItemContext` | internal dataclasses |
| `_require_name`, `_coerce_year`, `_coerce_str_list` | coercers |
| `_build_character`, `_resolve_interval`, `_build_event` | concrete builders |
| `_resolve_refs` | resolution helper |
| **`_resolve_setting`** (new), **`_build_location`** (new) | location builder + resolver |

| Stays in `bible.py` | Kind |
|---|---|
| `map_bible` | public entry point |
| `_map_single_dir`, `_map_collection`, `_map_collection_item`, `_build_item_index` | orchestration |
| `_safe_parse`, `_relpath`, `_slug_of`, `_record_unknown_keys` | orchestration helpers |
| `_DirSpec`, `_CollectionSpec` | spec dataclasses |
| `build_provenance` | public provenance emitter |
| `*_KEYS` constants + new `LOCATION_KEYS = frozenset({"name", "setting"})` | constants |

Re-export requirement: `bible.py` must `from ._bible_builders import (MapResult,
MappedEntity, _MapContext, _ItemContext, _Collisions, _build_character,
_build_event, _resolve_refs, _resolve_setting, _build_location, _require_name, …)`
so existing imports (`from bookwright.io.bible import map_bible`) and the
re-exported `MapResult`/`MappedEntity` keep resolving.

### Field/flag additions

- `_MapContext`: `+ settings_index: dict[str, URIRef] = field(default_factory=dict)`
- `_DirSpec`: `+ into_settings_index: bool = False`
- `_map_single_dir`: after a built entity, `if spec.into_settings_index:
  ctx.settings_index[_slug_of(entity)] = entity.uri` (mirrors the existing
  `into_entity_index` / `index` blocks).

### `map_bible` wiring (new locations pass, **after** settings)

```python
_map_single_dir(ctx, _DirSpec(
    directory=bible_dir / "locations",
    concept="NarrativeLocation",
    builder=lambda meta, rp: _build_location(uri_base, ctx, meta, rp),
    allowed_keys=LOCATION_KEYS,
    index=False,
    into_entity_index=True,
))
```

The settings `_DirSpec` gains `into_settings_index=True`.

## 5. Registry & test-pin deltas

| Artifact | Before | After |
|---|---|---|
| `DEFERRED_CONCEPTS` (deferrals.py) | 7 entries incl. `NarrativeLocation` | 6 entries; `NarrativeLocation` removed; docstring "Seven"→"Six" |
| parity `EXPECTED_REACHABLE` | 6 names | 7 names (`+ NarrativeLocation`) |
| parity `ORPHAN_NAMES` | 7 names | 6 names (`− NarrativeLocation`) |
| parity `EXPECTED_VERSIONS` | 7 keys | 6 keys (`NarrativeLocation` dropped) |
| parity `test_registry_well_formed` | `len == 7` | `len == 6` |
| parity module docstring | "Six … other seven are orphans" | "Seven … other six are orphans" |

`CARRIER_NAMES`, `CONCEPTS`, the frozen `CLASS_IRI` closure, and the drift-sim
tests are **unchanged**.
