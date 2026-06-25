# Feature Specification: Move 3 third dimension, second half (judgment) — judge first-person breaks in `bookwright-continuity`; close DEBT-021

**Feature Branch**: `054-move3-first-person-judgment`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "Necesidad: la TERCERA dimensión del move 3 —ruptura de 1ª persona (DEBT-021)— aterriza su mitad de JUICIO, cerrando la dimensión (la mitad de honestidad la dio 053). Es el espejo de 052 (head-hopping) sobre la OTRA abstención de `focalization`… (see the iteration prompt in `bookwright-implementation-plan.md`)"

## Context & Background

This is the **second half of the third move-3 dimension** — the 1st-person break /
pro-drop recall ceiling (**DEBT-021**) — and it **closes that dimension**. The
**honesty** half landed in iteration 053: `focalization` now declares its recall
ceiling honestly with a `pending_capability` `Abstention(_FIRST_PERSON_RECALL_PENDING,
code="first_person_recall")` under **any** declared third-person voice ("complete
first-person recall requires semantic judgment (move 3); the deterministic check only
covers the explicit subject pronoun"), while preserving the explicit-pronoun `warning`s
(`yo` / `nosotros`). **This iteration (054) makes `bookwright-continuity` JUDGE that
dimension**, restoring the lost signal — exactly as iteration 052 picked up the
head-hopping abstention 045/050 had declared.

This **completes the first wave of move 3**: the three open-set dimensions —
characters-used-but-undeclared (051), head-hopping (052), and first-person break
(053 honesty + 054 judgment) — are now all **judged** by `bookwright-continuity`,
anchored in the authored graph / source, with the CLI staying fully deterministic
(no LLM in CI).

This is the **mirror of iteration 052** over the **other** `focalization` abstention.
The standing decisions it reuses (`bookwright-design.md` § 20.6.2, design pass of
2026-06-24 after the 3rd dogfood `el-año-de-las-casas-vacías`):

- The judgment layer is an **Agent Skill** — `bookwright validate` stays fully
  deterministic with **no LLM dependency** (Constitution II).
- The existing `bookwright-continuity` skill is **extended** (no new skill created).
- The `not_evaluated` channel is the **contract between the two layers**: every
  `Abstention(kind=pending_capability)` that `bookwright validate` publishes is a
  *judgment task* the skill picks up and answers, anchored in the authored source.
- Since iteration 053, abstentions carry a stable `code` discriminator so two
  abstentions from the **same** validator stay distinguishable, and the `status`
  move-3 nudges key on `(validator, code)`.

The dimension of this slice is the **1st-person break / voice slip**: under a
declared **third-person** voice, does the prose **slide into first person**? The
deterministic core (`focalization`'s explicit-pronoun `warning`s) matches only the
**closed** subject-pronoun set (`yo` / `nosotros` / `nosotras` / `i` / `we`). But in
**pro-drop** Spanish the natural way to slip into first person is **verbal
morphology** without a pronoun (`Caminé`, `Me senté`, `Escribí`, `cerré`) — an **open
set** no regex captures without reopening the whack-a-mole issue #1 closed. The 3rd
dogfood measured this gap **lost, not theoretical**: `manuscript/03-dolors.md:3-13`,
a sustained, flagrant first-person passage under a declared third-person-limited
voice, produced **zero** findings because no `yo` / `nosotros` appears. This slice
makes `bookwright-continuity` **judge** that dimension — including the morphological
recall the deterministic check cannot see — restoring the signal.

The grounding (§ 20.6.2 decision 3) is the **declared narrative voice**
(`bible/constitution.md`) — that, and only that, is needed: the 1st-person break is a
question of **grammatical person**, not character identity, so it needs **neither the
roster nor the POV calendar** (unlike head-hopping). It applies to **all** declared
third person (limited **or** non-limited), unlike head-hopping, which is scoped to
limited-third.

## Clarifications

### Session 2026-06-25

- Q: The 6th axis judges grammatical person, not character identity. Which grounding
  inputs does it read, and does it need the roster or the POV calendar like the 5th
  (head-hopping) axis? → A: **Only the declared narrative voice** (`bible/constitution.md`,
  already in the skill's "Archivos a leer" for the 5th axis — reuse it, add **no** new
  file). It needs **neither the roster nor the POV calendar**: the 1st-person break is
  grammatical person, not character identity. It applies under **all** third person
  (limited **or** non-limited), unlike head-hopping (limited-only). Under a declared
  **first-person** voice it does **not** apply (the prose IS first person — nothing to
  report). Rationale: the grounding is exactly what the dimension needs and nothing more
  (scope discipline; mirrors how 052 named voice + POV calendar + roster because
  head-hopping needs character identity, which this dimension does not).
- Q: The skill `description` is at **1000 / 1024** chars (24 slack) — there is no room
  for new ES/EN trigger phrases. How is the 1st-person trigger added? → A: **Fold** it
  under the existing 5th-axis voice/focalization trigger **without growing** — e.g. widen
  «head-hopping / saltos de punto de vista / focalización rota» to also cover «rupturas de
  voz / persona narrativa» (and the EN twin "head-hopping / POV breaks" to cover "voice /
  narrative-person breaks") — or compress the existing text without losing **any** axis's
  trigger. The result MUST stay ≤ 1024 and be mirrored **verbatim** into
  `SKILL_DESCRIPTIONS["bookwright-continuity"]` (the equality gate
  `tests/integrations/test_descriptions.py` must stay green). Rationale: the hard cap
  forbids new triggers; the 1st-person dimension is the same "voice/focalization" family
  as head-hopping, so one widened trigger covers both without growth.
- Q: Where does the new `judge_first_person_recall` rule sit in the priority-ordered
  `RULES` table, and does `_judges` need changing? → A: **Immediately after
  `judge_head_hopping` and before `define_focus`**, so the three move-3 judge nudges are
  adjacent and the emitted `next_actions` order stays deterministic. `_judges` is **not**
  changed — iteration 053 already generalized it to key on `(validator, code)`; this slice
  only **adds a third peer `Rule`** keyed on `_judges("focalization", "first_person_recall")`.
  Rationale: the contract plumbing is already in place (053); this is purely the skill +
  one new nudge rule (the mirror of 052's `judge_head_hopping`).
- Q: Which fixture exercises the green-preserving 1st-person nudge, and where does the
  negative (first-person-voice → no nudge) case live? → A: **Reuse `tiny-historical`** —
  it declares third-person *limited* and, since iteration 053, already carries the
  `(focalization, pending_capability, first_person_recall)` abstention in
  `expected-status.md`; this slice flips its `next_actions` skills list **5 → 6** (a fourth
  `bookwright-continuity` nudge) while green stays. **No new fixture.** The negative case (a
  declared-first-person project where `focalization` emits no `first_person_recall`
  abstention gains no nudge) is covered at the pure `test_rules.py` synthetic-state level
  (the rules module is `state → actions`, no disk); `tiny-novel` / `tiny-memoir` stay
  GREEN. Rationale: no speculative fixture (scope discipline); pure-unit coverage for the
  negative path, mirroring 052.
- Q: Does this slice touch the deterministic `focalization` validator or the `code`
  contract? → A: **No.** Iteration 053 already added the `first_person_recall` abstention
  and the `code` discriminator. This slice is **skill + status only**: the 6th axis in
  `bookwright-continuity` and the `judge_first_person_recall` nudge. There are **zero**
  changes under `validation/`, and `code` / `_judges` are untouched. Rationale: the
  honesty/judgment split (mirroring 045/050 → 052) deliberately put the contract work in
  053 so the judgment half is a clean skill + nudge addition.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The author surfaces a first-person voice slip the validator could only abstain on (Priority: P1)

An author has written a novel in **third person**. One chapter (`03-dolors.md`) slips
sustainedly into first person through verbal morphology (`cerré la escuela`, `Caminé
hasta`, `Me senté`, `Escribí`) **without** ever writing `yo` / `nosotros` — a real break
of the declared voice the explicit-pronoun check **cannot** see. They ask their agent to
"check my manuscript against the bible" (or "revisa rupturas de voz / persona
narrativa"). The agent runs the extended `bookwright-continuity` skill, which reads the
**declared narrative voice** from `bible/constitution.md` (confirming it is third person —
if it were first person, the axis would not apply and nothing is reported), walks the
manuscript **outside dialogue**, and **judges** whether the narration slides into first
person — **including** the pro-drop verbal morphology the deterministic check misses. It
reports the passage as one more continuity deviation: the manuscript quote, "first-person
voice under a narration declared in third person", and a suggestion (rewrite in third
person, or confirm the voice).

**Why this priority**: This is the whole point of the slice — it restores a real,
measured signal (the sustained pro-drop first-person passage in `03-dolors.md`) that the
honest deterministic abstention (053) had to silence. It proves the move-3 pipeline for
the third dimension (`validate` abstains → continuity picks up the abstention → judges
anchored in the declared voice → reports) and **completes the first wave of move 3**.

**Independent Test**: Materialize the `bookwright-continuity` skill, confirm the new 6th
axis ("1st-person break / voice slip") is present in its `## Procedimiento` and `##
Output` sections, cites the **declared voice** as grounding, and that the skill still
passes the lint gate. The *quality* of the LLM judgment is **not** unit-asserted (as with
`bookwright-verify` / `bookwright-continuity` today); what is testable is that the skill
materializes, lints (≤ 1024), triggers, and documents the grounding.

**Acceptance Scenarios**:

1. **Given** a project whose constitution declares a third-person voice (limited **or**
   non-limited), **When** the author runs the `bookwright-continuity` skill, **Then** the
   skill's procedure directs the agent to read the declared voice, walk the manuscript
   outside dialogue, and report each passage that narrates in first person — including
   pro-drop verbal morphology without an explicit pronoun — as a deviation with a
   manuscript quote, the phrase "first-person voice under a narration declared in third
   person", and a remediation suggestion (rewrite in third person, or confirm the voice).
2. **Given** a project whose declared voice is **first person**, **When** the skill runs,
   **Then** its procedure instructs the agent that the 1st-person break axis does **not
   apply** (the prose IS first person) and reports nothing for this axis.
3. **Given** a project with **no constitution / no declared voice / a `[PENDING]`
   placeholder**, **When** the skill runs, **Then** its procedure directs the agent to
   report the grounding gap (no declared voice to anchor on) and **not** to guess.
4. **Given** the materialized skill, **When** the lint gate runs, **Then** `name` ≤ 64
   chars (matching its directory), `description` ≤ 1024 chars, and valid YAML front-matter
   all pass — and **no** existing axis's trigger (4th / 5th) is lost by the description
   change.

---

### User Story 2 - The author discovers *how* to get the first-person judgment (Priority: P1)

An author runs `bookwright status` on a third-person project where `focalization` has
declared its first-person-recall abstention (`not_evaluated`, `kind=pending_capability`,
`code=first_person_recall`). Status now surfaces **one** `next_action` pointing to
`bookwright-continuity` as the way to *obtain* that semantic judgment. The nudge is
**informative**: it does **not** degrade the project's green status, it is **distinct**
from the iteration-051 undeclared-character and iteration-052 head-hopping nudges, and the
`code` keying keeps the three precisely separated (the first-person nudge never fires on
the head-hopping abstention, and vice versa).

**Why this priority**: Without the discoverability loop, the first-person abstention 053
made honest is a dead end — the author has no signposted way to reach the judgment the
skill now provides. Closing the loop is what makes the contract between layers usable end
to end for this dimension, completing the first move-3 wave.

**Independent Test**: Empirically via `uv run pytest`. A third-person project carries the
`(focalization, pending_capability, first_person_recall)` abstention and therefore gains
exactly one new first-person continuity `next_action` while staying GREEN. The
**negative** cases are explicitly tested: (a) a declared-first-person project (no
`first_person_recall` abstention) does **not** receive the nudge; (b) the new nudge keys
on `code=first_person_recall` only — it does **not** fire on the head-hopping abstention
(`code=head_hopping`) and the head-hopping nudge does **not** fire on the first-person
one; (c) green is preserved in all cases.

**Acceptance Scenarios**:

1. **Given** a project whose validation report carries a `not_evaluated` entry from
   `focalization` with `kind=pending_capability` and `code=first_person_recall`, **When**
   `bookwright status` runs, **Then** the `next_actions` list includes exactly one action
   pointing to `bookwright-continuity` for the first-person judgment, distinct from the
   051 undeclared-character and 052 head-hopping actions.
2. **Given** a project whose **only** `focalization` `pending_capability` abstention is
   `code=head_hopping` (no `first_person_recall` — not reachable under current
   `focalization`, but asserted at the synthetic-state level), **When** `bookwright status`
   runs, **Then** the first-person `next_action` is **absent** (the `code` keeps the
   nudges separate).
3. **Given** a third-person-limited project carrying **both** `focalization`
   `pending_capability` abstentions (`head_hopping` **and** `first_person_recall`) plus the
   `character_unknown_mentions` abstention, **When** `bookwright status` runs, **Then**
   `status` emits **all three** move-3 continuity actions — undeclared-character (051),
   head-hopping (052), and first-person (054) — each coherent and distinct.
4. **Given** a flawless third-person project (no errors, no `missing_input` abstentions),
   **When** `bookwright status` runs, **Then** the project is still **GREEN** — the new
   first-person action is informative and never degrades green (the iteration-044 green
   predicate stays byte-for-byte unchanged).

---

### Edge Cases

- **Declared voice is first person**: the 1st-person break axis does **not** apply (the
  prose IS first person); the skill reports nothing for this axis, and `focalization`
  emits no `first_person_recall` abstention (053), so the status nudge is naturally absent.
- **Declared voice is third-person non-limited (omniscient-but-third)**: the 1st-person
  break axis **does** apply (unlike head-hopping, which is limited-only); `focalization`
  emits the `first_person_recall` abstention and the nudge fires.
- **No `bible/constitution.md` / no declared voice / a `[PENDING]` voice**: the declared
  voice is unknown, so the agent cannot anchor the judgment; it reports the grounding gap
  rather than guessing. (At the `status` level, that gap is `focalization`'s
  `missing_input` abstention, covered by `activate_dormant_validators`, not by this nudge.)
- **A project with no manuscript yet**: the skill behaves as today — reports "missing
  prerequisite" (nothing to verify); the new axis simply finds no prose to scan.
- **Both / all three move-3 abstentions present** (a limited-third project carries
  `character_unknown_mentions`, `focalization` head-hopping, **and** `focalization`
  first-person-recall): `status` emits **all three** continuity actions, each coherent and
  distinct, never merged and never redundant.
- **The agent cannot judge (offline / no model)**: the correct resting state is the
  `not_evaluated` the validator already emits (053) — the permanent track-A fallback. The
  skill *improves* the signal when it runs; its absence breaks nothing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `bookwright-continuity` skill MUST gain a **sixth axis** — "1st-person
  break / voice slip" — documented in its `## Procedimiento` and `## Output` sections. The
  existing five axes (bible compliance, character-arc coherence, timeline coherence,
  undeclared characters, head-hopping) MUST be preserved.
- **FR-002**: The new axis's procedure MUST instruct the agent to (a) read the **declared
  narrative voice** from `bible/constitution.md` and proceed with the axis **only** under a
  declared **third-person** voice — **limited OR non-limited** (under a declared
  **first-person** voice the axis does **not** apply: the prose IS first person — report
  nothing); (b) walk the manuscript **outside dialogue**; (c) **judge** whether the
  narration slides into first person, **including** the pro-drop verbal morphology without
  an explicit pronoun (`Caminé`, `Me senté`, `Escribí`) that the deterministic check (only
  `yo` / `nosotros`) does not see; and (d) when the declared voice is **absent or
  unresolved** (no `bible/constitution.md`, no voice declaration, or a `[PENDING]`
  placeholder), **report the grounding gap and do NOT guess** the voice.
- **FR-003**: The procedure MUST cite the **grounding** (§ 20.6.2 decision 3): the
  **declared narrative voice** (`bible/constitution.md`). The axis MUST NOT require the
  roster or the POV calendar — the 1st-person break is grammatical person, not character
  identity (it needs neither, unlike the head-hopping axis).
- **FR-004**: The skill MUST report each first-person slip as **one more deviation** in
  the continuity report: a manuscript quote, the phrase "first-person voice under a
  narration declared in third person" (`voz de 1ª persona bajo una narración declarada en
  3ª`), and a suggestion (rewrite in third person, or confirm the voice).
- **FR-005**: The new axis MUST **preserve** the deterministic explicit-pronoun core: it
  **adds** the morphological recall on top of (never suppresses) `focalization`'s
  explicit-pronoun `warning`s (`yo` / `nosotros`) — design § 20.6.1 principle 3,
  determinism adds confidence, never suppresses.
- **FR-006**: The skill `description` MUST trigger on first-person prompts (ES/EN — e.g.
  "revisa rupturas de voz / persona narrativa", "check for voice / narrative-person
  breaks") **without** exceeding 1024 characters. Because the description is at 1000 / 1024
  today (24 chars of slack), the new trigger MUST be **folded under the existing 5th-axis
  voice/focalization trigger** (e.g. widen «head-hopping / saltos de punto de vista /
  focalización rota» and its EN twin to also cover «rupturas de voz / persona narrativa»)
  **without growing**, or by compressing the existing text **without losing any axis's
  trigger** (4th and 5th included).
- **FR-007**: The materialized skill MUST pass the lint gate: `name` ≤ 64 chars and equal
  to its parent directory, `description` ≤ 1024 chars, valid YAML front-matter.
- **FR-008**: The skill MUST remain **read-only and POST-draft** (like all of continuity):
  it writes nothing to the project.
- **FR-009**: `bookwright status` MUST add **one** `next_action` pointing to
  `bookwright-continuity` (for the first-person judgment) when the validation report
  carries a `not_evaluated` entry whose **source validator** is `focalization`, **kind is
  `pending_capability`**, **and** `code == "first_person_recall"`. The rule MUST be keyed
  via the existing `_judges("focalization", "first_person_recall")` predicate (iteration
  053 already generalized `_judges` to `(validator, code)` — it is **not** changed here).
  The new `judge_first_person_recall` rule MUST sit **immediately after
  `judge_head_hopping` and before `define_focus`** in the priority-ordered table, so the
  emitted `next_actions` order is deterministic.
- **FR-010**: The new first-person `next_action` MUST have its **own** `prompt`/`reason`,
  **distinct** from the iteration-051 undeclared-character and iteration-052 head-hopping
  actions. When all three move-3 abstentions are present, `status` MUST emit **all three**
  actions, each coherent and distinct.
- **FR-011**: The first-person nudge MUST key precisely on `code=first_person_recall` — it
  MUST NOT fire on the head-hopping abstention (`code=head_hopping`), and the head-hopping
  nudge (052) MUST NOT fire on the first-person abstention. The `code` discriminator (053)
  keeps the two same-validator `focalization` nudges separated.
- **FR-012**: That `next_action` MUST be **informative**: it MUST NOT degrade green. The
  iteration-044 green predicate (`GREEN = status ok AND no not_evaluated entry has
  kind == missing_input`) MUST stay byte-for-byte identical; a `pending_capability` entry
  MUST NOT tumble green. The 044 green regression MUST NOT be reopened, and
  `activate_dormant_validators` MUST remain `missing_input`-only.
- **FR-013**: The deterministic validator `focalization` MUST NOT be touched: it already
  declares the `first_person_recall` abstention (iteration 053). There MUST be **zero
  changes** to anything under `validation/`, and the abstention `code` contract / `_judges`
  helper MUST NOT change.
- **FR-014**: The CI gate MUST NOT change: only `error` findings break CI, and **no
  `error` is ever born from an LLM** (§ 20.6.2 decision 4 — judgment, not gate).
- **FR-015**: The widened `description` MUST be mirrored **verbatim** into
  `SKILL_DESCRIPTIONS["bookwright-continuity"]` in `integrations/descriptions.py`, so the
  source frontmatter and the in-code mirror never diverge. This is enforced by the existing
  equality gate `tests/integrations/test_descriptions.py`. The mirror edit MUST be made
  together with the FR-006 widening, and the result MUST stay ≤ 1024 chars.
- **FR-016**: The grounding documentation for the declared-voice source
  (`bible/constitution.md`) MUST be documented **inline in the skill body** (the 6th axis in
  `## Procedimiento` + reuse of the existing "Archivos a leer" entry for
  `bible/constitution.md`, already present for the 5th axis). **No new file** (a
  `references/` file or a `bible/` file) MUST be created — the declared voice is already
  read by the skill.
- **FR-017**: The oracles that assert the skill body / materialization, the activation
  (bilingual trigger) oracle, the description equality gate, and the `status` rule oracles
  MUST be updated. The skill-body oracle MUST gain a **sixth-axis assertion** mirroring the
  existing fourth/fifth-axis oracles (`test_continuity_carries_the_fourth_undeclared_character_axis`
  / `test_continuity_carries_the_fifth_head_hopping_axis` in `tests/resources/test_command_body.py`):
  it MUST assert the 6th axis is present in `## Procedimiento` / `## Output`, names the
  first-person / voice-slip judgment, cites the **declared voice** (`bible/constitution.md`)
  as its grounding, and carries the exact deviation phrasing (FR-004). The *quality* of the
  LLM judgment MUST NOT be asserted in unit tests. All behavior MUST be verified empirically
  with `uv run pytest`, **including the negative cases**: (a) a declared-first-person project
  does not receive the first-person nudge; (b) the nudge keys on `code=first_person_recall`
  only (does not fire on `head_hopping`, and the head-hopping nudge does not fire on
  `first_person_recall`); (c) green is preserved. The e2e green-preserving fixture is the
  **existing `tiny-historical`** (it declares third-person *limited* and, since iteration
  053, already carries the `(focalization, pending_capability, first_person_recall)`
  abstention; **no new fixture is added**). Updating `tiny-historical/expected-status.md` is
  **not** a YAML-only edit: because it is a **co-located prose + YAML** oracle, the same edit
  MUST keep the human-readable prose and the inline `# nudge:` comment block internally
  consistent with the new state — (i) the YAML `next_actions` skills list goes **5 → 6** (a
  fourth `bookwright-continuity` nudge); (ii) the prose enumerating the workstreams ("enumera
  **cinco** workstreams… **tercer** `bookwright-continuity`") becomes **seis** / a **fourth**
  `bookwright-continuity`, naming the new first-person judgment nudge alongside the 051/052
  ones; (iii) the convergence-frame prose ("las acciones `verify`/`continuity` (las **tres**)…
  `len(next_actions)` **sigue siendo 5**") becomes **las cuatro** / **6**; and (iv) the inline
  `# nudge:` / iteration comments gain the 054 first-person rule. Leaving any of (ii)–(iv)
  stale while flipping (i) is a forbidden internally-inconsistent oracle. The negative case
  (a) is covered at the pure `test_rules.py` synthetic-state level, no disk. `tiny-novel` /
  `tiny-memoir` stay GREEN.
- **FR-018**: `DEBT-021` MUST be reconciled in `DEBT.md` **following the existing
  closed-debt convention** (git keeps the history): its honesty half landed in 053 and its
  judgment half lands here, so the dimension is **complete**. Concretely, (a) the **open
  `### DEBT-021` section** under `## Deuda abierta` MUST be **removed**; AND (b) the **Track C
  — move 3** bullet of the issue-#1 re-disposición closed-debt summary blockquote (the one
  already recording `~~DEBT-013~~`) MUST record it as a
  **struck-through closed entry** — `~~DEBT-021~~ (cerrada en la iteración 054 …)` — mirroring
  exactly how `~~DEBT-013~~` / `~~DEBT-015~~` / `~~DEBT-017~~` are recorded there, **replacing**
  the now-false forward-looking sentence "Queda DEBT-021 … plegado con el head-hopping para
  rebanadas posteriores de move 3" (leaving that stale forward reference is a forbidden
  internally-inconsistent record). The 054 closed-record summary MUST state the grounding is
  the **declared voice only** (no roster, no POV calendar — superseding the open entry's
  older "voz declarada + roster + calendario de POV" phrasing). The design / milestone record
  MUST be reconciled: `bookwright-design.md` § 20.6.2 / § 13.5 marks the third move-3
  dimension (first-person break) as **landed** and the **first move-3 wave complete** (051 +
  052 + 053/054), and the milestone prose / iteration index (row 054) is updated to reflect
  shipped work.
- **FR-019**: No new dependency (Constitution II) MUST be added; no validator (Principle X
  frozen ontology) MUST be created or modified beyond the (untouched) `focalization`; each
  changed file MUST stay ≤ 500 lines.

### Key Entities *(include if feature involves data)*

- **Declared narrative voice**: read from `bible/constitution.md`; the 6th axis applies
  **only** when it is declared **third person** (limited or non-limited). It is the
  **single** grounding input — no roster, no POV calendar — because the 1st-person break is
  grammatical person, not character identity.
- **`not_evaluated` entry (`Abstention`, `validator=focalization`, `kind=pending_capability`,
  `code=first_person_recall`)**: the data-level contract between the deterministic layer and
  the skill layer for this dimension (declared by iteration 053). The validator names the
  recall ceiling; the skill closes it with the declared voice as grounding.
- **Continuity deviation (1st-person break)**: a reported finding pairing a manuscript
  quote with the "first-person voice under a narration declared in third person" phrasing
  and a remediation suggestion — one more deviation in the continuity report; **adds** the
  pro-drop morphological recall on top of the preserved explicit-pronoun `warning`s.
- **Status `next_action` (first-person)**: an informative recommendation pointing to
  `bookwright-continuity` when a `(focalization, pending_capability, first_person_recall)`
  abstention exists; never degrades green; distinct from the 051 undeclared-character and
  052 head-hopping actions, separated by `code`.
- **`judge_first_person_recall` rule**: a third peer `Rule` in the `status` `RULES` table,
  keyed via `_judges("focalization", "first_person_recall")`, sitting immediately after
  `judge_head_hopping` and before `define_focus`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The `bookwright-continuity` skill materializes and passes the lint gate with
  the (folded, non-growing) `description` (≤ 1024 chars) and the new 6th axis present in
  `## Procedimiento` and `## Output`, citing the declared voice as grounding, and the
  procedure documenting the absent/`[PENDING]`-voice grounding-gap handling (report the
  gap, do not guess — FR-002 (d)).
- **SC-002**: The skill triggers on first-person prompts in both ES and EN (folded under
  the voice/focalization trigger), verified by the activation oracle, and the
  iteration-051 undeclared-character and iteration-052 head-hopping triggers still fire.
- **SC-003**: A project whose validation report carries the `(focalization,
  pending_capability, first_person_recall)` abstention gains **exactly one** new
  `bookwright-continuity` first-person `next_action` (distinct from the 051 and 052
  actions) while keeping its green status — verified via `uv run pytest`
  (`tiny-historical` `next_actions` skills list 5 → 6, with the co-located prose and inline
  `# nudge:` comments of `expected-status.md` updated in the same edit so the oracle stays
  internally consistent — FR-017).
- **SC-004**: The first-person nudge keys on `code=first_person_recall` only: a
  declared-first-person project (no such abstention) does **not** gain the nudge; the nudge
  does **not** fire on a `code=head_hopping` abstention and the head-hopping nudge does
  **not** fire on a `code=first_person_recall` abstention — verified empirically as
  negative cases.
- **SC-005**: A flawless project stays GREEN after this change; the iteration-044 green
  predicate is byte-for-byte unchanged and `activate_dormant_validators` stays
  `missing_input`-only; `tiny-novel` / `tiny-memoir` stay GREEN.
- **SC-006**: The deterministic `focalization` validator is unchanged (zero diff under
  `validation/`); the abstention `code` contract and the `_judges` helper are unchanged;
  the CI gate (error-only) is unchanged and no `error` originates from an LLM. The
  iteration-051 and iteration-052 nudges remain intact.
- **SC-007**: `DEBT-021` is reconciled in `DEBT.md` per the closed-debt convention — the
  open `### DEBT-021` section is **removed** and the Track-C bullet of the issue-#1
  re-disposición closed-debt summary blockquote records it as a struck-through
  `~~DEBT-021~~ (cerrada en la iteración 054 …)` entry (no stale forward-looking reference remains) — and `bookwright-design.md` § 20.6.2 / § 13.5 records the third move-3
  dimension landed and the first move-3 wave complete.
- **SC-008**: The full suite and all four gates (`ruff check`, `ruff format --check`,
  `mypy --strict`, `pytest` with ≥ 80 % coverage) pass green.

## Assumptions

- The semantic-judgment quality is exercised by the agent at runtime, not asserted in unit
  tests — consistent with how `bookwright-verify` / `bookwright-continuity` are tested today.
- The discoverability `next_action` is added by adding a **third peer move-3 judge rule**
  keyed on `(focalization, first_person_recall)` via the existing `_judges(validator, code)`
  helper (already `(validator, code)`-keyed since iteration 053); the contract plumbing is
  already in place, so this slice is purely the skill + one nudge rule.
- `bible/constitution.md` is an authored prose file already read by the skill (the 5th axis
  reads its "Voz narrativa"); the 6th axis reuses it as the single grounding input — there
  is no graph ingestion of grammatical person in this slice.
- `focalization` declares the `first_person_recall` abstention under **all** declared third
  person (iteration 053); under first person or input gaps it does not emit
  `pending_capability` `first_person_recall`, so the nudge is naturally scoped.
- The 6th axis adds the morphological recall **on top of** the preserved explicit-pronoun
  deterministic core (the `focalization` `warning`s) — it never suppresses them.

## Out of Scope

- **Gating** an LLM verdict (golden-runs / per-hash cache → an `error` that vetoes merge),
  deferred with its own activation condition (§ 20.6.2 decision 4).
- Changing the explicit-pronoun regex or the `focalization` validator — iteration 053 did
  its part; the deterministic core is **preserved**. There MUST be zero changes under
  `validation/` and no change to the `code` contract or the `_judges` helper.
- The iterations-051/052 skill axes (undeclared characters, head-hopping) — intact; not
  modified beyond living alongside the new 6th axis and sharing the description.
- Touching `bookwright-verify` (that is manuscript-vs-research, another layer).
- Any move-3 dimension **beyond** the 1st-person break (this completes the first wave;
  further dimensions, if any, are later iterations).
- Reopening the iteration-044 green predicate.
- Adding any dependency (Constitution II), touching the frozen ontology (Principle X), or
  creating / modifying a validator in `validation/` (move 3 is the skill layer, not a
  validator).
- Each changed file MUST stay ≤ 500 lines.
