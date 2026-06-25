# Feature Specification: Move 3 third dimension, first half — `focalization` declares an honest first-person-recall abstention + the abstention `code` discriminator

**Feature Branch**: `053-move3-first-person-honesty`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "Necesidad: la TERCERA dimensión del move 3 —la ruptura de 1ª persona (recall pro-drop, DEBT-021)— se parte en DOS iteraciones, igual que el head-hopping se partió en honestidad (045) y juicio (052). ESTA iteración (053) es la mitad de HONESTIDAD + el plumbing de contrato que la habilita; la siguiente (054) será el JUICIO en `bookwright-continuity`… (see the iteration prompt in `bookwright-implementation-plan.md`)"

## Context & Background

This is the **first half of the third move-3 dimension** — the 1st-person break /
recall ceiling driven by Spanish pro-drop morphology (**DEBT-021**). It deliberately
splits that dimension into **two iterations**, exactly as head-hopping was split into
**honesty** (iteration 045 / 050 — the deterministic heuristic was deleted and the
abstention declared) and **judgment** (iteration 052 — the skill picks up the
abstention and judges). **This iteration (053) is the HONESTY half plus the contract
plumbing that the honesty half forces.** The **judgment** half — the sixth axis of
`bookwright-continuity` and its own `status` nudge, which **closes DEBT-021** — is
**iteration 054** and is out of scope here.

Today, under a declared **third-person** voice, `focalization` runs its deterministic
first-person-break check (`_first_person_breaks`). That check matches **only the
explicit subject pronoun** (`yo` / `nosotros` / `nosotras` / `i` / `we`) — a **closed
set**, solid, with near-zero false positives. But the real question — "does this prose
**slip into** first person?" — is, in pro-drop Spanish, **verbal morphology** (`Caminé`,
`Me senté`, `Escribí`), an **open set** no regex captures without reopening the
whack-a-mole the issue #1 doctrine closed (DEBT-021). Today `focalization` does **not
declare** that ceiling: it runs the explicit-pronoun check, emits its `warning`s, and is
**silent** about everything the closed set cannot see — **false completeness**, the very
`[]`-means-clean lie that issue #1 banished, at the sub-check level.

This iteration makes `focalization` **declare that ceiling honestly**: it adds a
`pending_capability` `Abstention` saying *complete first-person recall requires semantic
judgment (move 3); the deterministic check covers only the explicit pronoun*, **while
preserving** the explicit-pronoun `warning`s unchanged (the solid deterministic core —
design § 20.6.1 principle 3: determinism **adds** confidence, never **suppresses**).

**But this forces a contract change.** Under third-person *limited*, `focalization` now
emits **two** `pending_capability` abstentions in one run: head-hopping (iterations
050 / 052) **and** the new first-person-recall one. The post-052 `status` keying —
`_judges(validator)` = `r.validator == validator AND r.kind is pending_capability` —
**cannot tell them apart**: the head-hopping nudge (052) would **also fire** on the
first-person abstention, and under third-person-**non-limited** (where the first-person
break exists but head-hopping does **not**) it would **mis-fire**. So this iteration
adds a **stable discriminator** to abstentions — a short `code` — so that multiple
abstentions from the **same validator** become distinguishable, and re-points the
existing move-3 nudges (051, 052) at their `code`.

This iteration does **three** things:

1. **CONTRACT** — `Abstention` (and its serialized twin `NotEvaluatedResult`) gain an
   **optional** `code: str | None = None`, a short stable discriminator (e.g.
   `"head_hopping"`, `"first_person_recall"`, `"undeclared_characters"`). The runner
   stamps it: the form (c) `EvalResult` path passes `abstention.code`; the form (b)
   `raise NotEvaluated` path leaves `code=None`. It is serialized **additively** in
   `not_evaluated[]` (a new key, exactly as iteration 044 added `kind` — no field is
   renamed or retyped). The `raise NotEvaluated` **exception itself does NOT gain
   `code`** (the discriminator belongs to **returned** abstentions, form (c)); its
   `NotEvaluatedResult.code` is `None`.
