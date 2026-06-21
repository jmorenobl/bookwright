# Quickstart — Validate actionable source error messages

Runnable checks proving F1, F2, and the SPARQL note. Assumes `uv sync` has run.
See [contracts/error-messages.md](./contracts/error-messages.md) for the exact
assertable strings and [data-model.md](./data-model.md) for the message grammar.

## Prerequisites
```bash
uv sync
```

## Scenario 1 — F1: out-of-vocabulary `type` enumerates accepted values (US1)
Build a project whose `bible/research/sources.md` declares `type: primario` (a
near-miss for `primaria`). The build aborts and the error names the accepted set.

Expected `message` substring:
```
unknown source type 'primario' in bible/research/sources.md; one of: primaria, secundaria, oficial, académica, periodística, testimonial
```
Repeat with a bad `reliability` (e.g. `altísima`) → `one of: alta, media, baja`.

Unit-level (fastest): extend `tests/io/test_research.py` —
`test_out_of_vocabulary_aborts_naming_value` already triggers both; assert the
`one of: …` enumeration is present and equals `", ".join(SOURCE_TYPE_IRI)` /
`", ".join(RELIABILITY_IRI)`.

## Scenario 2 — F2: a per-source failure names the failing source (US2)
A `sources.md` with two valid sources and one whose `access_date` is **quoted**
(`access_date: "1937-04-26"`). The build aborts naming the failing source.

Expected `message` (named by `name`):
```
source 'Diario de X': access_date: Input should be a valid date ...
```
And, for a source that fails before `name` is readable (missing `name` facet):
```
source #3: source is missing required `name` in bible/research/sources.md
```

Unit-level: add `tests/io/test_research.py` cases that (a) quote `access_date` on a
named source and assert the `source '<name>': ` prefix + the preserved pydantic
reason; (b) drop the `name` facet and assert the `source #<n>: ` prefix.

## Scenario 3 — FR-011: a source is named once as a locator
- Duplicate name: assert the human name appears once (prefix) and the slug appears
  in the body — `source 'A': duplicate source name (slug 'a')`.
- Translation rule (book language ≠ source language, no translation): assert
  `source 'B': needs a translation (language 'fr' ≠ book 'es')` — name once.

## Scenario 4 — Non-regression (SC-005)
```bash
uv run pytest tests/io/test_research.py
```
The existing `test_valid_source_parses` and the success-path tests stay green; a
fully valid `sources.md` yields identical entities.

## Scenario 5 — SPARQL empty-result note is discoverable (US3, FR-008)
```bash
uv run bookwright graph query --help        # English note about non-existent IRI → empty result, not error
```
And the docs page `docs/commands/graph-query.md` carries the Spanish note. A test
asserts the English help substring; a test/docs-check asserts the Spanish note.

## Exit bar (run before finishing)
```bash
uv run pytest                       # full suite, ≥80% coverage
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```
All four green; `DEBT.md` no longer lists DEBT-006 (`grep -c DEBT-006 DEBT.md` → 0).
