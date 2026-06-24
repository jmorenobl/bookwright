# Research: partial-evaluation contract (iteration 050)

The spec leaves exactly one thing open (Assumptions): *the concrete carrier type
of form (c) is a `/speckit-plan` decision; the spec fixes only its behavior.*
Everything else is pinned by the spec or by existing code. Decisions below.

## D1 — The carrier type for the partial abstention (the open `/speckit-plan` decision)

**Decision**: introduce a frozen `Abstention(reason: str, kind: NotEvaluatedKind =
missing_input)` in `validation/base.py` — the **returned-not-raised** sibling of
`NotEvaluated`, carrying only `(reason, kind)`. Form (c) is a frozen
`EvalResult(violations: list[Violation], not_evaluated: list[Abstention])`.

**Rationale**: FR-002 says each form-(c) abstention "carries only its `(reason,
kind)`; the **runner** stamps the validator name … the validator never names
itself." `Abstention` mirrors `NotEvaluated.__init__`'s `(reason, kind)` shape
exactly, with the **same** `missing_input` default — so `focalization`'s
`Abstention(_HEAD_HOPPING_PENDING, pending_capability)` reads identically to the
old `NotEvaluated(_HEAD_HOPPING_PENDING, kind=pending_capability)`, and the runner
converts it to `NotEvaluatedResult(name, reason, kind)` through the **same**
stamping point it uses for a caught `NotEvaluated` (FR-002: the authority must not
fork). Frozen + plain fields keep it hashable and `mypy --strict`-clean.

**Alternatives considered**:
- *Reuse the `NotEvaluated` exception instances as the list elements* (so
  `EvalResult.not_evaluated: list[NotEvaluated]`). Makes the stamping literally one
  expression, but storing **Exception instances that are never raised** as plain
  data is a code smell a quality pass would flag — and it conflates "the
  raised total-abstention signal" with "a returned partial datum." Rejected.
- *Reuse `NotEvaluatedResult` with a sentinel/empty `validator` the runner
  overwrites.* Violates FR-002 ("the validator never names itself"; the
  `NotEvaluatedResult.validator` invariant is *runner-stamped*) and forks the
  stamping authority (the validator would pre-fill a field the runner re-fills).
  Rejected.
- *No carrier — `validate` returns `tuple[list[Violation], list[Abstention]]`.* A
  bare tuple is structurally ambiguous against the existing `list[Violation]`
  return and reads worse at the call site than a named result. A named frozen
  dataclass is the project idiom (`Violation`, `NotEvaluatedResult`,
  `ValidatorError` are all frozen dataclasses). Rejected.

## D2 — Where the name is stamped (single point, FR-002)

**Decision**: a module-level helper in `runner.py`,
`_record(name, reason, kind) -> NotEvaluatedResult`, returning
`NotEvaluatedResult(name, reason, kind)`. Both paths call it:

- `except NotEvaluated as skip:` → `_record(validator.name, skip.reason, skip.kind)`
- the `EvalResult` loop → `_record(validator.name, ab.reason, ab.kind)` for each
  `ab` in `result.not_evaluated`.

**Rationale**: FR-002 — "form (c) reuses the same stamping point as form (b)."
Both `NotEvaluated` and `Abstention` expose `.reason: str` and `.kind:
NotEvaluatedKind`, so the two call sites are byte-identical except for the source
object. One helper = one definition of how a `NotEvaluatedResult` is built from a
`(name, reason, kind)`; the stamping authority cannot drift. (A helper for a
single constructor is justified here precisely because the spec makes
non-forking a hard requirement.)

## D3 — Runner normalization of the three shapes (FR-001)

**Decision**: after `found = validator.validate(project, indexer)` (still wrapped
by the existing `except NotEvaluated` / `except Exception`), branch on the
**returned** value:

```python
if isinstance(found, EvalResult):
    produced = found.violations
    for ab in found.not_evaluated:
        not_evaluated.append(_record(validator.name, ab.reason, ab.kind))
else:                       # a bare list[Violation] — form (a), unchanged
    produced = found
for violation in produced:  # the existing dedup loop, unchanged
    if violation not in seen:
        seen.add(violation)
        violations.append(violation)
