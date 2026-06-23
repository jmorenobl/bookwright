# Implementation Plan: Soft warning for unrecognized Propp/Greimas vocabulary terms

**Branch**: `047-vocab-term-warning` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/047-vocab-term-warning/spec.md`

## Summary

When a project activates a closed narrative vocabulary (`[vocabularies] active`,
e.g. `propp`), `graph build` types each authored term against it: a match gets a
`crm:P2_has_type` edge, a non-match is minted **untyped, in silence**. This
iteration (v0.5.x patch track, issue #1 **track B — pulido determinista**, closes
**DEBT-016**) makes that non-match emit a **non-fatal `graph build` warning** that
names the file, field, offending term, and active vocabulary, and whose
human-facing render **enumerates the valid terms** — the same enumerated-feedback
spirit as research's *fatal* unknown-vocabulary rejection. The node is still
ingested unchanged (closed for *typing*, open for *authoring*); the build neither
aborts nor changes its exit code.

**Technical approach**: add one soft-warning channel — `MapResult.untyped_vocab_terms`
carrying `UntypedVocabTerm{path, field, term, vocabulary}` records — populated at
the **two** silent `resolve()→None`-then-mint typing sites (Propp `functions:` in
`io/outline.py:_mint_functions`; Greimas `narrative_roles:` in
`io/_bible_builders.py:_build_character`), surfaced by `_graph.py` into
`BuildReport` and rendered by `commands/graph/build.py`, exactly as the sibling
`unknown_keys` / `unresolved_references` / `research_warnings` channels are. The
valid-term enumeration is exposed by a new `VocabularyIndex.terms` (the sorted,
unique `rdfs:label` set), derived from the `vocabulary` field at render time — never
denormalized into the structured record (FR-002).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II) — `from __future__ import annotations`.

**Primary Dependencies**: `rdflib` (already loads the vocabulary TTL), `pydantic` v2
(the `BuildReport` / channel models). **No new runtime dependency** (FR-015,
Constitution II).

**Storage**: plain-text bible/outline cards → derived `bible/graph.ttl` cache. The
warning is a build-report channel only; **no triple is added or removed** (FR-003,
FR-014, SC-003).

**Testing**: `pytest` (`uv run pytest`), full suite, ≥ 80 % coverage. Oracles are
empirical (build a fixture, assert the envelope + graph + determinism).

**Target Platform**: CLI, local.

**Project Type**: single project (src-layout `src/bookwright/`, `tests/` at root).

**Performance Goals**: N/A — one extra dict lookup + list append per authored term;
`load_vocabulary` is already `@cache`d.

**Constraints**: every changed file ≤ 500 lines (FR-015); frozen ontology
(`golem.ttl`, `propp.ttl`, `greimas.ttl`) untouched (FR-014, Constitution X); no
validator added/removed/modified (FR-005); validation `Severity` enum untouched, no
`info` level (FR-011); deterministic, byte-stable output (FR-016).

**Scale/Scope**: ~7 source files touched (one new ~12-line model, two ~6-line warn
branches, three one-liners, one render block) + two doc reconciliations. No new
module.

## Constitution Check

*GATE: must pass before Phase 0. Re-checked after Phase 1 design.*

| Principle | Verdict | Note |
|---|---|---|
| I — plain-text source of truth | ✅ | Warning is derived from bible/outline text; graph stays a derived cache. DEBT/design edits are plain text. |
| II — locked stack | ✅ | stdlib + existing `rdflib`/`pydantic`; no new dep. |
| IV — ≤ 500 lines / one subcommand per module | ✅ | All touched files keep headroom (largest is `outline.py` at 324). No CLI verb added. |
| V — plugin integrations, no monolith dispatcher | ✅ | Untouched. |
| VI/VII — Agent Skills only, agentskills limits | ✅ | Untouched. |
| VIII — test discipline ≥ 80 % | ✅ | New oracles cover both typing sites, determinism, no-vocab non-regression, exit code. |
| IX — single `--json` error envelope | ✅ | No new error type; this is a *success-envelope soft channel*, sibling of `unknown_keys`. The `BuildReport.to_json()` contract gains one additive key. |
| X — frozen 17-class ontology | ✅ | No class, no `.ttl` term added; the feature only *warns* about a term that matched nothing. |
| Scope discipline | ✅ | Closes a recorded, dogfood-reported debt (DEBT-016) with a decided design; no speculative plumbing. |

**No violations — Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/047-vocab-term-warning/
├── spec.md              # input
├── plan.md              # this file
├── research.md          # Phase 0 — decisions (enumeration set, render coupling, sweep)
├── data-model.md        # Phase 1 — UntypedVocabTerm, channel, VocabularyIndex.terms
├── contracts/
│   └── graph-build-envelope.md   # the additive `untyped_vocab_terms` envelope key
├── quickstart.md        # Phase 1 — runnable validation walkthrough
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/io/
├── report.py            # + UntypedVocabTerm model; + BuildReport.untyped_vocab_terms field + to_json() key
├── vocabularies.py      # + VocabularyIndex.terms (sorted unique rdfs:label); collect labels in _index_turtle
├── _bible_builders.py   # + MapResult.untyped_vocab_terms; thread relpath+result into _build_character; Greimas warn branch
├── bible.py             # character builder lambda passes rp + ctx.result to _build_character
└── outline.py           # _mint_functions: Propp warn branch on resolve()→None

src/bookwright/commands/
├── _graph.py            # BuildReport(..., untyped_vocab_terms=tuple(result.untyped_vocab_terms))
└── graph/build.py       # human render: one line per warning + valid-terms enumeration per vocabulary

bookwright-design.md     # § 4.4 fatal-vs-warning principle; reconcile § 13.5 move-3 item 3 → shipped (contract-before-code)
DEBT.md                  # remove DEBT-016; reconcile track-B index line

tests/                   # io + commands oracles (Phase 2 tasks)
```

