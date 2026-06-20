# Phase 0 Research: Propp/Greimas vocabularies as `E55_Type`

All NEEDS-CLARIFICATION were resolved during `/speckit-clarify` (see spec
§ Clarifications) and confirmed against the codebase. This document records the
remaining *plan-level* decisions the spec deferred to `/speckit-plan`.

## D1 — Where does activation come from, and how is it threaded?

**Decision**: Read `manifest.vocabularies.active: list[str]`
(`core/_blocks.py::VocabulariesBlock`). The pipeline `build_project_graph(root,
manifest)` (`commands/_graph.py`) already holds the manifest; it loads the active
vocabularies once and passes the relevant index into the two mappers:

- the **Greimas** index → `map_bible(...)` → the character pass (roles, G11);
- the **Propp** index → `map_outline(...)` → `_mint_functions` (functions, G10).

**Rationale**: FR-003 forbids inventing an activation mechanism. The manifest
list is the sole machine-readable source (the constitution's "Vocabularios
activos" prose is the human mirror, not parsed — spec Assumptions). Threading via
keyword-only `*, propp=None` / `*, greimas=None` parameters keeps every existing
caller of `map_bible`/`map_outline` working unchanged (default `None` ⇒ no
typing ⇒ FR-008/SC-003).

**Alternatives rejected**: (a) parsing the constitution markdown — not
machine-readable, would invent a mechanism; (b) a global/singleton "active
vocabularies" — hidden state, untestable, violates the explicit-wiring style of
the existing pipeline.

## D2 — Is the term→name mapping the TTL, or a Python table?

**Decision**: the **TTL is the single source of truth**. `io/vocabularies.py`
parses the bundled `resources/vocabularies/{name}.ttl` with rdflib and builds the
`slug(label) → term-URI` index from each `crm:E55_Type` subject's `rdfs:label`
literals. Python hardcodes **no** term URI and **no** alias.

**Rationale**: Principle I (plain text is the source of truth). Contrast with
`sources.ttl`, where the controlled values are *duplicated* into Pydantic
`Literal`s and a unit test asserts they stay in sync — a deliberate smell there
because the values are an authoring-input enum validated at parse time. Here the
values are *match keys for an optional link*, never validated input, so there is
no reason to duplicate them: deriving the index from the TTL is strictly simpler
and removes a whole sync-drift debt class. It also makes the spec's "carga/parseo
de los TTL poblados" test the natural integrity check.

**Alternatives rejected**: a Python `dict[str, URIRef]` per vocabulary (the
`SOURCE_TYPE_IRI` shape) — would force the TTL and the table to be kept in sync
by hand, exactly the drift the deferral/zero-debt bar warns against.

## D3 — Term URI scheme

**Decision**: mirror `sources.ttl`'s `<…bw#source-type/primaria>` shape:

- Propp: `<https://bookwright.dev/vocab/propp#function/{slug}>` (prefix
  `propp:`), e.g. `propp:function/departure`.
- Greimas: `<https://bookwright.dev/vocab/greimas#actant/{slug}>` (prefix
  `greimas:`), e.g. `greimas:actant/subject`.

Each term: `a crm:E55_Type ; rdfs:label "<EN>"@en, "<ES>"@es .` The stub
`owl:Class` lines (`propp:Function` / `greimas:Actant`) are **removed** so the
files match the `sources.ttl` pattern exactly (E55_Type individuals only); the
prefixes are kept.

**Rationale**: the slug in the URI is the EN canonical match-name, giving a
stable, human-legible IRI; the `function/` / `actant/` segment namespaces the
terms within the vocabulary, identical to `source-type/` / `reliability/` in
`sources.ttl`. Because the loader reads *labels*, not the URI segment, the URI
slug choice is cosmetic — but keeping it = the EN match-name keeps the file
self-documenting.

## D4 — How the typing link is emitted and provenanced (FR-013)

**Decision**: give the typed entities an optional `type_uri: URIRef | None`
field. When set:

- **`to_triples`** emits `(entity, crm:P2_has_type, term)` **and** `(term,
  rdf:type, crm:E55_Type)` — exactly the two-triple shape `CharacterFeature`'s
  biographical variant and `Source` already use (`HAS_TYPE` = `crm:P2_has_type`,
  `CLASS_IRI["Type"]` = `crm:E55_Type`). No new predicate or class.
- **`derived_assertions`** yields an extra `DerivedAssertion(target=entity,
  attribute=term, source_field=<origin key>)`, so `build_provenance` mints a
  `crm:E13_Attribute_Assignment` for the typing link uniformly with every other
  GOLEM assertion. `source_field` is `"functions"` for G10 and
  `"narrative_roles"` for G11 — the same key that provenances the entity's
  identity.

**Provenance granularity**:
- **Functions (G10)** are top-level `MappedEntity`s (minted in `_mint_functions`,
  appended with `key_lines={}`), so `build_provenance(function_mapped)` already
  iterates `NarrativeFunction.derived_assertions()`. The type assertion rides
  there. Source resolves to the card's file path (no `:line`, since minted
  functions carry `key_lines={}` — the existing minted-function precedent).
