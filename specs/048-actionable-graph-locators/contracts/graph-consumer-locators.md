# Contract — Graph-consumer validator locators & identifiers

The locator/identifier contract `temporal` and `factual_anchor` honor after
iteration 048. The `--json` `Violation` **shape** is unchanged (Principle IX); this
contract pins the **values** of `source` and the message identifier. The CI gate
(exit 1 on any unfiltered `error`) and exit codes are untouched (FR-005).

## C1 — `Violation.source` is resolvable for every graph-consumer finding

For both validators, every emitted `Violation` carries a `source` that resolves to
a real project file (never `null`), **except** the FR-010 defensive floor (C4).

- **`temporal` (all four rules a/b/c/d)**: `source` resolves to the
  `bible/timeline.md` file as a line-bearing `bible/timeline.md:<line>` locator
  (`resolve_source` prefers a `:line`-bearing provenance). Pre-048, only rule (d)
  did this; a/b/c emitted `null`. (FR-001, SC-002)
- **`factual_anchor` (every violation)**: `source` is the anchor's authoring file
  `bible/research/<topic>.md` (file-only — `AnchorIdentity` carries no line, by
  design, matching `status`). Pre-048 it was always `null`. (FR-003, SC-001)

The two granularities (`:line` for events, file-only for anchors) differ **by
design**, not by defect (spec Key Entities): an event's `E13` records a line; an
anchor is resolved via its `AnchorIdentity.relpath`, which is file-only.

## C2 — Message identifiers are human-readable, never a raw uuid7 (FR-004, SC-004)

- **`factual_anchor`**: the anchor is named by its authored handle —
  `<promotes-finding-id>`, plus ` -> <constrains-target>` when the anchor declares a
  target, omitted when it does not. Identical to what `status` renders for the same
  anchor (C3). The promoted *source* entity in an R2 message keeps its stable slug
  label (it was never a uuid7).
- **`temporal`**: event names continue to use `_label(event.uri)` — a stable slug
  segment (events are `SluggedEntity`), already human-readable; no change needed.

No normal-path message names an anchor or event by a raw uuid7 URI tail. The **sole**
exception is C4.

## C3 — `factual_anchor` and `status` agree, through one code path (FR-007, FR-009, SC-003)

The handle is produced by a **single** shared function,
`anchor_handle(promotes, constrains)` (`io/_research_identity.py`), called by both
`status._anchor_line` and `factual_anchor`. For the same anchor, the two surfaces
emit a **byte-identical** handle and the **same** file. A test asserts the
agreement; the two cannot drift.

## C4 — FR-010 defensive floor (the only place a uuid7 may surface)

If a defective anchor's authored identity is **absent** from the corpus mapping (a
join miss — e.g. a hand-built graph without identities, or a future divergence), the
violation is **still emitted** (the validator is a CI gate and MUST NOT drop a
defective-anchor finding), with the pre-048 spelling: identifier =
`_label(anchor.uri)` (uuid7 tail), `source = None`. This is the no-regression floor,
not the normal path; for a freshly built corpus every anchor has an identity (C2/C3
hold universally). (FR-010)

## C5 — Determinism (FR-002, FR-016)

- `temporal` resolves `source` from a fixed, total event choice: the carried
  triple's subject (rules b/c/d) or the lexicographically smallest event URI in the
  SCC (rule a). Two builds of the same fixture emit byte-identical `source`.
- `factual_anchor` `source`/`message` derive from stable authored data
  (`relpath`/handle); two builds are byte-identical on those fields. (`triples`
  retain the minted anchor URI — pre-existing, unchanged.)

## C6 — No semantic / dependency / ontology change (FR-005, FR-006, FR-008)

Same `error`/`warning` findings, same count, same severities, same gate and exit
code on every fixture (only `source` and the message identifier differ). No new
runtime dependency; `resolve_source` reused as-is. The frozen GOLEM ontology is
untouched — no new class, predicate, or `.ttl` change; the in-process corpus build
emits the same triples `graph build` already emits and persists nothing.
