# Feature Specification: Soft warning for unrecognized Propp/Greimas vocabulary terms

**Feature Branch**: `047-vocab-term-warning`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Con un vocabulario activo (`[vocabularies] active`, p. ej. `propp`), una unidad de `outline/units/*.md` con un término de `functions:` que NO casa ninguna de las 31 funciones de Propp se ingiere EN SILENCIO como `G10_Narrative_Function` sin `crm:P2_has_type`. No hay warning ni hallazgo de validación. Inconsistente con los vocabularios de research, que RECHAZAN lo desconocido con un mensaje enumerado. DEBT-016. Decisión issue #1 (track B): cerrado para *tipar*, abierto para *autorar* — un término no reconocido emite un `warning` NO FATAL en `graph build` que enumera los términos válidos, pero el nodo se ingiere igual, sin `P2_has_type`."

## Context

This is iteration 047 (patch track v0.5.x, issue #1 **track B — pulido
determinista**). It resolves **DEBT-016**.

Bookwright bundles two conceptually **closed** controlled vocabularies — Propp's
31 narrative functions (`propp.ttl`) and Greimas' actant model (`greimas.ttl`).
When a project activates one via `[vocabularies] active`, `graph build` types an
authored term against it: a matching name gets a `crm:P2_has_type` edge to the
canonical term; a non-matching name (a typo such as `intimidacion`, or an
invented label) is **minted into the graph silently as an untyped node** — no
warning, no validation finding. The author gets zero feedback that their term
typed nothing.

This is **inconsistent** with how the research subsystem treats its own closed
vocabularies (`type` / `reliability`): an unknown value is **rejected fatally**
with an enumerated message listing the valid values (DEBT-006/036). Two closed
vocabularies, two opposite treatments: research aborts, Propp/Greimas stays
silent.

Issue #1 decided the resolution: **closed for *typing*, open for *authoring*.**
An unrecognized term emits a **non-fatal warning** that enumerates the valid
terms (symmetry with research), but the node is **still ingested unchanged**,
without `P2_has_type` — the build does not abort and its exit code does not
change. The principle that makes this consistent with research's *fatal*
rejection: **fatal ⇔ an invalid value breaks downstream logic.** An invalid
`reliability` would break the `factual_anchor` gate, so research aborts; an
absent `P2_has_type` is descriptive metadata that breaks nothing downstream, so
this only warns.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Typo in a narrative-function name is surfaced (Priority: P1)

An author writes a unit card under `outline/units/` with
`functions: [intimidacion]` (a misspelling of an intended Propp function, or an
invented term) while the `propp` vocabulary is active. They run `graph build`.
Today the function node is created with no type and no feedback; the author never
learns their term typed nothing. With this feature, `graph build` reports the
unrecognized term — naming the file, the field, the offending term, and listing
the valid terms — so the author can fix the typo or knowingly keep their own
label.

**Why this priority**: This is the verified, dogfood-reported defect (DEBT-016)
and the core honesty gap the iteration closes. It is the minimum viable slice:
without it, a typo in a closed vocabulary is invisible.

**Independent Test**: With `propp` active, build a project containing one unit
whose `functions:` lists a non-Propp term and one valid Propp function. Assert
the `graph build` envelope reports exactly the unrecognized term (with the valid
terms enumerated) and reports nothing for the valid one; assert the function
node is still present in the graph **without** a `crm:P2_has_type` edge.

**Acceptance Scenarios**:

1. **Given** the `propp` vocabulary is active and a unit lists a `functions:`
   term that matches no Propp function, **When** `graph build` runs, **Then** the
   build succeeds (exit code unchanged), the function node is minted **without**
   `crm:P2_has_type`, and a non-fatal warning names the file, the `functions`
   field, the offending term, and enumerates the valid Propp terms.
2. **Given** the `propp` vocabulary is active and a unit lists a `functions:`
   term that **does** match a Propp function, **When** `graph build` runs,
   **Then** the node receives its `crm:P2_has_type` edge and **no** warning is
   emitted for that term.
3. **Given** the `propp` vocabulary is active and a unit with an unrecognized
   `functions:` term, **When** `graph build` runs **twice** over the same
   project, **Then** the warning output is byte-identical across both runs — both
   the order of warning entries and the order of each warning's enumerated valid
   terms (FR-016).

---

### User Story 2 - Unrecognized character actant role is surfaced the same way (Priority: P1)

An author assigns a character a `narrative_roles:` actant label that matches no
Greimas actant while the `greimas` vocabulary is active. Today that role node is
minted without its actant type, silently. With this feature, the same kind of
non-fatal enumerated warning is emitted — the treatment is uniform across both
closed vocabularies, not patched for one instance.

**Why this priority**: The fix is a **class sweep**, not an instance patch.
Greimas role typing has the identical silent `resolve()→None`-then-mint path;
leaving it silent would re-open the same debt class for the other vocabulary.

