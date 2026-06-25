# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state: v0.5.11 released (2026-06-25)

The current release is **v0.5.11** (iteration 052). The repo is on `main`
(tagged) with a real `src/bookwright/` package (~200 Python files), the full
test suite, docs, and CI gates green. **There is no active iteration branch.**

The latest work lands the **second vertical slice** of **issue #1 track C
(move 3 — semantic judgment)** (iteration 052), the same pattern as 051 with
only the judged dimension changed. The **third dogfood**
(`el-año-de-las-casas-vacías`, third-person limited) measured a **real head-hop**
— the interiority of `Irene` inside a chapter focalized on `Teo` — left
**invisible**, because `focalization` honestly abstains under limited-third
(`Abstention(_HEAD_HOPPING_PENDING, pending_capability)`, iteration 050) rather
than fake the judgment. v0.5.11 closes that gap (design § 20.6.2): the LLM
judgment is an **Agent Skill**, not Python — `bookwright-continuity` gains a
**fifth axis** that, **only** under a declared third-person *limited* voice
(`bible/constitution.md`), reads the focal POV per chapter from the prose **POV
calendar** (`bible/pov-structure.md`, "Calendario de POV") and the roster, then
judges per chapter whether the prose attributes interiority to a **non-focal**
POV character, reporting each head-hop as one more continuity deviation (and
reporting the grounding gap, never guessing, when the calendar is absent /
`[PENDING]`). The `not_evaluated` channel **is** the contract: each
`pending_capability` abstention is a judgment task the skill answers, and
`bookwright status` adds a peer **green-preserving** `next_action`
(`judge_head_hopping`). The 051 name-only `_JUDGE_SOURCES` frozenset is
**generalized** to a shared `_judges(validator)` predicate requiring
`validator == … AND kind is pending_capability` — `judge_undeclared_characters`
adopts it **byte-identically**, while the new predicate also expresses what
name-only keying could not: `focalization` emits **both** abstention kinds, and
only the `pending_capability` one fires the nudge (its `missing_input` gap stays
with `activate_dormant_validators`). The verdict is **informative, not a gate**:
the CLI stays deterministic with no LLM dependency, no `error` is born from an
LLM, the 044 green predicate is **byte-identical**, and `focalization` and all of
`validation/` are untouched. Head-hopping carries no debt of its own, so **no
`DEBT.md` entry is removed** — the third move-3 dimension (the pro-drop
first-person recall, DEBT-021) stays open and follows the same pattern in a later
slice; gating an LLM verdict (golden-run caching) stays deferred. The prior
v0.5.x work stands: the move-3 first slice (v0.5.10, undeclared characters,
closed DEBT-013), v0.5.9's general partial-evaluation contract (`EvalResult` +
`Abstention`, DEBT-019) and the track-A/B honesty + deterministic-polish patches
(v0.5.3–v0.5.8) — per-release detail in `CHANGELOG.md`.

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
- The **v0.5.x post-dogfooding track** (041–052, patches `v0.5.1`…`v0.5.11`)
  continues the issue #1 doctrine on two tracks. **Track A — evaluation
  honesty:** a deterministic heuristic measured insufficient on real prose
  **abstains** (`not_evaluated`, kind-categorized
  `missing_input`/`pending_capability`) instead of faking findings, a
  partial corpus surfaces what was excluded, and a **partial-evaluation
  contract** (form (c) `EvalResult`) lets a validator emit findings **and**
  abstentions in one run — so a deterministic sub-check no longer disappears
  behind a whole-run abstention, and **move 3 lands its first two vertical
  slices** — `bookwright-continuity` gains a fourth axis that judges *characters
  used in the prose but undeclared* (051) and a fifth axis that judges
  *head-hopping / broken focalization under limited-third* (052); the skill layer
  answers the `character_unknown_mentions` and `focalization` `pending_capability`
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
  partial-evaluation contract (050), and the **move-3 first two slices** (051,
  052) are the headline moves.

