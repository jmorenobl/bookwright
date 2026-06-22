# Feature Specification: Single prose/structure seam for prose validators

**Feature Branch**: `039-prose-structure-seam`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Los validadores de prosa de Bookwright acoplan a la SUPERFICIE markdown del manuscrito y la constitución, no a su estructura ya parseada, y cada uno reimplementa por su cuenta cómo «ver más allá» del markdown que el propio andamiaje emite. Esta iteración cierra la clase (issue #1): una COSTURA de prosa/estructura única que todos los validadores de prosa consumen."

## Overview

Three prose validators — `character_presence`, `focalization`, and
`setting_continuity` — each re-implement, locally and independently, how to "see
past" the Markdown that Bookwright's own scaffolding emits. `character_presence`
strips a leading ATX heading marker before its proper-noun heuristic (DEBT-008);
`focalization` strips bullet + emphasis around the "Voz narrativa" label and
recognizes the `[PENDING: …]` placeholder (DEBT-004/007); `setting_continuity`
re-scans raw `splitlines()`. These were patched one instance at a time: the same
**class** of defect, fixed three times. The next new Markdown surface an author
uses (an epigraph, a `> blockquote`) reopens the crack in whichever validator
meets it first.

This feature closes the class at the root. It introduces **one** shared,
Markdown-aware prose/structure seam in `io/` that every prose validator consumes
instead of re-scanning raw text. The seam splits a Markdown source into lines
once and, for each line, recognizes its leading **structural block prefix** (ATX
heading marker, blockquote/bullet marker) and exposes a *normalized view* (the
line's text with that prefix removed) alongside the original raw line and its
1-based source number. Each validator's heuristic runs against the field it needs:
the proper-noun scan against the normalized prose, the dialogue-sensitive scans
against the raw line (so dialogue exemption is byte-for-byte unchanged). The three
validators are rewritten on top of the seam and their local strippers are deleted;
no validator calls `splitlines()` itself any longer. The decisive proof that this
closes a class and not an instance: a brand new Markdown surface (an off-roster
character mention inside a `> blockquote`) is handled correctly **without touching
any validator**.

The seam stays generic — it knows only about block-level Markdown prefixes, never
about any validator's domain vocabulary. The label-adjacent emphasis the current
`focalization` strippers handle (`**Voz narrativa**:`) is not pushed into the
shared seam (that would couple `io/` to one validator's label); instead it is
dissolved into `focalization`'s own declaration recognizer, which is widened to
tolerate optional emphasis around the label — eliminating the `_LEAD_EMPHASIS` /
`_CLOSE_EMPHASIS` / `_normalize_declaration_line` constructs outright rather than
relocating them.

This is iteration 039, the first of two in the `v0.5.0` "validation robustness"
milestone (issue #1, facet A — surface coupling). Facet B — the tri-valued
validator result so an empty finding list stops reading as "clean" when it meant
"couldn't look" — is the separate, dependent iteration 040 and is explicitly out
of scope here.

## Clarifications

### Session 2026-06-22

- Q: Does the seam's normalized form strip a single leading block prefix or
  iterate through nested prefixes (e.g. `> - text`)? → A: **Iterate** — strip one
  leading block prefix at a time, left-to-right, repeating until the line carries
  no leading block prefix; each strip is a single (`count=1`) removal of a heading
  marker or a bullet/blockquote marker, and inline emphasis is never a block prefix
  so it never triggers a pass. *(Rationale: only iterative stripping closes the
  class for the nested surfaces the spec's own edge cases name (`> - text`); it
  preserves live-fixture parity because today's strippers only ever met single
  prefixes, so the loop runs exactly one pass on every existing input.)*
- Q: Do the heading and bullet/blockquote recognizers share one anchor, or keep
  the asymmetry of the two strippers they subsume? → A: **Keep the asymmetry
  exactly** — the heading recognizer is anchored strictly at column 0
  (`^#{1,6}\s+`, no leading whitespace, mirroring `character_presence._HEADING_MARKER`);
  the bullet/blockquote recognizer tolerates leading whitespace (`^\s*[-*+>]\s+`,
  mirroring `focalization._BULLET`). *(Rationale: FR-004 byte-for-byte parity
  requires each recognizer to anchor exactly where its predecessor did; unifying
  the anchors would be a "fix" the Assumptions forbid and would start
  heading-stripping indented `   # text` lines, shifting `character_presence`'s
  view.)*

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Zero regression across the existing validator suite (Priority: P1)

An author who runs `bookwright validate` on a project that today produces a
known set of findings must get **byte-for-byte the same findings** after this
refactor. The normalized view must reproduce exactly what each local stripper
produces today, so no existing behaviour shifts: a `# Capítulo 1` heading's first
word stays exempt from the proper-noun heuristic; an off-roster `Elena` in
`# La caída de Elena` still fires; the `- **Voz narrativa**: …` declaration still
parses; a body that is solely `[PENDING: …]` is still treated as no declaration.

**Why this priority**: The whole milestone's premise is that this is a structural
refactor, not a behaviour change. If any live fixture's findings move, the
refactor has failed its core contract. This is the gate everything else rests on.

**Independent Test**: Run the full existing test suite (every current validator
test and E2E oracle) with **no oracle edits**; it stays green.

**Acceptance Scenarios**:

1. **Given** the current validator test suite and E2E fixtures, **When** the
   three validators are rewritten on the shared seam, **Then** every existing
   test passes unchanged and no fixture oracle is edited.
2. **Given** a manuscript line `# Capítulo 1`, **When** `character_presence`
   runs, **Then** `Capítulo` is **not** flagged as an unknown proper noun (the
   heading's first content word is treated as line-initial).
3. **Given** a manuscript heading `# La caída de Elena` with `Elena` off the
   bible roster, **When** `character_presence` runs, **Then** the unknown
   proper-noun warning for `Elena` fires (only the marker is stripped, not the
   title's prose).
4. **Given** a constitution line `- **Voz narrativa**: tercera persona,
   limitada`, **When** `focalization` runs, **Then** the declaration parses
   identically to the bare `Voz narrativa: tercera persona, limitada` form.
5. **Given** a narrative-voice body that is solely `[PENDING: …]`, **When**
   `focalization` runs, **Then** it is treated as no declaration (zero findings),
   exactly as today.

---

### User Story 2 - A new Markdown surface is handled without touching a validator (Priority: P1)

An author quotes an off-roster character name inside a `> blockquote` (or an
epigraph) in the manuscript — a Markdown surface no validator special-cases
today. Because every prose validator now reads the shared normalized view, the
blockquote marker is stripped by the seam and the validator's heuristic sees the
quoted prose correctly, with **no change to any validator's code**.

**Why this priority**: This is the feature's reason to exist. It is the
observable proof that the seam closes the *class* of defect (surface coupling)
rather than adding a fourth instance-specific patch. Without this demonstration,
the work is indistinguishable from another whack-a-mole fix.

**Independent Test**: Add a fixture exercising the next surface (a `> blockquote`
or epigraph carrying an off-roster mention) and assert the seam handles it
correctly, with the validator source untouched by the fixture.

**Acceptance Scenarios**:

1. **Given** a manuscript line `> Una cita de Quevedo` where `Quevedo` is off the
   bible roster, **When** `character_presence` runs over the normalized view,
   **Then** the blockquote marker is stripped and `Quevedo` is evaluated as prose
   (its first-word/line-initial exemption applying exactly as for any other
   line), with no `> `-specific code in the validator.
2. **Given** the new surface fixture, **When** the validators are inspected,
   **Then** none of the three contains markup-stripping logic specific to that
   surface — the seam alone classifies and normalizes it.

---

### User Story 3 - The author's source-line locators are unchanged (Priority: P2)

When a validator reports a finding, the `relpath:line` locator an author follows
to the offending line must be identical to today's. Stripping a prefix marker
must not shift the reported line number.

**Why this priority**: A wrong locator sends authors to the wrong line and erodes
trust in the tool; it is a silent regression the suite might not otherwise catch.
It is P2 because it is a property of the refactor rather than a new capability.

**Independent Test**: Assert that findings emitted over the normalized view carry
the same 1-based line numbers as the raw-text scan does today.

**Acceptance Scenarios**:

1. **Given** a finding on a normalized line, **When** the locator is built,
   **Then** the line number comes from the source line's 1-based position, not
   from the offset of any regex match within the stripped text.

---

### Edge Cases

- **Marker not at column 0**: An indented or otherwise non-line-initial marker
  (e.g. `   # text`, or `#text` with no following space, or seven-plus `#`) is
  **not** treated as an ATX heading — it keeps today's behaviour. The seam's
  recognizers stay anchored exactly where the deleted local strippers anchored
  them (no looser, no tighter), preserving byte-for-byte parity: the heading
  recognizer is strict at column 0 while the bullet/blockquote recognizer
  tolerates leading whitespace — the asymmetry is kept deliberately
  (Clarifications 2026-06-22). So `   # text` is not heading-stripped, but
  `   - text` (indented bullet) is, exactly as `_BULLET` does today.
- **Distinguishing a bullet from an emphasis run**: A line-leading `* ` (bullet
  + space) is a structural bullet the seam strips; a `*Voz*` emphasis run (no
  following space) is inline styling the seam leaves untouched. The seam must
  preserve today's distinction (the trailing-whitespace rule the local `_BULLET`
  stripper uses), so a `*Pedro*` line is normalized to itself and a manuscript
  off-roster name in it behaves exactly as today (not made line-initial-exempt).
- **Emphasis around the narrative-voice label**: The leading `**` and the `**`
  between label and colon in `- **Voz narrativa**:` are NOT the seam's concern.
  The seam strips only the leading `- ` block bullet, yielding
  `**Voz narrativa**: …`; `focalization`'s declaration recognizer then tolerates
  the optional emphasis around the label and extracts the same body as the bare
  `Voz narrativa: …` form. No emphasis-stripping construct survives in either the
  seam or the validator.
- **Multiple markers / mixed nesting**: A line like `> - text` (blockquote +
  bullet) is normalized by removing the leading block markers iteratively,
  left-to-right (pass 1 strips `> `, pass 2 strips `- `), until none remains —
  `> - text` → `text` (Clarifications 2026-06-22). No third-party Markdown parse.
  Inline emphasis is never stripped by the seam and never triggers a pass.
- **Shared seam widens recognition uniformly across validators**: because every
  prose validator now reads the *same* normalized view, a block prefix the old
  per-validator strippers did not handle is now stripped for *all* of them — e.g.
  `focalization` reads its declaration over `normalized`, so a heading- or
  nested-prefixed voice line (`# Voz narrativa: …`, `> - Voz narrativa: …`) parses
  as a declaration where its old single-bullet stripper would have missed it. This
  is the intended class-closure (one recognizer, no per-validator drift), not a
  regression: it is inert on every live fixture (none carry such a prefix on a
  declaration), so byte-for-byte suite parity (SC-001) holds.
- **A leading block marker on a dialogue line**: A dialogue line carrying a
  leading `- ` or `> ` is stripped in the *normalized* view but its *raw* form is
  retained; `focalization`'s dialogue / first-person / head-hopping scans read the
  raw line, so a `—`/`-`/`>`-prefixed line's dialogue exemption is byte-for-byte
  unchanged. Only the proper-noun scan (which reads the normalized view) sees the
  prefix removed.
- **A placeholder body with real text before or after it**: A body containing
  `[PENDING: …]` *plus* real declaration text remains a real declaration; only a
  body that is *solely* the placeholder is treated as none — the existing
  `^…$`-anchored rule is preserved.
- **Empty manuscript / empty constitution**: An empty or absent source yields an
  empty classified view; validators behave exactly as they do today on empty
  input. (Whether an empty result should read as "not evaluated" is iteration
  040's concern, not this one.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single shared prose/structure seam,
  living in `io/` alongside `frontmatter.py`, that splits a Markdown source
  (a manuscript file or the constitution) into an ordered sequence of
  **classified lines**.
- **FR-002**: Each classified line MUST carry (a) its 1-based source line number,
  preserved from the original text; (b) its **raw** form (the original line,
  unmodified); and (c) its **normalized** form (FR-003). It MUST NOT carry a
  consumed "kind" field: no validator branches on a line's kind, so exposing one
  would be unused plumbing — the recognition of a prefix is an internal step of
  producing the normalized form, not a published attribute.
- **FR-003**: The normalized form of a line MUST be the line with its leading
  **structural block prefix(es)** removed: a single ATX heading marker (`#{1,6}`
  followed by whitespace) or a single bullet/blockquote marker (`[-*+>]` followed
  by whitespace). Stripping MUST be **iterative** — one prefix removed per pass,
  left-to-right, repeated until the line carries no leading block prefix (so a
  nested `> - text` normalizes to `text`); each pass is a single (`count=1`)
  removal. The two recognizers MUST preserve, byte-for-byte, the anchors of the
  strippers they subsume: the heading marker is anchored strictly at column 0
  (`^#{1,6}\s+`, no leading whitespace), while the bullet/blockquote marker
  tolerates leading whitespace (`^\s*[-*+>]\s+`) — the asymmetry is kept, not
  normalized away (Clarifications 2026-06-22). The seam MUST NOT strip inline
  emphasis (`**`/`*`/`_`) — that is not a block prefix, and it never triggers a
  pass — and MUST NOT reference any validator's domain vocabulary.
- **FR-004**: On every input the live fixtures exercise, the seam's block-prefix
  stripping MUST reproduce, byte-for-byte, what `character_presence`'s
  `_HEADING_MARKER` and `focalization`'s `_BULLET` produce today, and the seam's
  line splitting MUST reproduce each validator's current `splitlines()` pass. No
  live fixture's findings may change.
- **FR-005**: The seam MUST expose a **placeholder predicate** over a string,
  equivalent to `focalization`'s current `_PENDING_ONLY` (true when the string is
  *solely* a `[PENDING: …]` token — case-insensitive keyword, optional
  surrounding whitespace, the `^…$`-anchored rule). It operates on a declaration
  *body* string, not on a line kind, and is consumed by `focalization`.
- **FR-006**: `ValidationContext` MUST gain cached accessor(s) returning the
  classified-line view for the manuscript and for the constitution, using the
  same `_UNSET`/memo pattern as `manuscript_files()` / `constitution_text()`, so
  each source is split once per run and shared across validators.
- **FR-007**: `character_presence` MUST be rewritten to run its proper-noun
  heuristic over each classified line's **normalized** form, iterating the seam's
  lines instead of its own `splitlines()`; its local `_HEADING_MARKER` stripper
  MUST be deleted.
- **FR-008**: `focalization` MUST be rewritten to (a) locate its narrative-voice
  declaration over the classified lines' **normalized** forms, with its
  declaration recognizer widened to tolerate optional emphasis around the label so
  that `_LEAD_EMPHASIS`, `_CLOSE_EMPHASIS`, and `_normalize_declaration_line` are
  **deleted** (their effect folded into the one declaration pattern, not
  relocated); (b) consult the seam's placeholder predicate, deleting its local
  `_PENDING_ONLY`; (c) run its dialogue / first-person / head-hopping scans over
  each classified line's **raw** form (preserving dialogue exemption byte-for-byte)
  while still iterating the seam's lines instead of its own `splitlines()`; and
  (d) delete its local `_BULLET`, now subsumed by the seam.
- **FR-009**: `setting_continuity` MUST be rewritten to iterate the seam's
  classified lines instead of its own `splitlines()` pass. Its whole-file
  setting-name presence check (`name_re.search(text)`) continues to operate over
  the file's full text; block-prefix stripping is inert for its `\bterm\b` lexicon
  matching, so its findings are unchanged.
- **FR-010**: Reported `relpath:line` locators MUST be unchanged — the line
  number MUST come from each classified line's 1-based source position, never
  from the offset of a regex match within the normalized text.
- **FR-011**: A new Markdown surface (an off-roster character mention inside a
  `> blockquote` or an epigraph) MUST be handled correctly by the seam **without
  any change to a validator's code**, demonstrating the seam closes the class.
- **FR-012**: The seam MUST NOT introduce any new dependency. It MUST be a
  deterministic line/block classifier built on the existing regex primitives, not
  a third-party Markdown parser or AST (Constitution II).
- **FR-013**: The three prose validators MUST remain graph-free and LLM-free,
  continue to emit `triples=()`, and leave the frozen ontology untouched
  (Principle X). Their severities and the CI gate (only `error` findings break
  CI) MUST NOT change.
- **FR-014**: Every changed or new source file MUST stay ≤ 500 lines
  (Principle IV).
- **FR-015**: The four CI gates (`ruff check`, `ruff format --check`,
  `mypy --strict`, `pytest` with ≥ 80% coverage) MUST be green.

### Out of Scope

- The tri-valued validator result (`evaluated` / `not-evaluated(reason)`) — that
  is iteration 040, which depends on this one.
- Converting any heuristic into an LLM semantic judgment (issue #1, move 3 —
  demand-pulled horizon).
- `factual_anchor`, `temporal`, and `narrative_structure`: they operate over the
  graph / research records, not surface prose, and are not touched.
- Any new dependency, third-party Markdown parser, or general-purpose
  Markdown-AST layer.

### Key Entities *(include if feature involves data)*

- **Classified line**: One line of a Markdown source, carrying its 1-based source
  line number, its **raw** text (the original line), and its **normalized** text
  (the line with its leading structural block prefix removed). It exposes no
  consumed "kind" attribute — prefix recognition is an internal step of producing
  the normalized form. It is the unit a prose validator iterates over: the
  proper-noun scan reads `normalized`, the dialogue-sensitive scans read `raw`.
- **Prose/structure view**: The ordered sequence of classified lines for one
  Markdown source (a manuscript file or the constitution). It is the single object
  validators consume in place of `text.splitlines()`. The placeholder predicate is
  a sibling helper of the seam (a string predicate), not a property of the view.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The entire existing test suite (every current validator test and
  E2E oracle) passes with **zero** oracle edits after the refactor.
- **SC-002**: All local stripper constructs are removed from the validators —
  `_HEADING_MARKER` from `character_presence`; `_BULLET`, `_LEAD_EMPHASIS`,
  `_CLOSE_EMPHASIS`, `_normalize_declaration_line`, and `_PENDING_ONLY` from
  `focalization` — and **no validator calls `splitlines()` directly** any longer
  (line splitting is single-sourced in the seam). The count of per-validator
  markup-stripping / line-splitting constructs drops to zero; the emphasis
  strippers are deleted (folded into the declaration recognizer), not relocated to
  the seam.
- **SC-003**: A new fixture exercising the next Markdown surface (an off-roster
  mention inside a `> blockquote` or epigraph) is handled correctly **with the
  three validators' source unchanged by the fixture** — demonstrating one seam,
  not a fourth patch.
- **SC-004**: Reported `relpath:line` locators are identical to the pre-refactor
  locators for every finding the suite produces.
- **SC-005**: No new runtime dependency appears in the project (the dependency
  set is byte-identical), and every changed/new file is ≤ 500 lines.
- **SC-006**: The four CI gates are green.

## Assumptions

- The set of Markdown surfaces the seam must strip is the block-level prefixes the
  local strippers handle today (ATX heading, bullet/blockquote), plus the one new
  surface the generalization fixture proves (`> blockquote` / epigraph — already a
  bullet/blockquote prefix, so no new recognizer is needed). The label-adjacent
  emphasis the old `focalization` strippers handled is NOT a seam concern: it is
  folded into `focalization`'s declaration recognizer, keeping the shared seam free
  of any validator's domain vocabulary. The seam is not asked to model the full
  CommonMark grammar — only a conservative, deterministic block-prefix stripper
  sufficient to subsume the existing strippers and the next surface
  (Constitution II).
- "Byte-for-byte parity" is judged against the *normalized output* of the current
  strippers on the inputs the live fixtures exercise, not against an abstract
  Markdown spec. Where the current strippers are deliberately conservative (e.g.
  ATX marker anchored at column 0 with no leading whitespace, seven-plus `#` not
  matched), the seam preserves that conservatism rather than "fixing" it.
- The seam reads a Markdown source as plain text and classifies it line by line;
  it does not need YAML front-matter parsing (that remains `frontmatter.py`'s job)
  and consumes the same `(relpath, text)` / constitution-text material the
  `ValidationContext` accessors already expose.
- The generalization fixture targets `character_presence` (the proper-noun
  heuristic is the clearest place a new surface re-opens the crack); the seam's
  blockquote stripping benefits whichever validator scans that line.
- Whether an empty/absent source should surface as "not evaluated" is left to
  iteration 040; this iteration preserves today's empty-input behaviour exactly.
