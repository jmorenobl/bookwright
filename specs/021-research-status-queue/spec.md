# Feature Specification: `bookwright-research` consumes the status research queue

**Feature Branch**: `021-research-status-queue`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Necesidad: cuando el autor invoca la skill de investigación sin un tema explícito, hoy esta pregunta «¿qué investigamos?» en blanco, aunque el proyecto ya contiene preguntas de investigación abiertas y anclas sin fuente suficiente. Esa cola es justamente lo que `bookwright status` (iteración 020) computa. La skill debe consumirla (entrada bottom-up) y ofrecerla como punto de partida, manteniendo la entrada top-down (tema explícito) cuando el autor sí lo da."

## Clarifications

### Session 2026-06-12

- Q: When building the no-topic queue, should the skill read the raw status
  facts (`state.open_questions`, `state.unresolved_anchors`) or the pre-built
  `next_actions[]` research prompt? → A: Read the raw first-class facts; the
  skill does **not** consume the `next_actions` research prompt (that entry is
  iteration 020's cross-skill handoff, not input the research skill reads about
  itself).
- Q: If the author selects more than one queued item, how does the protocol
  handle them? → A: Sequentially — the full seven-step procedure runs once per
  selected item (one determined topic per pass), preserving clean per-topic
  provenance; selections are not merged into a single combined pass.
- Q: How is the queue presented on a project with many items? → A: Grouped by
  kind (open questions first, then unresolved anchors), each numbered and
  preserving the status contract's corpus-stable ordering, with a soft display
  cap (~top 10 combined) and a "+M more (run `bookwright status` for the full
  list)" overflow note; never invent placeholder items.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start from the project's own open research queue (Priority: P1)

An author opens a session and asks to research, but without naming a topic
("investiga", "research", "find sources" with no subject). Instead of being met
with a blank "what shall we research?", the skill surfaces the work the project
already knows is pending — its open research questions and the anchors that lack
a sufficiently reliable source — as a numbered queue, and invites the author to
pick from it or to name a new topic instead.

**Why this priority**: This is the concrete pain the iteration exists to fix.
The structural queue already exists (computed by `bookwright status`, iteration
020) but nothing consumes it; the author is forced to re-derive by hand what the
system already knows. Delivering only this story already removes the blank
prompt and closes the bottom-up loop.

**Independent Test**: On a project that has at least one open research question
or one unresolved anchor, invoke the research skill with no topic. The skill
presents those items as a queue and offers the "research these N / a new topic"
choice rather than asking the topic on a blank slate.

**Acceptance Scenarios**:

1. **Given** a project whose status reports 2 open research questions and 1
   unresolved anchor, **When** the author invokes research with no explicit
   topic, **Then** the skill first consults the project status, then presents
   the 3 items as a research queue and asks the author whether to investigate
   one/more of them or supply a new topic.
2. **Given** the author then picks one queued item, **When** the protocol
   continues, **Then** that item becomes the topic and the existing rigorous
   research procedure (the seven steps — decompose → search authoritative
   sources → cross-check provenances on sensitive topics → record full
   provenance → record each discrepant version → mark/promote anchors by the
   reliability threshold → leave unresolved sub-questions open — then the final
   `bookwright graph build`) runs against it unchanged.
3. **Given** the author instead answers "a new topic: X", **When** the protocol
   continues, **Then** X is treated as the topic exactly as the top-down path
   would.

---

### User Story 2 - Explicit topic keeps the top-down path (Priority: P2)

An author who already knows what they want invokes the skill with an explicit
topic ("investiga la logística de la Wehrmacht en 1943"). Nothing about the new
queue gets in the way: the skill proceeds straight into the research procedure
as it does today, without making a status consultation a mandatory first step.

**Why this priority**: The top-down entry is the established, working behavior
and must be preserved exactly. It guards against the bottom-up addition adding
friction or latency to the common case where the author already has a subject.

