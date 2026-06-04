# Phase 0 — Research & Decisions

All "NEEDS CLARIFICATION" were resolved against the codebase (the mechanism already
exists) and the spec's own Clarifications session (2026-06-05). No external research was
needed — this iteration consolidates merged code.

---

## D1 — Where the fixture lives

**Decision**: Static directory `tests/fixtures/tiny-historical/`, sibling to `tiny-novel` /
`tiny-essay` / `tiny-memoir`. Loaded into `tmp_path` via `tests/conftest.py::copy_fixture`
and driven through the real CLI in-process (`CliRunner`), exactly like
`tests/fixtures/test_fixtures.py` and the iteration-12 research-build tests.

**Rationale**: Every committed example already lives there; `copy_fixture` is name-based and
already shipped. The spec's "packaged example project" is the loose sense of "ships with the
repo" — the canonical convention (and the spec's own Assumptions) is `tests/fixtures/tiny-*`.
Putting it in `src/bookwright/resources/` would be a new distribution surface this iteration
has no mandate to add.

**Alternatives rejected**: (a) packaging it in the wheel under `resources/` — out of scope,
no requirement, would need new packaging + tests; (b) generating it programmatically like
`tests/fixtures/research.py` — that helper is for unit/integration scaffolds, but US1 wants a
*readable, openable* example a human inspects, which a static tree delivers and a code
generator does not.

---

## D2 — The two anachronisms are different things (the load-bearing decision)

**Decision**: The fixture plants **two** anachronisms, caught by **different layers**:

1. A **manuscript-prose** anachronism (FR-006) — e.g. a character using an object/technology
   that did not exist in the story's year. This is what the **LLM `bookwright-verify` skill**
   detects. It is *not* deterministically testable in CI; it is the documented manual step.
2. A **graph-level time-span** anachronism (FR-007 *error*) — an `anchor` whose year-span
   (`begin`/`end` or `date`) is **disjoint** from the year-interval of the dated timeline
   event it `constrains`. `factual_anchor`'s **R5** rule (`_anachronism`, using the shared
   `intervals_disjoint` predicate) reports this as a `Severity.error`, deterministically.

**Rationale**: Reading `factual_anchor.py` shows R5 compares the *anchor's span* against the
*constrained event's/timeline's interval* — it never reads manuscript prose. The verify skill
(`bookwright-verify.md`) is the only thing that reads the manuscript. Conflating them would
make the test either un-assertable (prose) or mis-scoped. The spec's Edge Cases and FR-006 vs
FR-007 already separate them; this decision records the mechanism behind that split.

**How R5 fires deterministically**: `bible/timeline.md` events accept `begin`/`end`/`date`
year fields (confirmed in `io/bible.py`, `EVENT_ITEM_KEYS`, mapped to `NarrativeEvent` with
`begin`/`end`, emitting the `crm:P4_has_time-span` boundaries `load_intervals` reads). So a
timeline event dated e.g. `date: 1850` constrained by an anchor with `begin: 1920` produces
disjoint ranges → one R5 error. Bounds are chosen far apart so the ranges are unambiguously
disjoint (no off-by-one).

---

## D3 — Modeling the planted "malformed anchor" (the warning)

**Decision**: The planted structural defect is an **under-reliable anchor** (R3): an anchor
whose only supporting source carries a reliability **below** the manifest's
`min_reliability_for_anchor`. With the manifest set to `min_reliability_for_anchor = "media"`,
a finding backed solely by a `baja` source, promoted to an anchor, parses cleanly (the reader
builds exactly the anchors authored — it does **not** enforce the threshold) but trips
`factual_anchor`'s R3 (`_under_reliable`) as a `Severity.warning`.

**Rationale**: The spec (FR-007, Assumptions, Edge Cases) requires a defect that is
**malformed at the validation layer, not the parse layer** — a parse-level fault (missing
facet, bad vocab, unknown promoted finding) aborts the build (`ResearchError`, strict fault
model in `io/research.py`) and the later stages never run. R3 under-reliability is exactly a
"parseable but structurally invalid" anchor. The reader's docstring and the iteration-13/14
tests confirm the reader does *not* gate promotion on reliability — that judgment is the
skill's and the validator's. The "Reliability threshold interplay" edge case is satisfied by
making the under-reliable source unambiguously `baja` under a `media` floor.

**Alternatives rejected**: an **unsourced** anchor (R1) — also a valid warning, but R1 is
suppressed when the promoted finding is absent and is a coarser signal; R3 better exercises
the multilingual/provenance richness (the `baja` source still carries full provenance) and
directly demonstrates `min_reliability_for_anchor`. We use R3 as *the* planted warning and
keep every other anchor clean so the count is exactly one.

