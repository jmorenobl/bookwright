# Quickstart: validating outline narrative-unit ingestion

A runnable walkthrough proving G9/G10 are alive. Assumes `uv sync` has installed the
dev environment. See [data-model.md](./data-model.md) and
[contracts/outline-units-ingestion.md](./contracts/outline-units-ingestion.md) for the
full rules; this guide only runs them.

## Prerequisites

```bash
uv sync
```

## 1. Author two unit cards sharing a function (US1 / SC-001/002)

In a project that already has `bible/characters/`, add:

`outline/units/opening.md`
```markdown
---
name: Opening
functions: [interdiction, departure]
---
The hero is warned and then leaves home.
```

`outline/units/return.md`
```markdown
---
name: Return
functions: [departure]
roles: [hero]
---
```

Assuming a character declares `narrative_roles: [hero]`.

## 2. Build the graph

```bash
uv run bookwright graph build --json
```

Expected: exit 0; the JSON `report` counts both cards under `files_processed` and the
new entities under `entities`; no card under `skipped`.

## 3. Query the plot structure (SC-001/002/004)

```bash
uv run bookwright graph query --json \
  'SELECT (COUNT(DISTINCT ?u) AS ?units) (COUNT(DISTINCT ?f) AS ?funcs) WHERE {
     ?u a <…golem…#G9_Narrative_Unit> . OPTIONAL { ?u <…crm…P67_refers_to> ?f .
       ?f a <…golem…#G10_Narrative_Function> } }'
```

Expected: `units = 2`, `funcs = 2` (`departure` deduplicated across both cards).
A "which units perform `departure`" query returns both `Opening` and `Return`; the
`hero` role on `Return` yields one unit→role edge to the character's role node.

## 4. Soft-miss on an unknown role (US2 / SC-004)

Add `roles: [ghost]` (no character plays `ghost`) to a card and rebuild: the unit is
still built, no role edge for `ghost`, and the build report lists one
unresolved-reference warning for it (build stays exit 0).

## 5. Robustness (SC-003 / FR-006-009)

- A card with no front-matter → listed under `skipped`, build continues.
- `functions: "not-a-list"` → card skipped with a reason; no `interdiction` function
  leaks into the graph.
- Two cards both named `Opening` → `graph build` exits non-zero with the standard
  `--json` error envelope (slug collision).
- Delete `outline/units/` entirely → the graph is byte-for-byte what it was before.

## 6. Automated gates

```bash
uv run pytest tests/io/test_outline.py tests/golem/test_ingestion_parity.py
uv run pytest                      # full suite, ≥ 80% coverage
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

Expected: green. The parity test now observes G9/G10 as **reachable** (fed by the
`parity-exercise` fixture's unit card) with the orphan set reduced to
`{NarrativeSequence, RelationshipRole, PsychologicalState}`.

## 7. Authoring surface (US3 / SC-007)

```bash
uv run pytest tests/integrations/test_materialize.py
```

Confirms the regenerated `bookwright-outline` `SKILL.md` (both `claude` and `generic`)
documents the `outline/units/` card format, keeps bilingual triggers, and passes the
skill lint gate. A freshly `bookwright init`-ed project contains `outline/units/`.
