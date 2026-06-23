# Feature Specification: Actionable locators for graph-consumer validators

**Feature Branch**: `048-actionable-graph-locators`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Los validadores graph-consumer (`factual_anchor`, `temporal`) emiten locators inaccionables, a diferencia de los de prosa (`character_presence`, `narrative_structure`, `focalization`), que siempre dan `relpath:línea`. (1) `factual_anchor` identifica cada anchor en el MENSAJE por su URI uuid7 opaco y emite `source: null` (un anchor no tiene arista E13 que apunte a él, así que `resolve_source(anchor.uri)` da `None`); mientras `bookwright status` reporta EL MISMO anchor de forma legible (`promotes`/`constrains`/`file`). (2) `temporal` es inconsistente consigo mismo: la regla (d) numérica resuelve `source` vía `resolve_source`, pero las reglas (a) ciclo, (b) orden-vs-solape y (c) contención-vs-orden emiten `source=None`, aunque todos los eventos viven en `bible/timeline.md` y `resolve_source` sobre la URI del evento sí resuelve. Esta iteración hace que ambos den un locator `relpath:línea` resoluble y un identificador legible, reusando la procedencia `file:line` que el grafo ya lleva reificada en los E13. NADA semántico; severidades y gate sin cambios. DEBT-015."

## Context

This is iteration 048 (patch track v0.5.x, issue #1 **track B — pulido
determinista**, the deterministic-polish sibling of the honesty track). It
resolves **DEBT-015**.

Bookwright's validators split into two families by how they read the project.
The **prose** validators (`character_presence`, `narrative_structure`,
`focalization`) read manuscript/outline text and always emit a `relpath:line`
locator and a human-readable identifier — an author can jump straight to the
offending line. The **graph-consumer** validators (`factual_anchor`, `temporal`)
read the derived graph by SPARQL and, today, emit locators that are absent or
inconsistent and identifiers that are opaque. Two concrete defects (DEBT-015):

1. **`factual_anchor` is unactionable.** Every violation it raises passes through
   a helper that sets `source = resolve_source(indexer, anchor.uri)`. But an
   anchor **is** the reified `E13_Attribute_Assignment` — no E13 edge points *to*
   it — so `resolve_source` returns `None` for every anchor. The message then
   names the anchor by `_label(anchor.uri)`, i.e. its opaque uuid7 tail. The
   author sees `anchor '019ef2c4-bc50-7b81-…' is backed only by sources below the
   minimum reliability 'media'` with `source: null` — no file, no readable name.
   Meanwhile `bookwright status` reports **the same anchor** legibly: its
   `anchor_gaps` projection joins each graph anchor record back to its
   `AnchorIdentity` (authored finding id it `promotes`, authored `constrains`
   target, and the `relpath` of `bible/research/<topic>.md`). The data exists and
   is resolvable; `factual_anchor` simply does not use that path.

2. **`temporal` is inconsistent with itself.** Its four contradiction rules emit
   the same kind of `error`, but only rule **(d)** (numeric begin/end) attaches
   `source = resolve_source(indexer, <event uri>)`. Rules **(a)** cycle, **(b)**
   order-vs-overlap and **(c)** containment-vs-order emit `source = None` —
   although every event lives in `bible/timeline.md` and `resolve_source` over an
   event URI resolves it (rule (d) proves it). Three of four rules drop a locator
   that is one call away.

The graph already carries `file:line` provenance reified in its `E13`
assignments, and `status` already demonstrates the readable anchor handle. This
iteration closes the actionability gap **without touching what the rules detect**:
both validators emit a resolvable `relpath:line` locator and a readable
identifier, reusing provenance and identity machinery the codebase already has.
Nothing semantic changes; severities and the exit-code gate are untouched.

## Clarifications

### Session 2026-06-24

