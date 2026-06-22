# Feature Specification: The prose seam recognizes the leading Spanish dialogue dash

**Feature Branch**: `041-prose-dialogue-dash`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Necesidad: en prosa española el diálogo se abre con la raya tipográfica `—` (U+2014; y a veces la semirraya `–`, U+2013). La costura de prosa única de Bookwright (`io/prose.py`, iteración 039) normaliza los marcadores de bloque ASCII —encabezado ATX `#{1,6} `, viñeta/blockquote `[-*+>] `— pero NO reconoce la raya de diálogo. Como consecuencia, `character_presence` ve `—Esto es el porvenir` con la `—` aún pegada: el término `Esto` no queda en offset 0, así que la exención de inicio-de-frase no dispara y `Esto` (un demostrativo, no un nombre propio) se reporta como nombre propio sin entrada en la bible. En una novela real —mayoritariamente diálogo con raya— esto inunda de warnings espurios el primer término capitalizado de CADA línea de diálogo (Esto, Sí, Claro, Nunca…), ahogando los hallazgos reales. Son `warning`, así que no vetan el gate, pero es exactamente el fallo de superficie que issue #1 quería cerrar de raíz, y la costura de 039 lo dejó abierto para la raya. Detectado por el dogfood end-to-end de `tiny-historical` tras `v0.5.0` (DEBT-009 en `DEBT.md`). Esta iteración cierra DEBT-009 en la COSTURA, no en el validador: `io/prose.py` añade la raya de diálogo líder (`—`/`–`, tolerando espacio alrededor) al conjunto de marcadores estructurales que su normalización retira. Tras normalizar, el primer término de contenido de la línea de diálogo queda en offset 0 y hereda la exención de inicio-de-frase YA existente en `character_presence`. NINGÚN validador se toca."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dialogue-heavy prose produces no spurious proper-noun warnings (Priority: P1)

An author writes a Spanish novel that is, like most Spanish prose, overwhelmingly
dialogue. Every line of dialogue opens with the typographic dash (`—Esto es el
porvenir`, `—Sí`, `—Claro que no`). They build the graph and run `bookwright
validate`. The `character_presence` validator must **not** treat the **first word
after a leading dialogue dash** as an unknown proper noun: that capitalization is
the start of the spoken sentence, exactly like a capitalized word that opens any
sentence — which the validator already excludes.

**Why this priority**: This is the entire defect. In a real, dialogue-dominated
manuscript the validator fires one spurious `warning` on the first capitalized word
of *every* dialogue line (`Esto`, `Sí`, `Claro`, `Nunca`…), drowning the genuine
unknown-name findings the author actually needs to see. It is the same
surface-marker class issue #1 set out to close at the root, and the 039 seam left
it open for the dialogue dash. The validator already promises to skip
sentence-initial capitalization; the leading dash simply hides that the word opens
the sentence.

**Independent Test**: Feed the prose seam a line `—Esto es el porvenir` (and the
half-dash variant `–Esto…`); assert its normalized form begins at offset 0 with
`Esto`, so the proper-noun heuristic sees a line-initial word and produces **zero**
findings attributable to that opening word.

**Acceptance Scenarios**:

1. **Given** a manuscript line `—Esto es el porvenir` (where `Esto` has no bible
   entry), **When** `character_presence` runs, **Then** it produces no
   `proper noun 'Esto' …` finding — the leading dash is removed and `Esto` is
   line-initial.
2. **Given** dialogue lines opening with the half-dash (`–`, U+2013) and with a
   space after the dash (`— Claro`), **When** `character_presence` runs, **Then**
   none of the dialogue-opening words is reported as an unknown proper noun.

---

### User Story 2 - A real out-of-roster name inside dialogue is still flagged (Priority: P1)

The fix must neutralize only the **leading** dash (the structural marker), not the
content of the line. A genuine proper noun that appears *later* in a dialogue line
— e.g. `—Pregúntale a Quirón —dijo.`, where `Quirón` is not in the bible roster —
must still be evaluated against the roster and flagged exactly as it would be in
ordinary prose. Internal dashes that fence a speech tag (`—dijo Arnela—`) must be
left untouched, so the words inside the inciso continue to be analyzed.

