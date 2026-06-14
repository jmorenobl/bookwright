# Quickstart — Validate "Index objects (G16)"

Runnable validation scenarios that prove the feature end-to-end. Run from the repo
root in the project venv (`uv sync` first). Details live in
[data-model.md](data-model.md) and
[contracts/object-frontmatter.md](contracts/object-frontmatter.md).

## Prerequisites

```bash
uv sync
```

## Scenario 1 — An object file becomes a G16 node with provenance (FR-001/002, SC-001)

In a temp project with `bible/objects/excalibur.md` (`name: "Excalibur"`), build
the graph and assert exactly one `G16_Object` node whose identity carries a
`file:line` locator pointing at the `name:` key line.

```bash
uv run pytest tests/io/test_bible.py -k "object" -q
```

Expect: round-trip test green — one `Object` entity, URI `…/object/excalibur`,
provenance `bible/objects/excalibur.md:<line of name:>`.

## Scenario 2 — A research link to an object resolves, no soft-miss (FR-003, SC-002)

The object's slug enters `result.entity_index`; a `map_research` pass whose
`bears_on:` names the object records **zero** soft-misses for that target.

```bash
uv run pytest tests/io/test_bible.py -k "entity_index or research" -q
```

Expect: the object is in `entity_index`; the research resolution test reports no
soft-miss for the object target.

## Scenario 3 — Skip / absent / collision are graceful (FR-004/005/006, SC-004)

```bash
uv run pytest tests/io/test_bible.py -k "object and (skip or absent or collision)" -q
```

Expect: a front-matter-less object file → recorded under `skipped`, no crash;
no `bible/objects/` directory → identical to today; two same-slug objects →
`SlugCollisionError`.

## Scenario 4 — The scaffold ships `bible/objects/` (FR-007, SC-005)

```bash
uv run pytest tests/commands/test_init_default.py -q
```

Expect: a freshly scaffolded project contains `bible/objects/.gitkeep`, mirroring
`bible/settings/` and `bible/locations/`.

## Scenario 5 — The bible skill teaches object front-matter for both integrations (FR-008/009, SC-005)

```bash
uv run pytest tests/integrations/ -q
uv run pytest tests/resources/test_command_frontmatter.py tests/resources/test_command_activation.py -q
```

Expect: the `bookwright-bible` `SKILL.md` regenerates and lints for `claude` and
`generic`; the command lists `bible/objects/` among the entity directories and
prescribes object sheets; bilingual (ES/EN) triggers preserved.

## Scenario 6 — Ingestion parity green with G16 reachable (FR-010, SC-003)

```bash
uv run pytest tests/golem/test_ingestion_parity.py -q
```

Expect: `Object` is reachable (registry now 5 entries), the parity guard is green,
and `test_drift_undeclared_orphan` (now keyed on `PsychologicalState`) still
passes.

## Final gate — all four CI gates (SC-005)

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest
```

Expect: all green, coverage ≥ 80 %, every pre-existing bible test unchanged.
