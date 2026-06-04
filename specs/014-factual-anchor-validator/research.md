# Phase 0 Research — `factual_anchor` Validator

The spec's Clarifications session (2026-06-04) already resolved the two open
behavioural questions (per-facet vs per-source reporting; how FR-007 and FR-008
interact on an unrated source). There are therefore **no `NEEDS CLARIFICATION`
markers** left. This document records the *design decisions* — how the requirements
become code that reuses the existing system instead of duplicating it. Each
decision lists what was chosen, why, and the alternatives rejected.

---

## D1 — One source of truth for "two intervals contradict" (FR-011)

**Decision.** Extract a single pure predicate into
`bookwright/validation/queries.py`:

```python
def intervals_disjoint(a: EventInterval, b: EventInterval) -> bool:
    """True when the two closed year ranges provably do not overlap.
    An open bound (``None``) is treated as unbounded on that side, so it never
    forces disjointness (an open-ended span cannot be proven disjoint)."""
    if a.end is not None and b.begin is not None and a.end < b.begin:
        return True
    if b.end is not None and a.begin is not None and b.end < a.begin:
        return True
    return False
```

Then **rewrite `temporal._numeric`'s overlap branch** (today two inlined
comparisons, `temporal.py:196-213`) so the **disjointness decision** is made by
`intervals_disjoint(ia, ib)`, and have `factual_anchor` call the *same* function for
its anachronism test.

**The predicate is the single source of the _decision_, not of message formatting.**
`temporal`'s overlap branch emits **two byte-distinct messages** depending on *which
direction* is disjoint (`ia.end < ib.begin` → "(ends X) and (begins Y)" vs.
`ib.end < ia.begin` → "(begins X) and (ends Y)"), while `intervals_disjoint` collapses
to one bool. FR-011 asks for one source of truth for **"do these two intervals
contradict"** — that is the bool, and after the refactor it lives in exactly one place.
Message wording may still re-inspect the bounds to pick the right phrasing; that is
*formatting*, not a second contradiction check, so it does not violate FR-011. The
rewire therefore keeps the two directional comparisons **only** to select the message,
guarded by the shared predicate, and `tests/validation/test_temporal.py` must stay
green byte-for-byte (the behaviour-preservation proof). Do **not** collapse the two
messages into one — that would change observable output and break the oracle.

**Rationale.** FR-011 demands exactly one place that decides interval
contradiction. The `temporal` validator already encodes "disjoint year ranges" in
its overlap branch; lifting it out is honest reuse, not new code. The existing
`tests/validation/test_temporal.py` (including `test_open_interval_is_handled`)
pins the overlap-disjoint behaviour, so the extraction is provably
behaviour-preserving — the refactor is safe by construction. This is the
zero-debt move: after it, adding the anchor check does not fork interval reasoning.

**Why disjointness is the *complete* contradiction condition for an anchor.** The
spec (FR-010, Assumptions "Anachronism semantics") frames a hard anachronism as
"disjoint-range / inconsistent-ordering." Inconsistent-ordering only arises between
two events joined by a declared `TR:*` order relation (`follows`/`precedes`). An
anchor and the event it constrains carry **no** such order relation — the anchor
merely asserts "this fact holds during `[begin, end]`," so the only way the event
can contradict it is by sitting in a year range provably disjoint from the span.
Extracting *only* `intervals_disjoint` (not the whole `_numeric` contradiction
suite) is therefore the right granularity: it shares everything the anchor needs
and nothing it does not (YAGNI / Constitution scope discipline).

**Alternatives rejected.**
- *Re-implement a disjoint check inside `factual_anchor`* — the literal FR-011
  violation; creates two sources of truth that can drift.
- *Extract the entire `_numeric` rule set into a reusable engine* — speculative
  generality; the anchor uses only one of its four comparisons, and the others
  (ordering, containment) have no anchor analogue. Rejected per scope discipline.

