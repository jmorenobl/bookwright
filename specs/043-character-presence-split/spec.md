# Feature Specification: Split `character_presence` — orphan rule (`error`) stays; unknown-mention rule declares `not_evaluated`

**Feature Branch**: `043-character-presence-split`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "Necesidad: el validador `character_presence` tiene DOS reglas de naturaleza opuesta. (1) La regla de HUÉRFANOS (severidad `error`, protege el gate): ¿toda CHARACTER del bible se menciona en el manuscrito? Conjunto CERRADO, determinista, sólida. (2) La regla de MENCIONES-DESCONOCIDAS (severidad `warning`): ¿todo token capitalizado de la prosa tiene entrada en el bible? Conjunto ABIERTO — el problema de NER sin NER. El 2º dogfood (`sombra-en-el-puerto`) midió la regla (2) como 4 FALSOS POSITIVOS, 0 SEÑAL. La regla de menciones-desconocidas DEJA DE FINGIR: declara `not_evaluated`. Como `NotEvaluated` (040) es por-validador, se SEPARAN las dos reglas en dos validadores. …"

## Context

The `character_presence` validator bundles **two rules of opposite nature**, split today
only by severity:

- **Orphan rule** (`error`, protects the CI gate): every bible **character** must be
  mentioned somewhere in the manuscript. This is a **closed-set** check — it searches the
  prose for **known** names from the character roster — deterministic, NER-free, and
  sound. It is what gates CI.
- **Unknown-mention rule** (`warning`): every capitalized proper-noun candidate in the
  prose should have a bible entry; one that does not is flagged. This is an **open-set**
  problem — *discovering unknown* names — i.e. the NER problem attempted without NER.

The second end-to-end dogfood (`sombra-en-el-puerto`, a crime novel, 2026-06-23, a
throw-away bench outside the repo) measured the unknown-mention rule on real prose as
**4 false positives, 0 real signal**: `«Inspectora`, `«Las` (an article), `Marea` (a word
from a chapter title), `Naviera` (the head of "la Naviera Salas", an organization). Three
are surface failures and one is semantic, but all share one root cause: telling an
*undeclared proper noun* apart from an *organization / toponym / displaced article / title
word* is **irreducibly semantic** for a capitalization heuristic. No new seam (the leading
quote) and no new roster (organizations) raises that ceiling — it is chasing an open set
with closed lists. Iteration 040 already built the right channel for "I could not evaluate
this reliably": `NotEvaluated` → the additive `not_evaluated[]` channel.

Issue #1's decision (second dogfood; transcribed to `bookwright-roadmap.md § 3` and
`bookwright-design.md § 13.5`): the unknown-mention rule **stops pretending**. It no longer
emits `warning` by default; it declares `not_evaluated` with a reason that names the
open-set NER problem and points to the LLM semantic-judgment escalation (issue #1 **move
3**), which will later *replace* this abstention with real findings.

Because `NotEvaluated` (040) is **per-validator** — raising it aborts the *whole*
validator's evaluation and would discard the orphan findings — the two rules must be
**separated into two validators**: an orphan validator (`error`, always evaluated, protects
the gate) and an unknown-mention validator (which declares `not_evaluated`). The validator
registry auto-discovers both; each is then **atomically** evaluated-or-not-evaluated, which
is exactly what 040 wanted.

This iteration (043) is the **track A — honestidad** landing of the issue #1 doctrine. It
**subsumes** DEBT-011 (paired leading-quote markers) and DEBT-012 (title-body scan): those
false positives disappear not because the rule is de-noised, but because the entire rule
abstains. The deterministic per-instance patches are **discarded** (scope discipline); the
real cure is move 3 (track C, its own design).

## Clarifications

### Session 2026-06-23

- Q: The prompt expects `tiny-historical`'s unknown-mention `warning` to disappear ("1 tras
  042"). What does `character_presence` actually emit on `tiny-historical` today? → A:
  **Zero** violations of any severity (verified empirically by running the validators over
  the fixture). After iteration 042 the union roster already suppresses `Real`/`Fábrica`/
  `Paños`; the only remaining project warning (`validation.counts.warning == 1`) is
  `factual_anchor`'s under-reliable-anchor warning, **not** `character_presence`'s, and the
  `error == 1` is `factual_anchor`'s anachronism. *Consequence: this iteration does **not**
  change `tiny-historical`'s `error`/`warning` counts; the only oracle delta is the **new**
  `not_evaluated` entry for the unknown-mention validator. The prompt's "el warning de
  menciones-desconocidas se va" describes a warning that 042 already removed.*
