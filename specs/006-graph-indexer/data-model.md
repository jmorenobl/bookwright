# Phase 1 — Data Model

This iteration introduces only the **indexer process model** (engine seam,
frontmatter reader, bible mapper, build report). The GOLEM typed model it needs
was completed in **iteration 5 and is on `main`** — see §0 for the dependency
surface this iteration consumes. No term outside the frozen ontology is
introduced.

---

## 0. Dependency: the iteration-5 GOLEM API (on `main`, consumed as-is)

The model the bible mapper builds against. **The mapper does not construct
feature/role/dimension nodes itself** — it passes frontmatter values straight to
the entity constructors, which materialize the sub-nodes deterministically. All
emitted classes/predicates are members of `frozen_terms()` (SC-001), guarded by
iteration-5's closure test.

### `Character` (`golem:G1_Character`) — `golem/modules/character.py`

```python
Character(uri_base=..., name=...,
          born: int | None = None,
          died: int | None = None,
          features: tuple[str, ...] = (),
          narrative_roles: tuple[str, ...] = ())
```
On construction it materializes (once, deduped by URI, character-scoped):
- each `features` string → a free-text `CharacterFeature` at
  `{character.uri}/feature/{slug}` emitting `golem:GP0_has_feature` + `rdfs:label`;
- `born`/`died` → a biographical `CharacterFeature` at
  `{character.uri}/feature/bio/{birth|death}` emitting `golem:GP0_has_feature`,
  `crm:P2_has_type {uri_base}type/{birth|death}` (a shared `crm:E55_Type`
  individual), and `crm:P43_has_dimension` → a `crm:E54_Dimension` carrying
  `crm:P90_has_value "YYYY"^^xsd:gYear` (4-digit/BCE-safe via `gyear_literal`);
- each `narrative_roles` string → a `CharacterRole` (`golem:G11_Narrative_Role`)
  at `{character.uri}/role/{slug}` emitting `edns:plays` + `rdfs:label`.

A character built with none of the four attributes emits only its `rdf:type`
assertion (identity-only behaviour preserved).

### Supporting types (also on `main`, **not** constructed by the mapper)
- `CharacterFeature` / `CharacterRole` / `Dimension` (`golem/modules/feature.py`)
  — inlined attribute carriers, excluded from the `CONCEPTS` registry.
- Namespaces/predicates: `HAS_FEATURE` (`gc:GP0_has_feature`), `PLAYS`
  (`edns:plays` — **ExtendedDnS** ns `…/ExtendedDnS.owl#`, distinct from the
  `DLP` = `…/DOLCE-Lite.owl#` constant), `HAS_TYPE`/`HAS_DIMENSION`/`HAS_VALUE`
  (`crm:P2`/`P43`/`P90`), `CLASS_IRI` for `G2_Feature`/`G17_Character_Feature`/
  `E54_Dimension`/`E55_Type`. The `edns:` prefix is bound by `bind_prefixes`.

### Other concepts the mapper uses unchanged
`Setting` (`G12`), `NarrativeEvent` (`G5`), `SocialRelationship` (`G4`) with
their existing `dlp:participant` edges; `AttributeAssignment` (`crm:E13`) for
provenance.

---

## 1. Indexer (engine seam)

### `Indexer` (Protocol — `indexers/base.py`)

| Method | Signature | Contract |
|---|---|---|
| `load` | `(ttl_path: Path) -> None` | Parse a Turtle file into the engine's graph. |
| `save` | `(ttl_path: Path) -> None` | Serialize to Turtle with short prefixes bound (FR-015); makes parent dirs. |
| `add_triple` | `(s, p, o) -> None` | Add one triple; accepts rdflib terms or `str`/`int`/`float`. |
| `query` | `(sparql: str) -> Iterable[dict[str, Any]]` | One dict per result row (var → str). Raises `InvalidQueryError` on malformed SPARQL. |
| `construct` | `(sparql: str) -> Indexer` | Run CONSTRUCT; return a new engine over the sub-graph. |
| `count` | `() -> int` | Triple count. |

`RdflibIndexer` wraps `rdflib.Graph`, binds prefixes in `__init__`, `count →
len(graph)`, `query` maps each `ResultRow` → `{var: str(value)}`.

### Registry (`indexers/__init__.py`)
- `INDEXER_REGISTRY: dict[str, type[Indexer]] = {"rdflib": RdflibIndexer}`.
- `resolve_indexer(name)` → class, or `UnknownIndexerError(name,
  available=sorted(INDEXER_REGISTRY))` (FR-007). No `GrafeoIndexer` (deferred).

---

## 2. Frontmatter reader (`io/frontmatter.py`)

`parse_frontmatter(text) -> Frontmatter`:

| Field | Type | Notes |
|---|---|---|
| `metadata` | `dict[str, Any]` | `yaml.safe_load` of the fenced block; `{}` if none. |
| `body` | `str` | Markdown after the fence. |
| `key_lines` | `dict[str, int]` | 1-based source line of each top-level key (provenance). |

