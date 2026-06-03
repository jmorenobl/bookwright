# Contract — emitted provenance triples

What `bookwright graph build` writes into `bible/graph.ttl` for research content.
All terms are CIDOC-CRM (already bound `crm:`) or Bookwright `bw:`
(`https://bookwright.dev/vocab/bw#`). **No new GOLEM/ontology class** (FR-001,
Constitution X): Findings/Anchors reuse `crm:E13_Attribute_Assignment`; Sources are
typed via `crm:E55_Type`; nothing is added to the frozen `CLASS_IRI` closure.

## Prefixes

```turtle
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix bw:  <https://bookwright.dev/vocab/bw#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
```

`bw` is bound by `bind_prefixes`; `@prefix bw:` appears in output only when a
research triple uses it (a research-free build is byte-stable, unchanged).

## URIs (design § 4.5)

| Entity | Pattern | Token |
|---|---|---|
| Source | `{uri_base}source/{slug}` | ASCII slug of `name` |
| Finding | `{uri_base}finding/{uuid7}` | UUIDv7 (time-ordered) |
| Anchor | `{uri_base}anchor/{uuid7}` | UUIDv7 |
| Anchor time-span | `{uri_base}anchor/{uuid7}/time-span` | derived sub-node |

## Source (no `rdf:type`; typed via E55)

```turtle
<…/source/registro-tip>
    crm:P2_has_type            bw:source-type/oficial ;   # E55_Type individual
    bw:reliability             bw:reliability/alta ;       # E55_Type individual
    bw:reliabilityJustification "Fuente oficial primaria…" ;
    bw:reference               "https://www.interior.gob.es/…" ;
    bw:author                  "Ministerio del Interior (España)" ;
    bw:originalLanguage        "es" ;
    bw:accessDate              "2026-05-30"^^xsd:date ;
    bw:originalQuote           "El detective privado requiere la TIP…" .
    # bw:translation present only when original language ≠ book language
```

`bw:source-type/oficial` and `bw:reliability/alta` are `a crm:E55_Type` in
`sources.ttl`. A source is found by `?s crm:P2_has_type ?t . ?t a crm:E55_Type`.

## Finding (E13 reification)

```turtle
<…/finding/0192e…>
    a   crm:E13_Attribute_Assignment ;
    bw:claim       "Un detective privado en España necesita la licencia TIP." ;
    bw:assertedBy  "agent" ;
    crm:P140_assigned_attribute_to <…/character/manuel-de-aparici> ;  # bears_on
    bw:supportedBy <…/source/registro-tip> .                          # one per source
```

Open finding (FR-008):

```turtle
<…/finding/0192f…>
    a       crm:E13_Attribute_Assignment ;
    bw:open true .
    # no bw:claim / bw:supportedBy / P140 required
```

## Anchor (E13 reification + optional time-span)

```turtle
<…/anchor/0193a…>
    a   crm:E13_Attribute_Assignment ;
    bw:promotes   <…/finding/0192e…> ;
    bw:constrains <…/character/manuel-de-aparici> ;
    crm:P4_has_time-span <…/anchor/0193a…/time-span> .

<…/anchor/0193a…/time-span>
    a crm:E52_Time-Span ;
    crm:P82a_begin_of_the_begin "1995"^^xsd:gYear ;
    crm:P82b_end_of_the_end     "2026"^^xsd:gYear .
```

An anchor with no `begin`/`end` emits **no** `crm:P4_has_time-span` and no
time-span node (FR-010). An anchor constraining the timeline emits
`bw:constrains <…/timeline-uri>` (FR-009 / US3 §4).

## Distinguishing E13 uses (FR-018 / SC-007)

| | inferred assertion | finding | anchor |
|---|---|---|---|
| URI segment | `assertion` | `finding` | `anchor` |
| diagnostic predicate | `crm:P141_assigned` + `crm:P16_used_specific_object` | `bw:claim` / `bw:open` | `bw:constrains` / `bw:promotes` |

`?f a crm:E13_Attribute_Assignment ; bw:claim ?c` ⇒ findings only.
`?a a crm:E13_Attribute_Assignment ; bw:constrains ?e` ⇒ anchors only.

## Worked SPARQL (SC-002, design § 20.5)

```sparql
# Every anchor constraining a character, with its claim and supporting sources
SELECT ?anchor ?claim ?source WHERE {
  ?anchor  a crm:E13_Attribute_Assignment ;
           bw:constrains <…/character/manuel-de-aparici> ;
           bw:promotes ?finding .
  ?finding bw:claim ?claim ;
           bw:supportedBy ?source .
}
```

## `bw:` property reference (declared in `sources.ttl`)

| Property | Domain → Range | Datatype/Object |
|---|---|---|
| `bw:reference` | Source | `xsd:string` |
| `bw:author` | Source | `xsd:string` |
| `bw:originalLanguage` | Source | `xsd:string` (ISO 639-1) |
| `bw:reliability` | Source → `crm:E55_Type` | object |
| `bw:reliabilityJustification` | Source | `xsd:string` |
| `bw:accessDate` | Source | `xsd:date` |
| `bw:originalQuote` | Source | `xsd:string` |
| `bw:translation` | Source | `xsd:string` |
| `bw:claim` | Finding | `xsd:string` |
| `bw:assertedBy` | Finding | `xsd:string` |
| `bw:supportedBy` | Finding → Source | object |
| `bw:open` | Finding | `xsd:boolean` |
| `bw:promotes` | Anchor → Finding | object |
| `bw:constrains` | Anchor → narrative entity / timeline | object |

Reused CRM predicates: `crm:P2_has_type`, `crm:P140_assigned_attribute_to`,
`crm:P4_has_time-span`, `crm:P82a_begin_of_the_begin`,
`crm:P82b_end_of_the_end`; reused CRM classes: `crm:E13_Attribute_Assignment`,
`crm:E55_Type`, `crm:E52_Time-Span`.