```

`except NotEvaluated` (form (b)) is unchanged: it `continue`s after recording one
entry. Form (a) is the `else` branch — its findings hit the exact same dedup loop.
Form (c)'s findings hit that same loop; its abstentions hit the same
`not_evaluated` list. The final `violations.sort(key=sort_key)` and
`not_evaluated.sort(key=not_evaluated_sort_key)` are unchanged — form (c)
introduces **no** new sort key, channel, or envelope key (FR-002).

**Rationale**: minimal diff, single dedup path, single sort. `isinstance` on a
frozen dataclass is the clean discriminator between the union arms; `mypy
--strict` narrows the union correctly across the branch.

**Alternative considered**: normalize *inside* `validate` (make every validator
return `EvalResult`). Rejected — it would touch every validator (violates FR-007
"without being touched") and break the back-compat the spec mandates (form (a)
must keep working untouched).

## D4 — Widening the `Validator` Protocol return type (FR-007)

**Decision**: `def validate(...) -> list[Violation] | EvalResult: ...`. A custom
validator that returns a bare `list[Violation]` still satisfies the Protocol
(`list[Violation]` is one arm of the union — structural subtyping accepts it).
`focalization.validate`'s annotation widens to the same union.

**Rationale**: FR-007 / SC-004 — `mypy --strict` must stay clean and a bare-list
validator must still type-check against the Protocol. A union return is covariant
in the obvious way; returning the narrower `list[Violation]` from a concrete
validator is assignable to the wider Protocol return. Verified by the existing
`_Good`/`_Boom` fakes (they return bare lists) which continue to type-check, plus
SC-004's explicit assertion.

## D5 — `focalization` adopts form (c) at exactly one site (FR-003/FR-006)

**Decision**: replace **only** the limited-third `raise NotEvaluated(...)` at
`focalization.py:101` with:

```python
return EvalResult(
    self._first_person_breaks(project.manuscript_view()),
    [Abstention(_HEAD_HOPPING_PENDING, NotEvaluatedKind.pending_capability)],
)
```

The four input-conditional `raise NotEvaluated(...)` (no constitution / no voice /
`[PENDING]` / no person — all `missing_input`), the omniscient `return
self._first_person_breaks(...)`, the first-person `return []`, the
`_HEAD_HOPPING_PENDING` reason string, and `_first_person_breaks` itself are
**untouched** (FR-006). The `validate` return annotation widens to the union (D4).

**Rationale**: the trigger for form (c) is the exact precondition the head-hopping
heuristic ran under (and 045 abstained under): `person == "third" and limited`
(spec Assumptions). `_first_person_breaks` already emits the warning shape
unchanged (FR-004), so reusing it verbatim under limited-third needs no rule
change — only the path that reaches it. The empty-`violations` case (the three
fixtures, no first-person break) is observationally equal to the old `raise`
(D1), keeping fixtures byte-identical (FR-012).

## D6 — Why the three focalized fixtures stay byte-identical (FR-012, SC-003)

**Decision / finding**: `tiny-historical`, `tiny-novel`, `tiny-quest` are
limited-third with **no** first-person break (verified by DEBT-019's own note:
they emit zero `focalization` findings today). Under form (c),
`_first_person_breaks` returns `[]`, so `EvalResult([], [Abstention(...)])` yields
**one** `not_evaluated` entry (`focalization`, `pending_capability`, the same
reason) and **zero** findings — identical on the wire to today's `raise`. No
fixture manuscript/constitution/oracle is edited.

## D7 — Test strategy (FR-013/FR-014/FR-015, empirical per FR-013)

- **Runner-level (FR-015, SC-008)**: add a synthetic `_Partial` fake to
  `test_runner.py` (mirroring `_Skip`/`_Good`/`_SkipCapability`) returning
  `EvalResult([Violation(...)], [Abstention("…", pending_capability)])`. Assert its
  finding lands in `violations[]` (deduped/sorted) and its abstention in
  `not_evaluated[]` with the **runner-stamped** name + `kind`, and it is in
  **neither** `errors[]` nor (for its finding) the abstention channel. This proves
  the general contract decoupled from `focalization`.
- **`focalization` (FR-013)**: add the **new** both-at-once case — a limited-third
  voice + a first-person marker outside dialogue — asserting **both** a
  `focalization` `warning` citing the marker **and** the `pending_capability`
  head-hop abstention, in the same `EvalResult`. Verified empirically with `uv run
  pytest` (which surfaces fire is decided by running, not asserted blind).
- **Retarget (FR-014)**: the limited-third tests that today assert `pytest.raises(
  NotEvaluated)` (`test_limited_third_abstains_as_capability_gap`,
  `test_limited_third_with_no_named_focal_abstains_identically`,
  `test_english_declaration_abstains_under_limited_third`,
  `test_replacing_placeholder_with_real_voice_wakes_validator`) now assert the
  returned `EvalResult`: its `not_evaluated[0]` is the head-hop
  `(reason, pending_capability)` abstention and its `violations` is empty (those
  fixtures have no first-person break). The English limited-third test currently
  documenting the DEBT-019 drop is updated/replaced so the first-person break
  **does** fire alongside the abstention (the FR-013 case can be the English one,
  or a sibling). The `_run` helper widens to return `list[Violation] | EvalResult`;
  total-abstention paths (the four `missing_input` `raise`s, `_parse_declaration`)
  still use `pytest.raises(NotEvaluated)` and are unchanged.

## D8 — Docs (contract-before-code, FR-010/FR-011)

- `bookwright-design.md` § 13.1: document the **third** accepted return shape — a
  validator MAY **return** a partial result carrying `violations` **and** one or
  more abstentions; the runner normalizes all three; the empty-findings partial is
  observationally equal to `raise NotEvaluated`. Add the row to the tri-value table.
- § 13.2 (`focalization` row) + § 13.5 (the head-hopping nuance) + § 20.6.1: state
  plainly that under limited-third `focalization` now **runs** the deterministic
  first-person-break check **and** abstains on head-hopping in the same run — the
  determinism↔LLM frontier (the deterministic half runs, the open-set half abstains)
  is now realized, not blocked by an all-or-nothing contract.
- `DEBT.md`: remove the **DEBT-019** entry (git keeps history) and reconcile the
  track-A closed-list line (line ~51) so it reflects DEBT-019's closure.

All doc edits land **before** the code diverges from the written contract (FR-010,
plan § 7.3 doctrine).
