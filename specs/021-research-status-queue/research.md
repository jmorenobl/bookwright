# Phase 0 Research — `bookwright-research` status queue

All NEEDS CLARIFICATION resolved (the spec's three clarifications already fix the
hardest choices). The decisions below are the technical ones the plan rests on.

## D1 — Source of the queue facts: raw `state.*`, not `next_actions[]`

- **Decision**: The no-topic step reads `state.open_questions.items` and
  `state.unresolved_anchors.items` from `bookwright status --json` and builds the
  queue itself. It does **not** read or echo `next_actions[]`.
- **Rationale**: Clarification #1. `next_actions[]` is iteration 020's
  *cross-skill handoff* (a prompt addressed to the research skill from outside),
  not the research skill's view of its own backlog. Reading the first-class facts
  keeps this skill's presentation (grouping, numbering, soft cap, per-item
  context) under its own control and avoids coupling to the wording of a prompt
  it does not own. The status contract
  ([cli-status.md](../020-status-command/contracts/cli-status.md)) freezes both
  fact shapes: each item carries `{id|promotes/constrains, text|problems, file}`
  and is ordered by corpus-stable keys with `count == len(items)`.
- **Alternatives considered**: consume `next_actions[]`'s ready-made prompt —
  rejected: it would surface only a templated sentence, lose per-item selection,
  and re-couple the two skills the way clarification #1 forbids.

## D2 — Where the step lives and how it's invoked: prose in the skill body

- **Decision**: Add the conditional step as authoring prose in the existing
  `## Procedimiento` / input section of `bookwright-research.md`. The agent runs
  `bookwright status --json` with its own shell tool, parses JSON, and presents
  the queue. No Python is written.
- **Rationale**: The behavior is a *protocol* the LLM follows, exactly like the
  current "if no topic, ask which" line it replaces. The skill already instructs
  the agent to run a CLI (`bookwright graph build --json` as its final step), so
  invoking `bookwright status --json` as a first step is the same well-trodden
  pattern (Principle IX boundary). Putting it in code would mean inventing a CLI
  surface the spec explicitly keeps out of scope.
- **Alternatives considered**: a new `bookwright research --queue` helper command
  — rejected: out of scope, adds CLI surface, duplicates what `status` already
  emits, and the spec confines the change to the command **source** (FR-009).

## D3 — Reusing the iteration-9 materialization pipeline unchanged

- **Decision**: Re-materialize via the existing
  `generate_skill_md(source, dest, integration)` over `iter_command_sources()`
  for `ClaudeIntegration` and `GenericIntegration`. No pipeline code is added or
  duplicated.
- **Rationale**: FR-010. The pipeline already discovers the source by filename
  stem, strips/maps front-matter, transforms `{ARGS}` → `$ARGUMENTS`, copies
  cited `references/`, and lints. An edited body flows through it with zero
  changes — confirmed by reading
  [materialize.py](../../src/bookwright/integrations/materialize.py)
  (`iter_command_sources` L46, `generate_skill_md` L136). The existing
  [test_research_skill.py](../../tests/integrations/test_research_skill.py)
  already exercises both integrations + `lint_skill_md` for this exact command.
- **Alternatives considered**: none viable — duplicating the pipeline is a
  Principle V/VI smell and an explicit FR-010 prohibition.

## D4 — Bilingual trigger & description: leave the front-matter untouched

- **Decision**: Do not change the `description` front-matter. It already carries
  both ES ("investiga <tema>", "documenta <tema> con fuentes") and EN ("research
  <topic>", "find sources on <topic>") trigger phrasings. Edit body prose only.
- **Rationale**: FR-008 / SC-005 require the bilingual trigger to *survive*; the
  surest way is to not touch it. Leaving `description` as-is also avoids touching
  the `SKILL_DESCRIPTIONS` mirror in `integrations/descriptions.py`, whose
  `test_v0_equality_gate_mirrors_source_frontmatter` enforces verbatim parity —
  no description edit means no risk of drift and no second file to change.
- **Alternatives considered**: extend the description to advertise the
  queue-start behavior — rejected: unnecessary for triggering, would force a
  synchronized edit to `descriptions.py`, and risks the 1024-char cap for no
  behavioral gain (the body governs behavior).

## D5 — Body token budget

- **Decision**: The added step (queue read + grouping/cap rules + the multi-item
  and fallback notes, in Spanish to match the file) adds well under ~250 tokens.
- **Rationale**: Measured current body ≈ 1135 approx-tokens against the 5000-token
  ceiling enforced by
  [test_command_budget.py](../../tests/resources/test_command_budget.py); ample
  headroom. Reference material that is long stays in `references/` per Principle
  VII — but nothing here is long enough to offload.
- **Alternatives considered**: offloading the queue protocol to a new
  `references/status-queue.md` — rejected as premature: the step is short, and an
  extra reference file adds a copy-along dependency for no budget pressure.

## D6 — Graceful degradation contract

- **Decision**: Treat **all** of {empty queue, `graph.available == false`,
  non-zero `status` exit, unparseable output} as "no queue" → fall back to asking
  the topic, never erroring or blocking.
- **Rationale**: FR-005 / FR-006 / SC-003 and the spec edge cases. The status
  contract guarantees a degraded but exit-0 report when there is nothing to build
  from (cli-status.md "Degraded-state guarantees"); the prose instructs the agent
  to also swallow the harder failures (exit ≠ 0) and fall back, so the author is
  never stuck. The `[research].enabled = false` inert-system behavior keeps
  precedence over the queue step (existing line, unchanged).
- **Alternatives considered**: surface a status error to the author — rejected:
  violates FR-006's "must not break, error out, or block."

## D7 — Verification strategy

- **Decision**: (a) extend `test_research_skill.py` with a contract assertion
  that the (source and materialized) body references `bookwright status`; (b)
  rely on the already-present both-integration materialize+lint test and the
  budget/description tests unchanged.
- **Rationale**: Per Constitution § VIII the sound E2E mode for an authoring
  skill is materialization compliance against `lint_skill_md`; the new behavior
  is a body string, so the smallest faithful assertion is "the body tells the
  agent to consult `bookwright status`." This guards against the protocol step
  being lost in a future edit without over-fitting to exact prose.
- **Alternatives considered**: a full LLM-in-the-loop behavioral test — rejected:
  non-deterministic, out of the repo's test discipline, and unnecessary to prove
  the protocol text is present and the skill still materializes/lints.
