# Data Model: Tri-valued validator result

In-memory only (the validation subsystem persists nothing). New types live beside
the existing ones in `validation/base.py`; `Violation` and `ValidatorError` shapes
are **unchanged** (FR-006).

## New types (`validation/base.py`)

### `NotEvaluated` — the signal (an exception)

```python
class NotEvaluated(Exception):
    """A validator's opt-in signal that it consciously did not evaluate (FR-001).

    Raised from inside ``validate`` when the validator has no input for ANY of its
    checks. NOT a ``BookwrightError`` (it is not an error envelope) and NOT a
    failure: the runner catches it BEFORE its generic handler and records a
    ``NotEvaluatedResult`` in the ``not_evaluated`` channel, never in ``errors[]``.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
```

- `reason: str` — human-readable, **English** (FR-002), e.g. `"the constitution does
  not declare a narrative voice"`. The validator never names itself; the runner
  stamps the name (D2).
- Backward compatibility: a validator that never raises it is always evaluated
  (FR-014). The `Validator` Protocol's `validate` return type is **unchanged**
  (`-> list[Violation]`).

### `NotEvaluatedResult` — the record (frozen)

```python
@dataclass(frozen=True)
class NotEvaluatedResult:
    """One validator that ran without error but consciously did not evaluate.

    Sibling to ``ValidatorError``; surfaced in the ``not_evaluated`` channel. It is
    not a finding (no severity, never gates) and not a load/run error (FR-005).
    """

    validator: str
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {"validator": self.validator, "reason": self.reason}
```

Frozen + two string fields → hashable, trivially deterministic, JSON-friendly.

## Changed types / signatures

### `Validator` Protocol — docstring only

The `validate(self, project, indexer) -> list[Violation]` signature is **unchanged**.
The docstring is updated to document that a validator MAY `raise NotEvaluated(reason)`
to declare it had no input for any check; an empty list still means "evaluated, no
findings" (a legitimate green, FR-003). Custom validators returning a bare list keep
working (FR-014).

### `runner.RunResult` and `run_validators`

```python
RunResult = tuple[
    list[Violation],            # deduped, sorted findings (unchanged)
    list[ValidatorError],       # load/run errors (unchanged)
    list[NotEvaluatedResult],   # NEW — sorted by validator name (FR-013)
    list[str],                  # ran names, sorted (unchanged)
]
```

`run_validators` gains, inside its per-validator loop, a clause **before** the
generic `except Exception`:

```python
try:
    found = validator.validate(project, indexer)
except NotEvaluated as skip:                 # conscious skip → not_evaluated channel
    not_evaluated.append(NotEvaluatedResult(validator.name, skip.reason))
    continue
except Exception as exc:                      # crash → errors[] (unchanged, FR-014)
    errors.append(ValidatorError(validator.name, f"{type(exc).__name__}: {exc}", "run"))
    continue
```

`not_evaluated` is sorted by `validator` before return (each validator appears at
most once — whole-validator verdict, so no dedupe needed beyond the natural one).

### `ValidationReport`

Gains `not_evaluated: tuple[NotEvaluatedResult, ...]`. `to_json` adds a top-level
`"not_evaluated"` key (sibling of `violations`/`errors`). `render` gains a
"not evaluated:" section and suppresses the "no violations found" clean line whenever
the channel is non-empty. `failed` (the gate) is **unchanged** — not-evaluated never
gates (FR-004).

### `status.ValidationSummary`

Gains `not_evaluated: tuple[NotEvaluatedResult, ...] = ()` (defaulted empty, last
field). `to_payload` adds `"not_evaluated": [r.to_json() for r in self.not_evaluated]`
under `state.validation` (additive). `validation_summary` reads the runner's 4-tuple
and fills it. The default keeps the degraded-path construction
`ValidationSummary(counts={}, ran=())` in `commands/status.py` (the no-prerequisite
branch of `_aggregate`) working **unchanged**, so the new key is always present even
on the degraded path and `status.py` needs no edit.

### `status.rules`

New `Rule("activate_dormant_validators", …)` + `_REMEDIES: dict[str, str]` static
map. Applies when `state.validation.not_evaluated` is non-empty; builds one `Action`
naming each dormant validator that has a remedy (`focalization` → declare the
narrative voice; manuscript-empty validators → add manuscript prose). Placed after
`review_continuity`, before `define_focus`.

## State transition (the verdict)

```
                 raises NotEvaluated(reason)
validate() ─────────────────────────────────► NOT-EVALUATED  (reason; no findings)
     │
     └── returns list[Violation] ───────────► EVALUATED
                                               ├── [] ............ clean (green)
                                               └── [v, …] ........ findings (gates iff any error)
```

The verdict is **whole-validator**: a validator is EVALUATED if it returns a list
(possibly empty) and NOT-EVALUATED only if it raises (no findings then). There is no
partial/per-sub-check state (clarification; Edge Case 2). A crash is neither — it is
a `ValidatorError` in `errors[]`.

## Determinism

- `not_evaluated[]` sorted by validator name, like `violations[]`/`errors[]` (FR-013).
- `reason` strings are fixed English templates (FR-002) — no clock, URI, or env data,
  so the channel and the derived `status` payload are byte-identical across runs.
