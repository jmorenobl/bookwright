# Phase 0 Research: Orchestration loop fixture, E2E, docs, release

All "NEEDS CLARIFICATION" were resolved in the spec's **Session 2026-06-13**
clarifications; this document records the resulting engineering decisions, each
grounded in the merged code (iterations 019–020) and the iteration-016 precedent.

---

## D1 — Fixture: extend `tiny-historical`, do not author a new one

**Decision.** The orchestration example is the *extended* committed
`tiny-historical` fixture (clarification Q1). The only additions are: a populated
`[focus]` block in `manifest.toml`; a co-located `expected-status.md` oracle; and
a top-level `_resolution/` directory holding the pre-baked answering finding. The
existing corpus (2 characters, 2 settings, timeline, `bible/research/`) is
untouched, so its two declared open questions and its `el-almacen-viejo`
under-reliable anchor become the orchestration loop's open state for free.

**Rationale.** `tiny-historical` already carries the exact derived-state inputs
`status` consumes (open questions in `_index.md`, an under-reliable anchor, a
low-reliability finding). A second fixture would duplicate that scaffolding and
add a second thing to keep coherent. Extending it keeps one realistic project.

**Alternatives rejected.** A dedicated new `tiny-orchestration` fixture — rejected
as redundant scaffolding (clarification Q1/Q4). Mutating the committed fixture's
anchor set to force a cleaner loop — rejected because FR-006 pins the M4 test to
`{error:1, warning:1}` and the `el-almacen-viejo` anchor is permanent.

---

## D2 — The progress assertion is **state convergence**, not a shorter list

**Decision (load-bearing, clarification Q4).** Do **not** assert
`len(next_actions): N → N−1`. The merged engine
([rules.py](../../src/bookwright/status/rules.py)) is a 5-rule table that
aggregates **per workstream**: `research_queue` fires once while *any* open
question OR *any* anchor gap remains (`applies=lambda s: bool(s.open_questions or
s.unresolved_anchors)`), bundling them all into one action. Resolving one open
question leaves both the remaining open question and the permanent
`el-almacen-viejo` anchor gap, so the action list length is unchanged.

The E2E therefore asserts that across the two `status` runs:

- `state.open_questions` loses exactly the resolved id (count K → K−1) and the
  remaining items are unchanged;
- the `research_queue` action's `prompt` no longer mentions the resolved id, and
  its `reason` reflects the new count (`"2 open research questions" → "1 open
  research question"` per `_plural`/`_research_queue`);
- **every other `state` fact and every other `next_actions` entry is byte-for-byte
  identical** — i.e. `phase`, `validation`, `unresolved_anchors`,
  `low_reliability_findings`, the `focus` block, and the `verify_findings` /
  `review_continuity` actions.

**The `state.graph` carve-out.** Resolving a question is a genuine corpus edit:
the open-question Finding is removed from `_index.md` and a closed answering
Finding is added in a new file (D4). Open questions *are* graph entities (the M4
test pins `findings == 6 = 4 closed + 2 open`), so entity count is net-zero
(−1 open finding, +1 closed finding); but a closed finding emits *different*
triples (`bw:claim`, `bw:supportedBy`, `bw:bearsOn`, `bw:assertedBy`) than the
minimal open finding (`bw:open`), so `state.graph.triples` legitimately moves.
This is the only fact besides `open_questions` and the `research_queue`
prompt/reason that changes. The E2E reconciles the spec's two framings — FR-008
("graph available, entity/triple **counts present**") and FR-009 ("every other
state fact byte-for-byte identical") — by asserting `state.graph` as
*available + counts-present* in **each** run independently, and **excluding
`state.graph` from the cross-run byte-identity comparison**. Graph headline
metrics are corpus telemetry that obviously move when the corpus is edited;
FR-009's byte-identity is about the derived *orchestration queues* and
*recommendations*, which is exactly what convergence proves.

> **For /speckit-analyze:** FR-008 and FR-009 are reconciled, not contradictory —
> `state.graph` is asserted per-run (presence) and carved out of the cross-run
> equality (D2). data-model § 4 enumerates the exact comparison sets.

**Rationale.** This is the engine's intended contract (design § 21.2/21.5: the
queue is *derived per workstream*), not a workaround. Asserting a length drop
would either force a redundant second fixture or require deleting the committed
anchor (forbidden by FR-006) — both worse for quality/tech-debt (clarification Q4).

**Alternatives rejected.** Forcing a literal `next_actions` length drop (Q4);
engineering net-zero triple counts to make `state.graph` byte-identical (fragile,
not faithful — a closed finding cannot emit the same triples as an open one).

