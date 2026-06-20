# Research: Outline ingestion — narrative sequences (G7)

All `[NEEDS CLARIFICATION]` from the spec (FR-005 missing-`order`, FR-006
duplicate-`order`) were resolved in the spec's Clarifications (Session
2026-06-20) and are restated here as D2/D3. The remaining decisions are
implementation choices the spec's Assumptions left to `/speckit-plan`.

## D1 — Where sequence assembly lives: a second pass over collected members

**Decision**: Read `sequence`/`order` off each unit card **inside** the existing
iteration-028 `outline/units/` per-file pass (`_map_single_dir`), recording a
`(seq_slug, seq_name, order, unit_slug, unit, relpath)` member record into a
side-channel accumulator as the **last** step of the unit builder. After
`_map_single_dir` returns, run a single assembly step over the accumulated
records that groups by `seq_slug`, sorts each group, and appends one
`NarrativeSequence` `MappedEntity` per group.

**Rationale**: The spec mandates "el ensamblaje de secuencias es un segundo paso
sobre el conjunto de unidades ya construido, no por-fichero." A sequence spans
multiple cards, so it cannot be minted while visiting a single card. The two new
keys are **not** attributes of the `NarrativeUnit` entity (golem/ is untouched),
so they cannot be recovered from `result.mapped` after the pass — they must be
captured during it. Capturing the raw `(sequence, order, unit)` triple is not
"assembly"; the grouping/sorting/minting is, and it genuinely runs once, after
all cards are read. This matches the spec Assumption that "whether the assembly
is a second sweep over collected `(sequence, order, unit)` triples or an
accumulating index is an implementation choice."

**Accumulator location**: a plain `list` local to `map_outline`, captured by the
builder lambda's closure (the lambda already closes over `ctx` and `uri_base`;
the builder is invoked as `spec.builder(metadata, relpath)`). This keeps the
shared `_MapContext` dataclass in `_bible_builders.py` free of an
outline-only field.

**Alternatives considered**:
- *A new `_MapContext.sequence_members` field* (mirroring the 028
  `functions_index`): rejected — it leaks outline-specific state into the shared
  bible/outline context for no reuse benefit; the closure-local list is narrower.
- *A separate `outline/sequences/` directory of authored sequence cards*:
  rejected by the spec (Out of Scope) — sequences are assembled, not authored.

## D2 — Missing `order` ordering (FR-005, from Clarifications)

**Decision**: A member that declares `sequence` but omits `order` is placed
**last** within its sequence — after every member with an explicit `order` — and,
among the order-less members, ordered deterministically by the unit's slug.

**Rationale**: Restated from the spec's Clarifications. Mirrors the 028 mapper
ethos (optional keys degrade softly), keeps `order` genuinely optional, adds no
new fatal-error class.

## D3 — Duplicate `order` tie-break (FR-006, from Clarifications)

**Decision**: Two members of the same sequence sharing the same `order` are
tie-broken **deterministically by the unit slug**, never rejected.

**Rationale**: Restated from the spec's Clarifications. No filesystem/dict-order
dependence; satisfies the identical-member-tuple-across-builds requirement.

**Implementation (D2 + D3 as one total sort key)**: for member `m`,

```
key(m) = (0, m.order, m.unit_slug)   if m.order is not None
key(m) = (1, 0,        m.unit_slug)   if m.order is None
```

Python tuple ordering then sorts explicit-`order` members first (group flag `0`)
by `order` then slug, and order-less members last (group flag `1`) by slug. The
middle element is a fixed `int` in both branches so the keys are mutually
comparable under `mypy --strict`. The sort is a stable `sorted(...)`, but the
slug tie-break makes it a **total** order — stability is not relied on.

## D4 — Sequence identity, dedup, and the display name

**Decision**: Group members by `make_slug(sequence_name)`. Mint exactly one
`NarrativeSequence(uri_base=…, name=…, units=…)` per distinct slug (URI segment
`narrative-sequence/<slug>`, supplied by the existing model `path_segment`). The
constructor `name` is the **raw `sequence` value of the first card, in
sorted-glob order, to name that slug** — i.e. the `seq_name` of the first record
inserted into the group (dict insertion order is preserved because
`_map_single_dir` walks `sorted(glob("*.md"))`).

**Rationale**: Dedup-by-slug is FR-002. Because `SluggedEntity` derives identity
from `make_slug(name)`, any raw casing/spacing variant that slugs to the same
token yields the same URI regardless of which raw name is chosen — so the choice
only affects the stored display `name`, and "first card in sorted-glob order"
makes it deterministic. This mirrors `_mint_functions`, where the first card to
introduce a function slug supplies its name.

## D5 — Provenance for the sequence and its proper-part edges (FR-010)

**Decision**: Append the `NarrativeSequence` as a `MappedEntity` with
`key_lines={}` and `relpath` = the relpath of the **first member in assembled
(ordered) order**. This yields **file-level** provenance (a `relpath`, no `:line`)
for the identity assertion and for each `dlp:proper-part` edge.

**Rationale**: `build_provenance` resolves a derived assertion's `source_field`
to a `relpath:line` only when `key_lines` holds that field; with `key_lines={}`
it falls back to file-level `relpath`. The `NarrativeSequence` model emits one
`DerivedAssertion` per member, all tagged `source_field="units"`; since the
members originate in *different* cards, no single `:line` could honestly locate
all of them. File-level provenance is exactly how iteration 028's
**minted `NarrativeFunction`** entities are recorded (`key_lines={}`,
`relpath` = the first introducing card), so this reuses an established precedent
"where locatable" (FR-010) rather than inventing per-edge line resolution — which
would require touching the frozen model and is out of scope. Choosing the first
*assembled* member's relpath (the opening beat of the sequence) is deterministic
and is the most natural single citation for the sequence as a whole.

