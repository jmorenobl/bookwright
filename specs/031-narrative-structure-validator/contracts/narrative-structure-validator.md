# Contract: `narrative_structure` validator

The validator's stable, externally-observable behaviour. It conforms to the
existing `Validator` protocol (`validation/base.py`); this contract pins the
behaviour tests assert against.

## Identity

- **`name`**: `narrative_structure` (the `[validators]` enable/disable key).
- **`severity_default`**: `warning`.
- **Discovery**: automatic — present at module level in
  `validation/validators/narrative_structure.py`, picked up by the registry's
  `pkgutil` scan. No hand-registration. (FR-001/FR-002)

## Inputs

`validate(project: ValidationContext, indexer: Indexer) -> list[Violation]`

- `indexer`: the manifest-selected engine with `bible/graph.ttl` loaded (built to
  include the outline pass). Source of US1's SPARQL and every `file:line` locator.
- `project.outline()`: the new cached accessor returning the combined
  `map_bible`→`map_outline` `MapResult`. Source of US2's unresolved-role records.

## Behaviour

### Rule a — orphan beat (FR-005)

For every `G9_Narrative_Unit` with **no** incoming `dlp:proper-part` from a
`G7_Narrative_Sequence` (one SPARQL `NOT EXISTS`), emit **one** finding:

- `validator="narrative_structure"`, `severity=warning`, `triples=()`.
- `message` names the unit (by URI slug) and states it belongs to no sequence.
- `source` = the unit card's `file:line` via `resolve_source(indexer, unit_uri)`.

### Rule c — unresolved role (FR-006)

For every `UnresolvedReference` in `project.outline().unresolved_references` whose
`path` is under `"{outline}/units/"`, emit **one** finding:

- `validator="narrative_structure"`, `severity=warning`, `triples=()`.
- `message` names the beat (`ref.entity`) and the unresolved role (`ref.name`).
- `source` = the unit card's `file:line` via `resolve_source` on the unit's URI
  (recovered from `outline().mapped`), falling back to `ref.path`.
- The records are **reused**, not recomputed — role resolution has one source of
  truth (`io/outline._resolve_roles`).

### Excluded rules (FR-007 + spec Out of Scope)

- **No** order-coherence finding: a sequence whose members have an `order:` gap or
  duplicate yields **no** order-related finding.
- **No** empty-sequence finding (structurally unreachable input).
- **No** LLM inference (FR-013).

## Invariants

- **Inert without structure** (FR-009): a project with no `outline/units/` produces
  **zero** findings and adds nothing to the report.
- **Read-only / deterministic** (FR-008, SC-005): writes nothing, mutates no graph;
  the same source yields the same findings byte-for-byte after the runner's sort.
- **No existing-validator change** (FR-011): names, severities, findings of other
  validators are untouched.
- **Frozen ontology** (FR-012, SC-007): no class or property added to `golem.ttl`.

## Output envelope (FR-003 / Principle IX)

Findings appear in the existing `--json` shape with **no** new top-level key:

```json
{
  "status": "violations",
  "failed": false,
  "violations": [
    {
      "validator": "narrative_structure",
      "severity": "warning",
      "message": "narrative unit 'the-flood' belongs to no narrative sequence (orphan beat)",
      "source": "outline/units/the-flood.md:2",
      "triples": []
    }
  ],
  "errors": [],
  "summary": { "ran": ["...", "narrative_structure", "..."], "total": 1, "reported": 1, "by_severity": {"error": 0, "warning": 1, "info": 0} }
}
```

`failed` stays `false` for a warning-only run — the validator never gates CI.

## Configuration (US3 / FR-010)

- Appears in the resolved active set for a default project.
- `[validators] disabled = ["narrative_structure"]` → it does not run, emits
  nothing; every other validator is unchanged.
- `[validators] enabled = ["narrative_structure"]` → only it runs.
