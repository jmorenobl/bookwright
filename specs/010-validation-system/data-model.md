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

## Indexer-gap closure — interval timeline format + `NarrativeEvent` (research D1/D11/D12)

To give `temporal` real graph data, three existing modules gain small, backward-
compatible extensions (all new inputs optional; an event with none of them behaves
exactly as today).

**`bible/timeline.md` frontmatter** — each `events:` item may add a begin/end year and
any of the five qualitative relation keys (each a list of event names resolved like
`participants`):

```yaml
events:
  - name: "Fundación de Destilerías Ayelo"
    begin: 1885                       # optional begin year (open interval if `end` omitted)
    end: 1912                         # optional end year   (open interval if `begin` omitted)
    participants: ["Manuel de Aparici"]
  - name: "Quiebra de la sociedad"
    date: 1884                        # shorthand: a single-year (point) interval, begin == end == 1884
    follows: ["Fundación de Destilerías Ayelo"]   # 1884 cannot follow [1885,1912] → temporal error (rule d)
    precedes: []                      # TR:precedes
    overlaps: []                      # TR:temporally-overlaps  (symmetric)
    includes: []                      # TR:temporally-includes  (containment)
    included_in: []                   # TR:temporally-included-in
```

- `date:` is a convenience shorthand for `begin == end == <year>`; it is **mutually
  exclusive** with `begin:`/`end:` (supplying both is a soft warning, like an unknown
  key, and `date:` is ignored). The new keys join `ITEM_KEYS` so they are not flagged
  as unknown.

**`NarrativeEvent` (`golem/modules/event.py`)** gains optional fields:

```python
begin: int | None = None                                   # interval begin year
end: int | None = None                                     # interval end year
follows: tuple[GolemEntity | URIRef, ...] = ()             # → TR:follows
precedes: tuple[GolemEntity | URIRef, ...] = ()            # → TR:precedes
overlaps: tuple[GolemEntity | URIRef, ...] = ()            # → TR:temporally-overlaps
includes: tuple[GolemEntity | URIRef, ...] = ()            # → TR:temporally-includes
included_in: tuple[GolemEntity | URIRef, ...] = ()         # → TR:temporally-included-in
```

The five relations are declared as ordinary multi `cross_refs` (one frozen `TR:*`
predicate each), so the base `to_triples()` emits them. The interval needs a custom
`to_triples()` override (the base machinery cannot express the typed-boundary +
dimension shape), reusing the existing `Dimension` class and `gyear_literal()`.

**Emitted interval triples (closure-safe, D11 — every term ∈ `frozen_terms()`):**

```
event              CSM:duration          {event}/time-span          # ⊑ TR:temporal-location
{event}/time-span  rdf:type              dlp:time-interval
# for each present boundary B ∈ {begin, end} (open interval emits only the known one):
{event}/time-span  TR:temporal-location  {event}/time-span/B
{event}/time-span/B  rdf:type            dlp:time-interval
{event}/time-span/B  crm:P2_has_type     {uri_base}type/B           # self-labels begin / end
{uri_base}type/B     rdf:type            crm:E55_Type
{event}/time-span/B  crm:P43_has_dimension  {event}/time-span/B/dimension
{…/B}/dimension      rdf:type            crm:E54_Dimension
{…/B}/dimension      crm:P90_has_value   "1885"^^xsd:gYear          # gyear_literal()
```

The begin/end `E55_Type` individuals (`{uri_base}type/begin`, `{uri_base}type/end`)
mirror the existing `birth`/`death` type individuals. `crm:P4_has_time-span` and CIDOC
`P82a/P82b/P81/P79/P80` are **not** emitted (absent from `frozen_terms()`, D11).

**`io/bible.py`** timeline mapper coerces `begin`/`end`/`date` to int years (reusing
`_coerce_year`), enforces the `date` ↔ `begin`/`end` exclusivity, and resolves the
five relation lists through the same `slug_index` used for participants; unresolved
names become `UnresolvedParticipant`-style soft warnings (no abort).

## Temporal reading model (`validation/validators/temporal.py` + `validation/queries.py`)

`temporal` is a **pure graph consumer**. `queries.py` exposes read-only helpers that
project the interval graph into a plain in-memory shape the validator reasons over:

```python
@dataclass(frozen=True)
class EventInterval:
    uri: str
    begin: int | None        # gYear reachable via boundary tagged type/begin, else None
    end: int | None          # gYear reachable via boundary tagged type/end, else None

def load_intervals(indexer) -> dict[str, EventInterval]   # one per G5_Narrative_Event
def load_relations(indexer) -> dict[str, set[tuple[str, str]]]
    # keyed by relation localname: {"follows": {(a,b),…}, "precedes": …, "overlaps": …,
    #                                "includes": …, "included-in": …}
```

- `load_intervals` reads the `gYear` reachable from each event via
  `(CSM:duration|TR:temporal-location)/TR:temporal-location/{boundary}` where the
  boundary's `crm:P2_has_type` is `…type/begin` (resp. `end`), then
  `(crm:P90_has_value | crm:P43_has_dimension/crm:P90_has_value)` — so it is insensitive
  to whether the year sits on the boundary directly or on its `Dimension`.
- The four FR-015 contradiction rules (a–d) are computed exactly as research **D12**;
  each yields one `error`-severity `Violation` whose `triples` carry the implicated
  relation edge(s) and whose `source` is `resolve_source(indexer, …)` (D6) or `None`
  for graph-wide findings (cycles, pairwise conflicts). Findings are deduped (D8).

## Graph predicate constants

In `golem/namespaces.py` (so the closure test covers them — all ∈ `frozen_terms()`,
verified 2026-06-02):

```python
TR  = Namespace("http://www.ontologydesignpatterns.org/ont/dlp/TemporalRelations.owl#")
CSM = Namespace("http://www.ontologydesignpatterns.org/ont/dlp/CommonSenseMapping.owl#")

DURATION              = CSM["duration"]                    # frozen ✓ (⊑ temporal-location)
TEMPORAL_LOCATION     = TR["temporal-location"]            # frozen ✓ (interval → boundary)
FOLLOWS               = TR["follows"]                      # frozen ✓
PRECEDES              = TR["precedes"]                      # frozen ✓
TEMPORALLY_OVERLAPS   = TR["temporally-overlaps"]          # frozen ✓ (symmetric)
TEMPORALLY_INCLUDES   = TR["temporally-includes"]          # frozen ✓
TEMPORALLY_INCLUDED_IN= TR["temporally-included-in"]       # frozen ✓
# CLASS_IRI gains:  "TimeInterval": DLP["time-interval"]   # frozen ✓ (DOLCE-Lite)
# Reused unchanged & already frozen: HAS_TYPE (crm:P2_has_type), HAS_DIMENSION
#   (crm:P43_has_dimension), HAS_VALUE (crm:P90_has_value), Dimension/E54, Type/E55.
# NOTE: crm:P4_has_time-span and CIDOC P82a/P82b/P81/P79/P80 are NOT frozen — never emit (D11).
```

`validation/queries.py` imports these read-only for its SPARQL/triple traversal. `CRM`
and the provenance predicates come from `golem.namespaces` unchanged.
