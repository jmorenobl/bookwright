# Phase 1 Data Model: prose/structure seam

In-memory only — nothing here is persisted (validators stay graph-free,
`triples=()`). All types live in `src/bookwright/io/prose.py`.

## `ProseLine` (the classified line)

A frozen dataclass: one line of a Markdown source.

| Field | Type | Meaning |
|-------|------|---------|
| `number` | `int` | 1-based source line number, from `enumerate(text.splitlines(), start=1)`. Preserved verbatim for locators (FR-002a, FR-010). |
| `raw` | `str` | The original line, unmodified (FR-002b). Read by dialogue-sensitive scans. |
| `normalized` | `str` | The line with its leading structural block prefix(es) removed, iteratively (FR-002c, FR-003). Read by the proper-noun / declaration scans. |

- **No `kind` field** — prefix recognition is internal to computing `normalized`
  (FR-002). Frozen + hashable for cheap reuse.
- **Invariant**: `normalized` is `raw` with zero or more leading block prefixes
  stripped; `normalized` is a suffix of `raw` after the stripped span (never adds
  or reorders characters). `number` is independent of any regex match offset.

## `ProseView` (the prose/structure view)

`ProseView = tuple[ProseLine, ...]` — the ordered sequence of classified lines for
one Markdown source. It is the single object validators iterate in place of
`text.splitlines()` (Key Entities). A type alias, not a wrapper class: it carries
no methods (the placeholder predicate is a sibling helper, D1/D5).

- **Ordering**: source order, ascending `number`. `prose_view("")` and
  `prose_view` of whitespace-only / absent input yield `()` (empty view) — Edge
  Cases "Empty manuscript / empty constitution".

## Module-level functions (the seam's surface)

| Function | Signature | Contract |
|----------|-----------|----------|
| `prose_view` | `(text: str) -> ProseView` | Split `text` into `ProseLine`s (FR-001/002/003). |
| `is_placeholder` | `(body: str) -> bool` | `True` iff `body` is *solely* a `[PENDING: …]` token (FR-005, mirrors `_PENDING_ONLY`). |

Internal (private, not exported): the two compiled recognizers and the `normalize`
helper (D2). See `contracts/prose-seam.md` for exact patterns and behaviour tables.

## `ValidationContext` additions (`validation/base.py`)

Two cached accessors, same `_UNSET`/memo pattern as `manuscript_files()` /
`constitution_text()` (FR-006, D6):

| Accessor | Return | Built from | Memo field |
|----------|--------|-----------|------------|
| `manuscript_view()` | `tuple[tuple[str, ProseView], ...]` (sorted `(relpath, view)`) | `manuscript_files()` (no second disk read) | `_manuscript_view` |
| `constitution_view()` | `ProseView` | `constitution_text()`; `()` when `None` | `_constitution_view` |

- Two new dataclass fields `_manuscript_view`/`_constitution_view`, both
  `field(default=_UNSET, repr=False, compare=False)`, mirroring the existing six.

## Consumer changes (no new validator types)

No new `Violation`/`Severity`/registry types. Each validator keeps its class,
`name`, `severity_default`, and emitted `Violation` shape (`triples=()`); only the
*reading* of source text changes (D7). The deleted module-level constants:

- `character_presence`: `_HEADING_MARKER`.
- `focalization`: `_BULLET`, `_LEAD_EMPHASIS`, `_CLOSE_EMPHASIS`,
  `_normalize_declaration_line` (function), `_PENDING_ONLY`. `_DECLARATION` is
  widened (D4) to absorb the emphasis handling.
- `setting_continuity`: no constant deleted; its per-line `text.splitlines()` loop
  becomes a `manuscript_view()` iteration over `.raw`.
