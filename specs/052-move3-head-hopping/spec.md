# Feature Specification: Move 3 second slice — judge head-hopping / broken focalization in `bookwright-continuity`

**Feature Branch**: `052-move3-head-hopping`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "Necesidad: el move 3 (juicio semántico en validación) aterriza su SEGUNDA rebanada vertical, mismo patrón que 051… La dimensión de ESTE slice es el HEAD-HOPPING (ruptura de focalización)… (see iteration prompt in `bookwright-implementation-plan.md`)"

## Context & Background

This is the **second vertical slice of move 3** — the semantic-judgment layer that
is the north star of issue #1. It mirrors iteration 051 exactly in shape; only the
judged *dimension* changes. The contract is already fixed in `bookwright-design.md`
§ 20.6.2 (design pass of 2026-06-24, after the 3rd dogfood
`el-año-de-las-casas-vacías`). The standing decisions this slice reuses:

- The judgment layer is an **Agent Skill** — the CLI (`bookwright validate`) stays
  fully deterministic with **no LLM dependency** (Constitution II).
- The existing `bookwright-continuity` skill is **extended** (no new skill is created).
- The `not_evaluated` channel is the **contract between the two layers**: every
  `Abstention(kind=pending_capability)` that `bookwright validate` publishes is a
  *judgment task* the skill picks up and answers, **anchored in the graph / authored
  source**.

The dimension of this slice is **head-hopping (broken focalization)**: under a
declared **third-person *limited* / focalized** narrative voice, does the prose enter
the **interiority** (thoughts, feelings, perceptions, interior monologue) of a
character who is **not the focal POV** of that chapter? The deterministic validator
`focalization` already **declares the head-hopping abstention** in this exact case
(`Abstention(_HEAD_HOPPING_PENDING, kind=pending_capability)`, iteration 050, under
limited-third), because distinguishing *real* head-hopping is irreducibly semantic —
the deterministic heuristic was measured nearly dormant on real prose and deleted in
iteration 045. The 3rd dogfood measured this signal **lost, not theoretical**: a real
head-hop (the interiority of *Irene* surfacing inside a chapter focalized on *Teo*)
is **invisible today** — the validator honestly abstains rather than fake the finding.
This slice makes `bookwright-continuity` **judge** that dimension, restoring the signal.

The grounding (§ 20.6.2 decision 3) is exactly what the deleted heuristic could not
resolve: the **declared voice** (`bible/constitution.md`), the **focal POV per chapter**
(`bible/pov-structure.md`, a prose file the skill does not read today), and the
**character roster**.

## Clarifications

### Session 2026-06-25

- Q: `focalization` emits abstentions of **two** kinds — `pending_capability`
  (head-hopping, under limited-third) and `missing_input` (no constitution / no voice /
  `[PENDING]` placeholder / no grammatical person). On which exact abstention must the new
  head-hopping `bookwright status` nudge fire? → A: **Only** on
  `(validator=focalization, kind=pending_capability)`. It MUST NOT fire on
  `focalization`'s `missing_input` abstentions (those are input-gaps already covered by the
  `activate_dormant_validators` rule). The iteration-051 keying (`_JUDGE_SOURCES`, by
  validator **name** alone) is **insufficient** for `focalization` because that validator
  has both kinds; the mechanism MUST be generalized to require `kind is pending_capability`
  AND match the abstaining source. This generalization is byte-identical for
  `character_unknown_mentions` (which is always `pending_capability`), so the 051
  undeclared-character nudge is unaffected.
- Q: Should the new dimension share the 051 continuity action or get its own? → A: Its
  **own** action, with a head-hopping-specific `prompt`/`reason` distinct from the 051
  undeclared-character action. The two are independent move-3 dimensions and may both fire
  in the same run (a limited-third project carries both the `character_unknown_mentions`
  and the `focalization` head-hopping abstentions), so each emits its own coherent
  continuity action.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The author surfaces a head-hop the validator could only abstain on (Priority: P1)

An author has written a multi-POV novel in **third-person limited**. In a chapter
focalized on *Teo*, a paragraph slips into *Irene*'s interiority ("Irene sintió que…"),
a real head-hop. They ask their agent to "check my manuscript against the bible" (or
"revisa head-hopping / saltos de punto de vista"). The agent runs the extended
`bookwright-continuity` skill, which reads the **declared voice** from
`bible/constitution.md` (confirming it is third-person limited — if it were omniscient
or first person, head-hopping would not apply and nothing is reported), reads the
**focal POV per chapter** from `bible/pov-structure.md`, reads the character roster, and
**judges**, per chapter, whether the prose attributes interiority to a non-focal
character. It reports the passage as one more continuity deviation: the manuscript
quote, "interiority of *Irene* under the POV of *Teo* in *<chapter>*", and a suggestion.

