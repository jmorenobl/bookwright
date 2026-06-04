# Phase 1 Data Model — `factual_anchor` Validator

The validator introduces **no persisted entity and no new graph vocabulary**. It
adds small **in-memory projections** of the graph (read once through the indexer
seam) plus the **violation kinds** it emits. Everything here is frozen / pure so the
reasoning is deterministic and hashable (the runner dedupes on `Violation`).

## Reused types (unchanged)

| Type | Where | Role here |
|---|---|---|
| `Violation` | `validation/base.py:66` | the unit the validator returns; `(validator, severity, message, source, triples)`. |
| `Severity` | `validation/base.py:32` | `warning` for structural defects, `error` for anachronism. |
| `ValidationContext` | `validation/base.py:157` | carries `root` + `manifest`; the validator reads `manifest.research` and `manifest.book.language` from it. No new field added. |
| `EventInterval` | `validation/queries.py:45` | `(uri, begin: int\|None, end: int\|None)`. **Reused unchanged** for both event intervals and anchor time-spans (D2). |
| `RELIABILITY_IRI` | `golem/namespaces.py:254` | `name → IRI`; inverted to a rank map for FR-008 (D6). |
| `timeline_uri(uri_base)` | `golem/namespaces.py:275` | the untyped timeline IRI a constraint may target (D3). |

## New shared interval helpers (in `queries.py`)

```python
def parse_gyear(raw: str) -> int | None: ...          # was _parse_year; now exported (D2)

def intervals_disjoint(a: EventInterval, b: EventInterval) -> bool:
    """The ONE place that decides "two year ranges provably do not overlap" (D1, FR-011).
    Open bounds (None) never force disjointness. Used by BOTH temporal and factual_anchor."""

def load_timeline_bounds(indexer: Indexer) -> EventInterval:
    """Overall (min begin, max end) across every G5_Narrative_Event (D3).
    URI is timeline_uri-agnostic; both bounds None when no event carries years."""
```

`temporal._numeric`'s overlap branch is rewritten to call `intervals_disjoint`
(behaviour pinned by `test_temporal.py`).

## New anchor projections (in `anchor_queries.py`)

### `AnchorRecord` (frozen dataclass)

One per anchor in the graph, the validator's working unit.

| Field | Type | Source triple(s) |
|---|---|---|
| `uri` | `str` | the anchor's `crm:E13_Attribute_Assignment` node. |
| `promotes` | `str` | `bw:promotes` → finding URI (always present). |
| `constrains` | `str \| None` | `bw:constrains` → target URI; `None` when the reader dropped the link (no triple). |
| `span` | `EventInterval` | `crm:P4_has_time-span` → `E52_Time-Span` with `P82a`/`P82b`; `(None, None)` when the anchor carries no span. |

### `FindingSources` / source facets

Reached `anchor —bw:promotes→ finding —bw:supportedBy→ source`:

| Read | Predicate | Used by |
|---|---|---|
| supporting source URIs | `bw:supportedBy` | FR-006 (none → unsourced), FR-007, FR-008. |
| source facet presence | each of `bw:reference`, `bw:author`, `bw:originalLanguage`, `crm:P2_has_type`, `bw:reliability`, `bw:reliabilityJustification`, `bw:accessDate`, `bw:originalQuote`, `bw:translation` | FR-007 (one warning per missing facet). |
| source original language | `bw:originalLanguage` literal | FR-007 translation conditionality (vs `manifest.book.language`). |
| source reliability name | `bw:reliability` → invert `RELIABILITY_IRI` | FR-008 best-of ranking. |

### Presence checks

| Helper | Returns | Used by |
|---|---|---|
| `entity_present(indexer, uri)` | `bool` — uri is the subject of ≥1 triple, or is the timeline IRI | FR-009 (finding + constrained entity). |

## Reliability ordering (FR-008, D6)

```python
_RELIABILITY_RANK = {"baja": 0, "media": 1, "alta": 2}   # derived from RELIABILITY_IRI keys
```

Best reliability = `max(rank(r) for r in rated_supporting_sources)`; the anchor is
under-reliable when `best < rank(min_reliability_for_anchor)`, or when there is no
rated supporting source at all (best treated as below every threshold).

## Violation kinds emitted

| # | Kind | Severity | Trigger | `message` (shape) | `triples` |
|---|---|---|---|---|---|
| V1 | unsourced anchor | `warning` | FR-006 — promoted finding has no `bw:supportedBy` | `anchor '<a>' promotes a finding with no supporting source` | `(anchor, bw:promotes, finding)` |
| V2 | provenance-incomplete | `warning` | FR-007 — a supporting source lacks facet *f* (one per facet) | `source '<s>' backing anchor '<a>' is missing its <facet>` | `(finding, bw:supportedBy, source)` — the existing edge that locates the source; the missing facet is named in `message`, never fabricated as a triple |
| V3 | under-reliable | `warning` | FR-008 — best supporting reliability < threshold (incl. none rated) | `anchor '<a>' is backed only by sources below the minimum reliability '<min>'` | `(anchor, bw:promotes, finding)` |
| V4 | missing entity | `warning` | FR-009 — promoted finding or constrained entity absent (incl. dropped link) | `anchor '<a>' constrains a narrative entity that is not present in the graph` / `… promotes a finding not present in the graph` | `(anchor, bw:constrains, target)` when a target exists, else `(anchor, bw:promotes, finding)` |
| V5 | anachronism | `error` | FR-010 — `intervals_disjoint(span, target_interval)` over event/timeline target | `anchor '<a>' (<begin>–<end>) constrains '<event>' (<eb>–<ee>), but their year ranges are disjoint (anachronism)` | `(anchor, bw:constrains, target)` |

Every message names the offending anchor and the reason (FR-013, contract). `source`
is filled from `resolve_source` when the graph records a locator, else `None` (D7).

`Violation.triples` is typed `tuple[tuple[str, str, str], ...]` (`base.py:78`): every
triple is three concrete strings. A **missing** facet (V2) has no object to cite, so it
is **never** rendered as a triple with an empty/placeholder object; V2 instead carries
the real `(finding, bw:supportedBy, source)` edge that locates the source and names the
absent facet in `message`. No `Violation` fabricates a non-existent triple.

## Determinism

The validator iterates anchors and their sources in **sorted URI order** and emits
violations in a stable order; the runner additionally applies its explicit
total-order sort (`runner.sort_key`). Identical findings collapse via the frozen
`Violation`'s hashability. No set-iteration order leaks into the output (SC-005,
the project's byte-stable-output discipline).
