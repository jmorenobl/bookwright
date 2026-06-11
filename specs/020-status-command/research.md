# Phase 0 Research — 020 `bookwright status`

All unknowns were resolved by inspecting the shipped codebase (no external
research required: the feature is pure aggregation over existing subsystems).
Each decision below names the spec requirement it serves and the alternatives
rejected.

## D1 — "Staleness resolution": rebuild in memory every run, refresh `graph.ttl`

**Decision**: `status` does not detect staleness — it **always rebuilds** the
graph from the corpus by reusing the `graph build` pipeline, then refreshes
the derived `bible/graph.ttl` cache exactly as `graph build` does. The
pipeline body of `commands/graph/build.py::_build()` is extracted into a
shared `commands/_graph.py::build_project_graph()` returning the populated
engine, the `BuildReport`, and the research mapping result; `graph build` and
`status` both call it.

**Rationale**: The spec assumes "the same staleness resolution `bookwright
validate` already uses" (FR-001), but **no staleness machinery exists
anywhere in `src/`** (verified by grep: no mtime/staleness logic;
`commands/validate.py::_load_indexer` simply loads whatever `graph.ttl` is on
disk). The spec's intent — "never report facts from a stale graph" (edge
case), "facts reflect the current corpus" (US1-AS2) — is satisfied most
simply and most strongly by unconditional recomputation, which the spec
itself endorses as the freshness mechanism for the status cache
("recomputation is the freshness mechanism", Assumptions). Writing
`graph.ttl` back is explicitly sanctioned ("the only writes are the existing
derived-graph refresh and the new derived status cache", Out of Scope;
SC-007) and keeps a subsequent `bookwright validate` consistent with the
report (SC-003).

**Alternatives considered**:
- *Load `graph.ttl` as-is, like `validate`* — rejected: fails US1-AS2 and the
  stale-cache edge case outright; the on-disk cache may predate the corpus.
- *mtime-based staleness detection* — rejected: new machinery the spec says
  not to invent ("reuses that mechanism rather than defining a new one"),
  fragile across filesystems, and strictly more code than rebuilding a
  corpus that is tiny by design.
- *Rebuild in memory but don't write `graph.ttl`* — rejected: leaves
  `validate` disagreeing with the just-printed report until the author
  manually runs `graph build` (SC-003), and forgoes a write the spec
  explicitly budgets for.

## D2 — Determinism vs. minted URIs: items carry authored identifiers, never URIs

**Decision**: The report identifies every research item by **corpus-stable
keys**: the authored finding `id` (YAML front-matter), the file relpath, and
the claim/question text. Minted entity URIs never appear in the report. To
make this possible, `io/research.py` is extended **additively**:
`ResearchResult` gains `finding_records` / `anchor_records` tuples (frozen
dataclasses carrying `id`/`relpath`/minted-`uri` for findings, and
`promotes_id`/`constrains` (authored name or `"timeline"` or `None`)/
`relpath`/minted-`uri` for anchors). The minted `uri` field exists only as a
join key from graph projections back to authored identity, inside one
process; it is never serialized.

**Rationale**: `Finding` and `Anchor` are `MintedEntity`s — each build mints
fresh time-ordered uuid7 URIs (`golem/modules/provenance.py`). Since D1
rebuilds per run, any URI in the report would change every run, violating
SC-002/FR-014 (byte-identical output). The authored `id` is already required
and uniqueness-checked per file by `_build_finding`; today it is discarded
after anchor resolution. The graph deliberately does **not** carry authored
ids (frozen ontology, Principle X — adding an id property is forbidden), so
the mapping result is the only legitimate carrier. This also fulfils the
clarification "Counts + item lists … the actual queue" (FR-011a) with items a
skill can actually quote back to the author.

**Alternatives considered**:
- *Report minted URIs/labels* — rejected: byte-unstable across runs (SC-002).
- *Persist authored ids into the graph* — rejected: new ontology property,
  Principle X violation.
- *Re-parse research files inside `status`* — rejected: duplicates the
  reader; the mapping result is already in hand from the D1 build.

## D3 — Anchor-gap detection: extract pure predicates from `factual_anchor`

**Decision**: The R1/R3/R4 *decisions* inside
`validation/validators/factual_anchor.py` are extracted as module-level pure
predicates — `anchor_unsourced(sources, finding_present)`,
`anchor_under_reliable(sources, minimum)` (returning the
under-reliable/unrated distinction), and target-presence via the existing
public `anchor_queries.entity_present` — with the reliability rank
(`_RELIABILITY_ORDER`/`_RANK`) promoted alongside them. The validator's
methods call the predicates and keep owning message construction and
`Violation` assembly; `status` aggregation calls the same predicates over the
same `anchor_queries.load_anchors` / `load_sources_by_anchor` projections.

**Rationale**: FR-005 mandates "reusing the detection logic … rather than
duplicating it". Deriving the anchor queue by parsing the validator's
`Violation` messages/triples was rejected as fragile (R2's implicated triple
subject is the finding, not the anchor; messages embed minted-URI labels —
byte-unstable under D1/D2). Predicate extraction is a behavior-preserving
refactor pinned by the existing `test_factual_anchor.py` suite plus new
parity guards, and gives `status` exactly the booleans it needs with zero
logic forks.

**Alternatives considered**:
- *Filter the validator's violations* — rejected: message/triple parsing is
  fragile and minted-label-dependent.
- *Reimplement the rules in `status/queries.py`* — rejected: the divergent
  re-implementation FR-005 forbids.

## D4 — Fault model: mirror `graph build`/`validate`; skipped bible files are corrupt corpus

**Decision**: `status` propagates the build pipeline's hard failures with the
same envelopes and exits as `graph build`: `ProjectNotFoundError` /
`ManifestError` / `MissingDirectoryError`-class faults / `UnknownIndexerError`
/ `ResearchError` → unified error envelope, exit 2 (`EXIT_CONFIG`);
`SlugCollisionError` → exit 3. A build that **skips** bible files (malformed
front-matter — `graph build`'s exit-4 condition) makes `status` fail with a
unified error envelope (code `skipped_sources`, details listing each skipped
file and reason) and **exit 4**, mirroring `graph build`'s exit code for the
identical corpus. All error types subclass `BookwrightError` (iteration 018);
no hand-rolled envelopes.

**Rationale**: The clarification is explicit: corrupt information is a hard
error "exactly as `graph build` / `validate` on the same corpus"; graceful
degradation is reserved for *absent* information. `graph build` signals
skipped files with exit 4 while still writing a partial graph — but `status`
cannot responsibly print a "facts" report computed from a corpus it knows it
dropped files from, so the partial-success half of exit 4 becomes a full
error for `status` while the exit code stays aligned per-corpus.

**Alternatives considered**:
- *Proceed on skipped files, exit 0* — rejected: reports facts from a
  knowingly incomplete corpus; contradicts the clarification.
- *Collapse everything to exit 2* — rejected: breaks per-corpus exit parity
  with `graph build` that the spec leans on.

## D5 — Graceful degradation boundary: missing build prerequisites ⇒ degraded, exit 0

**Decision**: When the build prerequisites are *absent* — `paths.bible` is
not a directory, or the manuscript signal `manuscript_present()` is false
(the conditions `graph build` turns into `MissingDirectoryError`) — `status`
does **not** run the pipeline and does not fail: it reports
`graph: {available: false, entities: 0, triples: 0}`, empty research facts,
an empty validation summary, plus phase and focus echo, and exits 0. The rule
table then yields at most a single bootstrap action. An *empty-but-present*
bible builds normally (zero entities) and is likewise a degraded state, not
an error. A missing `bible/research/` or absent `[focus]` is already a
non-event (`map_research` returns an empty result; `manifest.focus` is
`None`).

**Rationale**: FR-013 and the v0.2-era edge case (SC-006) require absence to
degrade, while `graph build` treats the same absence as exit 2 — the one
place `status` deliberately diverges from the pipeline's fault model, because
for a *report* "there is nothing here yet" is a fact, not a failure.

**Alternatives considered**: propagating `MissingDirectoryError` — rejected:
directly violates FR-013/SC-006.

## D6 — Success envelope helper + byte-identical cache

**Decision**: Add `ok_payload(**fields) -> dict` to `commands/_envelope.py`,
producing `{"status": "ok", **fields}` — the success-side complement of
`BookwrightError.to_json()`, single-sourcing the `"status": "ok"` literal that
`check`/`focus`/`graph` currently hand-roll (existing call sites are NOT
migrated in this iteration; scope discipline). `status` builds its document
once — `ok_payload(focus=…, state=…, next_actions=…)` — serializes it once
with the same encoding `emit_json` uses
(`json.dumps(payload, separators=(",", ":")) + "\n"`), then writes those
bytes to `.bookwright/cache/status.json` (creating `.bookwright/cache/`
with `mkdir(parents=True, exist_ok=True)`) and, under `--json`, the identical
bytes to stdout. One serialization, two sinks ⇒ US3-AS4 byte-identity is
structural, not tested-into-existence. The cache is written on every
successful run, also in human mode (FR-012); human report goes to stdout
without `--json` (FR-011), prose/progress to stderr.

**Rationale**: the user's planning input mandates an explicit success-envelope
helper; the cache/stdout byte-identity requirement makes shared serialization
the obvious mechanism. The scaffold's `.gitignore` already excludes
`.bookwright/cache/` (verified) — no scaffold change.

**Alternatives considered**: `io/fs.write_bytes_atomic` — rejected: it is
ledger/rollback machinery for `init`; a regenerated-every-run cache needs no
ledger. Plain `Path.write_text` suffices.

## D7 — Rule table shape: ordered static tuple of (predicate, action-builder)

**Decision**: `status/rules.py` defines a module-level
`RULES: tuple[Rule, ...]` in **fixed priority order**, where each `Rule`
pairs a name, a pure predicate over `StatusState`, and a pure action builder
producing one `Action(skill, prompt, reason)` from state facts. Fixed English
prompt templates (clarification #2) parameterized only by counts/identifiers.
`next_actions(state)` walks the table in order and concatenates — no
sorting pass needed beyond the table's own order, because item lists inside
the state are already deterministically ordered (D2/D8). The degraded state
(D5: `graph.available is false` or zero entities) short-circuits to at most
one bootstrap action. Baseline table (FR-009): ① bootstrap (degraded graph) →
build/author the bible; ② open questions ∪ unresolved anchors → skill
`bookwright-research`, prompt listing the queue, reason citing the count;
③ low-reliability findings → skill `bookwright-verify`; ④ validation errors →
review the bible (`bookwright validate` pointer); ⑤ no focus →
`bookwright focus set`. A healthy, focused project yields `[]`.

**Rationale**: FR-008/FR-010 demand purity, byte-stable order, and
isolation-testability; a declarative table makes SC-005 ("for every rule, a
synthetic state exercises it") a direct iteration over `RULES` in tests.

**Alternatives considered**: if/elif chain inside the command — rejected:
not isolation-testable, invites drift; priority ordering implicit.

## D8 — Aggregation queries live in `status/queries.py`, via the `Indexer` seam

**Decision**: New SPARQL aggregations — open findings
(`?f bw:open true`, with optional `bw:claim`) and findings with
below-threshold best support (`?f bw:supportedBy ?s . ?s bw:reliability ?r`)
— live in `src/bookwright/status/queries.py`, written like
`validation/queries.py` / `anchor_queries.py`: through the `Indexer`
protocol, IRIs from `golem.namespaces`, no rdflib import, results joined to
authored identity via the D2 record maps and sorted by `(relpath, id)`.
Anchor facts reuse `anchor_queries.load_anchors` / `load_sources_by_anchor`
unchanged. The validation summary reuses
`discover_validators` / `resolve_active` / `run_validators` and reports
counts per severity (the `ValidationReport._by_severity` shape) plus the
sorted `ran` list — violation *messages* stay out of the report (they embed
minted-URI labels; D2).

**Rationale**: matches the user's planning input ("no SPARQL duplication;
aggregation queries next to `validation/queries.py` or in a status queries
module") and the established projection-module idiom; keeps `status` free of
rdflib (mirroring FR-003 of iteration 014).

**Alternatives considered**: computing research facts purely from the mapping
result without SPARQL — workable, but rejected for FR-004's "in the graph"
wording, for symmetry with the anchor projections that *must* come from the
graph, and to honor the iteration's explicit module guidance.