- Q: How do the orphan findings stay "byte-for-byte identical" when the rule moves into its
  own validator? → A: The orphan validator **keeps the name `character_presence`** so every
  emitted `Violation.validator` value (part of the JSON and of the dedup/sort key) is
  unchanged; the unknown-mention rule moves to a **new** auto-discovered built-in validator
  with a distinct name. *Rationale: the gate and all pinned `error` oracles key on the
  finding's `validator` field; only a name-preserving split keeps them byte-identical.*
- Q: Under what condition does the new unknown-mention validator abstain? → A:
  **Unconditionally** — it always raises `NotEvaluated` with the open-set reason, regardless
  of whether prose or any roster is present, because the approach itself (not the inputs) is
  what is unreliable. *Consequence: every project now carries one permanent `not_evaluated`
  entry until move 3 ships, so the documented green predicate honestly reports a **known**
  gap on every project.*

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The unknown-mention dimension stops emitting false-positive warnings (Priority: P1)

An author runs validation on a finished manuscript full of organizations, toponyms,
titles, and dialogue. Today the unknown-mention rule floods the `warning` channel with
proper-noun false positives that have no real signal. After this change, **no**
unknown-mention `warning` is emitted on any manuscript; instead a single, legible
`not_evaluated` entry appears, telling the author this dimension is a known open-set gap
awaiting semantic judgment.

**Why this priority**: This is the entire defect and the issue #1 decision. The
unknown-mention rule measured as 100% noise on real prose; leaving it on erodes trust in
the whole `warning` channel. Replacing the pretence with an honest "not evaluated" is the
iteration's reason to exist.

**Independent Test**: Run validation over a project whose manuscript contains capitalized
words with no bible entry (an organization, a title word, a quoted first word). Confirm
**zero** unknown-mention `warning` findings and **one** `not_evaluated` entry naming the
unknown-mention validator with the open-set reason.

**Acceptance Scenarios**:

1. **Given** a manuscript with capitalized proper-noun candidates absent from every bible
   roster, **When** validation runs, **Then** the unknown-mention dimension emits **no**
   `warning` finding and instead contributes one `not_evaluated` entry.
2. **Given** any manuscript at all (including a clean one), **When** validation runs,
   **Then** the unknown-mention validator declares `not_evaluated` — it never emits a
   `warning` by default.
3. **Given** `tiny-historical`, **When** validation runs, **Then** the unknown-mention
   validator contributes one `not_evaluated` entry; `validation.counts` (`error: 1`,
   `warning: 1`) is **unchanged** because that error and warning are both `factual_anchor`'s
   and `character_presence` already emitted zero on this fixture after 042.

---

### User Story 2 - The orphan rule (`error`) is untouched and still gates CI (Priority: P1)

The orphan rule keeps deriving exclusively from the **character** roster, stays always
evaluated, and emits its `error` findings **byte-for-byte identical** to before — same
message, severity, source, and `validator` name. A bible character never mentioned in the
manuscript is still an `error` that fails the gate.

**Why this priority**: The orphan rule is what gates CI. Any change to its output — even
the `validator` name on its findings — would be a behavior change to the gate, which is
explicitly out of scope and dangerous. This is non-negotiable, exactly as in 040/042.

**Independent Test**: Run validation over the existing fixtures and confirm the set of
`error`-level findings is byte-for-byte unchanged (including each finding's `validator`
field); confirm an unmentioned character still produces exactly one `error`.

**Acceptance Scenarios**:

1. **Given** the existing fixtures, **When** validation runs, **Then** every `error`-level
   finding is byte-for-byte identical to before this change, including its `validator` name.
2. **Given** a bible character never mentioned in the manuscript, **When** validation runs,
   **Then** it is reported as exactly one `error`, citing the character's bible file,
   unchanged from today.
3. **Given** the CI gate (only `error` breaks CI), **When** the change ships, **Then** the
   gate's pass/fail behavior on every fixture is identical to before.

---

### User Story 3 - Each validator is atomically evaluated-or-not (Priority: P1)

After the split, every validator's verdict is atomic: the orphan validator is **always
evaluated** (so it always emits its `error` findings), and the unknown-mention validator
**always declares `not_evaluated`**. Raising `NotEvaluated` in one no longer silences the
other — the exact problem 040 set out to solve.

