# Research: Ingestion-parity guard + deferral registry

Phase 0 decisions. Each resolves a design choice the spec left open or that the
codebase forced. No NEEDS CLARIFICATION remain after this document.

## D1 — Exercise fixture: a new minimal `parity-exercise`, not an extended existing one

**Decision**: Add a dedicated, minimal fixture `tests/fixtures/parity-exercise/` that
drives exactly the six reachable ingestion paths.

**Rationale**: The spec's planning hint preferred reusing an existing fixture, but
**no committed fixture exercises every current ingestion path**. Confirmed by
inspection: neither `tiny-novel` nor `tiny-historical` ships a `bible/relationships.md`,
and `SocialRelationship` materializes *only* from that collection file
([bible.py:210](../../src/bookwright/io/bible.py#L210)). So "use an existing fixture as
is" is factually impossible — a fixture must be created or extended.

Between the two real options:

- **Extend `tiny-historical`** (add `relationships.md`): matches the hint literally but
  `tiny-historical` is the **oracle-pinned corpus** of the 023 orchestration E2E test
  (`tests/e2e/test_orchestration_workflow.py`, driven by `expected-status.md`). Adding a
  `SocialRelationship` risks shifting validation findings / `next_actions` / entity
  counts the oracle pins, turning a behavior-neutral guard into a cross-test
  regression. High blast radius for no benefit.
- **New `parity-exercise` fixture**: the spec explicitly permits "introduce a wholly new
  corpus." A single-purpose fixture whose *only reason to exist* is the parity guard
  cannot be silently under-exercised (its diff is its contract), keeps the guard's blast
  radius to zero, and is trivially minimal (5 files). Chosen.

**Alternatives considered**: extend `tiny-novel` (same oracle/Group-B coupling risk in
023); reuse `tiny-historical` unchanged (would make `SocialRelationship` look orphaned,
the test would fail surfacing a fixture gap — exactly the edge case the spec warns
about, so it must be avoided by construction).

## D2 — Liveness probe: `build_project_graph(...).engine`, not `map_bible` + `to_turtle`

**Decision**: Build the graph through the real pipeline
`build_project_graph(root, manifest)` ([_graph.py:75](../../src/bookwright/commands/_graph.py#L75))
and query the returned `BuildOutcome.engine` (an `RdflibIndexer`) with
`SELECT DISTINCT ?t WHERE { ?s a ?t }`.

**Rationale**: The `crm:E13_Attribute_Assignment` provenance carrier — one of the six
"alive" concepts — is **reified during indexing**, not emitted by `map_bible`/`to_turtle`.
Only the full pipeline produces it. Using the pipeline's own engine (a) observes the
graph the engine actually produces (FR-003: derived, never hand-listed), (b) runs
in-process so it counts toward coverage (Constitution VIII), and (c) matches the hint
"construye el grafo con `RdflibIndexer`" — the engine *is* the `RdflibIndexer`.

**Alternatives considered**: run `bookwright graph build` via `CliRunner` then reload
`bible/graph.ttl` into a fresh `RdflibIndexer` — equally faithful but adds a CLI hop and
a re-parse for no extra signal; querying the pipeline's engine directly is leaner.
Building only from `map_bible` entities — rejected: misses `AttributeAssignment`.

## D3 — Scoping the verdict: map observed IRIs back through `CLASS_IRI`, intersect with `CONCEPTS`

**Decision**: `reachable = { name for name, iri in CLASS_IRI.items()
if iri in observed_types and name in CONCEPTS }`; `orphans = set(CONCEPTS) - reachable`;
assert `orphans == set(DEFERRED_CONCEPTS)`.

**Rationale**: `CLASS_IRI` is a superset of `CONCEPTS` — it carries non-concept carriers
(`CharacterFeature`, `Dimension`, `Type`, `TimeInterval`) the closure test covers but the
parity contract must ignore (FR-010, edge case). Filtering the observed types through
`CLASS_IRI` and then `CONCEPTS` keeps the verdict scoped to the registry exactly. This
also handles the "new `CONCEPTS` entry" edge case for free: any `CONCEPTS` key that is
neither observed nor deferred lands in `orphans` but not `DEFERRED_CONCEPTS`, failing the
equality with a named symmetric-difference.

**Alternatives considered**: compare IRIs directly — clumsier to report by concept name
and would require re-deriving names for the failure message anyway.

## D4 — Registry shape: a frozen `NamedTuple` value in a static module-level dict

**Decision**: `class DeferralNote(NamedTuple): reason: str; target_version: str`, and
`DEFERRED_CONCEPTS: dict[str, DeferralNote]` with the seven entries from FR-002. Place in
a new `src/bookwright/golem/deferrals.py`.

**Rationale**: A `NamedTuple` is immutable, `mypy --strict`-friendly, trivially
unit-testable, and reads as plain data — no runtime state, no I/O (Key Entities). A new
module inside `golem/` honors "su propio módulo, junto a `golem/__init__.py`" and "no
toques `golem/` salvo el registro nuevo" (only addition, no edit to `__init__.py` or
`namespaces.py`). Keys are validated against `CONCEPTS` by the parity test, so a typo in
a key fails loudly. Target versions are free-text per FR-002 (`v0.3.x`, `v0.4`, and the
literal "undecided" / "to be decided" for G6/G3, whose wire-or-defer call is iteration
027's).

**Alternatives considered**: a `@dataclass(frozen=True)` (equivalent; `NamedTuple` is
lighter for a 2-field record); an `Enum` (over-modelled for free-text values); putting
the dict directly in `__init__.py` (rejected — the hint wants its own module and keeps
`__init__.py` untouched).

## D5 — Drift coverage: simulate the three failure modes in-test, no production hook

**Decision**: Beyond the live parity assertion (passes on current code), add
unit tests that simulate each drift by manipulating *local copies* of the two sets and
asserting the comparison helper reports the offending concept:

1. **fed-but-still-deferred** (FR-006): move a reachable concept into the deferred copy →
   failure names it.
2. **deferred-but-actually-fed** (FR-007): same condition viewed from the registry side.
3. **undeclared-orphan** (FR-008): drop a real orphan from the deferred copy → failure
   names it.

The comparison is factored into a small pure helper (e.g.
`parity_diff(reachable, deferred) -> (fed_but_deferred, undeclared_orphans)`) the live
assertion and the three simulations both call, so the failure-message contract (named
concept) is tested without mutating production data.

**Rationale**: FR-006/007/008 require the *test itself* to fail with a named concept
under drift; the cleanest way to prove that without committing a broken registry is to
exercise the pure diff helper on perturbed inputs. Determinism (FR-009/SC-004) follows
because the helper is a pure set function and the fixture build is reproducible.

**Alternatives considered**: parametrized `xfail` cases that actually corrupt
`DEFERRED_CONCEPTS` — fragile and pollutes the real registry; mutation via monkeypatch —
unnecessary indirection when a pure helper is directly callable.

## D6 — The author-only note: manuscript docstring + one Spanish docs line

**Decision**: Extend the module docstring of
[io/manuscript.py](../../src/bookwright/io/manuscript.py) (which already says "v0 does
**no** prose mining") so it explicitly also covers `outline/` as author-only in v0.3
(scaffold-created, engine-not-ingested), and add one line to the Spanish
[docs/authoring.md](../../docs/authoring.md) stating the same. There is **no**
`io/outline.py` — `outline/` has no reader at all — so the manuscript reader (the nearest
"presence-check, no mining" module) is the right code home, and the docs line is where an
author looks for directory status.

**Rationale**: FR-011 says "code and/or docs"; doing both removes the silence on both the
contributor side (code) and the author side (docs). Docs are Spanish by project
convention (CLAUDE.md); code/docstring is English. No ingestion behavior changes
(SC-005): `manuscript_present` and the absence of an `outline/` reader are untouched.

**Alternatives considered**: a new `io/outline.py` stub carrying the note — rejected as
scope creep (it would imply a reader exists); a standalone docs page — heavier than one
line in the existing authoring guide.
