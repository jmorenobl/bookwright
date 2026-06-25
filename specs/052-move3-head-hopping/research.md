# Phase 0 Research — Move 3 second slice: judge head-hopping in `bookwright-continuity`

All `NEEDS CLARIFICATION` are resolved. The spec's Clarifications session (2026-06-25)
closed the five design questions; this file consolidates the decisions with rationale and
the alternatives rejected. Nothing here reopens a § 16 axiom or the iteration-044 green
predicate.

## D1 — Surface = extend `bookwright-continuity` (no new skill)

- **Decision**: Add a **fifth axis** ("head-hopping / broken focalization") to the existing
  `bookwright-continuity` skill — its `## Procedimiento` and `## Output` — exactly as 051
  added the fourth.
- **Rationale**: § 20.6.2 decision 1 — the judgment is *manuscript vs. declared canon*,
  continuity's mandate. Continuity already loads the roster, the voice and the graph; a new
  skill would duplicate that grounding. One skill, five axes, one trigger surface.
- **Alternatives rejected**: a new `bookwright-focalization` skill (duplicate grounding,
  violates 051's established pattern); folding head-hopping into the deterministic validator
  (the heuristic was measured nearly dormant and deleted in 045 — the judgment is
  irreducibly semantic).

## D2 — Grounding = declared voice + focal POV calendar + character roster

- **Decision**: The axis reads three authored sources — (1) the **declared narrative voice**
  from `bible/constitution.md` (the same "Voz narrativa: …" line `focalization` parses),
  proceeding only under third-person *limited* / focalized; (2) the **focal POV per chapter**
  from `bible/pov-structure.md` (the "Calendario de POV" section), a prose file the skill
  does **not** read today; (3) the **character roster** from `bible/characters/*.md`.
  `bible/pov-structure.md` is added to "Archivos a leer".
- **Rationale**: § 20.6.2 decision 3 — these three are exactly what the deleted deterministic
  heuristic could not resolve (it had no per-chapter focal-POV anchor). The POV calendar
  tells the agent who *may* hold interiority in each chapter; the roster resolves whose
  interiority a passage attributes; the voice scopes the axis (head-hopping is undefined
  under omniscient or first person).
- **No new `references/` file** (Clarification Q5 → FR-016): none exists for focalization
  today, and `bible/pov-structure.md` is itself the authored source the agent reads directly.
  The grounding is documented **inline in the skill body**. Scope discipline / zero-debt.
- **Alternatives rejected**: a new `references/golem-focalization.md` (speculative new file
  for a source the agent reads directly); ingesting the POV calendar into the graph (the
  file carries no indexed frontmatter; the skill reads it as prose, like the constitution).

## D3 — The deterministic validator is already done (zero `validation/` diff)

- **Decision**: **Do not touch `focalization`.** It already declares the head-hopping
  abstention under limited-third —
  `EvalResult(self._first_person_breaks(...), [Abstention(_HEAD_HOPPING_PENDING,
  NotEvaluatedKind.pending_capability)])` (`validation/validators/focalization.py:113-116`,
  iteration 050, via the partial `EvalResult` form (c)).
- **Rationale**: FR-013 — the honesty half (abstain rather than fake) was closed by 045/050;
  this slice supplies only the *judgment* and the *discoverability*. This is the one
  structural difference from 051: there the abstainer was anchored *in* the slice; here it
  predates it, so the slice is purely skill + status.
- **Alternatives rejected**: re-adding a deterministic head-hopping heuristic (deleted in
  045 as near-dormant); adding a new abstention (that is the DEBT-021 1st-person slice, out
  of scope).

## D4 — Generalize the status keying: validator name + `pending_capability` kind

- **Decision**: **Delete** the iteration-051 `_JUDGE_SOURCES` frozenset (which matched on
  validator *name* alone) and replace it with a shared predicate helper requiring
  `validator == <name> AND kind is NotEvaluatedKind.pending_capability`. Both
  `judge_undeclared_characters` and the new `judge_head_hopping` adopt it.
- **Rationale**: Clarification Q1 (FR-009/FR-010). `character_unknown_mentions` is *always*
  `pending_capability`, so name-only keying was sound for it. `focalization` emits **both**
  `missing_input` (input gaps — covered by `activate_dormant_validators`) **and**
  `pending_capability` (head-hopping). The head-hopping nudge MUST fire only on the latter.
  Name-only keying cannot express that. The generalization is **byte-identical in behavior**
  for `character_unknown_mentions` (every entry is already `pending_capability`), so the 051
  nudge is unaffected. Doctrine §3: **delete the ill-fitting frozenset** rather than guard it.
- **Alternatives rejected**: keying the head-hopping rule on `pending_capability` *kind*
  alone (would also fire on `character_unknown_mentions` — wrong action); adding a second
  frozenset keyed by (name, kind) tuples (more state than a one-line predicate helper);
  adding a guard clause inside the 051 rule (guards the symptom, doctrine §3).

## D5 — Two distinct peer rules; `Rule.build` stays one-Action

- **Decision**: The head-hopping dimension is a **second peer `Rule`** (`judge_head_hopping`)
  with its **own** builder `_judge_head_hopping` producing a head-hopping-specific
  `prompt`/`reason`, **distinct** from the 051 undeclared-character action. `Rule.build` is
  **not** reshaped to return a list; the two judge nudges are **not** merged. Placed
  **immediately after `judge_undeclared_characters` and before `define_focus`**.
- **Rationale**: Clarifications Q2/Q3/Q4 (FR-010/FR-011/FR-009). The two move-3 dimensions
  are independent and may both fire in the same run (a limited-third project carries both
  the `character_unknown_mentions` and the `focalization` head-hopping abstentions), so each
  emits its own coherent action. Preserving the one-Rule-one-Action contract and the
  explicit-row table style is the lowest-debt fit (zero ripple). Adjacency keeps the emitted
  `next_actions` order deterministic (`test_actions_emit_in_table_priority_order`,
  `tiny-historical` 4 → 5).
- **Alternatives rejected**: a single merged "judge" rule emitting both actions (breaks the
  one-Rule-one-Action contract; couples two independent dimensions); reshaping `Rule.build`
  to return `list[Action]` (ripples through `next_actions` and every rule — disproportionate).

## D6 — Green is byte-identical; `activate_dormant_validators` stays `missing_input`-only

- **Decision**: No change to the green predicate (`validation/report.py`,
  `missing_input`-only filter) or to `activate_dormant_validators`.
- **Rationale**: FR-012 — a `pending_capability` entry never tumbles green; the new action is
  informative. The iteration-044 green regression is not reopened.
- **Alternatives rejected**: making the head-hopping verdict gate CI (deferred with its own
  activation condition, § 20.6.2 decision 4 — out of scope).

## D7 — Description widening + verbatim mirror

- **Decision**: Widen the source frontmatter `description` so the skill also triggers on
  "revisa head-hopping / saltos de punto de vista / focalización rota" and "check for
  head-hopping / POV breaks" (ES + EN), and mirror the widened string **verbatim** into
  `SKILL_DESCRIPTIONS["bookwright-continuity"]` (`integrations/descriptions.py:27`).
- **Rationale**: FR-006/FR-015. The equality gate (`test_descriptions.py`) fails on any
  divergence. Current length is **822/1024** — ~200 chars of slack; the head-hopping trigger
  must be brief, or the existing axes' trigger phrasing is compressed without losing any
  axis's trigger (the four current triggers — bible coherence, undeclared characters, and
  the post-draft/pre-draft sibling disambiguation — all stay live).