**Alternative considered**: populate `key_lines={"units": <line>}` from one
card's `sequence:` line — rejected: it would attach a single card's line to
*every* member edge, which is misleading, and it is not what the minted-function
precedent does.

## D6 — The `order` coercer: local to `outline.py`, not a shared refactor

**Decision**: Add a small `_coerce_order(value) -> int | None` in `io/outline.py`
that returns `None` for absent, raises `InvalidFrontmatterError` for a non-int
(and, like `_coerce_year`, rejects `bool` as a non-integer), else returns the
int. Do **not** refactor the structurally-identical `_coerce_year` in
`_bible_builders.py`.

**Rationale**: `order` is "optional int, reject bool" — the same shape as
`_coerce_year` — but extracting a shared `_coerce_optional_int` would touch the
well-tested year path and broaden the diff for a 4-line saving. Scope discipline
favours a localized coercer; the duplication is trivial and not debt-worthy.
`_coerce_sequence(value) -> str | None` likewise lives in `outline.py`, mirroring
`_resolve_setting`'s contract: `None`/blank/whitespace → absent (no membership),
non-string → `InvalidFrontmatterError` (card skipped).

## D7 — The skip-invariant ordering inside `_build_unit`

**Decision**: Perform **all** raising operations — `_require_name`,
`make_slug(name)`, `_coerce_str_list` for `functions`/`roles`, `_coerce_sequence`,
`_coerce_order` — **before** any state mutation (minting functions, resolving
roles, recording sequence membership, or recording the lone-`order` soft note).

**Rationale**: Preserves the 028 invariant (research D3 of that iteration): a card
with unusable front-matter contributes nothing but its `skipped` entry. Because
`_coerce_sequence`/`_coerce_order` can raise (FR-007), they must sit in the
up-front validation block so a non-string `sequence` or non-int `order` skips the
card cleanly with no partial sequence membership and no stray soft note. The
member record is appended **last**, after the `NarrativeUnit` is constructed, so
a unit that survives into `result.mapped` is exactly the set whose membership is
recorded (a later `SlugCollisionError` from `_map_single_dir` aborts the whole
build, so intra-result consistency is moot in that path).

## D8 — `order` without `sequence` is a soft note (FR-008)

**Decision**: When `order` is present and usable but `sequence` is absent/blank,
ignore the `order`, record the unit in no sequence, and append a soft
`UnknownKey(path=relpath, key="order")`.

**Rationale**: Mirrors `_resolve_interval`'s handling of a redundant `date`
(`unknown_keys.append(UnknownKey(..., key="date"))`) — a lone positional key with
nothing to position is a soft authoring nicety, never a fatal error.

## D9 — Backward compatibility / determinism (FR-011, SC-006, SC-004)

**Decision**: A project whose cards declare no `sequence` collects zero member
records, assembles zero `NarrativeSequence` entities, and appends nothing to
`result.mapped` — a byte-for-byte-identical graph. Adding `sequence`/`order` to
`UNIT_KEYS` does not change any existing fixture (none carries those keys, so no
new `unknown_keys` warning appears or disappears). Determinism follows from
sorted-glob iteration (D1), the total sort key (D2/D3), and insertion-ordered
grouping (D4) — no filesystem/dict-order dependence anywhere.

## D10 — Parity registry & test edits (FR-013), confirmed no drift-probe change

**Decision**: Remove the `NarrativeSequence` entry from `DEFERRED_CONCEPTS`; move
`"NarrativeUnit"`-style liveness for G7 into the reachable set. Concretely:
`deferrals.py` docstring prose "Three of the thirteen" → "Two of the thirteen"
and "Exactly three entries" → "Exactly two entries"; in the parity test,
`EXPECTED_REACHABLE` gains `"NarrativeSequence"`, `ORPHAN_NAMES` loses it,
`EXPECTED_VERSIONS` drops its key, `len(DEFERRED_CONCEPTS) == 3` → `== 2`, and the
docstring "Ten of the thirteen … the other three" → "Eleven of the thirteen …
the other two". The three drift-simulation probes (`Character`, `NarrativeEvent`,
`PsychologicalState`) name **no** now-fed concept, so they keep passing
unchanged — confirmed by inspection, not edited (FR-013).

**Rationale**: Single-sourced counts must move in lockstep or the parity test
contradicts itself; the spec enumerates every count-bearing site. The probes were
deliberately chosen by 028 to survive a G9/G10 (and now G7) flip.

## D11 — Fixture card for live G7 (FR-014)

**Decision**: Give the `parity-exercise` fixture's `outline/units/` at least one
card declaring `sequence` (and `order`) — simplest: add `sequence`/`order` to the
existing `opening.md` and add one more card sharing the same `sequence` with a
later `order`, so the live build emits a `NarrativeSequence` `rdf:type` IRI with
two ordered members. The parity test reads reachability from this real build, so
G7 only counts as fed because the engine actually produced it.

**Rationale**: FR-014 / FR-003 — reachability is observed, never hand-listed.
Two members (not one) also lets the parity fixture double as a light smoke of the
ordering, though the rigorous ordering coverage lives in
`tests/io/test_outline_sequences.py`.