**Why this priority**: This is the whole point of the slice — it restores a real,
measured signal (the *Irene*-under-*Teo* head-hop) that the honest deterministic
abstention had to silence. It proves the move-3 pipeline for a second dimension
(`validate` abstains → continuity picks up the abstention → judges anchored in voice +
POV calendar + roster → reports).

**Independent Test**: Materialize the `bookwright-continuity` skill, confirm the new
5th axis ("head-hopping / broken focalization") is present in its `## Procedimiento` and
`## Output` sections, cites the declared voice + the POV calendar (`bible/pov-structure.md`)
+ the roster as grounding, lists `bible/pov-structure.md` under "Archivos a leer", and
that the skill still passes the lint gate. The *quality* of the LLM judgment is not
unit-asserted (as with `bookwright-verify`/`bookwright-continuity` today); what is
testable is that the skill materializes, lints, triggers, and documents the grounding.

**Acceptance Scenarios**:

1. **Given** a project whose constitution declares a third-person *limited* voice and
   whose `bible/pov-structure.md` names a focal POV per chapter, **When** the author runs
   the `bookwright-continuity` skill, **Then** the skill's procedure directs the agent to
   read the declared voice, read the POV calendar, read the roster, and report each
   passage that gives interiority to a non-focal character as a deviation with a
   manuscript quote, the phrase naming the non-focal character under the focal POV in the
   chapter, and a remediation suggestion.
2. **Given** a project whose declared voice is **omniscient** or **first person**, **When**
   the skill runs, **Then** its procedure instructs the agent that head-hopping does **not
   apply** and reports nothing for this axis (the dimension is scoped to limited-third).
3. **Given** a limited-third project whose `bible/pov-structure.md` is absent or whose
   "Calendario de POV" is still a `[PENDING: …]` placeholder, **When** the skill runs, **Then**
   its procedure directs the agent to report the grounding gap (no focal POV to anchor on) and
   **not** to guess the focal POV or emit a head-hop finding.
4. **Given** the materialized skill, **When** the lint gate runs, **Then** `name` ≤ 64
   chars (matching its directory), `description` ≤ 1024 chars, and valid YAML front-matter
   all pass.

---

### User Story 2 - The author discovers *how* to get the head-hopping judgment (Priority: P1)

An author runs `bookwright status` on a limited-third project where `focalization` has
declared its head-hopping abstention (`not_evaluated`, `kind=pending_capability`). Status
now surfaces **one** `next_action` pointing to `bookwright-continuity` as the way to
*obtain* that semantic judgment. The nudge is **informative**: it does **not** degrade the
project's green status, and it is **distinct** from the iteration-051 undeclared-character
nudge (its own prompt/reason).

**Why this priority**: Without the discoverability loop, the head-hopping abstention is a
dead end — the author has no signposted way to reach the judgment the skill now provides.
Closing the loop is what makes the contract between layers usable end to end for this
dimension.

**Independent Test**: Empirically via `uv run pytest`. A limited-third project carries the
`(focalization, pending_capability)` abstention and therefore gains exactly one new
head-hopping continuity `next_action` while staying GREEN. The **negative** cases are
explicitly tested: (a) a project whose **only** focalization abstention is `missing_input`
(no constitution / no voice / `[PENDING]` / no grammatical person) does **not** receive the
head-hopping nudge; (b) green is preserved in all cases.

**Acceptance Scenarios**:

1. **Given** a project whose validation report carries a `not_evaluated` entry from
   `focalization` with kind `pending_capability` (head-hopping under limited-third), **When**
   `bookwright status` runs, **Then** the `next_actions` list includes exactly one action
   pointing to `bookwright-continuity` for the head-hopping judgment, distinct from the 051
   undeclared-character action.
2. **Given** a project whose **only** `focalization` abstention is `missing_input`, **When**
   `bookwright status` runs, **Then** the head-hopping `next_action` is **absent** (that gap
   is covered by `activate_dormant_validators`, not by the head-hopping judge nudge).
