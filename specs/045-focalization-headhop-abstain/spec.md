# Feature Specification: `focalization` head-hopping stops faking — it abstains as a permanent capability-gap instead of dozing in green

**Feature Branch**: `045-focalization-headhop-abstain`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "Necesidad: el validador `focalization` … comprueba head-hopping: interioridad atribuida a un personaje que NO es el focal. El 2º dogfood (`sombra-en-el-puerto`) midió esa regla como PRÁCTICAMENTE DORMIDA (falso negativo) … Igual que 043 hizo con las menciones-desconocidas, la regla de head-hopping DEJA DE FINGIR: cuando hay una declaración focal parseable, `focalization` DECLARA `not_evaluated` con `kind=pending_capability` … La detección real es el move 3 (juicio semántico LLM, track C)."

## Context (why this iteration exists)

The `focalization` validator reads the constitution's narrative-voice
declaration. When the declared voice is **third-person limited / focalized on a
character X**, it runs a deterministic, LLM-free head-hopping check: it flags
interiority verbs (Spanish/English `pensó`/`sintió`/`recordó`/`temió`/`thought`/
`felt`/`remembered`/…) attributed to a bible character who is **not** the focal
one.

The second dogfood (`sombra-en-el-puerto`, a noir novel, 2026-06-23, a
disposable bench outside the repo) **measured that rule as practically dormant**
— a false negative. The heuristic only fires when (1) a character's **full
bible name** (`Víctor Salas`) appears, and (2) it lands on the **same physical
line** as the interiority verb. But real narrative prose names characters by
their **first name** (`Víctor`) or by epithet, and spreads a paragraph across
several physical lines, so a paragraph in unmistakable interiority of a
non-focal character does **not** trigger. Verified empirically: substituting
`Víctor` → `Víctor Salas` on the verb's line makes the head-hop fire
immediately. A validator that *looks* active but is dormant paints a misleading
green — exactly the false confidence iteration 040 set out to erase. This is
recorded as **DEBT-014**.

Issue #1 (track A — honesty) already confirmed the governing principle: a
head-hop heuristic **without semantic judgment has a precision ceiling**.
Attributing interiority to a character in real prose — first names, epithets,
cross-sentence coreference — is irreducibly semantic. So the cure is **not** to
make the heuristic better (more/looser matching is chasing a semantic problem
with more regex). Instead, exactly as iteration 043 did with the open-set
unknown-mention rule, the head-hopping rule **stops faking**: when there is a
parseable focal voice declaration, `focalization` **declares `not_evaluated`**
with `kind=pending_capability` rather than running the near-null deterministic
heuristic. The real detection is **move 3** (LLM semantic judgment, track C).

