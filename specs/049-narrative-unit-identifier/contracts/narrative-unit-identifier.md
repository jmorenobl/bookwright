# Contract: `narrative_structure` unit-identifier message

The interface this feature changes is the **message text** of the `Violation`
records `narrative_structure` emits — consumed by `bookwright validate` (`--json`
`violations[].message`) and read by authors. This contract pins the observable
behavior; it is verified by the unit and E2E suites (FR-008/SC-001..SC-006).

## C1 — Orphan-beat finding names the unit by its human name

**Given** a `G9_Narrative_Unit` orphaned from every `G7_Narrative_Sequence`, whose
graph carries `(uri, rdfs:label, "<Human Name>")`,
**When** `narrative_structure` runs,
**Then** the finding message is:

```
narrative unit '<Human Name>' belongs to no narrative sequence (orphan beat)
```

— the human authored name, **not** the URI slug (FR-001/FR-002/SC-002).

## C2 — Unresolved-role finding is unchanged

**Given** a unit whose `roles:` names a slug resolving to no character role,
**When** `narrative_structure` runs,
**Then** the finding message is **exactly** what it is today:

```
narrative unit '<Human Name>' references role '<role>' which resolves to no character role
```

The identifier now flows through the shared `_unit_identifier` helper but the text is
byte-identical (FR-002/SC-006).

## C3 — Identical identifier format across both rules

Both messages render the unit identifier through the **one** `_unit_identifier`
helper, so the identifier substring is produced identically (the human name alone,
no parenthetical slug). No second identifier-formatting expression exists in
`narrative_structure.py` (FR-005/SC-006 — verified by diff).

## C4 — Defensive slug fallback (impossible-by-construction path)

**Given** an orphan unit with **no** `rdfs:label` in the graph (or an empty one),
**When** `narrative_structure` runs,
**Then** the finding still emits, naming the unit by its slug:

```
narrative unit '<slug>' belongs to no narrative sequence (orphan beat)
```

A finding is never dropped and the identifier is never empty (FR-004).

## C5 — Everything else is invariant

For every finding from either rule, the `relpath:line` locator (`source`), the
`warning` severity, the per-validator finding count, and the gate/exit-code outcome
(`failed`) are exactly what they were before this change (FR-006/SC-003). Only the
printed identifier text differs.

## Oracle bindings (where C1–C5 are checked)

| Contract | Test |
|---|---|
| C1 | `tests/validation/test_narrative_structure.py::test_orphan_beat_flagged_sequenced_not` (slug→name); E2E `test_validate_reports_the_orphan_beat` via `tiny-quest` oracle |
| C2 | `test_unresolved_role_flagged_with_location`; E2E `test_validate_reports_the_unresolved_role` |
| C3 | the diff (one helper, two call sites) + both messages asserted in the same suite |
| C4 | a new unit test exercising the missing/empty-label floor |
| C5 | `test_deterministic_and_read_only`, `test_validate_finding_counts_are_exact`, source-assertions in the existing tests |
