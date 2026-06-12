# Data Model — 020 `bookwright status`

All types are in-memory, frozen, and serialized only into the report document
(stdout `--json` + `.bookwright/cache/status.json`). Nothing here touches the
ontology (Principle X) or adds canonical storage (Principle I). Determinism
rules: no minted URIs, no timestamps, no environment data anywhere in a
serialized shape (research.md D2); every list deterministically ordered
(FR-010, FR-011a).

## 1. Report document (the envelope)

The single success document, built via `_envelope.ok_payload(...)` and
serialized once (research.md D6):

```json
{
  "status": "ok",
  "focus": {"target": "...", "notes": "...", "updated_at": "YYYY-MM-DD"} | null,
  "state": { ... StatusState payload ... },
  "next_actions": [ {"skill": "...", "prompt": "...", "reason": "..."}, ... ]
}
```

- `focus` — `manifest.focus.model_dump()` or `null`, exactly the shape
  `focus show --json` emits (FR-003, SC-003). `updated_at` comes from the
  manifest, never the clock.
- Failures never use this shape: they are `BookwrightError.to_json()`
  envelopes (`{"status":"error", "code", "message"[, "details"]}`, iteration
  018) with non-zero exit.

## 2. `StatusState` (`src/bookwright/status/model.py`)

The aggregate of all derived facts; the **only** input to the rule table.
Frozen dataclass; `to_payload() -> dict` produces the `state` object.

| Field | Type | Source | Payload key |
|---|---|---|---|
| `phase` | `BookStatus` (str literal) | `manifest.book.status` | `phase` |
| `focus_defined` | `bool` | `manifest.focus is not None` | *(not serialized — `focus` is top-level; predicate input only)* |
| `graph` | `GraphFacts` | build pipeline outcome | `graph` |
| `open_questions` | `tuple[OpenQuestion, ...]` | `status/queries.open_findings` ⋈ finding identities | `open_questions` |
| `unresolved_anchors` | `tuple[AnchorGap, ...]` | `anchor_queries` projections + extracted predicates ⋈ anchor identities | `unresolved_anchors` |
| `low_reliability_findings` | `tuple[LowReliabilityFinding, ...]` | `status/queries.low_reliability_findings` ⋈ finding identities | `low_reliability_findings` |
| `validation` | `ValidationSummary` | `run_validators` output | `validation` |

Each item-list payload is an object `{"count": N, "items": [...]}` (FR-011a:
count + items, always both).

### 2.1 `GraphFacts`

| Field | Type | Notes |
|---|---|---|
| `available` | `bool` | `False` only on the degraded path (research.md D5: build prerequisites absent) |
| `entities` | `int` | from `BuildReport.entities` (0 when unavailable) |
| `triples` | `int` | from `BuildReport.triples` (0 when unavailable) |

### 2.2 `OpenQuestion` — the bottom-up research queue (FR-004)

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | authored finding `id` (corpus-stable) |
| `text` | `str \| None` | the finding's `claim` (an open question may have none) |
| `file` | `str` | research file relpath |

Order: `(file, id)` ascending.

### 2.3 `AnchorGap` — anchors lacking support / unresolvable targets (FR-005)

