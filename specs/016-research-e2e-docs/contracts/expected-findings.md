# Contract — `expected-findings.md` (the co-located oracle)

Location: `tests/fixtures/tiny-historical/expected-findings.md` — fixture **root**, NOT under
`bible/research/` (the strict reader globs `bible/research/*.md`; this file must not be parsed
as a topic).

Plain-text Markdown with YAML front-matter. The E2E test loads the front-matter as the single
source of truth for its `factual_anchor` assertions (counts + which anchors); the docs and the
manual verify step quote the body. Presence is itself checked (FR-012).

## Front-matter schema

```yaml
---
# What the DETERMINISTIC validator (factual_anchor) must report on this fixture.
factual_anchor:
  expected_counts:                 # exact counts from `validate --json`, scoped to factual_anchor
    error: 1
    warning: 1
  warning_anchor: <id>             # the under-reliable anchor (defect #1) — its promoted finding id or anchor slug
  error_anchor:   <id>            # the time-span-anachronistic anchor (defect #2)

# What the MANUAL verify step (bookwright-verify LLM skill) should flag.
verify:
  manuscript_file: manuscript/NN-<slug>.md
  contradicted_anchor: <id>        # the dated finding/anchor the prose contradicts
  prose_anachronism: >-
    <one-sentence description of the planted prose contradiction>
---
```

## Body

Spanish prose that, for a human reader, states the deterministic expected findings:

1. which anchor `factual_anchor` warns on and why (under-reliable: only a `baja` source under
   the `media` floor);
2. which anchor it errors on and why (year-span disjoint from the dated event it constrains);
3. which manuscript passage `bookwright-verify` should flag and which anchor it contradicts.

This body **is** the "documented expected findings" FR-012 requires. It explicitly notes that
no verbatim LLM report is committed (it would rot and cannot be CI-verified) and that the
automated test asserts the *preconditions* of the verify step, not the LLM's output.

## Consumed by

- `tests/e2e/test_research_workflow.py` — reads `factual_anchor.expected_counts` and the two
  anchor identifiers; presence-checks the file.
- `docs/research.md` — links to / quotes the body as the worked-example expected findings.
