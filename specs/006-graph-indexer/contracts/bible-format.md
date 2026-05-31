# Contract — Bible source format → GOLEM mapping

Defines what `graph build` reads and the exact triples each file produces. Type
is determined by **location** (R2 — matches `bookwright init` / design § 7).
Iteration 7 authors templates that conform to this contract.

All emitted classes/predicates are members of `frozen_terms()` (SC-001).
Prefixes: `golem:` = `https://w3id.org/golem/ontology#`, `crm:` =
CIDOC-CRM, `dlp:` = DOLCE ExtendedDnS, `rdfs:`/`xsd:` standard.

---

## `bible/characters/<slug>.md` → `golem:G1_Character`

```yaml
---
name: "Manuel de Aparici"      # required → identity (slug) + rdf:type
born: 1828                      # optional → biographical feature (birth year)
died: 1900                      # optional → biographical feature (death year)
features:                       # optional list → G17_Character_Feature + label
  - "ingeniero químico"
  - "miembro fundador de Destilerías Ayelo"
narrative_roles:                # optional list → G11_Narrative_Role via dlp:plays
  - protagonist
---
```

Triples (sketch, `<C>` = `…/character/manuel-de-aparici`):
```turtle
<C> a golem:G1_Character .
# narrative_roles
<C> dlp:plays <…/narrative-role/protagonist> .
<…/narrative-role/protagonist> a golem:G11_Narrative_Role .
# features (free text)
<C> golem:GP0_has_feature <F1> .
<F1> a golem:G17_Character_Feature ; rdfs:label "ingeniero químico" .
# born / died (biographical features with a typed dimension value)
<C> golem:GP0_has_feature <Fbirth> .
<Fbirth> a golem:G17_Character_Feature ;
         crm:P2_has_type <…/type/birth> ;
         crm:P43_has_dimension <Dbirth> .
<Dbirth> a crm:E54_Dimension ; crm:P90_has_value "1828"^^xsd:gYear .
<…/type/birth> a crm:E55_Type .
# provenance (one per assertion; see contracts in data-model §4)
```

- **Required**: `name` (non-empty; slug must be non-empty — reuses iter-5
  `EmptySlugError`). Missing/empty `name` → file skipped (`invalid_frontmatter`).
- `born`/`died` must be integer-like years → `xsd:gYear`. Non-integer → skip with
  reason.
- **Unknown keys** are ignored and recorded in `unknown_keys`.

## `bible/settings/<slug>.md` → `golem:G12_Setting`
```yaml
---
name: "Destilerías Ayelo"
---
```
v0: identity only (`<S> a golem:G12_Setting`).

## `bible/timeline.md` → many `golem:G5_Narrative_Event`
One file, one frontmatter block, a top-level `events:` list:
```yaml
---
events:
  - name: "Fundación de Destilerías Ayelo"
    participants: ["Manuel de Aparici"]   # resolved to character URIs
  - name: "Incendio de 1900"
---
```
Each item → `<E> a golem:G5_Narrative_Event` + `<E> dlp:participant <C>` per
participant (resolved by character slug; unresolved name → recorded, edge skipped).

## `bible/relationships.md` → many `golem:G4_Social_Relationship`
```yaml
---
relationships:
  - name: "Sociedad Aparici–Ayelo"
    participants: ["Manuel de Aparici", "..."]
---
```
Each item → `<R> a golem:G4_Social_Relationship` + `<R> dlp:participant <C>`.

---

## Resolution & collisions
- Participant references resolve by character slug within the same build.
- Two entities of the same concept whose `name` slugifies identically →
  `slug_collision` (fatal, FR-014).
- Empty recognised dirs/files → zero entities (valid; empty graph).