**Why this priority**: The whole point of separating the rules is to let the gate-protecting
orphan check run while the open-set check honestly abstains. If a single validator carried
both, abstaining would discard the orphans (per-validator `NotEvaluated`), re-introducing
the bug 040 created the channel to avoid.

**Independent Test**: Run validation over a project with both a never-mentioned character
and unknown proper nouns. Confirm the orphan `error` **and** the unknown-mention
`not_evaluated` entry both appear in the same run.

**Acceptance Scenarios**:

1. **Given** a project with a never-mentioned character and off-roster proper nouns,
   **When** validation runs, **Then** the run reports the orphan `error` **and** the
   unknown-mention `not_evaluated` entry together (neither suppresses the other).
2. **Given** the orphan validator's existing abstention condition (no manuscript prose
   **and** an empty character roster), **When** validation runs, **Then** it declares
   `not_evaluated` with the **identical** reason string preserved from iteration 040/042.

---

### User Story 4 - The `not_evaluated` reason is legible and surfaces through the existing channels (Priority: P2)

The `not_evaluated` reason names the open-set NER problem and points to move 3, so the
documented green predicate (`status == "ok" AND not_evaluated == []`) honestly reflects that
open-set discovery is a **known** gap, not something silently absent. The entry appears in
every channel 040 wired — the `--json` `not_evaluated[]`, the human report, `bookwright
status`'s `state.validation`, and `next_actions` — with **no new channel** introduced.

**Why this priority**: The honesty is the deliverable. A terse or hidden reason would leave
authors guessing why no proper-noun warnings appear. Reusing 040's channels keeps the
contract stable.

**Independent Test**: Run `validate --json` and `bookwright status` over any project and
confirm the unknown-mention validator's `not_evaluated` entry, with a non-empty reason
naming the open-set/move-3 cause, appears in both.

**Acceptance Scenarios**:

1. **Given** any project, **When** `validate --json` runs, **Then** `not_evaluated[]`
   contains an entry for the unknown-mention validator with a non-empty reason that names
   the open-set proper-noun-discovery problem and references move 3 (semantic judgment).
2. **Given** any project, **When** `bookwright status` runs, **Then** the same `not_evaluated`
   state is visible through the channel 040 wired, with no new channel added.
3. **Given** any project, **When** the green predicate `status == "ok" AND not_evaluated ==
   []` is evaluated, **Then** it is `False` for every project (the open-set gap is a known,
   honestly-reported hole) until move 3 ships.

---

### Edge Cases

- **A clean manuscript**: the unknown-mention validator still declares `not_evaluated` (it
  abstains unconditionally on the approach, not on the inputs), so even a defect-free
  project is never "green" by the documented predicate until move 3.
- **No manuscript prose and an empty character roster**: the *orphan* validator declares
  `not_evaluated` with the identical 040/042 reason; the *unknown-mention* validator also
  declares `not_evaluated` with the open-set reason. Two distinct entries, two distinct
  reasons.
- **Gate**: `not_evaluated` is never a finding and never gates — the `validate` exit code
  and the CI gate (only `error` breaks CI) are unchanged.
- **Custom-validator config**: the new built-in validator is discovered like every other
  built-in; an author may `disable` it via the `[validators]` block exactly as with any
  built-in (no special-casing).
- **The dialogue dash (DEBT-009/041) and the union roster (DEBT-010/042)**: those landed in
  the *orphan*/deterministic path and the prose seam; both remain in effect and unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The unknown-mention dimension MUST NOT emit any `warning` finding by default
  on any manuscript. In its place it MUST declare itself *not-evaluated*.
- **FR-002**: The two rules MUST be separated so each is **atomically** evaluated-or-not:
  the orphan rule always evaluated and emitting its findings, the unknown-mention rule
  declaring `not_evaluated`. The validator registry MUST auto-discover both as built-ins,
  active by default (an author may disable either via the existing `[validators]` block).
- **FR-003**: The orphan rule MUST keep deriving **exclusively** from the character roster
  and MUST emit its `error` findings **byte-for-byte identical** to before this change —
  including each finding's `validator` field. (Implication: the orphan validator retains the
  name `character_presence`; the unknown-mention validator takes a new, distinct name.)
- **FR-004**: The orphan validator MUST retain the existing `NotEvaluated` guard — it
  declares not-evaluated only when there is no manuscript prose **and** an empty character
  roster — with the **identical reason string** preserved from iteration 040/042 (042's
  FR-007).
