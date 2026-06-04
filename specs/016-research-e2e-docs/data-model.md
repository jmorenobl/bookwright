# Phase 1 — Data Model

This iteration introduces **no new code-level entities** (no Pydantic model, no validator, no
manifest field). The "entities" here are the **fixture's data shape**, the **planted-defect
model**, and the **oracle file schema** that the E2E test and docs consume. All existing
shapes (`Source`, `Finding`, `Anchor`, `NarrativeEvent`, `ResearchBlock`, `Violation`) are
reused unchanged.

---

## E1 — `tiny-historical` fixture (the worked example)

A valid, *finished* Bookwright project with a historical setting. Same skeleton as
`tiny-novel`, plus a populated `bible/research/` and an `expected-findings.md` oracle.

| Part | Files | Constraints (FR) |
|---|---|---|
| Manifest | `manifest.toml` | `[research] enabled=true`, `source_languages=[…]`, `min_reliability_for_anchor="media"`; all built-in validators active (FR-001, D8). |
| Bible | `bible/constitution.md`, `bible/characters/*.md`, `bible/settings/*.md`, `bible/timeline.md` | Coherent short narrative; **≥1 timeline event carries a year** (`date`/`begin`/`end`) so R5 has an interval to contradict (FR-004/FR-006). |
| Research | `bible/research/sources.md`, `bible/research/<topic>.md`, `bible/research/_index.md` | Several Sources w/ full provenance incl. ≥1 foreign-language (translation); Findings citing them; several Anchors incl. ≥1 temporal; anchors link to real bible entities (FR-002/FR-003/FR-004/FR-005). |
| Outline | `outline/*.md` | Standard skeleton (synopsis/structure/arcs/scenes), enough to be a valid project. |
| Manuscript | `manuscript/NN-<slug>.md` | ≥1 chapter; contains the **prose anachronism** that contradicts a dated anchor (FR-006). |
| Oracle | `expected-findings.md` | Co-located, presence-checkable, machine-readable (E3); states the deterministic expected findings (FR-012). |

**Invariants** (asserted, mirroring `tests/fixtures/test_fixtures.py`): the committed tree is
source-only (no `bible/graph.ttl`, no `.claude/`/`.agents/`, no `SKILL.md`); no
`[PENDING: …]` sentinels survive. **Not** added to the clean-fixtures parametrization (it
validates with one warning + one error by design).

### Source provenance (E1a) — reused `Source` facets

Every Source carries all reader-required facets (`name`, `reference`, `author`,
`original_language`, `type` ∈ controlled vocab, `reliability` ∈ {alta,media,baja},
`reliability_justification`, `access_date`, `original_quote`), plus `translation` **iff**
`original_language ≠ book.language` (FR-003, multilingual provenance; enforced fatally by the
reader, so any omission aborts the build — which is *why* the planted warning cannot be a
missing facet, see E2).

---

## E2 — Planted-defect model (the spine of the deterministic test)

Exactly **three** planted defects, in **two** detection layers. Everything else in the fixture
is clean.

| # | Defect | Where | Detected by | Severity | FR |
|---|---|---|---|---|---|
| 1 | **Under-reliable anchor**: an anchor whose only supporting source is `baja`, below the manifest's `media` floor. Parses fine (reader does not gate promotion). | one `bible/research/<topic>.md` anchor | `factual_anchor` **R3** (`_under_reliable`) | **warning** | FR-007 |
| 2 | **Time-span anachronism**: an anchor whose year-span is disjoint from the dated timeline event it `constrains`. | one anchor + its dated target event | `factual_anchor` **R5** (`_anachronism`) | **error** | FR-007 |
| 3 | **Prose anachronism**: manuscript prose that contradicts a dated anchor (object/tech/event out of its era). | `manuscript/NN-<slug>.md` | `bookwright-verify` **LLM skill** (manual) | report `error` | FR-006 |

**Exactness** (FR-007 "no other research violations"): every other anchor is fully-sourced at
≥ `media`, promotes a present finding, constrains a present entity, and (if temporal) has a
span consistent with its target. Build-time strictness already guarantees every Source is
provenance-complete, so R2 cannot fire. ⇒ the validate run reports **exactly** `{warning: 1,
error: 1}` from `factual_anchor`. Defects #1 and #2 SHOULD be **different anchors** so each
rule fires once cleanly (an anchor that is both under-reliable *and* anachronistic would
emit two findings on one anchor — allowed, but separating them keeps the mapping 1:1 and the
oracle unambiguous).

**Distinct failure modes (Edge Case)**: defect #1 is *validation-malformed* (parseable),
**not** *parse-malformed* — a parse fault (missing facet, bad vocab, unknown promoted finding)
would raise `ResearchError` and abort `graph build`, so the query/validate stages would never
run. The fixture keeps the parse layer clean.

---

## E3 — Expected-findings oracle (`expected-findings.md`)

Co-located in the fixture root (outside `bible/research/`). Plain-text Markdown with YAML
front-matter; the E2E test loads it as the single source of truth for its expectations
(no drift), and the docs quote it.

| Field | Type | Meaning |
|---|---|---|
| `factual_anchor.warning_anchor` | str | identifier (finding id / anchor slug) of the under-reliable anchor (defect #1). |
| `factual_anchor.error_anchor` | str | identifier of the anachronistic anchor (defect #2). |
| `factual_anchor.expected_counts` | map | `{error: 1, warning: 1}` — the exact `factual_anchor` finding counts. |
| `verify.manuscript_file` | str | the chapter holding the prose anachronism (defect #3). |
| `verify.prose_anachronism` | str | the planted contradiction, in words (what verify should flag). |
| `verify.contradicted_anchor` | str | the dated finding/anchor the prose contradicts. |

Body: Spanish prose explaining each expected finding for a human reader (this *is* the
documented expected-findings statement FR-012 requires).

**Constraint**: the file MUST NOT live under `bible/research/` (the strict `map_research`
reader globs `bible/research/*.md` and would try to parse it as a topic). Fixture root is
safe — `graph build` reads only `bible/`.

---

## E4 — Research workflow test (`tests/e2e/test_research_workflow.py`)

Not a data entity, but the consumer contract. Reuses `copy_fixture` + `CliRunner`. Assertions
map 1:1 to FR-008..FR-014 — see `contracts/e2e-test-contract.md`. Loads `expected-findings.md`
to drive the `factual_anchor` count + identifier assertions. Stays ≤ 500 lines (Constitution
IV); split into helper-grouped sections if it approaches the limit.

---

## E5 — Documentation set

| Artifact | Type | FR |
|---|---|---|
| `docs/research.md` | new page: 5 topics + the two skills + worked-fixture reference | FR-015/FR-016/FR-017 |
| `docs/validation.md` | edit: `factual_anchor` row in "Validadores integrados" | FR-016 |
| `docs/authoring.md` | edit: skills reference notes `bookwright-research` / `bookwright-verify` | FR-016 |
| `docs/changelog.md` | new page: v0.2.0 entry (+ retroactive v0.1.0) | FR-018 |
| `mkdocs.yml` | edit: `nav` gains research + changelog; `strict: true` kept | FR-017/FR-021 |
