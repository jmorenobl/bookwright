# Phase 0 Research — Actionable locators for graph-consumer validators

Iteration 048 · DEBT-015 · issue #1 track B (pulido determinista). Design § 13.2 /
§ 20.6. No `NEEDS CLARIFICATION` remained after the spec's Session 2026-06-24
clarifications; the open *mechanism* choice ("decidir en /speckit-plan") is settled
in **D1** below.

---

## D1 — How `factual_anchor` obtains a join that resolves the anchor's file + handle

**Decision.** `factual_anchor` resolves the anchor sub-graph from an
**in-process-built research corpus** — a memoized, **non-persisting**
`ValidationContext.anchor_corpus()` accessor that returns
`(engine, anchor_identities)` from one `map_research` pass — and joins each anchor
to its `AnchorIdentity` **by URI within that single build**. This mirrors `status`
exactly. The readable handle and file are then resolved through a single shared
helper (`anchor_handle`, D2). FR-010's join-miss becomes a defensive floor.

**Why the spec's literal mechanism cannot work (the load-bearing finding).** The
spec says (FR-003/FR-007/Assumption) to join the authored identities to the graph
anchors *by URI*, "the same path `status` uses." Verified against the code, that
does not survive the `graph build` → `validate` **process boundary**:

1. `Anchor` and `Finding` are `MintedEntity`
   (`golem/base.py`: `_token = str(uuid_utils.uuid7())`) → their URIs are
   **re-minted on every build**, non-deterministic across processes. Only
   `Source`, `NarrativeEvent`, and bible entities are `SluggedEntity` (stable).
2. `validate` (`commands/validate.py:_load_indexer`) reads the **persisted**
   `bible/graph.ttl`, built by a *prior, separate* `graph build` process. Its
   anchors carry uuid7s from that build.
3. A fresh `map_research` inside the validator mints **different** uuid7s. A
   URI-keyed join (`{identity.uri: identity}`) therefore misses for **every**
   anchor — not just the FR-010 "source since removed" case.
4. `status` (`commands/status.py:_aggregate`) avoids this only because it calls
   `build_project_graph` and joins `anchor_gaps` over the **same in-process**
   engine + identities, where the uuid7s match. It never reads the persisted graph.

The graph itself carries **no** stable anchor handle: `Finding.to_triples` /
`Anchor.to_triples` emit no authored `id`, and `build_provenance` deliberately
**skips** research entities ("already E13 reifications" — `commands/_graph.py`), so
no `E13` points *to* an anchor and `resolve_source(anchor.uri)` is `None`.

**Therefore** the only faithful realization of "the same machinery `status` uses"
is to do what `status` does: build the corpus **in-process** so engine and
identities share one build. This honors FR-003 (file via `identity.relpath`, *not*
`resolve_source(anchor.uri)`), FR-004/FR-007/FR-009 (handle = `status`'s, byte-
identical, shared point), and FR-006/FR-008 (no new dependency, no ontology change).

**Alternatives considered and rejected.**

- **(A) URI-join against the disk graph — the spec's literal text.** Resolves
  nothing (every anchor misses). Rejected: it would ship a no-op dressed as a fix.