---

## D3 — Resolution materialized as a two-part edit on the `tmp_path` copy

**Decision (clarification Q5).** "Resolve one open question" is a deterministic,
LLM-free, two-part edit applied by the test to the working copy:

1. **Add the answering Finding** — copy `_resolution/q-libro-de-jornales.md` into
   `bible/research/` on the `tmp_path` copy. It declares one closed Finding with a
   real `claim` and a `sources` list naming an **already-registered `alta`/`media`
   source** (e.g. `"Memoria de la Real Fábrica de Paños"`), with **no `anchors`
   block** — so it adds no anchor gap and is not low-reliability.
2. **Close the question** — drop `q-libro-de-jornales` from `_index.md`'s
   `open_questions` on the copy (a string/line edit, recorded in the oracle so the
   test reads the id from one place).

Rebuilding the graph then closes precisely that one open question
([io/research.py](../../src/bookwright/io/research.py) maps `_index.md`
`open_questions` as `open_only=True` findings; removing the id removes the open
finding), leaving the focus, the `el-almacen-viejo` anchor, the `rumor-incendio`
low-reliability finding, the validation counts, and the remaining open question
(`q-origen-telares`) unchanged.

**Rationale.** Mirrors iteration 016's fixture-as-input + `tmp_path`-copy approach
and keeps the committed fixture pristine and the run repeatable (FR-005, edge
case "Mutating a packaged fixture"). The answering finding answers the actual
question ("¿Se conserva el libro de jornales…?") so the fixture reads as a genuine
documented project (edge case "realistic *and* exact").

**Alternatives rejected.** A pure overlay (copy-only, no `_index.md` edit) — FR-005
clarifies the open-question close is not expressible by file-addition alone
because the id is declared in `_index.md`. An LLM "resolve" step — forbidden in CI
(FR-010, Out of Scope). Giving the answering finding its own anchor or a `baja`
source — would perturb `unresolved_anchors` / `low_reliability_findings` and break
state convergence (D2).

---

## D4 — Where the pre-baked resolution lives so build #1 never sees it

**Decision.** The answering-Finding file lives in a top-level
`tests/fixtures/tiny-historical/_resolution/` directory — **outside** `bible/`,
`manuscript/`, `outline/`. The project loader only reads the configured corpus
paths, so the first `status`/`graph build` ignores `_resolution/` entirely
(FR-005: "MUST NOT be present in the corpus the first status reads"). The test
copies the file into `bible/research/` on the `tmp_path` copy before build #2.

**Rationale.** Satisfies FR-005's pre/post invariant without a brittle "delete it
before the first build" dance. `copy_fixture` copies the whole tree (including
`_resolution/` and `expected-status.md`), which is harmless — the committed-tree
invariants (`test_committed_fixture_is_source_only`, no `[PENDING:]` sentinel)
still hold as long as the resolution file ships no `graph.ttl`/`SKILL.md`/sentinel.

**Alternatives rejected.** Generating the answering finding's text inside the test
(hard-coded content — violates the "never hard-coded, oracle-sourced" precedent).
Storing it under `bible/research/` with a non-`.md` suffix (couples to loader glob
internals).

---

## D5 — Oracle: a new `expected-status.md`, not an extension of `expected-findings.md`

**Decision.** Add a co-located `tests/fixtures/tiny-historical/expected-status.md`
whose front-matter records: the exact open-question id set
(`[q-libro-de-jornales, q-origen-telares]`), the resolved id, the expected
`unresolved_anchors` (the `el-almacen-viejo`/`rumor-incendio` gap with its
`problems`), the expected `low_reliability_findings` (`rumor-incendio`), the
expected `validation.counts` (`{error:1, warning:1, info:0}`), the focus `target`
the test will set, and the expected `next_actions` **skill set + reason templates**
(`research_queue`, `verify_findings`, `review_continuity`). Loaded once via
`parse_frontmatter`, exactly as the 016 test loads `expected-findings.md`.

**Rationale.** FR-004 wants the open state "exactly enumerable in a co-located
oracle, per the `expected-findings.md` precedent." A *separate* file keeps
`expected-findings.md` byte-stable so the M4 test that parses it is provably
untouched (FR-006), and keeps the two concerns (deterministic-validator
expectations vs. orchestration-state expectations) cleanly separated.

**Alternatives rejected.** Extending `expected-findings.md` front-matter — would
work (the M4 test reads specific keys) but risks accidental coupling and muddies
the FR-006 "inert" argument. Hard-coding expectations in the test — violates the
precedent and FR-008.

