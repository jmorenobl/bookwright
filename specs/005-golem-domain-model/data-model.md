# Phase 1 Data Model: GOLEM Domain Model

Source of truth for entities, fields, URI patterns, and triple shapes. All class
IRIs and predicates below are confirmed present in the frozen ontology
(`golem/golem_v1-1.ttl` @ `f666128a…`, vendored as `golem.ttl`); the
term-closure test (SC-003) is the backstop against any drift.

Namespaces (per research § D5): `golem: https://w3id.org/golem/ontology#`,
`crm: http://www.cidoc-crm.org/cidoc-crm/`, the DOLCE-Lite-Plus layer bound as
`dlp` (see below), `rdf:`, `rdfs:`, `xsd:`. The frozen TTL's native alias for
the GOLEM namespace (`gc:` / `:`) is **not** rebound; we always emit the single
`golem:` prefix.

**`dlp` resolved (T021)**: the cross-reference object properties we emit
(`participant`, `proper-part`, `generically-dependent-on`, `generic-location`)
all live in the frozen ontology under
`http://www.ontologydesignpatterns.org/ont/dlp/DOLCE-Lite.owl#`, so `dlp` is
bound to **that** IRI (not the bare `…/ont/dlp/`); only then does Turtle emit
`dlp:participant` rather than a full `<…>` IRI (US2-4).

**+US5 — `edns` (D14, FR-018)**: the character → narrative-role link uses
`plays`, which lives **only** in the DOLCE **ExtendedDnS** layer
(`http://www.ontologydesignpatterns.org/ont/dlp/ExtendedDnS.owl#`), a *different*
namespace from the DOLCE-Lite `dlp` that supplies `participant`. A new `EDNS`
namespace constant is bound to the short prefix `edns`, **distinct** from `dlp`,
so the Turtle emits `edns:plays` and the load-bearing distinction stays visible.
The remaining sibling DnS / spatial / temporal DOLCE files imported by the
ontology contribute no emitted terms in v0, so no further prefix is bound.

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
| `Character` | `golem:G1_Character` | `character` | **+US5** `born: int \| None = None`, `died: int \| None = None`, `features: tuple[str, ...] = ()`, `narrative_roles: tuple[str, ...] = ()` (all optional; none → identity only) | **+US5** `golem:GP0_has_feature` → each feature node (free-text + biographical); `edns:plays` → each role node (see `modules/feature.py`) |
| `Object` | `golem:G16_Object` | `object` | — | — |

**`Character` attribute build (US5, FR-016–021)**. The public fields mirror the
documented frontmatter keys exactly (FR-016); the model does **not** read
frontmatter (FR-014) — iteration 6 populates these from the bible. At
construction (`model_post_init`, after the identity URI is fixed) `Character`
builds, deterministically and once:

- one biographical `CharacterFeature` per non-`None` `born`/`died`;
- one free-text `CharacterFeature` per `features` item (deduped by slug);
- one character-scoped `G11_Narrative_Role` node per `narrative_roles` item
  (deduped by slug).

`cross_refs` declares the single-hop edges over the built node tuples
(`golem:GP0_has_feature` for the feature nodes — biographical **and** free-text —
and `edns:plays` for the role nodes); `Character.to_triples()` then chains
`super().to_triples()` (the `rdf:type` assertion + those edges) with every nested
node's own `to_triples()`. A `Character` built with none of the four attributes
has empty node tuples, so it emits only its identity assertion — identity-only
behaviour of US1/US2 is preserved byte-for-byte (US5-6).

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

