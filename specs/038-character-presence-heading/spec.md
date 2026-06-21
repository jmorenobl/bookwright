# Feature Specification: `character_presence` does not flag the first word of a markdown heading as a proper noun

**Feature Branch**: `038-character-presence-heading`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "El validador `character_presence` marca la primera palabra de cada encabezado markdown del manuscrito como un nombre propio sin entrada en el bible. En un proyecto recién creado por `bookwright init` con un manuscrito que use `# Capítulo 1`, `## Escena`, etc., aparece `proper noun 'Capítulo' appears in the manuscript but has no bible entry (heuristic — may be a place or organization)` en cada cabecera. La causa: el heurístico de proper-noun excluye una mayúscula a inicio de línea o tras puntuación de fin de frase (`_SENTENCE_END`) por gramatical, pero no contempla la sintaxis markdown: la primera palabra de `# Capítulo 1` queda precedida por el prefijo `# ` y se trata como mitad de frase, así que se marca. Queremos que la primera palabra de un encabezado markdown reciba el mismo trato de «inicio de oración» que ya existe, sin cambiar ninguna otra regla del validador."

## Clarifications

### Session 2026-06-21

A non-interactive ambiguity scan found the spec fully determined for
implementation — the normalization seam, the ATX `#{1,6}␠` boundary, the
edge-case directions, locator stability, the no-regression parity bar, and the
frozen-ontology constraint are all pinned. One test-design decision was the only
genuinely open, materially-impactful choice; it is recorded below.

- Q: Should the FR-006/FR-007 regression tests bind to the live `bookwright init`
  scaffold (as iteration 037 did for the constitution) or construct a synthetic
  in-test manuscript? → A: Synthetic in-test manuscript — the scaffold ships an
  **empty** manuscript (`resources/project/manuscript/.gitkeep` only, no
  heading-bearing file), so there is no live scaffold artifact to bind to;
  authoring a focused in-test manuscript with `# Capítulo 1`-style headings is the
  only correct and non-speculative option (zero-debt doctrine §2: no plumbing
  whose only justification is "future X"). This differs from iteration 037, where
  the bug lived in the exact live-scaffold constitution text and binding to it was
  load-bearing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A manuscript with chapter headings produces no spurious proper-noun warnings (Priority: P1)

An author runs `bookwright init`, writes a manuscript whose scenes are organized
under markdown headings (`# Capítulo 1`, `## Escena`, `### El faro`, …) — the
universal shape of authored prose — and runs `bookwright validate`. The
`character_presence` validator must not treat the **first word of each heading
line** as an unknown proper noun: that capitalization is structural (it opens the
heading), exactly like a capitalized word that opens a sentence, which the
validator already excludes.

**Why this priority**: This is the entire defect. Every manuscript has headings,
so every project hits this on the very first `validate`. The author is flooded
with `proper noun 'Capítulo' …`, `proper noun 'Escena' …` warnings — one per
heading — training them to ignore the validator before it ever surfaces a real
unknown name. The validator already promises to skip sentence-initial
capitalization; markdown heading markers simply hide that the word is at the start.

**Independent Test**: Build a project whose manuscript contains chapter headings
(`# Capítulo 1`, `## Escena en el muelle`, …) and ordinary prose; run the
`character_presence` validator; assert it produces **zero** findings attributable
to a heading's first word.

**Acceptance Scenarios**:

1. **Given** a manuscript whose first line is `# Capítulo 1` and whose body is
   plain prose with no out-of-roster names, **When** `character_presence` runs,
   **Then** it produces no `proper noun '…'` finding for `Capítulo`.
2. **Given** headings at every supported depth (`#` … `######`, each followed by a
   space and a capitalized word), **When** `character_presence` runs, **Then**
   none of the heading-opening words is reported as an unknown proper noun.

---

### User Story 2 - A real out-of-roster name inside a heading is still flagged (Priority: P1)

The fix must skip only the heading's **opening** word (the structural
capitalization), not silence the whole title. A genuine proper noun that appears
*later* in a heading body — e.g. `# La caída de Elena`, where `Elena` is not in
the bible roster — must still be evaluated against the roster and flagged exactly
as it would be in ordinary prose.

