# Implementation Plan: Outline ingestion — narrative sequences (G7)

**Branch**: `029-narrative-sequences` | **Date**: 2026-06-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/029-narrative-sequences/spec.md`

## Summary

Bring `G7_Narrative_Sequence` into the derived graph by extending the
iteration-028 `outline/units/` pass to read two new optional unit-card keys —
`sequence` (string) and `order` (integer) — and, **after all unit cards are
built**, assembling one `NarrativeSequence` per distinct sequence slug whose
`dlp:proper-part` members are the units that named it, ordered ascending by
`order`. Assembly is a second step over a side-channel of `(sequence, order,
unit)` records collected during the per-file pass — never per-file — because
`sequence`/`order` are not attributes of the `NarrativeUnit` entity and cannot
be recovered from it (golem/ is untouched). The `NarrativeSequence` model and
its `units` cross-ref already exist (`golem/modules/narrative.py`); this feature
only supplies the ordered member tuple. G7 leaves the deferral registry,
the parity test asserts an orphan set of exactly `{RelationshipRole (G6),
PsychologicalState (G3)}`, the `bookwright-outline` source command documents the
two new keys, and every present-tense "G7 is unfed" docstring/doc statement is
swept.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `rdflib`, `pydantic` v2 — no new runtime dependency.
The frozen ontology already declares `G7_Narrative_Sequence` (`CLASS_IRI`) and
`dlp:proper-part` (`PROPER_PART`); Principle X holds with zero ontology edits.

**Storage**: Plain-text `outline/units/*.md` cards → GOLEM entities →
`RdflibIndexer` → derived `bible/graph.ttl` cache (always reconstructible,
Principle I). No new file or directory format; **no** `outline/sequences/` dir.

**Testing**: `pytest` (≥ 80 % coverage gate). New unit tests for the assembly
helper in `io/outline.py`; the existing `tests/golem/test_ingestion_parity.py`
flips G7 from orphan to fed; `tests/integrations/test_materialize.py` stays green
on the edited source command.

**Target Platform**: CLI (`bookwright graph build` / `validate`), offline.

**Project Type**: Single project (src-layout, `src/bookwright/`).

**Performance Goals**: N/A (build-time over a handful of cards; assembly is a
single grouped sort, O(n log n) in the number of sequenced units).

**Constraints**: Every source file ≤ 500 lines (Principle IV) — `outline.py` is
160 lines today and gains ~70; no split needed. Determinism is a release gate
(SC-003/004): sorted-glob iteration + a total sort key + insertion-ordered
grouping make the member tuple and the `NarrativeSequence` set byte-for-byte
stable across builds, independent of filesystem/dict iteration order.

**Scale/Scope**: One `io/outline.py` module edit, one `_bible_builders.py`
constant touch (none required — see Decision 6), one source command markdown,
one fixture card, the deferral registry, the parity test, and four
present-tense doc/docstring surfaces.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **Principle I — plain-text source of truth**: PASS. `sequence`/`order` are
  authored YAML front-matter on existing cards; the graph remains a derived,
  reconstructible cache. A duplicate/missing `order` degrades softly (no abort),
  consistent with the mapper ethos.
- **Principle IV — ≤ 500 lines / one subcommand per module**: PASS. `outline.py`
  ends well under 500; no new CLI subcommand (this rides the existing `graph
  build` pipeline). No split required (the `bible.py`/`_bible_builders.py`
  precedent is available if a future key set forces it).
- **Principle VI/VII — Agent Skills only, agentskills.io limits**: PASS. The
  `bookwright-outline` source command is re-materialized as `SKILL.md` by the
  existing pipeline for `claude` and `generic`; no `.claude/commands/` write; the
  `lint_skill_md` gate (name ≤ 64, description ≤ 1024, valid YAML) stays green.
- **Principle VIII — test discipline ≥ 80 %**: PASS. New assembly/coercion paths
  are covered by the five spec'd unit tests plus the parity flip.
- **Principle IX — JSON-over-stdout / acyclic layering**: PASS. `io/outline.py`
  already imports one-way from `.bible` / `._bible_builders`; no new import edge.
  No envelope change (this feature emits no new agent-facing command output).
- **Principle X — frozen ontology**: PASS. No new class or property; the 17-class
  closure and `golem.ttl` are untouched. `golem/` is not edited at all.
- **Scope & Release Discipline**: PASS. No plumbing "for future X": this iteration
  feeds G7 and nothing beyond it. `E55_Type` tagging (030), continuity validators
  (031), and the G6/G3 re-target (032) are explicitly out of scope and left in the
  registry.

**Result: PASS — no violations, Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/029-narrative-sequences/
├── plan.md              # This file
├── research.md          # Phase 0 — the assembly/ordering/provenance decisions
├── data-model.md        # Phase 1 — entities, the member record, the sort key
├── quickstart.md        # Phase 1 — runnable validation scenarios
├── contracts/
│   └── sequence-ingestion.md   # unit-card frontmatter + observable graph shape
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── io/
│   ├── outline.py            # EDIT: read sequence/order; collect members; assemble sequences
│   └── _bible_builders.py    # (no edit required — see research Decision 6)
├── golem/
│   ├── deferrals.py          # EDIT: drop NarrativeSequence; fix the count prose (3→2)
│   ├── modules/narrative.py  # UNTOUCHED — NarrativeSequence + units cross-ref already exist
│   └── ...                   # ontology frozen, not edited
└── resources/commands/
    └── bookwright-outline.md # EDIT: document optional sequence/order on unit cards (two places)

tests/
├── golem/test_ingestion_parity.py   # EDIT: G7 fed; orphan set → {RelationshipRole, PsychologicalState}
├── io/test_outline_sequences.py     # NEW: the five sequence-assembly scenarios
└── fixtures/parity-exercise/
    └── outline/units/                # EDIT: one card gains sequence/order so G7 is live in the build

docs/authoring.md            # EDIT: the v0.4 note adds "y secuencias"
bookwright-design.md         # EDIT: § 7.4 — G7 now ingested unit-driven; keys gain sequence/order
src/bookwright/io/manuscript.py  # EDIT: module docstring adds "drive NarrativeSequence"
```

**Structure Decision**: Single project, src-layout. The entire engine change is
contained in `io/outline.py`; the rest is the registry flip, the parity test, the
fixture, the source command, and the present-tense documentation sweep (FR-015).

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
