# Phase 1 Data Model: GOLEM Domain Model

Source of truth for entities, fields, URI patterns, and triple shapes. All class
IRIs and predicates below are confirmed present in the frozen ontology
(`golem/golem_v1-1.ttl` @ `f666128a…`, vendored as `golem.ttl`); the
term-closure test (SC-003) is the backstop against any drift.

Namespaces (per research § D5): `golem: https://w3id.org/golem/ontology#`,
`crm: http://www.cidoc-crm.org/cidoc-crm/`, the DOLCE-Lite-Plus layer at
`http://www.ontologydesignpatterns.org/ont/dlp/` (bound as `dlp`), `rdf:`,
`rdfs:`, `xsd:`. The frozen TTL's native alias for the GOLEM namespace (`gc:` /
`:`) is **not** rebound; we always emit the single `golem:` prefix.

---

## Base: `GolemEntity` (abstract)

Frozen Pydantic v2 model; not instantiated directly.

| Field | Type | Notes |
|---|---|---|
| `uri_base` | `str` | Project namespace base; absolute http/https ending in `/` (guaranteed by iteration 2; not re-validated). |
| `name` | `str` | Caller-supplied canonical name (Attribute Assignment excepted — see below). |

Class-level constants supplied by each subclass:
- `golem_class: URIRef` — the rdf:type target (e.g. `GOLEM.G1_Character`).
- `path_segment: str` — the FR-004 segment (e.g. `"character"`).

Computed (once, at construction; immutable — FR-007):
- `slug: str` — `make_slug(name)`; raises `EmptySlugError` if empty (FR-006).
- `uri: URIRef` — `f"{uri_base}{path_segment}/{slug}"` (FR-003/004).

Behavior:
- `to_triples() -> Iterable[tuple]` — yields at minimum
  `(self.uri, RDF.type, self.golem_class)` (FR-008), then any subclass-specific
  predicates. Subclasses extend, not replace, the base type triple.

Validation rules:
- Reassigning any field after construction → `ValidationError` (frozen). This is
  how US1 scenario 5 (immutable identifier) is enforced.

---

## Concept classes (12 slugged) + 1 assertion

Each lives in its GOLEM-module file (design § 4.2 grouping).

### `modules/character.py`

| Class | GOLEM class | Segment | Extra fields | Linking triples |
|---|---|---|---|---|
| `Character` | `golem:G1_Character` | `character` | — (v0: identity only) | — |
| `Object` | `golem:G16_Object` | `object` | — | — |

### `modules/relationship.py`

| Class | GOLEM class | Segment | Extra fields | Linking triples (FR-015) |
|---|---|---|---|---|
| `SocialRelationship` | `golem:G4_Social_Relationship` | `relationship` | `participants: tuple[GolemEntity \| URIRef, ...]` | one triple per participant using a DOLCE participation predicate (e.g. `dlp:participant`), object = participant `.uri` |
| `RelationshipRole` | `golem:G6_Relationship_Role` | `relationship-role` | optional `relationship: GolemEntity \| URIRef` | link role → relationship via the ontology's relationship/role property |

### `modules/event.py`

| Class | GOLEM class | Segment | Extra fields | Linking triples |
|---|---|---|---|---|
| `NarrativeEvent` | `golem:G5_Narrative_Event` | `event` | optional `participants: tuple[…]` | `dlp:participant` → each participant `.uri` |
| `PsychologicalState` | `golem:G3_Psychological_State` | `psychological-state` | optional `bearer: GolemEntity \| URIRef` | link state → its character |

### `modules/setting.py`

| Class | GOLEM class | Segment | Extra fields | Linking triples |
|---|---|---|---|---|
| `Setting` | `golem:G12_Setting` | `setting` | — | — |
| `NarrativeLocation` | `golem:G13_Narrative_Location` | `location` | optional `setting: GolemEntity \| URIRef` | link location → setting |

### `modules/narrative.py`

| Class | GOLEM class | Segment | Extra fields | Linking triples |
|---|---|---|---|---|
| `NarrativeUnit` | `golem:G9_Narrative_Unit` | `narrative-unit` | optional `functions`, `roles` refs | link unit → function/role |
| `NarrativeFunction` | `golem:G10_Narrative_Function` | `narrative-function` | — | — |
| `NarrativeRole` | `golem:G11_Narrative_Role` | `narrative-role` | — | — |
| `NarrativeSequence` | `golem:G7_Narrative_Sequence` | `narrative-sequence` | `units: tuple[GolemEntity \| URIRef, ...]` (ordered) | one triple per unit using the ontology's sequence/part predicate (e.g. `dlp:proper-part`) |

