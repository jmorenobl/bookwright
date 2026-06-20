# Phase 1 Data Model: Outline ingestion — narrative units & functions

All GOLEM classes, cross-refs, and `CONCEPTS` entries already exist
(`golem/modules/narrative.py`, `golem/modules/feature.py`). This iteration adds **no**
ontology and edits no `golem/` file. The model below documents what the io layer feeds.

## Entities (existing classes, newly fed)

### NarrativeUnit (G9) — `golem:G9_Narrative_Unit`

| Aspect | Value |
|---|---|
| Source | one `outline/units/*.md` card |
| Identity | `make_slug(name)` → URI `{uri_base}narrative-unit/{slug}` (`SluggedEntity`) |
| Front-matter | `name` (required, non-empty string), `functions` (optional list[str]), `roles` (optional list[str]) |
| Cross-refs (already declared) | `CrossRef("functions", REFERS_TO, multi=True)`, `CrossRef("roles", REFERS_TO, multi=True)` — both non-`owned` |
| Edges emitted | `unit crm:P67_refers_to function.uri` (one per distinct function slug); `unit crm:P67_refers_to role_uri` (one per matching character-scoped role node) |
| Body | **not ingested** (FR-003) |

### NarrativeFunction (G10) — `golem:G10_Narrative_Function`

| Aspect | Value |
|---|---|
| Source | minted by the units pass from each `functions` name |
| Identity | `make_slug(name)` → URI `{uri_base}narrative-function/{slug}` (identity-only) |
| Dedup | by slug across **all** units (`ctx.functions_index`); the first introducing unit appends one `MappedEntity`; later units reuse it |
| Triples | only its `rdf:type` (identity-only `SluggedEntity`) |

### Narrative role (G11, character-scoped) — read-only here

Already materialized inline by `Character` from `narrative_roles:` as `CharacterRole`
nodes with URI `{character.uri}/role/{make_slug(label)}`. The units pass **resolves**
`roles` names against these; it mints nothing.

## Indices threaded through the map

Two new fields on `_MapContext` (in `io/_bible_builders.py`):

| Field | Type | Populated by | Consumed by |
|---|---|---|---|
| `roles_index` | `dict[str, list[URIRef]]` | `map_bible` after the character pass (`_index_character_roles`) — slug → every matching character-scoped role URI | `_build_unit` role resolution |
| `functions_index` | `dict[str, NarrativeFunction]` | `_build_unit` as it mints functions | `_build_unit` dedup across units |

`roles_index` is **published on `MapResult`** so `map_outline` (operating on the same
`MapResult`) reads it. It is many-valued: one role slug played by C characters → C URIs.

The existing `slug_index`, `settings_index`, and research `entity_index` are untouched;
units feed none of them (`_DirSpec(index=False, into_entity_index=False)`).

## Resolution rules

### `functions` → mint + dedup

1. `functions = _coerce_str_list(meta["functions"], "functions")` — `None`→`()`; a
   non-list-of-strings raises `InvalidFrontmatterError` (card skipped).
2. Slug-dedup the names within the card.
3. For each distinct slug: if absent from `ctx.functions_index`, build
   `NarrativeFunction(uri_base, name)`, store it, and append a
   `MappedEntity(entity=function, relpath=<unit relpath>, key_lines={})`. Reuse the
   stored entity otherwise.
4. The unit's `functions` tuple = the (deduped) function entities → K unit→function
   edges (SC-002).

### `roles` → resolve (never mint)

1. `roles = _coerce_str_list(meta["roles"], "roles")`; coercion errors skip the card.
2. Slug-dedup within the card (clarification 2026-06-19).
3. For each distinct role slug: `matches = ctx.roles_index.get(slug, [])`.
   - `matches` non-empty → extend the unit's `roles` tuple with every URI in `matches`
     (one unit→role edge per match, SC-004).
   - `matches` empty → append exactly one `UnresolvedReference(path, entity=name,
     name=role_name)`; emit no edge; **still build the unit** (FR-005).

## Provenance (FR-010) — via existing machinery

`NarrativeUnit.derived_assertions()` is the base implementation (field names already
equal front-matter keys, no override): identity assertion (`source_field=None` →
file-level) + one per `functions` item tagged `"functions"` + one per `roles` item
tagged `"roles"`. `build_provenance` resolves each to `relpath:line` via the card's
`key_lines`, minting one `crm:E13_Attribute_Assignment` apiece. Each minted
`NarrativeFunction` contributes only its file-level identity assertion (its
`MappedEntity` carries the introducing card's `relpath`).

## Failure & edge-case handling (skip-and-continue, never abort)

| Input | Outcome |
|---|---|
| No front-matter / malformed YAML / unreadable bytes | `_safe_parse` records `SkippedFile`; build continues (FR-006) |
| `name` missing / empty / non-string | `_require_name` raises `InvalidFrontmatterError` → `SkippedFile` (FR-006) |
| `name` slugs to empty | `EmptySlugError` → `SkippedFile` |
| `functions`/`roles` not a list of strings | `_coerce_str_list` raises `InvalidFrontmatterError` → `SkippedFile`, **before** any function is minted (FR-007, ordering invariant) |
| Two unit `name` slugs collide | `_Collisions.record("NarrativeUnit", slug, …)` raises `SlugCollisionError` → build aborts (FR-008) |
| Function slug == role slug | separate identity spaces (`narrative-function/…` vs `{character}/role/…`); no collision/merge |
| No `outline/units/` directory | `_map_single_dir` returns immediately (`is_dir()` false); identical graph (FR-009, SC-006) |

## Deferral registry & parity invariants after this change

- `DEFERRED_CONCEPTS` = exactly `{NarrativeSequence, RelationshipRole, PsychologicalState}`
  (3 entries).
- Parity test: `EXPECTED_REACHABLE` gains `NarrativeUnit`, `NarrativeFunction` (→ 10);
  `ORPHAN_NAMES` / `EXPECTED_VERSIONS` drop them; `len(DEFERRED_CONCEPTS) == 3`.
- The `parity-exercise` fixture's new unit card makes the **live build** emit G9/G10
  `rdf:type` IRIs, so reachability is observed, not asserted.
- Drift-simulation probes (`Character`, `NarrativeEvent`, `PsychologicalState`) are
  unchanged and stay green.
