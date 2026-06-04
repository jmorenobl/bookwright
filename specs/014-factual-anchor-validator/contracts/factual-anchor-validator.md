# Contract — `factual_anchor` Validator

The behavioural contract of the fifth built-in validator. Binding for
FR-001..FR-017. It conforms to the existing
[Validator Protocol](../../010-validation-system/contracts/validator-protocol.md);
this document specifies only what is new.

## Identity & discovery

```python
class FactualAnchor:
    name: ClassVar[str] = "factual_anchor"
    severity_default: ClassVar[Severity] = Severity.warning   # FR-002
    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]: ...
```

- **Auto-discovered** as a built-in by `registry._discover_builtins()` (it lives in
  `validation/validators/factual_anchor.py`); **no** hand-registration, **no** new
  discovery mechanism (FR-004).
- Subject to `[validators].enabled` / `[validators].disabled` via the existing
  `resolve_active` rules (FR-004). Listing `factual_anchor` under `disabled` removes
  it; an `enabled` allow-list including it runs it (US3 scenarios 2–3).
- Returns only `Violation`s; `validate --json` / `--scope` / `--severity` behave
  unchanged (FR-005). The runner isolates a raise (FR-003 forbids it raising in
  normal operation; the contract still relies on runner isolation as a backstop).

## Inert preconditions (return `[]` immediately)

1. `project.manifest.research.enabled is False` → **no violations** even if anchors
   exist (FR-015, US3 scenario 4).
2. The graph contains **no** anchor node → **no violations** (FR-016, US3 scenario
   1) — covers a project with no `bible/research/` and a research project with no
   promoted anchors.

## Determinism & purity (FR-003)

The validator MUST NOT write to disk, fetch over the network, mutate the graph, or
invoke an LLM. It reads the built graph through `indexer.query(...)` and the
manifest through the `ValidationContext`. Same inputs ⇒ byte-identical output.

## Rules

For every anchor (iterated in sorted URI order), reached via
`anchor —bw:promotes→ finding —bw:supportedBy→ source(s)` and
`anchor —bw:constrains→ target`:

| Rule | FR | Severity | Fires when | Emits |
|---|---|---|---|---|
| **R1 unsourced** | FR-006 | warning | the promoted finding **exists** but has no `bw:supportedBy` source (incl. an open finding); **suppressed** when the finding is absent from the graph (reported once by R4, no double-label) | one warning per anchor |
| **R2 provenance-incomplete** | FR-007 | warning | a supporting source lacks a mandatory facet | **one warning per missing facet** (clarification) |
| **R3 under-reliable** | FR-008 | warning | ≥ 1 supporting source exists **and** (best supporting reliability `< min_reliability_for_anchor` **or** none of them is rated). **Not** evaluated for a zero-source anchor — that is R1's *unsourced* warning (no double-label) | one warning per anchor; an **unrated** source is *not* additionally flagged here (no double-label) |
| **R4 missing entity** | FR-009 | warning | the promoted finding, or the constrained entity (incl. a dropped `bw:constrains` link), is absent from the graph | one warning per missing reference |
| **R5 anachronism** | FR-010 | **error** | the anchor carries a time-span and `intervals_disjoint(span, target_interval)` is true for an **event** or the **timeline** target | one error per clash |

### R2 — the mandatory facets

`bw:reference`, `bw:author`, `bw:originalLanguage`, `crm:P2_has_type` (source type),
`bw:reliability`, `bw:reliabilityJustification`, `bw:accessDate`, `bw:originalQuote`,
and `bw:translation` **only when** the source's `bw:originalLanguage` ≠
`manifest.book.language`. A source missing several facets yields several distinct
warnings, each naming the facet.

This predicate set is the membership emitted by `provenance.Source.to_triples()` (D5),
pinned by a drift-guard test — **not** `io/research._SOURCE_FACETS` (field-names:
includes `name`, omits `translation`). A missing facet has no object to cite, so its
`Violation.triples` carries the existing `(finding, bw:supportedBy, source)` edge that
locates the source; the absent facet is named in `message`, never fabricated as a triple.

### R3 — reliability ordering

`baja < media < alta` (from `RELIABILITY_IRI`). Threshold default `"media"`. An
unrated supporting source contributes nothing to the best-of computation (its
missing rating is reported once by R2 only). The message distinguishes the two
triggers: a rating present but too low → "backed only by sources below the minimum
reliability '<min>'"; sources present but **none** rated → "backed by sources but
none carries a reliability rating (minimum required: '<min>')".

### R5 — the shared contradiction predicate (FR-011)

Both `temporal` and `factual_anchor` decide interval contradiction through the
single `queries.intervals_disjoint`:

```python
def intervals_disjoint(a: EventInterval, b: EventInterval) -> bool:
    """True when two closed year ranges provably do not overlap; open bounds never
    force disjointness. The ONE source of truth for interval contradiction."""
```

Target interval resolution (D3):
- target is a `G5_Narrative_Event` → its `load_intervals` interval;
- target is the `timeline_uri(uri_base)` → `load_timeline_bounds(indexer)`;
- target is any other entity (character/setting/…) or absent → **no comparable
  interval** → R5 emits nothing (FR-012, no false positive).

R5 only considers the bound(s) the span actually carries; an open-ended span
(`begin` only or `end` only) compares just the present bound (edge case).

## `Violation` payload (FR-013)

- `validator = "factual_anchor"`.
- `message` names the offending anchor and the reason, locatable without reading
  source.
- `source` = `resolve_source(indexer, anchor_uri)` when the graph records a
  locator, else `None` (location-less; FR-013 MAY clause — anchors currently carry
  no locator, exactly as `temporal` is location-less for some findings).
- `triples` carries the implicated **existing** `(s, p, o)` edges (the `bw:promotes`,
  `bw:supportedBy`, or `bw:constrains` edge as applicable) — never a triple with an
  empty/placeholder object (`Violation.triples` is three concrete strings).

## Out of scope (FR-017)

No semantic truth check (that is `bookwright-verify`, a later iteration), no
auto-fix, no vector search, no new GOLEM ontology class. The validator reports only.
