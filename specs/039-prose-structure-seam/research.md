# Phase 0 Research: prose/structure seam

All "NEEDS CLARIFICATION" were resolved in the spec's Clarifications session
(2026-06-22). This file records the design decisions that fix the implementation.

## D1 — Seam shape: classified lines, no `kind` attribute

- **Decision**: The seam exposes `ProseLine` (a frozen dataclass: `number: int`,
  `raw: str`, `normalized: str`) and a `prose_view(text) -> tuple[ProseLine, ...]`
  function. No `kind`/`block-type` field is published.
- **Rationale**: FR-002 forbids a consumed "kind" field — no validator branches on
  a line's kind, so exposing one is unused plumbing (Scope & Release Discipline).
  Prefix recognition is an *internal* step of computing `normalized`. A plain tuple
  of `ProseLine` is "the ordered sequence of classified lines" the spec's Key
  Entities describe; the view needs no methods.
- **Alternatives rejected**: (a) an enum `kind` per line + a `LineKind` taxonomy —
  rejected as speculative generality (no consumer). (b) a third-party Markdown AST
  (`markdown-it-py`, `mistune`) — rejected by FR-012 / Constitution II (new dep,
  over-models the problem). (c) a class wrapping the tuple with helper methods —
  rejected; the placeholder predicate is a sibling string helper, not a view method
  (Key Entities).

## D2 — Iterative block-prefix stripping, asymmetric anchors

