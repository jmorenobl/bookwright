# Data Model — the research queue as the skill reads it

No new persisted entities and **no Python model** are introduced in this
iteration. The "data model" here is the *read view* the skill's protocol takes
over the frozen `bookwright status --json` document (iteration 020). It is
documented so the prose step and its test reference the exact fields.

## Read view (consumed from `status --json`)

The skill reads two first-class fact lists from `state` (never `next_actions`).
Shapes are normative per
[cli-status.md](../020-status-command/contracts/cli-status.md).

### Research queue (author-facing, derived by the skill)

The ordered, grouped, soft-capped list presented on the no-topic path. Built in
memory from the two item kinds below; never persisted, never cached by the skill
(read fresh each invocation).

| Aspect | Rule | Source |
|---|---|---|
| Grouping | open questions first, then unresolved anchors | FR-002a |
| Ordering | preserve status' corpus-stable item order within each group | FR-002a, cli-status §items |
| Numbering | each presented item gets a stable 1..N number | FR-002a |
| Soft cap | ≈ top 10 combined; beyond it show `+M more (run \`bookwright status\` for the full list)` | FR-002a |
| Placeholders | never invented when a group is empty — omit that group | FR-002a, edge "Partial queue" |

### Open research question (queue item kind 1)

Read from `state.open_questions.items[]`.

| Field | Meaning | Used for |
|---|---|---|
| `id` | question identifier (e.g. `q-mercury`) | stable reference |
| `text` | the unresolved sub-question | the line the author reads/picks |
| `file` | where it's recorded (e.g. `bible/research/_index.md`) | identifying context |

`state.open_questions.count == len(items)`.

### Unresolved anchor (queue item kind 2)

Read from `state.unresolved_anchors.items[]`.

| Field | Meaning | Used for |
|---|---|---|
| `promotes` | the finding/relationship the anchor promotes (e.g. `rel-001`) | what it asserts |
| `constrains` | the narrative entity it binds (e.g. `timeline`) | identifying context |
| `file` | where it lives (e.g. `bible/research/medicine.md`) | identifying context |
| `problems` | sourcing problems (e.g. `["under_reliable"]`) | why it's in the queue |

`state.unresolved_anchors.count == len(items)`.

> **Not read**: `state.low_reliability_findings` (a different recommendation path,
> spec assumption), `state.validation`, and `next_actions[]` (clarification #1).

## Topic (the procedure's input)

| Origin | How obtained | Then |
|---|---|---|
| Queued item | author selects one or more numbers | each selection becomes one determined topic |
| New subject | author answers "a new topic: X" | X becomes the topic |
| Explicit (top-down) | given as `$ARGUMENTS` at invocation | the queue step is skipped entirely |

State transitions (no-topic path):

```text
invoke (no topic)
  → run `bookwright status --json`
    → [queue non-empty] present grouped/numbered queue + "these N / new topic" choice
        → author picks 1 item      → 1 topic            → seven-step procedure ×1
        → author picks M (>1) items → M topics           → seven-step procedure ×M (sequential, FR-003/FR-007)
        → author gives "new topic X" → topic X           → seven-step procedure ×1
        → author answer ambiguous/empty → re-ask (edge case)
    → [queue empty OR status unavailable/degraded/errored] → ask which topic (fallback, FR-005/FR-006)
  → [research disabled] inert-system notice (precedence over queue step, unchanged)
```

The seven-step procedure itself (decompose → search → provenance → discrepancies
→ anchor promotion → open questions → graph build) is **unchanged** (FR-007); per
multi-item pass it operates on exactly one determined topic to preserve clean
per-topic provenance (clarification #2).
