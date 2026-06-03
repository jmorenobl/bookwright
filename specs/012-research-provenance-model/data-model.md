# Phase 1 — Data Model

Provenance Model — Source / Finding / Anchor (iteration 012).

Two layers: (1) the **plain-text research files** the author maintains, and (2) the
**frozen Pydantic entities** the reader builds and serializes to RDF. The graph is
derived from the files, never the reverse (FR-017).

---

## 1. Domain entities (`src/bookwright/golem/modules/provenance.py`)

All three are immutable Pydantic v2 models subclassing `GolemEntity`
(`golem/base.py`): `frozen=True`, `extra="forbid"`, `strict=True`. Identity URI is
computed once in `model_post_init` as `{uri_base}{path_segment}/{token}` (FR-011,
design § 4.5).

### 1.1 `Source` (extends `SluggedEntity`)

| Field | Type | Req. | RDF emission |
|---|---|---|---|
| `uri_base` | `str` | ✓ | — (identity) |
| `name` | `str` | ✓ | slug → URI token; **no** `rdfs:label` triple in v0 |
| `reference` | `str` | ✓ | `bw:reference` (`xsd:string`) |
| `author` | `str` | ✓ | `bw:author` (`xsd:string`) |
| `original_language` | `str` (ISO 639-1) | ✓ | `bw:originalLanguage` (`xsd:string`) |
| `type` | `Literal["primaria","secundaria","oficial","académica","periodística","testimonial"]` | ✓ | `crm:P2_has_type` → `SOURCE_TYPE_IRI[type]` (an `E55_Type`) |
| `reliability` | `Literal["alta","media","baja"]` | ✓ | `bw:reliability` → `RELIABILITY_IRI[reliability]` (an `E55_Type`) |
| `reliability_justification` | `str` | ✓ | `bw:reliabilityJustification` (`xsd:string`) |
| `access_date` | `datetime.date` | ✓ | `bw:accessDate` (`xsd:date`) |
| `original_quote` | `str` | ✓ | `bw:originalQuote` (`xsd:string`) |
| `translation` | `str \| None` | – | `bw:translation` (`xsd:string`) — emitted only when set (the reader sets it iff `original_language != book_language`; see § 3) |

- **`path_segment`** = `"source"`; **token** = ASCII slug of `name`
  (`golem.slug.make_slug`).
- **`golem_class`** ClassVar = `CRM["E55_Type"]` — a documented placeholder; `Source`
  overrides `to_triples()` and emits **no `rdf:type`** (D2). Identity in the graph
  is `?s crm:P2_has_type ?t . ?t a crm:E55_Type`.
- **Validation**: `Literal` fields reject out-of-vocabulary `type`/`reliability`
  (FR-003/004/016). Empty `reliability_justification` is rejected (FR-004).

### 1.2 `Finding` (extends `GolemEntity`)

| Field | Type | Req. | RDF emission |
|---|---|---|---|
| `uri_base` | `str` | ✓ | — |
| `claim` | `str \| None` | – | `bw:claim` (`xsd:string`) — omitted when `None` |
| `asserted_by` | `str` | default `"author"` | `bw:assertedBy` (`xsd:string`) |
| `bears_on` | `URIRef \| None` | – | `crm:P140_assigned_attribute_to` — omitted when `None` |
| `sources` | `tuple[URIRef, ...]` | default `()` | `bw:supportedBy` — one triple per source |
| `open` | `bool` | default `False` | `bw:open` (`xsd:boolean`) — emitted **only** when `True` |

- **`path_segment`** = `"finding"`; **token** = `uuid_utils.uuid7()` minted once
  (design § 4.5, FR-011). **`golem_class`** = `CLASS_IRI["AttributeAssignment"]`
  → emits `rdf:type crm:E13_Attribute_Assignment` (FR-006).
- **Open-state invariant** (FR-008): when `open is True`, `claim`/`bears_on`/
  `sources` may all be empty and the entity is still valid; only `rdf:type` +
  `bw:open true` (+ optional `bw:assertedBy`) are emitted.
- **Non-open invariant** (enforced in the reader, not the model — see § 3): a
  non-open finding MUST have a `claim` and ≥ 1 source (FR-007), else `ResearchError`.

### 1.3 `Anchor` (extends `GolemEntity`)

