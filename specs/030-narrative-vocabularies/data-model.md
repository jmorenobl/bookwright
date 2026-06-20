# Phase 1 Data Model: Propp/Greimas typing

This feature adds **no GOLEM class** (Principle X / FR-002). It populates two
controlled vocabularies and adds one optional, non-identity attribute to two
existing entities. Nothing here changes any entity's identity URI.

## 1. Vocabulary terms (TTL data)

### Propp function term — `propp.ttl`

- **Subject**: `<https://bookwright.dev/vocab/propp#function/{en-slug}>`
- **Type**: `crm:E55_Type`
- **Labels**: `rdfs:label "<EN>"@en, "<ES>"@es` (term #8 carries four — see
  research D9).
- **Cardinality**: 31 terms.

### Greimas actant term — `greimas.ttl`

- **Subject**: `<https://bookwright.dev/vocab/greimas#actant/{en-slug}>`
- **Type**: `crm:E55_Type`
- **Labels**: `rdfs:label "<EN>"@en, "<ES>"@es`.
- **Cardinality**: 6 terms (subject, object, sender, receiver, helper, opponent).

Both files keep their `@prefix` declarations and gain a header comment matching
`sources.ttl`'s ("these terms are Bookwright's, not part of the frozen GOLEM
ontology; outside the `CLASS_IRI` 17-class closure"). The stub `owl:Class` lines
are removed (research D3).

**Invariant (FR-011)**: within one vocabulary, the set of `make_slug(label)`
values is injective (each slug → at most one term). Enforced at load time.

## 2. `VocabularyIndex` (new, `io/vocabularies.py`)

A transient build-time value object — never serialized.

| Member | Type | Meaning |
|---|---|---|
| `_by_slug` | `dict[str, URIRef]` | `make_slug(label) → term URI`, built from every term's `rdfs:label`s. |
| `resolve(name)` | `(str) -> URIRef \| None` | `make_slug(name)` then dict lookup; `None` on no-match or `EmptySlugError`. |

Module functions:

- `load_vocabulary(name: str) -> VocabularyIndex` — `importlib.resources` reads
  `bookwright.resources.vocabularies/{name}.ttl`, rdflib parses it, the index is
  built from `?t a crm:E55_Type ; rdfs:label ?l`. Raises `VocabularyDataError`
  (a `BookwrightError` subclass, or reuse an existing IO error) if two terms
  collide on a slug (FR-011). `@lru_cache`d by `name` (resources are static).
- `KNOWN_VOCABULARIES: frozenset[str] = {"propp", "greimas"}`.
- `load_active_vocabularies(active: list[str]) -> ActiveVocabularies` — loads each
  `name in active` that is in `KNOWN_VOCABULARIES`; ignores the rest (D7).

`ActiveVocabularies` is a tiny frozen record exposing `propp: VocabularyIndex |
None` and `greimas: VocabularyIndex | None` (only the active ones populated), so
the pipeline passes `vocabs.propp` to `map_outline` and `vocabs.greimas` to
`map_bible`.

## 3. Entity field additions

### `NarrativeFunction` (G10, `golem/modules/narrative.py`)

| Field | Type | Default | Notes |
|---|---|---|---|
| `type_uri` | `URIRef \| None` | `None` | The matched Propp term, or `None` (untyped, unchanged behavior). |

- `to_triples()` override: `yield from super().to_triples()` (the `rdf:type`),
  then if `type_uri`: `(uri, HAS_TYPE, type_uri)` and `(type_uri, RDF.type,
  CLASS_IRI["Type"])`.
- `derived_assertions()` override: `yield DerivedAssertion(self.uri, self.uri,
  None)`; if `type_uri`: `yield DerivedAssertion(self.uri, type_uri,
  "functions")`.

### `CharacterRole` (G11, `golem/modules/feature.py`)

| Field | Type | Default | Notes |
|---|---|---|---|
| `type_uri` | `URIRef \| None` | `None` | The matched Greimas term, or `None`. |

- `to_triples()`: keep `rdf:type` + `rdfs:label`; if `type_uri`: add `(uri,
  HAS_TYPE, type_uri)` and `(type_uri, RDF.type, CLASS_IRI["Type"])`.
- No `derived_assertions` on `CharacterRole` itself — it is an owned sub-node; its
  type E13 is emitted by its owner (below).

### `Character` (G1, `golem/modules/character.py`)

| Field | Type | Default | Notes |
|---|---|---|---|
| `role_types` | `dict[str, URIRef]` | `Field(default_factory=dict)` | role-slug → Greimas term; construction input only, emits no triples. |

- `model_post_init`: build each `CharacterRole` with
  `type_uri=self.role_types.get(make_slug(text))`.
- `derived_assertions()`: unchanged identity + feature + role assertions, **plus**
  for each role with `role.type_uri`: `yield DerivedAssertion(role.uri,
  role.type_uri, "narrative_roles")`.

## 4. Provenance (reuse, no new model)

`build_provenance` (`io/bible.py`) is unchanged: it iterates each mapped entity's
`derived_assertions()` and mints one `AttributeAssignment`
(`crm:E13_Attribute_Assignment`) per assertion. The new type assertions ride this
path:

- G10 type → E13 with `target = function`, `attribute = term`, `source =
  <unit-card path>` (file-level; minted functions carry `key_lines={}`).
- G11 type → E13 with `target = role node`, `attribute = term`, `source =
  <character-card path>:<narrative_roles line>`.

## 5. IO wiring (resolution sites)

| Pass | File | Resolution |
|---|---|---|
| Functions (Propp) | `io/outline.py::_mint_functions` | `type_uri = propp.resolve(raw)` when `propp` is not `None`; pass into `NarrativeFunction(...)`. Dedup-by-slug is unchanged — the first card to introduce a slug fixes the (already deterministic) `type_uri`. |
| Roles (Greimas) | `io/_bible_builders.py::_build_character` | `role_types = {make_slug(label): uri for label in roles if greimas and (uri := greimas.resolve(label))}`; pass into `Character(...)`. |

`map_bible` / `map_outline` gain keyword-only `greimas` / `propp` params (default
`None`), threaded from `build_project_graph` (`commands/_graph.py`) via
`load_active_vocabularies(manifest.vocabularies.active)`.

## 6. State / determinism

No state machine. Determinism (SC-004) holds because: `make_slug` is pure; the
index is injective (FR-011); resolution is a pure dict lookup; and the existing
slug-deduplication of functions and URI-deduplication of role nodes is unchanged.
Same source + same active vocabularies ⇒ identical `type_uri`s ⇒ identical
triples and identical E13 reifications every build. With no vocabulary active, all
`type_uri`s are `None` and `role_types` is empty ⇒ byte-for-byte the
iteration-028/029 graph (FR-008/SC-003).