The LLM **semantic-judgment** escalation (issue #1 move 3) is **activated** and
landed its **first two vertical slices** (051, 052, design § 20.6.2):
`bookwright-continuity` judges the character-used-but-not-declared dimension over
the `character_unknown_mentions` abstention (051) and the head-hopping / broken-
focalization dimension over the `focalization` `pending_capability` abstention
under limited-third (052), anchored in the authored roster + POV calendar —
judgment, not gate (the CLI stays deterministic, no LLM in CI, green
byte-identical). The remaining move-3 dimension (1st-person break / pro-drop
recall, DEBT-021) follows the same pattern in a later slice; gating an LLM
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
iterations through 052 (the move-3 second slice, `v0.5.11`) are merged; there is
no active iteration branch.

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
`specs/053-move3-first-person-honesty/plan.md` (iteration 053, design § 13.4 +
§ 13.5 / § 20.6.1 — issue #1 **move 3 THIRD dimension, FIRST half (honesty)**, plus the
contract plumbing it forces; *no gate, no skill change*). The third move-3 dimension —
the 1st-person break / pro-drop recall ceiling (**DEBT-021**) — is split into TWO
iterations, exactly as head-hopping split into honesty (045/050) and judgment (052):
THIS iteration (053) is the HONESTY half; the JUDGMENT half (the SIXTH
`bookwright-continuity` axis + its nudge, which CLOSES DEBT-021) is iteration 054 and is
OUT OF SCOPE. Today `focalization` runs `_first_person_breaks` (the CLOSED set
`yo`/`nosotros`/`nosotras`/`i`/`we`, near-zero FP) under a 3rd-person voice and is
SILENT about everything that closed set cannot see — Spanish pro-drop verbal morphology
(`Caminé`, `Me senté`), an OPEN set no regex captures without reopening the whack-a-mole
issue #1 closed. That silence is the `[]`-means-clean lie at the sub-check level. THREE
things: (1) CONTRACT — `Abstention` AND `NotEvaluatedResult` gain an OPTIONAL
`code: str | None = None` (short stable discriminator: `"head_hopping"`,
`"first_person_recall"`, `"undeclared_characters"`), serialized ADDITIVELY in
`NotEvaluatedResult.to_json` exactly as iter 044 added `kind`. The runner's single
`_record` naming point gains `code=None`: form (c) `EvalResult` passes `abstention.code`,
form (b) `raise NotEvaluated` passes `None`. The `NotEvaluated` EXCEPTION does NOT gain
`code` (the discriminator is of RETURNED abstentions). `not_evaluated_sort_key` stays
`(validator, reason)` — `code` is NOT a sort term (the two focalization reasons differ,
so the order is already total). (2) HONESTY — `focalization` defines
`_FIRST_PERSON_RECALL_PENDING` («full first-person recall requires semantic judgment
(move 3); the deterministic check only covers the explicit subject pronoun»), puts
`code="head_hopping"` on the existing head-hopping abstention, and adds
`Abstention(_FIRST_PERSON_RECALL_PENDING, pending_capability, code="first_person_recall")`
in BOTH 3rd-person branches (wrap the non-limited bare-`list` return in an `EvalResult`).
`_first_person_breaks`, the explicit-pronoun regex, the 1st-person `return []` branch, and
the FOUR `missing_input` raises are UNTOUCHED. (3) KEYING — `status/rules.py`
`_judges(validator)` → `_judges(validator, code)` (`... AND r.code == code`); re-point
`judge_undeclared_characters=_judges("character_unknown_mentions", "undeclared_characters")`
and `judge_head_hopping=_judges("focalization", "head_hopping")` (now PRECISE: never fires
on the first-person abstention, never mis-fires under 3rd-non-limited). Because a code-keyed
predicate needs a `code` on the wire and the raised path stays code-less,
`character_unknown_mentions` is CONVERTED from a raised total abstention (form (b)) to a
returned partial abstention (form (c)): `EvalResult([], [Abstention(<reason>,
pending_capability, code="undeclared_characters")])` — observationally additive (only the
`code` key changes from `null`), nudge behavior unchanged. NO first-person nudge yet (that
is 054). `code` flows into `status` for FREE (`ValidationSummary.not_evaluated` holds
`NotEvaluatedResult` directly; `status/model.py` + `status/queries.py` are verify-only);
`commands/validate.py` ingestion-skip `NotEvaluatedResult` call stays valid (code defaults
None). GREEN lives in `validation/report.py` (filters `missing_input`) — DO NOT touch;
`pending_capability` never degrades green; `activate_dormant_validators` stays
`missing_input`-only; the error-only CI gate is unchanged and NO `error` is born.
Tests/oracles (EMPIRICAL via `uv run pytest`): `test_base.py`, the runner + serialization
tests, `test_report.py`, `test_focalization.py`, `test_character_unknown_mentions.py`
(form (b)→(c); reason/kind unchanged), `test_rules.py` (keying by `code` + NEGATIVE
3rd-non-limited → NO head-hop nudge), `test_status.py`/`test_command.py`, and the oracles
`tests/fixtures/*/expected-status.md` (`tiny-historical` gains the `first_person_recall`
entry → 3 `not_evaluated`; `code` keys; `next_actions` STAYS 5) and `tests/e2e/*` that
assert `not_evaluated` (gain `code`, and in 3rd-person fixtures the `first_person_recall`
entry); `tiny-novel`/`tiny-memoir` stay GREEN. CONTRACT-BEFORE-CODE: § 13.4 (`not_evaluated`
gains `code`, the discriminator, as 044 added `kind`) + § 13.5 / § 20.6.1-2 (move 3
distinguishes dimensions by `code`; first-person honesty LANDED, judgment → 054); UPDATE
DEBT-021 (do NOT remove — honesty exists in 053, judgment + closure is 054); milestone
prose + iteration index (row 053). Out of scope: the JUDGMENT half (054, closes DEBT-021);
widening the explicit-pronoun regex (whack-a-mole); GATING an LLM verdict; touching
`bookwright-verify` or any skill; reopening the 044 green predicate; REMOVING any
`DEBT.md` entry; a closed `code` enum/registry (only three values); any new dependency
(Constitution II) / frozen ontology (Principle X) / new validator in `validation/`. Each
changed file ≤ 500 lines. `uv run pytest` + four gates green.
<!-- SPECKIT END -->
