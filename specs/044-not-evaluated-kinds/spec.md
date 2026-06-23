# Feature Specification: `not_evaluated` distinguishes a permanent capability-gap from an input-gap; green is reachable again

**Feature Branch**: `044-not-evaluated-kinds`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "Necesidad: la iteración 043 hizo honesto el heurístico de conjunto abierto — el validador `character_unknown_mentions` declara `NotEvaluated` INCONDICIONALMENTE… Esta iteración CATEGORIZA las entradas de `not_evaluated` y hace que SOLO las de tipo input gobiernen el verde y el nudge; las de tipo capability se SIGUEN mostrando pero no tumban el verde ni piden una acción que el autor no puede ejecutar."

## Context (why this iteration exists)

Iteration 040 introduced a tri-valued validator verdict — `evaluated` /
`not-evaluated(reason)` — and a single documented "green/clean" predicate:
`status == "ok"` AND `not_evaluated == []` (in `src/bookwright/validation/report.py`).
That predicate assumed every `not_evaluated` entry is **actionable**: a validator
that could not look at *this* project because an input is missing or malformed
(e.g. `focalization` with no narrative-voice declaration, an empty manuscript).
The author fixes the input and the validator evaluates next run.

Iteration 043 made the open-set proper-noun rule honest: the new
`character_unknown_mentions` validator is a **pure abstainer** that raises
`NotEvaluated` **unconditionally** — no project state can make a deterministic
capitalization heuristic do open-set discovery soundly; the honest answer waits
for move 3 (LLM semantic judgment). That is correct, but it broke the 040
contract as a side effect: because the abstainer is **always** dormant,

1. the green predicate is `False` in **every** project forever (until move 3),
   including a flawless one; and
2. the `_activate_dormant_validators` rule in `src/bookwright/status/rules.py`
   fires a `bookwright-continuity` nudge in **every** project, including a clean
   one.

A green that no project can ever reach does not inform: if pristine and broken
both read "not green", the author learns to **ignore** the `not_evaluated`
channel — exactly the alarm fatigue issue #1 set out to kill, merely relocated
from the `warning` channel (which 043 emptied) to the `not_evaluated` channel.

The root cause: there are **two kinds** of `not_evaluated` entry, and 043 mixed
them in the one channel that governs green. **(a) Input-conditional** (what 040
modelled): "I could not evaluate *your* project because of a missing/broken
input" — actionable, per-project, transient. **(b) Permanent capability-gap**
(the 043 abstainer): "no deterministic run evaluates this; it waits for move 3" —
not actionable by the author, identical in every project, permanent.

This iteration **categorizes** `not_evaluated` entries so that only the
input-conditional kind governs green and the dormant-validator nudge. The
capability-gap kind **stays visible** (visible gaps ≠ silence — issue #1
doctrine) but no longer knocks the project out of green or asks for an action the
author cannot perform. A flawless project can be green again, while the move-3
gap stays recorded and in plain view.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A flawless project reads as green again (Priority: P1)

An author runs `bookwright validate` (or `bookwright status`) on a project with
no `error`, no `warning`, and no missing/malformed inputs. Today the report
reads "not green" solely because the always-dormant `character_unknown_mentions`
abstainer sits in `not_evaluated`. After this change the project reads **green**:
the permanent capability-gap entry is still listed (labeled as such) but no
longer denies green status.

**Why this priority**: This is the headline outcome — restoring a reachable
green so the `not_evaluated` channel keeps its signal value. Without it, the
channel is noise the author is trained to ignore.

**Independent Test**: Run validation/status on a clean fixture
(`tiny-novel` / `tiny-memoir`) and assert the documented green predicate is
`True` even though `not_evaluated` carries one permanent capability-gap entry
(the concrete `kind` identifier is a `/speckit-plan` detail).

**Acceptance Scenarios**:

1. **Given** a project with no errors, no warnings, and no input-gaps, **When**
   the author runs validation, **Then** the run satisfies the refined green
   predicate (it is "green/clean") even though `not_evaluated` lists the
   `character_unknown_mentions` capability-gap entry.
2. **Given** that same project, **When** the author runs `bookwright status`,
   **Then** `next_actions` contains **no** `bookwright-continuity` action that
   asks them to "activate the dormant validators".

### User Story 2 - The author can tell an actionable gap from a permanent one (Priority: P1)

When a validator could not look because an input is missing (e.g.
`focalization` with no voice declaration, or an empty manuscript), the author
should still be told to fix that input — it is actionable and it should keep the
project out of green until fixed. When the entry is the permanent move-3
capability-gap, it should be shown but clearly marked as a known limitation the
author cannot act on.

**Why this priority**: The whole point is to separate "you can fix this" from
"nobody can fix this yet" so the author trusts each entry. Conflating them is the
defect being removed.

**Independent Test**: Construct one synthetic run with an input-conditional
not-evaluated entry and one with the capability-gap entry; assert only the former
denies green and only the former produces the dormant-validator nudge, while both
appear in every surface labeled by their kind.

**Acceptance Scenarios**:

1. **Given** a project where `focalization` raises not-evaluated for a missing
   voice declaration (an input-gap), **When** the author runs validation, **Then**
   the run is **not** green and `status` still nudges them (via
   `bookwright-continuity`) to declare the narrative voice.
2. **Given** a project whose only `not_evaluated` entry is the
   `character_unknown_mentions` capability-gap, **When** the author runs
   validation, **Then** the run is green and `status` does **not** nudge them.
3. **Given** either kind of entry, **When** the author inspects the `--json`
   envelope, the `bookwright status` payload, and the human report, **Then** each
   entry appears in all three, carrying a `kind` that distinguishes input-gap
   from capability-gap.

### User Story 3 - Tooling consumers can read the category from the contract (Priority: P2)

Agent skills and any machine consumer of the `--json` envelope and the `status`
payload need to distinguish the two kinds programmatically — to decide whether to
surface an action — without re-deriving the category from the reason string.

**Why this priority**: The status-consuming skills (021–022) drive author
guidance off the JSON contract. The category must be a first-class field, not
prose to be parsed.

**Independent Test**: Parse the `--json` output of `validate` and the payload of
`status`; assert each `not_evaluated` entry exposes a `kind` field with one of
the two documented values, and that no pre-existing field changed name or type.

**Acceptance Scenarios**:

1. **Given** any run with a `not_evaluated` entry, **When** a consumer reads the
   `--json` `not_evaluated[]` array, **Then** each element includes a `kind`
   field alongside the existing `validator` and `reason` fields (additive — no
   existing key renamed or retyped).
2. **Given** the same run, **When** a consumer reads `bookwright status`'s
   `state.validation.not_evaluated`, **Then** each element likewise includes
   `kind`.

### Edge Cases

- **A run with both kinds at once**: a project that is missing a voice
  declaration (input-gap) *and* carries the permanent capability-gap. The run is
  **not** green (the input-gap denies it); the dormant-validator nudge names
  **only** the input-gap validator; both entries are listed with their `kind`.
- **A custom third-party validator that raises not-evaluated without specifying a
  kind**: it MUST default to the input-conditional kind (so its behavior is
  byte-for-byte what 040 produced — it denies green and nudges as before).
- **The gate is never affected**: neither kind of `not_evaluated` entry, in any
  combination, changes whether CI fails. Only an `error` finding gates.
