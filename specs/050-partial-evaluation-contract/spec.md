# Feature Specification: a partial-evaluation contract — a validator may emit findings **and** abstain on another dimension in the same run; `focalization` recovers its first-person-break check under limited-third

**Feature Branch**: `050-partial-evaluation-contract`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Necesidad: el contrato del validador es TODO-O-NADA: `validate()` o devuelve `list[Violation]` o lanza `NotEvaluated` … No hay forma de que un validador compruebe deterministamente una dimensión Y declare `not_evaluated` de otra en el mismo run. … Esta iteración introduce un CONTRATO DE EVALUACIÓN PARCIAL … `focalization` lo estrena —recupera `_first_person_breaks` bajo 3ª-limitada y declara el head-hopping como `not_evaluated(pending_capability)` a la vez—, pero el contrato es GENERAL. … Borra DEBT-019 de `DEBT.md`."

## Context (why this iteration exists)

The validator contract is **all-or-nothing**. A validator's `validate()`
either returns a `list[Violation]` (it evaluated; the list may be empty for a
legitimate green) **or** raises `NotEvaluated(reason, kind)` (it consciously did
not look — the runner records one `not_evaluated` entry and discards any
findings). There is **no third option**: a validator cannot deterministically
check one dimension **and** declare `not_evaluated` on another in the same run.

Iteration 045 hit that wall. `focalization` checks two independent things under a
declared third-person voice:

1. **First-person breaks** — a deterministic, high-precision, closed rule:
   first-person pronouns (`yo`/`nosotros`/`I`/`we`) outside dialogue under a
   declared third-person voice. This is `_first_person_breaks`
   (`focalization.py:105`).
2. **Head-hopping** — interiority attributed to a non-focal character: an
   open-set **semantic judgment** (move 3). Measured nearly dormant on real
   prose (DEBT-014); iteration 045 made it correctly **abstain** with
   `kind=pending_capability`.

But because the contract is all-or-nothing, abstaining on head-hopping forced
`focalization` to abstain on the **whole run**: under "Tercera persona limitada,
focalizada en X", `validate()` does `raise NotEvaluated(pending_capability)`
(`focalization.py:101`) **before** reaching `_first_person_breaks`
(`focalization.py:102`). So the deterministic first-person-break check **no
longer runs for focalized projects** — it only runs under third-person
**non-limited** (omniscient). That is a real coverage regression, currently
**invisible** in the suite (no fixture exercises a first-person break under
limited-third), recorded as **DEBT-019**.

This is exactly the determinism/LLM frontier of `bookwright-design.md § 20.6.1`:
the deterministic half (first-person break) **must run**; the open-set semantic
half (head-hopping) **must abstain**. The all-or-nothing contract forbids having
both at once.

This iteration introduces a **partial-evaluation contract**: a validator may
emit `violations` **and** declare one or more `not_evaluated` abstentions in the
**same run**. `focalization` is its first consumer — it recovers
`_first_person_breaks` under limited-third **and** declares the head-hopping
abstention `not_evaluated(pending_capability)` at the same time — but the
contract is **general**: future move-3 validators will need it (the deterministic
part runs, the semantic part abstains). The contract is **available**, not
mandated — only `focalization` uses it today.

This **extends** the runner's normalization; it **consumes** — does not change —
the machinery iterations 040 and 044 already shipped (the tri-valued verdict,
the `not_evaluated[]` channel, the closed `NotEvaluatedKind` vocabulary, the
044 green predicate, the gate where only `error` breaks CI).

## Clarifications

### Session 2026-06-24

- Q: Does the existing all-or-nothing contract stay valid, or is it replaced? →
  A: It stays valid as two of three accepted return forms. The runner normalizes
  **three** shapes: (a) `list[Violation]` (today — every existing validator
  intact), (b) `raise NotEvaluated(reason, kind)` (today — a **total** abstention
  shortcut), and (c) the new partial form carrying `violations` **and** one or
  more abstentions. Forms (a) and (b) are unchanged; only `focalization` adopts
  (c).