---

## D6 — Determinism of the asserted JSON

**Decision.** Every asserted field is deterministic by construction:
[model.py](../../src/bookwright/status/model.py) and
[queries.py](../../src/bookwright/status/queries.py) sort all item lists by
corpus-stable keys (`(file, id)`, `(file, promotes, constrains)`) and carry no
minted URIs / timestamps. The two open questions share `file =
bible/research/_index.md`, so they sort by id (`q-libro-de-jornales` <
`q-origen-telares`) → removing the first deterministically leaves the second. The
`focus` block's `updated_at` is stamped once by `focus set` at the start of the
test and is identical across both `status` runs (the test does not re-stamp it
between runs), so the cross-run byte-identity holds; its absolute value is not
asserted (FR-008 asserts focus *defined* + `target`, not the date). The test runs
each `status` and may re-run to confirm repeatability (Acceptance Scenario 4).

**Rationale.** SC-002 / FR-010 require byte-identity on an unchanged corpus; the
merged engine already guarantees it. The only non-determinism risk is the
`focus.updated_at` clock — mitigated by stamping once and never asserting its
value.

---

## D7 — Inertness & degraded paths reuse `tiny-novel` (no new fixture)

**Decision.** The inertness test (FR-011) reuses the committed `tiny-novel`
(no `[focus]`, no `bible/research/`): `status --json` exits 0 with `focus: null`
and `next_actions: []`, and `build`/`validate` behave as pre-M5. The degraded
path (FR-012) is exercised by removing the bible (or pointing at a corpus with no
build prerequisite) on a `tmp_path` copy so `status` returns
`state.graph.available = false` with exit 0 — never a failure
([status.py](../../src/bookwright/commands/status.py) `_aggregate` degraded
branch). No new permanent fixture is authored (FR-011).

**Rationale.** `tiny-novel` is exactly the focus-free/research-free shape FR-011
names; the degraded branch already exists in the merged command and only needs a
test. Matches the 016 inertness group (`test_research_free_project_is_inert`).

**Alternatives rejected.** A new "empty" fixture for the degraded case — the
degraded branch is reachable by mutating a `tmp_path` copy, so no committed
fixture is needed (FR-011 forbids authoring one).

---

## D8 — Version bump: single source `__version__`

**Decision.** Bump `src/bookwright/__init__.py` `__version__` from `"0.2.0"` to
`"0.3.0"` (FR-022). `pyproject.toml` declares `dynamic = ["version"]` via
`[tool.hatch.version]`, so `__init__.py` is the single authoritative source; no
other file restates the number. `tests/test_smoke_import.py`,
`tests/test_cli_version.py`, and `tests/test_cli_subprocess.py` read
`bookwright.__version__` dynamically, so they stay green without edits.

**Rationale.** CLAUDE.md "single-sourced version, no drift"; the merged tests
already assert *against* `__version__` rather than a literal.

**Alternatives rejected.** Hard-coding `0.3.0` anywhere besides `__init__.py`
(introduces drift).

---

## D9 — Docs: one new top-level page, the rest verify-and-finalize

**Decision.** `docs/orchestration.md` is a **new top-level page** (sibling of
`docs/research.md`, **not** under the CLI-gated `docs/commands/`) covering, in
Spanish: the three-layer model (autoral `[focus]` vs. derivado `status` vs. juicio
the skills) per design § 21.2; what `bookwright status` reports and how
`next_actions` are derived (the 5-rule per-workstream table, § 21.5); the work
loop focus → status → act → repeat; and how the skills consume `status` at start
(021–022). It is wired into `mkdocs.yml` nav as `Orquestación: orchestration.md`
(FR-014). The existing `docs/commands/status.md` and `docs/commands/focus-*.md`
(added in 019–020, already in nav) are **verified and brought current** against
the live CLI, not duplicated (FR-015). Both changelogs — `docs/changelog.md`
(nav target) **and** the fuller root `CHANGELOG.md` (they are distinct files,
maintained in parallel) — gain a Spanish v0.3.0 entry consolidating 019–023
(FR-016). The site builds under existing `strict: true` with zero warnings
(FR-019).

**Rationale.** Mirrors how `research.md` shipped in M4 (top-level conceptual page
+ per-command reference). Spanish prose matches the docs site and design docs
(user convention). `strict: true` is the machine-checkable zero-warning gate.

**Alternatives rejected.** Putting orchestration content under `docs/commands/`
(it is conceptual, not a single-command reference). Updating only one changelog
(both exist and are author-facing; FR-016 "the changelog" is satisfied by keeping
them consistent).