- **FR-005**: The unknown-mention validator MUST declare `not_evaluated` **unconditionally**
  (regardless of prose or any roster), with a single legible reason that names the open-set
  proper-noun-discovery (NER-without-NER) problem and references move 3 (semantic judgment):
  e.g. "open-set proper-noun discovery requires semantic judgment (move 3); the deterministic
  heuristic was measured insufficient on real prose."
- **FR-006**: The `not_evaluated` entry MUST surface through the **existing** iteration-040
  channels — the `--json` `not_evaluated[]`, the human validation report, `bookwright
  status`'s `state.validation`, and `next_actions` — with **no new channel** introduced.
- **FR-007**: Gate semantics MUST NOT change: only `error` breaks CI; `not_evaluated` is
  never a finding and never gates; the `validate` exit code is unchanged.
- **FR-008**: The documented green predicate (`status == "ok" AND not_evaluated == []`) MUST
  now evaluate to `False` for every project (because the unknown-mention validator always
  contributes a `not_evaluated` entry), honestly reflecting open-set discovery as a known
  gap until move 3.
- **FR-009**: The prose seam (`io/prose.py`) MUST NOT be touched or deleted — it continues to
  serve the deterministic validators. The leading paired-quote markers (DEBT-011) MUST NOT be
  added and the title-body exemption (DEBT-012) MUST NOT be applied; those false positives
  disappear because the whole rule abstains, not because it is de-noised.
- **FR-010**: The DEBT-011 and DEBT-012 entries MUST be removed from `DEBT.md` (subsumed by
  the rule's move to `not_evaluated`; git preserves history).
- **FR-011**: The `tiny-historical` status oracle (`expected-status.md`) MUST be corrected to
  document the **new** `not_evaluated` entry for the unknown-mention validator, **without**
  editing the fixture's manuscript or bible. `validation.counts` (`error: 1`, `warning: 1`,
  `info: 0`) MUST stay **byte-identical** — both the error and the warning are
  `factual_anchor`'s; `character_presence` already contributed zero on this fixture after
  042, so there is no count to lower (the same oracle-correction discipline 042/041 applied,
  but here the delta is the added `not_evaluated` entry, not a lowered count).
- **FR-012**: Zero functional regression MUST be verified **empirically** via the full test
  suite (`uv run pytest`). Fixtures that assert only `error == 0` (`tiny-novel`,
  `tiny-memoir`) MUST NOT be edited; they tolerate the new `not_evaluated` entry without a
  pinned count.
- **FR-013**: Both validators MUST remain prose validators: each emits **no triples**
  (`triples=()`), requires **no built graph**, and leaves the frozen GOLEM ontology untouched
  (Principle X — no new class, no `.ttl` edit). **No new dependency** (Constitution II). Every
  changed source file MUST stay within the 500-line limit (Principle IV).
- **FR-014**: The behavior changes MUST be proven by tests: the orphan `error` still fires
  (synthetic project with a never-mentioned character) and the unknown-mention validator
  declares `not_evaluated` (synthetic project), built on the existing
  `tests/validation/conftest.py` `write_project`/`load_context` pattern. The existing
  `character_presence` test module MUST be migrated to the split shape so neither validator
  ships without coverage (Principle VIII).
- **FR-015**: The move 3 LLM evaluator, an opt-in deterministic mode of the rule, the
  `focalization` head-hopping defect (DEBT-014), and `validate` propagating a `skipped`
  count (DEBT-018) MUST NOT be implemented here (out of scope; see Out of Scope).

### Key Entities *(include if feature involves data)*

- **Orphan validator** (`character_presence`, `error`): the closed-set check that every bible
  character is mentioned. Always evaluated (except its preserved no-prose/no-roster
  `NotEvaluated` guard). Protects the CI gate. Name unchanged so its findings are byte-stable.
- **Unknown-mention validator** (new built-in, distinct name): the open-set check that no
  longer pretends. Always declares `not_evaluated` with the open-set reason; emits no
  findings by default. Auto-discovered, active by default, disable-able like any built-in.
- **`not_evaluated` entry**: a `(validator, reason)` record in the iteration-040 channel — the
  honest signal that open-set proper-noun discovery is a known gap awaiting move 3.
