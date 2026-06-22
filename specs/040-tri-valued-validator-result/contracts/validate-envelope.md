# Contract: `bookwright validate --json` envelope (tri-valued)

Additive change to the Principle-IX envelope. **No existing key changes shape**
(FR-007); one new top-level sibling key `not_evaluated` joins `violations`/`errors`.

## Shape

```jsonc
{
  "status": "ok" | "violations",          // UNCHANGED value space (D3)
  "failed": false,                          // UNCHANGED: gate over unfiltered errors
  "violations": [ /* Violation.to_json() */ ],
  "errors":     [ /* ValidatorError.to_json() */ ],
  "not_evaluated": [                        // NEW — sorted by validator name (FR-013)
    { "validator": "focalization", "reason": "the constitution does not declare a narrative voice" }
  ],
  "summary": {
    "ran": ["character_presence", "focalization", "setting_continuity", "..."],
    "total": 0, "reported": 0,
    "by_severity": { "error": 0, "warning": 0, "info": 0 }
  }
}
```

- `not_evaluated` is **unfiltered** by `--scope` / `--severity` (it carries no
  source location and no severity); it always reflects the full run, like the gate.
- `errors` keeps its exact shape (`{validator, phase, message}`); a crash never
  appears in `not_evaluated` (FR-005).
- `Violation` / `ValidatorError` JSON shapes are byte-unchanged (FR-006).

## The green / clean predicate (SC-002)

> A run is **green/clean** iff `status == "ok" AND not_evaluated == []`.

Consequences asserted by tests:

- For **every** run whose `not_evaluated` channel is non-empty, the predicate is
  **False** — including a run that is *entirely* not-evaluated (`violations == []`,
  `status == "ok"`, but `not_evaluated != []`): it is **not** green (SC-002, US1/US2
  Independent Tests).
- For an evaluated-and-clean run (`status == "ok"`, `not_evaluated == []`) the
  predicate stays **True**.
- The predicate is documented in `report.py` (the single place "clean" is defined),
  so no consumer re-derives it.

## Human (non-`--json`) report

- A dedicated `not evaluated:` section lists `validator: reason` lines, grouped after
  validator findings and distinct from `validator errors:`.
- The "no violations found" clean line is printed **only** when there are no reported
  violations, no errors, **and** no not-evaluated validators. A run that is solely
  not-evaluated prints the not-evaluated section instead of the clean line.

## Exit code

Unchanged: exit 1 iff `failed` (any unfiltered `error`-severity `Violation`); else
exit 0. A solely-not-evaluated run exits 0 (it is not a finding) but is **not**
reported as a clean pass (Edge Case "the gate").