> Cross-reference predicates resolved (T021). Each link below is bound to a
> single object property confirmed present in the frozen ontology and asserted
> ∈ `frozen_terms()` by `test_namespaces.py`. The model never coins a predicate.
>
> | Link | Predicate IRI |
> |---|---|
> | Social Relationship → participant | `dlp:participant` (`…/DOLCE-Lite.owl#participant`) |
> | Narrative Event → participant | `dlp:participant` |
> | Relationship Role → relationship | `crm:P67_refers_to` |
> | Psychological State → bearer | `dlp:generically-dependent-on` |
> | Narrative Location → setting | `dlp:generic-location` |
> | Narrative Unit → function / role | `crm:P67_refers_to` |
> | Narrative Sequence → unit (ordered) | `dlp:proper-part` |
>
> These IRIs live in `golem/namespaces.py` as the `PARTICIPANT`,
> `GENERICALLY_DEPENDENT_ON`, `GENERIC_LOCATION`, `PROPER_PART` and `REFERS_TO`
> constants. Because RDF is unordered, the *ordering* of a sequence's units is
> carried only by the caller's tuple order, not by the triples.

### `modules/feature.py` (+US5 — attribute-support entities)

These are **character-scoped** typed nodes (D13), not top-level concepts: they
are **not** in `CONCEPTS`/`CLASS_IRI`-as-concepts and take no `path_segment`
slug-token shape. Each computes a deterministic URI once at construction and owns
its `to_triples()`. They are exported from `bookwright.golem` (for iteration-10
validators) but excluded from the `CONCEPTS` registry (SC-001).

| Class | rdf:type | URI | Fields | Triples emitted |
|---|---|---|---|---|
| `CharacterFeature` (free-text) | `golem:G17_Character_Feature` | `{character.uri}/feature/{slug(label)}` | `character_uri: URIRef`, `label: str` | `(uri, rdf:type, G17)`, `(uri, rdfs:label, Literal(label))` |
| `CharacterFeature` (biographical) | `golem:G17_Character_Feature` | `{character.uri}/feature/bio/{birth\|death}` | `character_uri`, `uri_base`, `kind: "birth"\|"death"`, `year: int` | `(uri, rdf:type, G17)`, `(uri, crm:P2_has_type, {uri_base}type/{kind})`, `({uri_base}type/{kind}, rdf:type, crm:E55_Type)`, `(uri, crm:P43_has_dimension, dimension.uri)` + the `Dimension`'s own triples |
| `Dimension` | `crm:E54_Dimension` | `{feature.uri}/dimension` | `feature_uri: URIRef`, `year: int` | `(uri, rdf:type, E54)`, `(uri, crm:P90_has_value, Literal(str(year), datatype=xsd:gYear))` |
| character-scoped role | `golem:G11_Narrative_Role` | `{character.uri}/role/{slug(text)}` | `character_uri`, `label: str` | `(uri, rdf:type, G11)`, `(uri, rdfs:label, Literal(label))` |

Notes:
- **URI construction**: these subclass `GolemEntity` but build `self._uri`
  directly from the owner URI + fixed suffix in `model_post_init` (they do not
  use the `{base}{segment}/{slug}` triad, because `{feature}/dimension` has no
  token and `birth`/`death` are fixed tokens). `make_slug` is reused for the
  text-derived suffixes; an empty slug raises `EmptySlugError` (FR-021).
  Biographical features sit under a `bio/` sub-segment (`…/feature/bio/birth`);
  because a slug never contains `/`, a free-text feature can never collide with
  a biographical one on the same character, so no reserved-token guard is needed.
- **`xsd:gYear`**: the year is emitted as `Literal(str(year), datatype=XSD.gYear)`
  — never `xsd:integer` or a plain string (FR-019, spec edge case). This is what
  makes iteration-10's "born before 1850" temporal query answerable.
- **`E55_Type` individuals** `{base}type/birth` / `{base}type/death` are project
  -scoped and shared across all characters; they are individuals of the frozen
  `crm:E55_Type` class, not new vocabulary (FR-020). Duplicate type-assertion
  triples across characters collapse in the `to_turtle` graph.
- **Determinism & dedup** (FR-021): identity derives from the slugged text, so
  two identical feature/role values on the *same* character resolve to one node;
  the same value on two *different* characters yields two distinct,
  character-scoped nodes (no cross-character collapse). Re-serializing the same
  `Character` is byte-identical (SC-007 extends SC-002 to these nodes).