- **A run whose only content is a capability-gap entry** must not print the
  "no violations found" clean line as if nothing happened — the entry stays
  visible in the `not evaluated:` section of the human report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The not-evaluated signal (the `NotEvaluated` exception and the
  recorded `NotEvaluatedResult`) MUST carry a **kind** with exactly two values: an
  **input-conditional** kind ("could not evaluate *this* project due to a missing
  or malformed input" — actionable, per-project, transient) and a **permanent
  capability-gap** kind ("no deterministic run evaluates this; it awaits move 3" —
  not author-actionable, identical across projects, permanent).
- **FR-002**: The **input-conditional kind MUST be the default**. Every existing
  not-evaluated raise that does not specify a kind MUST keep its iteration-040
  behavior byte-for-byte — same reason string, same channel, same effect on green
  and on the nudge. The audit found the complete set of such raises (all
  input-conditional, all to remain default): all four `focalization` input-gap
  raises (no constitution file, no declaration, `[PENDING]`-only voice, a
  declaration naming no grammatical person), `setting_continuity`'s "manuscript is
  empty", `character_presence`'s "no roster and no files" guard, and any custom
  third-party validator. `character_unknown_mentions` (FR-003) is the **only**
  raise that opts into the non-default capability-gap kind.
- **FR-003**: `character_unknown_mentions` MUST raise the not-evaluated signal
  with the **permanent capability-gap** kind, with its reason string unchanged.
- **FR-004**: The documented "green/clean" predicate MUST be **refined**:
  green = `status == "ok"` AND there are **no** `not_evaluated` entries of the
  **input-conditional** kind. Capability-gap entries MUST NOT deny green. A
  project with no `error`, no `warning`, and no input-gaps MUST read green even
  while it carries the permanent `character_unknown_mentions` capability-gap
  entry. This predicate and its rationale MUST be re-documented where 040
  documented it.
- **FR-005**: The `status` rule that nudges the author to "activate the dormant
  validators" (`_activate_dormant_validators`) MUST fire **only** for
  input-conditional entries. Capability-gap entries MUST NOT trigger that nudge.
- **FR-006**: The remedy clause iteration 043 added for
  `character_unknown_mentions` in the dormant-validator nudge MUST be removed
  (the validator is no longer nudged on).
- **FR-007**: **Visibility is non-negotiable (issue #1 doctrine)**: a
  capability-gap entry MUST still appear in the `--json` `not_evaluated[]` array,
  in `bookwright status`, and in the human report, labeled by its kind as a
  **non-actionable known limitation**. The label MUST be **generic to the kind**
  (it MUST NOT hardcode any single validator's specifics): the validator-specific
  detail — e.g. `character_unknown_mentions`'s "awaits move 3" — stays in the
  existing `reason` string, not in the kind label, so the kind-rendering path is
  not coupled to one validator. It MUST NOT be hidden — hiding it would
  reintroduce the silence (false confidence) that iteration 040 eliminated.
- **FR-008**: The `--json` `not_evaluated[]` envelope and the `bookwright status`
  payload MUST each include the `kind` as an **additive** key: the entry shape
  gains one field; no existing field is renamed or retyped.
- **FR-009**: The CI gate MUST be unchanged: only an `error` finding fails CI;
  `not_evaluated` entries of **neither** kind gate. Only the (informative) green
  predicate and the `status` nudge change behavior.
- **FR-010**: The human report MUST continue to surface every `not_evaluated`
  entry (it MUST NOT print the "no violations found" clean line when the only
  content is a not-evaluated entry of either kind), and MUST present each entry's
  kind so a reader can tell an actionable gap from a permanent one.
- **FR-011**: The `tiny-historical` oracle MUST be updated to match observed
  behavior: its single `not_evaluated` entry gains the permanent capability-gap
  kind; `next_actions` returns from 4 to 3 (the universal dormant-validator nudge
  is gone); `validation.counts` stay byte-identical (`error: 1, warning: 1,
  info: 0`); the `error` count stays 1. The fixture manuscript/bible MUST NOT be
  edited.
- **FR-012**: The clean fixtures `tiny-novel` and `tiny-memoir` MUST read green
  again under the refined predicate.
- **FR-013**: The scope is bounded to the not-evaluated categorization. This
  iteration MUST NOT touch `character_presence` (the orphan rule) or
  `io/prose.py`. It MUST NOT add a new runtime dependency, MUST keep every changed
  file ≤ 500 lines, MUST keep prose validators emitting `triples=()`, and MUST
  leave the frozen ontology (the 17-class closure / `golem.ttl`) untouched.

### Key Entities

- **Not-evaluated signal / result**: the conscious-skip record a validator
  contributes when it did not look. It already carries the validator name and an
  English reason; this iteration adds a **kind** distinguishing input-conditional
  from permanent capability-gap. Surfaced (unchanged channels) in the `--json`
  `not_evaluated[]` array, the `status` payload, and the human report.
- **Green/clean predicate**: the single documented definition of a healthy run.
  Refined here to ignore capability-gap entries while still being denied by
  input-conditional ones and by any `error`.
- **Dormant-validator nudge**: the `status` recommendation that asks the author
  to activate validators that could not evaluate. Refined here to consider only
  input-conditional entries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project with no errors, no warnings, and no input-gaps is
  reported as green/clean by the refined predicate, even though it carries the
  permanent `character_unknown_mentions` capability-gap entry. (Verified on
  `tiny-novel` and `tiny-memoir`.)
- **SC-002**: For a clean project, `bookwright status` recommends **zero**
  "activate the dormant validators" actions (the universal nudge is gone).
- **SC-003**: Every `not_evaluated` entry — of either kind — is present in all
  three surfaces (the `--json` `not_evaluated[]` array, the `status` payload, and
  the human report), each carrying its `kind`. None is hidden.
- **SC-004**: A run with an input-conditional not-evaluated entry is **not**
  green and still produces the dormant-validator nudge; a run whose only
  not-evaluated entry is the capability-gap is green and produces no such nudge.
  Both are verifiable from synthetic state with nothing pre-baked on disk.
- **SC-005**: The CI gate outcome (pass/fail) is identical to before for every
  fixture — only `error` findings gate; `not_evaluated` of neither kind changes
  it.
- **SC-006**: The `tiny-historical` oracle matches the run empirically: the
  `not_evaluated` entry gains the capability-gap kind, `next_actions` is 3 (down
  from 4), `validation.counts` is byte-identical, `error` stays 1; the fixture
  manuscript/bible is unchanged.
- **SC-007**: Adding `kind` is additive across every serialized surface: no
  pre-existing field of any `not_evaluated` entry or `status` payload is renamed
  or retyped, and a parser reading the old shape still finds every old key.
- **SC-008**: The full test suite (`uv run pytest`) and the four gates
  (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest` ≥ 80 % coverage)
  pass.

## Assumptions

- The two kinds are represented as a small closed vocabulary (two named values),
  carried as one field on the not-evaluated signal and its recorded result, with
  the input-conditional value as the default so existing raises are unchanged.
  The exact identifiers and storage form are a planning detail.
- The category is the validator's own declaration at raise time (the only place
  that knows whether the gap is about *this* input or about the *approach*). The
  runner stamps it onto the recorded result alongside the validator name, exactly
  as it stamps the reason today.
- "Re-documented where 040 documented it" means the green-predicate docstring and
  the design-spec section that 040 established (`bookwright-design.md` § 13, the
  green predicate) are updated to state the refined predicate before the code
  diverges from the docs.
- The human-report label for the kind is short and English (the report is
  English); the precise wording is a planning/UX detail, constrained only by
  FR-007 (the kind label must read as a non-actionable known limitation, not as a
  silent pass, and must be generic to the kind — the validator-specific "move 3"
  detail stays in the unchanged `reason` string).

## Out of Scope

- The `focalization` head-hopping not-evaluated work (iteration 045).
- Move 3 itself — LLM semantic judgment for open-set proper-noun discovery
  (track C).
- The `errors[]` channel for validators that crash (distinct from
  `not_evaluated`; not touched).
- Any change to `character_presence` (the orphan rule) or `io/prose.py`.