**Independent Test**: Invoke the research skill with an explicit topic. The
protocol proceeds into decomposition/search for that topic without requiring the
status queue step.

**Acceptance Scenarios**:

1. **Given** an explicit topic is supplied, **When** the author invokes
   research, **Then** the skill does not require the status-queue step and
   behaves as the current (pre-021) protocol does.

---

### User Story 3 - Graceful fallback when there is no pending work (Priority: P3)

An author invokes the skill with no topic on a project that has no open research
questions and no unresolved anchors (a clean or brand-new project), or where the
project status cannot be computed at all. The skill never breaks or blocks: it
quietly falls back to the current behavior of asking which topic to research.

**Why this priority**: Robustness. The bottom-up feature must degrade elegantly
to the existing behavior; an empty or unavailable queue must never leave the
author stuck or produce an error.

**Independent Test**: Invoke the research skill with no topic on a project with
an empty queue (and separately, on one where status is unavailable). In both
cases the skill ends up asking the author for a topic, with no error and no dead
end.

**Acceptance Scenarios**:

1. **Given** the project status reports zero open questions and zero unresolved
   anchors, **When** the author invokes research with no topic, **Then** the
   skill falls back to asking the author which topic to research.
2. **Given** the project status cannot be produced (e.g., not yet a buildable
   project), **When** the author invokes research with no topic, **Then** the
   skill still falls back to asking for a topic without surfacing an error or
   blocking.

---

### Edge Cases

- **Research system disabled** (`[research].enabled = false`): the existing
  "system is inert; do not produce graph-linked findings" behavior is
  unchanged and takes precedence over the queue step.
- **Partial queue**: only open questions but no unresolved anchors (or vice
  versa) — the skill presents the non-empty category and omits the empty one;
  it does not invent placeholder items.
- **Status reports a degraded state** (graph not available): treated like an
  empty/unavailable queue → fall back to asking the topic, no error.
- **Author supplies an ambiguous or empty answer** to the "these N or a new
  topic" choice: the skill re-asks rather than guessing.
- **A queued item is later resolved**: because the queue is read fresh from
  status each invocation (never cached by the skill), already-resolved items do
  not reappear.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When the research skill is invoked **without** an explicit topic,
  its protocol MUST consult the project's derived status as its first step,
  before any other research action.
- **FR-002**: From that status the skill MUST extract the project's open
  research questions and the anchors that lack a sufficiently reliable source
  ("unresolved anchors") **from the raw status facts** (`state.open_questions`
  and `state.unresolved_anchors`) — it MUST NOT consume the `next_actions[]`
  research prompt for this — and present them to the author as a numbered
  research queue, with enough identifying context per item for the author to
  choose.
- **FR-002a**: The queue MUST be presented grouped by kind (open questions
  first, then unresolved anchors), each item numbered and preserving the status
  contract's corpus-stable ordering. The skill MUST apply a soft display cap
  (≈ top 10 items combined) and, when more items exist, MUST show a "+M more
  (run `bookwright status` for the full list)" note rather than truncating
  silently. It MUST NOT invent placeholder items.
- **FR-003**: The skill MUST offer the author a clear choice between
  investigating one or more queued items and supplying a new topic instead, and
  MUST proceed with the author's selection. When the author selects more than
  one queued item, the skill MUST run the research procedure **sequentially —
  once per selected item** (one determined topic per pass), not as a single
  merged pass.
- **FR-004**: When the research skill is invoked **with** an explicit topic, it
  MUST proceed directly with the existing top-down procedure and MUST NOT make
  the status consultation a mandatory step.
- **FR-005**: When the consulted status reports no open questions and no
  unresolved anchors, the skill MUST fall back to the current behavior of asking
  the author which topic to research.
- **FR-006**: The skill MUST degrade gracefully when the status cannot be
  produced — it MUST NOT break, error out, or block, and MUST fall back to
  asking for a topic.