**Independent Test**: With `greimas` active, build a character whose
`narrative_roles:` includes a non-Greimas label and a valid actant. Assert the
warning is emitted for the unrecognized label only, and the role node is minted
without `crm:P2_has_type`.

**Acceptance Scenarios**:

1. **Given** the `greimas` vocabulary is active and a character's
   `narrative_roles:` includes a label matching no Greimas actant, **When**
   `graph build` runs, **Then** the role node is minted **without**
   `crm:P2_has_type` and a non-fatal warning names the file, the
   `narrative_roles` field, the offending term, and enumerates the valid Greimas
   terms.
2. **Given** a valid Greimas actant label, **When** `graph build` runs, **Then**
   the role node is typed and **no** warning is emitted for it.

---

### User Story 3 - No active vocabulary leaves everything unchanged (Priority: P2)

A project with **no** active narrative vocabulary builds exactly as before — no
typing is attempted and therefore no unrecognized-term warning can arise. The
feature must not change the output of a vocabulary-free build.

**Why this priority**: Guards the non-regression contract. Typing only happens
under an active vocabulary; the warning is a by-product of typing and must be
absent whenever typing is absent.

**Independent Test**: Build the same project with no active vocabulary and assert
the `graph build` envelope and the graph are byte-identical to the pre-feature
output (no warning channel entries, no `P2_has_type`).

**Acceptance Scenarios**:

1. **Given** no active vocabulary, **When** `graph build` runs over units with
   `functions:` and characters with `narrative_roles:`, **Then** no
   unrecognized-term warning is emitted and no node is typed.

---

### Edge Cases

- **A term that already warns elsewhere must not be double-handled.** An
  outline-unit `roles:` name that resolves against no character role node already
  emits an `unresolved_references` soft note (it is a character-role edge
  resolution, *not* Greimas actant typing). That path is left untouched — the new
  warning covers only the silent `resolve()→None`-then-mint-untyped typing paths.
- **A blank / unsluggable term** contributes no node today (it is dropped before
  minting) and therefore must produce no warning — there is nothing untyped to
  report.
- **A term repeated across cards** is minted/typed once (functions are
  deduplicated across units; character roles are per character). The warning is
  emitted where the typing decision is made, so a deduplicated term is not warned
  about redundantly on every later reuse.
- **An active but unknown vocabulary name** (outside the two bundled ones) is
  already ignored silently and activates no typing; it therefore produces no
  warning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When a narrative vocabulary is active and an authored term's typing
  lookup matches no term of that vocabulary, `graph build` MUST record a
  **non-fatal warning** for that term.
- **FR-002**: The warning MUST name the source **file**, the **field** the term
  came from (`functions` for Propp, `narrative_roles` for Greimas), the
  **offending term** as authored, and the **active vocabulary** it failed to type
  against; and its human-facing rendering MUST **enumerate the valid terms** of
  that vocabulary — the same enumerated-feedback spirit as research's unknown-
  vocabulary rejection. The enumeration is **feedback content** carried by the
  rendered message and derivable from the vocabulary identity; the structured
  record MUST NOT denormalize the full valid-term set into every entry (research
  enumerates in its message string, not in a per-record field — its
  `ResearchTargetWarning` sibling stores only `{path, field, name}`).
- **FR-003**: The node MUST be minted **exactly as today** — created without
  `crm:P2_has_type`. The current ingestion behavior (iteration 030 FR-006) MUST
  NOT change; the warning is **purely additive**.
- **FR-004**: The build MUST NOT abort on an unrecognized term, and its **exit
  code MUST NOT change** because of one. The warning is a soft channel, never a
  gate.
- **FR-005**: This MUST be an **ingestion** warning surfaced by `graph build`,
  **not a validation finding**. No validator may be added, removed, or modified.
- **FR-006**: The warning MUST reuse the existing `graph build` **soft-warning
  channel pattern** (the same family as `unknown_keys` / `unresolved_references`,
  and structurally closest to `research_warnings` / `ResearchTargetWarning`, which
  is likewise a vocabulary-adjacent `{path, field, name}` record) and MUST be
  surfaced both in the `graph build` machine-readable envelope and in the
  human-readable build report, the same way those existing channels are.
- **FR-007**: The fix MUST be a **class sweep**: every site where an active
  vocabulary's typing lookup returns no match and the node is then minted untyped
  in silence MUST be handled **uniformly** — at minimum the Propp `functions:`
  typing path and the Greimas `narrative_roles:` typing path.
- **FR-008**: Sites that **already** surface a warning for a non-matching name
  (the outline-unit `roles:` → character-role resolution that emits
  `unresolved_references`) MUST NOT be touched or duplicated.
- **FR-009**: With **no** active vocabulary, behavior MUST be unchanged: no
  warning is emitted and no typing occurs (output byte-stable vs. pre-feature).
