# Feature Specification: Move 3 first slice — judge undeclared characters in `bookwright-continuity`

**Feature Branch**: `051-move3-undeclared-character`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Necesidad: el move 3 (juicio semántico en validación, norte de la issue #1) aterriza su PRIMER vertical slice… (see iteration prompt in `bookwright-implementation-plan.md`)"

## Context & Background

This is the **first vertical slice of move 3** — the semantic-judgment layer that
is the north star of issue #1. The contract is already fixed in
`bookwright-design.md` § 20.6.2 (design pass of 2026-06-24, after the 3rd dogfood
`el-año-de-las-casas-vacías`). The key decisions this slice realizes:

- The judgment layer is an **Agent Skill** — the CLI (`bookwright validate`) stays
  fully deterministic with **no LLM dependency**.
- The existing `bookwright-continuity` skill is **extended** (no new skill is created).
- The `not_evaluated` channel is the **contract between the two layers**: every
  `Abstention(kind=pending_capability)` that `bookwright validate` publishes is a
  *judgment task* the skill picks up and answers, **anchored in the authored roster**.

The dimension of this slice is the **character used-but-not-declared** — the signal
that the deterministic validator `character_unknown_mentions` declares
`not_evaluated`. Distinguishing "organization / place name" from "person with no
character sheet" is irreducibly semantic for a capitalization heuristic (an open set:
after organizations come place names, ships, vocatives…). The 3rd dogfood measured
this signal **lost, not theoretical**: a real character ("Amelia", mentioned several
times in the prose, with no sheet in `bible/characters/`) is **invisible today** —
abstained in the very same gesture that (correctly) silences orgs/place names. An
agent anchored in the roster **separates them**: it restores the signal without
reintroducing the noise.

## Clarifications

### Session 2026-06-24

- Q: Should the new `bookwright status` nudge key its trigger on the specific abstaining
  validator (`character_unknown_mentions`) or broadly on any `kind=pending_capability`
  abstention? → A: Narrowly on the abstaining **source** — match the set of abstention
  sources continuity actually judges (today only `character_unknown_mentions`), emit
  exactly one continuity action whose text names the *undeclared-character* judgment, and
  do NOT fire merely because `kind == pending_capability`. Rationale: `focalization`'s
  head-hopping abstention (reactivated in iteration 050) is also `pending_capability` but
  this slice's skill does **not** yet judge it; broad kind-keying would signpost a judgment
  the skill doesn't perform — a Scope-Discipline / track-A-honesty violation. Future
  dimensions join the matched-source set as their skill judgment lands; the 044
  `missing_input`-only green filter is untouched.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The author surfaces a character used but never declared (Priority: P1)

An author has written prose that repeatedly names a person ("Amelia") who has no
sheet under `bible/characters/`. They ask their agent to "check my manuscript against
the bible" (or "revisa si hay personajes sin declarar"). The agent runs the extended
`bookwright-continuity` skill, which reads the authored roster, scans the manuscript
for proper nouns, and **judges** which ones name a *person used in the prose but
absent from the bible* — separating that real signal from organizations, place names,
vocatives and title words that need no sheet. It reports "Amelia" as a continuity
deviation with the manuscript quote, "no entry in `bible/characters/`", and a
suggestion (create the sheet, or confirm it is not a character).

**Why this priority**: This is the whole point of the slice — it restores a real,
measured signal (the "Amelia" case) that the honest deterministic abstention had to
silence. It proves the full move-3 pipeline (`validate` abstains → continuity picks up
the abstention → judges anchored in the roster → reports) in its minimal form.

**Independent Test**: Materialize the `bookwright-continuity` skill, confirm the new
4th axis ("open-set mentions / undeclared characters") is present in its `## Procedimiento`
and `## Output` sections, cites the roster as grounding, and that the skill still passes
the lint gate. The *quality* of the LLM judgment is not unit-asserted (as with
`bookwright-verify`/`bookwright-continuity` today); what is testable is that the skill
materializes, lints, triggers, and documents the roster grounding.

**Acceptance Scenarios**:

1. **Given** a project whose manuscript names a person with no `bible/characters/`
   sheet, **When** the author runs the `bookwright-continuity` skill, **Then** the
   skill's procedure directs the agent to read the authored roster, scan proper nouns,
   and report each undeclared-person mention as a deviation with a manuscript quote,
   the phrase "no entry in `bible/characters/`", and a remediation suggestion.