3. **Given** a flawless project (no errors, no `missing_input` abstentions), **When**
   `bookwright status` runs, **Then** the project is still GREEN — the added action is
   informative and does not flip the green predicate.
4. **Given** the iteration-044 green predicate (`GREEN = status ok AND no not_evaluated
   entry has kind == missing_input`), **When** this feature ships, **Then** that predicate
   is **byte-for-byte unchanged**; a `pending_capability` entry never tumbles green.

---

### Edge Cases

- **Declared voice is omniscient or first person**: head-hopping does not apply; the
  skill reports nothing for this axis. (Note: `focalization` only declares the
  head-hopping `pending_capability` abstention under limited-third, so the status nudge is
  naturally absent here too.)
- **No `bible/pov-structure.md` / no POV calendar / a `[PENDING: …]` calendar**: the focal
  POV per chapter is unknown, so the agent cannot anchor the judgment; it reports the
  grounding gap (thin input is a judgment input, not an error) rather than guessing. The
  template ships this file with a `[PENDING]` "Calendario de POV", so this is the common
  early-stage state, not a rare one. The skill's procedure must say so (FR-002 clause (e)).
- **A project with no manuscript yet**: the skill behaves as today — reports "missing
  prerequisite" (nothing to verify); the new axis simply finds no prose to scan.
- **`focalization` abstains `missing_input` (no constitution / no voice / `[PENDING]` / no
  grammatical person)**: this is an **input gap**, already covered by
  `activate_dormant_validators`. The head-hopping judge nudge MUST NOT fire on it — it
  keys on `(focalization, pending_capability)` only.
- **Both move-3 abstentions present** (a limited-third project carries both
  `character_unknown_mentions` *and* the `focalization` head-hopping abstention): `status`
  emits **both** continuity actions — the 051 undeclared-character action and the new
  head-hopping action — each coherent and distinct, never merged and never redundant.
- **The agent cannot judge (offline / no model)**: the correct resting state is the
  `not_evaluated` the validator already emits — the permanent track-A fallback. The skill
  *improves* the signal when it runs; its absence breaks nothing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `bookwright-continuity` skill MUST gain a **fifth axis** — "head-hopping
  / broken focalization" — documented in its `## Procedimiento` and `## Output` sections.
  The existing four axes (bible compliance, character-arc coherence, timeline coherence,
  undeclared characters) MUST be preserved.
- **FR-002**: The new axis's procedure MUST instruct the agent to (a) read the **declared
  narrative voice** from `bible/constitution.md` and proceed with the axis **only** under a
  third-person *limited* / focalized voice (under omniscient or first person, head-hopping
  does not apply — report nothing); (b) read the **focal POV per chapter** from
  `bible/pov-structure.md` (the "Calendario de POV" section); (c) read the character roster;
  (d) **judge**, per chapter, whether the prose attributes interiority (verbs of
  thinking / feeling / perceiving, interior monologue) to a character who is **not** the
  focal POV of that chapter; and (e) when the POV calendar is **absent or unresolved** (no
  `bible/pov-structure.md`, no "Calendario de POV" section, or a `[PENDING: …]` placeholder
  in its place — treated as no focal POV declared, consistent with how `focalization` treats
  a `[PENDING]` voice, iteration 037), **report the grounding gap and do NOT guess** the
  focal POV (a missing anchor is a judgment-input gap, never a fabricated head-hop).
- **FR-003**: The procedure MUST cite the **grounding** (§ 20.6.2 decision 3): the declared
  voice + the POV calendar (`bible/pov-structure.md`) + the roster — exactly what the
  deleted deterministic heuristic could not resolve.