- **FR-010**: A term that **does** match a vocabulary term MUST type the node and
  MUST NOT produce any warning.
- **FR-011**: No new validation `Severity` value (e.g. an `info` level) may be
  introduced and the validation `Severity` enum MUST NOT be touched — this is a
  `graph build` warning channel, not a `Violation`.
- **FR-012**: The design document MUST record the **fatal-vs-warning principle**
  in the section covering the Propp/Greimas vocabularies (the iteration-030
  vocabulary typing): why research's unknown value is fatal and an unrecognized
  Propp/Greimas term only warns.
- **FR-013**: The DEBT-016 entry MUST be removed from `DEBT.md` (and any track-B
  index reference to it reconciled).
- **FR-014**: The frozen ontology MUST remain intact — no class is added,
  `golem.ttl` and the vocabulary `.ttl` files are not edited. The feature only
  **warns** about a term that matched nothing; it adds no vocabulary terms.
- **FR-015**: No new runtime dependency may be introduced (Constitution II), and
  every changed file MUST stay ≤ 500 lines.
- **FR-016**: The warning output MUST be **deterministic** — building the same
  project twice MUST yield byte-identical unrecognized-term warnings, both in the
  order of the warning entries (inheriting the sibling channels' stable
  sorted-glob file order) and in the order of each warning's **enumerated valid
  terms**. The valid-term enumeration is drawn from the vocabulary index, whose
  underlying label store has no guaranteed iteration order; it MUST therefore be
  emitted in a stable, sorted order rather than in incidental store order, so no
  run-to-run nondeterminism enters the `graph build` envelope or report.

### Key Entities *(include if feature involves data)*

- **Unrecognized-term warning**: a soft, non-fatal record in the `graph build`
  report describing one authored term that, under an active vocabulary, matched
  no vocabulary term and so produced an untyped node. Structured attributes
  (the machine-readable envelope record): source file, field of origin, the
  offending term as authored, and the **active vocabulary** it failed to type
  against — a minimal `{path, field, term, vocabulary}` record, mirroring its
  `ResearchTargetWarning` sibling. The **enumerated set of valid terms** is the
  warning's human-facing feedback, rendered into the build-report message and
  derivable from the vocabulary identity — not copied into every structured
  record. Sibling of the existing `unknown_keys` / `unresolved_references` soft
  channels; never affects the exit code.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With an active vocabulary, **100%** of authored `functions:` /
  `narrative_roles:` terms that type nothing are reported in the `graph build`
  output (today: 0%).
- **SC-002**: Every such report names the file, the field, the offending term,
  and lists the valid terms of the active vocabulary.
- **SC-003**: The graph produced for any given project is **identical** to the
  pre-feature graph — the same nodes, the same `crm:P2_has_type` edges, and the
  same absence of them (the warning adds no triple and removes none).
- **SC-004**: An unrecognized term **never** changes the `graph build` exit code;
  a build that would exit 0 still exits 0.
- **SC-005**: A vocabulary-free build emits **zero** unrecognized-term warnings
  and is byte-identical to its pre-feature output.
- **SC-006**: A valid term emits **zero** warnings while still being typed.
- **SC-007**: The behavior is verified **empirically** by the test suite
  (`uv run pytest`), with all four CI gates green.
- **SC-008**: Building the same project **twice** yields **byte-identical**
  unrecognized-term warning output — the warning entries and each entry's
  enumerated valid terms appear in the same order both times (no run-to-run
  nondeterminism enters the envelope or report).

## Assumptions

- The "valid terms" enumerated in the warning are the canonical authored term
  names of the active vocabulary (the same human-facing spirit as research
  enumerating its accepted `type` / `reliability` values). The exact rendering of
  that set — and the lookup that exposes it from the vocabulary index, which today
  offers only `resolve()` and no enumerator — is a plan-level detail; this spec
  requires only that a meaningful enumeration appears, in the stable, sorted order
  FR-016 mandates.
- The warning is emitted at the point where the typing decision is made (the
  mint/first-introduction of a term), so a term deduplicated across cards is
  reported once rather than on every reuse.
- The two bundled vocabularies (Propp functions, Greimas actants) are the
  complete set of closed-vocabulary typing surfaces in scope; should a third ever
  be added, the same uniform treatment is expected to apply, but no such
  vocabulary exists today.

## Out of Scope

- Making an unrecognized term **fatal** — the decision is explicitly non-fatal
  (open for authoring).
- Adding a **new validator** or any validation-layer finding for this.
- The **research** vocabularies (`type` / `reliability`) — they already reject
  unknown values (DEBT-006); they are not re-touched.
- The issue #1 **move 3** (semantic judgment) — unrelated track.
- Adding terms to `propp.ttl` / `greimas.ttl` or otherwise editing the frozen
  ontology / vocabulary data.
- Changing the `graph build` exit-code contract so that a skip or an unrecognized
  term gates the build.
