# Implementation Plan: The prose seam recognizes the leading Spanish dialogue dash

**Branch**: `041-prose-dialogue-dash` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/041-prose-dialogue-dash/spec.md`

## Summary

In Spanish prose, dialogue opens with the typographic em dash `—` (U+2014; the en
dash `–`, U+2013, is a documented variant). The single prose seam
(`src/bookwright/io/prose.py`, iteration 039) normalizes ASCII block markers — ATX
heading `#{1,6}␠`, bullet/blockquote `[-*+>]␠` — but **not** the dialogue dash. As a
result `character_presence` sees `—Esto es el porvenir` with the `—` still glued to
`Esto`: the word is not at offset 0, so `_is_sentence_initial` returns `False` and
`Esto` (a demonstrative, not a proper noun) is reported as an unknown proper noun. In
a real, dialogue-dominated novel this fires one spurious `warning` on the first
capitalized word of **every** dialogue line, drowning the genuine findings (DEBT-009,
detected by the `tiny-historical` dogfood after `v0.5.0`).

**Technical approach** (the issue-#1 doctrine: close the class at the *seam*, never
patch the validator): add a `_DIALOGUE_MARKER = re.compile(r"^\s*[—–]\s*")` to
`io/prose.py` and strip it inside the **existing** iterative `_normalize` loop, one
pass per marker (`sub(count=1)`), so only the **leading** dash is removed and internal
incise dashes (`—dijo Arnela—`) stay intact. After normalization the first content
word lands at offset 0 and inherits `character_presence`'s **existing**
sentence-initial exemption — exactly as DEBT-008 (iteration 038) reused it for the ATX
heading marker. **No validator is touched.** Verified empirically: today the seam
yields `[Real, Fábrica, Paños, Esto]` on the `tiny-historical` manuscript; with the
marker it yields `[Real, Fábrica, Paños]` — one fewer (`Esto`), the spurious
dialogue-dash flag and nothing else.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: stdlib only for this change — `re` + `dataclasses`, already
imported by `io/prose.py`. **No** new third-party dependency, **no** Markdown
parser/AST (FR-006, Constitution II).

**Storage**: N/A — this is a pure in-memory line-normalization change; the graph cache
and all on-disk formats are unchanged.

**Testing**: `pytest` (`tests/io/test_prose.py` for the seam contract;
`tests/validation/test_character_presence.py` for the both-directions generalization;
`tests/e2e/test_orchestration_workflow.py` consumes the `tiny-historical` oracle).

**Target Platform**: CLI / library (`src/bookwright/`), platform-agnostic.

**Project Type**: Single project (src-layout, Constitution III).

**Performance Goals**: N/A — one extra anchored `re.match`/`sub` per line, negligible.

**Constraints**: Every changed/new file ≤ 500 lines (Constitution IV);
`io/prose.py` is 81 lines and grows by ~6. The CI gate is unchanged (only
`error`-severity findings break CI; this change removes a `warning`).

**Scale/Scope**: One marker added to one module; one seam-contract test row group; one
validator-level generalization test; one fixture oracle count corrected downward
(`tiny-historical/expected-status.md`, `warning: 5 → 4`); one `DEBT.md` edit (remove
DEBT-009; DEBT-011 already recorded by the spec audit). No validator source edited.

## Constitution Check

*GATE: must pass before Phase 0 and re-checked after Phase 1.*

| Principle | Status | Justification |
|---|---|---|
| I. Plain text as source of truth | ✅ PASS | Pure-text prose normalization; graph is still a derived cache. DEBT-009 removal stays in plain-text `DEBT.md`. |
| II. Modern Python stack | ✅ PASS | stdlib `re` only — no new dependency, no Markdown library (FR-006). |
| III. src-layout | ✅ PASS | Change lives in `src/bookwright/io/prose.py`. |
| IV. Modular command surface (≤ 500 lines) | ✅ PASS | `io/prose.py` 81 → ~87 lines; no new CLI subcommand. |
| V. Plugin integrations | ✅ N/A | No integration change. |
| VI. Agent Skills only | ✅ N/A | No command/skill materialization. |
| VII. agentskills.io compliance | ✅ N/A | No skill front-matter touched. |
| VIII. Test discipline (≥ 80 %) | ✅ PASS | New seam-contract rows + a validator-level both-directions test (FR-009); coverage stays ≥ 80 %. |
| IX. JSON-over-stdout | ✅ PASS | Envelope shape unchanged; one fewer `warning` violation in `tiny-historical`'s output. |
| X. Design document axioms / frozen ontology | ✅ PASS | Prose-level change; `triples=()`, no class added, `golem.ttl`/`CLASS_IRI` untouched (FR-012). |