2. **HONESTY** — `focalization` declares the first-person-recall abstention in **both**
   third-person branches. Under third-person *limited*, its `EvalResult` now carries
   **two** abstentions — `Abstention(_HEAD_HOPPING_PENDING, pending_capability,
   code="head_hopping")` **and** `Abstention(_FIRST_PERSON_RECALL_PENDING,
   pending_capability, code="first_person_recall")` — alongside the `_first_person_breaks`
   violations. Under third-person *non-limited*, what is a bare `list` today becomes
   `EvalResult(_first_person_breaks(...), [Abstention(_FIRST_PERSON_RECALL_PENDING,
   pending_capability, code="first_person_recall")])`. The **first-person branch**
   (`return []`) and the **four** `raise NotEvaluated` `missing_input` causes are
   **untouched** (the recall abstention is about *third-person* prose slipping into
   first — it does not apply when the declared voice is already first person). The
   explicit-pronoun `warning`s stay **byte-for-byte**.
3. **KEYING** — the discriminator enters `status`: `_judges` keys by **(validator,
   code)** — `r.validator == validator AND r.kind is pending_capability AND r.code ==
   code`. `judge_undeclared_characters` is re-pointed to
   `_judges("character_unknown_mentions", "undeclared_characters")` (byte-identical: that
   source emits only that one abstention) and `judge_head_hopping` to
   `_judges("focalization", "head_hopping")` (**now precise**: it does **not** fire on the
   first-person abstention). **No first-person nudge is added yet** — that is iteration
   054, when the skill that answers it exists.

## Clarifications

### Session 2026-06-25

- Q: Should the `code` discriminator be added to the `NotEvaluated` **exception** as
  well as to the returned `Abstention`? → A: **No.** Only the returned `Abstention`
  (form (c)) and its stamped `NotEvaluatedResult` gain `code`. The `raise NotEvaluated`
  exception (form (b)) keeps its `(reason, kind)` signature; the runner stamps
  `code=None` for it. Rationale: a raised total abstention is one-per-validator and never
  needs intra-validator disambiguation; only a validator that **returns multiple
  abstentions** (form (c) `EvalResult`) needs the discriminator (the minimal contract
  surface — doctrine § 3, do not add plumbing without a consumer).
