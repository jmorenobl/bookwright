# Quickstart — validate the research status queue

Proves the iteration end-to-end: the edited source materializes/lints in both
integrations, its body references `bookwright status`, the budget holds, and the
bilingual trigger is intact. See [contracts/research-skill.md](./contracts/research-skill.md)
for the invariant↔test map and [data-model.md](./data-model.md) for the read view.

## Prerequisites

```bash
uv sync
```

## 1. Automated gates (the binding checks)

```bash
# The whole suite — must stay green at ≥ 80% coverage.
uv run pytest

# Focused: both-integration materialize + lint, body-references-status (RQ-1/RQ-9).
uv run pytest tests/integrations/test_research_skill.py -q

# Body stays under the 5000-token tier-2 budget (RQ-9).
uv run pytest tests/resources/test_command_budget.py -q

# Bilingual description preserved verbatim (RQ-7).
uv run pytest tests/integrations/test_descriptions.py -q

# Standard gates.
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

**Expected**: all green. `test_research_skill.py` includes the new
`bookwright status` assertion; nothing in `src/` changed, so coverage is
unaffected.

## 2. Inspect the materialized skill (manual spot-check)

```bash
# In a scratch project initialized with `bookwright init`, confirm the skill
# carries the new first step for both integrations.
grep -n "bookwright status" .claude/skills/bookwright-research/SKILL.md
grep -n "bookwright status" .agents/skills/bookwright-research/SKILL.md
```

**Expected**: both files reference `bookwright status` in the no-topic protocol.

## 3. Behavioral walkthroughs (agent-driven, per spec acceptance)

These are LLM-driven and not part of the deterministic suite — run them in an
agent session against a fixture project.

| Scenario | Setup | Expected |
|---|---|---|
| US1 — queue start | project with ≥ 1 open question or ≥ 1 unresolved anchor; invoke research **with no topic** | skill runs `bookwright status --json`, presents the grouped/numbered queue, offers "these N / a new topic" — never a blank prompt |
| US1 — pick item | from the queue, author picks one number | that item becomes the topic; the seven-step procedure runs unchanged |
| US1 — pick many | author picks 2+ numbers | the procedure runs **once per item**, sequentially (clean per-topic provenance) |
| US2 — top-down | invoke **with** an explicit topic | no status step; proceeds straight into decomposition/search |
| US3 — empty queue | project with no open questions and no unresolved anchors | falls back to asking which topic; no error |
| US3 — status unavailable | not-yet-buildable project (or `status` errors) | falls back to asking the topic; no error, no dead end |
| Edge — research disabled | `[research].enabled = false` | inert-system notice; queue step does not run |

## Done when

- Section 1 gates are all green.
- Section 2 confirms `bookwright status` is present in both materialized skills.
- Section 3 walkthroughs behave as tabled (manual confirmation).
