# Phase 0 Research — leading Spanish dialogue dash in the prose seam

All decisions below are resolved; the spec carries **no** `[NEEDS CLARIFICATION]`.

## D1 — Marker shape: `^\s*[—–]\s*`

- **Decision**: recognize a leading dialogue dash as
  `_DIALOGUE_MARKER = re.compile(r"^\s*[—–]\s*")` — anchored at line start, optional
  leading whitespace, optional **trailing** whitespace.
- **Rationale**:
  - Anchored `^` so only the *leading* dash is a marker; dashes elsewhere are content
    (FR-003).
  - Leading `\s*` mirrors `_BULLET_MARKER` (`^\s*[-*+>]\s+`), tolerating a little
    indentation (`␠␠—Esto`), edge case in the spec.
  - Trailing `\s*` (not `\s+`) because the canonical Spanish form glues the dash to
    the first spoken word (`—Esto`), and `— Esto` (with a space) must normalize to the
    same `Esto…`. The bullet marker needs `\s+` to tell a list bullet `* text` from
    inline emphasis `*text*`; a leading typographic dash is **unambiguous**, so no such
    guard is required and `\s*` is correct (Assumption in spec).
- **Alternatives considered**:
  - `\s+` trailing — **rejected**: would fail to strip the dominant glued form `—Esto`,
    leaving the exact defect unfixed.
  - Stripping *all* dashes on the line — **rejected**: would erase incise speech-tag
    dashes (`—dijo Arnela—`) and create a silent blind spot for names that appear only
    after an internal dash (FR-003/FR-004, User Story 2).

## D2 — Home of the fix: the seam's `_normalize`, not the validator

- **Decision**: add the marker as a third `elif` branch inside the existing
  `_normalize` strip loop in `io/prose.py`; do **not** edit
  `character_presence._is_sentence_initial` or any validator.
- **Rationale**: this is the issue-#1 doctrine made concrete — the surface-marker class
  (DEBT-004/007/008/009) is closed once, at the shared seam, so *every* prose validator
  benefits automatically and none re-couples to a surface marker. It is the same
  mechanism iteration 038 (DEBT-008) used for the ATX heading: with the marker removed,
  the first word is line-initial and inherits the **existing** sentence-initial
  exemption. The diff to the validators is empty (SC-004).
- **Alternatives considered**:
  - Add `—`/`–` to `character_presence._SENTENCE_END` — **rejected**: re-introduces the
    per-validator surface coupling that 039 paid off; would not help `focalization` or
    any future prose validator; and `_SENTENCE_END` models *sentence-ending punctuation*,
    not a leading structural marker.

## D3 — Code points: the dialogue-dash class `—` `–` `―` (U+2014/2013/2015)

- **Decision**: the new marker covers the full dialogue-dash class — `—` (U+2014),
  `–` (U+2013), and `―` (U+2015, the historical horizontal bar). All three are leading
  dashes with identical glued, unpaired semantics — one class, not three bugs.
- **Rationale**: these are the Spanish dialogue-dash convention (em/en is the form
  observed in the `tiny-historical` dogfood; `―` is the historical *raya*). The ASCII
  hyphen bullet `- ` stays owned by `_BULLET_MARKER` (requires a trailing space; FR-005).
  U+2015 was originally scoped to DEBT-011 but the review pass swept it in: it is
  same-class **and** same-design (one code point added to the class), so deferring it
  would be the instance-by-instance whack-a-mole issue #1 exists to stop (doctrine § 4).
- **Deferred (related class, distinct design)**: **leading quotation marks**
  (`«`/`»`, `"`/`"`, ASCII `"`/`'`) produce the identical spurious first-word flag —
  verified empirically during the spec audit (`«Esto`, `"Hola` fire today). They are
  **recorded as DEBT-011** in `DEBT.md`, not swept here: quotes have paired open/close
  semantics, appear mid-line as content, and overlap the `¿¡` opening punctuation
  `_SENTENCE_END` already exempts — a larger design than adding a dash code point.

## D4 — Parity: which oracles change, verified empirically

- **Decision**: the single pinned-count oracle that shifts is
  `tests/fixtures/tiny-historical/expected-status.md`: `validation.counts.warning`
  `5 → 4`. The fixture **manuscript is not touched** (exactly as iteration 038 corrected
  `tiny-historical` `6 → 5` for the spurious `Capítulo`).
- **Evidence** (planning-time simulation over the real manuscript + roster, current vs.
  marker-added normalization):
  - CURRENT `character_presence`: `[(3,'Real'), (3,'Fábrica'), (3,'Paños'), (12,'Esto')]`
  - PROPOSED: `[(3,'Real'), (3,'Fábrica'), (3,'Paños')]` — only `Esto` (line 12,
    `—Esto es el porvenir`) is removed; `Real/Fábrica/Paños` (DEBT-010, out of scope)
    stay. Project-wide total = factual_anchor's `{error:1, warning:1}` + these → was
    `{error:1, warning:5}`, becomes `{error:1, warning:4}`.
- **Other fixtures with leading dialogue dashes**: `tiny-novel`
  (`—Volviste`, `—Solo …`) and `tiny-memoir` (`—Marta …`) also lose spurious
  dialogue-dash flags, **but** their tests assert only `by_severity["error"] == 0`
  (`test_fixtures.test_fixture_validates_clean`) and research-fact counts
  (`test_status`), never a pinned warning count — so no oracle edit is needed there.
  The bare-scaffold `{0,0,0}` count in `test_status` is a no-bible project, not a
  fixture, and is unaffected.
- **Method**: parity is re-verified by running the full suite during implementation
  (`uv run pytest`) — counts are read empirically, never assumed (FR-008).