**Structure Decision**: single project, existing layers only. The change rides the
established soft-warning channel pattern (`MapResult` accumulates report models;
`_graph.py` copies them into `BuildReport`; `build.py` renders them) — no new
module, no new seam.

## Design decisions (Phase 0 summary — full rationale in `research.md`)

1. **Channel shape — direct report model in `MapResult`.** Follow the
   `unknown_keys` / `unresolved_references` precedent (the report model lives
   directly in `MapResult`), **not** the `research_warnings` translate-at-`_graph`
   precedent. `UntypedVocabTerm{path, field, term, vocabulary}` is defined in
   `io/report.py`, appended at the typing sites, and copied verbatim by `_graph.py`.
   Fewer moving parts; `field` is `functions`/`narrative_roles`, `term` is the
   authored spelling, `vocabulary` is `propp`/`greimas`. (FR-006, Key Entities.)

2. **Valid-term enumeration is render-derived, never denormalized (FR-002).**
   `VocabularyIndex` gains `terms: tuple[str, ...]` = `tuple(sorted(set(labels)))`
   collected in `_index_turtle` (all `rdfs:label`s, ES+EN, deduplicated, **sorted**
   → byte-stable, language-agnostic, keeps the loader manifest-free). The human
   render in `build.py` maps each distinct warning `vocabulary` →
   `load_vocabulary(vocabulary).terms` (already `@cache`d) and prints the
   enumeration **once per vocabulary block**, so a 31/62-term list is not repeated
   per offending term. The structured envelope record stays minimal — exactly the
   `ResearchTargetWarning`-stores-`{path,field,name}`-but-renders-"not in bible"
   pattern. (FR-002, FR-016.)

3. **Class sweep, two sites, mint-point emission (FR-007).**
   - Propp `functions:` — `outline.py:_mint_functions`, inside `if function is None:`
     (first introduction), warn when `ctx.propp is not None and type_uri is None`.
     Inputs there are already sluggable `(slug, raw)` pairs (`_distinct_slugs` drops
     unsluggable up front), so `resolve(raw) is None` is a genuine no-match — the
     blank-term edge case needs no extra guard. Dedup across cards ⇒ warned once.
   - Greimas `narrative_roles:` — `_bible_builders.py:_build_character`, in the
     existing `if greimas is not None:` loop, add an `else:` warn branch. Guard
     unsluggable labels first (`try make_slug(label) except EmptySlugError: continue`)
     so a blank role — which mints no warnable node — produces no warning (edge
     case), mirroring the Propp path. Thread `relpath` + `result` in via the
     existing `bible.py` lambda (`meta, rp` and `ctx` already in scope).

4. **Untouched siblings (FR-008).** The outline-unit `roles:` → character-role
   resolution (`_resolve_roles`) already emits `UnresolvedReference`; it is a
   different resolution (edge to a character role node, not Greimas actant typing)
   and is left exactly as-is — no double-handling.

5. **Determinism without a new sort (FR-016).** Warning entries inherit the
   sibling channels' sorted-glob file order (bible character pass first, then
   outline pass); within a file/field they follow authored YAML list order (the
   front-matter parser already preserves it — the clarified lowest-debt choice, no
   second sort key). The only nondeterminism risk — the vocabulary label store's
   incidental order — is removed by sorting `terms` once at index build.

## Contract-before-code (Phase 1 ordering)

Per the zero-debt doctrine, the canonical docs change **before** the code diverges:

- `bookwright-design.md` **§ 4.4** (Vocabularios controlados) gains the
  fatal-vs-warning principle paragraph (FR-012): research's invalid value is fatal
  because it breaks a downstream gate (`reliability` → `factual_anchor`); an absent
  `P2_has_type` is descriptive metadata that breaks nothing, so an unrecognized
  Propp/Greimas term only warns and the node is still ingested untyped.
- `bookwright-design.md` **§ 13.5 move-3 item 3** is reconciled from *planned* to
  *shipped in iteration 047*.
- `DEBT.md` removes the **DEBT-016** entry and reconciles the **track-B index**
  line (DEBT-015, ~~DEBT-016~~, DEBT-017) (FR-013).

## Phase 1 outputs

- `data-model.md` — the `UntypedVocabTerm` record, the `MapResult` /
  `BuildReport` channel additions, and the `VocabularyIndex.terms` enumerator, with
  field semantics and the determinism contract.
- `contracts/graph-build-envelope.md` — the additive `untyped_vocab_terms` key in
  the `graph build --json` success envelope (record schema, exit-code invariance,
  no-vocab byte-stability) and the human-render contract.
- `quickstart.md` — a runnable walkthrough proving US1/US2/US3 against a fixture.

## Complexity Tracking

No Constitution violations — section intentionally empty.
