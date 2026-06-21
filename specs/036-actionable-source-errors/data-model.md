# Phase 1 — Data Model

This iteration changes **no** data model: no schema field, no vocabulary value, no
ontology class, no error type/code/field. The only "model" affected is the shape of
the human-readable `message` string inside the existing error envelope. This file
documents that message grammar and the unchanged structures it rides on.

## Unchanged structures (for reference)

### `Source` (golem/modules/provenance.py)
Frozen Pydantic v2 model. Relevant facets: `name` (human identifier), `type`
(closed vocab via `SOURCE_TYPE_IRI`), `reliability` (closed vocab via
`RELIABILITY_IRI`), `access_date` (a date authors sometimes quote → pydantic
`ValidationError`). **No change.**

### Closed vocabularies (golem/namespaces.py)
- `SOURCE_TYPE_IRI`: ordered keys `primaria, secundaria, oficial, académica,
  periodística, testimonial`.
- `RELIABILITY_IRI`: ordered keys `alta, media, baja`.
Both are `dict[str, URIRef]` literals; key order = declaration order = enumeration
order (Decision 1). **No change** — read-only consumers of `.keys()`.

### `ResearchError` (io/errors.py)
`code = "invalid_research"`; `__init__(relpath, message, value=None)`;
`details = {"relpath": relpath, "value": value}`. Inherits `to_json()` →
`{status, code, message[, details]}`. **No change** — we only pass a richer
`message` and re-construct with the same `relpath`/`value`.

## The message grammar (the actual deliverable)

### Per-source locator prefix (F2, FR-004/005/011)
Every `ResearchError` raised while processing **one** source is re-emitted as:

```
source <id>: <original reason>
```

`<id>` ::= `'<name>'`  — when `raw["name"]` is a non-empty `str` that `make_slug`
                         accepts (single-quoted human name)
        |  `#<n>`      — otherwise; `n` = 1-based loop position

`<original reason>` is the verbatim `message` of the inner `ResearchError`
(FR-006), after the FR-011 reconciliation below.

### Vocabulary enumeration (F1, FR-001/002/003)
The two out-of-vocabulary messages (inner reasons, before prefixing):

```
unknown source type <value!r>; one of: primaria, secundaria, oficial, académica, periodística, testimonial
unknown reliability <value!r>; one of: alta, media, baja
```

- `<value!r>` is the offending value (Python `repr`, as today — keeps the existing
  value-naming behaviour and the `details.value`).
- `one of: …` is `", ".join(SOURCE_TYPE_IRI)` / `", ".join(RELIABILITY_IRI)` —
  comma-space, unquoted, declaration order (FR-003).
- The trailing `in {relpath}` segment present today is retained or folded — see the
  contract file for the exact final strings; the `relpath` also remains in
  `details`.

### FR-011-reconciled inner reasons
- Translation-rule (was `source {name!r} needs a translation …`):
  `needs a translation (language <orig!r> ≠ book <book!r>)` — inline name removed.
- Duplicate-name (was `duplicate source name {name!r} (slug {slug!r})`):
  `duplicate source name (slug <slug!r>)` — inline human name removed; slug (the
  collision subject) retained.

### Composed examples
```
source 'Diario de X': access_date: Input should be a valid date          # F2 quoted-date
source #3: source is missing required `name`                             # F2, name unavailable → index
source 'Café': unknown source type 'primario'; one of: primaria, secundaria, oficial, académica, periodística, testimonial   # F1 + prefix
source 'A': duplicate source name (slug 'a')                             # FR-011 (subject = slug; locator = prefix)
source 'B': needs a translation (language 'fr' ≠ book 'es')             # FR-011 (locator only in prefix)
```

## Validation rules (unchanged behaviour)
- A missing required facet, out-of-vocabulary value, model `ValidationError`,
  empty/unsluggable name, duplicate name, or translation-rule violation still
  **aborts** the build with no graph (research fault model D7). Message content is
  the only change.
- A fully valid `sources.md` produces **identical** entities to before (SC-005,
  US1 scenario 3 / US2 scenario 3) — the wrapping only intercepts the error path.

## Envelope invariant (SC-005, FR-007)
`status`, `code` (`invalid_research`), and `details` keys (`relpath`, `value`) are
byte-identical to before. Only `message` text changes.