- Q: In the `factual_anchor` message, by which authored handle should the anchor
  be named — the `promotes` finding id only, the `constrains` target only, or
  both? → A: Mirror exactly what `status` already renders for the same anchor
  (`AnchorGap`/`_anchor_line`): the promoted finding id, plus `-> <constrains
  target>` when the anchor declares one, omitted when it does not. Reusing
  `status`'s identity format (ideally a single shared resolution point) is the
  lowest-debt choice and guarantees the two surfaces never diverge in how they
  name the same anchor (FR-003/FR-009).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A defective research anchor points to its file and authored name (Priority: P1)

An author runs `bookwright validate` (or `validate --json`) on a research
project that contains a defective anchor — say, one promoting the finding
`paginas-arrancadas`, constraining `El cuaderno de bitácora`, backed only by
under-reliable sources, authored in `bible/research/puerto.md`. Today the
`factual_anchor` finding reads `anchor '019ef2c4-bc50-…' is backed only by
sources below the minimum reliability 'media'` with `source: null` — the author
cannot tell which file or which anchor it means. After this change, the finding
resolves `source` to `bible/research/puerto.md` and names the anchor by its
authored handle (`paginas-arrancadas -> El cuaderno de bitácora`), so the author
can open the file and fix the very anchor `status` already named.

**Why this priority**: This is the core unactionability defect — a `null`
locator plus an opaque uuid7 is the worst case, and it is what made DEBT-015
worth its own iteration. It is the larger half of the change.

**Independent Test**: Build a fixture project with one under-reliable / unsourced
anchor and assert that the `factual_anchor` violation carries
`source == "bible/research/<topic>.md"` (not `null`) and a message that cites the
authored handle (the `promotes` finding id, and the `constrains` target when
present) rather than the uuid7 tail. Cross-check that `status` and
`factual_anchor` agree on how that same anchor is named and located.

**Acceptance Scenarios**:

1. **Given** a research project with an anchor that is backed only by
   sources below `min_reliability_for_anchor`, **When** the author runs
   `bookwright validate --json`, **Then** the corresponding `factual_anchor`
   finding's `source` is the anchor's `bible/research/<topic>.md` relpath (not
   `null`) and its message identifies the anchor by its authored finding/target
   handle (not the uuid7 URI tail).
2. **Given** that same anchor, **When** the author compares the
   `factual_anchor` finding to the matching `status` `anchor_gaps` entry, **Then**
   both name and locate the anchor identically (same authored handle, same file).
3. **Given** an anchor whose `constrains` target was dropped or absent (no
   authored target), **When** `factual_anchor` reports a defect on it, **Then**
   the message names the anchor by its `promotes` finding id alone (no `->`
   suffix), exactly as `status` renders the same anchor.

---

### User Story 2 - Every timeline contradiction points to the timeline file (Priority: P1)

An author runs `bookwright validate` on a project whose `bible/timeline.md`
contains a temporal contradiction — a follows/precedes cycle (rule a), a pair
both ordered and overlapping (rule b), or a containment that conflicts with a
strict order (rule c). Today only the numeric rule (d) tells the author the
problem lives in `bible/timeline.md`; rules a/b/c emit `source: null`. After this
change, all four rules resolve `source` to `bible/timeline.md`, so every temporal
contradiction is equally actionable.

**Why this priority**: It is the smaller, mechanical half — three rules adopting
the resolution rule (d) already uses — but it removes a self-inconsistency in one
validator and is independently valuable: an author can locate a cycle as easily
as a numeric clash.

**Independent Test**: Build a timeline fixture that triggers each of rules a, b
and c and assert each emitted `temporal` violation carries
`source == "bible/timeline.md"` (not `null`), matching what rule (d) already
produces.

**Acceptance Scenarios**:

1. **Given** a timeline with a follows/precedes cycle, **When** the author
   runs `bookwright validate --json`, **Then** the rule (a) `temporal` violation's
   `source` is `bible/timeline.md` (not `null`).
2. **Given** a timeline with a pair both strictly ordered and overlapping,
   **When** the author runs validate, **Then** the rule (b) violation's `source`
   is `bible/timeline.md`.
3. **Given** a timeline with a containment that conflicts with a strict
   order, **When** the author runs validate, **Then** the rule (c) violation's
   `source` is `bible/timeline.md`.

