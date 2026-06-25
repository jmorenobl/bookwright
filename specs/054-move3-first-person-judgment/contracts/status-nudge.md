# Contract: `judge_first_person_recall` status nudge

The `status` discoverability rule that points the author at the first-person
judgment when `focalization` has abstained on first-person recall. Mirror of the
052 `judge_head_hopping` rule over the **other** `focalization` abstention
(FR-009..FR-012). The `code` contract and `_judges(validator, code)` helper
already exist (053) and are **only used**, not changed (FR-013).

## C1 — The new builder (`status/rules.py`)

`_judge_first_person_recall(state) -> Action` returns **one fixed,
byte-identical** `Action` (no minted data):

- `skill == "bookwright-continuity"`.
- `prompt`: directs the agent to read the declared narrative voice
  (`bible/constitution.md`); under **any** declared third-person voice (limited
  **or** non-limited), judge per passage whether the prose slides into first
  person — **including** the pro-drop verbal morphology (`Caminé`, `Me senté`,
  `Escribí`) the explicit-pronoun check cannot see — and report each slip as a
  continuity deviation. The prompt MUST be **distinct** from the head-hopping
  prompt: it MUST NOT name the POV calendar (`bible/pov-structure.md`) or the
  roster (a 1st-person break is grammatical person, not character identity).
- `reason`: starts with `"focalization abstained on first-person recall"` —
  distinct from `"focalization abstained on head-hopping"` (052) and
  `"character_unknown_mentions abstained …"` (051). It names the capability gap
  ("the deterministic check only covers the explicit subject pronoun; the skill
  provides the semantic judgment").

## C2 — The new rule + its position (FR-009)

```python
Rule(
    name="judge_first_person_recall",
    applies=_judges("focalization", "first_person_recall"),
    build=_judge_first_person_recall,
),
```

Inserted in `RULES` **immediately after `judge_head_hopping` and before
`define_focus`**. Tuple order IS the priority order, so the three move-3 judge
nudges (undeclared → head-hopping → first-person) emit as a deterministic
adjacent block.

## C3 — Keying precision (FR-011)

`_judges("focalization", "first_person_recall")` fires iff a `not_evaluated`
entry has `validator == "focalization"` AND `kind is pending_capability` AND
`code == "first_person_recall"`. Therefore:

- It fires on the first-person abstention (third-person limited **and**
  non-limited — both branches emit it).
- It does **NOT** fire on the `head_hopping` abstention.
- `judge_head_hopping` does **NOT** fire on the `first_person_recall` abstention
  (already true since 053; this contract preserves it).
- It does **NOT** fire on `focalization`'s `missing_input` gaps (those drive
  `activate_dormant_validators`, which stays `missing_input`-only).

## C4 — Informative, never degrades green (FR-012)

The action is informative: a `pending_capability` entry never denies green. The
iteration-044 green predicate (`validation/report.py`) stays byte-for-byte
unchanged; `activate_dormant_validators` stays `missing_input`-only; no `error`
is born; the CI gate (error-only) is unchanged (FR-014).

## C5 — Distinct and co-firing (FR-010)

When all three move-3 abstentions are present (`character_unknown_mentions` +
`focalization` head-hopping + `focalization` first-person-recall), `status` emits
**all three** continuity actions, each coherent and distinct, in table order
(undeclared, head-hopping, first-person), never merged.

## Verification (empirical — `uv run pytest`)

`tests/status/test_rules.py`:

- **Positive**: a lone `(focalization, pending_capability, first_person_recall)`
  state yields **exactly one** `bookwright-continuity` first-person action, GREEN.
  (Rewrite of the 053 `test_first_person_recall_alone_fires_no_judge_nudge`,
  which asserted no nudge — that intermediate state is exactly what 054 closes.)
- **Negative / keying (FR-011)**: a `head_hopping`-only state yields **no**
  first-person action (only the head-hopping one); the first-person nudge never
  fires on `head_hopping`.
- **All three co-fire** in table order, distinct prompts, no
  `activate_dormant_validators` (all `pending_capability`). (Rewrite of
  `test_head_hopping_and_recall_together_fire_only_the_head_hopping_judge`.)
- **Negative (declared first person)**: a synthetic state with **no**
  `first_person_recall` abstention gains **no** first-person nudge.
- The `_TRIGGER` dict gains a `judge_first_person_recall` entry so every rule is
  exercised by its own synthetic state.
- **Green**: a flawless third-person state stays GREEN (FR-012).

`tests/commands/test_status.py`: the action surfaces through the `--json`
envelope. `tests/e2e/test_orchestration_workflow.py` + the `tiny-historical`
oracle: `next_actions` length 5 → 6, GREEN preserved; `tiny-novel` /
`tiny-memoir` stay GREEN.
