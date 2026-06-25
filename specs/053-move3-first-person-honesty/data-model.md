# Phase 1 Data Model — abstention `code` discriminator

In-memory + on-the-wire only; the validation subsystem persists nothing (FR-020). The
single new datum is an optional discriminator string flowing through the existing
abstention types and the `not_evaluated[]` channel.

## Entities (changed)

### `Abstention` (returned, form (c)) — `validation/base.py`

A validator's per-dimension conscious skip, carried inside an `EvalResult`.

| Field | Type | Default | Change |
|---|---|---|---|
| `reason` | `str` | — | unchanged |
| `kind` | `NotEvaluatedKind` | `missing_input` | unchanged |
| **`code`** | **`str \| None`** | **`None`** | **NEW (FR-001)** — short stable discriminator so a validator returning multiple abstentions keeps them distinguishable. |

`frozen=True` dataclass — `code` is hashable; the type stays frozen.

### `NotEvaluatedResult` (serialized, name-stamped) — `validation/base.py`

The recorded abstention surfaced in the `not_evaluated` channel (runner-stamped with the
validator name).

| Field | Type | Default | Change |
|---|---|---|---|
| `validator` | `str` | — | unchanged |
| `reason` | `str` | — | unchanged |
| `kind` | `NotEvaluatedKind` | `missing_input` | unchanged |
| **`code`** | **`str \| None`** | **`None`** | **NEW (FR-002)** — stamped by the runner; serialized additively. |

`to_json()` gains one key (FR-002/FR-005):

```python
{
    "validator": self.validator,
    "reason": self.reason,
    "kind": self.kind.value,
    "code": self.code,          # NEW — additive; null when unset
}
```

`code` is placed **last** (additive, like 044's `kind` was added after `reason`); no key is
renamed or reordered relative to the pre-044 contract beyond appending.

### `NotEvaluated` (raised, form (b)) — `validation/base.py`

**Unchanged.** Signature stays `(reason, kind=missing_input)` (FR-004). The discriminator
belongs to returned abstentions only; the runner stamps its `NotEvaluatedResult.code` as
`None`.

## State transition — `character_unknown_mentions` (FR-013)

The one structural change a validator undergoes (forced by FR-004 — the raised path cannot
carry a `code`):

```text
BEFORE (form (b), raised total abstention):
    raise NotEvaluated(<reason>, kind=NotEvaluatedKind.pending_capability)

AFTER (form (c), returned partial abstention):
    return EvalResult(
        [],
        [Abstention(<reason>, kind=NotEvaluatedKind.pending_capability,
                    code="undeclared_characters")],
    )
```

Wire-observational delta: **only** the `code` key (`null` → `"undeclared_characters"`).
`reason`, `kind`, `validator`, and the `(validator, reason)` sort position are identical, so
the 051/052 nudge fires in exactly the same states.

## `focalization` abstention set, by declared voice (FR-006/007/008/009/014)

| Declared voice | Return form | `not_evaluated` abstentions emitted |
|---|---|---|
| 3rd **limited** | `EvalResult(_first_person_breaks(...), [head_hopping, first_person_recall])` | `Abstention(_HEAD_HOPPING_PENDING, pending_capability, code="head_hopping")` **and** `Abstention(_FIRST_PERSON_RECALL_PENDING, pending_capability, code="first_person_recall")` |
| 3rd **non-limited** | `EvalResult(_first_person_breaks(...), [first_person_recall])` (was a bare `list`) | `Abstention(_FIRST_PERSON_RECALL_PENDING, pending_capability, code="first_person_recall")` |
| **1st person** | `return []` (unchanged) | none |
| input gaps (no constitution / no voice / `[PENDING]` / no person) | `raise NotEvaluated(..., missing_input)` (×4, unchanged) | one `missing_input` entry, `code: null` |

New module constant (`focalization.py`):

```python
_FIRST_PERSON_RECALL_PENDING = (
    "full first-person recall requires semantic judgment (move 3); "
    "the deterministic check only covers the explicit subject pronoun"
)
```

The head-hopping `Abstention` (existing) gains `code="head_hopping"`. `_first_person_breaks`,
the `_FIRST_PERSON` regex, the dialogue exemption, the first-person branch, and all four
`raise NotEvaluated` sites are **untouched** (FR-009/FR-010/FR-011).

## `code` value vocabulary (free-form, owned by validators)

| `code` | Emitter | `kind` | Nudge keyed on it |
|---|---|---|---|
| `"undeclared_characters"` | `character_unknown_mentions` | `pending_capability` | `judge_undeclared_characters` (051) |
| `"head_hopping"` | `focalization` (limited-third only) | `pending_capability` | `judge_head_hopping` (052) |
| `"first_person_recall"` | `focalization` (both 3rd branches) | `pending_capability` | **none yet** (054) |
| `None` (`null`) | `focalization`'s four `missing_input` raises; the `ingestion` skip entries | `missing_input` | `activate_dormant_validators` (keys on `kind`, not `code`) |

No closed enum (spec Assumptions): three live values, each colocated with its validator.

## Sort invariance (FR-005a)

`not_evaluated_sort_key` stays `(validator, reason)`. `focalization`'s two entries are
ordered by `reason`: `"full first-person recall…"` (`f`) precedes `"head-hopping /
interiority…"` (`h`), a fixed total order. `code` is **not** a sort term.

## Status flow (no new fields)

`status/model.py:ValidationSummary.not_evaluated` already holds
`tuple[NotEvaluatedResult, ...]`; `status/queries.py:validation_summary` passes the runner's
output through unchanged. So `code` reaches `_judges` (which reads `r.code`) and the
`status` payload (via `NotEvaluatedResult.to_json`) with **no** edit to `model.py` or
`queries.py` — verify-only.