---

## D2 — Reading the anchor time-span (a different graph shape, the same model)

**Decision.** Read each anchor's optional time-span with a dedicated SPARQL
projection that targets the **anchor serialization shape** — `?anchor
crm:P4_has_time-span ?ts . ?ts crm:P82a_begin_of_the_begin ?begin .
?ts crm:P82b_end_of_the_end ?end .` (see `provenance.py:185-197`) — and load the
result into the **same `EventInterval` dataclass** the temporal validator uses.
Year literals are parsed by the shared `parse_gyear` helper (today `_parse_year`
in `queries.py`, promoted to a public, exported name so both loaders share one
parser, including BCE / `-0044` and zero-padded forms).

**Rationale.** An event's interval lives on a DOLCE boundary/`Dimension` shape
(`load_intervals`, reached via `(csm:duration|tr:temporal-location)/...`), whereas
an **anchor's** time-span is a plain `crm:E52_Time-Span` with `P82a`/`P82b` — two
genuinely different serializations. The *model* and the *reasoning* are shared
(`EventInterval`, `parse_gyear`, `intervals_disjoint`); only the read query differs.
This honours FR-011 ("reuse the interval model and contradiction logic") without
pretending the two serializations are identical.

**Alternatives rejected.** Forcing the anchor span through `load_intervals` — it
queries the event boundary shape and a G5 type, which the anchor span does not have;
it would silently return nothing. A second `EventInterval`-like dataclass — needless
duplication of a 3-field shape.

---

## D3 — The constrained target's interval (event / timeline / non-temporal)

**Decision.** Resolve `bw:constrains` to one of three cases and produce a
comparison interval accordingly:
1. **A `G5_Narrative_Event`** → its `EventInterval` from `load_intervals`. An event
   that carries **no** year boundary is absent from the `load_intervals` map; the rule
   treats that as **no comparable interval** → emits nothing (same outcome as a
   non-temporal target — no false positive, FR-012).
2. **The well-known timeline IRI** (`timeline_uri(uri_base)`, `namespaces.py:275`)
   → the timeline's overall bounds, a new `load_timeline_bounds(indexer)` returning
   `EventInterval(min(all begins), max(all ends))` over every event (edge case
   "Anchor constraining the timeline as a whole").
3. **Any other present entity** (character, setting, …) → **no comparable
   interval** → the anachronism rule produces nothing (FR-012, no false positives).

The anachronism error fires only in cases 1/2, only when the anchor carries a
time-span, and only when `intervals_disjoint(anchor_span, target_interval)` is true.

**Rationale.** Directly implements FR-010/FR-012 and the two timeline edge cases by
reusing `load_intervals` and the shared predicate. `load_timeline_bounds` is itself
a thin reduction over `load_intervals`, so it adds no new interval reasoning.

**Alternatives rejected.** Treating the timeline as a magic event — it is untyped
by design (research D10 of iteration 012); computing bounds from the event set is
the documented contract.

---

## D4 — Missing-entity detection (FR-009), incl. the dropped-constraint case

**Decision.** For each anchor, two existence checks, both at **warning**:
- **Promoted finding** — `bw:promotes` always names a URI; warn if that URI is
  absent from the graph (no triples describe it). Defense-in-depth for a
  hand-edited graph.
