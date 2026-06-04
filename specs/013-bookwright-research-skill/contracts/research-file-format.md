# Contract: `bible/research/` file format (the `map_research` parse target)

This is the **output contract** the `bookwright-research` skill and the
`resources/templates/bible/research/` templates MUST satisfy. It is *derived
from* (not the definition of) `bookwright.io.research.map_research` +
`bookwright.golem.modules.provenance`, both on `main` (iteration 13). The reader
is **strict**: violations marked *fatal* abort `graph build` with a
`ResearchError` and produce no graph.

Processing order (deterministic): `sources.md` → each `<topic>.md` (sorted) →
`_index.md`.

## Controlled vocabularies

- `type` ∈ `{primaria, secundaria, oficial, académica, periodística, testimonial}`
- `reliability` ∈ `{alta, media, baja}`
- An out-of-vocabulary `type` or `reliability` is **fatal**, error names the value.

## `sources.md`

Front-matter key `sources:` → a list of mappings. Per item:

| Key | Required | Type | Notes |
|---|---|---|---|
| `name` | ✅ | str | slug-unique across the file (duplicate slug = **fatal**) |
| `reference` | ✅ | str | citation locator |
| `author` | ✅ | str | |
| `original_language` | ✅ | str | ISO 639-1 |
| `type` | ✅ | enum | see vocab |
| `reliability` | ✅ | enum | see vocab |
| `reliability_justification` | ✅ | str | non-empty (entity validator) |
| `access_date` | ✅ | date | ISO `YYYY-MM-DD` (`xsd:date`) |
| `original_quote` | ✅ | str | original-language quotation |
| `translation` | conditional | str | **required iff** `original_language != book.language`; **dropped** when equal |

- A missing required facet is **fatal** (error names the facet).
- The translation rule is **fatal** when violated (missing translation for a
  foreign-language source).

## `<topic>.md`

Front-matter keys `findings:` and `anchors:` (both optional lists).

### `findings[]`

| Key | Required | Type | Notes |
|---|---|---|---|
| `id` | ✅ | str | non-empty; unique within the file; anchor target |
| `claim` | conditional | str | required unless `open: true` |
| `sources` | conditional | list[str] | ≥1 resolving source name unless `open: true`; each must resolve in `sources.md` (**fatal** if not) |
| `asserted_by` | ❌ | str | default `"author"` |
| `bears_on` | ❌ | str | narrative-entity name; unresolved = **soft** `ResearchWarning` |
| `open` | ❌ | bool | default `false` |

- A non-open finding lacking `claim` **or** ≥1 resolving source is **fatal**.

### `anchors[]`

| Key | Required | Type | Notes |
|---|---|---|---|
| `promotes` | ✅ | str | a finding `id` **in this file** (**fatal** if unknown) |
| `constrains` | ✅ | str | narrative-entity name, or literal `"timeline"`; key absent = **fatal**; unresolved entity = **soft** warning |
| `begin` | ❌ | int | year; integer only (**fatal** otherwise) |
| `end` | ❌ | int | year |
| `date` | ❌ | int | year; **mutually exclusive** with `begin`/`end` (**fatal** if combined) |

## `_index.md`

Front-matter key `open_questions:` → a list mapped as **open findings**
(`open_only=True`): `id` required, `claim`/`sources` optional. The Markdown body
(topic map + global open list) is human-facing and **not parsed**.

## Soft vs fatal — summary

- **Fatal** (`ResearchError`, no graph): malformed YAML; missing source facet;
  unknown vocab; duplicate source name; non-open finding without claim/sources;
  unresolved source name; anchor promoting an unknown finding; missing
  `constrains`; non-integer span; `date` combined with `begin`/`end`; translation
  rule breach.
- **Soft** (`ResearchWarning`, graph still built): a `bears_on`/`constrains`
  narrative target that does not resolve in the bible index (the link triple is
  omitted; iteration-15 validates existence).
- **Empty/absent** `bible/research/` → zero entities, never raises.

## Conformance test target (SC-003, SC-004, SC-005)

A fixture project with a `sources.md` (one foreign-language source with
`translation`, one conflicting-account pair), a `<topic>.md` (≥1 finding with
full provenance, ≥1 anchor `constrains`-ing a real bible entity, ≥1 open
finding), and an `_index.md` MUST:

1. Pass `map_research()` with **zero** `ResearchError`.
2. After `graph build`, a SPARQL query retrieves ≥1 anchor constraining a named
   entity (SC-003).
3. Conflicting sources appear as **two** findings, each with its own provenance
   (SC-005) — no silent collapse.