---

### Edge Cases

- **Anchor with no authored target** (`constrains` is `None`, whether
  authored `null` or a dropped unresolved link): the handle is the `promotes`
  finding id alone, with no `->` suffix — identical to how `status` renders it.
- **Anchor whose authored identity is unavailable** to the validator (an
  anchor URI not present in the corpus's anchor-identity records): the validator
  must still emit the violation (it reports every defective anchor, unlike
  `status`, which skips anchors with no identity). The behavior here must be
  defined so a finding is never dropped — see FR-010.
- **A temporal rule whose implicated event carries no E13 provenance**
  (should not occur for timeline events, but must not crash): `source` falls back
  to `None` rather than raising, exactly as `resolve_source` already degrades.
- **A temporal rule implicating several events** (a cycle spans an SCC; an
  overlap/containment names a pair): the locator is resolved from one
  deterministically-chosen implicated event so the output is byte-stable across
  builds.
- **A non-research project / a project with no anchors**: `factual_anchor`
  stays inert (returns `[]`) exactly as today — the locator change adds no work to
  a project with nothing to audit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every `temporal` violation from rules (a) cycle, (b)
  order-vs-overlap and (c) containment-vs-order MUST carry a resolved `source`
  locator instead of `None`, resolved the same way rule (d) already resolves it
  (`resolve_source` over an implicated event URI). All four rules MUST end up
  uniform in how they populate `source`.
- **FR-002**: For a `temporal` rule that implicates more than one event, the
  event whose URI is used to resolve `source` MUST be chosen deterministically
  (e.g. mirroring rule (d)'s choice), so repeated builds emit byte-identical
  `source` values.
- **FR-003**: Every `factual_anchor` violation MUST carry a `source` locator
  resolved to the anchor's authoring file (`bible/research/<topic>.md`) instead of
  `null`, resolved by the same path `status` uses (the anchor's `relpath` via its
  authored identity), **not** by `resolve_source(anchor.uri)` (which is `None` for
  an anchor by construction).
- **FR-004**: Every `factual_anchor` violation message MUST identify the anchor
  by its authored handle — the `promotes` finding id, plus the `constrains` target
  when the anchor declares one — instead of by the opaque uuid7 URI tail. The
  handle MUST match what `status` renders for the same anchor.
- **FR-005**: The change MUST NOT alter what the rules detect, nor any
  severity, nor the run's exit code / gate outcome. The same `error` / `warning`
  findings are emitted as today, differing only in their `source` and message
  identifier. (Actionability of the locator/message, not of the rule.)
- **FR-006**: Resolution MUST be a pure read over the graph (and the authored
  identity records the build already produces); it MUST add no new runtime
  dependency (Constitution II) and MUST keep `resolve_source`'s existing
  determinism (prefer a `:line`-bearing source, then the lexicographically
  smallest).
- **FR-007**: `factual_anchor`'s anchor-locator/handle resolution MUST be a
  **single shared resolution point** with `status` — both surfaces resolve "the
  readable handle and file of this anchor" through one code path so they cannot
  diverge in how they identify or locate the same anchor.
- **FR-008**: The frozen GOLEM ontology MUST remain untouched (Principle X): no
  new class, predicate, or `.ttl` change. Every changed source file MUST stay
  ≤ 500 lines (Principle IV).
- **FR-009**: The `factual_anchor` anchor handle and the `status` anchor
  handle MUST be byte-identical for the same anchor — verified empirically by a
  test that asserts the two surfaces agree.
- **FR-010**: If a defective anchor's authored identity is unavailable to the
  validator, the violation MUST still be emitted (no finding is ever dropped); the
  fallback identifier/locator for that case MUST be defined explicitly (e.g. the
  prior uuid7 label and a `None` source) so behavior is deterministic rather than
  an error.
- **FR-011**: The `DEBT-015` entry MUST be removed from `DEBT.md` (its class is
  resolved); the track-B index/roadmap lines that reference it MUST be reconciled
  to show it shipped in this iteration.
- **FR-012**: The behavior MUST be verified **empirically** with
  `uv run pytest`, with the affected oracles updated: a fixture with a defective
  anchor reports `source = bible/research/<topic>.md` (not `null`) and a message
  citing the authored handle (not the uuid7); a timeline fixture triggering rules
  a/b/c reports `source = bible/timeline.md` (not `null`); `factual_anchor` and
  `status` agree on naming/locating the same anchor. All four CI gates
  (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest`) stay green.

### Key Entities *(include if feature involves data)*

- **Anchor (research)**: the subject of a `bw:promotes` triple — itself the
  reified `E13_Attribute_Assignment`, so no E13 edge points *to* it (hence
  `resolve_source(anchor.uri)` is `None`). Identified for authors by its authored
  handle, not its minted uuid7 URI.
- **AnchorIdentity**: the authored, corpus-stable identity record the research
  mapping produces per anchor — carries the `promotes` finding id, the authored
  `constrains` target (or `None`), and the `relpath` of the authoring
  `bible/research/<topic>.md` file. The in-process URI is the join key back from
  graph projections. This is the data `status` already uses and that
  `factual_anchor` must reuse.
- **Violation `source` locator**: the `relpath[:line]` provenance string a
  validator attaches to a finding so an author can jump to the offending line —
  resolved for events via the graph's reified `E13` provenance
  (`resolve_source`), and for anchors via their `AnchorIdentity.relpath`.
- **Timeline event**: a `G5_Narrative_Event` authored in `bible/timeline.md`;
  unlike an anchor it **does** carry an inbound E13, so `resolve_source` over its
  URI yields `bible/timeline.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of `factual_anchor` violations on a project with defective
  anchors carry a non-`null` `source` pointing to the anchor's
  `bible/research/<topic>.md` (today: 0%).
- **SC-002**: 100% of `temporal` violations across all four rules carry a
  non-`null` `source` (today: only rule (d), i.e. one of four rule families).
- **SC-003**: For every defective anchor, the identifier and file that
  `factual_anchor` reports are identical to those `bookwright status` reports for
  the same anchor (zero divergence) — verified by a test that compares the two.
- **SC-004**: No `factual_anchor` or `temporal` message names an anchor or
  event by a raw uuid7 URI tail; every message uses an authored, human-readable
  handle.
- **SC-005**: The set of findings (count, severity, and gate/exit-code
  outcome) on every existing fixture is unchanged before and after this change —
  only `source` and message identifiers differ.

## Assumptions

- The exact rendered handle format mirrors `status`'s existing
  `AnchorGap`/`_anchor_line` rendering (`<promotes-finding-id>` plus
  `-> <constrains-target>` when present); reusing that one format — ideally a
  shared helper — is preferred over inventing a second spelling, per the
  clarification above and FR-007.
- The validator can obtain the authored anchor-identity records for the project
  under validation through the same machinery `status` uses (the research mapping
  of `bible/research/`); exposing them to the validator is in scope as the plumbing
  that FR-007's shared resolution point requires, and is not "future X" plumbing —
  it is the minimum needed to resolve the anchor locator.
- All timeline events are authored in `bible/timeline.md`, so any
  deterministically-chosen implicated event resolves to that same file; the choice
  of which implicated event to resolve from affects only determinism, not the
  resulting relpath.
- `resolve_source` already returns the deterministic, `:line`-preferring result
  and is reused as-is; no change to its tie-breaking is needed.

## Out of Scope

- Changing **what** the rules detect — only their locator/identifier. No new
  rule, finding, or severity; the gate and exit-code contract are untouched.
- The LLM semantic-judgment escalation (issue #1 **move 3**).
- The prose validators (`character_presence`, `narrative_structure`,
  `focalization`) — they already emit `relpath:line` and are not touched here.
- `narrative_structure`'s name-vs-slug identifier inconsistency (DEBT-017,
  iteration 049) — a sibling presentation cleanup, deferred to its own iteration.
- Any new runtime dependency, any change to the frozen ontology
  (`golem.ttl` / vocab `.ttl`), or any file growing past the 500-line ceiling.
