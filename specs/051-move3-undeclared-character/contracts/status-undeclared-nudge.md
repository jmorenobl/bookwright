# Contract — `bookwright status` undeclared-character nudge

A new, separate rule in the pure `state → list[Action]` table
(`src/bookwright/status/rules.py`). No I/O, no graph, no clock — only the
already-aggregated `StatusState`.

## Rule: `judge_undeclared_characters`

- **Name**: `judge_undeclared_characters` (stable identity, exercised by
  `test_rules.py::test_every_rule_is_exercised_by_a_synthetic_state`).
- **Source-set** (module-level frozenset, the set of abstaining sources continuity
  judges): `{"character_unknown_mentions"}` today. Future move-3 dimensions join by
  adding their source validator name.
- **Predicate (`applies`)**: `True` iff any `state.validation.not_evaluated` entry has
  `validator` in the source-set. **Keys on the source validator, NOT on the
  `pending_capability` kind** (FR-009, Clarifications) — so `focalization`'s head-hopping
  abstention (also `pending_capability`) does NOT fire it in this slice.
- **Builder (`build`)**: returns exactly **one** `Action`:
  - `skill` = `"bookwright-continuity"`
  - `prompt` = fixed English template directing the agent to scan the manuscript for
    proper nouns, read the authored roster (`bible/characters/` `name:` plus
    settings/locations/objects), and report each person used in the prose with no sheet in
    `bible/characters/`.
  - `reason` = fixed English template stating that `character_unknown_mentions` abstained
    (open-set proper-noun discovery is a capability gap) and the skill provides the
    semantic judgment.
  - Both `prompt` and `reason` are non-empty fixed templates with **no minted data**, so
    the same state yields a byte-identical action (SC-002 determinism).

## Table position (priority order)

```
… review_continuity → activate_dormant_validators → judge_undeclared_characters → define_focus
```

- After `activate_dormant_validators` (the other dormant-related nudge), before
  `define_focus` (the catch-all).
- The `bootstrap_graph` short-circuit still suppresses every later rule on a degraded
  graph (research D5) — the new rule included.

## Invariants

- **Green is byte-for-byte unchanged** (FR-010, SC-003). The green predicate lives in
  `validation/report.py` (`status == "ok"` AND no `not_evaluated` entry has
  `kind == missing_input`). This rule never touches it; a `pending_capability` entry
  does not degrade green. The action is purely additive to `next_actions[]`.
- **`activate_dormant_validators` stays `missing_input`-only** (iteration 044). The new
  rule does NOT re-add a `character_unknown_mentions` clause to `_REMEDIES`
  (`test_rules.py::test_removed_character_unknown_mentions_remedy_clause_is_gone` stays
  green).
- **The validator is untouched** (`character_unknown_mentions` stays a pure abstainer,
  FR-011).

## Oracle deltas

- `test_rules.py`:
  - add `judge_undeclared_characters` to `_TRIGGER` (keeps the exhaustiveness assertion);
  - add an exact-match test for the judge action's `skill`/`prompt`/`reason`;
  - **retarget** `test_capability_gap_only_run_suppresses_the_dormant_nudge`: a
    `pending_capability` `character_unknown_mentions` entry now produces the
    `bookwright-continuity` judge action (and still produces NO
    `activate_dormant_validators` action). Rename/repurpose to assert exactly that.
- `test_status.py`: assert the judge `next_action` appears in the `--json` envelope on a
  project carrying the abstention.
- `tiny-historical/expected-status.md`: `next_actions.skills` gains a second
  `bookwright-continuity` (emitted after `review_continuity`); `validation.counts`, the
  `not_evaluated` entries, and GREEN status byte-identical. Update the NOTE prose.
- `tiny-novel`/`tiny-memoir`: stay GREEN, carry the same nudge (informative).

**All behavior verified empirically with `uv run pytest`** (FR-013).