**Exactness guarantee (FR-007 "no other violations")**: every *other* anchor must be
fully-sourced at/above `media`, promote a present finding, constrain a present entity, and
(if temporal) have a span consistent with its target. R2 (incomplete provenance) is avoided
by giving every source all required facets — which the strict reader already enforces at
build time anyway. R4 (missing entity) is avoided by linking only to entities present in the
bible. So exactly **one warning (R3)** + **one error (R5)** remain.

---

## D4 — The expected-findings oracle: format and location

**Decision**: A single file `tests/fixtures/tiny-historical/expected-findings.md` —
**co-located with the fixture, at its root, outside `bible/research/`** — with YAML
front-matter carrying the machine-checkable expectations and a Spanish prose body explaining
them. Front-matter keys (illustrative):

```yaml
---
factual_anchor:
  warning_anchor: <finding-id or anchor slug of the under-reliable anchor>
  error_anchor:   <finding-id or anchor slug of the anachronistic anchor>
  expected_counts: { error: 1, warning: 1 }
verify:
  manuscript_file: manuscript/NN-<slug>.md
  prose_anachronism: "<the planted prose contradiction, in words>"
  contradicted_anchor: <finding-id of the dated anchor the prose violates>
---
```

The E2E test **loads this file as the single source of truth** for its assertions (the
expected anchor identifiers and the `{error: 1, warning: 1}` counts), so the test and the
docs never drift — the same "one source, no drift" discipline as `tests/fixtures/research.py`.

**Rationale**: The 2026-06-05 clarification and commit `65ca852` fixed: a *documented
procedure*, not a committed LLM transcript; the deterministic expected findings stated in the
docs; the oracle **co-located inside the fixture dir** and **presence-checkable**. Front-matter
+ prose satisfies plain-text (Constitution I) and lets the test both *presence-check* it and
*read* the expectations rather than hard-coding them. It MUST sit **outside `bible/research/`**
so the strict `map_research` reader never tries to parse it as a topic file (it globs
`bible/research/*.md`). The fixture root is safe: `graph build` only reads `bible/`.

**Alternatives rejected**: (a) a committed verbatim `verify-report.md` — explicitly rejected
by the clarification (rots, can't be CI-verified); (b) a TOML file — Markdown-with-front-matter
matches the project's research-file idiom and reads as documentation; (c) embedding the oracle
inside `bible/research/_index.md` — would be parsed by the reader and pollute the graph.

---

## D5 — What "E2E test" means here and where it lives

**Decision**: New module `tests/e2e/test_research_workflow.py`. It exercises the
**deterministic** stages in-process via `CliRunner`: `graph build --json` → `graph query
--json` (anchors + their claims/spans) → `validate --json` (assert exactly one R3 warning +
one R5 error from `factual_anchor`, no other research findings). The **verify** stage is a
documented manual step (quickstart); the test asserts only its *preconditions* (D6).

**Rationale**: `tests/e2e/` already exists with `test_full_workflow.py` (the
init→build→query→validate CLI walk) and `test_fixtures.py` (copy-to-tmp + in-process CLI). The
spec's Assumptions name `tests/e2e/` and "fixtures-as-input, `tmp_path` where a project is
mutated" — this matches. The LLM `bookwright-verify` stage stays manual by design (§ 20.6,
Constitution VIII's clarified Agent-Skill E2E split): an LLM-judgment step is not
deterministically CI-testable.

---

## D6 — Asserting the verify preconditions (FR-012)

**Decision**: The test asserts the two deterministic inputs the manual verify step needs:

1. **Anchors are queryable** — the payoff SPARQL (anchor `bw:promotes` finding `bw:claim`,
   `bw:supportedBy` source) returns the fixture's anchors with their claims/sources, including
   the dated anchor the prose contradicts.
2. **The `bookwright-verify` skill is materialized** — run `bookwright integration use claude`
   in the `tmp_path` copy, then assert `.claude/skills/bookwright-verify/SKILL.md` exists
   (and, lightly, that `bookwright-research`'s does too). (The committed fixture tree carries
   no `.claude/`; materialization happens in the tmp copy, mirroring `test_fixtures.py`'s
   source-only guard.)

**Rationale**: This is exactly what `bookwright-verify.md`'s "Procedimiento" reads — the graph
anchors and the skill being present. The test confirms the manual step *can* run; the docs
(quickstart + research page) state what it *should* find (from the oracle). No LLM is invoked.

---

## D7 — Documentation placement and the docs-match gate

**Decision**:
- New top-level page `docs/research.md` (Spanish) covering the five required topics
  (what research is, Source/Finding/Anchor, the research-skill protocol, two-layer
  verification, multilingualism & provenance). It also documents **`bookwright-research`** and
  **`bookwright-verify`** (FR-016) and references the worked fixture + its oracle.
- `docs/validation.md` gains `factual_anchor` under "Validadores integrados" (FR-016).
- `docs/authoring.md` skills reference notes the two new M4 skills (cross-link).
- New `docs/changelog.md` with a **v0.2.0** entry (+ a retroactive v0.1.0 entry); add both
  `research.md` and `changelog.md` to `mkdocs.yml` `nav`.

**Rationale — do NOT put the skills under `docs/commands/`**:
`tests/e2e/test_docs_commands_match.py` introspects the live Typer app and asserts the
`docs/commands/` set **equals the CLI leaf-command set**. `bookwright-research` /
`bookwright-verify` are **Agent Skills, not CLI verbs**, so a page for them under
`docs/commands/` would make that test fail (an "extra command"). FR-016 says "command
reference", which here means the *authoring/skills* reference (where the other generative
skills already live, in `docs/authoring.md`) plus the research page — not the CLI command
directory. The site is `strict: true`, so every new page must be in `nav` with no broken
links (this is the FR-021 zero-warnings gate).

