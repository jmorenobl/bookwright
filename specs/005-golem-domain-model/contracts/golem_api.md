# Contract: `bookwright.golem` public Python API

This iteration ships an **internal library**, not a CLI command. Its consumers
are iteration 6 (graph indexer) and iteration 10 (validators). This document is
the stable contract those iterations may rely on. Breaking it requires a spec
revision.

## Importable surface (`bookwright.golem`)

```python
from bookwright.golem import (
    # Character module
    Character, Object,
    # Relationship module
    SocialRelationship, RelationshipRole,
    # Event module
    NarrativeEvent, PsychologicalState,
    # Setting module
    Setting, NarrativeLocation,
    # Narrative module
    NarrativeUnit, NarrativeFunction, NarrativeRole, NarrativeSequence,
    # Inference module
    AttributeAssignment,
    # Feature module (+US5 — attribute-support entities, not narrative concepts)
    CharacterFeature, Dimension,
    # helpers
    to_turtle,
    # errors
    GolemError, EmptySlugError,
)
```

A `CONCEPTS` registry (mapping concept name → class) is also exported for
downstream introspection. **`CharacterFeature` / `Dimension` are intentionally
excluded from `CONCEPTS`** — they are character-scoped attribute carriers, not
one of the thirteen narrative concepts (SC-001). They are exported only so
iteration-10 validators can introspect the attribute subgraph; iteration 6
constructs them indirectly by passing `born`/`died`/`features`/`narrative_roles`
to `Character`.

## Construction contract

Every named concept:

```python
e = Character(uri_base="https://example.org/my-book/", name="Aparici")
```

- `uri_base` — absolute http/https URI ending in `/` (not re-validated here).
- `name` — non-empty after slugging; a name that slugs to empty raises
  `EmptySlugError`.
- Instances are **frozen**: assigning to any field after construction raises
  `pydantic.ValidationError`.

**`Character` optional attributes (+US5)** — all default to empty/`None`, so
existing identity-only construction is unchanged:

```python
c = Character(
    uri_base="https://example.org/my-book/",
    name="Aparici",
    born=1828,                              # int year | None
    died=1900,                              # int year | None
    features=("ingeniero químico",),        # tuple[str, ...]; deduped by slug
    narrative_roles=("protagonist",),       # tuple[str, ...]; deduped by slug
)
```

- `features` / `narrative_roles` items follow the slug rule; an item that slugs
  to empty raises `EmptySlugError` (FR-021). Free-text and biographical features
  live in disjoint URI subspaces (`/feature/{slug}` vs `/feature/bio/{kind}`), so
  a free-text feature never collides with `born`/`died` on the same character.
- Supplying none of the four → `c.to_triples()` yields only the `rdf:type`
  assertion (US5-6), byte-identical to the identity-only `Character` above.
- The generated feature / dimension / role nodes carry deterministic,
  character-scoped URIs (`{c.uri}/feature/{slug}`, `{c.uri}/feature/bio/{birth|death}`,
  `{feature}/dimension`, `{c.uri}/role/{slug}`) — never blank nodes (FR-021).

`AttributeAssignment` is the one exception — constructed without `name`:

```python
a = AttributeAssignment(
    uri_base="https://example.org/my-book/",
    target=some_entity,            # GolemEntity | rdflib.URIRef
    attribute=some_attr_entity,    # GolemEntity | rdflib.URIRef
    source="manuscript/cap-04.md:42",   # verbatim path string
    premise=None,                  # optional GolemEntity | URIRef
)
```

## Identity contract

- `e.uri -> rdflib.URIRef`, equal to `f"{uri_base}{segment}/{token}"`.
- Segment is fixed per concept (FR-004 table). Token is the ASCII slug for named
  concepts; a `uuid7()` string for `AttributeAssignment`.
- **Deterministic**: same `(class, uri_base, name)` → byte-identical `uri` across
  runs and processes (SC-002).
- **Immutable**: `uri` never changes for the lifetime of the object (FR-007).

Worked examples (from spec US1):

| Construction | `.uri` |
|---|---|
| `Character(B, "Aparici")` | `{B}character/aparici` |
| `NarrativeEvent(B, "La caída del puente")` | `{B}event/la-caida-del-puente` |
| `NarrativeLocation(B, "El faro")` | `{B}location/el-faro` |

(`B = https://example.org/my-book/`)

## Serialization contract

- `e.to_triples() -> Iterable[tuple]` — yields `rdflib` triples, always including
  `(e.uri, RDF.type, <its GOLEM class>)`, plus cross-reference triples linking to
  referenced entities by their `.uri` (FR-015).
- `to_turtle(entities) -> str` — Turtle document using the registered short
  prefixes (`golem`, `crm`, `dlp` (DOLCE-Lite), **+US5 `edns`** (DOLCE
  ExtendedDnS, distinct from `dlp`), `rdf`, `rdfs`, `xsd`) (FR-010/FR-018).
- **Term closure**: every class/predicate emitted is defined in the frozen GOLEM
  ontology (FR-008, SC-003).
- **Well-formed**: `to_turtle(...)` output parses back through
  `rdflib.Graph().parse(...)` with no malformed triples and round-trips
  isomorphically (FR-012, SC-004).

## Error contract

- `GolemError` — base for all errors this package raises.
- `EmptySlugError(GolemError)` — raised at construction when the canonical name
  slugs to empty. Exposes `.to_json()` returning
  `{"error": "golem_empty_slug", "name": <str>, "message": <str>}`, matching the
  `core/errors.py` JSON shape so downstream `--json` commands stay compliant
  (Principle IX).

## Frozen-ontology contract (FR-011)

- The package bundles `bookwright/resources/schemas/golem-1.1/golem.ttl` and a
  `version.json` that names the upstream repository and the exact upstream commit
  the Turtle was frozen from (SC-005), plus `version_iri`/`version_info`.
- `bookwright version [--json]` reports the bundled schema label (read from the
  sibling `VERSION` file).

## Out of contract (this iteration)

- No reading of bible/manuscript, no semantic coherence validation (FR-014).
- No persistence/querying of the graph (later `graph` commands).
- No controlled-vocabulary content (Propp/Greimas/etc.).
