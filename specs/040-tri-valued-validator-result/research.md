# Research: Tri-valued validator result

The spec is fully clarified (two clarifications recorded; the per-validator
predicates are resolved in FR-008/FR-009). Phase 0 therefore resolves a single open
**mechanism** question (FR-001) plus the small downstream shape choices. Format per
entry: **Decision / Rationale / Alternatives considered**.

---

## D1 — How a validator signals not-evaluated (the contract mechanism)

**Decision.** A validator signals not-evaluated by **raising a dedicated
`NotEvaluated(reason)` exception** (a plain `Exception` subclass, *not* a
`BookwrightError`). The runner — already the per-validator try/except isolation
boundary — catches `NotEvaluated` in a clause placed **before** its generic
`except Exception` handler and records a `NotEvaluatedResult(validator, reason)` in
a new channel. `Validator.validate` keeps its return type **`list[Violation]`,
unchanged**.

**Rationale.**

- **FR-001's hard constraint is the decider.** The contract "MUST NOT leave the
  runner permanently sniffing the return type or carrying a dual-shape return
  contract as a justified smell (zero-debt doctrine §3 — eliminate the cause)."
  Raising keeps `validate`'s return type pure (`list[Violation]`); the not-evaluated
  signal travels out-of-band. There is **no** `list | Outcome` union and **no**
  `isinstance` on a return value anywhere. The forbidden residue simply never exists
  — nothing to record in `DEBT.md`.
- **FR-014 backward compatibility is free.** A custom validator returning a bare
  `list[Violation]` still satisfies the unchanged Protocol and is read as
  **evaluated** without edits. It never raises `NotEvaluated`, so it is never
  not-evaluated (matching the Edge Case requirement).
- **It reuses the architecture already present.** `run_validators` *already* wraps
  each `validate()` in try/except to isolate crashes (FR-014). Adding one typed
  `except NotEvaluated` clause before the generic handler is consistent with that
  design, not a new construct. The ordering keeps "crashes vs. consciously skips"
  cleanly separated **by type**: a crash is any other `Exception` → `errors[]`
  (`ValidatorError`, shape unchanged, FR-006); a conscious skip is `NotEvaluated` →
  `not_evaluated[]`. The two channels can never be conflated (Edge Case 1, FR-005).
- **The decision is computed where it is known.** `focalization`'s not-evaluated
  verdict (e.g. "no grammatical person resolved") is decided *inside* the same parse
  that would feed the scan. Raising at that point needs no second pass and no cached
  precondition; the early `return []` lines become `raise NotEvaluated(reason)`
  one-for-one.

**Alternatives considered.**

- **Explicit `ValidationOutcome` return (`evaluated`, `reason`, `violations`),
  `validate -> list[Violation] | ValidationOutcome`.** The user offered this as one
  option, but it is *exactly* the dual-shape return contract FR-001 forbids: the
  runner must `isinstance`-sniff every return value forever, and a bare list must be
  normalized into an outcome. That residue would have to be justified in `DEBT.md`.
  Rejected because a clean alternative exists.
- **Uniform `ValidationOutcome` return for every validator.** Removes the union, but
  breaks FR-014: a custom validator returning `list[Violation]` no longer
  type-checks unless the runner normalizes it — which reintroduces the sniffing.
  Rejected.
- **A separate optional precondition method (`not_evaluated_reason(project,
  indexer) -> str | None`) the runner calls before `validate`.** No dual return
  shape, but it forces the precondition logic to run *separately* from the scan;
  `focalization` would parse the voice declaration twice (once to decide
  evaluability, once to scan), duplicating logic — a new smell. Rejected.
- **A sentinel `Violation` of severity `info`.** Explicitly rejected by the user and
  the spec (Edge Case): it would conflate "not evaluated" with "informational
  finding" and risk leaking into the gate/severity machinery. Rejected.

---

## D2 — The `not_evaluated` record shape

**Decision.** A frozen dataclass `NotEvaluatedResult(validator: str, reason: str)`
in `validation/base.py`, sibling to `ValidatorError`, with
`to_json() -> {"validator": …, "reason": …}`. The raised signal
`NotEvaluated(Exception)` carries only `reason: str`; the runner stamps the
validator name from `validator.name` (the validator never needs to name itself,
mirroring how `ValidatorError` is built in the runner).

**Rationale.** Keeps `Violation` and `ValidatorError` shapes untouched (FR-006);
the new record is a third, distinct type. Stamping the name in the runner keeps the
signal minimal and impossible to mislabel. Frozen + 2 string fields → trivially
deterministic and JSON-friendly.

**Alternatives considered.** Reusing `ValidatorError` with a third `phase` value
(`"skip"`) — rejected: it would conflate the channel FR-005 requires distinct and
change `ValidatorError`'s value space (a consumer asserting `phase in {load, run}`
breaks).

