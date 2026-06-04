# Quickstart — the research flow on `tiny-historical`

This walks the deterministic stages the E2E test automates, then the **manual** verify step.
Everything reads the plain-text project; nothing here needs vectors or a network.

## 0. Get a working copy

```bash
# The fixture is source-only; build into a throwaway copy (never commit graph.ttl).
cp -r tests/fixtures/tiny-historical /tmp/th && cd /tmp/th
```

## 1. Build the graph (research entities land in the derived cache)

```bash
uv run bookwright graph build --json
```

Succeeds (exit 0). The derived `bible/graph.ttl` now carries the Sources, Findings, and
Anchors alongside the characters/settings/events. A foreign-language Source carries a
`bw:translation`; a Spanish one does not.

## 2. Query the anchors (the verify input)

```bash
uv run bookwright graph query --json '
  PREFIX bw:  <https://bookwright.dev/vocab/bw#>
  PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
  SELECT ?anchor ?claim ?source WHERE {
    ?anchor bw:promotes ?f . ?f bw:claim ?claim ; bw:supportedBy ?source }'
```

Returns the fixture's anchors with their researched claims and provenance — including the
**dated** anchor the manuscript later contradicts.

## 3. Validate (the deterministic verification layer)

```bash
uv run bookwright validate --json
```

`factual_anchor` reports **exactly** two findings:

- one **warning** — the *under-reliable anchor*: its only source is `baja`, below the
  manifest's `min_reliability_for_anchor = "media"`;
- one **error** — the *time-span anachronism*: the anchor's year-span is disjoint from the
  dated timeline event it constrains.

`validate` exits non-zero because of the error. These exact findings (which anchor, which
counts) are recorded in `expected-findings.md` next to the fixture.

## 4. Verify the manuscript (manual — the LLM layer)

This stage uses the `bookwright-verify` Agent Skill and an LLM's judgment; it is **not** a CLI
command and is **not** run in CI. Materialize the skills, then run it from your agent:

```bash
uv run bookwright integration use claude   # writes .claude/skills/bookwright-verify/SKILL.md
# then, in your agent (Claude Code, …):
/bookwright-verify
```

**Expected finding** (stated in `expected-findings.md`): the report flags the planted prose
anachronism in `manuscript/NN-<slug>.md` — a passage whose content is impossible in the
story's year — and cites the dated research anchor it contradicts. No verbatim report is
committed (it would rot and can't be CI-verified); the automated test instead confirms the
**preconditions** this step relies on (the anchors are queryable, the skill is materialized).

## 5. Inertness (what a non-research project sees)

```bash
# A research-free project (e.g. tiny-novel): build/query/validate behave exactly as in v0.1 —
# zero research entities, zero factual_anchor findings.
# Disabling research on this fixture has the same effect:
#   set [research].enabled = false in manifest.toml → factual_anchor produces no findings.
```

## Running the regression

```bash
uv run pytest tests/e2e/test_research_workflow.py
uv run pytest                 # full suite, ≥80% coverage gate
uv run ruff check && uv run ruff format --check && uv run mypy --strict
uv run mkdocs build           # strict: true → zero warnings (the docs gate)
```
