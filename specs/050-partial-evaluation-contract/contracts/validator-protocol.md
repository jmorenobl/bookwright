# Contract: the three-shape `validate()` return (iteration 050)

The seam between `run_validators` and any validator. This iteration adds a
**third** accepted return shape; the two existing shapes are unchanged. The
runner normalizes all three into its existing `violations[]` / `not_evaluated[]` /
`errors[]` channels — no new channel, sort key, or `--json` envelope key.

## The contract

```python
class Validator(Protocol):
    name: str
    severity_default: Severity
    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation] | EvalResult: ...
```

A validator's `validate()` does **exactly one** of:

| # | Shape | Meaning | Runner routing |
|---|---|---|---|
| (a) | `return list[Violation]` (possibly `[]`) | evaluated; these are the findings | findings → dedup + `sort_key` → `violations[]` |
| (b) | `raise NotEvaluated(reason, kind)` | **total** abstention; did not evaluate any check | one `not_evaluated[]` entry; **no** findings |
| (c) | `return EvalResult(violations, not_evaluated)` | **partial**: evaluated some dimension(s) **and** abstained on other(s) in the same run | `violations` → dedup + `sort_key` → `violations[]`; each `Abstention` → one `not_evaluated[]` entry |

A validator that raises any **other** exception is isolated as
`ValidatorError(phase="run")` in `errors[]` (unchanged, FR-014).

## Invariants (MUST)

- **C1 — back-compat (FR-007)**: every validator returning shape (a) or raising
  shape (b) keeps working **without being touched**. A custom validator returning a
  bare `list[Violation]` still satisfies the Protocol and `mypy --strict`.
- **C2 — single name-stamping point (FR-002)**: the validator **never** names
  itself. The runner stamps `validator.name` onto every `not_evaluated[]` entry,
  for **both** shape (b) and shape (c), through the **same** point
  (`_record(name, reason, kind)`). The stamping authority MUST NOT fork.
- **C3 — `Abstention` carries only `(reason, kind)`**: with the same closed
  `NotEvaluatedKind` vocabulary and the same `missing_input` default as
  `NotEvaluated`.
- **C4 — no new channel/key/sort (FR-002)**: shape (c)'s findings use the existing
  dedup + `sort_key`; its abstentions use the existing `not_evaluated_sort_key`
  (`(validator, reason)`). `RunResult` stays the 4-tuple `(violations, errors,
  not_evaluated, ran)`.
- **C5 — observational equivalence (FR-012)**: `EvalResult([], [Abstention(r,
  k)])` is indistinguishable on the wire from `raise NotEvaluated(r, k)` — both
  yield one `not_evaluated` entry and zero findings.
- **C6 — determinism (design § 13.1)**: output is byte-stable; shape (c) adds no
  nondeterminism (`_first_person_breaks` already emits one finding per file,
  citing the first break).

## `focalization` — the first and only consumer of shape (c)

| Voice precondition | Shape | Behavior |
|---|---|---|
| no constitution / no voice / `[PENDING]` / no grammatical person | (b) `raise NotEvaluated(..., missing_input)` | **unchanged** — total abstention, byte-for-byte reason strings |
| first person | (a) `return []` | **unchanged** — evaluated, no findings |
| third, **non-limited** (omniscient) | (a) `return self._first_person_breaks(view)` | **unchanged** — the deterministic break check |
| third, **limited/focalized** | **(c)** `return EvalResult(self._first_person_breaks(view), [Abstention(_HEAD_HOPPING_PENDING, pending_capability)])` | **new** — runs the break check **and** abstains on head-hopping in the same run (closes DEBT-019) |

The first-person-break finding under limited-third is identical in shape to the
one under non-limited third (validator `focalization`, `severity = warning`, same
message wording, a `relpath:line` `source`, `triples = ()`) — FR-004. The
head-hopping abstention's `kind` stays `pending_capability`, so by the 044
predicate it does **not** deny green and does **not** trigger the dormant-validator
nudge (FR-005).

## Out of scope (this contract does NOT change)

- The 044 green predicate, the `NotEvaluatedKind` enum, the `not_evaluated[]`
  serialization, the `status` nudge, the error-only CI gate — **consumed**, not changed.
- Any other validator (`character_unknown_mentions` keeps its **total**
  abstention — no deterministic half to recover), command, envelope, or `.ttl`.
- Move 3 (head-hopping stays `not_evaluated` until then).
