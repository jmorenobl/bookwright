# Phase 1 Data Model: `focalization` markdown-prefixed voice declaration

This feature adds **no** new persisted entity and **no** GOLEM concept (Principle
X). The only structured object involved is the in-memory parse result, which is
**unchanged**. This file documents the recognition surface and the
already-existing parse model for completeness.

## Existing entity (unchanged): `_Declaration`

`focalization.py` `@dataclass(frozen=True) _Declaration`:

| Field   | Type           | Meaning                                              |
|---------|----------------|------------------------------------------------------|
| person  | `"first" \| "third" \| None` | declared grammatical person (None ⇒ no rule fires) |
| limited | `bool`         | whether "limited/limitada" appears in the body       |
| focal   | `str \| None`  | a bible character named in the body, if any          |

**No field is added, removed, or retyped.** The body-extraction logic
(`_THIRD`, `_FIRST`, `_LIMITED`, the focal-name scan) is frozen. The *only*
change is which surface lines are recognized as carrying a declaration before
the body is extracted.

## Recognition surface (the behavioral delta)

The declaration line is recognized when, after a bounded normalization, it
matches the label-and-body shape. Normalization tolerates, around the existing
labels `Voz narrativa` / `Narrative voice` (case-insensitive, bilingual):

| Markup element        | Tolerated set            | Position                              | Notes |
|-----------------------|--------------------------|---------------------------------------|-------|
| Leading list/quote marker | `-`, `*`, `+`, `>`   | one, line-leading, then whitespace    | FR-001 |
| Emphasis run          | `*`, `**`, `_`           | around the label, each side independently | FR-002; no balance check |
| Colon                 | `:`                      | after closing emphasis run or bare label | FR-003 |
| Whitespace            | spaces / indentation     | leading + between marker and label    | unchanged |

Recognition result invariants (the contract `/contracts/` formalizes):

- **R1 (parity)**: For body `B`, every recognized surface form
  (`Voz narrativa: B`, `- **Voz narrativa**: B`, `*Voz narrativa*: B`,
  `> _Voz narrativa_: B`, …) yields the **same** `_Declaration` as the bare
  `Voz narrativa: B`.
- **R2 (no false widening)**: A line not containing the literal label (after
  normalization) yields no match; no new synonym is introduced.
- **R3 (first match wins)**: When several candidate lines exist, the first
  recognized line in document order is used (unchanged behavior).
- **R4 (None-person edge)**: A recognized line whose body names no person
  (e.g. the scaffold's `[PENDING: …]`) yields `person=None` → zero findings,
  identical to today's bare-form behavior.

## Validation rules (unchanged — FR-006)

Listed to make the freeze explicit; none of these change:

1. **First-person-outside-dialogue** (third person declared): a first-person
   marker (`yo|nosotros|nosotras|i|we`) on a non-dialogue line ⇒ one
   `warning` per file (first break cited).
2. **Head-hopping / interiority** (third-person-limited): an interiority verb
   attached to a **non-focal** bible character ⇒ one `warning` per non-focal
   character.

Dialogue-exemption prefixes, the pronoun/interiority lexicons, the
person/limited keywords, and the one-finding-per-file behavior are all frozen.
Severity stays `warning` (so `validate` exit codes and the `error` tally are
unaffected — only the `warning` tally moves).