- **(B) Graph-emission "root fix": emit an `E13` provenance edge for each anchor
  (so `resolve_source(anchor.uri)` returns the file) + the finding's authored `id`
  as a label (for the handle).** Cleanest *long-term* (anchors gain real
  provenance like every other entity, uniform `resolve_source`, benefits `status`
  too, validator stays a pure consumer of the passed graph, no rebuild). Rejected
  **for this iteration**: it directly contradicts FR-003 ("**not** by
  `resolve_source(anchor.uri)`") and the spec's Key-Entities premise ("an anchor
  *is* the reified `E13` — no `E13` edge points *to* it"), and it changes build
  output. Reversing those load-bearing premises is a spec rewrite, not a plan
  decision. Recorded here as the natural follow-up if the owner later prefers the
  root fix (it would supersede D1's in-process build).
- **(C) Stable-signature join** (re-key identities by constrains-target slug +
  supporting-source slugs + span, all graph-survivable). Rejected: signature
  uniqueness is **not** guaranteed (two anchors with the same target/sources/span
  collide), and `promotes_id` — the spec's chosen handle — is not in the graph at
  all. Fragile = real debt, against the zero-debt bar.

**FR-010 reconciliation (documented, minor).** The spec's clarification frames the
join-miss as "a stale derived graph still carrying an anchor whose `bible/research/`
source was since removed." Under D1 (in-process build from *current* source) that
exact phantom-anchor scenario cannot arise — a removed source simply yields no such
anchor. The FR-010 fallback (`identifier = _label(anchor.uri)` uuid7 tail,
`source = None`) is retained as a **defensive floor** for any anchor whose identity
is absent from the corpus mapping (e.g. a hand-built test graph without identities,
or a future divergence), so a defective-anchor finding is never dropped — exactly
the no-regression guarantee FR-010 asks for. A one-line note is added to the spec's
FR-010 / clarification recording this (the fallback is defensive, not the normal
path). SC-004's "no uuid7" guarantee holds for every anchor with an available
identity — the universal case for a freshly built corpus.

**Determinism.** The corpus build is deterministic except for the uuid7 URIs, which
are used **only** as the in-build join key and never surface: the resolved `source`
is `identity.relpath` (stable authored data) and the message identifier is the
`anchor_handle` (stable authored data). The `Violation.triples` field still carries
the anchor's uuid7 URI — **pre-existing** and out of scope (today's findings already
embed minted URIs in `triples`; `status` excludes violation *messages* for exactly
this reason). Two-build byte-stability is therefore asserted on the **`source` and
`message`** fields, which become stable; `triples` are unchanged by this iteration.

---

## D2 — The single shared resolution point for the anchor handle (FR-007/FR-009)

**Decision.** Extract the handle spelling `status` already renders into one free
function in the lowest layer that owns `AnchorIdentity`:

```python
# io/_research_identity.py
def anchor_handle(promotes: str, constrains: str | None) -> str:
    """The author-facing handle for an anchor: the promoted finding id, plus
    ``-> <constrains>`` when the anchor declares a target (else the id alone)."""
    target = f" -> {constrains}" if constrains is not None else ""
    return f"{promotes}{target}"
```

Both surfaces call it:

- `commands/status.py:_anchor_line` →
  `f"{anchor_handle(gap.promotes, gap.constrains)}: {', '.join(gap.problems)} ({gap.file})"`
  (byte-identical output to today — pure extraction).
- `factual_anchor` → `anchor_handle(identity.promotes_id, identity.constrains)`.

**Rationale.** FR-007 requires "one code path" so the two surfaces cannot diverge,
and FR-009 requires the handles be byte-identical for the same anchor. A free
function on `(promotes, constrains)` is the single spelling both `AnchorGap`
(status) and `AnchorIdentity` (validator) feed, since both carry exactly those two
fields. Placing it in `io/_research_identity.py` keeps the layer direction clean
(`io` is below both `commands` and `validation`) and co-locates it with
`AnchorIdentity`, matching how `is_timeline_ref` already lives there.

**Alternatives considered.** A method/property on `AnchorIdentity` (`.handle`) —
rejected because `status._anchor_line` operates on `AnchorGap`, not
`AnchorIdentity`; a free function over the `(promotes, constrains)` pair is the
common denominator of both. A new module — rejected as overkill for one function.

---

## D3 — `temporal` rules a/b/c: deterministic implicated-event resolution (FR-001/FR-002)

**Decision.** Rules (a)/(b)/(c) adopt rule (d)'s existing
`source = resolve_source(indexer, <event uri>)` over the **passed** indexer (no
rebuild — events are `SluggedEntity` with `E13` provenance already in the disk
graph, which is why rule (d) already resolves). The implicated event is chosen by a
fixed total rule for byte-stability:

- **Rule (b) order-vs-overlap** and **(c) containment-vs-order** each carry a
  single implicated triple `(a, pred, b)`; resolve from its **subject `a`** —
  mirroring rule (d), which resolves from the relation subject `a`.
- **Rule (a) cycle** spans a strongly-connected component with no single subject;
  resolve from the **lexicographically smallest event URI in the component**
  (the component is already sorted; take `component[0]`).

**Rationale.** FR-002 demands a fixed, total choice so repeated builds emit
byte-identical `source`. Event URIs are stable slugs, so the lexicographic min /
triple-subject are deterministic and reproducible. All four rules end uniform in how
they populate `source` (FR-001). `resolve_source` is reused unchanged, preserving
its `:line`-preferring, then-lexicographically-smallest tie-break (FR-006); a/b/c
inherit the same `bible/timeline.md:<line>` granularity rule (d) produces.

**Alternatives considered.** Resolving from *all* implicated events and joining —
rejected: a single deterministic event already yields the correct file
(`bible/timeline.md`), and the spec's Assumption confirms the choice "affects only
determinism, not the resulting relpath." A new sort key — rejected (FR-016): the
existing component/triple ordering already gives a total order.

---

## D4 — Test strategy: an injection seam, not a harness rewrite (FR-012)

**Decision.** The `factual_anchor` unit harness (`tests/validation/conftest.py`)
hand-builds anchors into an engine with **stable** suffix URIs (`anchor/a1`) and no
identities. Rather than rewrite it to real `bible/research/` markdown, add a small
**corpus-injection seam** to `ValidationContext`: when an
`(engine, identities)` corpus is injected, `anchor_corpus()` returns it; otherwise
it builds fresh. Tests then build the existing `AnchorSpec` engine **plus** matching
`AnchorIdentity` records (same stable URIs) and inject both. The join succeeds on
the stable URIs, the existing fixtures keep their shape, and only the expected
`source` (`None` → relpath) and message (uuid7 → handle) change.

**Rationale.** Keeps the change to existing tests **mechanical** (add identities,
update two assertions per case) instead of a full rewrite, and gives the production
path (`anchor_corpus()` builds fresh) its own coverage via the E2E research workflow
(real `graph build` → `validate`, asserting a non-`null`
`bible/research/<topic>.md` source and a uuid7-free message). The cross-surface
agreement test (FR-009/SC-003) asserts `factual_anchor` and `status` name + locate
the same anchor identically.

**Oracles (empirical, `uv run pytest`).**
- `temporal`: a fixture triggering rules a/b/c each reports `source` resolving to
  `bible/timeline.md` (line-bearing, like rule d), not `null`; two builds of the
  same fixture emit byte-identical `source`.
- `factual_anchor`: a defective anchor reports `source == bible/research/<topic>.md`
  (not `null`) and a message citing the authored handle (`promotes -> constrains`,
  or `promotes` alone when no target), never the uuid7 tail.
- agreement: the same anchor's `factual_anchor` finding and `status` `anchor_gaps`
  entry carry the same handle + file.
- no-regression: SC-005 — finding count/severity/gate unchanged on every existing
  fixture (only `source`/`message` differ); FR-010 fallback path covered by an
  identity-less anchor still emitting its finding.

---

## D5 — Contract-before-code (design § 13.2 / § 20.6, DEBT.md, index)

**Decision.** Before the code diverges, reconcile the prose contracts:
- `bookwright-design.md` § 13.2 (`temporal`, `factual_anchor` rows) + § 20.6 — state
  that both graph-consumer validators now emit a resolvable `relpath[:line]` locator
  and a readable identifier, and record the D1 mechanism (in-process corpus,
  identity-resolved file, shared handle) and the file-vs-`:line` granularity that
  differs **by design** (event = `:line` via `E13`; anchor = file-only via
  `AnchorIdentity.relpath`).
- `DEBT.md` — **remove** DEBT-015 (its class is resolved); reconcile the track-B
  index line (`DEBT-015` → shipped iter 048) and the iteration table /milestone
  prose in `CLAUDE.md`.
- `spec.md` — add the one-line FR-010 note that the fallback is a defensive floor
  (D1 reconciliation), so the spec and code agree.

**Rationale.** The project's standing rule (CLAUDE.md, the zero-debt doctrine): the
plain-text contract is reconciled **before** the code, and a resolved debt class is
**removed** from `DEBT.md` (git keeps history). DEBT-017 (`narrative_structure`
name-vs-slug) stays open — it is iteration 049's scope (spec Out of Scope).