> Cross-reference predicate selection: the confirmed object-property inventory in
> the frozen ontology includes `crm:P67_refers_to`, `crm:P16_used_specific_object`,
> `golem:GP1_is_character_in`, and the DOLCE (`dlp`) `participant` / `participant-in` /
> `involves` / `involved-in` / `proper-part(-of)` family. Each link above is bound
> to a specific one of these during implementation and verified by the
> term-closure test. The model never coins a new predicate.

### `modules/inference.py`

| Class | GOLEM class | Segment | Token |
|---|---|---|---|
| `AttributeAssignment` | `crm:E13_Attribute_Assignment` | `assertion` | `uuid_utils.uuid7()` (string) |

Fields (FR-009):

| Field | Type | Required | Triple |
|---|---|---|---|
| `target` | `GolemEntity \| URIRef` | yes | `(self.uri, crm:P140_assigned_attribute_to, target.uri)` |
| `attribute` | `GolemEntity \| URIRef` | yes | `(self.uri, crm:P141_assigned, attribute.uri)` |
| `source` | `str` (path, e.g. `manuscript/cap-04.md:42`) | yes | source path as `xsd:string` literal via the ontology's source/"used" property (exact IRI confirmed and recorded in T021 — never coined); stored & emitted **verbatim** (FR-009, US3-2) |
| `premise` | `GolemEntity \| URIRef \| None` | no | when present, link this assignment to its premise assignment via the ontology's premise property (exact IRI confirmed and recorded in T021); when `None`, omitted (US3-3) |

Construction: `AttributeAssignment` does **not** take `name`; it overrides token
generation to `uuid7()` and exposes the same `.uri` / `.to_triples()` surface.
The uuid is generated once at construction and frozen (FR-013); two assignments
created in sequence sort in creation order (US3-4).

---

## Supporting modules

### `golem/slug.py`
- `make_slug(name: str) -> str` — `python-slugify` default (lowercase, ASCII,
  single-hyphen, trimmed). Empty result → `raise EmptySlugError(name)`.

### `golem/namespaces.py`
- `GOLEM`, `CRM`, DOLCE-layer namespaces, `RDF`, `RDFS`, `XSD` as
  `rdflib.Namespace`.
- `bind_prefixes(graph: Graph) -> None` — binds all short prefixes (FR-010).
- Class-IRI access (per-class `golem_class` attribute or a `CLASS_IRI` map).
- `load_frozen_ontology() -> Graph` and `frozen_terms() -> set[URIRef]` — load
  the vendored `golem.ttl`; used by the term-closure test / optional
  `validate_terms()`.

### `golem/serialize.py`
- `to_turtle(entities: Iterable[GolemEntity]) -> str` — fresh `Graph`,
  `bind_prefixes`, add all `to_triples()`, `serialize(format="turtle")`.

### `golem/errors.py`
- `GolemError(Exception)` — base.
- `EmptySlugError(GolemError)` — canonical name slugified to empty; carries the
  offending name; `.to_json()` mirrors `core/errors.py` shape
  (`{"error": "golem_empty_slug", "name": …, "message": …}`).

---

## Frozen ontology resource (FR-011, US4)

`src/bookwright/resources/schemas/golem-1.1/`:
- `golem.ttl` — frozen Turtle (bytes from upstream `golem/golem_v1-1.ttl`).
- `version.json`:
  ```json
  {
    "repository": "https://github.com/GOLEM-lab/golem-ontology",
    "commit": "f666128a9a29f39c9f23c96ae1c48023cc8e7898",
    "file": "golem/golem_v1-1.ttl",
    "version_iri": "https://w3id.org/golem/ontology/v1.1",
    "version_info": "1.1",
    "retrieved": "2026-05-30"
  }
  ```
- `VERSION` — `golem-1.1` (selector label read by `bookwright version`).

---

## Determinism & immutability invariants (success criteria)

- **SC-002**: `Character(uri_base=B, name="Aparici").uri` is byte-identical across
  independent constructions/processes — slug + concatenation are pure.
- **FR-007**: every field is frozen; no setter mutates `.uri`.
- **SC-003**: every predicate/class emitted by any `to_triples()` ∈
  `frozen_terms()`.
- **SC-006**: every `AttributeAssignment` has a non-empty `source`; sequential
  uuid7 tokens are strictly increasing.