- **Alternatives rejected**: offloading triggers to the body (frontmatter `description` is
  the only trigger surface the agent loads at tier 1); exceeding 1024 (lint gate fails).

## D8 — Judgment, not gate (no LLM in CI, no `error` from an LLM)

- **Decision**: The verdict is informative. The CLI stays deterministic with no LLM
  dependency; the CI gate stays error-only; no `error` is ever born from an LLM.
- **Rationale**: § 20.6.2 decision 4 (FR-014). Consequently the LLM judgment quality is
  **not** unit-asserted — consistent with how `bookwright-verify`/`bookwright-continuity`
  are tested today (Principle VIII materialization split).

## D9 — Reuse `tiny-historical`; negative case is pure-unit

- **Decision**: The e2e green-preserving fixture is the **existing `tiny-historical`** — it
  already declares third-person *limited* and already carries the `(focalization,
  pending_capability)` abstention; its `expected-status.md` `next_actions` flips **4 → 5**
  while GREEN stays. **No new fixture.** The negative case (a focalization-`missing_input`-only
  project gains no head-hopping nudge) is covered at the pure `test_rules.py` synthetic-state
  level (no disk).
- **Rationale**: Clarification Q5 / FR-017. No speculative fixture (scope discipline); the
  rules module is `state → actions`, so the negative path is a one-line synthetic state.
  `tiny-historical` ships **no** `bible/pov-structure.md`, which is consistent: the status
  nudge keys on the validator abstention (present), and the skill's runtime grounding-gap
  handling (FR-002 (e)) is the absent-calendar path — exercised by the agent at runtime,
  never unit-asserted.
- **Alternatives rejected**: a new limited-third fixture with a populated POV calendar
  (speculative; the abstention + green-preservation contract is already exercised by
  `tiny-historical`).

## Resolution summary

| # | Question | Resolution |
|---|---|---|
| D1 | New skill or extend? | Extend `bookwright-continuity` — fifth axis |
| D2 | Grounding sources? | voice + `bible/pov-structure.md` POV calendar + roster; no new `references/` |
| D3 | Touch the validator? | No — `focalization` already abstains (050); zero `validation/` diff |
| D4 | Keying mechanism? | Delete `_JUDGE_SOURCES`; shared predicate (validator + `pending_capability`) |
| D5 | One rule or two? | Two peer rules; `judge_head_hopping` after `judge_undeclared_characters` |
| D6 | Green / dormant rule? | Both byte-identical; `pending_capability` never degrades green |
| D7 | Description? | Widen + mirror verbatim; stay < 1024 (822 today) |
| D8 | Gate? | Informative only; no LLM in CI; no `error` from an LLM |
| D9 | Fixture? | Reuse `tiny-historical` (4 → 5); negative case pure-unit; no new fixture |

No open clarifications remain.
