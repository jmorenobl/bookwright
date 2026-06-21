# Quickstart — validate the v0.4 close (032)

Runnable checks that prove each deliverable. Run from the repo root on the
`032-v04-close` branch. (References: [data-model.md](./data-model.md),
[contracts/fixture-oracle.md](./contracts/fixture-oracle.md),
[contracts/e2e-narrative-workflow.md](./contracts/e2e-narrative-workflow.md).)

## 1. The fixture works end to end (US1, SC-001)

```bash
# Copy the source-only fixture somewhere writable (the build mutates bible/graph.ttl):
cp -r tests/fixtures/tiny-quest /tmp/tiny-quest && cd /tmp/tiny-quest

uv run --project /Users/jorge/Projects/bookwright bookwright graph build --json   # exit 0
uv run --project /Users/jorge/Projects/bookwright bookwright validate --json | python -m json.tool
#   → status "violations", failed false; violations[] includes the two
#     narrative_structure warnings (orphan beat + unresolved role) with file:line sources
cd - && rm -rf /tmp/tiny-quest
```

Expected: a successful build whose graph carries the G9/G10/G7 entities + Propp
`E55_Type` typings, and a validate run reporting exactly the oracle's
`narrative_structure` warnings.

## 2. The workflow test passes (US2, SC-002)

```bash
uv run pytest tests/e2e/test_narrative_workflow.py -q
```

Expected: green. Groups A (build graph facts), B (exact validator findings), C
(no-vocabulary-active non-regression), D (determinism + source-only) all pass, every
count/identifier sourced from `tiny-quest/expected-narrative.md`.

## 3. The deferral registry is honest and parity stays green (US4, SC-003)

```bash
uv run pytest tests/golem/test_ingestion_parity.py -q
# And prove no stale target string survives anywhere:
rg -n '"v0\.4"' src/bookwright/golem/deferrals.py tests/golem/test_ingestion_parity.py && echo "STALE!" || echo "clean"
rg -n 'Target: v0\.4' DEBT.md && echo "STALE DEBT!" || echo "DEBT clean"
```

Expected: `test_ingestion_parity.py` green (`EXPECTED_VERSIONS` ==
`{"RelationshipRole": "demand-pulled", "PsychologicalState": "demand-pulled"}`, the
no-`"undecided"` assertion still holds); no `"v0.4"` deferral-target string remains in
`deferrals.py`/the parity test; DEBT-001/DEBT-002 carry no stale `Target: v0.4`.

## 4. The docs cover the layer and build clean (US3, SC-004)

```bash
uv run mkdocs build --strict        # zero warnings (FR-024)
rg -n "narrative-structure.md" mkdocs.yml        # nav entry present
```

Expected: `docs/narrative-structure.md` exists, is reachable from nav, and covers (in
Spanish) `outline/units/` ingestion, unit frontmatter (`functions`/`roles`/`sequence`/
`order`), Propp/Greimas activation via `[vocabularies] active`, and the
`narrative_structure` validator's two rules; README reflects v0.4; the site builds
with no warnings.

## 5. The roadmap reflects v0.4 delivered (user request)

```bash
rg -n "v0.4 entregada|← AQUÍ" bookwright-roadmap.md
```

Expected: § 1 states v0.4 is delivered; the § 2 `← AQUÍ` marker has advanced past the
`v0.4` line (to the demand-pulled horizon).

## 6. Full gates (SC-006)

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest                       # full suite, coverage ≥ 80 % (single enforced gate)
```

## 7. Release handoff — the `bookwright-release` skill (US5, SC-005)

The version bump, CHANGELOG, `CLAUDE.md`/design status, release commit, and the
annotated tag are **not** committed on this branch (CLAUDE.md: the iteration branch
does not bump the version, merge, or tag). After the branch is green and merged to
`main`, run the release skill:

> *"Haz la release de la iteración 032 — corta `v0.4.0`."*

It verifies the four gates → merges to `main` → bumps `__version__` to `0.4.0` →
writes the `v0.4.0` CHANGELOG section (consolidating 028–032) → flips the `CLAUDE.md`
status table + milestone prose → updates `bookwright-design.md` where shipped code
diverged → release commit → annotated `v0.4.0` tag. After it runs:

```bash
uv run bookwright version           # → 0.4.0
git describe --tags                 # → v0.4.0
```
