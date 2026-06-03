# Quickstart — Provenance Model (Source / Finding / Anchor)

End-to-end walk-through proving the three user stories on a fixture. Assumes
iterations 1–6 are on `main` (`bookwright init`, the GOLEM model, `graph build`,
`graph query` all work).

## 0. Setup

```bash
uv sync
```

The walk-through is exercised by `test_research_build.py` over the graph-test
`tiny_novel` scaffold (`tests/commands/graph/conftest.py`,
`scaffold_project(with_research=True)`), whose narrative bible already has the
character `Manuel de Aparici` (→ `…/character/manuel-de-aparici`). With
`with_research=True` the scaffold gains a `bible/research/` directory:

```
bible/research/
├── _index.md
├── sources.md
└── detective-licencia.md
```

`sources.md` declares one `oficial` source (`reliability: alta`, Spanish — same as
the book's `language = "es"`, so no translation). `detective-licencia.md` declares
one finding citing that source and bearing on the character, plus an anchor that
promotes the finding, constrains the character, and carries a time-span. (See
`contracts/research-format.md` for the exact front-matter.)

## 1. US1 — Sources become typed nodes with full provenance

```bash
# from a project scaffolded like the with_research=True tiny_novel (see conftest.py)
uv run bookwright graph build --json
```

The build now parses `bible/research/` and writes Source triples into
`bible/graph.ttl`. Query the source's provenance facets:

```bash
uv run bookwright graph query \
  'SELECT ?p ?o WHERE { <…/source/registro-tip> ?p ?o }' --json
```

**Expect**: `crm:P2_has_type → bw:source-type/oficial`, `bw:reliability →
bw:reliability/alta`, plus `bw:reference`, `bw:author`, `bw:originalLanguage`,
`bw:accessDate`, `bw:originalQuote`, `bw:reliabilityJustification`. **No**
`bw:translation` (source language == book language) — SC-004. Asserts SC-001,
SC-003 (URI `…/source/{slug}`).

A source with a bad `type`/`reliability` aborts the build with a value-naming
error and writes no graph (FR-016, US1 §3, SC-006).

## 2. US2 — Findings reify on E13 and link to the narrative

```bash
uv run bookwright graph query \
  'SELECT ?f ?claim ?src WHERE {
     ?f a crm:E13_Attribute_Assignment ;
        bw:claim ?claim ;
        crm:P140_assigned_attribute_to <…/character/manuel-de-aparici> ;
        bw:supportedBy ?src }' --json
```

**Expect**: one row — the finding's claim and its supporting source, addressed by a
`…/finding/{uuid7}` URI. The open question from `_index.md` appears separately as
`?o a crm:E13_Attribute_Assignment ; bw:open true` with no claim/source (FR-008).
The finding is distinguishable from the bible's inferred assertions (segment
`finding` + `bw:claim`; SC-007). Asserts US2.

## 3. US3 — Anchors constrain the fiction and answer the payoff query

```bash
uv run bookwright graph query \
  'SELECT ?anchor ?claim ?source WHERE {
     ?anchor a crm:E13_Attribute_Assignment ;
             bw:constrains <…/character/manuel-de-aparici> ;
             bw:promotes ?finding .
     ?finding bw:claim ?claim ; bw:supportedBy ?source }' --json
```

**Expect**: the anchor, the promoted finding's claim, and its source — SC-002.
The time-span:

```bash
uv run bookwright graph query \
  'SELECT ?b ?e WHERE {
     ?a bw:constrains <…/character/manuel-de-aparici> ;
        crm:P4_has_time-span ?ts .
     ?ts crm:P82a_begin_of_the_begin ?b ; crm:P82b_end_of_the_end ?e }' --json
```

**Expect**: the begin/end years (FR-010). An anchor without a time-span returns no
row. An anchor with `constrains: timeline` links to the timeline URI (US3 §4).

## 4. Regression — projects that don't research pay nothing

```bash
# The default tiny_novel (with_research=False) — no bible/research/ directory:
uv run bookwright graph build --json   # succeeds; zero research triples (SC-005)
uv run pytest tests/commands/graph/test_provenance.py   # bible E13 count still 10
```

## 5. Full gate

```bash
uv run pytest
uv run ruff check && uv run ruff format --check
uv run mypy --strict src tests
```

All green ⇒ the provenance model is in `bible/graph.ttl`, derived from
`bible/research/`, with no new GOLEM class and no new runtime dependency.