- Q: Is `code` required or optional, and what happens to abstentions that don't set it
  (the existing `raise NotEvaluated` `missing_input` causes, and any future returned
  abstention that omits it)? → A: **Optional**, defaulting to `None`. Every
  `not_evaluated[]` entry carries the `code` key (additive, like 044's `kind`); entries
  from `raise NotEvaluated` serialize `code: null`. Rationale: additive and
  backward-compatible — no existing field changes name or type, and an abstention that
  needs no discriminator simply leaves it `None`.
- Q: With `focalization` now emitting **two** `pending_capability` abstentions, how must
  the `status` keying change so the 052 head-hopping nudge fires on **only** the
  head-hopping one? → A: Generalize `_judges` to key on **(validator, code)** — add
  `AND r.code == code` to the existing `validator == … AND kind is pending_capability`
  predicate. Re-point `judge_undeclared_characters` to
  `_judges("character_unknown_mentions", "undeclared_characters")` (byte-identical
  behavior — that source emits only that abstention) and `judge_head_hopping` to
  `_judges("focalization", "head_hopping")`. Rationale: the discriminator is exactly what
  name-only keying cannot express; the change is the minimal precise predicate.
- Q: Does this iteration add a `status` nudge for the new first-person-recall abstention?
  → A: **No.** A nudge is added only once a skill exists to answer it; that is iteration
  054 (the judgment half, which closes DEBT-021). This iteration's first-person
  abstention is **honestly visible** in `not_evaluated[]` but has **no** `next_action`
  yet — the same staging head-hopping went through (045 honesty → 052 judgment).
  Rationale: no signposted dead-end nudge before a destination exists (scope discipline).
- Q: Is DEBT-021 removed by this iteration? → A: **No.** Its **judgment** half is still
  pending (iteration 054). DEBT-021's text is **updated** to note that the honest recall
  abstention now exists (053) and the judgment is deferred to 054 — exactly as 045 made
  head-hopping honest and 052 added its judgment. Rationale: the debt class is not closed
  until the semantic judgment lands.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - `focalization` stops faking completeness on first-person recall (Priority: P1)

An author has written a multi-POV novel in **third-person limited**. One chapter
(`03-dolors.md`) slips sustainedly into first person through verbal morphology (`cerré la
escuela`, `Caminé hasta`, `Me senté`) **without** ever writing `yo` / `nosotros` — a real
break of the declared voice that the explicit-pronoun check **cannot** see. They run
`bookwright validate --json`. The report now carries an honest `not_evaluated` entry from
`focalization`: `{validator: focalization, kind: pending_capability, code:
first_person_recall, reason: …}` — declaring that complete first-person recall is a
semantic-judgment capability gap (move 3), while the explicit-pronoun `warning`s it
already emits stay exactly as before. The validator no longer pretends the absence of
`yo` means the prose is in third person.

**Why this priority**: This is the whole point of the honesty half — it ends the
sub-check `[]`-means-clean lie for the first-person dimension, the same lie issue #1
banished elsewhere. It makes the recall ceiling **visible** so the judgment half (054)
has a contract entry to pick up, mirroring how 045 made head-hopping honest before 052
judged it.

**Independent Test**: Empirically via `uv run pytest`. A third-person fixture (limited or
non-limited) gains a `not_evaluated` entry with `validator=focalization`,
`kind=pending_capability`, `code=first_person_recall`; its explicit-pronoun `warning`s are
unchanged; and the first-person-voice fixture and the four `missing_input` causes gain no
such entry.

**Acceptance Scenarios**:

1. **Given** a project whose constitution declares a third-person **limited** voice,
   **When** `bookwright validate --json` runs, **Then** `not_evaluated[]` carries **two**
   `focalization` entries — one `code=head_hopping` and one `code=first_person_recall`,
   both `kind=pending_capability` — alongside any explicit-pronoun `warning`s, and those
   `warning`s are byte-for-byte unchanged from before this iteration.
2. **Given** a project whose constitution declares a third-person **non-limited** voice,
   **When** `bookwright validate --json` runs, **Then** `not_evaluated[]` carries exactly
   **one** `focalization` entry, `code=first_person_recall`, `kind=pending_capability` (no
   `head_hopping` entry, since head-hopping is scoped to limited-third), alongside any
   explicit-pronoun `warning`s.
3. **Given** a project whose declared voice is **first person**, **When** `bookwright
   validate --json` runs, **Then** `focalization` emits **no** first-person-recall
   abstention (the recall ceiling is about third-person prose slipping into first; it does
   not apply here) — the `return []` branch is unchanged.
4. **Given** a project with **no constitution / no declared voice / a `[PENDING]`
   placeholder / a declaration naming no grammatical person**, **When** `bookwright
   validate --json` runs, **Then** `focalization` still raises `NotEvaluated`
   (`missing_input`) for that cause and the resulting `not_evaluated` entry carries
   `code: null` (the four `missing_input` causes are untouched and gain no `code`).

---

### User Story 2 - Multiple abstentions from one validator stay distinguishable on the wire and in `status` (Priority: P1)

The contract that two layers share — `not_evaluated[]` — must let a consumer tell apart
two abstentions that come from the **same** validator. With `focalization` now emitting
**both** a head-hopping and a first-person-recall `pending_capability` abstention, every
`not_evaluated` entry carries a stable `code`, and `bookwright status` keys its move-3
nudges on that `code`. The head-hopping nudge (052) fires on **only**
`code=head_hopping`, never on the first-person abstention; under third-person-non-limited
(first-person-recall present, head-hopping absent) the head-hopping nudge does **not**
fire — the exact mis-fire this contract prevents. No first-person nudge is emitted yet.

**Why this priority**: Without the discriminator, the 052 head-hopping nudge would fire
on the new first-person abstention and mis-fire under non-limited third — a regression in
the move-3 discoverability loop the moment `focalization` emits a second abstention.
Keying by `code` is what keeps each nudge precise as the abstention set grows.

**Independent Test**: Empirically via `uv run pytest`, at the pure `test_rules.py`
synthetic-state level (state → actions, no disk) **and** the e2e fixture level. Positive:
a `(focalization, pending_capability, head_hopping)` abstention fires the head-hopping
nudge. Negatives: a `(focalization, pending_capability, first_person_recall)` abstention
**alone** fires **no** head-hopping nudge; a `(focalization, missing_input)` abstention
fires no head-hopping nudge.

**Acceptance Scenarios**:

1. **Given** a validation report carrying a `focalization` abstention with
   `kind=pending_capability` and `code=head_hopping`, **When** `bookwright status` runs,
   **Then** the head-hopping `next_action` (052) is present.
2. **Given** a report whose **only** `focalization` `pending_capability` abstention is
   `code=first_person_recall` (head-hopping absent — e.g. third-person-non-limited),
   **When** `bookwright status` runs, **Then** the head-hopping `next_action` is
   **absent** (the mis-fire this contract prevents) and **no** first-person `next_action`
   is emitted.
3. **Given** a report carrying a `character_unknown_mentions` abstention (always
   `pending_capability`, `code=undeclared_characters`), **When** `bookwright status` runs,
   **Then** the iteration-051 undeclared-character `next_action` is present and unchanged
   (the re-pointed predicate is byte-identical for that source).
4. **Given** a flawless third-person project (no errors, no `missing_input` abstentions),
   **When** `bookwright status` runs, **Then** the project is still **GREEN** — the new
   `first_person_recall` `pending_capability` entry is permanently visible but never
   degrades green.

---

### Edge Cases

- **Declared voice is first person**: the first-person-recall abstention does **not**
  apply (the ceiling is about third-person prose slipping into first); `return []` is
  unchanged, and no `code=first_person_recall` entry appears.
- **Third-person-limited**: `focalization` emits **two** `pending_capability` abstentions
  (`head_hopping` **and** `first_person_recall`) in one `EvalResult`, plus any
  explicit-pronoun `warning`s.
- **Third-person-non-limited**: `focalization` emits **one** `pending_capability`
  abstention (`first_person_recall` only), plus any explicit-pronoun `warning`s; the bare
  `list` return becomes an `EvalResult`.
- **`raise NotEvaluated` `missing_input` causes** (no constitution / no voice /
  `[PENDING]` / no grammatical person): unchanged; their `NotEvaluatedResult.code` is
  `None` and serializes as `code: null`.
- **A consumer that ignores `code`**: the field is additive and optional; existing
  consumers that read only `validator` / `kind` / `reason` are unaffected.
- **The new abstention and green**: a `pending_capability` entry never degrades green
  (iteration 044 predicate); a flawless third-person project stays GREEN with the
  `first_person_recall` entry permanently visible.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `Abstention` MUST gain an **optional** field `code: str | None = None`, a
  short stable discriminator distinguishing multiple abstentions returned by the **same**
  validator (e.g. `"head_hopping"`, `"first_person_recall"`, `"undeclared_characters"`).
- **FR-002**: `NotEvaluatedResult` (the serialized twin) MUST gain the same optional
  `code: str | None = None` and serialize it **additively** in its `to_json()` (a new key
  alongside `validator` / `reason` / `kind`, exactly as iteration 044 added `kind`). **No**
  existing field is renamed or retyped.
- **FR-003**: The runner MUST stamp `code` through the **same single naming point** that
  stamps `validator` and `kind`: the form (c) `EvalResult` path MUST pass
  `abstention.code`; the form (b) `raise NotEvaluated` path MUST leave `code=None`. The
  stamping authority MUST NOT fork.
- **FR-004**: The `NotEvaluated` **exception** (form (b)) MUST NOT gain a `code` field —
  the discriminator belongs to **returned** abstentions (form (c)) only. Its stamped
  `NotEvaluatedResult.code` is `None`.
- **FR-005**: Every `not_evaluated[]` JSON entry MUST carry the `code` key. Entries
  originating from `raise NotEvaluated` MUST serialize `code: null`; entries from a
  returned `Abstention` that sets `code` MUST serialize that value.
- **FR-006**: `focalization` MUST declare a **first-person-recall** abstention
  (`Abstention(<reason>, kind=pending_capability, code="first_person_recall")`) under
  **both** third-person branches. The reason MUST state that complete first-person recall
  requires semantic judgment (move 3) and that the deterministic check covers only the
  explicit subject pronoun.
- **FR-007**: Under third-person **limited**, `focalization`'s `EvalResult` MUST carry
  **both** the head-hopping abstention (`code="head_hopping"`, iterations 050 / 052) **and**
  the new first-person-recall abstention (`code="first_person_recall"`), alongside the
  `_first_person_breaks` violations.
- **FR-008**: Under third-person **non-limited**, `focalization` MUST return an
  `EvalResult(_first_person_breaks(...), [Abstention(<recall>, pending_capability,
  code="first_person_recall")])` — replacing today's bare `list[Violation]` return — and
  MUST NOT carry a head-hopping abstention (head-hopping is scoped to limited-third).
- **FR-009**: The **first-person voice** branch (`return []`) and the **four** `raise
  NotEvaluated` `missing_input` causes (no constitution / no declared voice / `[PENDING]`
  placeholder / no grammatical person) MUST be **untouched**: the recall abstention does
  not apply to a declared first-person voice or to an input gap.
- **FR-010**: The explicit-pronoun first-person-break `warning`s (`_first_person_breaks`,
  matching the closed set `yo` / `nosotros` / `nosotras` / `i` / `we`) MUST stay
  **byte-for-byte unchanged**. The deterministic core is **preserved**, not modified or
  widened (design § 20.6.1 principle 3 — determinism adds, never suppresses).
- **FR-011**: The explicit-pronoun regex MUST NOT be widened or changed to chase verbal
  morphology — that is the whack-a-mole issue #1 closed (DEBT-021); the open-set recall is
  the **judgment** layer's job (move 3), not a bigger regex.
- **FR-012**: The `status` keying helper `_judges` MUST be generalized to key on
  **(validator, code)** — its predicate becomes `r.validator == validator AND r.kind is
  NotEvaluatedKind.pending_capability AND r.code == code`. It takes the `code` as a second
  argument.
- **FR-013**: `judge_undeclared_characters` MUST be re-pointed to
  `_judges("character_unknown_mentions", "undeclared_characters")`. This MUST be
  **byte-identical in behavior** to the iteration-052 name-only keying (that source emits
  only the `undeclared_characters` abstention). `character_unknown_mentions` MUST therefore
  set `code="undeclared_characters"` on the abstention it returns.
- **FR-014**: `judge_head_hopping` MUST be re-pointed to `_judges("focalization",
  "head_hopping")`, so it fires on **only** the head-hopping abstention and **never** on
  the new first-person-recall abstention. The head-hopping `Abstention` MUST set
  `code="head_hopping"`.
- **FR-015**: **No `status` nudge** for the first-person-recall abstention is added in
  this iteration. The abstention is honestly visible in `not_evaluated[]` but has no
  `next_action` yet (that is iteration 054, the judgment half).
- **FR-016**: The iteration-044 green predicate (`GREEN = status ok AND no not_evaluated
  entry has kind == missing_input`) MUST stay **byte-for-byte unchanged**; the new
  `pending_capability` abstention MUST NOT degrade green. `activate_dormant_validators`
  MUST remain `missing_input`-only.
- **FR-017**: The CI gate MUST NOT change: only `error` findings break CI, and **no
  `error`** is born from this change. `focalization` MUST remain a **prose** validator
  (`triples=()`), with no change to the frozen ontology (Principle X) and no new dependency
  (Constitution II).
- **FR-018**: The relevant oracles MUST be updated and verified **empirically** with `uv
  run pytest`: the `base` tests (the new `code` field + default), the serialization tests
  (`code` key additive; `code: null` for raised abstentions), the runner tests (`code`
  stamped from form (c), `None` from form (b)), the `focalization` validator tests (the new
  abstention under both third-person branches; first-person and `missing_input` branches
  untouched; explicit-pronoun `warning`s unchanged), and the `status` rule tests (keying by
  `code`, **including** the negative third-person-non-limited case → no head-hop nudge). The
  *quality* of any LLM judgment is NOT in scope here (no skill changes in this slice).
- **FR-019**: The third-person fixtures' `not_evaluated[]` MUST gain the
  `first_person_recall` entry, and **every** `not_evaluated[]` entry across the fixtures
  MUST gain the `code` key (raised ones carry `code: null`). Fixtures that are GREEN MUST
  stay GREEN, byte-identical except for the additive `code` keys and the new
  `first_person_recall` entry.
- **FR-020**: `DEBT-021` MUST NOT be removed. Its text MUST be **updated** to record that
  the honest first-person-recall abstention now exists (053) and that the **judgment**
  half (the sixth `bookwright-continuity` axis + its nudge) is deferred to 054 — mirroring
  how 045 made head-hopping honest and 052 judged it.
- **FR-021**: The design / milestone record MUST be reconciled: the contract addition
  (abstention `code`) and the `focalization` first-person-recall honesty MUST be reflected
  in `bookwright-design.md` (§ 13.x / § 20.6.x as appropriate) and the milestone prose /
  iteration index (row 053), noting that the judgment half is 054.
- **FR-022**: Each changed file MUST stay ≤ 500 lines.

### Key Entities *(include if feature involves data)*

- **`Abstention` (returned, form (c))**: a validator's per-dimension conscious skip
  carried inside an `EvalResult`. Gains an optional `code` discriminator so a validator
  that returns **multiple** abstentions keeps them distinguishable. Carries
  `(reason, kind, code)`.
- **`NotEvaluated` (raised, form (b))**: the total-abstention exception. Unchanged signature
  `(reason, kind)`; the runner stamps its `NotEvaluatedResult.code` as `None`.
- **`NotEvaluatedResult` (serialized)**: the recorded, name-stamped abstention surfaced in
  the `not_evaluated` channel. Gains `code: str | None`, serialized additively as a new
  JSON key (`code: null` when absent).
- **`code` discriminator**: a short stable string (e.g. `head_hopping`,
  `first_person_recall`, `undeclared_characters`) identifying *which* abstention a
  validator emitted — the new key in the data contract between the deterministic layer and
  the `status` / skill consumers, needed because a single validator (`focalization`) now
  emits **two** `pending_capability` abstentions.
- **First-person-recall abstention**: `focalization`'s new honest declaration that complete
  first-person recall (pro-drop morphology) is a move-3 capability gap; `kind=pending_capability`,
  `code=first_person_recall`; emitted under both third-person branches; the contract entry
  iteration 054 will pick up.
- **`status` `_judges(validator, code)` predicate**: keys a move-3 judge nudge on a
  `(validator, kind=pending_capability, code)` triple, so two abstentions from the same
  validator drive distinct (or no) nudges.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Under a declared third-person voice (limited **or** non-limited), `bookwright
  validate --json` carries a `not_evaluated` entry `{validator: focalization, kind:
  pending_capability, code: first_person_recall, reason: …}`; under third-person-limited
  it coexists with the `head_hopping` entry (two `focalization` entries) — verified via
  `uv run pytest`.
- **SC-002**: **Every** `not_evaluated[]` entry carries a `code` key; entries from `raise
  NotEvaluated` carry `code: null`; entries from returned `Abstention`s carry their set
  `code` — verified empirically.
- **SC-003**: The explicit-pronoun first-person-break `warning`s are byte-for-byte
  unchanged, and the explicit-pronoun regex is unchanged — verified empirically.
- **SC-004**: `bookwright status` fires the head-hopping nudge on **only** a
  `(focalization, pending_capability, head_hopping)` abstention; the negative
  third-person-non-limited case (`first_person_recall` present, `head_hopping` absent)
  fires **no** head-hopping nudge; the iteration-051 undeclared-character nudge is
  unchanged; **no** first-person nudge is emitted — verified empirically.
- **SC-005**: A flawless third-person project stays **GREEN**; the iteration-044 green
  predicate is byte-for-byte unchanged and `activate_dormant_validators` stays
  `missing_input`-only.
- **SC-006**: The CI gate (error-only) is unchanged and **no `error`** is born from this
  change; `focalization` stays a prose validator (`triples=()`); the frozen ontology and
  the dependency set are untouched.
- **SC-007**: `DEBT-021` is still present in `DEBT.md`, with its text updated to record the
  053 honesty and the 054 judgment deferral.
- **SC-008**: The full suite and all four gates (`ruff check`, `ruff format --check`,
  `mypy --strict`, `pytest` with ≥ 80 % coverage) pass green.

## Assumptions

- The `status` aggregator builds its `not_evaluated` directly from the runner's
  `NotEvaluatedResult` tuple (no JSON round-trip), so once the runner stamps `code` the
  `status` state's entries carry it and `_judges` can key on it without further plumbing.
- The discriminator is a free-form short string owned by each validator; there is no
  closed enum for `code` in this slice (a `StrEnum` would be speculative — only three
  values exist and they live with their validators). If a registry is later warranted it
  is its own change.
- `character_unknown_mentions` already emits exactly one `pending_capability` abstention;
  setting its `code="undeclared_characters"` keeps the 051/052 nudge behavior byte-identical.
- `focalization` declares the head-hopping abstention only under limited-third (iteration
  050); the first-person-recall abstention applies under both third-person branches but not
  under first person or input gaps.
- The first-person-recall abstention has **no** consumer nudge in this slice; its consumer
  (the sixth `bookwright-continuity` axis) arrives in iteration 054.

## Out of Scope

- The **judgment half** of the first-person dimension — the sixth `bookwright-continuity`
  axis that judges pro-drop first-person breaks, plus its own `status` nudge — which
  **closes DEBT-021**. That is **iteration 054**.
- Widening or changing the explicit-pronoun regex / `_first_person_breaks` to chase verbal
  morphology — the whack-a-mole issue #1 closed; the deterministic core is **preserved
  verbatim**.
- **Gating** an LLM verdict (golden-runs / per-hash cache → an `error` that vetoes merge),
  deferred with its own activation condition (§ 20.6.2 decision 4).
- The iterations-051/052 axes (undeclared characters, head-hopping) — intact; only their
  `status` keying is re-pointed to the `code` and `character_unknown_mentions` sets its
  `code`.
- Touching `bookwright-verify`, or making **any** skill change in this slice (the
  first-person judgment is 054).
- Reopening the iteration-044 green predicate.
- Removing any `DEBT.md` entry (DEBT-021 stays open; its text is updated, not deleted).
- Adding any dependency (Constitution II), touching the frozen ontology (Principle X), or
  creating / modifying a validator under `validation/` beyond `focalization`'s honest
  abstention and the shared `base`/`runner` contract field.
- Introducing a closed enum / registry for `code` values (speculative — only three exist).
- Each changed file MUST stay ≤ 500 lines.
