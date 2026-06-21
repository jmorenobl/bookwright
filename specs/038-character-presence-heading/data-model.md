# Phase 1 Data Model: `character_presence` heading-marker normalization

This is a prose-level validator change. It introduces **no** GOLEM entity, no RDF
triple, and no persisted data (FR-009 / Principle X — the frozen ontology is
untouched, every emitted `Violation` keeps `triples=()`). The "entities" below are
in-memory analysis constructs only.

## Analysis constructs (in-memory, transient)

### Manuscript line

- A single line of manuscript text, produced by `text.splitlines()` and paired with
  its 1-based `lineno` (from `enumerate(..., start=1)`).
- **State distinction introduced by this change**: a line is either
  - an **ATX heading line** — matches `_HEADING_MARKER` (`^#{1,6}\s+`): its
    structural marker is removed to form the `scan` string before analysis; or
  - an **ordinary line** — no match: `scan` is the line unchanged (today's behavior).
- The `lineno` is **invariant** across this distinction — it is never derived from a
  match offset, so the reported `relpath:line` locator is identical whether or not a
  marker was stripped (FR-005).

### Scan string

- The string actually fed to `_CANDIDATE.finditer` and `_is_sentence_initial`:
  the manuscript line with any leading ATX marker removed.
- **Invariant**: matching and the sentence-initial check read the *same* `scan`
  string, so a candidate's `match.start()` is consistent with the prefix
  `_is_sentence_initial` inspects. For a stripped heading, the first content word
  has `start == 0` → empty prefix → exempt (reuses the existing rule, D1).

### Proper-noun candidate (unchanged definition)

- A capitalized token of ≥3 letters (`_CANDIDATE`), accent-aware.
- Validation/decision rules (all pre-existing; **none changed** by this iteration):
  exempt if its slug is in the roster slugs, already seen, in the pinned
  `_STOP_WORDS`, **or** `_is_sentence_initial(scan, start)` is true. The only new
  effect is that, on a heading line, the first content word's `start` is now `0`
  (marker removed) and so satisfies the existing sentence-initial branch.

## Validation rules touched / untouched

| Rule | Direction | Severity | Changed? |
|---|---|---|---|
| Unknown proper-noun mention, deduped per name | manuscript → roster | `warning` | **Only** the line-normalization seam: heading marker stripped before the heuristic. Detection logic, dedup, message, severity all byte-identical. |
| Orphan: bible character never mentioned | roster → manuscript | `error` | Untouched (FR-004). |
| Pinned stop-set `_STOP_WORDS` | — | — | Untouched (FR-003/FR-004). |
| `_CANDIDATE` regex, `_MIN_TOKEN_LEN` | — | — | Untouched. |

## No persistence / no graph

- No `golem/` model, `CLASS_IRI` entry, or `.ttl` change (FR-009).
- The `Violation` record shape (`validator`, `severity`, `message`, `source`,
  `triples=()`) is unchanged, so the `--json` validate envelope is byte-stable
  (Principle IX).
