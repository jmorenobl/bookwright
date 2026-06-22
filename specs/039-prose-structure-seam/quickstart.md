# Quickstart / Validation Guide: prose/structure seam

How to prove iteration 039 works end to end. See `contracts/prose-seam.md` for the
exact behaviour tables and `data-model.md` for the types.

## Prerequisites

```bash
uv sync
```

## 1. The seam splits and normalizes (unit level)

```bash
uv run pytest tests/io/test_prose.py
```

Expected — covers the `contracts/prose-seam.md` tables:

- `prose_view("# Capítulo 1")[0]` → `number=1`, `raw="# Capítulo 1"`,
  `normalized="Capítulo 1"` (C2).
- `prose_view("> - text")[0].normalized == "text"` — iterative strip (C2, D2).
- `prose_view("   # text")[0].normalized == "   # text"` — heading strict at col 0
  (asymmetry, C2).
- `prose_view("   - text")[0].normalized == "text"` — indented bullet stripped.
- `prose_view("*Pedro*")[0].normalized == "*Pedro*"` — emphasis never stripped (C2.2).
- `prose_view("")` → `()`; multi-line text preserves 1-based `number` (C1).
- `is_placeholder("[PENDING: x]")` is `True`; `is_placeholder("x [PENDING: y]")` is
  `False` (C3).

## 2. Zero regression across the existing suite (SC-001 / US1)

```bash
uv run pytest
```

Expected: the **entire** existing suite passes with **zero** oracle edits — every
current validator test and E2E oracle (`tiny-historical`, `tiny-quest`, etc.) stays
green. If any live fixture's findings move, stop and inspect the fixture (D10) —
never loosen the seam to make a test pass.

Spot checks (US1 acceptance scenarios), all unchanged from today:

- `# Capítulo 1` → `Capítulo` **not** flagged (heading first word line-initial).
- `# La caída de Elena` (off-roster `Elena`) → the unknown-proper-noun warning for
  `Elena` **still fires** (only the marker is stripped, not the title's prose).
- `- **Voz narrativa**: tercera persona, limitada` → parses identically to the bare
  `Voz narrativa: …` form.
- A narrative-voice body that is solely `[PENDING: …]` → treated as no declaration
  (zero findings).

## 3. A new Markdown surface, no validator touched (SC-003 / US2 / FR-011)

```bash
uv run pytest tests/validation/test_character_presence.py -k blockquote
```

Expected: with a manuscript blockquote line `> Quevedo lo dijo` (`Quevedo`
off-roster):

- At the seam: `prose_view("> Quevedo lo dijo")[0].normalized == "Quevedo lo dijo"`.
- At the validator: `Quevedo` is **not** flagged — line-initial after stripping
  (over the raw `> Quevedo …` it would be non-initial → flagged). The delta proves
  the seam stripped `> ` — with **no `>`-specific code** in any validator (D9).

## 4. Locators unchanged (SC-004 / US3)

Findings emitted over the normalized view carry the same `relpath:line` as today —
the line number is `ProseLine.number` (1-based source position), never a match
offset within the normalized text.

## 5. The strippers are gone (SC-002)

```bash
grep -nE "_HEADING_MARKER|_BULLET|_LEAD_EMPHASIS|_CLOSE_EMPHASIS|_normalize_declaration_line|_PENDING_ONLY|splitlines" \
  src/bookwright/validation/validators/character_presence.py \
  src/bookwright/validation/validators/focalization.py \
  src/bookwright/validation/validators/setting_continuity.py
```

Expected: **no matches** — every local stripper is deleted and no validator calls
`splitlines()` (line splitting is single-sourced in `io/prose.py`).

## 6. The four gates (SC-005 / SC-006)

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest          # ≥ 80% coverage enforced
```

Expected: all green; dependency set byte-identical (no new runtime dep); every
changed/new file ≤ 500 lines.
