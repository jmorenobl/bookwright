# Contract — `graph build` envelope: `untyped_vocab_terms`

Additive change to the `bookwright graph build --json` success envelope and to the
human build report. Sibling of `unknown_keys` / `unresolved_references` /
`research_warnings`. **Soft channel — never affects the exit code.**

## Machine-readable envelope (`--json`, stdout)

`BuildReport.to_json()` gains one key. Everything else is byte-stable.

```jsonc
{
  "status": "ok",
  "files_processed": 5,
  "entities": 12,
  "triples": 87,
  "skipped": [],
  "unknown_keys": [],
  "unresolved_references": [],
  "untyped_vocab_terms": [
    {
      "path": "outline/units/04-struggle.md",
      "field": "functions",
      "term": "intimidacion",
      "vocabulary": "propp"
    }
  ],
  "sources": 0,
  "findings": 0,
  "anchors": 0,
  "research_warnings": [],
  "graph_path": "bible/graph.ttl"
}
```

### Record schema — `untyped_vocab_terms[]`

| Key | Type | Notes |
|---|---|---|
| `path` | string | project-relative source file |
| `field` | string | `"functions"` (Propp) \| `"narrative_roles"` (Greimas) |
| `term` | string | offending term **as authored** |
| `vocabulary` | string | `"propp"` \| `"greimas"` |

**The valid-term enumeration is NOT in the record** (FR-002) — a consumer that wants
it derives it from `vocabulary` (the bundled vocabulary is the source of truth),
exactly as a consumer derives "not in bible" for `research_warnings`.

### Invariants

| ID | Invariant |
|---|---|
| C-1 | The key is **always present** (empty list when no vocabulary is active or every term typed). |
| C-2 | Adding/removing entries **never** changes `exit_code` — only `skipped` does (FR-004, SC-004). |
| C-3 | The minted graph is **identical** with or without this channel — no triple added/removed; an unrecognized term is still an untyped node (FR-003, SC-003). |
| C-4 | A **valid** term produces **no** entry and is still typed (FR-010, SC-006). |
| C-5 | With **no** active vocabulary the list is empty and the whole envelope is byte-identical to pre-feature output (FR-009, SC-005). |
| C-6 | Two builds of the same project ⇒ **byte-identical** `untyped_vocab_terms` — entry order (sorted-glob, bible-pass-then-outline-pass; authored list order within a card) and, in the render, enumeration order are stable (FR-016, SC-008). |

## Human-readable report (stderr)

When `untyped_vocab_terms` is non-empty, `_print_summary` appends, in the existing
per-channel style:

```text
1 unrecognized vocabulary term(s):
  - outline/units/04-struggle.md: functions 'intimidacion' is not a propp term
  valid propp terms: absentation, complicity, ... , wedding
```

- One `  - {path}: {field} '{term}' is not a {vocabulary} term` line per entry, in
  envelope order.
- One `  valid {vocabulary} terms: …` line **per distinct vocabulary** present
  (not per entry), enumerating `load_vocabulary(vocabulary).terms` (sorted, unique
  `rdfs:label`s). Stays on stderr; does not enter the `--json` envelope.

## Out of scope (unchanged contracts)

- Exit code / gating — a skip still exits 4; an unrecognized term never gates
  (FR-004).
- Validation layer — no validator, finding, or `Severity` value added (FR-005,
  FR-011).
- `propp.ttl` / `greimas.ttl` / `golem.ttl` — frozen, untouched (FR-014).