- **Constrained entity** — warn when *either* the anchor emits **no**
  `bw:constrains` triple at all (the iteration-12 reader dropped the link because the
  bible target did not resolve — `provenance.py:188`, Assumptions "Unresolved
  constraints") *or* it names a URI that resolves to no present entity. The
  well-known timeline IRI counts as present (it is a legitimate target though
  untyped).

"Present" = the URI appears as the subject of at least one triple, established by an
`ASK { <uri> ?p ?o }`-style projection through the indexer seam.

**Rationale.** Both sub-cases are the same author-facing defect ("constrains a
missing narrative entity", US1 scenario 4) and collapse to one warning kind. Using
"has any describing triple" as the presence test is engine-agnostic and matches how
the reader's drop manifests (an anchor with no `bw:constrains` triple).

**Alternatives rejected.** Requiring a specific `rdf:type` — sources are
deliberately untyped (`crm:E55_Type`, not `rdf:type`), and the timeline IRI is
untyped, so a type test would misfire. Presence-by-any-triple is correct and
uniform.

---

## D5 — Source provenance-completeness facets (FR-007)

**Decision.** For every source backing the anchor's promoted finding (reached
`anchor —bw:promotes→ finding —bw:supportedBy→ source`), check the presence of each
mandatory facet **predicate** in the graph and emit **one warning per missing
facet** (FR-007, clarified): `bw:reference`, `bw:author`, `bw:originalLanguage`,
`crm:P2_has_type` (source type), `bw:reliability`, `bw:reliabilityJustification`,
`bw:accessDate`, `bw:originalQuote`, and `bw:translation` **only when** the source's
`bw:originalLanguage` differs from the book language (`manifest.book.language`).
Each warning names the specific facet and the offending source.

**Single source of truth.** The one authoritative definition of "which predicates a
well-formed `Source` carries" is **`provenance.Source.to_triples()`**
(`provenance.py:109-120`): a fully-populated `Source` (translation included) emits
*exactly* these nine predicates and no others. The validator's mandatory-facet tuple
therefore reuses the **predicate constants from `golem.namespaces`** (`BW_REFERENCE`,
`BW_AUTHOR`, `BW_ORIGINAL_LANGUAGE`, `HAS_TYPE`, `BW_RELIABILITY`,
`BW_RELIABILITY_JUSTIFICATION`, `BW_ACCESS_DATE`, `BW_ORIGINAL_QUOTE`,
`BW_TRANSLATION`) — the single source of the IRIs — and a **drift-guard unit test**
asserts that this tuple's predicate set equals the predicate set emitted by a
fully-populated `Source.to_triples()`. If iteration-12 ever adds or renames a Source
facet, that test fails and forces the tuple to follow — no silent divergence.

> **Not aligned with `io/research._SOURCE_FACETS`.** That tuple is a list of *Pydantic
> field names* (it includes `"name"`, which is a label with **no** graph predicate, and
> it **omits** `translation`, which the reader governs by the language rule). It is a
> different representation with different membership, so it is deliberately **not** a
> co-source here; treating it as one would be the drift it looks like it prevents. The
> graph-predicate membership comes from `Source.to_triples()` alone.

The translation conditionality reproduces the reader's D6 rule (translation expected
iff languages differ — edge case "Source language equals the book language").
One-warning-per-facet matches FR-007's singular wording and keeps each gap
independently fixable/testable. This check is **defense-in-depth**: the build-time
reader normally rejects incomplete sources, but a hand-edited or older graph can
still carry one (edge case, Assumptions).

**Alternatives rejected.**
- *One aggregate warning per incomplete source* — rejected by the clarification (extra
  coupling, harder to fix incrementally).
- *Sourcing the facet membership from `io/research._SOURCE_FACETS`* — wrong
  representation (field names, not predicates) and wrong membership (`name` in,
  `translation` out); it cannot be the single source for a graph-predicate check.

---

## D6 — Best-reliability threshold (FR-008) and the no-double-label rule

