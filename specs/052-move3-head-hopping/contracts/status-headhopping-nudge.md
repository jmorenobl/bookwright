# Contract — `bookwright status` head-hopping nudge + generalized judge keying

The status-rule contract for the head-hopping discoverability `next_action` and the keying
generalization. Pure `StatusState → list[Action]`; verified by `tests/status/test_rules.py`,
`tests/commands/test_status.py`, and the `tiny-historical` oracle. No I/O, no graph, no clock.

## Source file

- `src/bookwright/status/rules.py`

## C1 — Delete `_JUDGE_SOURCES`; add a shared predicate helper

- The iteration-051 `_JUDGE_SOURCES: frozenset[str]` (matched validator **name** alone) MUST
  be **deleted**, not guarded (doctrine §3; FR-010).
- A shared predicate factory MUST replace it, requiring **both** the source validator name and
  `kind is NotEvaluatedKind.pending_capability`:

  ```python
  def _judges(validator: str) -> Callable[[StatusState], bool]:
      return lambda s: any(
          r.validator == validator and r.kind is NotEvaluatedKind.pending_capability
          for r in s.validation.not_evaluated
      )
  ```

## C2 — `judge_undeclared_characters` stays byte-identical in behavior

- Its `applies` MUST become `_judges("character_unknown_mentions")`.
- Behavior MUST be **byte-identical** to iteration 051: `character_unknown_mentions` always
  abstains `pending_capability`, so adding the kind clause changes nothing for it (FR-010).
- Its builder `_judge_undeclared_characters`, prompt, and reason are **unchanged**.

## C3 — New `judge_head_hopping` peer rule

- A NEW `Rule(name="judge_head_hopping", applies=_judges("focalization"),
  build=_judge_head_hopping)` MUST be added to `RULES`.
- `Rule.build` MUST stay one-Rule-one-Action — it is **not** reshaped to return a list, and
  the two judge nudges are **not** merged (FR-010, Clarification Q3).
- The builder `_judge_head_hopping(state)` MUST return one `Action`:
  - `skill = "bookwright-continuity"`
  - a fixed-template head-hopping `prompt` (read the declared narrative voice + the
    `bible/pov-structure.md` POV calendar + the roster; under limited-third, judge per chapter
    whether the prose attributes interiority to a non-focal POV character; report each as a
    deviation) — a fixed English template parameterized only by state facts (byte-identical
    across runs, SC-002).
  - a head-hopping `reason` (focalization abstained on head-hopping under limited-third — the
    semantic judgment is available via the skill).
  - **Distinct** from the 051 undeclared-character action's prompt/reason (FR-011).

## C4 — Table position

- `judge_head_hopping` MUST sit **immediately after `judge_undeclared_characters` and before
  `define_focus`** in `RULES` (FR-009, Clarification Q4), so emitted `next_actions` order is
  deterministic.

## C5 — Negative case: `missing_input` does not fire it

- A `(focalization, missing_input)` abstention MUST fire `activate_dormant_validators` and
  **NOT** `judge_head_hopping` (FR-009; SC-004). `activate_dormant_validators` stays
  `missing_input`-only (FR-012).

## C6 — Green invariant

- The iteration-044 green predicate (`validation/report.py`, `missing_input`-only filter) MUST
  be **byte-for-byte unchanged**; a `pending_capability` entry MUST NOT degrade green
  (FR-012; SC-005).

## C7 — Both move-3 nudges may co-fire

- When the report carries **both** `(character_unknown_mentions, pending_capability)` **and**
  `(focalization, pending_capability)`, `status` MUST emit **both** judge actions — the 051
  undeclared-character action then the head-hopping action — each coherent and distinct, in
  table order (FR-011).

## Oracles

- `tests/status/test_rules.py`:
  - add `judge_head_hopping` to `_TRIGGER` (state `make_state(not_evaluated=(_DORMANT_FOCAL_CAP,))`)
    so `test_every_rule_is_exercised_by_a_synthetic_state` stays exhaustive;
  - **RETARGET** `test_focalization_capability_gap_does_not_fire_the_judge_nudge` — it must now
    assert the `(focalization, pending_capability)` entry fires **exactly one**
    `bookwright-continuity` head-hopping action (C3);
  - add an exact-match test for the head-hopping action prompt/reason;
  - add the negative test: `(focalization, missing_input)` fires `activate_dormant_validators`
    and **not** `judge_head_hopping` (C5);
  - update `test_both_kinds_at_once_*` / priority-order tests for the shifted action counts (C7).
- `tests/commands/test_status.py`: the head-hopping `next_action` surfaces in the `--json`
  envelope, distinct from the 051 action.
- `tests/fixtures/tiny-historical/expected-status.md`: `next_actions` 4 → 5 (a third
  `bookwright-continuity`); `validation.counts`, `not_evaluated`, GREEN status byte-identical.
- `tests/e2e/test_orchestration_workflow.py`: reads the oracle; passes once it records the 5th
  action.