- **Roles (G11)** are *owned sub-nodes* of `Character`; only the `Character` is a
  `MappedEntity`. So `Character.derived_assertions()` (which already overrides the
  base and loops `_role_nodes`) gains, per typed role, a
  `DerivedAssertion(target=role.uri, attribute=role.type_uri,
  "narrative_roles")`. `key_lines["narrative_roles"]` resolves to the character
  card's `narrative_roles:` line, so the role-type E13 carries a real
  `relpath:line` locator.

**Rationale**: FR-013 + the clarify answer require the link to flow through the
existing structural-provenance machinery, never as a special-cased bare triple.
This reuses `DerivedAssertion` / `build_provenance` / `AttributeAssignment`
verbatim. The `(term, rdf:type, E55_Type)` triple is intra-`to_triples` (like the
bio type and `Source`), so the term individual is self-declared in the emitted
graph without loading the whole vocab TTL into it.

**Alternatives rejected**: (a) a `CrossRef("type_uri", HAS_TYPE)` — the base
`to_triples` would emit the link but *not* the `(term, rdf:type, E55_Type)`
triple, and the base `derived_assertions` would label the source_field
`"type_uri"` instead of the originating front-matter key; cleaner to override the
two methods explicitly (the same call the bio variant makes). (b) Loading the
full vocab TTL into the graph — unnecessary; only the linked terms need to appear.

## D5 — How a `Character` builds *typed* role nodes without coupling `golem` to the manifest

**Decision**: `Character` gains an optional `role_types: dict[str, URIRef]`
field (default empty), keyed by **role slug** → term URI. In
`model_post_init`, each `CharacterRole` is built with
`type_uri=self.role_types.get(make_slug(label))`. The IO builder
`_build_character` computes `role_types` from the active Greimas index and passes
it in.

**Rationale**: `golem/` must do no IO and must not know about manifest
activation (`tests/golem/test_no_io.py`). Keeping the *matching* (TTL parse,
activation gating) in `io/` and handing `Character` a pre-resolved `slug → URI`
map keeps the domain model pure and symmetric with how `NarrativeFunction`
receives a pre-resolved `type_uri`. The map is construction input only — it emits
no triples itself, so the graph is unchanged when it is empty.

**Alternatives rejected**: passing a resolver callable or the `VocabularyIndex`
into `Character` (couples `golem` → `io`); retrofitting `type_uri` onto already
built role nodes (impossible — entities are frozen).

## D6 — Match key & ES/EN tolerance

**Decision**: normalize the authored name with the existing
`golem.slug.make_slug` (lowercase + ASCII transliteration via `python-slugify`),
and look it up in the vocab index. Case- and accent-tolerance fall out of
`make_slug` (FR-010); ES/EN tolerance comes from each term carrying **both** an
`@en` and an `@es` `rdfs:label`, each slugged into the index. An unsluggable name
(`EmptySlugError`) resolves to no term (untyped, silent).

**Disjointness (FR-011)**: the loader raises a clear error if two terms in one
vocabulary slug to the same alias — a vocabulary-data bug surfaced at load time,
**not** a runtime tie-break. A test asserts the populated TTLs load without
collision, so the guarantee is enforced, not assumed.

## D7 — Unknown active-vocabulary names (FR-003 edge case)

