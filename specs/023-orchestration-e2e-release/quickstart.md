# Quickstart: validate the orchestration loop, docs, and v0.3.0 release

Runnable validation for iteration 023. Assumes `uv sync` has been run and you are
at the repo root. Details live in [data-model.md](./data-model.md) and
[contracts/e2e-orchestration-contract.md](./contracts/e2e-orchestration-contract.md).

## Prerequisites

- iterations 019–022 merged on `main` (focus, `status` engine, status-consuming skills)
- `uv sync` (installs deps + dev group)

## 1. The fixture is a working orchestration example (SC-001)

Manually drive the loop over a throwaway copy to see `status` recommend work:

```bash
# work on a copy so the committed fixture stays pristine
cp -r tests/fixtures/tiny-historical /tmp/orch && cd /tmp/orch
uv run --project "$OLDPWD" bookwright focus set \
  --target "Cerrar la investigación del libro de jornales" --json
uv run --project "$OLDPWD" bookwright graph build --json
uv run --project "$OLDPWD" bookwright status --json | python -m json.tool
```

**Expected:** exit 0; a defined `focus`; `state.graph.available == true`;
`state.open_questions.count == 2`; a non-empty `next_actions` whose first entry is
`bookwright-research` and whose prompt names `q-libro-de-jornales` and
`q-origen-telares`. (`cd -` to return.)

## 2. Apply the pre-baked resolution and see convergence (SC-002)

```bash
cp _resolution/q-libro-de-jornales.md bible/research/   # add the answering Finding
# drop `- id: q-libro-de-jornales` from bible/research/_index.md open_questions
uv run --project "$OLDPWD" bookwright graph build --json
uv run --project "$OLDPWD" bookwright status --json | python -m json.tool
```

**Expected:** `state.open_questions.count == 1` (only `q-origen-telares`); the
`bookwright-research` prompt no longer names `q-libro-de-jornales`;
`len(next_actions)` is still **3** (the research workstream keeps firing for the
remaining question + the permanent `el-almacen-viejo` anchor gap); `verify_findings`,
`review_continuity`, `state.validation`, `state.unresolved_anchors`,
`state.low_reliability_findings`, and `focus` are unchanged.

## 3. The automated regression (SC-002, SC-003)

```bash
uv run pytest tests/e2e/test_orchestration_workflow.py -v
```

**Expected:** all groups green — the loop convergence (Group A), inertness over
`tiny-novel` (Group B), the degraded `graph unavailable` path (Group C), and the
committed-tree invariants (Group D).

## 4. The M4 research test is unaffected (FR-006)

```bash
uv run pytest tests/e2e/test_research_workflow.py -v
```

**Expected:** still green; `factual_anchor` still reports `{error:1, warning:1}`;
`expected-findings.md` is byte-unchanged.

## 5. Docs build clean and cover orchestration (SC-004, SC-006)

```bash
uv run --group docs mkdocs build --strict
```

**Expected:** zero warnings; `docs/orchestration.md` reachable from the nav
(`Orquestación`); `status`/`focus` command pages accurate; `docs/changelog.md`
and root `CHANGELOG.md` each carry a v0.3.0 entry.

## 6. Version bumped to 0.3.0 (SC-004)

```bash
uv run bookwright version --json | python -m json.tool   # package_version == "0.3.0"
uv run pytest tests/test_smoke_import.py tests/test_cli_version.py -q
```

**Expected:** `0.3.0`; smoke/version tests green (they read `__version__`).

## 7. Full gate (SC-005, SC-006)

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest          # ≥ 80 % coverage enforced (single source)
```

**Expected:** all four gates green; overall coverage ≥ 80 %.
