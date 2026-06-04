# Contract — `tiny-historical` fixture layout

The committed tree under `tests/fixtures/tiny-historical/`. Source-only (no derived
artifacts). Spanish narrative prose; English identifiers/structure (project language
convention). Short but coherent.

```text
tiny-historical/
├── manifest.toml
├── expected-findings.md            # co-located oracle (see expected-findings.md contract)
├── bible/
│   ├── constitution.md
│   ├── timeline.md                 # ≥1 event with a year (date/begin/end)
│   ├── characters/<slug>.md        # ≥1 character; the anachronistic anchor constrains a real one
│   ├── settings/<slug>.md          # ≥1 setting
│   └── research/
│       ├── sources.md              # several Sources, full provenance; ≥1 foreign-language (+translation); ≥1 `baja`
│       ├── <topic>.md              # findings + anchors (clean ones + defect #1 + defect #2)
│       └── _index.md               # ≥1 open question + topic map (prose body not indexed)
├── outline/
│   ├── synopsis.md
│   ├── structure.md
│   ├── arcs.md
│   └── scenes.md
└── manuscript/
    └── NN-<slug>.md                # chapter with the planted prose anachronism (defect #3)
```

## `manifest.toml` (required keys)

```toml
[bookwright]
cli_version_min = "0.0.1"
schema_version  = "golem-1.1"
manifest_version = "1"
uri_base = "https://example.org/tiny-historical/"
indexer  = "rdflib"

[book]
title    = "<título histórico>"
type     = "novel"
language = "es"
authors  = ["Equipo Bookwright"]
status   = "drafting"

[research]
enabled = true
source_languages = [ "<códigos ISO-639-1 de las fuentes extranjeras, p.ej. de, fr>" ]
min_reliability_for_anchor = "media"

[validators]
enabled = []      # all built-ins active, incl. factual_anchor
disabled = []
custom = []

[integration]
key = "claude"
skills_dir = ".claude/skills"

[paths]
manuscript = "manuscript/"
bible = "bible/"
outline = "outline/"
graph = "bible/graph.ttl"
constitution = "bible/constitution.md"
```

> `[vocabularies] active` is added **only if** a build/validate actually requires it (D8);
> existing research fixtures build without it.

## Research-file rules (must satisfy the strict reader — `io/research.py`)

- Every Source: all 9 required facets; `type` ∈ {primaria, secundaria, oficial, académica,
  periodística, testimonial}; `reliability` ∈ {alta, media, baja}; `translation` present iff
  `original_language ≠ "es"` (and absent when equal).
- Findings: non-open findings need a `claim` + ≥1 resolving `sources`. `bears_on` resolves to
  a real bible entity (no soft warnings — the fixture is otherwise clean).
- Anchors: `promotes` a finding in the same file; `constrains` a present bible entity (or the
  literal `"timeline"`); years are integers; `date` is mutually exclusive with `begin`/`end`.
- **Defect #1 (warning)**: one anchor promotes a finding whose only source is `baja`
  (< `media`). Everything about it parses; R3 flags it.
- **Defect #2 (error)**: one anchor `constrains` a **dated** timeline event with a year-span
  **disjoint** from the event's year (e.g. event `date: 1850`, anchor `begin/end: 1920`).
- All other anchors: fully-sourced ≥ `media`, present finding + entity, temporally consistent.

## Committed-tree invariants (asserted)

- No `bible/graph.ttl`; no `.claude/` / `.agents/`; no `SKILL.md`; no `[PENDING:` sentinel.
- The fixture is **excluded** from `tests/fixtures/test_fixtures.py`'s clean-fixtures
  parametrization (it validates with one warning + one error). Its hygiene (source-only,
  no-PENDING) is asserted inside `tests/e2e/test_research_workflow.py`.
