# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state: v0.5.1 released (2026-06-22, the first post-`v0.5.0` patch, iteration 041, DEBT-009 — the single prose seam (`src/bookwright/io/prose.py`) now also strips the leading Spanish dialogue dash `—`/`–`/`―` so `character_presence` stops mis-flagging the first spoken word of every dialogue line as an unbound proper noun; the class is closed at the seam, not the validator — one `_normalize` branch, zero validator edits (issue #1 doctrine, the same mechanism 038 used for ATX headings). v0.5.0 (2026-06-22, the validation-robustness minor, issue #1) shipped 039+040 at once at the close of the milestone: a single Markdown-aware prose/structure seam now backs every prose validator, closing the surface-coupling *class* behind DEBT-004/007/008 at the root (039), and a validator's per-run verdict is now tri-valued — `evaluated` / `not-evaluated(reason)` raised as `NotEvaluated` and surfaced in an additive `not_evaluated[]` channel — so `[]` stops reading as "clean" when it meant "couldn't look" (040))

Five milestones are **fully implemented and released**: `v0.1.0` (2026-06-03,
the v0 toolkit, iterations 1–11), `v0.2.0` (2026-06-05, the M4 research &
verification system, iterations 12–18), `v0.3.0` (2026-06-13, the M5 context
orchestration system, iterations 19–23), the **v0.3.x hardening track**
(iterations 024–027, shipped as successive patches `v0.3.1`…`v0.3.4`, the last on
2026-06-15) and `v0.4.0` (2026-06-21, the narrative-structure layer:
Propp/Greimas G7/G9/G10 + `outline/` ingestion, iterations 028–032), the
`v0.4.1` hardening patch (2026-06-21, iteration 033: remove the dead
`NarrativeRole` concept + close the carrier-IRI parity loophole, DEBT-001) and
the `v0.4.2` hardening patch (2026-06-21, iteration 034: make the `focalization`
validator tolerate the markdown-prefixed `- **Voz narrativa**: …` declaration its
own scaffold emits, waking a check that had been silently dormant, DEBT-004) and
the `v0.4.3` hardening patch (2026-06-21, iteration 035: emit `rdfs:label` on
narrative units/functions and materialize a queryable `bw:sequenceOrdinal` so the
v0.4 narrative layer is searchable by content and walkable in declared order under
unordered RDF, DEBT-005) and the `v0.4.4` hardening patch (2026-06-21, iteration
036: make research-source load errors actionable — enumerate the closed
`type`/`reliability` vocabulary in the message and prefix every per-source fault
with a single locator (`name` or 1-based `#index`), the `--json` envelope
byte-unchanged, DEBT-006; this release also folds in the EUPL-1.2 relicense + GOLEM
CC BY 4.0 attribution that had accumulated on `main`) and the `v0.4.5` hardening
patch (2026-06-21, iteration 037: make the `focalization` validator treat a body
that is *solely* an unanswered `[PENDING: …]` narrative-voice placeholder as no
declaration — a fresh `bookwright init` constitution carries
`- **Voz narrativa**: [PENDING: …(primera/tercera persona, omnisciente/limitada)?]`,
whose placeholder text literally contains "tercera persona"/"limitada" and so
parsed as a real declaration, flooding head-hopping warnings on the first
interiority verb; one anchored `_PENDING_ONLY` guard routes it into the existing
"no declaration → zero findings" path, DEBT-007) and the `v0.4.6` hardening patch
(2026-06-22, iteration 038: make the `character_presence` validator strip a leading
ATX heading marker (`#{1,6}␠`) before its proper-noun heuristic, so a chapter
heading like `# Capítulo 1` no longer flags `Capítulo` as an unbound proper noun —
the heading's first word lands at offset 0 and inherits the existing
sentence-initial exemption, while a real off-roster name later in the title still
fires, DEBT-008). All
of it is on `main` (tagged) with a real `src/bookwright/` package, ~200 Python
files, the full test suite, docs, and CI gates green. There is **no active
iteration branch**. With v0.4 the ingestion-parity north star is reached.

A **dogfooding exercise** (a real book run end-to-end, 2026-06-21) surfaced
actionable findings — a silently-disabled validator, a measured structural-recall
gap, blinding error messages, a placeholder-mis-parse that flooded spurious
warnings, and a heading-marker blind spot that mis-flagged every chapter title —
recorded as **DEBT-004/005/006/007/008** and shipped as the **`v0.4.x`
post-dogfooding hardening track** (iterations 034–038, one patch each:
`v0.4.2`/`v0.4.3`/`v0.4.4`/`v0.4.5`/`v0.4.6`). All five are now closed (034, `v0.4.2`,
DEBT-004; 035, `v0.4.3`, DEBT-005; 036, `v0.4.4`, DEBT-006; 037, `v0.4.5`,
DEBT-007; 038, `v0.4.6`, DEBT-008) — the track is **complete** and `DEBT.md` carries no open debt. The
ready-to-run workflow commands and the
per-iteration debt-cancellation/release cycle live in
`bookwright-implementation-plan.md`.

