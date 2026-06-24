# Data model: partial-evaluation contract (iteration 050)

In-memory only; the validation subsystem persists nothing (design § 13.1). Every
new type is a frozen dataclass, hashable, `mypy --strict`-clean.

## New types (`validation/base.py`)

### `Abstention` (new, frozen)

The **returned-not-raised** sibling of `NotEvaluated`: one partial abstention a
validator declares **alongside** findings. Carries only `(reason, kind)` — the
validator never names itself; the runner stamps the registered name (FR-002).

| Field | Type | Default | Notes |
|---|---|---|---|
| `reason` | `str` | — | Fixed English text, deterministic (no minted data), exactly as `NotEvaluated.reason`. |
| `kind` | `NotEvaluatedKind` | `missing_input` | Same closed vocabulary and **same default** as `NotEvaluated`, so an `Abstention(reason)` and a `NotEvaluated(reason)` declare the gap identically. |

Mirrors `NotEvaluated.__init__`'s `(reason, kind)` shape so the runner converts
either to `NotEvaluatedResult(name, reason, kind)` through one stamping point.

### `EvalResult` (new, frozen) — form (c)

The partial carrier a validator MAY **return** instead of a bare `list[Violation]`.

| Field | Type | Default | Notes |
|---|---|---|---|
| `violations` | `list[Violation]` | — | Findings (possibly empty), routed to the existing dedup + `sort_key` path exactly as a bare list. |
| `not_evaluated` | `list[Abstention]` | — | One or more abstentions, each → one `not_evaluated[]` entry under the runner-stamped name. |

**Invariant**: an `EvalResult([], [Abstention(r, k)])` is observationally equal to
`raise NotEvaluated(r, k)` — both yield one `not_evaluated` entry and zero
findings. This equality keeps the three focalized fixtures byte-identical (FR-012).

> `list` fields (not tuples) are intentional: `EvalResult` is a transient carrier
> consumed once by the runner and never hashed/deduped as a whole (only its
> `Violation`s are deduped, and `Violation` is already frozen/hashable). It need
> not itself be frozen-hashable, but is declared `@dataclass(frozen=True)` for
> immutability consistency with the module's other result types.

## Changed contract (`validation/base.py`)

### `Validator` Protocol — widened return

```python
def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation] | EvalResult: ...
```

A custom validator returning a bare `list[Violation]` still satisfies the Protocol
(`list[Violation]` is one arm of the union). Forms (a) and (b) are unchanged
(FR-007).

## Unchanged types (explicitly not modified)

| Type | Why unchanged |
|---|---|
| `Violation` | Form (c)'s findings are ordinary `Violation`s; shape identical (FR-004). |
| `NotEvaluated` (exception) | Form (b), the **total**-abstention shortcut, is kept (FR-001/FR-006). Still a plain `Exception`. |
| `NotEvaluatedResult` | The runner-stamped `not_evaluated[]` element; form (c) produces these via the same stamping point as form (b) (FR-002). |
| `NotEvaluatedKind` | The closed `{missing_input, pending_capability}` vocabulary is consumed, not changed (FR-005, out of scope). |
| `ValidatorError` | Crashes still land in `errors[]`; unrelated. |
| `RunResult` (`runner.py`) | Still the same 4-tuple `(violations, errors, not_evaluated, ran)`; both consumers (`commands/validate.py`, `status/queries.py`) unchanged (FR-016). |

## Runner state machine (`run_validators`, three shapes → existing channels)

```
found = validator.validate(project, indexer)
├── raises NotEvaluated(reason, kind)   → form (b): _record(name, reason, kind) → not_evaluated[]; continue
├── raises any other Exception          → ValidatorError(name, …, "run") → errors[]; continue   (unchanged)
├── isinstance(found, EvalResult)       → form (c): findings = found.violations
│                                          for ab in found.not_evaluated:
│                                              _record(name, ab.reason, ab.kind) → not_evaluated[]
└── else (bare list[Violation])         → form (a): findings = found                              (unchanged)

findings → dedup against `seen` → violations[]            (single shared dedup loop)
violations.sort(sort_key); not_evaluated.sort(not_evaluated_sort_key)   (unchanged)
```

`_record(name, reason, kind) -> NotEvaluatedResult` is the **single** name-stamping
point shared by forms (b) and (c) (FR-002).

## `__all__` / exports

`validation/base.py` `__all__` gains `"Abstention"` and `"EvalResult"` (sorted
into place). `validation/__init__.py` re-exports as needed by tests (the test
imports them from `validation.base` directly, as it does `NotEvaluated`).
