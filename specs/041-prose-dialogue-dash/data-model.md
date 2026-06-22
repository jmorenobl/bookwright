# Phase 1 Data Model — leading dialogue marker in the prose seam

This iteration adds **no** new type and changes **no** field. It extends the set of
*structural leading markers* the seam's `normalized` projection removes. The model
below restates the affected entities and the invariants the change must preserve.

## Entities

### `ProseLine` (unchanged shape)

| Field | Type | Meaning |
|---|---|---|
| `number` | `int` | 1-based source line index, from `enumerate` — **never** a regex match offset (locator stability, FR-007). |
| `raw` | `str` | the exact `splitlines()` element, byte-for-byte. |
| `normalized` | `str` | `raw` with leading structural block/dialogue marker(s) iteratively stripped. |

Only the **derivation of `normalized`** changes: it now also removes a leading dialogue
dash. `number` and `raw` are untouched, so every reported `relpath:line` locator is
identical (FR-007).

### Structural leading markers (the set `_normalize` strips)

| Marker | Pattern | Trailing ws | Notes |
|---|---|---|---|
| ATX heading | `^#{1,6}\s+` | required | strict column 0 (no leading ws). Unchanged. |
| Bullet / blockquote | `^\s*[-*+>]\s+` | required (`\s+`) | tolerant of leading ws. Unchanged. The `\s+` disambiguates a bullet from inline emphasis. |
| **Dialogue dash (NEW)** | `^\s*[—–]\s*` | **optional** (`\s*`) | em `—` (U+2014) / en `–` (U+2013); tolerant of leading ws; trailing optional because Spanish glues the dash to the word (`—Esto`). Leading typographic dash is unambiguous → no `\s+` guard needed. |

Only the **leading** occurrence is a marker; any dash later in the line is content
(FR-003) — guaranteed by the `^` anchor and `sub(count=1)`.

## State / behavior — `_normalize` loop

The loop is unchanged in structure; one branch is added (order: heading → bullet →
dialogue; mutually exclusive at the leading position since first chars differ):

```text
loop:
  if heading matches      → strip one heading (count=1)
  elif bullet matches     → strip one bullet  (count=1)
  elif dialogue matches   → strip one dialogue dash (count=1)   # NEW
  else                    → return line
```

### Invariants the change must hold

- **I1 — termination**: every stripping pass deletes ≥ 1 character (the dash, and any
  whitespace it spans), so the loop still terminates (contract C2.1). A dash-only line
  `—` strips to `""` and the next pass returns `""`.
- **I2 — leading-only**: `^` + `sub(count=1)` removes exactly the leading dash;
  internal incise dashes (`—dijo Arnela—`) remain in `normalized` (FR-003).
  Concretely `—dijo Arnela—, y se fue` → `dijo Arnela—, y se fue`.
- **I3 — composition**: the dialogue strip composes with the existing markers — a
  blockquoted line of dialogue `> —Esto` reduces across two passes (`> ` then `—`) to
  `Esto` (FR / edge case "interaction with other markers").
- **I4 — offset-0 result**: after normalization the first content word of a dialogue
  line is at offset 0, so `character_presence._is_sentence_initial(scan, match.start())`
  sees an empty prefix and exempts it — the **existing** code path, no validator edit
  (FR-002, the DEBT-008 mechanism).
- **I5 — empty/idempotent**: `prose_view("") == ()` and `is_placeholder(...)` are
  byte-identical; lines with no leading marker are returned unchanged (FR-010).

## Downstream consumers (read-only, unchanged code)

- `character_presence._unknown_mentions` scans `line.normalized`; with the dash gone,
  the opening demonstrative is line-initial and exempt, while a mid-line off-roster name
  (`Quirón` in `—Pregúntale a Quirón —dijo.`) is still analyzed and flagged (FR-004).
- `focalization`, `setting_continuity` consume the same seam and benefit automatically;
  none is edited (SC-004).
- The frozen GOLEM ontology is untouched; prose validators keep `triples=()` (FR-012).