**Why this priority**: Over-correcting (treating the entire heading line as exempt)
would create a silent blind spot: an author could introduce a never-defined
character only ever named in titles and the validator would never notice. The
normalization must strip the heading *marker*, restoring the title to ordinary
prose for analysis — not exempt the line.

**Independent Test**: Build a manuscript whose heading is `# La caída de Elena`
with `Elena` absent from the bible roster; run `character_presence`; assert the
unknown-proper-noun finding for `Elena` fires.

**Acceptance Scenarios**:

1. **Given** a heading `# La caída de Elena` with `Elena` not in the roster,
   **When** `character_presence` runs, **Then** it emits the
   `proper noun 'Elena' …` warning (the heading marker is removed; `Elena` is
   still mid-line, so it is analyzed normally).
2. **Given** a heading `# Elena observó el faro` where `Elena` — a ≥3-letter
   proper-noun candidate not in the roster — **opens** the heading, **When**
   `character_presence` runs, **Then** `Elena` is treated as heading-initial and is
   **not** flagged: the opening word receives the same exemption a sentence-opening
   capital already gets, so the validator never invents a name from a structural
   capital. (Contrast scenario 1: the *same* word mid-heading **is** flagged — this
   scenario is load-bearing precisely because `Elena` would be flagged here but for
   the heading-initial exemption.)

---

### Edge Cases

- **No space after the marker**: a line like `#Capítulo` (no space) is **not** an
  ATX heading (CommonMark requires the space). Its marker is **not** stripped and
  the line is analyzed exactly as today, so this fix neither adds nor removes a
  finding for the no-space form — only a valid `#{1,6}␠` marker is normalized.
- **Leading whitespace before the marker**: indented heading-like lines are not in
  scope; the recognized form is a line that *starts* with one to six `#`
  characters followed by a space, matching the manuscript headings `bookwright`
  scaffolds and authors write.
- **Heading depth boundary**: one through six `#` followed by a space is a heading
  whose marker is stripped; seven or more `#` is not an ATX heading, so its marker
  is **not** stripped and the line is analyzed exactly as today — no behavior change
  in either direction.
- **Real proper noun opening a heading**: `# Elena observó el faro` — `Elena` opens
  the heading and, like a sentence-opening capital, receives the existing
  heading/line-initial exemption (the validator's conservative direction: it never
  invents a name from a structural capital).
- **Closing-hash (ATX) headings**: a trailing ` #` sequence (`# Capítulo 1 #`) is
  cosmetic; the opening marker is still stripped and the trailing hashes affect no
  capitalized word, so behavior is unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When a manuscript line is a markdown heading — it begins with one to
  six `#` characters immediately followed by a space — the `character_presence`
  proper-noun heuristic MUST treat the line's **first content word** as
  sentence-initial (the same exemption a capitalized word at the start of a line
  already receives), so that word is never reported as an unknown proper noun.
- **FR-002**: The exemption MUST apply only to the heading's opening word by virtue
  of removing the heading *marker* before the existing heuristic runs. The
  remainder of the heading body MUST continue to be analyzed exactly as ordinary
  prose: a real out-of-roster proper noun later in the title (e.g. `Elena` in
  `# La caída de Elena`) MUST still be flagged.
- **FR-003**: Real proper nouns in ordinary (non-heading) prose MUST continue to be
  flagged exactly as today — no regression on the existing `character_presence`
  fixtures and no change to the pinned stop-set.
- **FR-004**: No other `character_presence` rule MUST change: the inverse direction
  (a bible character never mentioned in the manuscript → `error`), the pinned
  stop-set, the per-distinct-name collapsing, and the `warning` severity of the
  unknown-mention finding all stay byte-identical.
- **FR-005**: The reported source locator (`relpath:line`) for any finding that
  still fires MUST remain correct — removing the heading marker for analysis MUST
  NOT shift the reported line number.
