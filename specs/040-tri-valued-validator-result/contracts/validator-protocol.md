# Contract: the tri-valued validator protocol

Supersedes the v0 `validator-protocol.md` "empty list means OK" reading for the
not-evaluated dimension. Binds `validation/base.py`, `validation/runner.py`, and
`bookwright-design.md § 13.1`.

## The verdict (per validator, per run)

| Verdict | How the validator expresses it | Where it surfaces | Gates CI? |
|---|---|---|---|
| **evaluated, no findings** | `return []` | nowhere (counts as clean) | no |
| **evaluated, findings** | `return [Violation, …]` | `violations[]` | yes, iff any `error` |
| **not-evaluated(reason)** | `raise NotEvaluated(reason)` | `not_evaluated[]` | no |
| **crashed (load/run)** | raises any other `Exception` (or fails to load) | `errors[]` (`ValidatorError`) | no |

- The verdict is **whole-validator**: a validator that returns a list is evaluated
  even if the list is empty; it is not-evaluated only when it raises `NotEvaluated`
  (it then contributes no findings). No partial/per-sub-check state.
- `Validator.validate` return type is **`list[Violation]` — unchanged**. The
  not-evaluated signal is out-of-band (raised), so there is no `list | Outcome`
  union and the runner never sniffs a return value (FR-001).
- **Backward compatibility (FR-014):** a custom validator that returns a bare
  `list[Violation]` and never raises `NotEvaluated` keeps working unchanged and is
  always **evaluated**.

## `NotEvaluated` vs `ValidatorError` (must never be conflated, FR-005)

| | `NotEvaluated` | `ValidatorError` |
|---|---|---|
| Trigger | validator ran without error, consciously had no input | validator failed to load, or raised any other exception |
| Type | `NotEvaluated(Exception)` (not a `BookwrightError`) | recorded by the runner / discovery |
| Channel | `not_evaluated[]` | `errors[]` |
| Caught | a dedicated `except NotEvaluated` **before** the generic handler | the generic `except Exception` |

## Runner obligations

1. Catch `NotEvaluated` **before** `except Exception`; record
   `NotEvaluatedResult(validator.name, exc.reason)`; `continue` (no findings from
   that validator).
2. Any other exception → `ValidatorError(phase="run")` as today (FR-014).
3. Emit `not_evaluated` sorted by validator name (FR-013); a validator appears at
   most once.
4. `RunResult` becomes `(violations, errors, not_evaluated, ran)`.

## Reason strings (FR-002)

English, fixed templates, no minted data. Canonical set for the migrated validators:

| Validator | Reason |
|---|---|
| `focalization` (i) | `the constitution does not declare a narrative voice` *(no constitution / no parseable declaration share this OR are split — see FR-008 i & ii)* |
| `focalization` (ii) | `the constitution does not declare a narrative voice` |
| `focalization` (iii) | `the narrative-voice declaration is still unanswered ([PENDING])` |
| `focalization` (iv) | `the narrative-voice declaration names no grammatical person (neither first nor third)` |
| `setting_continuity` | `the manuscript is empty` |
| `character_presence` | `there is no manuscript prose and no bible character roster to cross-check` |

> FR-008 requires a **distinct** reason per *cause*; (i) "no constitution" and (ii)
> "no parseable voice declaration" MAY share the user-facing wording (both mean "no
> voice is declared") or be split — planning leaves the exact wording of (i)/(ii) to
> implementation, but each of the four early-return branches MUST route to
> `NotEvaluated`, none may keep returning `[]`. The placeholder (iii) and no-person
> (iv) reasons are distinct and fixed.