Malformed YAML → caller raises `InvalidFrontmatterError(path, reason)`.

---

## 3. Bible mapping (`io/bible.py`) — type by location (R2)

The mapper reads frontmatter and calls the iteration-5 constructors; the model
emits the triples (§0). The mapper never assembles feature/role/dimension nodes.

| Source | Constructor call | Notes |
|---|---|---|
| `bible/characters/*.md` | `Character(uri_base, name, born?, died?, features=tuple(...), narrative_roles=tuple(...))` | identity = slug of `name` (fallback: filename); `born`/`died` must be int years |
| `bible/settings/*.md` | `Setting(uri_base, name)` | identity only (v0) |
| `bible/timeline.md` → items under `events:` | `NarrativeEvent(uri_base, name, participants=(...))` | participants resolved to character URIs → `dlp:participant` |
| `bible/relationships.md` → items under `relationships:` | `SocialRelationship(uri_base, name, participants=(...))` | participants resolved → `dlp:participant` |

- **Unknown keys** (not in a concept's recognised set) → ignored, recorded in
  the report's `unknown_keys` (edge case; typo aid).
- **Unresolved participants** (a `participants:` name matching no character slug
  built in the same run) → the entity is still constructed, only that
  participation edge is omitted, and the reference is recorded in the report's
  `unresolved_participants` (FR-019; soft warning, not a skip or failure).
  Resolution is a single in-build pass: characters are constructed first to
  populate a `slug → Character URI` index, then `events:`/`relationships:`
  participants are looked up against it.
- The `events:` / `relationships:` collection-item schema is fixed in
  [contracts/bible-format.md](contracts/bible-format.md).

### Collision detection (FR-014)
`dict[(concept_name, slug)] -> path`; a second entity of the same `(concept,
slug)` raises `SlugCollisionError(identifier, first_path, second_path)` — hard
error, no graph written. (Note: collisions are checked on the **top-level**
entity slug; character-scoped feature/role nodes are deduped internally by the
model.)

---

## 4. Provenance (`AttributeAssignment`, R6 / FR-011 / SC-006)

One iteration-5 `AttributeAssignment` per derived top-level entity (and, where a
line is locatable, per attribute assertion):

| Field | Value |
|---|---|
| `target` | the entity URI the assertion is about |
| `attribute` | the entity URI (or the feature/role/event URI when attaching to a specific assertion) |
| `source` | `"<relpath>"` or `"<relpath>:<line>"` (from `key_lines`) |
| `premise` | `None` (v0) |

Emitted alongside the entity triples so SC-006 holds for every derived entity.

---

## 5. Build report (`io/report.py`)

`BuildReport` (pydantic, frozen):

| Field | Type | Meaning |
|---|---|---|
| `files_processed` | `int` | Source files read (valid + skipped). |
| `entities` | `int` | Entities successfully constructed. |
| `triples` | `int` | `engine.count()` after build. |
| `skipped` | `list[SkippedFile]` | `{path, reason}` (FR-013). |
| `unknown_keys` | `list[UnknownKey]` | `{path, key}`. |
| `unresolved_participants` | `list[UnresolvedParticipant]` | `{path, entity, name}` — a `participants:` reference that matched no character slug; the edge is omitted, the entity kept (FR-019). |
| `graph_path` | `str` | Relative path of written `bible/graph.ttl`. |

Supporting models (frozen pydantic): `SkippedFile{path, reason}`,
`UnknownKey{path, key}`, `UnresolvedParticipant{path, entity, name}` — where
`entity` is the owning event/relationship slug and `name` is the unresolved
participant string.

`status` derived: `"ok"`; exit 0 when `skipped` empty, else exit 4 (R7).
`unknown_keys` and `unresolved_participants` are soft warnings — they populate
the report but never change the exit code.

---

## 6. Errors (`io/errors.py`, `indexers/errors.py`)

Each carries `.to_json()` (mirrors `core.errors`/`golem.errors`) for Principle IX.

| Exception | `code` | Raised when |
|---|---|---|
| `ProjectNotFoundError` | `not_a_project` | No `manifest.toml` in cwd/ancestors. |
| `MissingDirectoryError` | `missing_directory` | `bible/` or `manuscript/` absent. |
| `InvalidFrontmatterError` | `invalid_frontmatter` | Bad YAML / wrong types / missing required key (per-file, collected). |
| `SlugCollisionError` | `slug_collision` | Two entities of one type share an identifier (fatal). |
| `UnknownIndexerError` | `unknown_indexer` | Manifest names an unregistered engine. |
| `GraphNotBuiltError` | `graph_not_built` | `graph query` with no `bible/graph.ttl`. |
| `InvalidQueryError` | `invalid_query` | Malformed SPARQL. |