| Field | Type | Notes |
|---|---|---|
| `promotes` | `str` | authored `id` of the promoted finding (the anchor's stable identity) |
| `constrains` | `str \| None` | authored target name, `"timeline"`, or `None` (dropped link) |
| `file` | `str` | research file relpath |
| `problems` | `tuple[str, ...]` | sorted subset of `{"unsourced", "under_reliable", "unrated", "missing_finding", "missing_target"}` — one entry per extracted predicate that fired (research.md D3) |

Order: `(file, promotes, constrains or "")` ascending. An anchor appears once
with all its problems (no duplicate rows per rule).

### 2.4 `LowReliabilityFinding` (FR-006)

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | authored finding `id` |
| `best_reliability` | `str \| None` | best supporting rating name (`baja`/`media`/`alta`) or `None` when no source carries a rating |
| `file` | `str` | research file relpath |

Membership: findings **with ≥ 1 source** whose best rated support ranks below
`manifest.research.min_reliability_for_anchor` (unrated counts as below every
threshold) — the same scale/rank single-sourced from the `factual_anchor`
extraction (research.md D3). Order: `(file, id)` ascending.

### 2.5 `ValidationSummary` (FR-007)

| Field | Type | Notes |
|---|---|---|
| `counts` | `dict[str, int]` | one key per `Severity`, zero-filled, serialized in fixed key order `error`/`warning`/`info` — the `ValidationReport._by_severity` shape (byte-identity, SC-002) |
| `ran` | `tuple[str, ...]` | validator names, sorted (the runner's `ran`) |

No violation items: messages embed minted-URI labels (research.md D2/D8);
counts are what FR-007 requires and what rule ④ consumes.

## 3. `Action` and the rule table (`src/bookwright/status/rules.py`)

### 3.1 `Action`

| Field | Type | Constraint |
|---|---|---|
| `skill` | `str` | skill or CLI command to invoke (SC-004) |
| `prompt` | `str` | paste-ready, fixed English template + state facts only |
| `reason` | `str` | one line, cites the triggering fact/count |

### 3.2 `Rule`

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | stable rule identifier (test addressing, SC-005) |
| `applies` | `Callable[[StatusState], bool]` | pure predicate |
| `build` | `Callable[[StatusState], Action]` | pure builder |

`RULES: tuple[Rule, ...]` — module-level constant, **priority order is the
tuple order** (FR-010). `next_actions(state: StatusState) -> list[Action]`
walks the tuple, with the D5 short-circuit: a degraded/empty graph yields at
most the bootstrap action.

| # | name | predicate | action (skill / reason sketch) |
|---|---|---|---|
| 1 | `bootstrap_graph` | `not graph.available or graph.entities == 0` | author/build the bible (bootstrap; suppresses 2–5) |
| 2 | `research_queue` | `open_questions or unresolved_anchors` | `bookwright-research`; prompt lists the queue ids/texts; reason cites the count |
| 3 | `verify_findings` | `low_reliability_findings` | `bookwright-verify`; reason cites the count |
| 4 | `review_continuity` | `validation.counts["error"] > 0` | review the bible (run `bookwright validate` for detail) |
| 5 | `define_focus` | `not focus_defined` | `bookwright focus set`; suppressed by the D5 short-circuit, like rules 2–4 |

Exact prompt wording is fixed at implementation time and pinned by the
exact-match tests (FR-008: determinism requires the templates be *fixed*, not
any particular wording).

## 4. `io/research.py` additive records (research.md D2)

| Type | Fields | Purpose |
|---|---|---|
| `FindingIdentity` | `id: str`, `relpath: str`, `uri: str` | authored identity for every finding; `uri` is the in-process join key to graph projections, never serialized |
| `AnchorIdentity` | `promotes_id: str`, `constrains: str \| None` (authored name / `"timeline"`), `relpath: str`, `uri: str` | authored identity for every anchor |

`ResearchResult` gains `finding_identities: tuple[FindingIdentity, ...]` and
`anchor_identities: tuple[AnchorIdentity, ...]`; existing fields, entity models,
and emitted triples are untouched (no ontology change, no behavior change for
`graph build`).

## 5. Shared pipeline outcome (`commands/_graph.py`, research.md D1)

`build_project_graph(root, manifest) -> BuildOutcome` where `BuildOutcome`
bundles `engine: Indexer`, `report: BuildReport`, `research: ResearchResult`.
`graph build` keeps its exact observable behavior (same report, same writes,
same fault model); `status` consumes the engine + the research identities and applies its own
fault mapping (research.md D4/D5).

## 6. Status cache (`.bookwright/cache/status.json`)

Byte-identical copy of the `--json` stdout document (one serialization, two
sinks — research.md D6). Regenerated on every successful run, in both output
modes. Write-only output: never parsed, never an input (FR-012); directory
created on demand; already gitignored by the scaffold.
