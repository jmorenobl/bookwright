# Implementation Plan: G9 `rdfs:label` + queryable sequence order

**Branch**: `035-narrative-label-order` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/035-narrative-label-order/spec.md`

## Summary

Make the v0.4 narrative layer queryable **by content** and **by order**, closing the
DEBT-005 recall gap measured in dogfooding, without touching the frozen GOLEM ontology.

Two deltas, both in `src/bookwright/golem/modules/narrative.py`:

1. **Labels (US1/US3, P1/P2)** — `NarrativeUnit` and `NarrativeFunction` each emit a
   single `(uri, rdfs:label, Literal(name))` triple carrying their authored `name`,
   reusing the existing `CharacterRole` / `CharacterFeature` one-triple label shape. No
   new E13: the label rides the entity's already-emitted identity assertion (FR-006).
2. **Queryable order (US2, P1)** — each member unit's resolved position in its
   `G7_Narrative_Sequence` is materialized as a single per-unit predicate triple
   `(unit, bw:sequenceOrdinal, Literal(rank, xsd:integer))`, emitted from
   `NarrativeSequence.to_triples()` (the only place that knows the resolved order). The
   rank is the member's **1-based contiguous index in the already-sorted `units` tuple**
   (the existing `_member_sort_key` total order), so it is total and gap-free under a
   missing/duplicate/absent authored `order:`. It is reified through its **own**
   file-level `crm:E13_Attribute_Assignment` on the sequence-assembly path.

`bw:sequenceOrdinal` is a new property in Bookwright's own `bw:` namespace, declared in
`resources/vocabularies/sources.ttl` (the `bw:reference` home) with an
`rdfs:label`/`rdfs:comment` like its siblings — **never** in `golem.ttl`, never in
`CLASS_IRI`, never in the `test_namespaces.py` closure list. Two demonstrative SPARQL
queries ship as tests (find-by-label, list-in-order). DEBT-005 is deleted.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `rdflib` (graph + SPARQL), `pydantic` v2 (frozen entity
models). No new dependency.

**Storage**: Plain-text `outline/units/*.md` → derived `bible/graph.ttl` cache
(Constitution I). The graph stays a fully reconstructible cache; no authored state
moves into it (FR-013).

**Testing**: `pytest` (≥80% coverage gate), `mypy --strict`, `ruff check`, `ruff format
--check` — the four CI gates.

**Target Platform**: CLI, cross-platform.

**Project Type**: Single project (src-layout CLI), Option 1.

**Performance Goals**: N/A — emission adds O(units) triples per build; negligible.

**Constraints**: Frozen ontology (Principle X): no class/predicate added to `golem.ttl`
or `CLASS_IRI`. Every source file ≤ 500 lines (Principle IV). `narrative.py` is 76
lines today; the deltas keep it well under.

**Scale/Scope**: ~3 source files touched (`narrative.py`, `namespaces.py`,
`sources.ttl`), ~6 test files reconciled/added, 2 docs/debt edits.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I — Plain-text source of truth | ✅ PASS | Labels/ordinals are **derived** from `name`/`order:` in the plain-text cards; the graph remains a reconstructible cache (FR-013/SC-006). No authoring-format change (FR-010). |
| IV — One subcommand per module, ≤500 lines | ✅ PASS | All entity logic stays in `narrative.py` (~76→~120 lines). No CLI surface added. |
| V — Plugin integrations / no monolith | ✅ N/A | No integration or dispatcher change. |
| VI — Agent Skills only | ✅ N/A | No skill change. |
| VIII — Test discipline ≥80% | ✅ PASS | New triples covered by emission unit tests + two demonstrative SPARQL tests + E2E reconciliation. |
| IX — JSON-over-stdout | ✅ N/A | No CLI envelope change; `graph build`/`validate` payloads unchanged in shape. |
| **X — Design Document Axioms / frozen ontology** | ✅ PASS (with one justified test refinement) | **No** class/predicate added to `golem.ttl`; `CLASS_IRI` unchanged (17 IRIs); the `test_namespaces.py` closure list is **unmodified and green** (SC-005). `rdfs:label` is already in `frozen_terms()` (verified). The ordinal uses `bw:sequenceOrdinal`, declared in `sources.ttl`, intentionally outside the frozen GOLEM closure exactly like every `bw:reference`-family term. **One emission-closure test (`test_triples.py::test_term_closure_over_frozen_ontology`) needs a documented `bw:`-namespace exemption** — see Complexity Tracking; it preserves Principle X's substance (frozen GOLEM untouched) and merely makes explicit a tolerance the test already had implicitly. |
| Scope & Release Discipline | ✅ PASS | No speculative plumbing: the per-unit predicate (not a reified membership node) is chosen precisely because a unit declares at most one `sequence:` (clarified). Ships as `v0.4.3`, one observable delta family. |

**Initial gate: PASS.** Re-checked post-design (Phase 1): still PASS — the design adds no
ontology class/predicate and confines the only test-policy change to a single, justified
emission-closure exemption.

## Project Structure

### Documentation (this feature)

```text
specs/035-narrative-label-order/
├── plan.md              # This file
├── spec.md              # Feature spec (hardened)
├── research.md          # Phase 0 — the 6 design decisions + the closure-test resolution
├── data-model.md        # Phase 1 — entity deltas, the ordinal, provenance shape
├── quickstart.md        # Phase 1 — the two demonstrative SPARQL queries, run guide
├── contracts/
│   └── narrative-label-order.md   # Phase 1 — the triple/provenance/query contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── golem/
│   ├── namespaces.py            # + BW_SEQUENCE_ORDINAL = BW["sequenceOrdinal"] (+ __all__, doc)
│   └── modules/
│       └── narrative.py         # NarrativeUnit.to_triples (label); NarrativeFunction.to_triples
│                                #   (+ label); NarrativeSequence.to_triples (+ ordinals) and
│                                #   .derived_assertions (+ ordinal E13s)
└── resources/
    └── vocabularies/
        └── sources.ttl          # + bw:sequenceOrdinal rdf:Property declaration (label/comment)

tests/
├── golem/
│   ├── test_triples.py          # bw: exemption in term-closure test; label/ordinal emission asserts
│   ├── test_derived_assertions.py  # + NarrativeSequence ordinal-E13 assertion
│   └── test_narrative_label_order.py  # NEW — the two demonstrative SPARQL queries (FR-007/008/SC-003)
├── io/
│   └── test_outline_sequences.py   # + ordinal-materialization reinforcement (subject=unit, 1..N)
├── e2e/
│   └── test_narrative_workflow.py  # _ordered_members → SPARQL ORDER BY ordinal; docstring fix; label facts
└── fixtures/tiny-quest/
    └── expected-narrative.md       # + labels facts (units/functions); members list unchanged (FR-011)

docs/narrative-structure.md      # Spanish: labels + queryable order, with the two SPARQL snippets
DEBT.md                          # − DEBT-005 (resolved, removed per convention; FR-012)
```

**Structure Decision**: Single project, Option 1. The entire behavioural change lives in
`golem/modules/narrative.py` and one namespace constant; the vocabulary declaration is a
data file. Everything else is test/doc/debt reconciliation.

## Complexity Tracking

> One Constitution-adjacent decision needs to be recorded explicitly.

| Item | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| `bw:`-namespace exemption in `test_triples.py::test_term_closure_over_frozen_ontology` | `NarrativeSequence` is in `_sample_entities()` and now emits `bw:sequenceOrdinal`. That test asserts every emitted predicate ∈ `frozen_terms()` (the frozen GOLEM closure). `bw:` terms are **by design** outside that closure — which is exactly why research entities (`Source`/`Finding`, which emit `bw:reference` etc.) are excluded from `_sample_entities()` today. The exemption makes that already-existing tolerance explicit so a registered concept can carry a `bw:` term. | **Removing `seq` from `_sample_entities`** — loses real coverage of a core concept's emission and `rdf:type`. **Reverting to no `bw:` predicate** — the ordinal would need a frozen GOLEM predicate, i.e. an ontology change (forbidden, Principle X). The exemption preserves Principle X's substance: `golem.ttl`/`CLASS_IRI`/the `test_namespaces.py` closure list are all untouched (SC-005). |
| The ordinal's own `crm:E13_Attribute_Assignment` (target=unit, attribute=sequence, file-level) | FR-006 mandates the relational ordinal be reified (structural provenance: every non-identity assertion gets an E13). | Folding it into the unit's identity assertion (the label's shortcut) — rejected because the ordinal is *relational* (a property of the assembled membership), not intrinsic to the unit. The E13 mint URI is a time-ordered uuid7 (pre-existing `MintedEntity` behaviour, iteration 012) — not newly non-deterministic here; the determinism tests compare asserted facts, not E13 mint URIs (documented in research.md). |
