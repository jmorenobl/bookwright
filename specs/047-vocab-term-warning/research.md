# Phase 0 Research — Soft warning for unrecognized Propp/Greimas terms

No `NEEDS CLARIFICATION` remained in Technical Context; the open design questions
are the *how* of an already-decided behavior (issue #1 track B, DEBT-016). Each is
resolved below with the codebase fact that grounds it.

## D1 — Where the silent typing happens (the sweep surface)

**Decision**: two sites, both an `active-vocabulary.resolve(name) → None`-then-mint
path.

- **Propp `functions:`** — `io/outline.py:_mint_functions` (~line 295):
  `type_uri = ctx.propp.resolve(raw) if ctx.propp is not None else None`. When
  `ctx.propp is not None` and `type_uri is None`, `raw` is an unrecognized Propp
  function minted untyped.
- **Greimas `narrative_roles:`** — `io/_bible_builders.py:_build_character`
  (~line 177): `uri = greimas.resolve(label); if uri is not None: role_types[...]`.
  The missing `else` is the silent Greimas no-match.

**Rationale**: these are the only two closed-vocabulary typing surfaces today
(`ActiveVocabularies` carries exactly `propp`/`greimas`). FR-007 demands both be
swept uniformly; patching one re-opens the debt class for the other (US2).

**Alternatives rejected**: a single shared helper wrapping `resolve`+warn — the two
call sites differ (one has `ctx`/`relpath` directly, one needs them threaded; one
pre-slugs, one must guard), so a shared helper would carry more glue than the two
3-line branches it replaces. Not worth the indirection at two sites.

## D2 — Which channel pattern to reuse

**Decision**: the **direct-report-model-in-`MapResult`** pattern (as `unknown_keys`
/ `unresolved_references`), not the **translate-at-`_graph`** pattern
(`research.warnings` → `ResearchTargetWarning`).

`MapResult` already holds `list[UnknownKey]` / `list[UnresolvedReference]`
(report.py models) and `_graph.py` copies them verbatim into `BuildReport`. The new
`UntypedVocabTerm` lives in `report.py` and `MapResult.untyped_vocab_terms` holds it
directly; `_graph.py` does `untyped_vocab_terms=tuple(result.untyped_vocab_terms)`.

**Rationale**: fewer moving parts than minting an io-layer record only to retype it
in `_graph.py`; the research translate-layer exists for historical reasons, not as
the preferred shape. The record `{path, field, term, vocabulary}` mirrors its
`ResearchTargetWarning` sibling (a vocabulary-adjacent `{path, field, name}`),
adding `vocabulary` (which vocab failed) and using `term` (the spec's field name).

## D3 — How to enumerate valid terms (and where)

**Decision**: `VocabularyIndex` gains `terms: tuple[str, ...] = tuple(sorted(set(labels)))`,
collected in `_index_turtle` from every `rdfs:label`. The human render
(`build.py`) derives the enumeration from the warning's `vocabulary` via
`load_vocabulary(vocabulary).terms`; the structured envelope record does **not**
carry it.

**Rationale**:
- FR-002 forbids denormalizing the full valid set into every record; research
  enumerates in its *message string*, not a per-record field. Render-derivation is
  the faithful mirror — `load_vocabulary` is `@cache`d and already loaded during the
  build, so the lookup is free.
- **All `rdfs:label`s, both languages, sorted, deduplicated**: the loader is
  deliberately manifest-free (`vocabularies.py` never reads the book language), so a
  language-filtered enumeration would force a new coupling for no real gain. Showing
  both ES and EN names is *more* useful to the bilingual author (the same name a
  slug could have matched). `sorted(set(...))` makes it byte-stable (FR-016) —
  curing the only nondeterminism risk (the label store has no guaranteed order).

**Alternatives rejected**:
- *One canonical label per term* — reintroduces a language choice the pure loader
  must not make; and "canonical" is undefined when a term has ES+EN labels.
- *Store the full set in each record* — explicitly barred by FR-002.

## D4 — Render layout (avoid repetition, stay in style)

**Decision**: `build.py:_print_summary` prints `N unrecognized vocabulary term(s):`
then one `  - {path}: {field} '{term}' is not a {vocabulary} term` line per entry,
then — **once per distinct `vocabulary`** present — a `  valid {vocabulary} terms:
a, b, c` line. Matches the existing per-channel `console.print` style on stderr.

**Rationale**: enumerating 31 (Propp) or 6 (Greimas) terms per offending entry would
bury the signal; grouping the enumeration once per vocabulary keeps it readable and
deterministic. Human prose stays on stderr (Principle IX); the `--json` envelope is
unchanged by the layout.

## D5 — Determinism (FR-016) without a new sort

**Decision**: rely on existing ordering; add no sort key.

- **Cross-entry order**: the bible character pass (`map_bible`) runs before the
  outline pass (`map_outline`), and each walks files in sorted-glob order — so
  Greimas entries (sorted-glob characters) precede Propp entries (sorted-glob
  units), each internally file-ordered. This is exactly how `unknown_keys` is
  already deterministic.
- **Intra-field order**: multiple bad terms in one `functions:`/`narrative_roles:`
  list follow authored YAML list order — the front-matter parser preserves it and
  `_distinct_slugs` / the role loop iterate in that order. (Clarification 2026-06-24:
  authored-sequence order, no second sort key — lowest debt.)
- **Enumeration order**: `terms` is pre-sorted at index build (D3).

**Rationale**: every axis is already total/stable; introducing a sort would be
unjustified plumbing (Constitution scope discipline) and risk reordering pinned
fixtures.

## D6 — Edge cases confirmed against the code

- **Blank / unsluggable term → no warning**: Propp pairs are pre-filtered by
  `_distinct_slugs` (unsluggable dropped before `_mint_functions`); the Greimas
  branch guards `make_slug(label)` and `continue`s on `EmptySlugError`. Neither
  mints a warnable untyped node, so neither warns (spec Edge Cases).
- **Repeated term → warned once**: Propp warns inside `if function is None:` (first
  mint); the function/type decision is itself deduped there, so reuse never re-warns.
  Greimas roles are per character (no cross-card dedup needed).
- **Valid term → typed, no warning**: the `if uri is not None` / `type_uri is not
  None` branches are unchanged; the warning is strictly the `else`.
- **Unknown active vocabulary name** (outside `KNOWN_VOCABULARIES`): already yields a
  `None` index slot, so no typing and no warning (FR-009 / spec Edge Cases).
- **No active vocabulary**: `propp`/`greimas` are `None`, the warn branches are
  unreachable, output byte-identical (US3 / SC-005).
