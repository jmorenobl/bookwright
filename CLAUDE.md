# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state: v0.5.12 released (2026-06-25)

The current release is **v0.5.12** (iteration 053). The repo is on `main`
(tagged) with a real `src/bookwright/` package (~200 Python files), the full
test suite, docs, and CI gates green. **There is no active iteration branch.**

The latest work lands the **third move-3 dimension, first half (honesty)** of
**issue #1 track C** (iteration 053) — the same split head-hopping took, honesty
(045/050) before judgment (052). Today `focalization` runs `_first_person_breaks`
over a **closed** explicit-pronoun set (`yo`/`nosotros`/…/`i`/`we`) under a
third-person voice and is **silent** about everything that set cannot see —
Spanish pro-drop verbal morphology (`Caminé`, `Me senté`), an **open** set no
regex captures without reopening issue #1's whack-a-mole (**DEBT-021**). That
silence is the `[]`-means-clean lie at the sub-check level. v0.5.12 closes it
(design §§ 13.4/13.5/20.6): `focalization` declares the recall ceiling
**honestly** with a `pending_capability`
`Abstention(_FIRST_PERSON_RECALL_PENDING, …, code="first_person_recall")` under
**both** third-person branches (under limited-third it joins the head-hopping
abstention in one partial `EvalResult`; the non-limited bare `list` is now
wrapped in an `EvalResult`), while the explicit-pronoun `warning`s, the
`_FIRST_PERSON` regex, and the four `missing_input` raises stay
**byte-identical**. The forced contract plumbing rides inside the patch that
needs it, exactly as iteration 044 added `kind`: both `Abstention` and
`NotEvaluatedResult` gain an **optional** `code: str | None = None` discriminator,
serialized **additively** (`code: null` for a raised abstention), stamped through
the runner's **single** `_record` naming point (the raised `NotEvaluated`
*exception* does not gain `code`); `not_evaluated_sort_key` stays
`(validator, reason)` (`code` is **not** a sort term). Because `focalization` now
emits **two** `pending_capability` abstentions, `status` `_judges(validator)` is
generalized to `_judges(validator, code)`, so `judge_head_hopping` keys precisely
on `(focalization, head_hopping)` and never mis-fires on the recall abstention;
`judge_undeclared_characters` re-points to
`(character_unknown_mentions, undeclared_characters)`, which forces that validator
from a raised total abstention (form (b)) to a returned partial one (form (c)) so
it can carry the `code` — observationally additive (only `code` changes from
`null`), nudge behaviour unchanged. **No** first-person nudge yet (that, plus
DEBT-021's closure, is iteration 054); **no** gate, **no** skill change, the 044
green predicate **byte-identical**, no `error` born, and **no `DEBT.md` entry
removed** (DEBT-021's honesty half landed; its judgment half stays open). The
prior v0.5.x work stands: the move-3 first two slices (v0.5.10 undeclared
characters / closed DEBT-013, v0.5.11 head-hopping judgment), v0.5.9's general
partial-evaluation contract (`EvalResult` + `Abstention`, DEBT-019) and the
track-A/B honesty + deterministic-polish patches (v0.5.3–v0.5.8) — per-release
detail in `CHANGELOG.md`.

**The per-release detail (what changed, which regex, which oracle) lives in
`CHANGELOG.md` — not here.** This section states only the current state and the
rules that govern work; do not grow it into an inline changelog.

**Released versions** (the per-iteration status is the table below; the
per-release narrative is `CHANGELOG.md`):

- `v0.1.0` — the v0 toolkit (M3, iterations 1–11).
- `v0.2.0` — the M4 research & verification system (12–18).
- `v0.3.0` — the M5 context orchestration system (19–23), plus the **v0.3.x
  hardening track** (024–027, patches `v0.3.1`…`v0.3.4`).
- `v0.4.0` — the narrative-structure layer (Propp/Greimas G7/G9/G10 + `outline/`
  ingestion, 028–032), which **reaches the ingestion-parity north star**, plus
  the **v0.4.x post-dogfooding hardening track** (033–038, patches
  `v0.4.1`…`v0.4.6`) that closed DEBT-001/004/005/006/007/008.
- `v0.5.0` — the **validation-robustness** minor (issue #1, iterations 039+040):
  a single Markdown-aware prose seam (`io/prose.py`) all prose validators consume
  (closing the surface-coupling class at the root), and a **tri-valued** result —
  `evaluated` / `not-evaluated(reason)` surfaced in an additive `not_evaluated[]`
  channel — so `[]` stops reading as "clean" when it meant "couldn't look". GREEN
  is the single documented predicate `status == "ok" AND no not_evaluated entry
  has kind == "missing_input"`; only `error` findings gate CI.
- The **v0.5.x post-dogfooding track** (041–053, patches `v0.5.1`…`v0.5.12`)
  continues the issue #1 doctrine on two tracks. **Track A — evaluation
  honesty:** a deterministic heuristic measured insufficient on real prose
  **abstains** (`not_evaluated`, kind-categorized
  `missing_input`/`pending_capability`, plus an additive per-dimension `code`
  discriminator from 053) instead of faking findings, a
  partial corpus surfaces what was excluded, and a **partial-evaluation
  contract** (form (c) `EvalResult`) lets a validator emit findings **and**
  abstentions in one run — so a deterministic sub-check no longer disappears
  behind a whole-run abstention, and **move 3 lands its first two judgment
  slices plus a third dimension's honesty half** — `bookwright-continuity` gains
  a fourth axis that judges *characters used in the prose but undeclared* (051)
  and a fifth axis that judges *head-hopping / broken focalization under
  limited-third* (052), and `focalization` declares the *first-person pro-drop
  recall* ceiling honestly (053, the `code="first_person_recall"` abstention —
  its judgment half is 054); the skill layer answers the
  `character_unknown_mentions` and `focalization` `pending_capability`
  abstentions anchored in the authored roster + POV calendar, and the CLI stays
  deterministic. **Track B — authoring honesty + deterministic
  polish:** an unrecognized controlled-vocabulary term is no longer typed in
  silence but emits a non-fatal enumerated `graph build` warning, and the
  graph-consumer validators now emit actionable locators + legible handles.
  Closed DEBT-009/010/013/014/015/016/017/018/019; the `character_unknown_mentions`
  abstainer (043), the `focalization` head-hopping abstention (045), `validate`
  surfacing ingestion-skipped bible files (046), the `untyped_vocab_terms`
  soft-warning channel (047), the actionable graph-consumer locators (048), the
  unified `narrative_structure` unit identifier (049), the
  partial-evaluation contract (050), the **move-3 first two slices** (051,
  052), and the **move-3 third dimension's honesty half + the `code`
  discriminator** (053) are the headline moves.

The LLM **semantic-judgment** escalation (issue #1 move 3) is **activated** and
landed its **first two vertical slices** (051, 052, design § 20.6.2):
`bookwright-continuity` judges the character-used-but-not-declared dimension over
the `character_unknown_mentions` abstention (051) and the head-hopping / broken-
focalization dimension over the `focalization` `pending_capability` abstention
under limited-third (052), anchored in the authored roster + POV calendar —
judgment, not gate (the CLI stays deterministic, no LLM in CI, green
byte-identical). The third move-3 dimension (1st-person break / pro-drop recall,
DEBT-021) landed its **honesty half** (053): `focalization` declares the recall
ceiling with a `code="first_person_recall"` `pending_capability` abstention under
both third-person branches; its **judgment half** (the sixth axis + a
`judge_first_person_recall` nudge, which CLOSES DEBT-021) is iteration 054. Gating
an LLM
verdict stays deferred. The remaining
longer-horizon work — semantic judgment in validation, vector search (ChromaDB
over rdflib) and export — is deferred to an unversioned, demand-pulled horizon:
each ships only when its activation condition is met — see `bookwright-roadmap.md`.

The canonical references:

- `bookwright-design.md` (Spanish, ~74 KB) — canonical design spec. Section
  numbering is load-bearing; specs and iteration prompts cite it as
  `bookwright-design.md § N.M`. Section 16 lists axiomatic decisions that
  MUST NOT be reopened. § 20 covers the research system (shipped in v0.2);
  § 21 the context orchestration (shipped in v0.3).
- `bookwright-roadmap.md` (Spanish) — the **durable** intent across versions
  (the *what* and *why*): the version line (… → v0.4 → v0.4.x → v0.5.0 → v0.5.x →
  demand-pulled horizon), the
  ingestion-parity north star, the cancelled list. Unlike the plan, it is **not**
  emptied each milestone. A guide, not a commitment.
- `bookwright-implementation-plan.md` (Spanish) — ordered iteration plan for the
  **current milestone only**; emptied of
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

`specs/` holds one directory per iteration. The table below is the canonical
per-iteration status; the narrative for each release is in `CHANGELOG.md`. All
iterations through 053 (the move-3 third-dimension honesty half, `v0.5.12`) are
merged; there is no active iteration branch.

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
| 042 | `character_presence` unknown-mention crosses setting/location/object rosters (DEBT-010) | v0.5.2 | ✅ merged |
| 043 | Split `character_presence`: orphan `error` rule + `character_unknown_mentions` abstainer → `not_evaluated` (issue #1 track A; subsumes DEBT-011/012) | v0.5.3 | ✅ merged |
| 044 | Kind-categorized `not_evaluated` (`missing_input`/`pending_capability`); green reachable again (issue #1, 040 green-contract repair) | v0.5.3 | ✅ merged |
| 045 | `focalization` head-hopping abstains → `pending_capability` under limited-third; heuristic deleted (issue #1 track A; closes DEBT-014, records DEBT-019) | v0.5.4 | ✅ merged |
| 046 | `validate` surfaces ingestion-skipped bible files as `not_evaluated` (`ingestion`/`missing_input`); closes `status`↔`validate` asymmetry (issue #1 track A; closes DEBT-018) | v0.5.5 | ✅ merged |
| 047 | `graph build` soft-warns unrecognized Propp/Greimas vocab terms (`untyped_vocab_terms` channel, enumerated, non-fatal; node stays untyped) (issue #1 track B; closes DEBT-016) | v0.5.6 | ✅ merged |
| 048 | Actionable graph-consumer locators: `factual_anchor` resolves `source` to `bible/research/<topic>.md` + shared authored handle (`anchor_corpus()` in-process build), `temporal` rules a/b/c adopt `resolve_source` over a deterministic event (issue #1 track B; closes DEBT-015) | v0.5.7 | ✅ merged |
| 049 | Unify `narrative_structure` unit identifier: both rules name the `G9` unit by its human `rdfs:label` via one shared `_unit_identifier` point (orphan-beat drops the opaque slug; `load_orphan_units` carries the label via `OPTIONAL`) (issue #1 track B; closes DEBT-017) | v0.5.8 | ✅ merged |
| 050 | Partial-evaluation contract: third validator return shape (`EvalResult(violations, not_evaluated)` + `Abstention`); `focalization` runs `_first_person_breaks` AND abstains on head-hopping under limited-third in one run (issue #1 track A; closes DEBT-019) | v0.5.9 | ✅ merged |
| 051 | Move 3 first vertical slice: `bookwright-continuity` gains a 4th axis judging characters used-but-undeclared (reads the person roster from `bible/characters/` `name:`), and `status` adds an informative `judge_undeclared_characters` nudge keyed on the `character_unknown_mentions` abstention; judgment not gate, green byte-identical (issue #1 track C — move 3; closes DEBT-013) | v0.5.10 | ✅ merged |
| 052 | Move 3 second vertical slice: `bookwright-continuity` gains a 5th axis judging head-hopping / broken focalization (reads the declared voice + the `bible/pov-structure.md` POV calendar + the roster, under limited-third only), and `status` adds a peer `judge_head_hopping` nudge — the 051 name-only `_JUDGE_SOURCES` frozenset generalized to a shared `_judges(validator)` predicate (source + `pending_capability`); judgment not gate, green byte-identical, `focalization` untouched (issue #1 track C — move 3; DEBT-021 stays open) | v0.5.11 | ✅ merged |
| 053 | Move 3 third dimension, FIRST half (honesty): `focalization` declares the first-person-recall ceiling honestly — a `pending_capability` `Abstention(code="first_person_recall")` under BOTH 3rd-person branches (pro-drop verbal morphology is an open set no regex captures, DEBT-021) — while the explicit-pronoun `warning`s stay byte-identical. The forced contract plumbing: `Abstention`/`NotEvaluatedResult` gain an optional `code` discriminator (additive, exactly as 044 added `kind`), stamped through the runner's single `_record`; `status` `_judges(validator)` → `_judges(validator, code)` so the 052 head-hop nudge keys precisely on `(focalization, head_hopping)` and never mis-fires on the new recall abstention; `character_unknown_mentions` converts form (b)→(c) to carry `code="undeclared_characters"`. No first-person nudge (that + closure is iteration 054); no gate, no skill change, green byte-identical (issue #1 track C — move 3; DEBT-021 honesty half landed, judgment is 054) | v0.5.12 | ✅ merged |

The narrative layer (G7/G9/G10) is alive end to end as of v0.4: `outline/units/*.md`
ingests as `G9_Narrative_Unit` + `G10_Narrative_Function` and assembles
`G7_Narrative_Sequence` (design § 7.4); `propp.ttl`/`greimas.ttl` type functions
(G10) and roles (G11) via `crm:P2_has_type` when a `[vocabularies] active`
vocabulary is on; the `narrative_structure` validator is its first consumer
(orphan-beat + unresolved-role, LLM-free). Vector search and export remain
deferred to the unversioned, demand-pulled horizon (activate on a concrete
trigger, not a pre-assigned version). See `bookwright-roadmap.md`.

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
- v0.3 / M5 — context orchestration (design § 21): shipped in `v0.3.0`, plus the
  v0.3.x hardening track (024–027).
- v0.4 — the Propp/Greimas narrative-structure layer (G7/G9/G10) and `outline/`
  ingestion (closes ingestion parity): shipped in `v0.4.0`, plus the v0.4.x
  hardening track (033–038).
- v0.5 — validation robustness (issue #1): shipped in `v0.5.0`, plus the v0.5.x
  honesty/abstention track (041–047). The patch tracks follow one rule worth
  keeping: each patch is one observable delta, with internal plumbing riding
  inside the patch it enables (not a zero-change release).
- **The current frontier is the demand-pulled horizon below** — there is no open
  versioned milestone. **Demand-pulled horizon (no version assigned)** — ships only when an explicit
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
`specs/054-move3-first-person-judgment/plan.md` (iteration 054, design § 20.6.2 +
§ 13.5 — issue #1 **move 3 THIRD dimension, SECOND half (judgment)**, which CLOSES
DEBT-021 and **completes the first move-3 wave**). This is the exact MIRROR of 052
(head-hopping) over the OTHER `focalization` abstention: 053 made `focalization` HONEST
(it already emits `Abstention(_FIRST_PERSON_RECALL_PENDING, pending_capability,
code="first_person_recall")` in BOTH 3rd-person branches, and the `code` discriminator +
`_judges(validator, code)` keying already ship); 054 makes `bookwright-continuity` JUDGE
that dimension. **ZERO diff under `validation/`** — `focalization` and the `code` contract
/ `_judges` helper are UNTOUCHED (FR-013). THREE edits: (1) SKILL — add a SIXTH axis
("1st-person break / voice slip") to `resources/commands/bookwright-continuity.md`
(`## Procedimiento` + `## Output`, mirror of the 5th head-hopping axis), grounded ONLY in
the declared narrative voice (`bible/constitution.md`, already read by the 5th axis) — NO
roster, NO POV calendar (a 1st-person break is grammatical person, not character identity).
It applies under ALL declared 3rd person (limited OR non-limited — unlike the limited-only
5th axis), JUDGES the pro-drop verbal morphology (`Caminé`, `Me senté`) the explicit-pronoun
check can't see, ADDS on top of (never suppresses) `focalization`'s explicit-pronoun
`warning`s, and on absent/`[PENDING]`/person-less voice REPORTS THE GROUNDING GAP (does not
guess). Update the «Revisa cinco ejes» intro → seis; report each slip as one more deviation:
quote + "first-person voice under a narration declared in third person" + a suggestion. (2)
DESCRIPTION — it sits at 1000/1024 (measure: `uv run python -c "from
bookwright.integrations.descriptions import SKILL_DESCRIPTIONS as D;
print(len(D['bookwright-continuity']))"`); FOLD the 1st-person trigger into the existing
5th-axis voice/focalization phrase WITHOUT growing (e.g. «head-hopping / saltos de punto de
vista / focalización rota» → also «rupturas de voz / persona narrativa», EN twin too), stay
≤1024, mirror VERBATIM into `SKILL_DESCRIPTIONS["bookwright-continuity"]`
(`descriptions.py:27`); equality gate `tests/integrations/test_descriptions.py`. (3) NUDGE —
in `status/rules.py` add `_judge_first_person_recall` builder + a `judge_first_person_recall`
`Rule` with `applies=_judges("focalization", "first_person_recall")`, inserted IMMEDIATELY
AFTER `judge_head_hopping` and BEFORE `define_focus`. `_judges(validator, code)` already
exists (053) — only USE it. The action is fixed/byte-identical, DISTINCT from the 051/052
ones (reason starts "focalization abstained on first-person recall"; prompt names the
declared voice only — NO POV calendar/roster). Keys PRECISELY on `first_person_recall`:
never fires on `head_hopping`, and head-hopping never fires on first-person. INFORMATIVE —
never degrades green: the 044 green predicate (`validation/report.py`, missing_input-only) is
byte-identical, `activate_dormant_validators` stays missing_input-only, NO `error` is born,
the error-only CI gate is unchanged. Tests/oracles (EMPIRICAL via `uv run pytest`):
`test_command_body.py` (NEW 6th-axis assertion mirroring the 5th), `test_command_activation.py`
(folded ES+EN trigger fires; 4th/5th still fire), `test_descriptions.py`/`test_skill_capabilities.py`/
`test_materialize.py` (lint ≤1024 + verbatim mirror), `test_rules.py` (POSITIVE
first_person_recall → nudge — REWRITE the 053 `test_first_person_recall_alone_fires_no_judge_nudge`
and `test_head_hopping_and_recall_together_…`; add the `judge_first_person_recall` `_TRIGGER`
entry; NEGATIVE head_hopping-only → NO first-person nudge; all-three co-fire in table order),
`test_status.py`, and the oracle `tests/fixtures/tiny-historical/expected-status.md`
(`next_actions` 5 → 6 — a 4th `bookwright-continuity` — with the co-located PROSE + inline
`# nudge:`/iteration comments updated in the SAME edit: «cinco workstreams… tercer» → «seis…
a fourth», «(las tres)… sigue siendo 5» → «las cuatro… 6»; leaving any stale is a forbidden
inconsistent oracle) + `tests/e2e/test_orchestration_workflow.py`; `tiny-novel`/`tiny-memoir`
stay GREEN. Records: REMOVE DEBT-021 from `DEBT.md` (the dimension is COMPLETE — honesty 053
+ judgment 054); reconcile `bookwright-design.md` § 20.6.2 / § 13.5 (3rd dimension LANDED,
first wave complete; the 1st-person axis grounds on the DECLARED VOICE ONLY — see
`research.md` Decision 1, superseding the older "voz + roster + POV" phrasing); milestone
prose + iteration index (row 054). Out of scope: GATING an LLM verdict; widening the
explicit-pronoun regex (whack-a-mole); touching `focalization`/anything under `validation/`,
the `code` contract, or `_judges`; touching `bookwright-verify`; reopening the 044 green
predicate; any new dependency (Constitution II) / frozen ontology (Principle X) / new
validator. Each changed file ≤ 500 lines. `uv run pytest` + four gates green.
<!-- SPECKIT END -->
