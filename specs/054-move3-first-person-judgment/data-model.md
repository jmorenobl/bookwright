# Phase 1 Data Model: Move 3 third dimension, judgment half

This slice adds **no** new type, field, or persisted entity. The data-level
contract — the `Abstention` / `NotEvaluatedResult` `code` discriminator — already
shipped in iteration 053. What this iteration manipulates are **existing**
structures: the skill body, the static description table, and one new `Rule` row
over the unchanged `StatusState`. This document records the entities the change
**reads** and the one **conceptual** entity it adds.

## 1. Declared narrative voice (read-only grounding)

- **Source**: `bible/constitution.md`, the line `Voz narrativa: …` /
  `Narrative voice: …` (already parsed by `focalization` and already read by the
  5th axis of `bookwright-continuity`).
- **Role in this slice**: the **single** grounding input for the 6th axis. The
  axis proceeds only under a declared **third-person** voice (limited **or**
  non-limited); under first person it does not apply; under an absent / `[PENDING]`
  / person-less declaration the agent reports the grounding gap and does not guess.
- **Not read**: the roster (`bible/characters/ name:`) and the POV calendar
  (`bible/pov-structure.md`) — used by the 4th/5th axes, **not** by the 6th
  (grammatical person, not character identity).

## 2. `not_evaluated` entry — `Abstention` (the layer contract, unchanged)

The data contract between the deterministic layer and the skill, **declared by
053** and only **consumed** here:

| Field | Value for this dimension | Notes |
|---|---|---|
| `validator` | `"focalization"` | the abstaining source |
| `kind` | `NotEvaluatedKind.pending_capability` | permanent capability gap, not `missing_input` |
| `code` | `"first_person_recall"` | the 053 discriminator that separates it from `"head_hopping"` |
| `reason` | "full first-person recall requires semantic judgment (move 3); the deterministic check only covers the explicit subject pronoun" | byte-identical to 053 |

`focalization.py` emits this in **both** third-person branches
(`focalization.py:124-151`). **Zero** change to this entry in 054.

`not_evaluated_sort_key` stays `(validator, reason)` (`code` is **not** a sort
term) — `focalization`'s two reasons differ ("full first-person recall…" sorts
before "head-hopping…"), so the order is already total. Unchanged.

## 3. `StatusState` (read-only, unchanged shape)

`status/rules.py` predicates read `state.validation.not_evaluated`, a tuple of
`NotEvaluatedResult` (which already carries `code` since 053). No field is added.
`ValidationSummary.not_evaluated` holds `NotEvaluatedResult` directly, so `code`
flows into `status` for free — `status/model.py` and `status/queries.py` are
**verify-only** (no edit).

## 4. NEW conceptual entity — the first-person `Action` / `Rule`

The only *new* structure, built from existing primitives in `status/rules.py`:

### `_judge_first_person_recall(state) -> Action`

A pure builder returning **one fixed, byte-identical** `Action` (no minted data),
the mirror of `_judge_head_hopping` (`status/rules.py:194-212`):

| `Action` field | Value (fixed template) |
|---|---|
| `skill` | `"bookwright-continuity"` |
| `prompt` | reads the declared narrative voice (`bible/constitution.md`); under **any** declared third-person voice (limited or non-limited), judges per passage whether the narration slides into first person — **including** the pro-drop verbal morphology (`Caminé`, `Me senté`) the explicit-pronoun check cannot see — and reports each slip as a continuity deviation. **Distinct** from the head-hopping prompt (no POV calendar, no roster). |
| `reason` | starts with `"focalization abstained on first-person recall"` — distinct from the head-hopping `"focalization abstained on head-hopping"` and the undeclared-character `"character_unknown_mentions abstained"` reasons (FR-010). |

### `Rule(name="judge_first_person_recall", applies=_judges("focalization", "first_person_recall"), build=_judge_first_person_recall)`

Inserted in the `RULES` tuple **immediately after `judge_head_hopping` and before
`define_focus`** (FR-009). The tuple order IS the priority order, so the three
move-3 judge nudges emit in a deterministic, adjacent block.

## 5. Skill body axis (prose entity in `bookwright-continuity.md`)

The 6th `## Procedimiento` axis + its `## Output` paragraph — see
`contracts/skill-sixth-axis.md` for the exact required content. Mirror of the 5th
(head-hopping) axis, but grounded only in the declared voice and applying under
all third person. Adds the pro-drop morphological recall on top of (never
suppressing) `focalization`'s explicit-pronoun `warning`s.

## State transitions / invariants

- **Green invariant (FR-012)**: the iteration-044 green predicate
  (`GREEN = status ok AND no not_evaluated entry has kind == missing_input`,
  in `validation/report.py`) is **byte-for-byte unchanged**; a
  `pending_capability` entry never tumbles green; `activate_dormant_validators`
  stays `missing_input`-only. The new informative action never degrades green.
- **Keying invariant (FR-011)**: `_judges("focalization", "first_person_recall")`
  fires **only** on the first-person abstention; it never fires on `head_hopping`,
  and `judge_head_hopping` (`_judges("focalization", "head_hopping")`) never fires
  on `first_person_recall`. The `code` discriminator (053) keeps the two
  same-validator nudges separate.
- **Determinism invariant (FR-014)**: no `error` is born; the CI gate (error-only)
  is unchanged; no LLM in CI.
