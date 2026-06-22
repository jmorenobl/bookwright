# Contract — leading dialogue-dash normalization (`io/prose.py`)

The seam's public surface (`prose_view`, `ProseLine`, `is_placeholder`) is **unchanged**.
This contract extends the C2 normalization table from iteration 039 with the new
leading dialogue marker. Each row is asserted as a `ProseLine(number=1, raw=…,
normalized=…)` over a one-line input, exactly like the existing C2 table in
`tests/io/test_prose.py`.

## C2-D — leading dialogue dash stripping

| # | `raw` (input line) | `normalized` (expected) | Why |
|---|---|---|---|
| D1 | `—Esto es el porvenir` | `Esto es el porvenir` | em dash glued to the word (`\s*` trailing) — the canonical Spanish form. |
| D2 | `— Claro` | `Claro` | em dash + space → same result as glued. |
| D3 | `–Esto` | `Esto` | en dash (U+2013) recognized identically to the em dash (FR-005). |
| D4 | `  —Esto` | `Esto` | leading whitespace tolerated (`^\s*`), mirrors the bullet marker. |
| D5 | `—dijo Arnela—, y se fue` | `dijo Arnela—, y se fue` | only the **leading** dash is stripped; the internal incise dash stays (FR-003). |
| D6 | `—` | `` (empty) | dash-only line → empty; yields no candidates, no finding/error. |
| D7 | `> —Esto` | `Esto` | composes with the blockquote marker across two passes (FR / "interaction"). |
| D8 | `Pregúntale a Quirón —dijo.` | `Pregúntale a Quirón —dijo.` | no **leading** dash → line unchanged; mid-line dashes are content. |
| D9 | `- Pedro` | `Pedro` | ASCII hyphen bullet stays owned by `_BULLET_MARKER` (unchanged, FR-005) — NOT the new dialogue marker. |

D9 is a **non-regression** anchor: the existing bullet behavior must not change. (It is
already covered by the iteration-039 C2 table; restated here to make the boundary
explicit.)

## Invariants reasserted (already-passing rows, must stay green)

- `prose_view("") == ()` (C1.2) and a blank line normalizes to `""` (FR-010).
- `is_placeholder(...)` unchanged (FR-010).
- `number` is the 1-based source index, never a match offset (C1.4 / FR-007).
- inline emphasis (`*highlight*`, `__init__`) is never a prefix and is left intact (C2.2).

## `character_presence` generalization (both directions, FR-009 / SC-001/SC-002)

Asserted in `tests/validation/test_character_presence.py` (validator-level, NOT a seam
edit), mirroring the existing blockquote/heading tests:

| Scenario | Roster | Manuscript line | Expectation |
|---|---|---|---|
| Leading demonstrative after dash | (no `Esto`) | `—Esto es el porvenir` | **no** finding mentioning `Esto` (leading dash stripped → line-initial → exempt). |
| Mid-line off-roster name in dialogue | (no `Quirón`) | `—Pregúntale a Quirón —dijo.` | finding for `Quirón` fires exactly once; the opening word is not flagged (only the leading dash neutralized). |

## CI / envelope contract (unchanged)

- The `--json` validation envelope shape is unchanged; only `error`-severity findings
  gate CI. This change removes one `warning`, never adds or removes an `error`.
- Prose validators keep `triples=()`; the frozen ontology is untouched (FR-012).