**Why this priority**: Over-correcting (stripping *every* dash, or treating the
whole dialogue line as exempt) would create a silent blind spot: an author could
introduce a never-defined character only ever named in dialogue and the validator
would never notice. The normalization must remove only the *leading* dialogue
marker, restoring the line to ordinary prose for analysis — not exempt the line and
not touch internal dashes.

**Independent Test**: Feed the seam `—Pregúntale a Quirón —dijo.` with `Quirón`
absent from the bible roster; run `character_presence`; assert the
unknown-proper-noun finding for `Quirón` fires while the leading-dash position
produces nothing.

**Acceptance Scenarios**:

1. **Given** a dialogue line `—Pregúntale a Quirón —dijo.` with `Quirón` not in the
   roster, **When** `character_presence` runs, **Then** it emits the
   `proper noun 'Quirón' …` warning (the leading dash is removed; `Quirón` is still
   mid-line, so it is analyzed normally) and does **not** flag the opening word.
2. **Given** a dialogue line whose speech tag is fenced by internal dashes
   (`—dijo Arnela—, y se fue`) where `Arnela` is not in the roster, **When**
   `character_presence` runs, **Then** the internal dashes are **not** treated as
   leading markers and `Arnela` is analyzed exactly as today (no behavior change for
   internal dashes).

---

### Edge Cases

- **Dash glued to the word**: the canonical Spanish form glues the dash to the first
  word (`—Esto`, no space). The recognized leading marker therefore tolerates
  **optional** trailing whitespace (`\s*`, so `—Esto` and `— Esto` both normalize to
  `Esto…`), unlike the bullet marker whose trailing space is required (`\s+`).
- **Leading whitespace before the dash**: a small amount of indentation before the
  dash (`␠␠—Esto`) is tolerated, mirroring the bullet/blockquote marker which is
  already whitespace-tolerant at the line start.
- **Internal dashes (incisos)**: a dialogue line with dashes that fence a speech
  tag — `—dijo Arnela—` — has only its **leading** dash removed; the internal
  dashes and the words around them are analyzed unchanged.
- **ASCII hyphen vs. typographic dash**: the ASCII hyphen-led bullet `- ` is already
  covered by the existing bullet marker (and requires a trailing space); this change
  adds **only** the typographic em dash (`—`, U+2014) and en dash (`–`, U+2013) as a
  new dialogue marker. A bare hyphen mid-word (`bien-venido`) is unaffected.
- **Dash-only line**: a line that is solely a dash (`—`) normalizes to the empty
  string and yields no candidates — no finding, no error.
- **Interaction with other markers**: the leading-dash strip composes with the
  existing iterative normalization (a heading or bullet already removed first leaves
  a following dialogue dash to be removed in a later pass), so a combined prefix
  reduces to its content exactly as the existing block markers do.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The shared prose seam (`io/prose.py`) MUST recognize a **leading
  dialogue dash** — the em dash `—` (U+2014) or the en dash `–` (U+2013), anchored at
  the line start, tolerating optional leading whitespace and optional trailing
  whitespace (`\s*`) — as a structural marker and strip it during line normalization,
  alongside the heading and bullet/blockquote markers it already removes.
