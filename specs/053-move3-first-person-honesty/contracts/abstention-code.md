# Contract: the abstention `code` discriminator (base + runner + serialization)

The additive contract field that lets a single validator's multiple abstentions stay
distinguishable on the wire and in `status`. Modeled byte-for-byte on the iteration-044
`kind` addition.

## C1 — field shape (`validation/base.py`)

- `Abstention` gains `code: str | None = None` (FR-001).
- `NotEvaluatedResult` gains `code: str | None = None` (FR-002).
- Both stay `@dataclass(frozen=True)`.
- The `NotEvaluated` **exception** does **not** gain `code` (FR-004) — its signature stays
  `(reason, kind=missing_input)`.

## C2 — single stamping authority (`validation/runner.py`)

`_record` is the only place a `not_evaluated` entry is name-stamped, and it MUST stay the
only place `code` is set (FR-003 — the authority MUST NOT fork):

```python
def _record(name, reason, kind, code=None) -> NotEvaluatedResult:
    return NotEvaluatedResult(name, reason, kind, code)
```

- Form (b), `except NotEvaluated`: `_record(validator.name, skip.reason, skip.kind)` →
  `code` defaults to `None`.
- Form (c), `EvalResult` loop: `_record(validator.name, abstention.reason, abstention.kind,
  abstention.code)`.

## C3 — serialization (`NotEvaluatedResult.to_json`)

```python
{
    "validator": ...,
    "reason": ...,
    "kind": self.kind.value,
    "code": self.code,    # additive; null when unset (FR-005)
}
```

- **Every** `not_evaluated[]` entry carries the `code` key (FR-005).
- Raised abstentions serialize `code: null`; returned abstentions that set `code` serialize
  that value.
- No existing key renamed or retyped.

## C4 — sort invariance (FR-005a)

`not_evaluated_sort_key` stays `(validator, reason)`. `code` MUST NOT enter the sort. The
runner's single shared sort literal is unchanged.

## C5 — green/gate invariance (FR-016/FR-017)

- `report.py` is untouched: `GREEN = status ok AND no not_evaluated entry has kind ==
  missing_input` — byte-identical.
- `activate_dormant_validators` stays `missing_input`-only.
- The CI gate stays error-severity-only; **no `error`** is born from this change.

## C6 — verification (FR-018)

- `test_base.py`: the `code` field exists, defaults to `None`, and `to_json` emits the key
  (value `None` by default; a set value round-trips).
- runner / serialization tests: `code` stamped from a form (c) `Abstention`; `None` from a
  form (b) `raise NotEvaluated`; the additive key present on every entry.
- `test_report.py`: a `pending_capability` entry **carrying a `code`** still does not deny
  green.
