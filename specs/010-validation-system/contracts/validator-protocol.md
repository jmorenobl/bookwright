# Contract — Validator Protocol & Discovery

The stable seam between the validation runner and any validator (built-in or
user-supplied). Mirrors design § 13.1; binding for FR-001..007.

## The protocol

```python
@runtime_checkable
class Validator(Protocol):
    name: str                       # stable, unique identifier (e.g. "temporal")
    severity_default: Severity      # error | warning | info
    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]: ...
```

- **`name`** — stable and unique within its tier (built-in / custom). Used by the
  manifest `[validators]` lists, in the report, and for deterministic ordering.
- **`severity_default`** — the validator's default level (FR-001). Individual
  violations MAY carry a different `severity` (FR-002).
- **`validate(project, indexer)`** — examines the project (`ValidationContext`:
  bible roster, manuscript prose, constitution, manifest, root) and the already-built
  graph (`indexer`, possibly empty), returning a list of `Violation`. An **empty
  list means "no problems found"** (FR-001). MUST be deterministic (FR-019): the
  same inputs always yield the same list. MUST NOT write to disk or mutate the graph
  (FR-020). MAY raise — the runner isolates it (FR-014).

## Violation (the finding contract)

Every `Violation` MUST carry (FR-002/003):

| Field | Meaning |
|---|---|
| `validator` | name of the producing validator |
| `severity` | `error` \| `warning` \| `info` |
| `message` | human-readable: which rule was broken and **why**, locatable without reading validator source |
| `source` | `"relpath"` or `"relpath:line"` (project-relative posix), or `None` when no specific location applies |
| `triples` | the implicated graph relationships as `(s, p, o)` tuples; may be empty for prose-only findings |

A finding with no precise location sets `source=None`; it is reported in a full run
but **omitted under an active `--scope`** (location-less has nothing to match).

## Discovery (FR-004 / FR-005)

- **Built-ins** are auto-discovered by iterating the
  `bookwright.validation.validators` package (`pkgutil.iter_modules`), importing
  each module, and collecting every module-level object satisfying `Validator`.
  No hand-registration (FR-004).
- **Custom** validators are loaded from sorted `*.py` under
  `<project_root>/.bookwright/validators/` via `importlib.util.spec_from_file_location`;
  every protocol-conforming object found is collected (FR-005).
- A custom file that fails to import, or exposes no conforming validator, is
  **skipped with an attributed message** (a `ValidatorError`, `phase="load"`) and
  does **not** crash the command (edge case; SC-007).
- Names MUST be unique within a tier; a duplicate is a load error, not a silent
  shadow.
- A **custom** validator whose `name` collides with a **built-in's** is rejected the
  same way: the built-in wins, the custom is skipped with an attributed
  `ValidatorError(phase="load")` ("custom validator name '<n>' collides with a
  built-in; rename it"), and the run continues. A built-in coherence check is **never**
  silently shadowed by project code — silent override would erode the determinism
  guarantee (FR-019). The discovered built-in / custom sets are therefore disjoint by
  name.

## Configuration (FR-006 / FR-007)

`[validators]` in `manifest.toml` (already modelled by `ValidatorsBlock`):

```toml
[validators]
enabled  = []   # empty = all built-ins run; non-empty = only these run
disabled = []   # names removed from the active set
custom   = []   # empty = all discovered customs run; non-empty = allow-list of customs
```

Resolution (research D7):
1. If `custom` non-empty, restrict discovered customs to listed names.
2. `candidates = builtins ∪ customs`, minus `disabled`.
3. If `enabled` non-empty, intersect `candidates` with `enabled`.
4. Any name in `enabled` / `disabled` / `custom` absent from the discovered
   `builtins ∪ customs` → **unknown-validator error** (FR-007), reported clearly,
   exit 2 — never silently ignored.

The active list is returned sorted by `name` (determinism, FR-019).

## Built-in validators shipped in v0

| name | `severity_default` | Source it reads | Detects |
|---|---|---|---|
| `temporal` | `error` | graph | timeline contradictions over a multi-year **interval** model + the five `TR:*` relations (FR-015): (a) `follows`/`precedes` cycles, (b) a pair both ordered and `temporally-overlaps`, (c) containment vs. strict order, (d) numeric begin/end contradicting a declared relation. All four uniform `error`. Intervals (typed begin/end boundaries) + relation edges are emitted by the timeline indexer (research D1/D11/D12). |
| `character_presence` | `error` | bible + manuscript | bible character never mentioned → **error**; manuscript proper-noun mention absent from bible → **warning** (heuristic). Per-violation severity, FR-002/FR-016, research D3. |
| `setting_continuity` | `warning` | bible + manuscript | same setting described with contradicting descriptor terms across files (FR-017) |
| `focalization` | `warning` | constitution + manuscript | prose violating the declared narrative person / focal character (FR-018) |

All four are deterministic and LLM-free (FR-019). A validator's `severity_default`
is its baseline; `character_presence` deliberately downgrades its heuristic
direction to `warning` so a false positive can never trip the CI gate (FR-013).