**Decision**: `load_active_vocabularies(active)` loads only names in a fixed
`KNOWN_VOCABULARIES = {"propp", "greimas"}` set; any other entry in `active` is
ignored silently (types nothing). No new failure mode.

**Rationale**: spec edge case — the project's existing active-vocabularies
declaration semantics own unknown names; this feature adds no diagnostic for them
(consistent with the silent-on-no-match decision, D8).

## D8 — Silent on no-match (decided in clarify)

No warning/diagnostic when a name matches no active term. Unmatched names are
normal authoring; discoverability is served by the US3 references. No new
reporting plumbing (scope discipline).

## D9 — Canonical term sets (fixed here so implementation is mechanical)

### Propp — 31 functions (`propp.ttl`)

`#` = the slug used in the URI (the EN canonical match-name). Each term carries
the EN and ES `rdfs:label` shown; both slug into the index. Villainy/Lack is the
single function #8 (Propp's A/a), carrying both pairs as labels so all four names
match it.

| # | EN label (`@en`) | ES label (`@es`) |
|---|---|---|
| 1 | absentation | alejamiento |
| 2 | interdiction | prohibición |
| 3 | violation | transgresión |
| 4 | reconnaissance | interrogatorio |
| 5 | delivery | información |
| 6 | trickery | engaño |
| 7 | complicity | complicidad |
| 8 | villainy | fechoría · (alt: lack / carencia) |
| 9 | mediation | mediación |
| 10 | counteraction | principio de la acción contraria |
| 11 | departure | partida |
| 12 | donor function | primera función del donante |
| 13 | hero reaction | reacción del héroe |
| 14 | acquisition | recepción del objeto mágico |
| 15 | guidance | desplazamiento |
| 16 | struggle | combate |
| 17 | branding | marca |
| 18 | victory | victoria |
| 19 | liquidation | reparación |
| 20 | return | regreso |
| 21 | pursuit | persecución |
| 22 | rescue | socorro |
| 23 | unrecognized arrival | llegada de incógnito |
| 24 | unfounded claims | pretensiones engañosas |
| 25 | difficult task | tarea difícil |
| 26 | solution | realización de la tarea |
| 27 | recognition | reconocimiento |
| 28 | exposure | desenmascaramiento |
| 29 | transfiguration | transfiguración |
| 30 | punishment | castigo |
| 31 | wedding | boda |

Term #8 carries four labels: `"villainy"@en, "lack"@en, "fechoría"@es,
"carencia"@es` — Propp's combined function-8 slot, so any of the four names types
to it. All other slugs are pairwise disjoint (verified by eye; **enforced** by
the loader's disjointness guard + test). *Note for `/speckit-tasks`/implement: if
any ES/EN pair accidentally collides under `make_slug`, the load-time guard
fails the test — fix the label, do not add tie-break logic (FR-011).*

### Greimas — 6 actants (`greimas.ttl`)

| URI slug | EN label (`@en`) | ES label (`@es`) |
|---|---|---|
| subject | subject | sujeto |
| object | object | objeto |
| sender | sender | destinador |
| receiver | receiver | destinatario |
| helper | helper | ayudante |
| opponent | opponent | oponente |

These are exactly the pairs the existing `references/greimas-actants.md` already
names (*Destinador (sender)*, *Destinatario (receiver)*, *Ayudante (helper)*,
*Oponente (opponent)*, *Sujeto*, *Objeto*), so the reference needs only a small
"canonical match-names" section, not a rewrite.

## D10 — Reference ↔ vocabulary agreement (SC-005, FR-012)

**Decision**: each reference gets a clearly delimited **"Canonical match-names"**
section listing one `- <EN> / <ES>` line per term. `propp-functions.md`'s current
condensed 6-movement digest is replaced by the 31-line list (its dramatis
personae prose is kept only as context, explicitly flagged "typed via Greimas,
not here" so it is not read as a Propp match-name). `greimas-actants.md` keeps its
prose and gains the 6-line section. A `tests/resources/` test parses those
sections and asserts set-equality with the slugs the loader derives from each
TTL — making SC-005 (no orphan on either side) machine-checked, both directions.

**Rationale**: SC-005 is bidirectional; a parseable delimited list is the only
way to assert "no term in the reference is absent from the vocabulary, and none in
the vocabulary is absent from the reference" without brittle prose-scraping.
