# Contract — `bookwright-research` body protocol (iteration 021)

Binding authoring invariants added/preserved by this iteration on the
`bookwright-research` command source and its materialized `SKILL.md`. The
front-matter/length/lint invariants from iteration 013
([013 research-skill.md](../../013-research-skill/contracts/research-skill.md))
still hold and are **not restated** — they are re-verified by the unchanged
`tests/integrations/test_research_skill.py`.

## Subject

- Source: `src/bookwright/resources/commands/bookwright-research.md` (the only
  edited artifact).
- Materialization: the **unchanged** iteration-9 pipeline
  (`generate_skill_md` over `iter_command_sources`) for `claude` and `generic`.

## Invariants

| ID | Invariant | FR / SC | Verified by |
|---|---|---|---|
| RQ-1 | The body references `bookwright status` — the no-topic protocol consults the derived status as its first step. | FR-001, SC-002 | **new** `test_body_consults_status_queue` in `test_research_skill.py` (source body + materialized body contain `bookwright status`) |
| RQ-2 | The status step is **conditional on no topic**: when a topic is given the body keeps the top-down procedure with no mandatory status step. | FR-004, SC-004 | spec acceptance US2-AS1; prose review |
| RQ-3 | The queue is built from the **raw facts** `state.open_questions` / `state.unresolved_anchors`, not `next_actions`. | FR-002, clar. #1 | **`test_body_consults_status_queue`** deterministically asserts the body contains `open_questions` **and** `unresolved_anchors` (the queue is built from the raw facts); the "not `next_actions`" side is by prose review only — the body legitimately names `next_actions` to forbid it, so an absence check would be brittle |
| RQ-4 | Queue presentation: grouped (open questions, then unresolved anchors), numbered, corpus-stable order, soft cap ≈10 with a `+M more` overflow note, no invented placeholders. | FR-002a | prose review against data-model |
| RQ-5 | The body offers the "investigate one/more queued items **or** a new topic" choice and, on a multi-item selection, runs the seven-step procedure **sequentially per item**. | FR-003, FR-007, clar. #2 | prose review |
| RQ-6 | Graceful fallback: empty/unavailable/degraded/errored status → ask the topic, never error or block; `[research].enabled = false` inert notice keeps precedence. | FR-005, FR-006, SC-003 | prose review against spec edge cases |
| RQ-7 | The bilingual `description` trigger (ES + EN phrasings) is preserved verbatim. | FR-008, SC-005 | unchanged `tests/integrations/test_descriptions.py` (`test_v0_equality_gate_mirrors_source_frontmatter`) |
| RQ-8 | Change confined to the `bookwright-research` source — no edit to `bookwright status` or any other skill/command. | FR-009 | git diff scope; review |
| RQ-9 | Materialized `SKILL.md` lints green for **both** integrations; body stays < 5000 approx-tokens. | FR-010, FR-011, SC-001, SC-006 | unchanged `test_research_skill.py` (both-integration + `lint_skill_md`) and `tests/resources/test_command_budget.py` |

## Test map (delta this iteration introduces)

- **Add** to `tests/integrations/test_research_skill.py` one test,
  `test_body_consults_status_queue`, mirroring the existing
  `test_body_instructs_the_final_graph_build` pattern. Against the source body
  **and** the materialized body (≥1 integration) it asserts: `"bookwright status"`
  is present (RQ-1); and `"open_questions"` **and** `"unresolved_anchors"` are
  present (RQ-3 / FR-002 — deterministic guards on stable iteration-020 contract
  field names, no over-fitting to prose). It deliberately does **not** assert
  `"next_actions"` is absent (the prose names it to forbid its use, so an absence
  check would be brittle — that side stays prose-review). This covers RQ-1 + the
  positive half of RQ-3.
- **Reuse unchanged**: `test_materializes_and_lints_for_both_integrations`
  (RQ-9), `test_command_budget.py` (RQ-9 budget),
  `test_descriptions.py::test_v0_equality_gate_mirrors_source_frontmatter`
  (RQ-7).

## Non-goals (out of contract)

- No assertion on exact queue wording or item count — those are runtime,
  LLM-driven, and the spec keeps fetch/search out of scope.
- No change to the `bookwright status` JSON contract (iteration 020 is closed).