2. **Given** the same manuscript also names organizations and place names, **When** the
   skill runs, **Then** its procedure instructs the agent to use the roster to
   distinguish persons-without-a-sheet (report) from organizations/place names/vocatives/
   title words (do not report) — restoring the signal without the noise.
3. **Given** the materialized skill, **When** the lint gate runs, **Then** `name` ≤ 64
   chars (matching its directory), `description` ≤ 1024 chars, and valid YAML
   front-matter all pass.

---

### User Story 2 - The author discovers *how* to get the semantic judgment (Priority: P1)

An author runs `bookwright status` on a project where `character_unknown_mentions` has
abstained (`not_evaluated`, `kind=pending_capability`). Status now surfaces **one**
`next_action` pointing to `bookwright-continuity` as the way to *obtain* that semantic
judgment. Iteration 044 had removed this nudge because at that time nothing was
actionable (move 3 did not exist); now running the skill **is** the action, so the
nudge returns — but **informatively**: it does **not** degrade the project's green
status.

**Why this priority**: Without the discoverability loop, the abstention is a dead end —
the author has no signposted way to reach the judgment the skill now provides. Closing
the loop is what makes the contract between layers usable end to end.

**Independent Test**: Empirically via `uv run pytest`. Because
`character_unknown_mentions` abstains **unconditionally**, the `pending_capability`
entry — and therefore the new continuity `next_action` — is present on **every**
validated project; the fixtures verify the two testable claims, not a presence/absence
split: `tiny-historical` carries the `next_action` while its status stays GREEN, and the
flawless controls (`tiny-novel`/`tiny-memoir`) stay GREEN with the same `next_action`
present (the nudge is informative — it never flips green). No oracle asserts the nudge is
*absent* on any validated project (that would contradict the validator's unconditional
abstention).

**Acceptance Scenarios**:

1. **Given** a project whose validation report carries a `not_evaluated` entry from
   `character_unknown_mentions` (kind `pending_capability`), **When** `bookwright status`
   runs, **Then** the `next_actions` list includes exactly one action pointing to
   `bookwright-continuity` as the way to obtain the semantic judgment.
2. **Given** a flawless project (no errors, no `missing_input` abstentions), **When**
   `bookwright status` runs, **Then** the project is still GREEN — the added action is
   informative and does not flip the green predicate.
3. **Given** the iteration-044 green predicate (`GREEN = status ok AND no not_evaluated
   entry has kind == missing_input`), **When** this feature ships, **Then** that
   predicate is **byte-for-byte unchanged**; a `pending_capability` entry never tumbles
   green.

---

### Edge Cases

- **A project with no manuscript yet**: the skill behaves as today — reports "missing
  prerequisite" (nothing to verify), does not fail opaquely; the new axis simply finds
  no prose to scan.
- **A project with no character sheets but plenty of proper nouns**: the roster of
  persons is empty, so every proper noun is a candidate; the agent still judges
  org/place-name vs. person, and reports the persons. The grounding being thin is a
  judgment input, not an error.
- **`G1_Character` has no `rdfs:label`**: the authored person name lives in the sheet's
  `name:` field and in the URI slug — so the person roster is read from the **sheets**,
  not from a graph label. The skill's procedure must say so.
- **Multiple `pending_capability` abstentions** (today only `character_unknown_mentions`,
  later head-hopping / 1st-person break): the status nudge keys on the abstention's
  **source validator**, not on the `pending_capability` *kind* (see Clarifications). It
  matches the set of sources continuity actually judges — today the single member
  `character_unknown_mentions` — and emits **exactly one** continuity action naming the
  undeclared-character judgment. `focalization`'s head-hopping abstention is also
  `pending_capability` but does NOT trigger the nudge in this slice (the skill does not yet
  judge it); when a later slice teaches continuity that dimension, its source joins the
  matched set and the rule still emits one coherent action, never one redundant action per
  abstention.
- **The agent cannot judge (offline / no model)**: the correct resting state is the
  `not_evaluated` the validator already emits — the permanent track-A fallback. The
  skill *improves* the signal when it runs; its absence breaks nothing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `bookwright-continuity` skill MUST gain a **fourth axis** — "open-set
  mentions / undeclared characters" — documented in its `## Procedimiento` and `## Output`
  sections. The existing three axes (bible compliance, character-arc coherence, timeline
  coherence) MUST be preserved.
- **FR-002**: The new axis's procedure MUST instruct the agent to read the **authored
  roster** — person names from `bible/characters/*.md` (`name:` field), plus the names
  from `bible/settings|locations|objects` (to know which proper nouns are already
  declared) — scan the manuscript for proper nouns, and **judge** which ones name a
  *person used in the prose but with no sheet in the bible*, distinguishing them from
  organizations, place names, vocatives and title words (which need no sheet).
