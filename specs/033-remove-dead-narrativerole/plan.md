# Implementation Plan: Remove dead `NarrativeRole` concept + harden ingestion-parity

**Branch**: `033-remove-dead-narrativerole` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/033-remove-dead-narrativerole/spec.md`

## Summary

Delete the dead top-level GOLEM concept `NarrativeRole` (in `CONCEPTS`, but no
builder ever mints it) without losing any capability: the RDF class
`golem:G11_Narrative_Role` stays frozen and is still materialized exactly as
before by its real, character-scoped carrier `CharacterRole`. The change is
information-preserving by construction — zero triple regression — and **closes
DEBT-001** by hardening the ingestion-parity contract so a concept whose class
IRI is carried *only* by a non-`CONCEPTS` carrier (the IRI-collision pattern
that let the dead concept masquerade as "reachable") is named as a failure
rather than silently counted alive.

Technical approach: a small, mechanical surface edit (remove the class + its
three references in `golem/__init__.py`), a reconciliation sweep of every stale
"thirteen concepts" count across live source and tests (CHANGELOG history left
untouched per Principle I), a one-line widening of the parity test's
`CARRIER_NAMES` plus a new pure collision invariant + drift simulation, the
relocation of the deleted class's G11 triple/URI coverage onto `CharacterRole`
(already independently covered), and the deletion of the DEBT-001 ledger entry
and its roadmap §4 cross-reference. No new mechanism, no new dependency, and —
the load-bearing gate — **no ontology change**.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `rdflib`, `pydantic` v2 (no change; no addition)

**Storage**: plain-text source (`bible/*.md`, `outline/units/*.md`) → derived
`bible/graph.ttl` cache (Constitution I). Unchanged by this iteration.

**Testing**: `pytest` + `pytest-cov` (≥ 80 % gate), `mypy --strict`, `ruff`

**Target Platform**: cross-platform CLI / library (`bookwright-cli`)

**Project Type**: single project (src-layout library + Typer CLI)

**Performance Goals**: N/A — no runtime-path change; graph build emits identical
triples.

**Constraints**: the frozen ontology MUST NOT change — `golem.ttl` byte-for-byte
identical and `CLASS_IRI` still holds all 17 class IRIs including
`golem:G11_Narrative_Role` (Constitution X / Principle X). Zero triple
regression in any built graph. All four CI gates green.

**Scale/Scope**: surgical. Touches ~9 files: 3 source
(`golem/modules/narrative.py`, `golem/__init__.py`, `golem/deferrals.py`,
`golem/modules/feature.py` docstring only), 4 tests
(`test_ingestion_parity.py`, `test_namespaces.py`, `test_triples.py`,
`test_uri.py`), 1 fixture header (`parity-exercise/manifest.toml`), and 2
plain-text ledgers (`DEBT.md`, `bookwright-roadmap.md`). No file is created or
grows toward the 500-line limit; `narrative.py` shrinks.

**Unknowns**: none. The spec resolved every owner decision (G11 = "rol de un
personaje", design line 1603; no character-independent role surface — Out of
Scope) and `/speckit-clarify` recorded no open questions. No NEEDS
CLARIFICATION remains.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` v1.5.0. Re-checked
after Phase 1 — still PASS.*

| Principle | Verdict | Note |
|---|---|---|
| I — Plain text as source of truth | ✅ PASS | Only `.py` / `.md` / `.toml` edits; the derived `graph.ttl` cache is untouched and still rebuilds identically. |
| II — Modern Python stack | ✅ PASS | No dependency added, removed, or swapped. |
| III — src-layout | ✅ PASS | All source edits under `src/bookwright/`, all test edits under `tests/`. |
| IV — Modular command surface / ≤ 500 lines | ✅ PASS | No new CLI verb; `narrative.py` shrinks (one class removed); no file approaches the limit. |
| V — Plugin-based integrations | ✅ N/A | No integration touched. |
| VI — Agent Skills only | ✅ N/A | No skill/command directory touched. |
| VII — agentskills.io compliance | ✅ N/A | No `SKILL.md` generated or changed. |
| VIII — Test discipline (≥ 80 % coverage) | ✅ PASS | Deleting dead, never-instantiated code removes only uncovered-by-intent lines; G11 triple/URI coverage is **relocated**, not dropped — `CharacterRole`'s G11 typing is already asserted in `tests/golem/test_character_attributes.py:50` and its URI segment in `test_uri.py::test_character_scoped_node_uri_patterns`. The parity contract gains tests. Coverage holds or rises. |
| IX — JSON-over-stdout | ✅ N/A | No CLI output contract touched. |
| X — Design-document axioms / frozen ontology | ✅ PASS (load-bearing) | The deletion is of the **Python concept**, never the **RDF class**. `golem:G11_Narrative_Role` stays in `CLASS_IRI` (17 IRIs preserved) and `golem.ttl` does not change. The `…thirteen_concepts…` namespace test is **reclassified** (G11's IRI moves concept→carrier bucket, 12 + 5 = 17), never lowered — the frozen 17 is asserted, not weakened. No § 16 axiom is reopened. |
| Scope & Release Discipline | ✅ PASS | Resolves recorded debt (DEBT-001) in its own structural iteration; adds no speculative plumbing; G6/G3 deferrals untouched (FR-010); no demand-pulled capability pulled forward. |

**Result**: no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/033-remove-dead-narrativerole/
├── spec.md              # Feature spec (input)
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 — decisions (mostly "no unknowns; here is why")
├── data-model.md        # Phase 1 — the concept/IRI/carrier registry as data
├── quickstart.md        # Phase 1 — the runnable before/after verification
├── contracts/
│   └── golem-surface.md # Phase 1 — post-change public surface + parity invariants
└── tasks.md             # Phase 2 — created by /speckit-tasks (NOT here)
```

### Source Code (repository root)

The files this iteration actually touches (no new files; src-layout preserved):

```text
src/bookwright/golem/
├── __init__.py                 # remove NarrativeRole import / CONCEPTS entry / __all__ entry; "thirteen"→"twelve" docstring
├── deferrals.py                # "Two of the thirteen"→"Two of the twelve"; DEFERRED_CONCEPTS unchanged
└── modules/
    ├── narrative.py            # DELETE the NarrativeRole class (FR-001)
    └── feature.py              # CharacterRole docstring rewrite only (FR-012); golem_class = CLASS_IRI["NarrativeRole"] PRESERVED

tests/golem/
├── test_ingestion_parity.py    # drop NarrativeRole from reachable pin; CARRIER_NAMES gains it; add collision invariant + drift sim
├── test_namespaces.py          # rename …thirteen_concepts…; move G11 IRI concept→carrier bucket (12+5=17)
├── test_triples.py             # drop NarrativeRole import/instantiation; NarrativeUnit.roles cross-ref via bare URIRef
└── test_uri.py                 # drop NarrativeRole from SEGMENTS; "12 slugged concepts"→"11"

tests/fixtures/parity-exercise/
└── manifest.toml               # header comment: describe G11 via CharacterRole carrier, not a top-level NarrativeRole path

# repo root (plain-text ledgers)
DEBT.md                         # remove the ### DEBT-001 block (FR-009)
bookwright-roadmap.md           # remove the §4 "Decisión estructural sobre NarrativeRole (DEBT-001)" item; G11 status row (line 112) stays
```

Files deliberately **NOT** touched (each a guard against scope creep):
`src/bookwright/golem/namespaces.py` (the `CLASS_IRI["NarrativeRole"]` key is
preserved), `golem.ttl` / `schemas/` (frozen ontology), `CHANGELOG.md` (frozen
release history — Principle I), `tests/golem/test_character_attributes.py`
(already carries G11 carrier coverage; left as the relocation target),
`specs/005-golem-domain-model/` (frozen historical artifact).

**Structure Decision**: single project, src-layout — unchanged. This iteration
edits existing modules in place and creates no new package, module, or CLI verb.

## Complexity Tracking

No Constitution Check violations — section intentionally empty.
