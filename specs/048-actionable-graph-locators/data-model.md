# Phase 1 Data Model — Actionable locators for graph-consumer validators

In-memory only (the subsystem persists nothing — FR-013). This iteration adds **no**
new entity and **no** new serialized field; it adds one accessor, one shared helper,
and changes two value-fields of existing `Violation`s. The frozen GOLEM ontology is
untouched (Principle X / FR-008).

## 1. Existing shapes reused as-is (no change)

- **`AnchorIdentity`** (`io/_research_identity.py`) — the authored, corpus-stable
  identity per anchor: `promotes_id`, `constrains` (`str | "timeline" | None`),
  `relpath` (the `bible/research/<topic>.md` file), `uri` (the in-process minted
  join key, never serialized). **This is the data `factual_anchor` reuses** for the
  file (`relpath`) and the handle (`promotes_id` [+ `constrains`]).
- **`AnchorGap`** (`status/model.py`) — `promotes` / `constrains` / `file` /
  `problems`. Its `_anchor_line` rendering is the handle spelling being extracted
  into the shared helper (D2). No field change.
- **`AnchorRecord`** (`validation/anchor_queries.py`) — `uri` / `promotes` /
  `constrains` / `span`. **Unchanged**; it stays a pure graph projection. (Spec
  Option A — extending it with `relpath` — is **rejected**: the relpath lives in the
  identity, not the graph; see `research.md` D1/D2.)
- **`Violation`** (`validation/base.py`) — `validator` / `severity` / `message` /
  `source` / `triples`. **Shape unchanged.** Only the `source` and `message`
  *values* of `temporal` (a/b/c) and `factual_anchor` violations change.
- **`resolve_source(indexer, uri)`** (`validation/queries.py`) — reused verbatim
  (FR-006), `:line`-preferring then lexicographically smallest.

## 2. New / changed surfaces

### 2.1 `anchor_handle(promotes, constrains)` — new free function (D2)

`io/_research_identity.py`. The **single** spelling of the author-facing anchor
handle, consumed by both `status._anchor_line` and `factual_anchor`.

| Input | Type | Notes |
|---|---|---|
| `promotes` | `str` | the promoted finding's authored id (`AnchorGap.promotes` / `AnchorIdentity.promotes_id`). |
| `constrains` | `str \| None` | authored target name / `"timeline"` / `None` (dropped or absent). |

Returns `f"{promotes} -> {constrains}"` when `constrains is not None`, else
`promotes` alone. Pure, total, no I/O. Byte-identical to today's `_anchor_line`
inline format (FR-009).

### 2.2 `ValidationContext.anchor_corpus()` — new memoized accessor (D1)

`validation/base.py`. Returns `tuple[Indexer, tuple[AnchorIdentity, ...]]` — a
fresh, **non-persisting** research corpus engine and its anchor identities from one
build, so the anchor URIs in the engine and the identities **match** (the join key
is coherent within this single build).

- **Construction**: reuse the already-memoized `self.outline()` `MapResult` (bible +
  outline triples + `build_provenance`) indexed into a fresh
  `resolve_indexer(manifest.bookwright.indexer)()`, then `map_research(root,
  bible/research, uri_base, book.language, result.entity_index, timeline_uri(...))`
  triples added. **No `engine.save`** (a validator never writes — FR-013). Active
  vocabularies are omitted (they only add `P2_has_type` typing, irrelevant to
  anchors/findings/intervals — same rationale as `outline()`).
- **Memoization**: a `_anchor_corpus` slot (`_UNSET` sentinel), like the other
  accessors — built once per run, shared if `factual_anchor` is asked twice.
- **Injection seam (tests, D4)**: an optional pre-set corpus; when present the
  accessor returns it instead of building. Lets the hand-built `AnchorSpec` unit
  fixtures supply `(engine, identities)` directly.

### 2.3 `factual_anchor` resolution (FR-003/FR-004/FR-010)

Per anchor, resolve once:

| Case | `source` | message identifier |
|---|---|---|
| identity found (`id_by_uri[anchor.uri]`) | `identity.relpath` (file-only) | `anchor_handle(identity.promotes_id, identity.constrains)` |
| identity **absent** (FR-010 defensive floor) | `None` | `_label(anchor.uri)` (uuid7 tail) |

The resolved `(handle, source)` replace, respectively, every `_label(anchor.uri)`
in a message and the `resolve_source(indexer, anchor.uri)` in `_violation` /
`_anachronism`. The **source** entity's own `_label(source.uri)` in the R2 message
is a stable slug and stays unchanged (only the **anchor** uuid7 is the problem).

### 2.4 `temporal` rules a/b/c `source` (FR-001/FR-002)

| Rule | implicated event used | `source` |
|---|---|---|
| (a) cycle | `component[0]` — lexicographically smallest event URI in the SCC | `resolve_source(indexer, event)` |
| (b) order-vs-overlap | the carried triple's subject `a` | `resolve_source(indexer, a)` |
| (c) containment-vs-order | the carried triple's subject `a` | `resolve_source(indexer, a)` |
| (d) numeric | *(unchanged)* `a` | *(unchanged)* `resolve_source(indexer, a)` |

All four end uniform; events are slug-stable so this works on the **passed** disk
graph with no rebuild.

## 3. Determinism & invariants

- **Byte-stability (FR-002)**: `temporal` `source` is reproducible across
  two builds (slug URIs + fixed event choice). `factual_anchor` `source` and
  `message` are reproducible (stable authored `relpath`/handle); `triples` keep the
  minted anchor URI — **pre-existing**, out of scope.
- **No new sort key**: the runner's `sort_key` (validator, severity, source,
  message, triples) already totally orders the now-stable `source`/`message`.
- **Inert path preserved**: `factual_anchor` returns `[]` with no corpus build when
  `[research].enabled` is false; a corpus with no anchors likewise yields `[]`.
- **Gate/exit-code untouched (FR-005/SC-005)**: same findings, same severities.
