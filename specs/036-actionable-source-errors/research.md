# Phase 0 — Research & Decisions

Iteration 036 (DEBT-006). No external research needed: every decision is grounded
in the existing loader code (`src/bookwright/io/research.py`), the vocab maps
(`src/bookwright/golem/namespaces.py`), the error base (`src/bookwright/errors.py`),
and the `graph query` surface. The spec's Clarifications session already fixed the
three open questions; this file records the implementation-level decisions.

## Decision 1 — Enumeration source & order (FR-003)

**Decision**: Enumerate the **keys** of `SOURCE_TYPE_IRI` (for `type`) and
`RELIABILITY_IRI` (for `reliability`), joined as `", ".join(...)` and embedded as
the substring `one of: <v1>, <v2>, …`. The keys are the accented author-facing
values (`primaria`, `secundaria`, `oficial`, `académica`, `periodística`,
`testimonial`; `alta`, `media`, `baja`).

**Rationale**: Python dicts preserve insertion order, and both maps are authored
as literals in `namespaces.py`, so `list(SOURCE_TYPE_IRI)` is a deterministic,
declaration-ordered sequence — identical on every run, so a test can assert the
exact string (FR-003). Reusing the same map the validator already checks against
guarantees the enumerated set can never drift from the accepted set (single
source of truth — add a value to the map and the message follows for free).

**Alternatives rejected**:
- Hard-coding the value list in the message string → drifts from the map; a future
  vocabulary addition would silently leave the error stale. Rejected.
- Sorting the keys alphabetically → still deterministic but loses the meaningful
  authored order (`primaria` before `secundaria`, `alta`/`media`/`baja`
  high→low); declaration order is both stable and intentional.

## Decision 2 — Single per-source prefix point (FR-004, US2)

**Decision**: Wrap the **body of the `for raw in raw_sources` loop** in
`_map_sources` in one `try/except ResearchError`. On catch, compute the source
identifier and re-raise a `ResearchError(exc.relpath, f"source {id}: {exc.message}",
exc.value)` — same `code` (class attribute), same `details` (`relpath`, `value`).
This is the **only** place that knows both the 1-based index *and*, after a read,
the candidate `name`; it is a single locator point, not a prefix bolted onto each
`raise` site.

**Rationale**: Loop-boundary wrapping is the only scope that satisfies US2
scenario 2 (a failure *before* `name` is read — e.g. a missing-`name` facet — where
the 1-based index is the only available locator). The `ResearchError` raised deep
in `_build_source`/`_apply_translation_rule` bubbles to exactly one handler. The
re-raise reuses `BookwrightError.message`/`.details` (verified in
`src/bookwright/errors.py`: `self.message` holds the human text, `self.details`
the `{relpath, value}` dict), so the envelope is byte-compatible (FR-007) and the
underlying reason is preserved verbatim (FR-006).

**Alternatives rejected**:
- Prefixing at each individual `raise` in `_build_source` / `_reject_unknown_vocab`
  / `_apply_translation_rule` → many locator points, violates FR-004's "single
  point", and `_build_source` does not always know the 1-based index. Rejected.
- Threading the identifier as a parameter into every helper → invasive, widens
  signatures, and still leaves the index unknown to value-level helpers. Rejected.

## Decision 3 — Identifier resolution: name-or-index (FR-005, edge cases)

**Decision**: A small helper resolves the identifier from the raw mapping and the
0-based loop index `i`:
- If `raw.get("name")` is a non-empty `str` **and** `make_slug(name)` succeeds
  (does not raise `EmptySlugError`) → identifier is the **name single-quoted**:
  `'Diario de X'`.
- Otherwise → identifier is `#<n>` where `n = i + 1` (1-based position).

The two forms are visually distinguishable (single quotes vs `#`), so the author
knows whether they got a name or a row number (SC-002).

**Rationale**: Covers all spec edge cases with one predicate: name present &
usable → name; name empty/absent/unsluggable, or failure before name is read →
index. Reusing `make_slug` for the "usable" test ties the locator's notion of
usability to the loader's own (the same `EmptySlugError` the model raises).

**Placement**: Define the helper in `research.py` next to `_map_sources`. If the
file would exceed 500 lines (Constitution IV — it is 463 today), move it to the
existing `io/_research_identity.py` companion (already imported by `research.py`),
which is the natural home for source-identity logic.

## Decision 4 — FR-011 reconciliation: name a source once as a locator

Two per-source errors embed the source name inline today. After the uniform prefix
is added, each must be reconciled so the **locator** identity appears exactly once.

- **Translation-rule error** (`_apply_translation_rule`): today
  `source {source.name!r} needs a translation (language … ≠ book …)`. Here the
  name is a **pure locator** — the prefix now supplies it. **Decision**: drop the
  inline `source {name!r}` framing; keep only the reason
  (`needs a translation (language {orig!r} ≠ book {book!r})`). Prefixed result:
  `source 'X': needs a translation (language 'fr' ≠ book 'es')`.
- **Duplicate-name error** (`_map_sources`): today
  `duplicate source name {source.name!r} (slug {slug!r})`. FR-011's final sentence
  is controlling: the **duplicated value is the semantic subject** of this fault and
  is retained — it is not a redundant locator. **Decision**: report the subject as
  the **slug** (`duplicate source name (slug {slug!r})`), dropping the inline human
  `{source.name!r}` (which equals the prefix and is the redundant locator). The
  slug is the actual collision key (two distinct names can slug identically), so it
  is the more correct subject and avoids naming the same source twice. Prefixed
  result: `source 'X': duplicate source name (slug 'x')`.

**Rationale**: This satisfies both halves of FR-011 simultaneously — the redundant
inline *locator* (the human name, duplicated by the prefix) is removed from both
errors, while the duplicate-name fault retains its *subject* (the colliding slug).
No message names the same source twice as a locator.

**Alternative considered**: keep `{source.name!r}` in the duplicate-name message as
the subject (accepting an intentional double mention: prefix + subject). Rejected
in favour of the slug because it is unambiguous about *what* collided and keeps the
"named once" invariant literal — the slug is a different token from the prefix name.

## Decision 5 — SPARQL footgun: document in both surfaces (FR-008, US3)

**Decision**: Add a brief note to **both** (a) the `sparql` argument `help=` string
in `src/bookwright/commands/graph/query.py` (English, in-product, the surface
SC-004 demands reachable "without reading source code") and (b)
`docs/commands/graph-query.md` (Spanish, per language conventions). Content: a
query that references a non-existent / misspelled class or predicate IRI is still
valid SPARQL, so it **succeeds with zero rows** — indistinguishable from "no data
matches"; double-check IRI spelling when a query unexpectedly returns nothing.

**Rationale**: The decision is explicitly *document, not fix* — validating
arbitrary user IRIs against the graph is out of scope (spec Assumptions, Out of
Scope). Both surfaces are mandatory so the note is discoverable from either.

**Alternatives rejected**: any IRI-existence validation over arbitrary SPARQL →
out of scope, and would couple query to schema knowledge it deliberately lacks.

## Decision 6 — No new error type, code, or field (FR-007)

**Decision**: Reuse `ResearchError` (code `invalid_research`) unchanged; the
`details` dict (`{relpath, value}`) is unchanged. Only the `message` string carries
the enrichment.

**Rationale**: Constitution IX and FR-007 require a byte-compatible envelope. The
re-raise constructs a new `ResearchError` with the same class (→ same `code`) and
the same `relpath`/`value` (→ same `details`), proving the contract holds.