- **FR-002**: After normalization, the first content word of a dialogue line MUST
  land at offset 0, so that `character_presence`'s **existing** sentence-initial
  exemption (`_is_sentence_initial`) treats it as line-initial and never reports it
  as an unknown proper noun. No edit to any validator is permitted — the fix lives
  **only** in the shared seam (the criterion that proves the class is closed at the
  root, not patched per-instance, per issue #1).
- **FR-003**: Only the **leading** dash MUST be stripped. Internal dashes that fence
  a speech tag (`—dijo Arnela—`) MUST be left untouched, so the words inside an
  inciso continue to be analyzed exactly as today.
- **FR-004**: A real out-of-roster proper noun appearing *later* in a dialogue line
  (e.g. `Quirón` in `—Pregúntale a Quirón —dijo.`) MUST still be flagged — the seam
  removes the leading marker, not the line content.
- **FR-005**: The en dash `–` (U+2013) MUST be recognized identically to the em dash
  `—` (U+2014). The ASCII hyphen-led bullet (`- `) MUST remain covered by the
  existing bullet marker and is not part of this change.
- **FR-006**: The recognizer MUST be a deterministic, anchored regular expression
  (the same shape as the existing `_BULLET_MARKER`), with NO new third-party
  dependency and NO Markdown parser/AST (Constitution II).
- **FR-007**: The reported source locator (`relpath:line`) for any finding that still
  fires MUST remain correct — the line number continues to come from `enumerate`,
  never from a regex match offset; normalization affects only the scanned text, not
  the numbering.
- **FR-008**: There MUST be ZERO regression on the live fixtures, verified
  **empirically** by running the full suite. No finding oracle may be edited EXCEPT
  where a fixture currently carries a **spurious dialogue-dash false positive**; such
  a count is corrected **downward** (the fixture manuscript itself is NOT touched),
  exactly as iteration 038 corrected the `tiny-historical` count `6 → 5` for the
  spurious `Capítulo`.
- **FR-009**: A regression/generalization test MUST prove both directions on a
  dialogue paragraph: the leading demonstrative after a dash (`—Esto…`) is NOT
  flagged, while an out-of-roster character named **mid-line** in dialogue
  (`—Pregúntale a Quirón —dijo.`) IS still flagged — demonstrating that only the
  leading marker is neutralized, not the content.
- **FR-010**: No other prose-seam behavior MUST change: the existing heading, bullet,
  and blockquote stripping, the `is_placeholder` check, the 1-based line numbering,
  and `prose_view("") == ()` all stay byte-identical; every other validator
  (`focalization`, setting continuity, temporal) reads the seam unchanged and any
  prose validator automatically benefits.
- **FR-011**: The DEBT-009 entry MUST be removed from `DEBT.md` (git retains the
  history), per the repo's debt-cancellation convention.
- **FR-012**: The frozen GOLEM ontology (Constitution X) MUST NOT change — this is a
  prose-level, graph-free, LLM-free change; prose validators keep `triples=()`. Every
  changed/new file MUST remain ≤ 500 lines; the CI gate (only `error`-severity
  findings break CI) and all severities are unchanged.

### Key Entities *(include if feature involves data)*

- **Prose line (`ProseLine`)**: one source line carried by the seam — its 1-based
  `number`, its exact `raw` text, and its `normalized` text. A dialogue line carries
  a leading typographic dash that is structural, not prose; after this change the
  leading dash is removed in `normalized` before any validator's heuristic evaluates
  the line, restoring the spoken line to ordinary prose whose first word is
  line-initial. `number` is never a match offset (the locator is stable).
- **Leading dialogue marker**: a new structural marker class in the seam — the em
  dash `—` or en dash `–` at the line start (optional leading whitespace, optional
  single trailing space) — joining the heading and bullet/blockquote markers the
  seam already strips. Only the leading occurrence is a marker; dashes elsewhere in
  the line are content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A dialogue-dominated manuscript in which every line opens with a
  typographic dash, with no out-of-roster names in the spoken content, produces
  exactly **0** `character_presence` findings attributable to a dialogue-opening
  word.
- **SC-002**: An out-of-roster name appearing mid-line in dialogue is reported
  exactly once (per the existing per-distinct-name collapsing), proving the spoken
  line is still analyzed and only the leading dash was neutralized.
- **SC-003**: All existing fixtures behave identically — 100% parity, no finding
  added or removed in non-dialogue prose — except a downward correction of any
  oracle that counted a spurious dialogue-dash false positive (fixture manuscript
  untouched).
- **SC-004**: No validator source file is edited — the diff to the validators is
  empty, proving the class is closed in the shared seam and any prose validator
  benefits automatically.
- **SC-005**: All four quality gates pass: `ruff check`, `ruff format --check`,
  `mypy --strict`, and `pytest` at ≥ 80 % coverage.
- **SC-006**: `DEBT.md` no longer contains a DEBT-009 entry, and the implementation
  introduces no new debt of its own. The pre-existing, **same-class** leading
  quotation-mark / horizontal-bar (`«`, `"`, `―` U+2015) false positives discovered
  while closing DEBT-009 are **recorded** as DEBT-011 (a future iteration), never
  silently dropped — this recording is the doctrine-mandated trail, not new debt the
  change creates.

## Assumptions

- The dialogue marker shape that matters is the typographic em dash `—` (U+2014),
  with the en dash `–` (U+2013) as a documented variant — the universal Spanish-prose
  convention for opening dialogue. The ASCII hyphen-led bullet (`- `) is a distinct,
  already-handled marker and is intentionally excluded here.
- The Spanish convention glues the dash to the first spoken word (`—Esto`), so the
  marker's trailing space is **optional** (`\s*`), unlike the bullet marker whose
  trailing space is required (`\s+`) to distinguish a bullet from inline emphasis. A
  leading typographic dash is unambiguous, so no such disambiguation is needed.
- The fix reuses the **existing** sentence-initial exemption in `character_presence`
  rather than adding a parallel rule, exactly as DEBT-008 reused it for the ATX
  heading marker. The first dialogue word is handled by the same code path as the
  first word of a sentence — minimizing new behavior and surface area.
- Because the unknown-mention finding's source locator is `relpath:line` (no column),
  stripping the leading dash from the line for analysis cannot shift a reported
  position.
- The change is confined to the line-normalization step in the shared seam; the
  orphan (bible→manuscript) direction reads the full manuscript text and is
  unaffected by leading dashes.
- "ZERO regression unless a spurious dash false positive exists" is verified
  empirically by running the suite, not assumed; should a live oracle carry such a
  count it is corrected downward, never the fixture text.

## Out of Scope

- The incomplete cross-reference roster for settings / locations / objects — a
  separate-class defect (DEBT-010, iteration 042): `character_presence` only knows the
  character roster, so multi-word setting tokens are still flagged. Not addressed
  here.
- Replacing the pinned proper-noun heuristic with semantic judgment / NER (issue #1
  move 3, demand-pulled): the correction is to strip the leading dialogue marker in
  the shared seam, not to redesign the detector.
- Editing any validator: the fix lives **solely** in `io/prose.py`. Touching
  `character_presence` (or any other validator) would reintroduce exactly the
  per-instance surface coupling that iteration 039 paid off.
- Any validator that does not scan surface prose (`factual_anchor`, `temporal`,
  `narrative_structure`) — they do not consume the prose seam's line view, so they
  are unaffected.
- Other **leading typographic markers of the same class** — the horizontal bar `―`
  (U+2015) and leading quotation marks (`«`/`»`, `"`/`"`, ASCII `"`/`'`) — that
  produce the identical spurious first-word flag (verified empirically during this
  spec's audit: `«Esto`, `"Hola`, and `―Esto` all fire today). These are NOT silently
  dropped: per the zero-debt doctrine they are recorded as **DEBT-011** in `DEBT.md`
  for a future iteration. They are deferred (not swept here) because the
  leading-quote/horizontal-bar family is a genuine design decision of its own — paired
  open/close semantics (`«`…`»`), quotes that also appear mid-line as content, and the
  overlap with the `¿¡` opening punctuation that `_SENTENCE_END` already exempts —
  larger than adding the dialogue-dash code points. This iteration closes ONLY the
  observed DEBT-009 defect: the dialogue dash (`—`/`–`).
- Full Markdown emphasis inside dialogue (`**`/`*`/`_`): out of scope; emphasis is
  `focalization`'s own vocabulary, never a seam block prefix (per the 039 seam).
- Touching the frozen ontology (Constitution X); this is a prose-level change that
  never touches the graph.
