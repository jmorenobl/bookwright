# Data Model — `validate` surfaces ingestion-skipped bible files

**No new types and no schema change.** This iteration only *consumes* what 040/044
delivered (FR-011). The model section records the two existing types in play and the
one sentinel value the merge introduces.

## Reused (frozen) — read input

### `SkippedFile` (`io/report.py`)

```python
class SkippedFile(BaseModel):
    path: str       # project-relative posix path of the omitted bible file
    reason: str     # human-readable skip cause (e.g. "malformed YAML frontmatter: …")
```

Carried in `MapResult.skipped: list[SkippedFile]` (`io/bible.py`), populated by
`map_bible` whenever a bible file's front-matter is unusable (broken YAML, missing
`name`, wrong container shape, unreadable file). **Read-only here** — this iteration
does not change ingestion (FR-001, Assumptions).

Reachable from `validate` via the memoized `ValidationContext.bible().skipped`
(`validation/base.py:246`) — the same call the validators already trigger (research
D1). Safe on a missing/empty bible dir (empty list).

## Reused (frozen) — output record

### `NotEvaluatedResult` (`validation/base.py`, iteration 044)

```python
@dataclass(frozen=True)
class NotEvaluatedResult:
    validator: str
    reason: str
    kind: NotEvaluatedKind = NotEvaluatedKind.missing_input

    def to_json(self) -> dict[str, Any]:
        return {"validator": self.validator, "reason": self.reason, "kind": self.kind.value}
```

`NotEvaluatedKind` is the closed vocabulary `{missing_input, pending_capability}`
(unchanged, FR-011). Serialized into `not_evaluated[]` (`--json` envelope and human
report) by `ValidationReport` — both reused as-is (FR-008).

## The one new value (not a new type) — the `ingestion` skip entry

Each `SkippedFile` is mapped to:

| Field | Value | Source |
|---|---|---|
| `validator` | `"ingestion"` (literal sentinel, shared by every skip entry) | FR-004 / Clarifications |
| `reason` | `f"bible file '{path}' skipped (unusable front-matter): {reason}"` | FR-003 (path-uniqueness is the load-bearing property) |
| `kind` | `NotEvaluatedKind.missing_input` | FR-002 / FR-006 (denies green) |

This is a value, not a type: `"ingestion"` is a sentinel `validator` string that no
real validator uses (validator names come from the registry), so it never collides
with a true `not_evaluated` entry.

## Ordering invariant (FR-009)

`not_evaluated[]` is ordered by the **total** key `(validator, reason)`, defined
once as `not_evaluated_sort_key` in `validation/runner.py` and imported by the
`validate` skip-merge. Because all skip entries share `validator="ingestion"`, the
`reason` tie-break (each carries a unique path) is what makes the order total — so
two skipped files emit in the same order on every run (byte-identical JSON and
human report).

## Invariants summary

- **No new channel** — skip entries ride `not_evaluated[]` (FR-008).
- **Green predicate unchanged** — a `missing_input` entry denies green via the 044
  predicate in `report.py`; the predicate is not modified (FR-005).
- **Gate unchanged** — no `Violation` is produced, so `report.failed` and the exit
  code are identical for the same findings (FR-007).
- **Skip-free byte-identity** — no skip ⇒ no skip entry; the total-order promotion
  reorders nothing (validator names already unique), so pinned fixtures are
  untouched (FR-010).
