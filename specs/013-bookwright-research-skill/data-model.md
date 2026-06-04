# Phase 1 Data Model: `bookwright-research` Skill + `bible/research/`

This iteration introduces **one** new typed model (`ResearchBlock`) and **emits**
(does not define) the iteration-13 provenance entities. The provenance format is
restated here only as the *output contract* the skill and templates must hit; its
authoritative source is `src/bookwright/io/research.py` +
`src/bookwright/golem/modules/provenance.py` (already on `main`).

---

## 1. `ResearchBlock` — the `[research]` manifest block (NEW)

**Home**: `src/bookwright/core/_research_block.py` (extracted to keep
`manifest.py` under the 500-line ceiling). Re-exported from `bookwright.core`.

**Wiring**: `Manifest.research: ResearchBlock = Field(default_factory=ResearchBlock)`.

### Fields

| Field | Type | Default | Validation | FR |
|---|---|---|---|---|
| `enabled` | `bool` | `True` | strict bool | FR-011, FR-012 |
| `source_languages` | `list[str]` | `[]` (empty) | each entry ∈ `ISO_639_1_CODES`; error names `source_languages[i]` | FR-011, FR-016 |
| `min_reliability_for_anchor` | `Literal["alta","media","baja"]` | `"media"` | Literal membership; bad value raises naming `min_reliability_for_anchor` | FR-011, FR-013, FR-015 |

### Model config

- `ConfigDict(extra="forbid", strict=True)` — identical to every sibling block
  (`BookwrightBlock`, `BookBlock`, …). An unknown key inside `[research]` is a
  validation error.

### Validators

- `min_reliability_for_anchor`: the `Literal` does the work. A unit test asserts
  `set(get_args(...))` equals `set(RELIABILITY_IRI)` from `golem.namespaces` to
  catch vocabulary drift **without** importing `golem` into `core` (the test
  imports both; production code does not — preserves layering).
- `source_languages`: `@field_validator("source_languages", mode="after")`
  rejecting any non-ISO-639-1 entry, mirroring `BookBlock._check_language`, with
  a `PydanticCustomError` carrying `{"index": i, "value": entry}`.

### Default-vs-present behavior (FR-012 / FR-014a)

- **Absent block** → `default_factory` builds `ResearchBlock()` with the three
  defaults above. `Manifest.load()` succeeds; `manifest.research.enabled is
  True`, etc.
- **Present block** (the scaffolded case) → parsed and validated; comments
  round-trip through tomlkit.
- **`enabled = false`** → the model exposes it; the *skill* reads it and reports
  the system inert (US2-1, edge case). No CLI behavior changes — `graph build`
  still maps whatever files exist (the gate is the protocol's, not the reader's).

### Reliability ordering (FR-015, protocol-side)

`min_reliability_for_anchor` is a **floor** the skill applies when deciding
anchor promotion. Ordering, high→low: `alta` > `media` > `baja`. A finding whose
best supporting source's `reliability` is below the floor stays a finding (never
an anchor). This comparison is performed *by the agent following the skill*, not
by Python in this iteration (the enforcing validator is iteration 15). The block
merely **supplies** the threshold.

---

## 2. Research file format (EMITTED — defined by iteration 13)

The skill and the `resources/templates/bible/research/` templates MUST produce
front-matter that `map_research()` parses without raising. Full field-by-field
contract: [contracts/research-file-format.md](contracts/research-file-format.md).
Summary of the three file shapes:

### 2a. `bible/research/sources.md` → `Source[]`

```yaml
---
sources:
  - name: "Kriegstagebuch des OKW, Bd. III"     # unique within sources.md
    reference: "BA-MA RH 2/..., ff. 12–18"
    author: "Oberkommando der Wehrmacht"
    original_language: "de"
    type: "primaria"        # primaria|secundaria|oficial|académica|periodística|testimonial
    reliability: "alta"     # alta|media|baja
    reliability_justification: "Registro oficial contemporáneo."
    access_date: 2026-06-04 # ISO date (xsd:date)
    original_quote: "Die Nachschublage an der Ostfront ..."
    translation: "La situación de abastecimiento en el frente oriental ..."
    # translation REQUIRED iff original_language != book.language; DROPPED if equal
---
```

Every facet except `translation` is required; a missing facet **aborts the
build** (`ResearchError`). Duplicate source `name` (by slug) is fatal.

### 2b. `bible/research/<topic>.md` → `Finding[]` + `Anchor[]`

```yaml
---
findings:
  - id: "f1"                       # unique within this file; referenced by anchors
    claim: "El ferrocarril de vía estrecha limitaba el tonelaje diario."
    asserted_by: "author"          # optional, default "author"
    sources: ["Kriegstagebuch des OKW, Bd. III"]   # source names; must resolve
    bears_on: "Wehrmacht"          # optional narrative-entity name (soft if unresolved)
    open: false                    # default false
  - id: "q-supply-route"           # an OPEN sub-question
    open: true                     # claim/sources may be omitted when open
anchors:
  - promotes: "f1"                 # MUST name a finding id in THIS file
    constrains: "Wehrmacht"        # entity name, or the literal "timeline"
    begin: 1943                    # optional integer years; or `date: 1943`; or begin/end
    end: 1943
---
```

Rules the reader enforces (all **fatal** unless noted):

- A non-open finding without a `claim` *and* ≥1 resolving `sources` → error.
- `sources` names that don't resolve in `sources.md` → error.
- `anchors[].promotes` naming an unknown finding id → error.
- `anchors[].constrains` missing → error; value `"timeline"` maps to the
  project timeline; any other value resolves against the bible — **a miss is a
  soft `ResearchWarning`**, build still succeeds (iteration-15's job to verify).
- `begin`/`end`/`date` must be integer years; `date` is mutually exclusive with
  `begin`/`end`.

### 2c. `bible/research/_index.md` → open questions + topic map

```yaml
---
open_questions:
  - id: "q-rail-gauge"             # parsed as OPEN findings (open_only=True)
    claim: "..."                   # optional
---
# Índice de investigación
## Temas
- [Logística de la Wehrmacht en 1943](logistica-de-la-wehrmacht-en-1943.md)
## Preguntas abiertas globales
- ...
```

`open_questions` are mapped as open findings: `claim`/`sources` optional. The
prose body (topic map, global open list) is human-facing and **not** parsed.

---

## 3. Filenames & identity

- **Topic → filename**: `golem.slug.make_slug(<topic title>)` →
  `<slug>.md`. The human title is preserved as the `# Heading` inside the file
  and in the `_index.md` topic map (edge case: spaces/accents/punctuation).
- **Source identity**: `make_slug(source.name)` — collisions across
  `sources.md` are fatal; the slug is also how `findings[].sources` names
  resolve. Names must be slug-unique.
- **Re-run on existing topic** (FR-017): the skill updates the existing
  `<topic>.md` / `_index.md` / `sources.md` in place — read first, merge, never
  clobber prior findings or provenance (same discipline as the bible mapper's
  in-place update).

---

## 4. Relationship to the graph (no schema change)

`graph build` already feeds `map_research()` output into the same `rdflib`
engine and saves `bible/graph.ttl` (`commands/graph/build.py`). Sources,
findings, and anchors are already CIDOC-CRM `E13`-style reifications emitted by
the iteration-13 entities — **no new GOLEM class, no ontology edit** (Constitution
X). This iteration adds zero triples-emitting code; it only causes conformant
files to exist for that pass to read.