| Field | Type | Req. | RDF emission |
|---|---|---|---|
| `uri_base` | `str` | ✓ | — |
| `promotes` | `URIRef` | ✓ | `bw:promotes` → the Finding URI |
| `constrains` | `URIRef` | ✓ | `bw:constrains` → narrative entity URI (or the untyped `{uri_base}timeline` IRI, D10) |
| `begin` | `int \| None` | – | time-span sub-node `crm:P82a_begin_of_the_begin` (`xsd:gYear`) |
| `end` | `int \| None` | – | time-span sub-node `crm:P82b_end_of_the_end` (`xsd:gYear`) |

- **`path_segment`** = `"anchor"`; **token** = `uuid_utils.uuid7()`.
  **`golem_class`** = `CLASS_IRI["AttributeAssignment"]` → emits
  `rdf:type crm:E13_Attribute_Assignment` (FR-009).
- **Time-span** (FR-010): when `begin` or `end` is set, emit
  `<anchor> crm:P4_has_time-span <anchor-uri/time-span>` and the sub-node
  `rdf:type crm:E52_Time-Span` + the P82a/P82b year literals. When both are `None`,
  emit nothing (no `P4_has_time-span`). A single-year `date` shorthand in the file
  sets `begin == end`.
- **`constrains` kinds** (FR-009): the reader resolves the named target to a
  `G1_Character` / `G12_Setting` / `G5_Narrative_Event` URI via the bible
  `entity_index` (D11), or to the well-known **untyped** timeline IRI
  `{uri_base}timeline` for `constrains: timeline` (research D10 — no new GOLEM class).
  This iteration emits the link as declared; *verifying* the target exists and is
  an allowed kind is the `factual_anchor` validator's job (iter 15) — see edge cases.

---

## 2. Controlled vocabulary (`src/bookwright/resources/vocabularies/sources.ttl`)

Declares, in Turtle, exactly what code references (FR-005). Canonical human-readable
artifact; enforcement is the Pydantic `Literal`s (D4).

- Prefix `bw: <https://bookwright.dev/vocab/bw#>`, `crm:`, `rdfs:`, `xsd:`.
- **Six source-type individuals** — `bw:source-type/primaria`,
  `…/secundaria`, `…/oficial`, `…/academica`, `…/periodistica`, `…/testimonial`,
  each `a crm:E55_Type ; rdfs:label "<accented Spanish word>"@es`.
- **Three reliability individuals** — `bw:reliability/alta`, `…/media`, `…/baja`,
  each `a crm:E55_Type ; rdfs:label …@es`.
- **`bw:` property declarations** — each property `a rdf:Property` with `rdfs:label`
  and a one-line `rdfs:comment` (the table in `contracts/provenance-graph.md`).
- **Provenance note** at the top: these `bw:` terms are Bookwright's own; they are
  **not** part of the frozen GOLEM `golem.ttl` and are intentionally outside the
  `CLASS_IRI` closure (Constitution X).

`sources` is *not* auto-merged into `graph.ttl` by this iteration; it is the
declaration the emitted triples conform to. (Adding `sources` to
`[vocabularies].active` and copying it at scaffold time is iteration 14.)

---

## 3. Plain-text research files (`bible/research/`) — parsed by `io/research.py`

Front-matter is YAML; prose Markdown below is ignored by the parser (FR-012,
design § 20.7). Provenance locators (`file:line`) are **not** required for research
entities in v0 (findings/anchors are themselves the provenance reification).

### 3.1 `sources.md`

```yaml
---
sources:
  - name: Registro TIP                 # slug → …/source/registro-tip
    reference: https://www.interior.gob.es/...
    author: Ministerio del Interior (España)
    original_language: es
    type: oficial
    reliability: alta
    reliability_justification: Fuente oficial primaria del organismo regulador.
    access_date: 2026-05-30
    original_quote: "El detective privado requiere la TIP expedida por..."
    # translation: omitted — source language (es) == book language (es)
---
Prose notes about the source registry…
```

### 3.2 `<topic>.md` (e.g. `detective-licencia.md`)