**Changelog**: no `CHANGELOG.md` exists anywhere today; the docs site is the home for it.
Create `docs/changelog.md` (Spanish prose) rather than a root file, to keep it in the
navigable site and under the strict build.

---

## D8 — The fixture's manifest configuration

**Decision**: `tiny-historical/manifest.toml` mirrors `tiny-novel`'s shape (schema
`golem-1.1`, `uri_base = "https://example.org/tiny-historical/"`, `indexer = "rdflib"`,
`[integration] key = "claude"`) and adds:

```toml
[research]
enabled = true
source_languages = [<the foreign ISO-639-1 codes actually used, e.g. "de", "fr">]
min_reliability_for_anchor = "media"

[validators]
enabled = []      # all built-ins active (incl. factual_anchor)
disabled = []
custom = []
```

`factual_anchor` is **auto-discovered** as a built-in (the registry walks the `validators`
package via `pkgutil`; no hand-registration), so leaving `enabled`/`disabled` empty activates
it. It self-inerts unless `[research].enabled` and ≥1 anchor exist — both true here.

**Open verification (resolve in implementation, not blocking)**: whether
`[vocabularies] active = ["sources"]` is *required* for build/validate. The existing
iteration-12/13/14 tests build and validate research projects with **no** `[vocabularies]`
block at all, so it appears **not** required. The implementation will use the minimal config
that works and only activate `sources` if a build/validate actually needs it — favoring "what
the code requires" over the spec's Assumption wording (which is advisory).

---

## D9 — Proving inertness (FR-013 / FR-014)

**Decision**: Two assertions in the same E2E module, no new permanent fixture:
- **No-directory case (FR-013)**: reuse `tiny-novel` (research-free). Build → query →
  validate; assert zero research entities (the derived `graph.ttl` carries no `bw:` prefix and
  the E13 count equals the bible baseline) and zero `factual_anchor` findings — byte-for-byte
  the v0.1 behavior. This reuses the exact regression pattern in `test_research_build.py`.
- **Disabled-block case (FR-014)**: `copy_fixture("tiny-historical", tmp_path)`, flip
  `[research].enabled = false` in the copied `manifest.toml`, then build → validate; assert
  `factual_anchor` produces **no** findings and overall validation behaves like a clean
  project. `factual_anchor.validate` returns `[]` immediately when `research.enabled is False`.

**Rationale**: Matches the spec's clarification (reuse existing research-free fixtures + flip a
tmp copy; no dedicated disabled fixture). Both inertness paths are already supported by the
validator's early-return guards; the test just exercises them on the real fixtures.

---

## D10 — Coverage policy

**Decision**: Keep the **single** enforced gate at ≥ 80 % global (`fail_under = 80` in
`[tool.coverage.report]`, unchanged). The ≥ 85 % target on M4 code is **report-only**,
verified at review — **no** second per-package `fail_under`, no `--cov-fail-under` anywhere.

**Rationale**: The 2026-06-05 clarification chose report-only to preserve "one source, no
drift". This iteration mostly adds tests/fixtures/docs, so global coverage rises, not falls;
the M4 ≥ 85 % figure is computed and noted in the PR, not gated.

---

## D11 — Scope guard

**Decision**: No vector search, no ChromaDB, no new validator/provenance/skill behavior, no
"future X" plumbing (FR-022, Constitution Scope & Release Discipline). Verification reads the
research Markdown / graph directly. This iteration is fixtures + tests + docs only.
