# Contract — `validate` surfaces ingestion-skipped bible files

The observable delta of `bookwright validate` when one or more bible files are
omitted by ingestion. Reuses the `not_evaluated[]` channel and its serialization
(040/044) — no new channel, field, kind, or predicate (FR-008/FR-011).

## Trigger

A bible file under `bible/**` whose front-matter is unusable (broken YAML, missing
`name`, wrong container shape, unreadable) → `map_bible` records it in
`MapResult.skipped` and excludes its entity from the graph.

## `--json` envelope delta

For each skipped file, `not_evaluated[]` gains exactly one entry:

```json
{
  "validator": "ingestion",
  "reason": "bible file 'bible/characters/rota.md' skipped (unusable front-matter): malformed YAML frontmatter: …",
  "kind": "missing_input"
}
```

- `validator` is the literal `"ingestion"` for every skip entry (FR-004).
- `reason` cites the skipped path and the skip cause (FR-003).
- `kind` is `"missing_input"` (FR-002).

No other envelope key changes shape: `status`, `failed`, `violations`, `errors`,
and `summary` are computed exactly as before. In particular `summary.by_severity`
and `failed` are untouched (a skip is not a `Violation`).

## Human-report delta (no `--json`)

The skip appears in the existing `not evaluated:` section, rendered by the unchanged
`_KIND_LABEL` map:

```
not evaluated:
  ingestion [input gap]: bible file 'bible/characters/rota.md' skipped (unusable front-matter): …
```

(`missing_input` renders as `input gap`.)

## Green predicate (unchanged, 044)

> A run is **green/clean** ⟺ `status == "ok"` AND no `not_evaluated` entry has
> `kind == "missing_input"`.

A skip entry is `missing_input`, so **its presence denies green**. The predicate
itself is not modified (FR-005). A project that also carries `pending_capability`
abstentions (e.g. `focalization` under limited-third) keeps reading those as
non-green-denying; only the `missing_input` skip denies green.

## Exit code (unchanged)

`validate` exit code = `1` iff some `violations[]` entry is `error`-severity, else
`0`. A skip emits no violation, so the exit code is **identical** to a no-skip run
with the same findings (FR-007, SC-002). The skip degrades the informational green
and is visible, but does not change the CI gate.

## Ordering (FR-009)

`not_evaluated[]` is sorted by the total order `(validator, reason)`. With multiple
skips (all `validator="ingestion"`), the `reason` tie-break (unique paths) makes the
list byte-identical across repeated runs. The key is defined once
(`not_evaluated_sort_key` in `validation/runner.py`) and imported by both the runner
and the `validate` skip-merge.

## No-skip invariant (FR-010 / SC-003)

A project with no skipped bible files produces **no** `ingestion` entry and is
byte-identical to today's output. Promoting the sort key reorders nothing (validator
names are already unique, so no tie exists). Pinned skip-free fixtures are not
edited.

## Cross-command agreement (User Story 3 / SC-004)

`status` and `validate` no longer disagree on a skipped bible file:
- `bookwright status` aborts with `code=skipped_sources`, exit 4 (unchanged —
  `status` never reaches its embedded validation state on a skip, FR-008).
- `bookwright validate` surfaces the same file in `not_evaluated[]` (new) and
  degrades green.

They report it by **different** pre-existing mechanisms (a hard refusal vs. a
degraded-green not-evaluated entry), not a shared third channel.