- **FR-007**: Once a topic is determined (whether chosen from the queue or
  supplied new), the remainder of the rigorous research procedure (the seven
  steps, provenance, anchor promotion threshold, open-question handling,
  persistence and reindex) MUST run unchanged. For a multi-item selection
  (FR-003) this procedure repeats per item, each pass operating on exactly one
  determined topic.
- **FR-008**: The skill's bilingual triggering MUST be preserved — it MUST keep
  triggering on both Spanish and English author prompts.
- **FR-009**: The change MUST be confined to the `bookwright-research` command
  source; it MUST NOT alter the `bookwright status` command (iteration 020) or
  any other skill.
- **FR-010**: The updated command source MUST be re-materialized into a valid
  `SKILL.md` through the existing materialization pipeline (iteration 009), for
  both the `claude` and `generic` integrations, with no new or duplicated
  pipeline.
- **FR-011**: The materialized `SKILL.md` MUST stay within the platform limits
  (valid front-matter, `name`/`description` length bounds, body within the
  established budget) so the existing lint gate passes.

### Key Entities *(include if data involved)*

- **Research queue**: the author-facing list presented when no topic is given.
  Composed of two item kinds read from the project status:
  - **Open research question**: an unresolved sub-question recorded in the
    research index, identified by its question id/text and source location.
  - **Unresolved anchor**: an anchor whose best source does not reach the
    reliability threshold (and/or is otherwise insufficiently sourced),
    identified by what it promotes/constrains and its source location.
- **Topic**: the subject the research procedure runs against — either an item
  selected from the queue or a new subject supplied by the author.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A freshly initialized project produces a valid
  `bookwright-research` skill in **both** integrations (the existing skill lint
  gate passes for each).
- **SC-002**: On a project with at least one open question or one unresolved
  anchor, a no-topic invocation results in the queue being presented (with the
  "these N / a new topic" choice) in 100% of cases, never a blank topic prompt.
- **SC-003**: On a project with an empty or unavailable queue, a no-topic
  invocation results in the topic-asking fallback in 100% of cases, with zero
  errors or blocked states.
- **SC-004**: An explicit-topic invocation never requires the status step — the
  top-down path is unchanged in 100% of explicit-topic cases.
- **SC-005**: The materialized skill triggers on both a Spanish and an English
  research prompt (both trigger phrasings remain present in the description).
- **SC-006**: All project quality gates remain green and the materialized
  `SKILL.md` stays within the platform body/front-matter limits.

## Assumptions

- The shape and field names of the status output consumed here are those frozen
  by iteration 020 (open questions and unresolved anchors are first-class facts
  in its JSON contract). This iteration only reads the raw fact lists
  (`state.open_questions`, `state.unresolved_anchors`); it does not consume the
  `next_actions[]` research prompt, nor does it extend or change the contract.
- "Anchors without sufficient source" maps to the status notion of *unresolved
  anchors* (anchors flagged with sourcing problems such as under-reliability);
  low-reliability findings are surfaced by a different recommendation path and
  are not part of this queue.
- The author drives the actual web search with their own tools; this skill
  instructs and writes text — it never implements fetching. (Unchanged from the
  current skill.)
- The status consultation is performed fresh on each no-topic invocation; the
  skill does not maintain its own cache of the queue.

## Dependencies

- **Iteration 020** (`bookwright status` — derived state + `next_actions`):
  provides the open-questions and unresolved-anchors facts the queue is built
  from. Merged on `main`.
- **Iteration 009** (materialize commands as Agent Skills): provides the
  command-source → `SKILL.md` pipeline this iteration re-runs for `claude` and
  `generic`.
- **Iteration 014** (`factual_anchor` validator): underpins how the status
  identifies anchors that lack sufficient sourcing.

## Out of Scope

- Changing the `bookwright status` command (iteration 020, closed).
- Wiring the rest of the skills to read status / adding a "next steps" block to
  them (iteration 022).
- Any search/fetch engine: the agent provides search; the skill instructs, it
  does not implement fetch.