This consumes — does not change — the machinery iterations 040 and 044 already
shipped: the tri-valued verdict (040), the `not_evaluated[]` channel, the closed
`NotEvaluatedKind` vocabulary, and the refined green predicate where only
`missing_input` entries deny green and fire the dormant-validator nudge (044).
A `pending_capability` entry stays **visible** (visible gaps ≠ silence — issue
#1 doctrine) but does not knock a clean project out of green nor ask the author
for an action they cannot perform.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Head-hopping stops dozing in green; the gap becomes visible and honest (Priority: P1)

An author has a project with a third-person-limited / focalized narrative voice
declared in the constitution and clean prose. Today `focalization` runs its
near-dormant heuristic, finds nothing, and the report reads as if head-hopping
was actually checked — a false green. After this change, `focalization` reports
a single **permanent capability-gap** `not_evaluated` entry stating that
head-hopping detection requires semantic judgment (move 3) and that the
deterministic heuristic was measured nearly dormant on real prose. The author
now sees, plainly, that this dimension is **not** machine-checked.

**Why this priority**: This is the headline outcome — converting a false
negative that paints misleading green into a visible, honest gap, the false
confidence 040 was built to kill. Without it, authors keep trusting a check that
does nothing.

**Independent Test**: Run validation on a project whose constitution declares
"Tercera persona limitada, focalizada en X". Assert `focalization` produces no
`warning` finding and instead one `not_evaluated` entry whose `kind` is
`pending_capability`.

**Acceptance Scenarios**:

1. **Given** a project whose constitution declares a parseable third-person
   **limited/focalized** voice, **When** the author runs `bookwright validate`,
   **Then** `focalization` emits **no** head-hopping `warning` and **one**
   `not_evaluated` entry with `kind == pending_capability` and a reason naming
   semantic judgment / move 3.
2. **Given** that same project, **When** the author inspects the report, **Then**
   the entry is **labeled** (kind-generic tag, per the 044 render) so the gap is
   distinguishable from an input-gap — it is not silently dropped.

---

### User Story 2 - A clean focalized project stays green and asks for no impossible action (Priority: P1)

An author runs `bookwright validate` / `bookwright status` on a project with a
declared focal voice, no `error`, no `warning`, and no missing/malformed inputs.
The new `focalization` capability-gap entry **must not** deny green and **must
not** add a `next_action` — the author cannot "fix" a permanent capability gap.

**Why this priority**: This is the non-negotiable correctness boundary inherited
from 044. Using `missing_input` here would break green in **every** project that
declares a focal voice — the exact regression 044 repaired. Green must stay
reachable.

**Independent Test**: On a clean focal-voice fixture, assert the documented
green predicate (`status == "ok"` AND no `not_evaluated` entry has
`kind == "missing_input"`) is `True` even though `not_evaluated` now carries the
`focalization` capability-gap entry, and that `status`'s `next_actions` gains no
`bookwright-continuity` action for it.

**Acceptance Scenarios**:

1. **Given** a clean project with a declared focal voice, **When** the author
   runs validation, **Then** the run satisfies the refined green predicate even
   though `not_evaluated` lists the `focalization` `pending_capability` entry.
2. **Given** that same project, **When** the author runs `bookwright status`,
   **Then** `next_actions` contains **no** action prompting the author to act on
   the `focalization` gap.

---

### User Story 3 - The four input-conditional abstentions keep their actionable meaning (Priority: P2)

`focalization` already abstains for four input-conditional causes: (i) no
constitution, (ii) a constitution that declares no voice, (iii) an unanswered
`[PENDING]` voice placeholder, (iv) a declaration that names no grammatical
person. These are things the **author can fix** by declaring/answering the
voice. They must keep `kind == missing_input` (the 044 default) — so they keep
denying green and firing the dormant-validator nudge. Only the head-hopping
branch becomes a permanent capability-gap.

**Why this priority**: It preserves the actionable half of `focalization`'s
honesty contract. Mislabeling these as `pending_capability` would silence
genuinely fixable problems.

**Independent Test**: For each of the four causes, assert `focalization` raises
`not_evaluated` with `kind == missing_input` (unchanged from 044) and that
`status` still nudges the author to declare/answer the voice.

**Acceptance Scenarios**:

1. **Given** a project with no constitution / no declared voice / an unanswered
   `[PENDING]` voice / a declaration naming no grammatical person, **When** the
   author runs validation, **Then** `focalization` abstains with
   `kind == missing_input` (byte-identical reason strings to today) and the
   project is **not** green.

---

### Edge Cases

- **First-person declared voice** (e.g. `tiny-memoir`, `tiny-essay`): the
  head-hopping branch never applied. `focalization` keeps **evaluating** (it has
  nothing third-person to flag) and produces **no** `not_evaluated` entry — it is
  evaluated-with-no-findings, not abstaining. The capability-gap entry appears
  **only** when a third-person-limited/focal voice is declared.
- **Third-person, non-limited (omniscient) voice**: head-hopping never applied
  here either; the existing first-person-break check (first-person markers
  outside dialogue under a declared third person) keeps running and stays
  `evaluated`. The capability-gap abstention is scoped to the
  **limited/focalized** case — the exact precondition under which the
  head-hopping heuristic ran today.
- **A focal voice declaration with no bible character named as focal** (limited
  third, focal unresolved): this is still the limited-third precondition the
  head-hopping heuristic ran under, so it likewise abstains with
  `pending_capability` (the heuristic that would have run is the deleted one).
- **Partial evaluation is explicitly out of scope**: when a limited-third voice
  is declared, `focalization` abstains **wholly** for that run — it does not both
  emit other findings and abstain. Emitting-and-abstaining at once would require
  a new contract beyond 040/044's scope. Two things are therefore dropped for the
  limited-third case, not just the head-hopping hits: (a) the rare high-precision
  full-name-same-line head-hop hits (a 95%-dormant false green is worse than
  losing them), and (b) the still-working **first-person-break** check — which
  under a *non-limited* third-person voice keeps running. Losing (b) for the
  limited-third case is a genuine, if currently-invisible (no repo fixture
  exercises it), coverage regression; it is **not** silently accepted but recorded
  as **DEBT-019** (the all-or-nothing `NotEvaluated` contract is the cause; a
  partial-evaluation contract or move 3 closes it). See FR-015.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When `focalization` reads a **parseable third-person
  limited/focalized** voice declaration, it MUST NOT run a deterministic
  head-hopping heuristic and MUST NOT emit any head-hopping `warning`. Instead it
  MUST abstain by raising the not-evaluated signal with
  `kind = NotEvaluatedKind.pending_capability`.
- **FR-002**: The abstention reason MUST state that head-hopping / interiority
  attribution requires semantic judgment (move 3) and that the deterministic
  heuristic was measured nearly dormant on real prose (the user-supplied reason
  string: *"head-hopping / interiority attribution requires semantic judgment
  (move 3); the deterministic heuristic was measured nearly dormant on real
  prose"*).
- **FR-003**: The capability-gap entry's `kind` MUST be `pending_capability`,
  **never** the `missing_input` default. By the 044 refined predicate this entry
  MUST NOT deny green and MUST NOT trigger the `status` dormant-validator nudge.
- **FR-004**: The four existing input-conditional abstentions of `focalization`
  — (i) no constitution, (ii) no declared voice, (iii) unanswered `[PENDING]`
  placeholder, (iv) declaration naming no grammatical person — MUST remain
  `not_evaluated` with the **default** `missing_input` kind, with their reason
  strings byte-for-byte unchanged. They MUST NOT be relabeled
  `pending_capability`.
- **FR-005**: The `[PENDING]`-only guard introduced in iteration 037
  (`_PENDING_ONLY`) MUST be preserved byte-for-byte; cause (iii) still routes
  into the `missing_input` abstention.
- **FR-006**: `focalization` MUST remain a **single** validator (it is **not**
  split as `character_presence` was in 043). Only its head-hopping branch becomes
  an abstention; the validator's identity, name, registration, and discovery are
  unchanged.
- **FR-007**: The now-unused deterministic head-hopping heuristic (the
  `_head_hopping` routine and anything that **only** fed it, e.g. the interiority
  verb matcher) MUST be **deleted**, not parked "for move 3" — move 3 is a
  distinct semantic approach that does not reuse this regex; parking it is the
  speculative plumbing scope discipline forbids (mirroring 043 deleting its
  heuristic). Zero remaining consumers MUST be confirmed before deletion.
- **FR-008**: The non-head-hopping behavior of `focalization` that does not
  depend on the limited-third precondition MUST be preserved: a declared
  third-person **non-limited** voice still runs the first-person-break check and
  stays `evaluated`; a first-person voice still evaluates with no findings.
- **FR-009**: No changes to the green predicate, the `NotEvaluatedKind`
  vocabulary, the `not_evaluated[]` channel serialization, the `status` nudge
  rule, or the report render are required — this iteration only **consumes**
  `pending_capability`, which 044 already delivered.
- **FR-010**: Pinned E2E oracles (`expected-status.md`) MUST be corrected to
  match the new behavior **empirically** (verified with `uv run pytest`): a
  fixture with a declared focal voice gains a `focalization`
  `pending_capability` entry in `not_evaluated[]` that does **not** break its
  green status nor add a `next_action`. Any oracle that counted a `focalization`
  `warning` loses it. `error` counts are unchanged. Fixture
  manuscripts/constitutions MUST NOT be edited.
- **FR-011**: The **DEBT-014** entry MUST be removed from `DEBT.md` (its honesty
  half is closed here; the precision ceiling is closed by track C / move 3 — git
  retains the history).
- **FR-012**: `focalization` MUST remain a prose validator: `triples=()`, no
  graph access, the frozen GOLEM ontology untouched (Constitution Principle X).
- **FR-013**: No new runtime dependency (Constitution II); stdlib only. Every
  changed source file MUST stay ≤ 500 lines.
- **FR-014**: Contract-before-code: the canonical design (`bookwright-design.md`,
  the `focalization` section describing its abstention causes) MUST be updated to
  document the new head-hopping `pending_capability` cause **before** the
  validator diverges from the written contract. The design note MUST state plainly
  that under a limited-third voice the **whole** validator abstains (the
  first-person-break check no longer runs for that case), so the written contract
  does not over-claim.
- **FR-015**: The coverage regression that abstaining-wholly introduces — the
  deterministic first-person-break check no longer runs under a limited-third
  voice (it still runs under non-limited third) — MUST be recorded as a new
  **DEBT-019** entry in `DEBT.md` (debt class: validators are all-or-nothing, so a
  validator that can deterministically check one dimension but needs semantic
  judgment for another must abstain wholly; the partial-evaluation contract is the
  fix). It MUST NOT be left only in this spec's prose. This is the doctrine's
  "record genuinely-out-of-scope debt, never drop it" rule, not scope-widening.
- **FR-016**: Any existing unit/E2E test that asserts `focalization` **evaluates**
  (or asserts a head-hopping `warning`) on a limited-third project MUST be updated
  to the new abstention behavior, and any test that exercised the deleted
  head-hopping heuristic (FR-007) MUST be removed rather than retargeted at the
  abstention — a deleted heuristic has no behavior to assert. No test may be left
  asserting a code path that no longer exists.

### Key Entities *(include if feature involves data)*

- **`focalization` validator**: the single prose validator under change. Reads
  the constitution's narrative voice; after this change its limited-third branch
  abstains instead of running a heuristic.
- **`not_evaluated` entry (capability-gap)**: a `focalization` entry with
  `kind == pending_capability`, a reason naming move 3, and the validator's name —
  surfaced additively across the `--json` envelope, the human report,
  `status.state.validation`, and (suppressed from) `next_actions`.
- **DEBT-014**: the `DEBT.md` entry for the dormant head-hopping false negative,
  removed by this iteration.
- **DEBT-019**: the new `DEBT.md` entry opened by this iteration for the
  first-person-break check dropped under a limited-third voice (the
  all-or-nothing `NotEvaluated` contract is the cause; closed by a
  partial-evaluation contract or move 3).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On any project declaring a third-person limited/focalized voice,
  `focalization` emits **zero** head-hopping `warning` findings (down from the
  rare dormant-case hit) and **exactly one** `not_evaluated` entry with
  `kind == pending_capability`.
- **SC-002**: A clean focal-voice project (no error, no warning, no input-gap)
  satisfies the documented green predicate — verified to be **green** despite the
  new `focalization` capability-gap entry — and its `status.next_actions` gains
  **no** action attributable to that entry.
- **SC-003**: All four input-conditional `focalization` abstentions keep
  `kind == missing_input` and their reason strings are byte-for-byte unchanged
  from the current release; their green-denial and nudge behavior is unchanged.
- **SC-004**: The `tiny-historical` oracle (the only pinned `expected-status.md`)
  gains a `focalization` `pending_capability` `not_evaluated` entry; its
  `validation.counts` stay `{error: 1, warning: 1, info: 0}` and its
  `next_actions` length is unchanged (the `warning` is a `factual_anchor` finding,
  not focalization — head-hopping emits nothing on this fixture today).
- **SC-005**: First-person fixtures (`tiny-memoir`, `tiny-essay`) gain **no**
  `focalization` `not_evaluated` entry; they remain evaluated-with-no-findings.
- **SC-006**: `DEBT.md` no longer contains a DEBT-014 entry.
- **SC-007**: The full suite (`uv run pytest`) and all four gates
  (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest` with ≥ 80%
  coverage) pass.
- **SC-008**: `DEBT.md` contains a new DEBT-019 entry recording the
  first-person-break check dropped under a limited-third voice (debt class:
  validators cannot partially evaluate); its suggested resolution names a
  partial-evaluation contract or move 3.

## Assumptions

- The trigger for the capability-gap abstention is the **same precondition** the
  deleted head-hopping heuristic ran under today: a parseable declaration whose
  grammatical person is third **and** is marked limited (`limitada`/`limitado`/
  `limited`), whether or not a focal bible character is resolvable. The
  first-person-break check (third-person, any limitation) is retained for the
  non-limited case.
- Because `NotEvaluated` is all-or-nothing (no partial-evaluation contract
  exists), a limited-third declaration causes the **whole** `focalization` run to
  abstain for that project, including the first-person-break check that would
  otherwise also run under a third-person voice. Partial evaluation is out of
  scope (it is a 040/044-scale contract change); the resulting loss of the
  first-person-break check for the limited-third case is **recorded as DEBT-019**,
  not dropped (FR-015, SC-008).
- Empirical verification governs the oracle edits: head-hopping was confirmed to
  emit nothing on `tiny-historical` today, so the only oracle delta is *adding* a
  `not_evaluated` entry — no `warning` count drops in any current fixture.
- Of the repo fixtures, `tiny-historical`, `tiny-novel`, and `tiny-quest` declare
  a third-person-limited focal voice (they gain the entry); `tiny-memoir` and
  `tiny-essay` are first-person (no entry). Only `tiny-historical` carries a
  pinned `expected-status.md`; the others are covered by unit/E2E tests.

### Out of scope

- The real head-hopping detection via semantic judgment (move 3 / track C).
- A partial-evaluation contract (a validator emitting findings **and** a
  `not_evaluated` entry in one run); recorded as DEBT-019, it is the eventual fix
  for the first-person-break check this iteration drops under a limited-third
  voice.
- `validate` propagating `skipped` inputs (DEBT-018 / iteration 046).
- `character_presence` / `character_unknown_mentions` (closed in 043).
- Any change to the green predicate or the `kind` channel (delivered by 044; this
  iteration only **consumes** `pending_capability`).