- **FR-003**: The procedure MUST cite the **roster as the grounding** (§ 20.6.2 decision
  3): it is what separates signal (a real character with no sheet) from noise
  (org / place name).
- **FR-004**: The skill MUST report each undeclared-person mention as **one more
  deviation** in the continuity report: a manuscript quote, the phrase "no entry in
  `bible/characters/`" (ES/EN equivalent), and a suggestion (create the sheet, or confirm
  it is not a character).
- **FR-005**: The procedure MUST document that the **person roster is read from the
  sheets, not from the graph** — `G1_Character` carries no `rdfs:label`; the authored
  name lives in the sheet's `name:` field and in the URI slug. This MUST be documented by
  reusing or extending `references/golem-character.md`.
- **FR-006**: The skill `description` MUST be widened so the skill also triggers on
  prompts like "revisa si hay personajes sin declarar / mencionados pero sin ficha" and
  "check for undeclared / unbacked characters", in **both ES and EN**, WITHOUT exceeding
  1024 characters.
- **FR-007**: The materialized skill MUST pass the lint gate: `name` ≤ 64 chars and equal
  to its parent directory, `description` ≤ 1024 chars, valid YAML front-matter.
- **FR-008**: The skill MUST remain **read-only and POST-draft** (like all of continuity):
  it writes nothing to the project.
- **FR-009**: `bookwright status` MUST add **one** `next_action` pointing to
  `bookwright-continuity` when the validation report carries a `not_evaluated` entry whose
  **source validator** is `character_unknown_mentions`. The rule MUST key on the abstaining
  **source** (the set of sources continuity actually judges, today the single member
  `character_unknown_mentions`), NOT on the `pending_capability` *kind* — so an abstention
  the skill does not yet judge (e.g. `focalization` head-hopping, also `pending_capability`)
  does NOT trigger the nudge in this slice. This restores the nudge iteration 044 removed
  (now that running the skill is an actionable remedy).
- **FR-010**: That `next_action` MUST be **informative**: it MUST NOT degrade green. The
  iteration-044 green predicate (`GREEN = status ok AND no not_evaluated entry has
  kind == missing_input`) MUST stay byte-for-byte identical; a `pending_capability` entry
  MUST NOT tumble green. The 044 green regression MUST NOT be reopened.
