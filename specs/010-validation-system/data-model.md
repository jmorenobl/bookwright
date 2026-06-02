# Phase 1 Data Model — Validation System

In-memory types only; this feature persists nothing (FR-020). All types live under
`src/bookwright/validation/`.

## Severity (`base.py`)

```python
class Severity(str, Enum):
    error = "error"
    warning = "warning"
    info = "info"
```

- String-valued (JSON-friendly, matches design § 13.1).
- **Ordering** for the `--severity` threshold and the gate: `error > warning > info`.
  A module-level `_RANK = {error: 2, warning: 1, info: 0}` provides the ordinal;
  `Severity.at_least(threshold)` returns whether a severity meets a threshold.
- The **gate** triggers iff any violation has `severity == error`.

## Violation (`base.py`)

```python
@dataclass(frozen=True)
class Violation:
    validator: str                 # FR-002: producing validator's name
    severity: Severity             # FR-002
    message: str                   # FR-002/003: human-readable rule + why
    source: str | None             # "relpath" | "relpath:line" | None (location-less)
    triples: tuple[tuple[str, str, str], ...] = ()   # FR-002: implicated graph relationships
```

- `frozen=True` + tuple fields → hashable, enabling dedupe (D8).
- `source` is a project-relative `posix` path, optionally `:line`. Helpers
  `source_file(self) -> str | None` and `source_line(self) -> int | None` split it
  for scope matching and rendering.
- `to_json(self) -> dict` → `{"validator","severity","message","source","triples"}`
  where `triples` is a list of 3-element lists (FR-002, SC-004).

**Validation rules / invariants.**
- An empty list from a validator means "no problems" (FR-001).
- `triples` carry the implicated relationships; may be empty for prose-only findings.
- Identical `Violation` values from one run are collapsed to one (edge case
  "duplicate detection").

## ValidatorError (`base.py`)

```python
@dataclass(frozen=True)
class ValidatorError:
    validator: str    # name, or the offending file path for load failures
    message: str       # attributed reason
    phase: Literal["load", "run"]
```

Surfaced in the report's `errors[]` (FR-014, edge cases). Never affects the gate.

## Validator protocol (`base.py`)

```python
@runtime_checkable
class Validator(Protocol):
    name: str
    severity_default: Severity
    def validate(self, project: "ValidationContext", indexer: Indexer) -> list[Violation]: ...
```

- Matches design § 13.1. `project` is the `ValidationContext`; `indexer` is the
  loaded graph engine (an empty engine when no `graph.ttl` exists).
- Built-ins are small classes implementing this protocol, instantiated once at
  discovery. `severity_default` is the validator's default; individual violations
  may carry a different severity (FR-001/002). Concretely, `character_presence` has
  `severity_default = error` and emits orphan-in-bible findings at `error`, but
  emits the heuristic unknown-mention findings at `warning` (research D3) so a false
  positive cannot fail the build.

## ValidationContext (`base.py`)

The `project` argument. Bundles the project root + manifest and provides cached
accessors so each source file is read once per run (shared across validators).

```python
@dataclass
class ValidationContext:
    root: Path
    manifest: Manifest
    # cached lazily:
    def bible(self) -> MapResult                     # io.bible.map_bible(root, bible_dir, uri_base)
    def character_names(self) -> tuple[tuple[str, str], ...]   # (name, bible_relpath), sorted
    def setting_names(self) -> tuple[tuple[str, str], ...]     # (name, bible_relpath), sorted
    def manuscript_files(self) -> tuple[tuple[str, str], ...]  # (relpath, text), sorted by relpath
    def constitution_text(self) -> str | None        # paths.constitution, or None if absent
```

- Paths come from `manifest.paths` (`bible`, `manuscript`, `constitution`,
  `graph`). `uri_base` from `manifest.bookwright`.
- `manuscript_files()` globs `**/*.md` under the manuscript dir, sorted (D8),
  skipping unreadable files defensively.
- Accessors memoize on first call (private cached fields).

## ValidationReport (`report.py`)

Aggregates a run and owns filtering, the gate, and rendering.

```python
@dataclass
class ValidationReport:
    violations: tuple[Violation, ...]   # ALL found, deduped, pre-filter
    errors: tuple[ValidatorError, ...]
    ran: tuple[str, ...]                # validator names that executed (sorted)

    @property
    def failed(self) -> bool            # gate: any violation.severity == error (pre-filter, FR-013)

    def reported(self, *, scope: ScopeFilter | None, severity: Severity | None) -> list[Violation]
    def to_json(self, *, scope, severity) -> dict
    def render(self, console, *, scope, severity) -> None   # human, grouped by validator
```

- `failed` ignores `scope`/`severity` (FR-013): the gate is computed from the full
  set.
