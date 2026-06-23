# Phase 1 — Data Model: `not_evaluated` kinds

All types live in `src/bookwright/validation/base.py` unless noted. The change is
**additive**: one new enum and one new field on each of two existing types; no
pre-existing field is renamed or retyped (SC-007).

## `NotEvaluatedKind` (new)

```python
class NotEvaluatedKind(StrEnum):
    """Why a validator consciously did not evaluate (iteration 044, design § 13.4).

    A small closed vocabulary mirroring :class:`Severity`. The wire value is the
    member name; carried on the not-evaluated signal and its recorded result.
    """

    missing_input = "missing_input"        # input-conditional, actionable, per-project, transient (the 040 default)
    pending_capability = "pending_capability"  # permanent capability-gap, not author-actionable, identical everywhere
```

- **Closed set, exactly two values** (FR-001). String-valued for JSON (`.value`).
- `missing_input` is the **default** everywhere a kind is omitted (FR-002).

## `NotEvaluated` (exception) — gains `kind`

```python
class NotEvaluated(Exception):
    def __init__(
        self, reason: str, kind: NotEvaluatedKind = NotEvaluatedKind.missing_input
    ) -> None:
        self.reason = reason
        self.kind = kind
        super().__init__(reason)
```

- `kind` is the **last** parameter with a default → every existing
  `raise NotEvaluated(reason)` is unchanged and yields `missing_input` (FR-002,
  edge case "custom validator defaults to input-conditional").
- The validator declares the kind at raise time — the only place that knows
  whether the gap is about *this input* or about the *approach* (spec Assumption).

## `NotEvaluatedResult` (frozen dataclass) — gains `kind`

```python
@dataclass(frozen=True)
class NotEvaluatedResult:
    validator: str
    reason: str
    kind: NotEvaluatedKind = NotEvaluatedKind.missing_input

    def to_json(self) -> dict[str, Any]:
        return {
            "validator": self.validator,
            "reason": self.reason,
            "kind": self.kind.value,   # additive key (FR-008, SC-007)
        }
```

- `kind` is the **last** field with a default → existing constructions
  `NotEvaluatedResult(name, reason)` keep working (tests, any caller).
- `to_json` gains exactly one key, `kind`; `validator` and `reason` are byte-identical.

## Raise inventory (validator → kind)

| Validator | Raise reason (unchanged) | Kind |
|---|---|---|
| `focalization` | "there is no constitution to read the narrative voice from" | `missing_input` (default) |
| `focalization` | "the narrative-voice declaration names no grammatical person (neither first nor third)" | `missing_input` |
| `focalization` | "the constitution does not declare a narrative voice" | `missing_input` |
| `focalization` | "the narrative-voice declaration is still unanswered ([PENDING])" | `missing_input` |
| `setting_continuity` | "the manuscript is empty" | `missing_input` |
| `character_presence` | "there is no manuscript prose and no bible character roster to cross-check" | `missing_input` |
| any custom third-party validator | (its own reason) | `missing_input` (default) |
| **`character_unknown_mentions`** | "open-set proper-noun discovery requires semantic judgment (move 3); the deterministic heuristic was measured insufficient on real prose" | **`pending_capability`** (FR-003) |

## Runner stamping (`validation/runner.py`)

```python
except NotEvaluated as skip:  # conscious skip → not_evaluated channel (FR-005)
    not_evaluated.append(NotEvaluatedResult(validator.name, skip.reason, skip.kind))
    continue
```

The kind is stamped onto the recorded result alongside the validator name and
reason. Sorting (`not_evaluated.sort(key=lambda r: r.validator)`) is unchanged.

## Derived predicate (refined)

The **green/clean** predicate (documented in `report.py` docstring + design
§ 13.4; asserted via the `_is_green(payload)` test helpers — no code property):

> green ⟺ `status == "ok"` **and** no `not_evaluated` entry has
> `kind == "missing_input"`.

- A `pending_capability` entry does **not** deny green (FR-004).
- An `error`, or any `missing_input` entry, denies green.
- The CI **gate** is independent of this and unchanged: only an `error` `Violation`
  fails CI (FR-009) — neither kind of `not_evaluated` gates.

## Status surfaces (`status/model.py`, `status/rules.py`)

- `ValidationSummary.not_evaluated: tuple[NotEvaluatedResult, ...]` — type
  unchanged; `to_payload` already delegates to `r.to_json()`, so `kind` appears in
  `state.validation.not_evaluated[]` automatically (no edit).
- `_activate_dormant_validators` consumes only the `missing_input` subset:
  ```python
  dormant = [r for r in state.validation.not_evaluated
             if r.kind is NotEvaluatedKind.missing_input]
  ```
  and the `activate_dormant_validators` rule's `applies` predicate tests for any
  such entry. The 043 `_REMEDIES["character_unknown_mentions"]` clause is removed
  (FR-006).

## Human report (`validation/report.py`)

- `_KIND_LABEL: dict[NotEvaluatedKind, str]` — a short, English, **kind-generic**
  label (FR-007); the validator-specific "move 3" detail stays in `reason`.
- The `not evaluated:` section renders `  {validator} [{label}]: {reason}`.
- The clean-line early-return (`if not reported and not self.errors and not
  self.not_evaluated:`) is **unchanged** — both kinds keep it suppressed so a
  capability-gap entry stays visible (FR-010, edge case).
