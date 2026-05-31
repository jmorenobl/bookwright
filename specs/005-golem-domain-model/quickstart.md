# Quickstart: GOLEM Domain Model

How a downstream component (indexer, validator) uses the model once this
iteration lands. Everything here runs in-process; nothing touches disk except
reading the bundled, frozen ontology.

## 1. Construct typed entities

```python
from bookwright.golem import Character, SocialRelationship, AttributeAssignment

B = "https://example.org/my-book/"   # manifest.toml > bookwright.uri_base

aparici = Character(uri_base=B, name="Aparici")
pena    = Character(uri_base=B, name="José Peña")

aparici.uri   # rdflib.URIRef('https://example.org/my-book/character/aparici')
pena.uri      # rdflib.URIRef('https://example.org/my-book/character/jose-pena')
```

Identifiers are deterministic and immutable — constructing `Character(B,
"Aparici")` again anywhere yields the same `.uri`, and the object is frozen.

## 2. Link entities and serialize to Turtle

```python
from bookwright.golem import to_turtle

rel = SocialRelationship(uri_base=B, name="Aparici y Peña",
                         participants=(aparici, pena))

ttl = to_turtle([aparici, pena, rel])
print(ttl)
# @prefix golem: <https://w3id.org/golem/ontology#> .
# @prefix crm:   <http://www.cidoc-crm.org/cidoc-crm/> .
# ...
# <.../character/aparici> a golem:G1_Character .
# <.../relationship/aparici-y-pena> a golem:G4_Social_Relationship ;
#     <dolce participant predicate> <.../character/aparici>, <.../character/jose-pena> .
```

## 2b. Carry character attributes (+US5: born/died/features/roles)

```python
c = Character(
    uri_base=B, name="Aparici",
    born=1828, died=1900,
    features=("ingeniero químico",),
    narrative_roles=("protagonist",),
)

ttl = to_turtle([c])
print(ttl)
# <.../character/aparici> a golem:G1_Character ;
#     golem:GP0_has_feature <.../character/aparici/feature/birth>,
#                        <.../character/aparici/feature/death>,
#                        <.../character/aparici/feature/ingeniero-quimico> ;
#     edns:plays <.../character/aparici/role/protagonist> .
# <.../character/aparici/feature/birth> a golem:G17_Character_Feature ;
#     crm:P2_has_type <.../type/birth> ;
#     crm:P43_has_dimension <.../character/aparici/feature/birth/dimension> .
# <.../character/aparici/feature/birth/dimension> a crm:E54_Dimension ;
#     crm:P90_has_value "1828"^^xsd:gYear .
# <.../character/aparici/feature/ingeniero-quimico> a golem:G17_Character_Feature ;
#     rdfs:label "ingeniero químico" .
# <.../character/aparici/role/protagonist> a golem:G11_Narrative_Role ;
#     rdfs:label "protagonist" .
```

Every node URI is deterministic and character-scoped (never a blank node), so
re-serializing the same `Character` is byte-identical. `edns:plays` is the DOLCE
**ExtendedDnS** property — distinct from the DOLCE-Lite `dlp:participant` used in
§2. A `Character` built with none of these attributes serializes to just its
`rdf:type` triple, exactly like §1.

## 3. Record provenance for an inferred attribute

```python
note = AttributeAssignment(
    uri_base=B,
    target=aparici,
    attribute=some_feature,                 # another GolemEntity or URIRef
    source="bible/characters/aparici.md",   # stored verbatim
    premise=None,                           # optional
)

note.uri   # https://example.org/my-book/assertion/<uuid7>
ttl = to_turtle([note])
```

Two assignments created in sequence carry distinct, creation-ordered ids.

## 4. Errors

```python
from bookwright.golem import EmptySlugError

try:
    Character(uri_base=B, name="!!!")       # slugs to empty
except EmptySlugError as e:
    print(e.to_json())   # {"error": "golem_empty_slug", "name": "!!!", "message": ...}
```

## 5. Inspect the bundled ontology

```bash
uv run bookwright version --json
# {"package_version": "...", "golem_schema_version": "golem-1.1"}
```

The frozen ontology and its provenance live at
`src/bookwright/resources/schemas/golem-1.1/{golem.ttl,version.json,VERSION}`.

## Validate the iteration

```bash
uv run pytest tests/golem/ -q
uv run pytest --cov=bookwright.golem --cov-report=term-missing   # expect ≥ 80%
uv run ruff check && uv run ruff format --check
uv run mypy --strict src tests
```

All four gates must be green before merge to `main` (Constitution VIII).
