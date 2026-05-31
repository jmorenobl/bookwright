# Phase 1 — Data Model

Two layers change:

1. **GOLEM typed model (iteration-5 layer, extended here — R1a)**: new typed
   entities + `Character` fields + predicate constants so the documented bible
   frontmatter can be *constructed and emitted* with frozen terms.
2. **Indexer process model (new this iteration)**: the engine seam, the
   frontmatter reader, the bible mapper, the build report.

No term outside the frozen ontology is introduced; the iteration-5 term-closure
test (SC-003) extends to cover every new class/predicate.

---

## 0. GOLEM model extension (`src/bookwright/golem/`, R1a)

### New predicate constants (`namespaces.py`) — all ∈ `frozen_terms()`

| Constant | IRI | Use |
|---|---|---|
| `HAS_FEATURE` | `gc:GP0_has_feature` (GOLEM ns) | Character → `G17_Character_Feature` |
| `PLAYS` | `plays` in **ExtendedDnS** ns — see note | Character → `G11_Narrative_Role` |

> **Namespace note (must not be missed):** `plays`/`played-by`/`uses`/`setting`
> live in `http://www.ontologydesignpatterns.org/ont/dlp/ExtendedDnS.owl#`,
> which is **distinct** from the existing `DLP` constant
> (`…/DOLCE-Lite.owl#`, source of `participant`/`proper-part`/etc.). Add a new
> namespace constant (e.g. `EDNS`) + a bound prefix (e.g. `edns:`) in
> `bind_prefixes`. The `golem.ttl` examples that read `dlp:plays` are loose
> shorthand; the emitted Turtle binds the correct ExtendedDnS prefix.
| `HAS_TYPE` | `crm:P2_has_type` | feature → `E55_Type` (birth/death/category) |
| `HAS_DIMENSION` | `crm:P43_has_dimension` | feature → `E54_Dimension` |
| `HAS_VALUE` | `crm:P90_has_value` | dimension → literal value |
| (reuse) `RDFS.label` | `rdfs:label` | feature free-text label |

New `CLASS_IRI` entries: `Feature` → `gc:G2_Feature`, `CharacterFeature` →
`gc:G17_Character_Feature`, `Dimension` → `crm:E54_Dimension`, `Type` →
`crm:E55_Type`.

### New entity classes (`modules/feature.py`)

**`Dimension`** (`crm:E54_Dimension`) — a literal value carrier.

| Field | Type | Emits |
|---|---|---|
| `value` | `str` | `crm:P90_has_value "<value>"^^<datatype>` |
| `datatype` | `URIRef` (default `xsd:string`) | the literal datatype (e.g. `xsd:gYear`) |

**`CharacterFeature`** (`gc:G17_Character_Feature`) — a biographical/physical/
psychological trait.

| Field | Type | Emits |
|---|---|---|
| `label` | `str \| None` | `rdfs:label "<label>"` |
| `feature_type` | `URIRef \| None` | `crm:P2_has_type <E55 individual>` (e.g. birth/death) |
| `dimension` | `Dimension \| URIRef \| None` | `crm:P43_has_dimension <dim>` |

Identity token: slug of `label`, or a `uuid7` when label-less (mirrors
`AttributeAssignment`). `Dimension` is uuid7-identified.

### Extended `Character` (`modules/character.py`)

Adds two optional reference tuples; identity-only behaviour is preserved when
both are empty (existing iter-5 tests keep passing).

| Field | Type | Cross-ref edge |
|---|---|---|
| `features` | `tuple[CharacterFeature \| URIRef, ...] = ()` | `gc:GP0_has_feature` (multi) |
| `roles` | `tuple[NarrativeRole \| URIRef, ...] = ()` | `dlp:plays` (multi) |

`NarrativeRole` (G11) already exists (identity-only) and is reused as-is.

### E55_Type individuals
`birth` and `death` are minted once as `crm:E55_Type` individuals at stable URIs
(`<uri_base>type/birth`, `<uri_base>type/death`) and referenced by biographical
features. (Individuals of a frozen class — not new vocabulary; SC-001 unaffected.)

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

| Source | Concept | Identity | Frontmatter → emission |
|---|---|---|---|
| `bible/characters/*.md` | `Character` | slug of `name` (fallback: filename) | `name`→identity; `narrative_roles[]`→`NarrativeRole` + `dlp:plays`; `features[]`→`CharacterFeature`(label) + `GP0_has_feature`; `born`/`died`→biographical `CharacterFeature`(`P2_has_type` birth/death) + `E54_Dimension`(`P90_has_value` `xsd:gYear`) + `GP0_has_feature` |
| `bible/settings/*.md` | `Setting` | slug of `name` | identity (v0) |
| `bible/timeline.md` → items under `events:` | `NarrativeEvent` | slug of item `name`/`title` | `participants[]` → `dlp:participant` (resolved to character URIs) |
| `bible/relationships.md` → items under `relationships:` | `SocialRelationship` | slug of item `name` | `participants[]` → `dlp:participant` |

- **Unknown keys** (not in a concept's recognised set) → ignored, recorded in
  the report's `unknown_keys` (edge case; typo aid).
- The `events:` / `relationships:` collection-item schema is fixed in
  [contracts/bible-format.md](contracts/bible-format.md).

### Collision detection (FR-014)
`dict[(concept_name, slug)] -> path`; a second entity of the same `(concept,
slug)` raises `SlugCollisionError(identifier, first_path, second_path)` — hard
error, no graph written.

---

## 4. Provenance (`AttributeAssignment`, R6 / FR-011 / SC-006)

One iteration-5 `AttributeAssignment` per derived attribute assertion:

| Field | Value |
|---|---|
| `target` | the character/entity URI the assertion is about |
| `attribute` | the feature / role / event URI asserted (or the entity URI for the identity assertion) |
| `source` | `"<relpath>"` or `"<relpath>:<line>"` (from `key_lines`) |
| `premise` | `None` (v0) |

Emitted alongside the entity triples so SC-006 holds for every derived triple.

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
| `graph_path` | `str` | Relative path of written `bible/graph.ttl`. |

`status` derived: `"ok"`; exit 0 when `skipped` empty, else exit 4 (R7).

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