- Q: Do the three existing focalized fixtures change their emitted output? →
  A: No — `tiny-historical`/`tiny-novel`/`tiny-quest` stay **byte-identical**.
  They already carry the head-hop `pending_capability` entry and have **no**
  first-person breaks, so `_first_person_breaks` adds nothing; only the internal
  mechanism changes (form (c) instead of `raise`). A **new** unit case (not a new
  shipped fixture) exercises the both-at-once path empirically.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The deterministic first-person-break check runs again under a focalized voice (Priority: P1)

An author writes a focalized novel — "Tercera persona limitada, focalizada en
X" — and slips a first-person pronoun outside dialogue into a scene (`Yo no
entendía nada.`). Today `focalization` abstains for the whole run and **never
sees** that break: a real, deterministic, high-precision finding is silently
dropped because head-hopping (a different, semantic dimension) abstains. After
this change, `focalization` runs `_first_person_breaks` **and** declares the
head-hopping abstention in the same run: the author gets (i) the first-person
`warning` citing the marker and its `relpath:line`, **and** (ii) the head-hopping
`pending_capability` `not_evaluated` entry. The deterministic check is no longer
sacrificed to the semantic abstention.

**Why this priority**: This is the headline outcome — it closes DEBT-019 by
recovering a deterministic check that the all-or-nothing contract was suppressing
for every focalized project. Without it, focalized projects keep losing a real
check.

**Independent Test**: Run `focalization` on a project whose constitution
declares a third-person **limited/focalized** voice and whose manuscript has a
first-person pronoun outside dialogue. Assert the result carries **both** a
`focalization` `warning` finding citing the marker **and** a `focalization`
`not_evaluated` entry with `kind == pending_capability`.

**Acceptance Scenarios**:

1. **Given** a project with a parseable third-person **limited** voice and a
   first-person marker outside dialogue, **When** the author runs
   `bookwright validate`, **Then** `focalization` emits **one** `warning`
   (first-person break, with a `relpath:line` locator) **and** **one**
   `not_evaluated` entry with `kind == pending_capability` and the head-hopping
   reason — in the **same** run.
2. **Given** that same project, **When** the author inspects the report, **Then**
   the `warning` sets `status = violations` (a real finding, as it should) while
   the `pending_capability` entry does **not** deny green on its own.
3. **Given** a project with a limited voice and **no** first-person break,
   **When** the author runs validation, **Then** `focalization` emits **zero**
   findings and the **single** head-hopping `not_evaluated` entry — byte-identical
   to today's output (the form changed internally, the emission did not).

---

### User Story 2 - Every other validator keeps working byte-for-byte (Priority: P1)

The partial-evaluation contract is **additive**. Every validator that today
returns a `list[Violation]` or raises `NotEvaluated` continues to work
**without being touched** — the runner accepts the new third form **alongside**
the two existing ones and routes each into the same `violations` /
`not_evaluated` channels it always has. `focalization`'s four input-conditional
abstentions (no constitution / no declared voice / `[PENDING]` / no person) and
the omniscient and first-person paths are unchanged.

**Why this priority**: Back-compat is the non-negotiable boundary. A widened
return type must not perturb any existing validator's output or the runner's
deduping/sorting, and `mypy --strict` must stay clean across the wider type.

**Independent Test**: Run the full validator set on every existing fixture and
assert no change in `violations`, `errors`, `not_evaluated`, or `ran` ordering
or content; assert `mypy --strict` passes with the widened `validate` return
type.

**Acceptance Scenarios**:

1. **Given** any existing validator returning a bare `list[Violation]`, **When**
   the runner runs it, **Then** its findings are deduped and sorted exactly as
   before (no observable change).
2. **Given** any validator raising `NotEvaluated(reason, kind)` (a **total**
   abstention), **When** the runner runs it, **Then** it contributes one
   `not_evaluated` entry and no findings — exactly as today (form (b) is kept as
   the total-abstention shortcut).
3. **Given** the three focalized fixtures (`tiny-historical`/`tiny-novel`/
   `tiny-quest`), **When** validation runs, **Then** their emitted `violations`
   and `not_evaluated` are **byte-identical** to the current release.

---

### User Story 3 - The green predicate and gate are unchanged (Priority: P2)

The head-hopping abstention stays `pending_capability`, so it does **not** deny
green (044 predicate: only a `missing_input` entry denies green). A first-person
`warning`, when present, marks `status = violations` — a real finding — but the
CI gate still breaks only on `error`. None of 044's machinery changes; this
iteration only **consumes** it.

**Why this priority**: It preserves the correctness boundary inherited from 044.
The new partial form must not let a `pending_capability` entry leak into the
green-denial path, nor change what gates CI.

**Independent Test**: On a clean focalized fixture (no error, no warning, no
input gap), assert the documented green predicate holds despite the
`focalization` `pending_capability` entry; on a focalized project with a
first-person break, assert `status` reflects `violations` but the gate
(error-only) is unaffected.

**Acceptance Scenarios**:

1. **Given** a clean focalized project, **When** validation runs, **Then** the
   044 green predicate (`status == "ok"` AND no `not_evaluated` entry has
   `kind == "missing_input"`) holds even though `not_evaluated` lists the
   `focalization` `pending_capability` entry.
2. **Given** a focalized project with a first-person break, **When** validation
   runs, **Then** `status` is `violations` (because of the `warning`) and the CI
   gate (error-only) does **not** break.

---

### Edge Cases

- **Limited-third with a first-person break** (the new case): both surfaces fire
  at once — one `warning` citing the marker **and** the head-hop
  `pending_capability` entry. This is the path the all-or-nothing contract made
  impossible; it is now the partial form's defining test.
- **Limited-third with no first-person break** (the three current fixtures):
  zero findings + the single head-hop entry — byte-identical to today. Only the
  internal mechanism (form (c) vs. `raise`) changed.
- **Third-person non-limited (omniscient)**: unchanged — `_first_person_breaks`
  already ran here and there is no head-hopping abstention; it stays a plain
  `list[Violation]` (form (a)).
- **First-person declared voice**: unchanged — returns `[]` (evaluated, no
  findings), no abstention.
- **The four input-conditional abstentions** (no constitution / no declared
  voice / `[PENDING]` / no grammatical person): unchanged — they stay a
  **total** abstention via `raise NotEvaluated(...)` with `missing_input` and
  byte-for-byte reason strings. Partial form is **not** used here: there is no
  manuscript voice to check, so there is no deterministic half to recover.
- **A validator returning the new form with an empty `violations` list and one
  abstention**: indistinguishable in emitted output from a `raise
  NotEvaluated(...)` of the same reason/kind — both yield one `not_evaluated`
  entry and no findings. The two are interchangeable for the empty-findings case
  (that is what keeps the three current fixtures byte-identical).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The runner MUST accept **three** return shapes from a validator's
  `validate()` and normalize all three into its existing channels: (a)
  `list[Violation]` — evaluated, the findings (possibly empty); (b) a raised
  `NotEvaluated(reason, kind)` — a **total** abstention contributing one
  `not_evaluated` entry and no findings (today's shortcut, kept); (c) a **new**
  result that carries `violations` **and** one or more abstentions, each becoming
  a `not_evaluated` entry, the `violations` flowing into the findings channel.
- **FR-002**: Findings from form (c) MUST be deduped against the whole run and
  sorted by the existing total-order `sort_key` exactly as form (a)'s are; the
  abstentions from form (c) MUST be merged into `not_evaluated[]` and sorted by
  the existing `not_evaluated_sort_key` (`(validator, reason)`). No new sort key,
  channel, or envelope key is introduced.
- **FR-003**: Under a parseable third-person **limited/focalized** voice,
  `focalization` MUST run `_first_person_breaks` over the manuscript **and**
  declare the head-hopping abstention `not_evaluated` with
  `kind = pending_capability` and the **current** `_HEAD_HOPPING_PENDING` reason
  string (byte-for-byte) — both in the same run, returned via form (c). It MUST
  NOT `raise NotEvaluated` for this case any longer.
- **FR-004**: The first-person-break finding emitted under limited-third MUST be
  identical in shape to the one emitted under non-limited third today (validator
  `focalization`, `severity = warning`, the same message wording, a
  `relpath:line` `source`, `triples = ()`) — the rule itself is unchanged, only
  the path that reaches it.
- **FR-005**: The head-hopping abstention's `kind` MUST remain
  `pending_capability` (never `missing_input`); by the 044 predicate it MUST NOT
  deny green and MUST NOT trigger the `status` dormant-validator nudge. A
  first-person `warning`, when present, MUST set the run's status to `violations`
  (a real finding) without affecting the error-only CI gate.
- **FR-006**: The four input-conditional abstentions of `focalization` (no
  constitution / no declared voice / unanswered `[PENDING]` / declaration naming
  no grammatical person) MUST remain **total** abstentions raised via
  `NotEvaluated` with `kind = missing_input` and byte-for-byte unchanged reason
  strings. The first-person-voice path MUST still return `[]`; the non-limited
  third path MUST still return its `list[Violation]`.
- **FR-007**: Every validator that today returns `list[Violation]` or raises
  `NotEvaluated` MUST keep working **without being touched** (back-compat). Only
  `focalization` adopts form (c). The widened `validate` return type MUST keep
  `mypy --strict` clean across `src` and `tests`, and the `Validator` Protocol
  MUST continue to type-accept a validator that returns a bare `list[Violation]`.
- **FR-008**: `focalization` MUST remain a **single** prose validator: same name,
  registration, and discovery; `triples = ()`; no graph access; the frozen GOLEM
  ontology untouched (Constitution Principle X).
- **FR-009**: No new runtime dependency (Constitution II); stdlib only. Every
  changed source file MUST stay ≤ 500 lines.
- **FR-010**: Contract-before-code: the canonical design
  (`bookwright-design.md`, the validator-contract / `focalization` sections,
  and the § 20.6.1 determinism↔LLM frontier note) MUST be updated to document the
  partial-evaluation contract — a validator may emit findings **and** abstain in
  one run — **before** the code diverges from the written contract. The note MUST
  state plainly that `focalization` now runs the first-person-break check **and**
  abstains on head-hopping under limited-third.
- **FR-011**: The **DEBT-019** entry MUST be removed from `DEBT.md` (this
  iteration is its resolution: the partial-evaluation contract recovers the
  first-person-break check; git retains the history). The track-A closed-list
  line in `DEBT.md` that references DEBT-019 MUST be reconciled to reflect its
  closure.
- **FR-012**: The three focalized shipped fixtures (`tiny-historical`,
  `tiny-novel`, `tiny-quest`) and their pinned oracles MUST stay
  **byte-identical** — they carry the head-hop `pending_capability` entry and
  have no first-person breaks, so form (c) emits exactly today's output. Fixture
  manuscripts/constitutions MUST NOT be edited.
- **FR-013**: A **new** test case MUST exercise a first-person break **under**
  third-person-limited and assert **both** surfaces at once: (i) a `focalization`
  `warning` citing the marker, and (ii) the `focalization`
  `not_evaluated`/`pending_capability` head-hop entry. It MUST be verified
  **empirically** with `uv run pytest` (which surfaces emit what is decided
  empirically, not asserted blind).
- **FR-014**: Existing `focalization` unit tests that assert the limited-third
  case `raise`s `NotEvaluated` (e.g. the three limited-third abstention tests and
  the placeholder-replacement wake-up test) MUST be retargeted to the new form
  (c) behavior: they now assert the returned result's `violations` (empty when
  the fixture has no break) **and** its head-hop abstention, rather than a raised
  exception. The English limited-third test that today asserts the first-person
  break does **not** fire MUST be updated to assert it **now does** fire
  alongside the abstention.
- **FR-015**: The change MUST be confined to the validation runner/contract seam
  and `focalization`: approximately `validation/base.py` (the widened return
  contract / a partial-result carrier), `validation/runner.py` (normalizing the
  three forms), and `validation/validators/focalization.py` (adopting form (c)),
  plus the focalization tests and the design/DEBT docs. No other validator, no
  command, no envelope, and no ontology file changes.

### Key Entities *(include if feature involves data)*

- **Validator contract (`validate`)**: the seam between the runner and a
  validator. Today its return is `list[Violation]` (or a raised `NotEvaluated`).
  After this change it admits a third, partial shape carrying both findings and
  abstentions; the runner normalizes all three.
- **Partial result (form (c))**: the new carrier holding a validator's
  `violations` **and** its `not_evaluated` abstentions for a single run. Returned
  (not raised). Its empty-findings case is observationally equal to a `raise
  NotEvaluated`.
- **`focalization` validator**: the first and only consumer of form (c) in this
  iteration. Under limited-third it returns the first-person breaks **and** the
  head-hop abstention together.
- **`not_evaluated` entry (capability-gap)**: a `focalization` entry with
  `kind == pending_capability` and the head-hopping reason — now arriving via
  form (c) instead of a raised exception, but identical on the wire.
- **DEBT-019**: the `DEBT.md` entry for the first-person-break check dropped
  under limited-third — resolved and removed by this iteration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a project with a third-person-limited voice **and** a
  first-person break outside dialogue, `focalization` produces **exactly one**
  `warning` finding (the break, with a `relpath:line` locator) **and** **exactly
  one** `not_evaluated` entry with `kind == pending_capability` — both in the
  same run.
- **SC-002**: On a project with a third-person-limited voice and **no**
  first-person break, `focalization` produces **zero** findings and **exactly
  one** `pending_capability` `not_evaluated` entry — byte-identical to the
  current release.
- **SC-003**: The three focalized shipped fixtures (`tiny-historical`,
  `tiny-novel`, `tiny-quest`) emit `violations`, `errors`, `not_evaluated`, and
  `ran` **byte-identical** to the current release; their pinned oracles are
  unchanged.
- **SC-004**: Every validator other than `focalization` is **unmodified** and
  emits identical output on every fixture; `mypy --strict` passes with the
  widened return type; a custom validator returning a bare `list[Violation]`
  still type-checks against the `Validator` Protocol.
- **SC-005**: The 044 green predicate, the `NotEvaluatedKind` vocabulary, the
  `not_evaluated[]` serialization, the `status` nudge rule, and the error-only CI
  gate are **unchanged** — this iteration only consumes them. A clean focalized
  project stays green; a focalized project with a first-person break is
  `violations` but does not break the gate.
- **SC-006**: `DEBT.md` no longer contains a DEBT-019 entry, and the track-A
  closed-list reference to DEBT-019 is reconciled to reflect closure.
- **SC-007**: The full suite (`uv run pytest`) and all four gates (`ruff check`,
  `ruff format --check`, `mypy --strict`, `pytest` with ≥ 80% coverage) pass.

## Assumptions

- Form (c) is a **returned** value, not a raised exception: form (b) (`raise
  NotEvaluated`) is kept as the **total**-abstention shortcut, and form (c) is the
  partial shape. A validator that has nothing to evaluate at all keeps using the
  raise; a validator that evaluates one dimension and abstains on another returns
  form (c). The concrete carrier type is a `/speckit-plan` decision; this spec
  only fixes its behavior.
- The empty-`violations` form (c) and a `raise NotEvaluated` of the same
  reason/kind are observationally equivalent (both → one `not_evaluated` entry,
  no findings). This equivalence is what keeps the three focalized fixtures
  byte-identical despite `focalization` switching from raise to return.
- The trigger for the partial path is the **same precondition** the head-hopping
  heuristic ran under (and 045 abstained under): a parseable declaration whose
  grammatical person is third **and** is marked limited, whether or not a focal
  bible character is resolvable.
- Of the repo fixtures, `tiny-historical`/`tiny-novel`/`tiny-quest` are
  limited-third (they gain nothing new because they have no first-person break);
  the new both-at-once case is a **unit** test (and/or a disposable test fixture
  in the test tree), not a new shipped E2E fixture, so no pinned oracle gains a
  warning.
- `_first_person_breaks` already emits one finding per file citing the first
  break; reusing it verbatim under limited-third needs no change to the rule
  itself, only to the path that invokes it.

### Out of scope

- **Move 3** itself (track C) — head-hopping stays `not_evaluated` until then.
- Converting **other** total abstentions into partial ones — only `focalization`
  needs it today; the contract is **available** for any future consumer but not
  retrofitted. In particular `character_unknown_mentions` keeps its **total**
  abstention (its entire rule is open-set; it has no deterministic half to
  recover) — it is explicitly **not** touched.
- Any change to the green predicate or the `NotEvaluatedKind` enum (044
  delivered both; this iteration only **consumes** them).
- The prose seam, `factual_anchor`/`temporal` locators (DEBT-015 / iteration
  048, closed), the `narrative_structure` identifier (iteration 049), or any
  other validator.
- Any new runtime dependency or ontology change (Constitution II / Principle X).