- **FR-011**: The deterministic validator `character_unknown_mentions` MUST remain a
  **pure abstainer**: `raise NotEvaluated(..., kind=pending_capability)` unconditional. No
  detection logic may be added to it (that would be the whack-a-mole issue #1 closed). The
  only change touching its surface is the discoverability `next_action` (FR-009), which
  lives in `status`, not in the validator.
- **FR-012**: The CI gate MUST NOT change: only `error` findings break CI, and **no
  `error` is ever born from an LLM** (§ 20.6.2 decision 4 — judgment, not gate).
- **FR-013**: The oracles that assert the skill body / materialization and the `status`
  oracles that gain the `next_action` MUST be updated. The *quality* of the LLM judgment
  MUST NOT be asserted in unit tests. All behavior MUST be verified empirically with
  `uv run pytest`.
- **FR-014**: `DEBT-013` MUST be removed from `DEBT.md` — this slice is its cure (the skill
  distinguishes org/place-name from person-without-a-sheet, exactly what DEBT-013 asked,
  to be closed "when move 3 lands"). Git retains the history.
- **FR-015**: The design record MUST be reconciled: `bookwright-design.md` § 20.6.2 marks
  the first vertical slice as landed (continuity now answers the
  `character_unknown_mentions` abstention anchored in the roster), and any milestone /
  iteration index reflecting shipped work is updated.
- **FR-016**: The widened `description` MUST be mirrored **verbatim** into
  `SKILL_DESCRIPTIONS["bookwright-continuity"]` in `integrations/descriptions.py`, so the
  source frontmatter and the in-code mirror never diverge. This is enforced by the existing
  equality gate `test_descriptions.py::test_v0_equality_gate_mirrors_source_frontmatter`
  (the source-of-truth check that the table mirrors each source frontmatter `description`
  byte-for-byte). The mirror edit MUST be made together with the FR-006 widening.

### Key Entities *(include if feature involves data)*

- **Authored person roster**: the set of declared person names, read from
  `bible/characters/*.md` `name:` fields (NOT from a graph label, since `G1_Character` has
  no `rdfs:label`), augmented with names from `bible/settings|locations|objects` so the
  agent knows which proper nouns are already declared.
- **`not_evaluated` entry (`Abstention`, `kind=pending_capability`)**: the data-level
  contract between the deterministic layer and the skill layer. The validator names the
  gap; the skill closes it with the roster as grounding.
- **Continuity deviation (undeclared-character)**: a reported finding pairing a manuscript
  quote with "no entry in `bible/characters/`" and a remediation suggestion — one more
  deviation in the continuity report.
- **Status `next_action`**: an informative recommendation pointing to
  `bookwright-continuity` when a `pending_capability` abstention exists; never degrades green.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The `bookwright-continuity` skill materializes and passes the lint gate with
  the widened `description` (≤ 1024 chars) and the new 4th axis present in `## Procedimiento`
  and `## Output`.
- **SC-002**: The skill triggers on undeclared-character prompts in both ES and EN
  ("revisa si hay personajes sin declarar" / "check for undeclared characters"), verified
  by the activation oracle.
- **SC-003**: A flawless project (`tiny-novel`, `tiny-memoir`) stays GREEN after this
  change — the green predicate is unchanged.
- **SC-004**: A project whose validation report carries the
  `character_unknown_mentions` `pending_capability` abstention gains **exactly one**
  `bookwright-continuity` `next_action` (pointing to the semantic judgment) while keeping
  its green status — verified via `uv run pytest` on `tiny-historical`. Since the
  abstention is unconditional, the green controls (`tiny-novel`/`tiny-memoir`) carry the
  same `next_action`; what distinguishes them is only that they have no errors/`missing_input`,
  so they too stay GREEN. No oracle asserts the `next_action` is absent on a validated project.
- **SC-005**: The deterministic `character_unknown_mentions` validator still raises
  `NotEvaluated(kind=pending_capability)` unconditionally; the CI gate (error-only) is
  unchanged and no `error` originates from an LLM.
- **SC-006**: `DEBT-013` no longer appears in `DEBT.md`; the design § 20.6.2 record reflects
  the landed first slice.
- **SC-007**: The full suite and all four gates (`ruff check`, `ruff format --check`,
  `mypy --strict`, `pytest` with ≥ 80 % coverage) pass green.

## Assumptions

- The semantic-judgment quality is exercised by the agent at runtime, not asserted in unit
  tests — consistent with how `bookwright-verify`/`bookwright-continuity` are tested today.
- The discoverability `next_action` is added by introducing a **new, separate** `status`
  rule (distinct from the existing `missing_input`-only "activate dormant validators" rule,
  so the 044 filter that protects green stays intact) that matches the abstention's
  **source validator** — `character_unknown_mentions` (the lone member, today, of the set
  of sources continuity judges) — and yields exactly one continuity action. It keys on the
  source, not on the `pending_capability` kind, so dimensions the skill does not yet judge
  do not fire it (see Clarifications).
- `character_unknown_mentions` abstains **unconditionally** (`tests/status/test_queries.py`
  asserts it is "ALWAYS dormant"), so its `pending_capability` entry — and the new nudge —
  is present on every validated project. `tiny-historical` is the named fixture used to
  assert the nudge's presence; `tiny-novel`/`tiny-memoir` are green controls that prove the
  nudge is **informative** (green is preserved), NOT controls that lack the nudge.
- The roster grounding documentation extends the existing `references/golem-character.md`
  rather than adding a new reference file.

## Out of Scope

- The **other two move-3 dimensions** — head-hopping and 1st-person-break (DEBT-021) — which
  follow the **same pattern** in later iterations. This slice proves the pipeline with the
  simplest grounding dimension (the roster alone).
- **Gating** an LLM verdict (golden-runs / per-hash cache → an `error` that vetoes merge),
  deferred with its own activation condition (§ 20.6.2 decision 4).
- Creating a 5th "organization" roster — DEBT-013 is NOT fixed with another closed list; the
  agent distinguishes org/place-name from person without a new roster.
- Any change to the deterministic `character_unknown_mentions` validator beyond the
  discoverability `next_action`.
- Touching `bookwright-verify` (that is manuscript-vs-research, another layer).
- Reopening the iteration-044 green predicate.
- Adding any dependency (Constitution II), touching the frozen ontology (Principle X), or
  creating a new validator in `validation/` (move 3 is the skill layer, not a validator).
- Each changed file MUST stay ≤ 500 lines.
