# Phase 0 Research: `character_presence` heading-marker normalization

All Technical Context items are known (a single-module prose-validator patch with
no new dependency). The research below records the four design decisions that
materially shape the implementation.

## D1 — Reuse the existing sentence-initial exemption instead of adding a rule

- **Decision**: Strip a leading ATX heading marker from the line **before** the
  existing `_CANDIDATE` scan, so the heading's first content word lands at offset
  0 and is exempted by the *existing* empty-prefix branch of `_is_sentence_initial`
  (`prefix = line[:start].rstrip(); if not prefix: return True`). Do **not** add a
  parallel "heading-initial" predicate.
- **Rationale**: FR-001 and the spec Assumptions require the first heading word to
  receive "the same exemption a capitalized word at the start of a line already
  receives." Removing the marker restores the title to ordinary prose whose first
  word is line-initial — one code path, minimal new behavior, smallest surface
  area. The remainder of the line is unchanged, so FR-002 (a real name later in the
  title is still flagged) falls out for free: after stripping `# ` from
  `# La caída de Elena`, `Elena`'s prefix is `La caída de ` whose last non-space
  char is `e` ∉ `_SENTENCE_END`, so it is not exempt and fires.
- **Alternatives considered**: (a) Add an `_is_heading_initial(line, start)`
  predicate alongside `_is_sentence_initial` — rejected: a second rule to keep in
  sync, and it would also have to special-case "first word only," duplicating logic
  the empty-prefix branch already gives once the marker is gone. (b) Full markdown
  parse / NER — explicitly Out of Scope.

## D2 — Marker shape: `^#{1,6}\s+`, anchored, no leading whitespace

- **Decision**: Recognize the marker with `_HEADING_MARKER = re.compile(r"^#{1,6}\s+")`
  and strip the matched span (the hashes **and** the whitespace run that follows)
  so the first content word becomes offset 0.
- **Rationale**: This is the CommonMark ATX opening form and exactly what the
  `bookwright` scaffold emits and authors write. Anchored at `^` with **no**
  leading-whitespace allowance, matching FR-001 ("begins with one to six `#`")
  and the spec Edge Cases ("the recognized form is a line that *starts* with one to
  six `#`"; "Leading whitespace before the marker: indented heading-like lines are
  not in scope"). Consuming the trailing `\s+` (one-or-more) tolerates the multiple
  spaces/tab a writer may type and guarantees the next word is at offset 0.
  - **Divergence from the `/speckit-plan` hint, recorded deliberately**: the hint
    wrote `^\s*#{1,6}\s+` (a leading `\s*`). The spec's Edge Cases section is the
    authority and puts **indented** heading-like lines explicitly out of scope, so
    the leading `\s*` is dropped. Allowing it would strip the marker from an
    indented `   # Foo` and *change* that line's behavior (today its `Foo` is
    flagged because the rstripped prefix ends in `#`), which the spec says must not
    happen ("analyzed exactly as today"). Anchoring at `^#{1,6}` keeps the indented
    direction byte-identical.
- **Boundary behaviors (all "no change vs. today", per spec Edge Cases)**:
  - `#Capítulo` (no space) — `\s+` fails, no match, marker not stripped, analyzed
    as today.
  - `####### Foo` (seven `#`) — `#{1,6}` matches only the first six, but the seventh
    char is `#`, not whitespace, so `\s+` fails → no match → not an ATX heading →
    analyzed as today. (Greedy `#{1,6}` then a required `\s+` correctly rejects 7+.)
  - `# Capítulo 1 #` (closing-hash ATX) — opening marker stripped; trailing ` #`
    touches no capitalized candidate, so behavior is unchanged.

## D3 — Apply at the line-scan seam in `_unknown_mentions` only; locator unchanged

- **Decision**: Compute a `scan` string (`line` with the marker removed, else
  `line` unchanged) inside the existing `for lineno, line in enumerate(...)` loop,
  then run `_CANDIDATE.finditer(scan)` and pass `scan` to `_is_sentence_initial`.
  The `lineno` used in the `relpath:line` locator is untouched.
- **Rationale**: FR-005 — the unknown-mention locator is `relpath:line` (no
  column), and `lineno` comes from `enumerate`, not from the match offset, so
  stripping the marker cannot shift a reported position. Matching and the
  sentence-initial check must read the **same** string, hence both use `scan`.
- **Inverse direction left alone (FR-004)**: `_orphans` / `_is_mentioned` run a
  whole-text word-boundary regex (`\bName\b`) over the raw manuscript text. A
  heading marker is never adjacent to a word character in a way that would break
  `\b`, and a roster name appearing only inside a heading is still "mentioned." So
  the orphan (bible→manuscript, `error`) direction needs no change and gets none.

## D4 — Recognizer stays local; no shared utility; constitution template unchanged

- **Decision**: Keep `_HEADING_MARKER` and the strip helper module-private in
  `character_presence.py`. Do not extract a shared markdown-heading utility, and do
  not touch any other validator or the scaffold.
- **Rationale**: No other current consumer needs heading-marker stripping; a shared
  helper would be speculative plumbing (Scope & Release Discipline; zero-debt
  doctrine §2). This mirrors iteration 037, which kept its `_PENDING_ONLY`
  recognizer local to `focalization.py`.
- **Alternatives considered**: a shared `bookwright.io`/markdown helper — rejected
  as premature generalization with a single caller.

## Resolved unknowns

No `NEEDS CLARIFICATION` remained from the spec. The one open test-design choice
(synthetic in-test manuscript vs. live-scaffold binding) was resolved in the spec's
Clarifications (2026-06-21): **synthetic in-test manuscript**, because the scaffold
ships an empty `manuscript/` (`.gitkeep` only) with no heading-bearing file to bind
to.
