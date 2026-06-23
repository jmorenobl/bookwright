# Contract — the two validators after the split

This is the behavioral contract `/speckit-tasks` and `/speckit-implement` must honor. It is the
seam (`validation/base.Validator` Protocol) and the 040 `not_evaluated[]` channel — neither is
re-shaped; only the *set* of validators and which one abstains changes.

## C1 — `character_presence` (orphan, `error`) — unchanged contract

```
name = "character_presence"
severity_default = Severity.error

validate(project, indexer) -> list[Violation]:
    roster = project.character_names()
    files  = project.manuscript_files()
    if not roster and not files:
        raise NotEvaluated(
            "there is no manuscript prose and no bible character roster to cross-check"
        )                                   # IDENTICAL reason string (FR-004)
    return self._orphans(roster, files)     # error findings, byte-for-byte as today (FR-003)
```

- MUST emit each orphan `Violation` with `validator="character_presence"`,
  `severity=Severity.error`, the same message template, `source=<bible relpath>`, `triples=()`.
- MUST NOT consult settings/locations/objects (the union is gone) and MUST NOT scan prose for
  proper nouns (that rule moved out).
- Guard reason string is byte-identical to iterations 040/042.

## C2 — `character_unknown_mentions` (open-set abstainer) — new contract

```
name = "character_unknown_mentions"
severity_default = Severity.warning      # cosmetic; never emits

validate(project, indexer) -> list[Violation]:
    raise NotEvaluated(
        "open-set proper-noun discovery requires semantic judgment (move 3); "
        "the deterministic heuristic was measured insufficient on real prose"
    )
```

- MUST raise **unconditionally** — no reference to `project`/`indexer` state (FR-005, D3).
- MUST be discovered as a built-in by `registry.discover_validators` with no hand-registration,
  active by default, disable-able via `[validators] disabled = ["character_unknown_mentions"]`.
- MUST never appear in `violations[]`/`errors[]`; it appears only in `not_evaluated[]` (FR-006).

## C3 — Runner / channel behavior (existing — assert, don't re-implement)

For any project with both validators active, `run_validators` returns:

- `violations`: contains the orphan `error`s (when any), no unknown-mention `warning` ever.
- `errors`: does **not** contain `character_unknown_mentions` (it raised `NotEvaluated`, not a
  crash — caught **before** the generic `except`, `runner.py:68`).
- `not_evaluated`: contains `NotEvaluatedResult("character_unknown_mentions", <reason>)`, sorted
  by validator name; may also contain `character_presence` when *its* guard trips.
- `ran`: includes both names (the runner appends to `ran` before calling `validate`).

## C4 — `--json` envelope (existing contract, asserted)

```jsonc
{
  "status": "ok" | "violations",
  "not_evaluated": [
    { "validator": "character_unknown_mentions",
      "reason": "open-set proper-noun discovery requires semantic judgment (move 3); ..." }
    // ... plus character_presence when its guard trips
  ],
  // violations[], errors[], summary.ran[] (now 7 built-ins) unchanged in shape
}
```

- Green predicate `status == "ok" AND not_evaluated == []` is **`False`** on every project
  (FR-008, SC-006), because `not_evaluated` always carries the abstainer entry.
- Exit code: not-evaluated never gates (exit unchanged; only `error` → non-zero) (FR-007).

## C5 — `status` / `next_actions` (existing channel — ripple asserted)

- `state.validation.not_evaluated` always carries the abstainer entry; `state.validation.ran`
  length is **7**.
- `next_actions` always includes one `bookwright-continuity` action from the existing
  `activate_dormant_validators` rule (predicate `bool(s.validation.not_evaluated)`), with a
  prompt clause for `character_unknown_mentions` (tailored remedy, D6).
- On `tiny-historical` this yields the 4-action shape
  `[bookwright-research, bookwright-verify, bookwright-continuity, bookwright-continuity]`;
  `validation.counts` stays `{error: 1, warning: 1, info: 0}` (FR-011, SC-005).
