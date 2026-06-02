# Phase 0 Research: The 10 Bookwright Command Source Prompts

All unknowns from Technical Context resolved below. No `NEEDS CLARIFICATION` remains.

## R1 — How to measure the < 5000-token body budget (FR-015, SC-002)

**Decision**: Char-based approximation is the deterministic default. Estimate
`tokens ≈ ceil(len(body_chars) / 4)` and assert `< 5000`. If `tiktoken` is importable
in the test environment, count with `tiktoken.get_encoding("cl100k_base")` and assert
the real count `< 5000` instead. The test never *requires* tiktoken.

**Rationale**:
- Constitution II forbids adding a runtime dependency without amendment; `tiktoken` is
  not in the minimum set and pulling it in (plus its encoding download) for a static
  documents check is unjustified.
- `len/4` is the standard rough English/Spanish heuristic and runs offline and
  deterministically. 5000 tokens ≈ 20 000 chars; bodies are authored well under that
  (target ≤ ~14 000 chars ≈ ~3500 tokens) so the heuristic's slack never bites.
- FR-015 explicitly sanctions "tiktoken when available, otherwise a character-based
  approximation" — this honors both branches without making the build network-dependent.

**Alternatives considered**:
- *Add `tiktoken` as a dev dependency* — rejected: needs a model/encoding download on
  first use (non-hermetic CI), and the precision buys nothing given the headroom.
- *Word-count proxy* — rejected: less faithful to tokenization than `len/4`.

## R2 — The `references/` roster (FR-028, FR-029)

**Decision**: Ship six reference files, each cited by at least one body:

| File | Domain content | Cited by |
|---|---|---|
| `golem-character.md` | `G1_Character` fields, the `name/born/died/features/narrative_roles` frontmatter contract, the platonic vs narrative distinction | bible |
| `golem-relationships.md` | `G4_Social_Relationship` / `G6_Relationship_Role` reified-relationship modeling + `relationships.md` container | bible, continuity |
| `golem-events-timeline.md` | `G5_Narrative_Event` vs `G3_Psychological_State`, the `timeline.md` `events` container contract | bible, continuity |
| `propp-functions.md` | Propp's narrative functions + dramatis personae roles | outline, scenes |
| `greimas-actants.md` | Greimas's actantial model (subject/object/sender/receiver/helper/opponent) | outline, scenes |
| `pending-protocol.md` | The shared `[PENDING: <pregunta>]`-vs-stop-and-ask rule + the YAML-quoting caveat for string-typed fields | every generative command |

**Rationale**: The binding requirement is FR-029 (no dangling reference), not a fixed
list. Splitting GOLEM by module (character / relationships / events) mirrors design § 4.2
and lets each generative body link only the module it needs, protecting the token budget.
`pending-protocol.md` centralizes the rule that would otherwise be repeated verbatim in
five bodies — single source of truth, and it keeps each body leaner.

**Alternatives considered**:
- *One monolithic `golem.md`* — rejected: every body would pull the whole ontology into
  the reader's tier-3 even when it needs one module; also harder to keep individual
  citations precise.
- *Inline the domain context in each body* — rejected: blows the tier-2 budget and
  violates the progressive-disclosure intent (Constitution VII, US4).

Implementation MAY consolidate as long as every `references/…` path a body cites resolves
to a shipped file.

## R3 — `[PENDING: …]` vs stop-and-ask, and the YAML-quoting caveat (FR-013, FR-016)

**Decision**: All generative bodies adopt the iteration-7 marker `[PENDING: <pregunta>]`
(English token, Spanish question). The discrimination rule, authored once in
`pending-protocol.md` and linked from each generative body:
- **Mark `[PENDING: …]` and continue** when the brief merely *lacks* a field.
- **Stop and ask the author** only when proceeding would require inventing *load-bearing
  canon* that contradicts or cannot be derived from existing artifacts (e.g. a
  protagonist's core motivation).
- When a `[PENDING: …]` lands in a *string-typed* YAML frontmatter field (e.g. a
  character `name`), it MUST be quoted: `name: "[PENDING: …]"` — bare `[…]` parses as a
  YAML list and the indexer discards the file.

**Rationale**: This is exactly the contract the iteration-7 molds already encode (see
`character.md.tmpl`); the commands must agree with the molds, the sentinel sweep, and the
checklist command on one marker. Centralizing avoids drift.

## R4 — Description authoring for cross-language activation precision (US3, SC-003)

**Decision**: Each `description` (< 1024 chars) is intent-led and bilingual, and carries
explicit **disambiguation** against its closest sibling:
- `constitution` invites tone/voice/pact/red-lines intent; states it is the *setup* step
  **before** the bible (so "define el tono" does not fire `bible`).
- `bible` invites character/setting/location *sheets*; states it runs *after* the
  constitution.
- `analyze` = *pre-draft* cross-artifact consistency (constitution+bible+outline+scenes);
  `continuity` = *post-draft* manuscript-vs-bible. Each names its phase to repel the other.
- `clarify` = open questions to resolve next; `checklist` = whether *one named artifact* is
  complete. Each names its distinct question.

Every description embeds Spanish **and** English trigger phrases so implicit activation
fires regardless of the author's request language (bilingual convention; user is ES/EN).

**Rationale**: US3 makes activation precision a first-class quality bar. The discriminating
signal lives entirely in the description; sibling pairs are the documented failure mode, so
each description is written to win its intent and lose its sibling's.

**Validation**: SC-003 is a hand-run A/B battery (≥4 scenarios × ES+EN = 8 phrasings),
backstopped by `test_command_activation.py` asserting each description contains both an
ES and an EN trigger and the sibling-disambiguating keyword.

## R5 — No `handoffs:` / `scripts:` in source (FR-005, FR-006)

**Decision**: Source frontmatter carries only `name` + `description` (plus other
agentskills.io-valid keys if genuinely needed). The § 10.1 `handoffs` block and the Spec
Kit `scripts` token are **excluded**; "next step" suggestions (e.g. "run `bookwright-clarify`
before `bookwright-bible`") appear as **body prose**, and CLI calls are written inline as
`bookwright <sub> --json` in the procedure.

**Rationale**: Confirmed in `/speckit-clarify` (Session 2026-06-01). Sources stay
integration-agnostic; agent-specific affordances are injected during iteration-9
materialization (Constitution V–VII). The § 10.1 `handoffs` is illustrative of the eventual
materialized skill, not a source requirement.

## R6 — Where the validation suite lives

**Decision**: Extend `tests/resources/` (iteration-7's template-validation home). Add a
`COMMANDS_DIR` constant + command/reference enumerators to the existing `helpers.py`, and
add five focused `test_command_*.py` modules. Reuse the shipped
`bookwright.io.frontmatter.parse_frontmatter` to read frontmatter (so tests assert the live
reader contract, never a re-implementation).

**Rationale**: Command sources are packaged resources, same as the iteration-7 templates;
co-locating keeps one resource-validation suite and reuses its enumerator/`read_text`
pattern. No new top-level test package needed.