- `reported(...)` applies scope then the severity **threshold** (`Severity.at_least`).
- `to_json` shape (Principle IX / SC-004):

```json
{
  "status": "ok" | "violations",
  "failed": true,
  "violations": [ { "validator": "...", "severity": "error",
                    "message": "...", "source": "manuscript/cap-04.md:42",
                    "triples": [["s","p","o"]] } ],
  "errors":     [ { "validator": "temporal", "phase": "run", "message": "..." } ],
  "summary":    { "ran": ["character_presence","focalization","setting_continuity","temporal"],
                  "total": 7, "reported": 3,
                  "by_severity": { "error": 2, "warning": 4, "info": 1 } }
}
```

`status` is `"violations"` iff `reported(...)` is non-empty; `failed` is the gate
(independent of filters). `total` counts unfiltered violations; `reported` counts
the filtered list emitted in `violations[]`.

## ScopeFilter (`report.py`)

```python
@dataclass(frozen=True)
class ScopeFilter:
    rel: str            # project-relative posix path of the scope (file or dir)
    is_dir: bool
    def matches(self, source: str | None) -> bool   # False for None (location-less omitted)
```

Constructed by the command after validating the scope path exists under the root
(else exit 2, D10).

## Configuration resolution (`registry.py`)

Inputs: `manifest.validators` (`enabled`, `disabled`, `custom`), discovered
built-ins `B`, discovered customs `C`. Output: ordered active validators +
`ValidatorError`s for malformed customs.

```python
def discover_validators(custom_dir: Path) -> tuple[dict[str, Validator],   # built-ins
                                                    dict[str, Validator],   # customs (loaded ok)
                                                    list[ValidatorError]]   # load failures

def resolve_active(builtins, customs, cfg: ValidatorsBlock) -> list[Validator]
    # raises UnknownValidatorError(names) when a referenced name ∉ B ∪ C
```

Algorithm = research D7. `resolve_active` returns validators sorted by `name` (D8).

## UnknownValidatorError (`base.py` or `registry.py`)

```python
class UnknownValidatorError(Exception):
    def __init__(self, names: tuple[str, ...]) -> None: ...
    def to_json(self) -> dict   # {"error":"unknown_validator","names":[...],"message":"..."}
```

Raised at exit 2 (FR-007). Carries the offending name(s) for a clear message.

## Indexer-gap closure — timeline format + `NarrativeEvent` (research D1/D11)

To give `temporal` real graph data, three existing modules gain small, backward-
compatible extensions (all new inputs optional):

**`bible/timeline.md` frontmatter** — each `events:` item may add:

```yaml
events:
  - name: "Fundación de Destilerías Ayelo"
    date: 1885                       # optional integer year
    participants: ["Manuel de Aparici"]
  - name: "Quiebra de la sociedad"
    date: 1884                       # earlier year …
    follows: ["Fundación de Destilerías Ayelo"]   # … but declared to follow → temporal violation
    overlaps: []                     # optional list of event names
```

**`NarrativeEvent` (`golem/modules/event.py`)** gains optional fields:

```python
date: int | None = None                       # year
follows: tuple[GolemEntity | URIRef, ...] = ()        # → TR:follows edges
overlaps: tuple[GolemEntity | URIRef, ...] = ()       # → TR:temporally-overlaps edges
```

Emitted triples (closure-safe, D11):
- `event  TR:follows  other_event` per `follows` entry (likewise `temporally-overlaps`).
- when `date` is set: `event  TR:temporal-location  {event.uri}/time-span` and
  `{event.uri}/time-span  crm:P90_has_value  "1885"^^xsd:gYear` (reusing
  `gyear_literal()` from `golem/modules/feature.py`).

**`io/bible.py`** timeline mapper resolves `follows`/`overlaps` names through the
same slug index used for participants; unresolved names become
`UnresolvedParticipant`-style soft warnings (no abort).

## Graph predicate constants

In `golem/namespaces.py` (so the closure test covers them — all ∈ `frozen_terms()`):

```python
TR = Namespace("http://www.ontologydesignpatterns.org/ont/dlp/TemporalRelations.owl#")
FOLLOWS = TR["follows"]                       # frozen ✓
TEMPORALLY_OVERLAPS = TR["temporally-overlaps"]  # frozen ✓
TEMPORAL_LOCATION = TR["temporal-location"]   # frozen ✓ (event → time node)
# HAS_VALUE (crm:P90_has_value) already exists in namespaces.py and is frozen ✓.
# NOTE: crm:P4_has_time-span is NOT in the frozen ontology — do not emit it (D11).
```

`validation/queries.py` imports these read-only for its SPARQL (`FOLLOWS`,
`TEMPORALLY_OVERLAPS`, and the `temporal-location → P90_has_value` path for the
year). `CRM` and the provenance predicates come from `golem.namespaces` unchanged.