### `modules/inference.py`

| Class | GOLEM class | Segment | Token |
|---|---|---|---|
| `AttributeAssignment` | `crm:E13_Attribute_Assignment` | `assertion` | `uuid_utils.uuid7()` (string) |

Fields (FR-009):

| Field | Type | Required | Triple |
|---|---|---|---|
| `target` | `GolemEntity \| URIRef` | yes | `(self.uri, crm:P140_assigned_attribute_to, target.uri)` |
| `attribute` | `GolemEntity \| URIRef` | yes | `(self.uri, crm:P141_assigned, attribute.uri)` |
| `source` | `str` (path, e.g. `manuscript/cap-04.md:42`) | yes | source path as `xsd:string` literal via `crm:P16_used_specific_object` (confirmed T021 — the ontology's own comment names P16 as the "source … used in an inference (E13)" property); stored & emitted **verbatim** (FR-009, US3-2) |
| `premise` | `GolemEntity \| URIRef \| None` | no | when present, links this assignment to its premise assignment via `crm:P67_refers_to` (confirmed T021); when `None`, omitted (US3-3) |

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
- `GOLEM`, `CRM`, `DLP` (DOLCE-Lite), **+US5 `EDNS`** (DOLCE ExtendedDnS), `RDF`,
  `RDFS`, `XSD` as `rdflib.Namespace`.
- `bind_prefixes(graph: Graph) -> None` — binds all short prefixes including
  **+US5 `edns`**, distinct from `dlp` (FR-010/FR-018).
- Class-IRI access (per-class `golem_class` attribute or a `CLASS_IRI` map);
  **+US5** `CLASS_IRI` gains `CharacterFeature → golem:G17_Character_Feature`,
  `Dimension → crm:E54_Dimension`, `Type → crm:E55_Type`.
- **+US5 predicate/term constants**: `HAS_FEATURE` (`golem:GP0_has_feature`),
  `PLAYS` (`edns:plays`), `HAS_TYPE` (`crm:P2_has_type`), `HAS_DIMENSION`
  (`crm:P43_has_dimension`), `HAS_VALUE` (`crm:P90_has_value`); `rdfs:label` is
  reused from `rdflib.RDFS`. All asserted ∈ `frozen_terms()` by `test_namespaces.py`.
- `load_frozen_ontology() -> Graph` and `frozen_terms() -> set[URIRef]` — load
  the vendored `golem.ttl`; used by the term-closure test / optional
  `validate_terms()`.

### `golem/serialize.py`
- `to_turtle(entities: Iterable[GolemEntity]) -> str` — fresh `Graph`,
  `bind_prefixes`, add all `to_triples()`, `serialize(format="turtle")`.

### `golem/errors.py`
- `GolemError(BookwrightError)` — abstract base (no `code`, no `to_json`).
- `EmptySlugError(GolemError)` — canonical name slugified to empty; carries the
  offending name; serializes through the **unified error envelope** owned by
  `BookwrightError.to_json()` (iteration 018) as
  `{"status": "error", "code": "golem_empty_slug", "message": …, "details": {"name": …}}`.
  Authoritative schema:
  [`specs/018-unified-error-envelope/contracts/error-envelope.md`](../../018-unified-error-envelope/contracts/error-envelope.md).

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
- **SC-007** (+US5): an attributed `Character` reaches every attribute through the
  frozen chain (feature via `golem:GP0_has_feature`/`rdfs:label`; role via
  `edns:plays`/`rdfs:label`; year via `crm:P2_has_type` +
  `crm:P43_has_dimension → crm:E54_Dimension → crm:P90_has_value` `xsd:gYear`),
  zero emitted terms fall outside `frozen_terms()`, every generated node is a
  deterministic character-scoped URI (no blank node) so re-serialization is
  byte-identical, and a `Character` with no attributes emits only its identity
  assertion.