- **Green predicate**: `status == "ok" AND not_evaluated == []` (040). Now universally `False`
  until move 3, by design.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a manuscript containing capitalized words with no bible entry (organization,
  title word, quoted first word), the count of unknown-mention `warning` findings is **0**
  (today each such word produces one).
- **SC-002**: On every project, exactly one `not_evaluated` entry for the unknown-mention
  validator is present, with a non-empty reason naming the open-set/move-3 cause.
- **SC-003**: The set of `error`-level findings across the full test suite is byte-for-byte
  identical before and after the change (0 added, 0 removed, 0 changed), including each
  finding's `validator` field.
- **SC-004**: A bible character never mentioned still produces exactly **1** `error`; the CI
  gate's pass/fail outcome on every fixture is unchanged.
- **SC-005**: On `tiny-historical`, `validation.counts` is byte-identical (`error: 1`,
  `warning: 1`, `info: 0`) and the oracle gains exactly one documented `not_evaluated` entry;
  the fixture's manuscript and bible are unedited.
- **SC-006**: The documented green predicate evaluates to `False` on every project after the
  change (the unknown-mention `not_evaluated` entry is always present).
- **SC-007**: All four CI gates (lint, format, type-check, test suite with ≥80% coverage)
  pass; `DEBT.md` no longer contains a DEBT-011 or DEBT-012 entry.
- **SC-008**: Both validators emit **0** triples and require **no** built graph; the frozen
  GOLEM ontology closure is byte-unchanged (no class added, no `.ttl` edited); `io/prose.py`
  is unmodified; and every source file changed by this iteration is **≤500** lines — all
  checkable directly (`triples` stay `()`, `git diff` over `resources/schemas/golem-1.1/`,
  `golem.ttl`, and `io/prose.py` is empty, and `wc -l` on each changed file is ≤500).

## Assumptions

- **Empirically verified**: `character_presence` emits **0** violations on `tiny-historical`
  today (post-042). The `tiny-historical` `{error: 1, warning: 1}` totals are entirely
  `factual_anchor`'s (the anachronism `error` and the under-reliable-anchor `warning`, both
  pinned in `expected-findings.md`). Therefore this iteration adds a `not_evaluated` entry but
  changes **no** count — diverging from the prompt's framing that a `character_presence`
  warning would be removed (042 already removed it).
- The orphan validator keeps the name `character_presence` so existing `error` findings (and
  the gate that keys on the `validator` field) stay byte-identical; the unknown-mention
  validator takes a new distinct built-in name (the plan selects the exact name).
- The unknown-mention validator abstains **unconditionally** because the open-set approach,
  not the inputs, is what is unreliable — so the `not_evaluated` entry is permanent on every
  project until move 3 replaces it with real findings.
- 040's channels (`--json` `not_evaluated[]`, human report, `status` `state.validation`,
  `next_actions`) already render any validator's `not_evaluated` result; reusing them needs no
  new plumbing.
- The orchestration E2E asserts `validation.counts` (unchanged here); the new oracle
  `not_evaluated` documentation is additive and the test surface may be extended to assert it
  (a plan/tasks decision), but is not required to change the gate.

## Dependencies

- Iteration 040 (tri-valued result / `NotEvaluated` → `not_evaluated[]`) — the channel this
  iteration routes the unknown-mention rule into; must remain intact.
- Iteration 042 (union roster, DEBT-010) — already removed the setting/location/object false
  positives from the deterministic path; explains why `tiny-historical` counts are unchanged
  here.
- The validator registry's auto-discovery of built-ins (no hand-registration) — the mechanism
  that surfaces the new validator without wiring.
- Issue #1's decision, transcribed to `bookwright-roadmap.md § 3` and `bookwright-design.md
  § 13.5` — the durable record this iteration implements.

## Out of Scope

- **Move 3** — the LLM semantic-judgment evaluator that will *replace* this `not_evaluated`
  with real findings (issue #1 track C; its own design).
- **An opt-in deterministic mode** of the unknown-mention rule — discarded by scope
  discipline; would be additive if ever demanded.
- **`focalization` head-hopping** (DEBT-014, iteration 044) — same honesty class, its own
  patch.
- **`validate` propagating a `skipped` count** (DEBT-018, iteration 045) — its own iteration.
- **The leading paired-quote seam (DEBT-011) and the title-body exemption (DEBT-012)** — not
  patched per-instance; subsumed by the rule's move to `not_evaluated` and removed from
  `DEBT.md`.