- **FR-006**: A regression test MUST start from a **synthetic in-test** manuscript
  that uses chapter headings (`# Capítulo 1`, etc.) and assert **zero**
  `character_presence` findings caused by a heading's opening word. The test
  authors its own heading-bearing manuscript rather than binding to the
  `bookwright init` scaffold, because the scaffold ships an empty manuscript
  (`resources/project/manuscript/.gitkeep`) with no heading file to bind to
  (Clarifications 2026-06-21).
- **FR-007**: A complementary test MUST confirm that an out-of-roster name inside a
  heading body (e.g. `# La caída de Elena`, `Elena` not in the roster) is still
  flagged — proving the normalization strips the `#` marker, not the whole title.
- **FR-008**: The DEBT-008 entry MUST be removed from `DEBT.md` (git retains the
  history), per the repo's debt-cancellation convention; the "Deuda abierta"
  section becomes `_Ninguna por ahora._`.
- **FR-009**: The frozen GOLEM ontology (Constitution X) MUST NOT change — this is
  a prose-level validator that never touches the graph (`triples=()`).

### Key Entities *(include if feature involves data)*

- **Manuscript line**: a single line of manuscript prose scanned by the
  proper-noun heuristic. A line that is a markdown heading carries a leading
  `#{1,6}␠` marker that is structural, not prose; after this change the marker is
  removed before the heuristic evaluates the line, restoring the title to ordinary
  prose whose first word is line-initial.
- **Proper-noun candidate**: a capitalized token of ≥3 letters found in a line.
  Candidates opening a sentence — or, after this change, opening a heading — are
  exempt; all others are checked against the roster and stop-set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A manuscript whose scenes are organized under markdown headings,
  with no out-of-roster names in the prose, produces exactly **0**
  `character_presence` findings.
- **SC-002**: An out-of-roster name appearing only inside a heading body is
  reported exactly once (per the existing per-distinct-name collapsing), proving
  the title is still analyzed.
- **SC-003**: All existing `character_presence` fixtures and the pinned stop-set
  behave identically — 100% parity, no finding added or removed in non-heading
  prose.
- **SC-004**: All four quality gates pass: `ruff check`, `ruff format --check`,
  `mypy --strict`, and `pytest` at ≥ 80 % coverage.
- **SC-005**: `DEBT.md` no longer contains a DEBT-008 entry, and no new debt entry
  is introduced by this change.

## Assumptions

- The markdown heading shape that matters is the ATX form a line starting with one
  to six `#` characters followed by a space — the shape `bookwright`'s own scaffold
  emits and the universal convention in authored manuscripts. Setext headings
  (underlined with `===`/`---`) and indented/fenced forms are out of scope: their
  opening word is already line-initial and thus already exempt, so they do not
  trigger the defect.
- The fix removes the heading *marker* and reuses the **existing** sentence-initial
  exemption rather than adding a parallel rule, so the first heading word is
  handled by the same code path as the first word of a sentence — minimizing new
  behavior and surface area.
- Because the unknown-mention finding's source locator is `relpath:line` (no
  column), stripping the marker from the line for analysis cannot shift a reported
  position.
- The change is confined to the line-normalization step that feeds the proper-noun
  heuristic; the orphan (bible→manuscript) direction reads the full manuscript text
  and is unaffected by heading markers.

## Out of Scope

- Replacing the pinned proper-noun heuristic with NER or a full markdown parser:
  the correction is to strip the heading marker before the existing
  sentence-initial rule runs, **not** to redesign the detector.
- Changing any other `character_presence` rule: the inverse bible→manuscript
  orphan check, the pinned stop-set, the per-name collapsing, or the `warning`
  severity of the unknown-mention finding.
- Changing any other validator (`focalization`, setting continuity, temporal, …).
- Handling non-ATX heading forms (setext, indented) or inline markdown emphasis
  (`**bold**`, `_italic_`) inside a heading: their opening word is already exempt
  or already analyzed as prose; only the ATX `#{1,6}␠` marker causes the defect.
- Touching the frozen ontology (Constitution X); this is a prose validator that
  does not touch the graph.