The milestone **`v0.5.0` — validation robustness** (issue #1) is **released**
(2026-06-22, tagged): a **minor** that shipped its two ordered iterations at
once at the close (M4→`v0.2.0`-style). The v0.4.x dogfooding made plain that
DEBT-004/007/008 were **one class** of defect patched instance-by-instance (each
validator re-implementing how to "see past the markdown the tool itself emits"),
not three bugs. Issue #1 decided to **close the class at the root** rather than
keep playing whack-a-mole. **039 — single prose/structure seam** landed a
markdown-aware view in `io/prose.py` all prose validators consume, deleting the
per-validator strippers and closing the surface-coupling facet. **040 —
tri-valued result** made a validator's per-run verdict `evaluated` /
`not-evaluated(reason)` (signalled by raising `NotEvaluated`, surfaced in an
additive `not_evaluated[]` channel across the `--json` envelope, the human
report, `status`'s `state.validation`, and `next_actions`), so `[]` stops
reading as "clean" when it meant "couldn't look" — closing the false-confidence
facet. GREEN is now the single documented predicate
`status == "ok" AND not_evaluated == []`; the CI gate is unchanged (only
`error` findings gate). Both iterations are **merged and released**. The LLM
**semantic-judgment** escalation (issue #1 move 3) is parked in the demand-pulled
horizon.

The **`v0.5.x` post-dogfooding track** then continues the issue #1 doctrine
against defects the `tiny-historical` dogfood of the released `v0.5.0` surfaced.
Iteration 041 shipped as the **`v0.5.1`** patch (2026-06-22, DEBT-009): the
single prose seam (`io/prose.py`) now strips the leading Spanish dialogue dash
(`—` U+2014 / `–` U+2013 / `―` U+2015) inside its existing `_normalize` loop as a
third `elif` branch (`_DIALOGUE_MARKER = ^\s*[—–―]\s*`, `sub(count=1)`), so
`character_presence` stops emitting one spurious unbound-proper-noun `warning` on
the first spoken word of every dialogue line (`—Esto` → `Esto` at offset 0,
inheriting the existing sentence-initial exemption — the same mechanism 038 used
for ATX headings). Only the leading dash is removed (internal incise dashes
`—dijo Arnela—` survive); **no validator is edited** (the load-bearing issue #1
"close the class at the seam" criterion); the only pinned oracle that shifts is
`tiny-historical/expected-status.md` (`warning 5 → 4`, manuscript untouched, as
038 did `6 → 5`). The audit recorded **DEBT-011** (the genuinely-distinct
*paired* leading-quote markers `«`/`"`/`'`) for a future iteration; the
horizontal bar `―` U+2015, being the same glued dash class **and** design, was
swept here. The next planned patch is iteration 042 (`v0.5.2`, DEBT-010 — cross
the proper-noun roster against settings/locations/objects, not just characters).
The remaining longer-horizon work — semantic judgment in validation, vector
search (ChromaDB over rdflib) and export — is deferred to an unversioned, demand-pulled
horizon: each ships only when its activation condition is met, not on a pre-assigned
version — see `bookwright-roadmap.md`.

The canonical references:

- `bookwright-design.md` (Spanish, ~74 KB) — canonical design spec. Section
  numbering is load-bearing; specs and iteration prompts cite it as
  `bookwright-design.md § N.M`. Section 16 lists axiomatic decisions that
  MUST NOT be reopened. § 20 covers the research system (shipped in v0.2);
  § 21 the context orchestration (shipped in v0.3).
- `bookwright-roadmap.md` (Spanish) — the **durable** intent across versions
  (the *what* and *why*): the version line (v0.3.x → v0.4 → v0.4.x → v0.5.0 →
  demand-pulled horizon), the
  ingestion-parity north star, the cancelled list. Unlike the plan, it is **not**
  emptied each milestone. A guide, not a commitment.
- `bookwright-implementation-plan.md` (Spanish) — ordered iteration plan for the
  **current milestone only** (now the v0.3.x hardening track); emptied of
  delivered work each milestone. § 2 has the dependency map; § 3+ have one
  ready-to-paste `/speckit-specify` prompt per iteration.
- `.specify/memory/constitution.md` — ratified, currently **v1.4.0**.
  **Binding** on every PR. Three principles are explicitly NON-NEGOTIABLE:
  plain-text source of truth (I), Agent Skills only — no legacy `commands/`
  directories (VI), and test discipline with ≥ 80 % coverage (VIII).
- `specs/NNN-<name>/` — per-iteration `{spec,plan,tasks}.md` (plus
  `research.md`, `data-model.md`, `contracts/`, `quickstart.md`). The
  iteration's plan is the most precise statement of what its code does.
- `.claude/skills/speckit-*` — the Spec Kit slash-command skills that drive
  the workflow.

Every feature lands through a numbered iteration, not as a freehand commit.

## Common commands

```
uv sync                          # install deps + dev group into .venv
uv run bookwright <subcommand>   # run the CLI (version | check | init | validate | graph | integration)
uv run pytest                    # full suite (excludes `manual` marker, enforces ≥80% coverage)
uv run pytest tests/golem/test_triples.py::test_name   # single test
uv run pytest -m manual          # opt-in packaged-install / subprocess smoke (slow, networked)
uv run ruff check && uv run ruff format --check
uv run mypy --strict             # files = src + tests (configured in pyproject)
```

All four gates (`ruff check`, `ruff format --check`, `mypy --strict`,
`pytest`) run in CI on every push / PR. The coverage threshold is
single-sourced in `[tool.coverage.report]` (`fail_under = 80`,
`precision = 2`) — do **not** add `--cov-fail-under` anywhere; one source, no
drift.

## Code intelligence: use codegraph first

This repo has a **codegraph** index (a local SQLite knowledge graph of every
symbol, edge, and file, kept fresh by a file watcher in `.codegraph/`, not
committed). Before grepping/reading to understand the code, query it via the
`mcp__codegraph__*` tools — it's faster and already built:

- `codegraph_context` — primary entry point for "what's the deal with area X".
- `codegraph_trace` — full call path from X to Y (follows dynamic dispatch).
- `codegraph_callers` / `codegraph_callees` / `codegraph_impact` — who calls
  what, and what a change would break.
- `codegraph_explore` / `codegraph_node` — survey or read specific symbols.

Answer architecture/trace/where-is-X questions directly with 2–3 of these
calls; fall back to raw Read/Grep only to confirm a detail codegraph missed.

## How work is done here

Built **with** Spec Kit, **for** narrative authoring. Every iteration runs
this fixed sequence — do not skip steps, do not write code outside this flow:

```
/speckit-specify <iteration prompt from bookwright-implementation-plan.md>
/speckit-clarify          # mandatory; say "no clarifications" to unblock if truly none
/speckit-plan <technical hint, usually a pointer into bookwright-design.md §X.Y>
/speckit-tasks
/speckit-analyze          # cross-artifact consistency check
/speckit-implement
```

Each iteration is a branch `NNN-<short-name>` with its own `specs/` dir. Merge
to `main` only when tests are green and `/speckit-analyze` reports no issues;
later iterations assume earlier code is on `main`. The auto-git hooks in
`.specify/extensions.yml` offer to commit between phases.

### Autonomous workflow (`bookwright-quality`)

That same sequence is packaged as a headless, zero-debt Spec Kit workflow at
`.specify/workflows/bookwright-quality/workflow.yml` (registered in
`.specify/workflows/workflow-registry.json`). It runs, unattended, `specify →
harden-spec → clarify → plan → tasks → analyze-resolve → implement → converge →
implement-remainder → review-fix → finalize`; every decision is made against the
constitution / CLAUDE.md (it never asks), and each step commits its own edits (the
auto-git hooks are unreliable in headless dispatch). The shared anti-debt rules
live once in `.specify/workflows/bookwright-quality/zero-debt-doctrine.md` (every
prompt step reads it rather than re-stating the doctrine). `converge` runs before
the final review so the work it appends gets built (`implement-remainder`) and
reviewed; `review-fix` is the last quality net over all code and pulls an
independent adversarial second opinion; `finalize` re-runs the four gates so the
run cannot end clean-in-git but red-in-gates. It ends with a clean tree on a fresh
`NNN-<short-name>` branch — it does **not** push, merge, bump the version, or tag.
Merging to `main` stays a separate, manual step (replicate the prior iteration's
`Merge iteration NNN: …` `--no-ff` commit + a `docs(claude): record iteration NNN
merged` commit that flips the table row and the milestone prose).

Run it from a clean `main` (the `specify` step creates the branch). It takes two
required string inputs — `spec` (the `/speckit-specify` prompt body, **without**
the leading `/speckit-specify` line) and `plan_hint` (the `/speckit-plan` hint) —
both copied **verbatim** from that iteration's section in
`bookwright-implementation-plan.md`:

```bash
# Load the prompts into vars with a *quoted* heredoc so zsh does NOT expand the
# backticks / `$` / `§` in the text, then pass them as -i key=value:
SPEC=$(cat <<'EOF'
Necesidad: …            # the iteration's /speckit-specify body, verbatim
EOF
)
PLAN_HINT=$(cat <<'EOF'
…                       # the iteration's "Pista para /speckit-plan", verbatim
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

Useful siblings: `specify workflow status` (follow a run), `specify workflow
resume <run_id>` (restart a failed step), `specify workflow list` / `info
bookwright-quality`. Run state lives under `.specify/workflows/runs/<run_id>/`
(`state.json`, `log.jsonl`, `inputs.json`) — these are gitignored. **Refresh
`inputs.json`/the `-i` values for each iteration**: a stale `spec`/`plan_hint`
left over from the previous run is a real failure mode (run `24e61111` for 029
still carried 028's prompt in its recorded inputs even though the shipped spec
was correct) and corrupts the run's audit trail.

## Iterations (shipped + planned)

`specs/` holds one directory per iteration. 001–011 are merged (v0.1.0),
012–018 are merged (v0.2.0), and 019–023 are merged and released (v0.3.0).
024 is merged (v0.3.1), 025 is merged (v0.3.2), 026 is merged (v0.3.3) and 027 is merged (v0.3.4) — the v0.3.x hardening track is complete. The v0.4 narrative-structure milestone is now **released**: 028–032 are all merged and shipped **once** as `v0.4.0` (2026-06-21) at the closing iteration (032), like M4→`v0.2.0` and M5→`v0.3.0`. Iteration 033 then shipped as the `v0.4.1` hardening patch (2026-06-21): it removes the dead top-level `NarrativeRole` concept (`CONCEPTS` 13→12) and hardens the ingestion-parity contract so a dead concept colliding on a carrier's class IRI can never again pass as reachable, closing DEBT-001. Iteration 034 shipped as the `v0.4.2` hardening patch (2026-06-21), the first of the v0.4.x post-dogfooding track: the `focalization` validator now normalizes the candidate line before matching, so the markdown-prefixed `- **Voz narrativa**: …` shape its own scaffold emits parses byte-identically to the bare form — waking a check that had been silently dormant on every voice-bearing fixture, closing DEBT-004. Iteration 035 shipped as the `v0.4.2`'s successor, the `v0.4.3` hardening patch (2026-06-21), the second of the v0.4.x post-dogfooding track: `NarrativeUnit`/`NarrativeFunction` now emit a single `rdfs:label` (the `CharacterRole`/`E55_Type` one-triple shape, riding the identity assertion — no new E13), and `NarrativeSequence` materializes each member's resolved position as a per-unit `bw:sequenceOrdinal` triple (`xsd:integer`, 1-based contiguous rank over the already-sorted members, reified through its own file-level E13) — so the narrative layer is queryable by content (find-by-label) and walkable in declared order (`ORDER BY`) under unordered RDF, closing DEBT-005. `bw:sequenceOrdinal` lives in `sources.ttl` outside the frozen GOLEM closure (Principle X); the CHANGELOG and the `v0.4.3` annotated tag landed with the release step (the `bookwright-release` skill). Iteration 036 shipped as the `v0.4.4` hardening patch (2026-06-21), the third and last of the v0.4.x post-dogfooding track: `_reject_unknown_vocab` now enumerates the accepted members of the closed `type`/`reliability` vocabulary in the rejection message (derived from `SOURCE_TYPE_IRI`/`RELIABILITY_IRI` in declaration order — drift-proof), and `_map_sources` wraps each per-source fault once with a `source '<name>': …` / `source #<n>: …` (1-based) locator prefix, the `--json` error envelope (`code=invalid_research`, `details={relpath, value}`) byte-unchanged — only the human `message` improves (Principle IX); the SPARQL empty-result footgun is documented (not "fixed") in the `graph query` help + docs, closing DEBT-006. This release also folds in the EUPL-1.2 relicense + GOLEM CC BY 4.0 attribution that had accumulated on `main` since `v0.4.3` (previously the CHANGELOG `[Unreleased]` section). Iteration 037 shipped as the `v0.4.5` hardening patch (2026-06-21), the fourth of the v0.4.x post-dogfooding track: a module-level `_PENDING_ONLY = re.compile(r"(?i)^\s*\[pending\b[^\]]*\]\s*$")` plus one guard in `_parse_declaration` make the `focalization` validator treat a body that is *solely* an unanswered `[PENDING: …]` narrative-voice placeholder as no declaration (routing it into the existing "no declaration → zero findings" path), so a fresh `bookwright init` constitution — whose placeholder text literally contains "tercera persona"/"limitada" — no longer parses as a real declaration and floods head-hopping warnings on the first interiority verb. The full `^…$` anchor keeps a body with real text *before or after* the token a real declaration; the guard runs on the already markdown-normalized body (iteration 034); recognition is case-insensitive and label-agnostic; no other focalization rule changed and the frozen ontology is untouched (prose validator, `triples=()`, Principle X), closing DEBT-007. Iteration 038 shipped as the `v0.4.6` hardening patch (2026-06-22), the fifth and last of the v0.4.x post-dogfooding track: a module-level `_HEADING_MARKER = re.compile(r"^#{1,6}\s+")` plus a `scan = _HEADING_MARKER.sub("", line, count=1)` step in `_unknown_mentions` strip a single leading ATX heading marker before the proper-noun heuristic, so the heading's first content word lands at offset 0 and inherits the validator's existing sentence-initial exemption — a chapter title like `# Capítulo 1` no longer reports `Capítulo` as an unbound proper noun. The marker is anchored at `^` with no leading whitespace (so `#Capítulo`, seven-plus `#`, and indented forms are out of scope and behave as before); the rest of the line is analyzed unchanged, so a real off-roster name later in the title (`Elena` in `# La caída de Elena`) still fires; `lineno` still comes from `enumerate`, so the `relpath:line` locator is unchanged. The recognizer stays local to `character_presence.py` (no shared markdown-stripping utility, mirroring 037's `_PENDING_ONLY`); the `tiny-historical` E2E oracle, which had baked the spurious `Capítulo` flag into its expected `warning` count, is corrected `6 → 5` (the fixture manuscript untouched); no other rule changed and the frozen ontology is untouched (prose validator, `triples=()`, Principle X), closing DEBT-008. `__version__` is now `0.4.6`; the CHANGELOG and the `v0.4.6` annotated tag landed with the release step.

| # | Iteration | Milestone | Status |
|---|---|---|---|
| 001 | Repo bootstrap + empty CLI | M0 | ✅ merged |
| 002 | Manifest model (`pydantic` + `tomlkit`) | M0 | ✅ merged |
| 003 | Integration architecture (plugin registry) | M0 | ✅ merged |
| 004 | `bookwright init` command | M0 | ✅ merged |
| 005 | GOLEM domain model (`rdflib`) | M1 | ✅ merged |
| 006 | Graph indexer + `graph build`/`query` | M1 | ✅ merged |
| 007 | Bible / outline / constitution templates | M2 | ✅ merged |
| 008 | The 10 source commands (Markdown) | M2 | ✅ merged |
| 009 | Materialize commands as Agent Skills | M2 | ✅ merged |
| 010 | Validation system | M3 | ✅ merged |
| 011 | Release prep (fixtures, E2E, docs, v0.1.0) | M3 | ✅ merged |
| 012 | Research provenance model (Source/Finding/Anchor) | M4 | ✅ merged |
| 013 | `bookwright-research` skill + `[research]` manifest block | M4 | ✅ merged |
| 014 | `factual_anchor` validator | M4 | ✅ merged |
| 015 | `bookwright-verify` LLM check | M4 | ✅ merged |
| 016 | Research E2E fixture, workflow test, docs | M4 | ✅ merged |
| 017 | Traceability-tag cleanup + non-regression gate | — | ✅ merged |
| 018 | Unified `--json` error envelope | — | ✅ merged |
| 019 | Authored focus state: `[focus]` block + `bookwright focus` | M5 | ✅ merged |
| 020 | `bookwright status` (derived state + `next_actions`) | M5 | ✅ merged |
| 021 | `bookwright-research` consumes anchors / open questions | M5 | ✅ merged |
| 022 | Skills read `status` at start + "Next steps" block | M5 | ✅ merged |
| 023 | Orchestration E2E fixture, workflow test, docs, v0.3.0 | M5 | ✅ merged |
| 024 | Ingestion-parity guard + deferral registry | v0.3.x | ✅ merged |
| 025 | Index locations (G13) + `bible.py` split | v0.3.x | ✅ merged |
| 026 | Index objects (G16) + `bible/objects/` scaffold + skill | v0.3.x | ✅ merged |
| 027 | JSON-envelope cleanup + G6/G3 decision | v0.3.x | ✅ merged |
| 028 | Ingest narrative units (G9) + functions (G10) from `outline/units/` | v0.4 | ✅ merged |
| 029 | Ingest narrative sequences (G7) | v0.4 | ✅ merged |
| 030 | Propp/Greimas vocabularies as `E55_Type` + references | v0.4 | ✅ merged |
| 031 | Narrative-structure continuity validator | v0.4 | ✅ merged |
| 032 | v0.4 close: E2E + docs + re-target G6/G3 + `v0.4.0` | v0.4 | ✅ merged |
| 033 | Remove dead `NarrativeRole` from `CONCEPTS` + harden parity (DEBT-001) | v0.4.1 | ✅ merged |
| 034 | `focalization` tolerates markdown-prefixed voice declaration (DEBT-004) | v0.4.2 | ✅ merged |
| 035 | G9 `rdfs:label` + queryable sequence order (DEBT-005) | v0.4.3 | ✅ merged |
| 036 | Actionable research-source error messages (DEBT-006) | v0.4.4 | ✅ merged |
| 037 | `focalization` treats unanswered `[PENDING]` voice placeholder as no declaration (DEBT-007) | v0.4.5 | ✅ merged |
| 038 | `character_presence` skips ATX heading first word (DEBT-008) | v0.4.6 | ✅ merged |
| 039 | Single prose/structure seam — validators stop coupling to surface markdown (issue #1, facet A) | v0.5.0 | ✅ merged |
| 040 | Tri-valued validator result: `evaluated` / `not-evaluated(reason)` (issue #1, facet B) | v0.5.0 | ✅ merged |
| 041 | Prose seam strips leading Spanish dialogue dash `—`/`–`/`―` (DEBT-009) | v0.5.1 | ✅ merged |

M5/v0.3 is **complete and released** (`v0.3.0`, 2026-06-13): authored focus
(019), `bookwright status` with deterministic `next_actions` (020), the
status-consuming skills (021–022), and the orchestration E2E fixture/tests/docs
(023) all merged. The current milestone is the **v0.3.x hardening track** (iterations
024–027, released as patches `v0.3.1`…`v0.3.4`): ingestion-parity is now explicit
(024, `v0.3.1`, merged), locations G13 are wired (025, `v0.3.2`, merged),
objects G16 are wired (026, `v0.3.3`, merged) — the second cheap mirror of
`settings/` — and the closing cleanup/decision pass landed (027, `v0.3.4`,
merged): the `focus`/`graph` success envelopes are single-sourced byte-for-byte,
the last two `"undecided"` orphan verdicts (G6/G3) are firmly deferred to v0.4,
and the `UnresolvedParticipant` misnomer is renamed to `UnresolvedReference`. The
v0.3.x hardening track is **complete**.

**v0.4 — the narrative-structure layer** (Propp/Greimas: G7/G9/G10) plus
`outline/` ingestion, which closes ingestion parity, is now **released** (`v0.4.0`,
2026-06-21). It was a minor milestone: iterations 028–032 accumulated on `main` and
shipped **once** as `v0.4.0` at the close (032), like M4→`v0.2.0` and M5→`v0.3.0` —
no per-iteration patch tags.
Iterations 028–031 are **merged**: `outline/units/*.md` now ingests into the graph
as `G9_Narrative_Unit` + `G10_Narrative_Function` entities and assembles
`G7_Narrative_Sequence` from their optional `sequence`/`order` keys (see
`bookwright-design.md § 7.4`), taking G7/G9/G10 out of the deferral registry's set —
the modelled-but-unfed narrative-structure layer is now alive end to end. Iteration
030 then populates `propp.ttl`/`greimas.ttl` as `crm:E55_Type` vocabularies (31
Propp functions + 6 Greimas actants, ES+EN labels) and types narrative functions
(G10) and character roles (G11) via `crm:P2_has_type` when the manifest's
`[vocabularies] active` list turns a vocabulary on — the link reified through the
existing `E13` provenance path, with zero regression when no vocabulary is active.
Iteration 031 adds the `narrative_structure` validator — the first *consumer* of
that layer: an auto-discovered, `warning`-default, LLM-free check with two rules,
orphan beat (a `G9` unit in no `G7` sequence, via SPARQL `NOT EXISTS` over
`dlp:proper-part`) and unresolved role (re-surfaced from outline ingestion's
`UnresolvedReference` records through a new cached `ValidationContext.outline()`
accessor), both cited via the existing `E13` provenance path, no ontology change.
Iteration 032 closes the milestone (merged): a source-only `tests/fixtures/tiny-quest/`
fixture + oracle, the build→validate E2E `tests/e2e/test_narrative_workflow.py`, the
Spanish `docs/narrative-structure.md`, and the honest G6/G3 deferral re-target
(`"v0.4"` → the first-class `"demand-pulled"` sentinel, swept across `deferrals.py`,
the parity test, and `DEBT.md`). The `v0.4.0` release metadata — the `__version__`
bump to `0.4.0`, the CHANGELOG section, the CLAUDE.md/design status edits, the
release commit and the annotated tag — landed via the `bookwright-release` skill,
closing the milestone. Vector search and export remain deferred to an unversioned, demand-pulled
horizon (activate on a concrete trigger, not a pre-assigned version). See
`bookwright-roadmap.md`.

When a spec or prompt references `§ 6`, `§ 20.5`, etc., that's a section in
`bookwright-design.md`. Open it.

## Architecture (the big picture)

`bookwright` is a CLI (`src/bookwright/cli.py`) that assembles a `typer` app
from per-command modules. The layers, in dependency order:

- **`errors.py`** (package root) — `BookwrightError`, the **single** shared base
  that owns the canonical `--json` error envelope (`{status, code, message
  [, details]}`) and its one `to_json()`. Every serializable error across the
  codebase (eight origins: `core`, `golem`, `io`, `indexers`, `validation`,
  `commands.validate`, `integrations`, `commands.init`) subclasses it and defines
  **no** per-class serializer. The module imports nothing from the other layers,
  so it sits below all of them with no cycle (Principle IX, iteration 018).
- **`core/`** — the manifest (`manifest.py`, `pydantic` model round-tripped
  through `tomlkit` so author comments survive), the manifest error hierarchy
  (`errors.py`, `ManifestError(BookwrightError)` + the `ManifestWarning` payload),
  and language helpers (`iso639_1.py`).
- **`golem/`** — the GOLEM narrative domain model serialized to Turtle/RDF.
  Each concept is an **immutable Pydantic v2 model** subclassing `GolemEntity`
  (`base.py`): identity (its `URIRef`) is computed once in `model_post_init`
  from a slug. Concepts live in `golem/modules/*` (character, event, setting,
  narrative, relationship, inference, feature) and register in the `CONCEPTS`
  name→class map. **Provenance is structural**: an entity declares
  `DerivedAssertion`s and `CrossRef` edges; the base emits triples uniformly,
  and the indexer reifies each assertion as a CIDOC-CRM
  `crm:E13_Attribute_Assignment` resolving the originating *field* (never a
  file path) to a `file:line` locator. The ontology is **frozen** — the
  17-class closure (`CLASS_IRI`) and `golem.ttl` must not gain classes
  (Constitution X); new vocabulary goes in separate `.ttl` files.
- **`indexers/`** — the `Indexer` `Protocol` (`base.py`) is the only seam the
  `graph` verbs depend on; `RdflibIndexer` is the one concrete engine.
  `rdflib` is permanent; `Grafeo`/`GrafeoIndexer` is **cancelled**.
- **`io/`** — plain-text readers/writers. `frontmatter.py` parses YAML
  front-matter + Markdown body **with line tracking** (`key_lines`) so the
  indexer can build `file:line` provenance. `bible.py` maps `bible/*.md` into
  GOLEM entities; `project.py`, `manuscript.py`, `fs.py`, `report.py` round
  it out, plus `research.py` (iteration 012), an analogue of `bible.py`.
- **`integrations/`** — materializes the 10 source commands as **Agent
  Skills**. `SkillsIntegration` is the plugin base; `INTEGRATION_REGISTRY`
  (populated on import via `_register_builtins`) holds `claude` and `generic`.
  No monolithic dispatcher (Constitution V).
- **`validation/`** — continuity checks (`validators/*`: character presence,
  focalization, setting continuity, temporal) run by `runner.py` against the
  graph via SPARQL (`queries.py`), registered in `registry.py`.
- **`commands/`** — one sub-package/module per CLI verb. Each agent-facing
  command pairs its logic with an `envelope.py` that emits the `--json`
  contract. `init/` is the largest (conflict matrix, rollback ledger,
  optional git init, scaffold from `resources/project/`).
- **`resources/`** — packaged data read at runtime via `importlib.resources`:
  `project/` (the scaffold tree, `.j2` / `.tmpl` templates), `commands/`
  (the 10 source-command Markdown + `references/`), `schemas/golem-1.1/`
  (frozen ontology + VERSION), `vocabularies/` (`propp.ttl`, `greimas.ttl`,
  and the new `sources.ttl`).

**Data flow**: `bible/*.md` → `map_bible` → GOLEM entities → `RdflibIndexer`
→ derived cache `bible/graph.ttl` → `bookwright validate` (SPARQL). The graph
is **always a derived cache**, reconstructible from plain text, never the
source of truth (Constitution I).

## Stack (locked by Constitution II — substituting any requires an amendment)

- **Python 3.11+** only. **`uv`** + committed `uv.lock`. **`hatchling`** build
  backend. **src-layout** (`src/bookwright/`, `tests/` at root), no exceptions.
- Runtime deps: `typer`, `rich`, `rdflib`, `pydantic` v2, `tomlkit`, `jinja2`,
  `python-slugify`, `platformdirs`, `uuid-utils` (**not** `uuid7`), plus
  `pyyaml` and `packaging`. Dev group: `mypy`, `ruff`, `pytest`,
  `pytest-cov`, `pre-commit`, `types-pyyaml`. Docs group (never imported by
  `src/`): `mkdocs` + `mkdocs-material`.
- Every source file ≤ 500 lines, one CLI subcommand per module (Principle IV).

## Domain knobs / non-negotiable behaviors

- **Agent Skills, never legacy commands**: emit one `SKILL.md` per command
  under the integration's `skills_dir`. Writing to `.claude/commands/` or
  analogues is a Principle VI violation that blocks merge. Principle VII
  enforces agentskills.io limits: `name` ≤ 64 chars matching its parent
  directory, `description` ≤ 1024 chars, valid YAML front-matter (the
  `lint_skill_md` gate checks this).
- **JSON-over-stdout (Principle IX)**: any agent-consumed subcommand accepts
  `--json` and then emits a single JSON document on stdout and *only* that.
  Human prose / progress goes to stderr.
- **Integrations**: only `claude` (writes `.claude/skills/`) and `generic`
  (writes `.agents/skills/`) ship. Use the `SkillsIntegration` +
  `INTEGRATION_REGISTRY` plugin shape (Principle V).

## Scope discipline — do NOT implement ahead of the plan

A PR that adds plumbing whose only justification is "future X" MUST be
rejected (Constitution "Scope & Release Discipline").

When a cleanup is detected but is genuinely out of the current iteration's
scope (an unrelated debt class that would be its own iteration), it is **not**
dropped silently: it is recorded in `DEBT.md` (repo root) so the trail is plain
text, not lore. Debt of the *same* class the iteration already touches is swept
in full now, not deferred. Resolving a debt entry **removes** it (git keeps the
history); only consciously `aceptada` (won't-fix) debt stays recorded.

- v0.2 / M4 (design § 20) — research & verification: shipped in `v0.2.0`.
- v0.3 / M5 — context orchestration (design § 21): shipped in `v0.3.0`.
- **v0.3.x hardening (current, iterations 024–027) — cancel tech debt / close v0
  shortcuts:** ingestion-parity guard + deferral registry (024); index locations
  G13 + `bible.py` split (025); index objects G16 (026); JSON-envelope cleanup +
  G6/G3 decision (027). Each is a patch with one observable delta; internal
  plumbing rides inside the patch it enables (e.g. the `bible.py` split ships
  with locations, not as a zero-change release). Don't pull v0.4 work below into it.
- v0.4 — the Propp/Greimas narrative-structure layer (G7/G9/G10) and `outline/`
  ingestion (closes ingestion parity).
- **Demand-pulled horizon (no version assigned)** — ships only when an explicit
  activation condition is met, never as speculative plumbing: **vector search**
  (ChromaDB over rdflib, decoupled from Grafeo — activate on a real
  multi-book/series corpus, or measured structural-recall failure in a skill);
  **export** to EPUB / PDF / print via pandoc (activate once the end-to-end flow
  is proven on a real book). The `1.0` label is earned by that proven flow, not
  pre-assigned to export.

**Cancelled — never implement (owner decision):** preset / genre-package
system (template resolution is 2 layers, overrides → core); `GrafeoIndexer` /
Grafeo engine; multi-integration beyond `claude` / `generic` and the
`bookwright integrate` command; extension system. See design § 15.5, § 20.12.

## GitHub issues — design discussion only (NOT the source of truth)

The repo (`jmorenobl/bookwright`) has issues enabled, but they are **not** an
intake or tracking system — that would violate Principle I (plain-text source of
truth). Plain text stays canonical: shippable, out-of-scope debt → `DEBT.md`;
durable cross-version intent → `bookwright-roadmap.md`; the ordered iteration
plan → `bookwright-implementation-plan.md`; per-iteration artifacts → `specs/`.

Issues fill the **one** gap plain text doesn't: an open-ended **design /
deliberation thread** for "should we change our approach" questions that span a
whole subsystem and are bigger than a `DEBT.md` entry. Rules:

- Open an issue **only** for cross-cutting design discussion, never for a bug or a
  single shippable fix (that's `DEBT.md`) or for ordered work (that's the plan).
- The issue is a scratchpad. **The decision MUST be transcribed back** to
  `bookwright-roadmap.md` / `bookwright-design.md §` (or the constitution) — the
  issue never becomes the record.
- Do **not** migrate the plain-text intake to issues. That move is demand-pulled:
  it activates only on a concrete trigger (a second contributor without repo
  fluency, or external bug reporters), not speculatively.

Labels (the only three; created 2026-06-22 with the first issue): **`design`**
(a direction decision), **`discussion`** (an open deliberation thread),
**`validation`** (the validation layer / validators). Precedent: issue **#1**
("parchear por instancia vs. cerrar la clase", the `focalization`/`character_presence`
surface-heuristic class behind DEBT-004/007/008).

## Language conventions

- `bookwright-design.md`, `bookwright-implementation-plan.md`, the README, and
  the `docs/` site are **Spanish** — the user authored them deliberately so.
  Keep edits to them in Spanish.
- Source code, identifiers, commit messages, the constitution, and per-spec
  artifacts are **English**.
- Agent Skills must trigger on both ES and EN author prompts.

## Spec Kit specifics

- The installed Spec Kit version lives in `.specify/integration.json` (and the
  `.specify/integrations/*.manifest.json`) — that's the source of truth, not
  this file, since it moves often. Don't upgrade without a reason worth chasing
  template churn.
- Don't modify Spec Kit *core* (templates, scripts, manifests). Per-project
  *copies* (`.specify/extensions.yml`, `git-config.yml`) are editable.
- Skill names are hyphenated (`speckit-plan`). `extensions.yml` hook entries
  use dot form (`speckit.git.commit`); the dispatcher converts dots to
  hyphens when invoking.
- `auto_execute_hooks: true`. Mandatory hooks (`before_constitution`,
  `before_specify`) execute without prompting; optional commit hooks ask
  first.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/041-prose-dialogue-dash/plan.md` (iteration 041, the first post-`v0.5.0`
patch, closing DEBT-009 — detected by the `tiny-historical` dogfood). In Spanish
prose, dialogue opens with the typographic em dash `—` (U+2014; en dash `–` U+2013
is a variant). The single prose seam (`io/prose.py`, iteration 039) normalizes ASCII
block markers (`#{1,6}␠`, `[-*+>]␠`) but NOT the dialogue dash, so `character_presence`
sees `—Esto es el porvenir` with the `—` glued to `Esto`: the word is not at offset 0,
`_is_sentence_initial` returns `False`, and the demonstrative `Esto` is reported as an
unknown proper noun — one spurious `warning` on the FIRST capitalized word of EVERY
dialogue line, drowning the real findings. THE LOAD-BEARING DECISION (issue #1
doctrine, research D2): close the class at the SEAM, never the validator. Add
`_DIALOGUE_MARKER = re.compile(r"^\s*[—–]\s*")` to `io/prose.py` and strip it inside
the EXISTING iterative `_normalize` loop as a third `elif` branch (`sub(count=1)`,
one pass per marker), so only the LEADING dash is removed and internal incise dashes
(`—dijo Arnela—`) stay intact. Trailing `\s*` (NOT `\s+`) because Spanish glues the
dash to the word (`—Esto`); a leading typographic dash is unambiguous so no
bullet-vs-emphasis guard is needed. After normalization the first content word lands
at offset 0 and inherits `character_presence`'s EXISTING sentence-initial exemption —
the SAME mechanism DEBT-008 (iteration 038) used for the ATX heading. NO validator is
edited (SC-004 — the diff to validators is empty). Code points: em `—`/en `–` ONLY;
ASCII hyphen bullet `- ` stays owned by `_BULLET_MARKER`; the horizontal bar `―`
(U+2015) and leading quotes (`«`/`"`/`'`) are the SAME class but a distinct design,
RECORDED as DEBT-011 (not swept here). PARITY (verified empirically during planning):
today the seam yields `[Real, Fábrica, Paños, Esto]` on `tiny-historical`, with the
marker `[Real, Fábrica, Paños]` — one fewer (`Esto`). The ONLY pinned-count oracle
that shifts is `tiny-historical/expected-status.md` (`validation.counts.warning 5 → 4`,
fixture manuscript UNTOUCHED, as 038 did `6 → 5`); `tiny-novel`/`tiny-memoir` carry
leading-dash dialogue too but their tests assert only `error == 0` (warnings
tolerated, no pinned count) so they need no edit. New tests: C2 seam rows
(glued/spaced/indented/internal-intact/dash-only/composed) + a `character_presence`
both-directions test (`—Esto` not flagged; mid-line `—Pregúntale a Quirón —dijo.`
flagged). stdlib `re` only — no new dep, no Markdown parser (Constitution II); prose
validator, `triples=()`, frozen ontology untouched (Principle X / FR-012); every
changed file ≤ 500 lines (`io/prose.py` 81 → ~87). Remove DEBT-009 from `DEBT.md`.
Design § 13. `uv run pytest` and the four gates green.
<!-- SPECKIT END -->