---

## D3 — The `--json` envelope channel and the "green" predicate (SC-002)

**Decision.** The `validate` envelope gains a top-level `"not_evaluated"` array of
`{validator, reason}`, sibling to `"violations"` and `"errors"`, sorted by validator
name (FR-013). `status` is left two-valued (`"ok"` / `"violations"`). **Green/clean
is the single documented predicate `status == "ok" AND not_evaluated == []`.** A run
whose `not_evaluated` channel is non-empty never satisfies it; a fully-not-evaluated
run (no violations) has `status == "ok"` but a non-empty channel, so it is **not**
green.

**Rationale.** Additive (no existing key changes shape, Principle IX / FR-007). The
spec itself offers this exact predicate form as the example (SC-002). Keeping
`status` two-valued avoids breaking any consumer asserting `status in
{"ok","violations"}`; the third state lives in its own channel, read by conjunction.
The human (non-JSON) report mirrors this: a dedicated "not evaluated:" section, and
the "no violations found" clean line is suppressed whenever the channel is non-empty.

**Alternatives considered.** A third `status` value `"not_evaluated"` — rejected:
changes the value space of an existing key and forces a two-way split when both
violations and not-evaluated validators coexist (`status` cannot be both). The
sibling-channel + conjunction is unambiguous and additive.

---

## D4 — `status` integration: derived state + activation action (FR-010/SC-004)

**Decision.** `ValidationSummary` gains
`not_evaluated: tuple[NotEvaluatedResult, ...]`; `to_payload` adds a
`"not_evaluated": [{validator, reason}, …]` key under `state.validation`.
`status/queries.validation_summary` reads the runner's new 4-tuple and fills it. A
new pure rule `activate_dormant_validators` in `rules.py` applies when
`state.validation.not_evaluated` is non-empty and builds one `Action` whose prompt
enumerates each dormant validator with a concrete remedy drawn from a static
`_REMEDIES: dict[str, str]` map — `focalization` → "declare the narrative voice in
the constitution", the manuscript-empty validators → "add manuscript prose". The
rule is placed after `review_continuity` and before `define_focus` in `RULES`
(priority order, FR-010).

**Rationale.** Satisfies SC-004 (a `next_actions` step that names the focalization
remedy by name) while keeping the rule table pure (`state → list[Action]`, no I/O).
The reason strings carried by `NotEvaluatedResult` are generic English; the concrete
remedy comes from the static map keyed by validator name, so the action is both
deterministic (FR-013) and concrete. Validators without a mapped remedy contribute
nothing to the action (FR-010 "where an actionable remedy exists").

**Alternatives considered.** Per-validator `Action`s (one per dormant validator) —
rejected for table consistency (every existing rule yields exactly one `Action`); a
single enumerated prompt is equally concrete and keeps the report compact.

---

## D5 — Per-validator not-evaluated triggers (already resolved by the spec)

The spec resolves these in FR-008/FR-009 and the Edge Cases; research only confirms
they map cleanly onto D1's raise-at-decision-point:

- **`focalization` (FR-008, four reasons).** The current `validate` early-returns
  `[]` when `declaration is None or declaration.person is None`. That single branch
  covers four causes; to give a distinct reason per cause, `_parse_declaration`
  returns enough to distinguish them, and `validate` raises `NotEvaluated` with:
  (i) no constitution — `project.constitution_view()` is `()`; (ii) no parseable
  declaration — no line matches `_DECLARATION`; (iii) placeholder — `is_placeholder`
  on the body (reusing the iteration-039 seam); (iv) declaration present but no
  person (`person is None`). A usable first/third person → **evaluated** (may emit
  zero findings — a legitimate green, FR-003). The enumeration is exhaustive over the
  early-return condition, so no "could not look" path returns `[]` (FR-008).
- **`setting_continuity` (FR-009).** Its sole input is manuscript prose. When
  `project.manuscript_view()` is empty (no readable prose), raise
  `NotEvaluated("the manuscript is empty")`; otherwise evaluate as today.
- **`character_presence` (FR-009).** Two directions. Raise `NotEvaluated` **only**
  when *both* inputs are empty — no manuscript prose **and** an empty roster
  (`not files and not roster`). An empty manuscript with a non-empty roster stays
  **evaluated** and emits its `error`-level orphan findings byte-for-byte unchanged
  (the rule that protects the gate, FR-004/FR-012).

**Determinism / parity note (FR-012/FR-013/SC-003).** Every migrated trigger fires
*only* on an input shape that today produces `[]` (no violations), so no existing
fixture's `Violation` count changes — the not-evaluated state is purely additive over
inputs that were already empty-result. Verify empirically; never weaken a trigger to
make a test pass.