**Decision.** Order reliability `baja < media < alta` via a rank map derived by
inverting `namespaces.RELIABILITY_IRI` (single source of the vocabulary). For an
anchor, compute the **maximum** rank among supporting sources that **carry** a
`bw:reliability` value; compare to the rank of
`manifest.research.min_reliability_for_anchor` (default `"media"`). Warn when the
best is strictly below the threshold. A source with **no** `bw:reliability`
contributes nothing to this max (its missing rating is reported once under FR-007,
never additionally as "under-reliable" — the clarification's no-double-label rule).
When **no** supporting source carries any rating, the best is treated as below every
threshold and the anchor is flagged once.

**Rationale.** Implements FR-008 and the second clarification exactly. Reading the
ordering from `RELIABILITY_IRI` keeps the scale single-sourced with the ontology
vocabulary, the same anti-drift discipline the `[research]` block uses (RB-8).

**Alternatives rejected.** Treating an unrated source as `baja` — would double-label
it as both incomplete (FR-007) *and* under-reliable (FR-008), which the
clarification explicitly forbids.

---

## D7 — Violation `source` locations (FR-013): present when the graph records one

**Decision.** Populate each `Violation.source` via the existing
`resolve_source(indexer, uri)` helper (`queries.py:129`) on the anchor (and fall
back to the source/finding URI where more apt). When the graph records no
`E13 → P16_used_specific_object` locator for the subject — which is the current
state for anchors, since iteration-12 anchor serialization emits no provenance
locator — `source` is `None` (location-less). The `triples` payload always carries
the implicated `(s, p, o)` edges.

**Rationale.** FR-013 makes the location a **SHOULD** that **MAY** be absent "as the
temporal validator already is for some findings." Reusing `resolve_source` means
locations appear automatically if/when iteration-12 provenance gains anchor
locators, with **no** change here, and never fabricates a path the graph does not
record. Adding provenance emission to anchors is iteration-012 territory and is out
of scope (no scope creep).

**Alternatives rejected.** Re-parsing `bible/research/*.md` to recover line numbers
— the validator is a pure graph consumer (FR-003, Assumptions "Reasoning surface");
re-reading files would break that contract and duplicate the reader.

---

## D8 — Inert preconditions: no-research and `[research].enabled = false`

**Decision.** Two early exits returning `[]`:
- `manifest.research.enabled` is `False` → emit nothing (FR-015), even if anchors
  exist in the graph.
- The graph contains **no** anchors → emit nothing (FR-016), covering the
  no-`bible/research/` project and a research project with no promoted anchors.

Both are read through the `ValidationContext` (`project.manifest.research`) and the
indexer — no new context field needed; the manifest is already on the context.

**Rationale.** Directly satisfies US3 and FR-015/FR-016. Being a built-in that
no-ops on irrelevant projects is the "you pay only if you use it" property the scope
discipline requires; the registry runs it by default, and `[validators].disabled`
turns it off via the existing mechanism (no special-casing).

**Alternatives rejected.** Gating discovery on the presence of `bible/research/` —
would fork the discovery mechanism (FR-004 forbids a new one); a cheap in-`validate`
anchor count is simpler and correct.

---

## D9 — Where the new code lives (Principle IV, testability)

**Decision.**
- `queries.py` gains `intervals_disjoint`, `load_timeline_bounds`, and the exported
  `parse_gyear` (its docstring widens from "for the `temporal` validator" to "for
  the `temporal` and `factual_anchor` validators"). It stays well under 500 lines.
- A new `anchor_queries.py` holds the anchor-specific projections (`AnchorRecord`,
  `load_anchors`, source-facet + reliability reads) — anchor structure is a distinct
  concern from interval reasoning, so it does not bloat `queries.py`.
- `validators/factual_anchor.py` holds the `FactualAnchor` class and its rule
  methods, reasoning over the in-memory shapes — no rdflib in the validator body,
  mirroring how `temporal` is structured.

**Rationale.** Keeps each file single-concern and small (Principle IV), keeps SPARQL
out of the reasoning code (the pattern the four shipped validators follow), and
makes every rule unit-testable against hand-built graphs.

**Alternatives rejected.** Folding all anchor SPARQL into `queries.py` — mixes
"interval projections" with "anchor structure," muddying the module and pushing it
toward the size ceiling. One mega-validator file with inline SPARQL — harder to
test, against the established pattern.