- **Decision**: `normalize` strips one leading block prefix per pass, left-to-right,
  repeating until no prefix matches. Each pass does a single `count=1`
  `re.sub`: try the **heading** recognizer `^#{1,6}\s+` (strict column 0) first,
  else the **bullet/blockquote** recognizer `^\s*[-*+>]\s+` (tolerates leading
  whitespace). Loop ends when neither matches. So `> - text` → `text`; `# text` →
  `text`; `   # text` → unchanged (heading not at column 0); `   - text` → `text`
  (indented bullet stripped, mirroring today's `_BULLET`).
- **Rationale**: Clarifications 2026-06-22 — only iterative stripping closes the
  class for nested surfaces (`> - text`); it preserves live-fixture parity because
  today's strippers only ever met **single** prefixes, so the loop runs exactly one
  pass on every existing input (FR-003/FR-004). The asymmetry is kept *exactly*:
  the heading recognizer mirrors `character_presence._HEADING_MARKER`
  (`r"^#{1,6}\s+"`), the bullet recognizer mirrors `focalization._BULLET`
  (`r"^\s*[-*+>]\s+"`). Unifying the anchors would start heading-stripping indented
  `   # text` lines — a "fix" the Assumptions forbid (shifts `character_presence`'s
  view).
- **Termination**: each pass that strips removes ≥ 1 leading character; a pass that
  matches neither recognizer exits. Inline emphasis (`**`/`*`/`_`) is never a block
  prefix (the recognizers require `[-*+>]` or `#` + **whitespace**), so it never
  triggers a pass — `*Voz*` and `**bold**` normalize to themselves.
- **Alternatives rejected**: single-pass strip (fails `> - text`); a unified anchor
  (breaks parity per above); stripping inline emphasis in the seam (would couple
  `io/` to styling and is unnecessary — emphasis handling moves into
  `focalization`'s recognizer, D4).

## D3 — Bullet vs. emphasis-run disambiguation

- **Decision**: The bullet recognizer requires trailing whitespace (`\s+` after
  `[-*+>]`). So `* Pedro` (bullet + space) is stripped; `*Pedro*` (emphasis, no
  following space) is left untouched.
- **Rationale**: This is exactly today's `_BULLET` rule (`^\s*[-*+>]\s+`). Edge
  Cases require `*Pedro*` to normalize to itself so a manuscript off-roster name in
  it behaves as today (not made line-initial-exempt). Byte-for-byte parity (FR-004).

## D4 — Emphasis around the narrative-voice label folds into `focalization`

- **Decision**: The seam strips only the leading block bullet of
  `- **Voz narrativa**: …`, yielding `**Voz narrativa**: …`. `focalization`'s
  declaration recognizer is widened to tolerate optional emphasis around the label:
  `(?i)^\s*(?:\*\*|\*|_)*\s*(?:voz narrativa|narrative voice)(?:\*\*|\*|_)*\s*:\s*(?P<body>.+)$`.
  `_LEAD_EMPHASIS`, `_CLOSE_EMPHASIS`, and `_normalize_declaration_line` are
  **deleted** (their effect lives in the one pattern, not relocated).
- **Rationale**: FR-008(a) and the spec's Overview/Assumptions — emphasis is a
  validator-domain concern (it is adjacent to *this validator's* label), so pushing
  it into the shared seam would couple `io/` to `focalization`'s vocabulary
  (forbidden, FR-003). The widened pattern's `(?:…)*` (zero-or-more) subsumes both
  the present-emphasis and bare forms, so the parsed `_Declaration` is byte-identical
  to today on every input. The `(?P<body>.+)$` group is unchanged, so the body — and
  thus the parsed person/limited/focal — never shifts.
- **Verification of parity**: `**` is matched before `*` inside the alternation so
  the longest emphasis run is consumed; the label has no asterisks, so the greedy
  `(?:…)*` cannot over-consume into the label or body.

## D5 — Placeholder predicate as a seam sibling helper

- **Decision**: The seam exposes `is_placeholder(body: str) -> bool`, equivalent to
  `focalization._PENDING_ONLY` (`r"(?i)^\s*\[pending\b[^\]]*\]\s*$"`). It is a
  module-level string predicate, **not** a property of `ProseView`. `focalization`
  consults it on the declaration **body**; its local `_PENDING_ONLY` is deleted.
- **Rationale**: FR-005 — it operates on a declaration body string, not a line kind.
  The full `^…$` anchor keeps a body with real text before/after the token a real
  declaration (Edge Cases / contract C-PLH). Living in `io/prose.py` next to the
  view keeps "see past the scaffold's markdown" knowledge single-sourced, while
  staying domain-agnostic (it knows `[PENDING]`, a scaffold token, not narrative
  vocabulary).

## D6 — `ValidationContext` accessors mirror the existing memo pattern

- **Decision**: Add `manuscript_view() -> tuple[tuple[str, tuple[ProseLine, ...]], ...]`
  (sorted `(relpath, view)`, built from the already-cached `manuscript_files()`) and
  `constitution_view() -> tuple[ProseLine, ...]` (built from `constitution_text()`;
  empty tuple when the constitution is absent/`None`). Both memoize via the
  `_UNSET`/field pattern (`_manuscript_view`, `_constitution_view`).
- **Rationale**: FR-006 — each source split once per run, shared across validators.
  Building from the existing accessors means **no second disk read** and single-
  sources line splitting. Empty view on absent source preserves today's empty-input
  behaviour (Edge Cases; tri-valued "not evaluated" is iteration 040's concern).
- **Whole-file checks stay on the text accessors**: `character_presence._orphans`/
  `_is_mentioned` and `setting_continuity`'s `name_re.search(text)` keep reading the
  full text from `manuscript_files()`; only the **per-line** scans move to the view.
  A validator therefore uses *both* accessors — both cached, the file read once
  (FR-009 explicitly keeps the whole-file presence check over full text).

## D7 — Per-validator rewrite mapping (what each validator reads)

| Validator | Per-line field read | Strippers deleted | Still uses `manuscript_files()`? |
|-----------|--------------------|--------------------|----------------------------------|
| `character_presence` | `normalized` (proper-noun scan) | `_HEADING_MARKER` | yes — orphan / `_is_mentioned` over full text |
| `focalization` | `normalized` (declaration) + `raw` (dialogue/first-person/head-hopping) | `_BULLET`, `_LEAD_EMPHASIS`, `_CLOSE_EMPHASIS`, `_normalize_declaration_line`, `_PENDING_ONLY` | yes — manuscript scans iterate `manuscript_view()` reading `.raw`; declaration over `constitution_view()` |
| `setting_continuity` | `raw` (per-line term scan) | none (was raw `splitlines()`) | yes — `name_re.search(text)` whole-file gate |

- **Rationale**: FR-007/008/009. The proper-noun scan must see past the marker
  (normalized); the dialogue-sensitive scans must see the raw line so the dialogue
  prefix exemption (`—`/`-`/`>`/quotes) is byte-for-byte unchanged (Edge Case "a
  leading block marker on a dialogue line"). `setting_continuity`'s `\bterm\b`
  matching is inert to block-prefix stripping, so reading `.raw` keeps findings and
  line numbers identical (FR-009).

## D8 — Locators unchanged

- **Decision**: `ProseLine.number` is the 1-based source position from
  `enumerate(text.splitlines(), start=1)` inside `prose_view`. Validators build
  `f"{relpath}:{line.number}"` — never from a regex match offset within `normalized`.
- **Rationale**: FR-010 / SC-004 / US3. Today every validator already takes `lineno`
  from `enumerate`, not from the match offset, so this is preserved verbatim.

## D9 — Generalization fixture (US2 / FR-011): blockquote surface

- **Decision**: Demonstrate class-closure with a manuscript blockquote line whose
  off-roster proper noun is **line-initial after stripping** — e.g. `> Quevedo lo
  dijo` (`Quevedo` off the roster). The seam normalizes it to `Quevedo lo dijo`, so
  `Quevedo` lands at offset 0 and inherits the existing line-initial exemption →
  **not** flagged; over the *raw* line `> Quevedo …` the prefix `>` would make it
  non-initial → flagged. The observable delta (a flag that disappears) proves the
  seam stripped the marker — with **no `>`-specific code** in any validator.
- **Rationale**: US2 AS1 frames the proof as "its first-word/line-initial exemption
  applying exactly as for any other line". Placing the off-roster name line-initial
  makes that exemption the observable signal. (Were the name placed mid-quote —
  `> Una cita de Quevedo` — the stripping's delta lands on the *first* word `Una`
  and the mid-line name still fires; that also proves the strip but less directly,
  so we adopt the line-initial framing of AS1.) The test also asserts at the seam
  level that `prose_view("> Quevedo lo dijo")[0].normalized == "Quevedo lo dijo"`.
- **No new recognizer**: a `> blockquote` is already a bullet/blockquote prefix
  (`[-*+>]`), so the generalization needs **no** code beyond what FR-003 already
  specifies — which is exactly why it proves a *class* closed, not a fourth patch
  (Assumptions).

## D10 — Parity risk surfaced for the byte-for-byte gate

- **Observation**: `character_presence` today strips only headings; under the seam
  it also reads past **bullets/blockquotes** (normalized). If a *live* manuscript
  fixture contained a bullet/blockquote line carrying an off-roster proper noun
  whose finding would flip, SC-001 (zero oracle edits) would fail.
- **Decision**: This is the intended new capability (US2), not a regression — but
  the implementation MUST verify it against the live fixtures. The implementation
  task runs the full suite with **no** oracle edits; if a live fixture's finding
  moves, that is a real signal to inspect (a pre-existing bullet-name the heading-
  only stripper happened to flag), resolved by examining the fixture, never by
  loosening the seam. The spec asserts no such fixture exists (SC-001); the gate
  confirms it empirically.
- **Rationale**: FR-004 parity is judged against the live fixtures' normalized
  output; D2's "exactly one pass on existing inputs" plus this empirical gate close
  the loop.