**Result: PASS — no violations, Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/041-prose-dialogue-dash/
├── spec.md              # Feature spec (already written + hardened)
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (marker shape, ordering, parity)
├── data-model.md        # Phase 1 — the ProseLine / leading-marker model delta
├── quickstart.md        # Phase 1 — runnable validation scenarios
├── contracts/
│   └── dialogue-marker.md   # Phase 1 — the normalization contract addition (tables)
└── tasks.md             # Phase 2 — created by /speckit-tasks (NOT here)
```

### Source Code (repository root)

```text
src/bookwright/io/prose.py            # ← THE ONLY source edit: + _DIALOGUE_MARKER + one
                                      #   elif branch in _normalize; docstring updated
tests/io/test_prose.py                # ← new C2 rows: leading dash (em/en), glued/spaced,
                                      #   indented, internal-dash intact, dash-only, composed
tests/validation/test_character_presence.py  # ← new both-directions test (FR-009): leading
                                      #   `—Esto` not flagged; mid-line `—… Quirón —dijo.` flagged
tests/fixtures/tiny-historical/expected-status.md  # ← validation.counts.warning 5 → 4
                                      #   (fixture manuscript UNTOUCHED) + its prose notes
DEBT.md                               # ← remove DEBT-009 (DEBT-011 already recorded)
```

**Structure Decision**: Single project, src-layout. The change is confined to the
shared seam `io/prose.py`; **no validator file is edited** (SC-004) — the criterion
that proves the surface-marker class is closed at the root per issue #1, not patched
per-instance.

## Phase 0 — Research

See [research.md](./research.md). All decisions resolved (no NEEDS CLARIFICATION):

- **D1 — marker shape**: `^\s*[—–]\s*` — anchored at line start, optional leading
  whitespace (mirrors `_BULLET_MARKER`), optional **trailing** whitespace (`\s*`, not
  `\s+`) because the Spanish convention glues the dash to the first word (`—Esto`); a
  leading typographic dash is unambiguous so no bullet-vs-emphasis disambiguation is
  needed.
- **D2 — home of the fix**: the seam (`_normalize`), inside the existing strip loop,
  as a third `elif` branch — *not* `_is_sentence_initial`. This is the load-bearing
  issue-#1 decision: any prose validator benefits automatically and no validator
  couples to a surface marker.
- **D3 — code points**: em dash `—` (U+2014) and en dash `–` (U+2013) only. The ASCII
  hyphen bullet `- ` stays owned by `_BULLET_MARKER`; the horizontal bar `―` (U+2015)
  and leading quotes (`«`/`"`/`'`) are the **same class** but a distinct design and are
  deferred as DEBT-011 (already recorded — not silently dropped).
- **D4 — parity**: verified empirically (script run during planning) — the only
  pinned oracle that shifts is `tiny-historical/expected-status.md` (`warning: 5 → 4`);
  `tiny-novel`/`tiny-memoir` carry leading-dash dialogue but their tests assert only
  `error == 0` (warnings tolerated, no pinned count), so they need no edit.

## Phase 1 — Design & Contracts

- [data-model.md](./data-model.md) — `ProseLine` is unchanged in shape; the new
  **leading dialogue marker** joins heading/bullet as a structural-marker class the
  `normalized` projection removes. State/loop-termination invariants restated.
- [contracts/dialogue-marker.md](./contracts/dialogue-marker.md) — the normalization
  contract table: input line → `normalized`, covering glued/spaced/indented dashes,
  internal-dash preservation, dash-only → empty, and composition with heading/bullet.
- [quickstart.md](./quickstart.md) — runnable scenarios: the seam table assertion, the
  `character_presence` both-directions check, the full-suite empirical parity run, and
  the four gates.

**Agent context update**: the managed `<!-- SPECKIT … -->` block in `CLAUDE.md` is
repointed to this plan (done as the final planning step).

## Complexity Tracking

> No Constitution violations — section intentionally empty.
