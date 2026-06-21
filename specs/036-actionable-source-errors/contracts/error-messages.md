# Contract — Error message strings

The stable, test-assertable contract for the improved `message` text. The JSON
envelope (`status`, `code=invalid_research`, `details={relpath, value}`) is
unchanged (FR-007); only the strings below change. Tests assert **substrings**, so
the exact surrounding punctuation may be tuned in implementation as long as the
contract substrings appear verbatim.

## C1 — Vocabulary enumeration (FR-001/002/003)

`_reject_unknown_vocab` raises, for an out-of-vocabulary `type`:

```
unknown source type {value!r} in {relpath}; one of: primaria, secundaria, oficial, académica, periodística, testimonial
```

and for an out-of-vocabulary `reliability`:

```
unknown reliability {value!r} in {relpath}; one of: alta, media, baja
```

**Contract substrings a test MUST assert:**
- the offending `value` is present (existing behaviour, kept).
- `one of: primaria, secundaria, oficial, académica, periodística, testimonial`
  appears verbatim for `type` — derived from `", ".join(SOURCE_TYPE_IRI)`.
- `one of: alta, media, baja` appears verbatim for `reliability` — derived from
  `", ".join(RELIABILITY_IRI)`.
- The enumerated list equals `", ".join(<the map>)` (a test may compute the
  expected list from the map itself to stay drift-proof).

**Interaction with the per-source prefix (C2):** `_reject_unknown_vocab` runs
inside the `_map_sources` loop body that C2's single locator point wraps, so the
emitted vocabulary error is *also* prefixed — the full runtime message is
`source '<name>': unknown source type {value!r} …; one of: …` (see data-model.md
"Composed examples"). The strings above are the **inner** reason; assert them as
**substrings**, never with `startswith`.

## C2 — Per-source locator prefix (FR-004/005/006)

Every `ResearchError` raised inside the per-source loop is re-emitted prefixed:

```
source {id}: {inner message}
```

where `{id}` is:
- `'{name}'` (single-quoted) when `raw["name"]` is a non-empty `str` accepted by
  `make_slug`;
- `#{n}` (1-based loop position) otherwise.

**Contract substrings a test MUST assert:**
- A source with a valid `name` failing on another field (quoted `access_date`):
  message starts with `source '<name>': ` **and** still contains the underlying
  reason (e.g. `Input should be a valid date`) — FR-006.
- A source failing with no usable `name` (e.g. `name` facet missing): message
  starts with `source #<n>: ` carrying the correct 1-based position.
- `code == "invalid_research"` and `details` keys are `relpath`, `value`
  (envelope unchanged, FR-007).

## C3 — FR-011 single-locator reconciliation

**Translation-rule** inner message (after change):
```
needs a translation (language {orig!r} ≠ book {book!r})
```
Prefixed: `source '{name}': needs a translation (language 'fr' ≠ book 'es')`.
- Contract: the source name appears **once** (in the prefix) — assert the
  substring `source '{name}':` occurs exactly once.

**Duplicate-name** inner message (after change):
```
duplicate source name (slug {slug!r})
```
Prefixed: `source '{name}': duplicate source name (slug '{slug}')`.
- Contract: the human `{name}` appears **once** (prefix); the `{slug}` (the
  retained semantic subject) appears in the body.

## C4 — SPARQL empty-result note (FR-008)

**Command help** (`graph query`, English, in `query.py`): the `sparql` argument
`help=` text contains a note that an unknown / misspelled IRI returns an empty
result set, not an error. Contract substring (illustrative — final wording set in
implementation): a phrase combining `non-existent`/`misspelled` `IRI` with
`empty`/`zero` result and `not an error`.

**Docs page** (`docs/commands/graph-query.md`, Spanish): a short note with the same
meaning (e.g. *"un IRI inexistente o mal escrito devuelve cero resultados, no un
error"*).

- Contract: a test asserts the English note substring is present in the command's
  help output; a test (or docs check) asserts the Spanish note is present in the
  docs page.

## C5 — Non-regression (SC-005)

- A fully valid `sources.md` (`SOURCES_OK` fixture) produces identical entities
  (count, URIs, fields) to before — the wrapping never touches the success path.
- `to_json()` for any research error keeps the keys `status`, `code`, `message`
  and (when present) `details` with sub-keys `relpath`, `value`.
