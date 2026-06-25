# Contract: `status` move-3 nudge keying by `(validator, code)`

The `status` rule table keys its move-3 judge nudges on the abstention `code`, so two
abstentions from the **same** validator drive distinct (or no) nudges.

## C1 — the generalized predicate (`status/rules.py`)

```python
def _judges(validator: str, code: str) -> Callable[[StatusState], bool]:
    return lambda s: any(
        r.validator == validator
        and r.kind is NotEvaluatedKind.pending_capability
        and r.code == code
        for r in s.validation.not_evaluated
    )
```

Adds the `code` argument and the `r.code == code` clause to the post-052 predicate
(`validator == … AND kind is pending_capability`) (FR-012).

## C2 — the two re-pointed rules

| Rule (table order, unchanged) | `applies` before (052) | `applies` after (053) |
|---|---|---|
| `judge_undeclared_characters` | `_judges("character_unknown_mentions")` | `_judges("character_unknown_mentions", "undeclared_characters")` (FR-013) |
| `judge_head_hopping` | `_judges("focalization")` | `_judges("focalization", "head_hopping")` (FR-014) |

- `Rule.build` stays one `Action` (not a list, not merged).
- No rule is added or removed; **no first-person nudge** (FR-015) — the destination is 054.
- Table order and every other rule are unchanged.

## C3 — firing behavior (the cases that MUST be tested, FR-018 / SC-004)

| State (`not_evaluated` entry) | `judge_head_hopping` | `judge_undeclared_characters` |
|---|---|---|
| `(focalization, pending_capability, head_hopping)` | **fires** | — |
| `(focalization, pending_capability, first_person_recall)` **alone** | **does NOT fire** (the mis-fire this contract prevents) | — |
| `(focalization, missing_input)` | does NOT fire | — |
| `(character_unknown_mentions, pending_capability, undeclared_characters)` | — | **fires** (byte-identical to 052) |

The negative `first_person_recall`-only case models third-person-**non-limited** (recall
present, head-hopping absent). **No** first-person `next_action` is emitted in any state.

## C4 — green / count invariance

- `judge_*` rules are informative — they never degrade green (entries stay
  `pending_capability`).
- For a third-person-limited fixture, the head-hopping nudge still fires (the
  `head_hopping` `code` is present), so `next_actions` length is unchanged from 052 (e.g.
  `tiny-historical` stays **5**), and the new `first_person_recall` entry adds **no**
  action.

## C5 — `code` reaches `status` for free

`status/queries.py:validation_summary` passes the runner's `NotEvaluatedResult` tuples into
`ValidationSummary.not_evaluated` unchanged, so once the runner stamps `code`, `_judges` can
read `r.code` and the payload serializes it — **no** edit to `status/model.py` or
`status/queries.py` (verify-only).