- **FR-004**: The skill MUST report each head-hop as **one more deviation** in the
  continuity report: a manuscript quote, a phrase naming the **non-focal character's
  interiority under the focal POV in the chapter** (e.g. "interiority of *Irene* under the
  POV of *Teo* in *<chapter>*"), and a suggestion.
- **FR-005**: The skill MUST **begin reading `bible/pov-structure.md`** (it does not today):
  the file MUST be added to the skill's "Archivos a leer" section.
- **FR-006**: The skill `description` MUST be widened so the skill also triggers on prompts
  like "revisa head-hopping / saltos de punto de vista / focalización rota" and "check for
  head-hopping / POV breaks", in **both ES and EN**, WITHOUT exceeding 1024 characters. If
  the additions would exceed 1024, the existing axes' trigger phrasing MUST be compressed
  without losing any axis's trigger.
- **FR-007**: The materialized skill MUST pass the lint gate: `name` ≤ 64 chars and equal to
  its parent directory, `description` ≤ 1024 chars, valid YAML front-matter.
- **FR-008**: The skill MUST remain **read-only and POST-draft** (like all of continuity):
  it writes nothing to the project.
- **FR-009**: `bookwright status` MUST add **one** `next_action` pointing to
  `bookwright-continuity` (for the head-hopping judgment) when the validation report carries
  a `not_evaluated` entry whose **source validator** is `focalization` **and** whose **kind
  is `pending_capability`**. The rule MUST NOT fire on `focalization`'s `missing_input`
  abstentions.
- **FR-010**: The status keying mechanism MUST be **generalized** to require
  `kind is pending_capability` in addition to matching the abstaining source validator. This
  generalization MUST be **byte-identical in behavior** for the iteration-051
  `character_unknown_mentions` nudge (which always abstains `pending_capability`), which MUST
  remain intact.
- **FR-011**: The new head-hopping `next_action` MUST have its **own** `prompt`/`reason`,
  **distinct** from the iteration-051 undeclared-character action. When both move-3
  abstentions are present, `status` MUST emit **both** actions, each coherent and distinct.
- **FR-012**: That `next_action` MUST be **informative**: it MUST NOT degrade green. The
  iteration-044 green predicate (`GREEN = status ok AND no not_evaluated entry has
  kind == missing_input`) MUST stay byte-for-byte identical; a `pending_capability` entry
  MUST NOT tumble green. The 044 green regression MUST NOT be reopened, and
  `activate_dormant_validators` MUST remain `missing_input`-only.
- **FR-013**: The deterministic validator `focalization` MUST NOT be touched: it already
  declares the head-hopping abstention (iteration 050). There MUST be **zero changes** to
  anything under `validation/`.
- **FR-014**: The CI gate MUST NOT change: only `error` findings break CI, and **no `error`
  is ever born from an LLM** (§ 20.6.2 decision 4 — judgment, not gate).
- **FR-015**: The widened `description` MUST be mirrored **verbatim** into
  `SKILL_DESCRIPTIONS["bookwright-continuity"]` in `integrations/descriptions.py`, so the
  source frontmatter and the in-code mirror never diverge. This is enforced by the existing
  equality gate `tests/integrations/test_descriptions.py`. The mirror edit MUST be made
  together with the FR-006 widening.
- **FR-016**: The grounding documentation for the focal-POV-per-chapter source
  (`bible/pov-structure.md`, its "Calendario de POV" section) MUST be documented in the
  skill (and/or a `references/` file) so the agent knows where the focal POV comes from.
- **FR-017**: The oracles that assert the skill body / materialization, the activation
  (bilingual trigger) oracle, the description equality gate, and the `status` rule oracles
  MUST be updated. The *quality* of the LLM judgment MUST NOT be asserted in unit tests. All
  behavior MUST be verified empirically with `uv run pytest`, **including the negative
  cases**: (a) a focalization-`missing_input`-only project does not receive the head-hopping
  nudge; (b) green is preserved.
- **FR-018**: The design record MUST be reconciled: `bookwright-design.md` § 20.6.2 marks
  the second vertical slice (head-hopping) as landed, and any milestone / iteration index
  reflecting shipped work is updated. **No `DEBT.md` entry is removed** — head-hopping has
  no open debt of its own (its honesty was closed by 045/050; its judgment is this slice),
  and **DEBT-021** (the 1st-person pro-drop recall dimension) **stays open**.

### Key Entities *(include if feature involves data)*

- **Declared narrative voice**: read from `bible/constitution.md`; the axis applies **only**
  when it is third-person *limited* / focalized. It is one of the three grounding inputs.
- **Focal POV calendar**: the focal POV per chapter, read from `bible/pov-structure.md` (the
  "Calendario de POV" section) — a prose file the skill does not read today and begins to
  read in this slice. It tells the agent who *may* hold interiority in each chapter.
- **Authored character roster**: the set of declared character names (from
  `bible/characters/*.md`), used to resolve which character a passage's interiority belongs
  to.
- **`not_evaluated` entry (`Abstention`, `validator=focalization`, `kind=pending_capability`)**:
  the data-level contract between the deterministic layer and the skill layer for this
  dimension. The validator names the gap (head-hopping under limited-third); the skill closes
  it with voice + POV calendar + roster as grounding.
- **Continuity deviation (head-hopping)**: a reported finding pairing a manuscript quote with
  the non-focal-character-under-focal-POV-in-chapter phrasing and a remediation suggestion —
  one more deviation in the continuity report.
- **Status `next_action` (head-hopping)**: an informative recommendation pointing to
  `bookwright-continuity` when a `(focalization, pending_capability)` abstention exists;
  never degrades green; distinct from the 051 undeclared-character action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The `bookwright-continuity` skill materializes and passes the lint gate with
  the widened `description` (≤ 1024 chars) and the new 5th axis present in `## Procedimiento`
  and `## Output`, citing voice + POV calendar + roster as grounding, with
  `bible/pov-structure.md` listed under "Archivos a leer", and the procedure documenting the
  absent/`[PENDING]`-calendar grounding-gap handling (report the gap, do not guess — FR-002 (e)).
- **SC-002**: The skill triggers on head-hopping prompts in both ES and EN ("revisa
  head-hopping / saltos de punto de vista" / "check for head-hopping / POV breaks"), verified
  by the activation oracle, and the iteration-051 undeclared-character triggers still fire.
- **SC-003**: A project whose validation report carries the `(focalization,
  pending_capability)` head-hopping abstention gains **exactly one** new
  `bookwright-continuity` head-hopping `next_action` (distinct from the 051 action) while
  keeping its green status — verified via `uv run pytest`.
- **SC-004**: A project whose **only** `focalization` abstention is `missing_input` does
  **not** gain the head-hopping `next_action` — verified empirically as a negative case.
- **SC-005**: A flawless project stays GREEN after this change; the iteration-044 green
  predicate is byte-for-byte unchanged and `activate_dormant_validators` stays
  `missing_input`-only.
- **SC-006**: The deterministic `focalization` validator is unchanged (zero diff under
  `validation/`); the CI gate (error-only) is unchanged and no `error` originates from an
  LLM. The iteration-051 `judge_undeclared_characters` nudge remains intact.
- **SC-007**: `DEBT-021` is still present in `DEBT.md` (no debt removed by this slice).
- **SC-008**: The full suite and all four gates (`ruff check`, `ruff format --check`,
  `mypy --strict`, `pytest` with ≥ 80 % coverage) pass green.

## Assumptions

- The semantic-judgment quality is exercised by the agent at runtime, not asserted in unit
  tests — consistent with how `bookwright-verify`/`bookwright-continuity` are tested today.
- The discoverability `next_action` is added by **generalizing** the iteration-051 mechanism
  to key on `(source validator, kind=pending_capability)` and adding head-hopping as a second
  judged dimension with its own action — distinct from the existing `missing_input`-only
  "activate dormant validators" rule, so the 044 filter that protects green stays intact.
- `bible/pov-structure.md` is an authored prose file (already referenced by other skills such
  as `bookwright-bible` / `bookwright-checklist`); its "Calendario de POV" section is the
  source of the focal POV per chapter. The skill reads it as prose — there is no graph
  ingestion of it in this slice.
- `focalization` declares the head-hopping abstention **only under limited-third** (iteration
  050); under omniscient/first-person or input gaps it does not emit `pending_capability`, so
  the nudge is naturally scoped.
- The grounding documentation extends the skill body and/or an existing `references/` file
  rather than adding a brand-new reference file, where practical.

## Out of Scope

- The **third move-3 dimension** — the 1st-person break / recall ceiling driven by pro-drop
  morphology (DEBT-021) — which follows the **same pattern** in a later iteration and
  **additionally** needs `focalization` to declare a *new* abstention for its recall ceiling.
  This slice does **not** add that abstention.
- **Gating** an LLM verdict (golden-runs / per-hash cache → an `error` that vetoes merge),
  deferred with its own activation condition (§ 20.6.2 decision 4).
- The iteration-051 undeclared-character axis (intact; not modified beyond the shared
  mechanism generalization).
- Touching `bookwright-verify` (that is manuscript-vs-research, another layer).
- Any change to the deterministic `focalization` validator or any other deterministic
  validator under `validation/`.
- Reopening the iteration-044 green predicate.
- Removing any `DEBT.md` entry (DEBT-021 stays open; head-hopping carries no open debt).
- Adding any dependency (Constitution II), touching the frozen ontology (Principle X), or
  creating a new validator in `validation/` (move 3 is the skill layer, not a validator).
- Each changed file MUST stay ≤ 500 lines.
</content>
</invoke>