```yaml
---
findings:
  - id: tip-required
    claim: Un detective privado en España necesita la licencia TIP.
    asserted_by: agent
    bears_on: Manuel de Aparici        # resolved against the bible entity_index (D11)
    sources: [Registro TIP]            # references the Source by name
  - id: open-q-archivo
    open: true                         # an unresolved question — no claim/source needed
anchors:
  - promotes: tip-required             # the in-file finding id
    constrains: Manuel de Aparici      # a character (or 'timeline')
    begin: 1995                        # optional time-span
    end: 2026
---
Readable prose about the topic…
```

### 3.3 `_index.md`

```yaml
---
open_questions:                        # optional → each emits an open Finding
  - id: q-fronteras-1943
    claim: ¿Cómo denominaba la Wehrmacht la zona X en 1943?
---
Topic map and global open-questions prose…
```

### 3.4 Reader behaviour (`map_research`)

1. **Empty/absent** `bible/research/` → return an empty result; build proceeds,
   zero triples (FR-015, SC-005).
2. Parse `sources.md` first → build a `name-slug → Source` index (sources are
   needed to resolve `findings[].sources`).
3. Parse each `<topic>.md` and `_index.md` `open_questions` → `Finding`s, then
   `anchors` → `Anchor`s, resolving:
   - `findings[].sources` → source URIs via the source index.
   - `findings[].bears_on` / `anchors[].constrains` → narrative-entity URIs via the
     **bible** `entity_index` (`make_slug(name) → URI` covering characters, settings
     and events; passed in from the bible pass — research D11), or the well-known
     `{uri_base}timeline` IRI for the literal `timeline` (D10).
   - `anchors[].promotes` → the in-file finding `id` → that Finding's URI.
4. **Translation rule** (D6): set `Source.translation` only when
   `original_language != book_language`; require it (else `ResearchError`) when they
   differ; drop a supplied translation when they match (SC-004).
5. **Hard errors** (`ResearchError`, build aborts, no graph — D7): out-of-vocabulary
   `type`/`reliability`; missing required Source facet; non-open finding missing
   `claim` or `sources`; `anchors[].promotes` referencing an unknown finding id;
   translation-rule violation. Each error names the offending file and value
   (FR-016).
6. **Soft miss** (D12, build continues, exit code unchanged): a `bears_on` /
   `constrains` target name absent from the bible `entity_index` (and not the literal
   `timeline`) → the link triple is **omitted** and recorded as a `ResearchWarning`
   (`relpath` + field + name) surfaced in the build report. Existence/kind enforcement
   is `factual_anchor`'s job (iter-15).

---

## 4. Reader result types (`io/research.py`)

Mirrors `io/bible.py`'s `MapResult`/`MappedEntity` shape:

```python
@dataclass(frozen=True)
class ResearchResult:
    sources: tuple[Source, ...]
    findings: tuple[Finding, ...]
    anchors: tuple[Anchor, ...]
    files_processed: int
    warnings: tuple[ResearchWarning, ...]   # D12 — unresolved bears_on/constrains targets (soft)

    @property
    def entities(self) -> tuple[GolemEntity, ...]: ...   # sources + findings + anchors
```

The build feeds `result.entities` through `engine.add_triple(*t)` for `t in
entity.to_triples()`. No `build_provenance` pass over research entities (they are
already E13 reifications — D8).

---

## 5. Namespace additions (`src/bookwright/golem/namespaces.py`)

- `BW = Namespace("https://bookwright.dev/vocab/bw#")`; add `("bw", BW)` to
  `_PREFIXES` so `bind_prefixes` binds it deterministically.
- `bw:` property URIRef constants (`BW_REFERENCE`, `BW_RELIABILITY`,
  `BW_CLAIM`, `BW_CONSTRAINS`, `BW_PROMOTES`, `BW_SUPPORTED_BY`, `BW_OPEN`, …).
- `SOURCE_TYPE_IRI: dict[str, URIRef]` and `RELIABILITY_IRI: dict[str, URIRef]`
  (value → E55 individual IRI).
- Reused CRM constants: `HAS_TYPE` (`P2_has_type`, already present),
  `ASSIGNED_ATTRIBUTE_TO` (`P140`, already present), and new
  `HAS_TIME_SPAN` (`crm:P4_has_time-span`), `E52_TIME_SPAN` (`crm:E52_Time-Span`),
  `BEGIN_OF_BEGIN` (`crm:P82a_begin_of_the_begin`), `END_OF_END`
  (`crm:P82b_end_of_the_end`). **None** added to `CLASS_IRI` or the closure lists.
