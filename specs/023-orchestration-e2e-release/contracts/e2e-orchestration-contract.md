# Contract: `test_orchestration_workflow.py` ↔ requirements

The CLI surface this iteration exercises is **already shipped and contract-frozen**
(iterations 019–020): `bookwright focus set/show/clear`, `bookwright graph build`,
`bookwright status`, `bookwright validate` — each `--json`, single JSON document on
stdout (Principle IX). This iteration adds **no new CLI contract**; it adds a test
that binds the orchestration loop's behavior to the requirements below, plus the
fixture/docs/release artifacts. This file maps each test obligation to its FR and
its assertion, the way `specs/016-research-e2e-docs/contracts/` did.

## Test groups

### Group A — the loop proven end to end over the extended `tiny-historical`

| ID | Obligation | FR | Assertion |
|---|---|---|---|
| A1 | Fixture loads & focus records | FR-002, US2-1 | `focus set --target <oracle.target>` exit 0; subsequent `status` → `focus` non-null, `focus.target == oracle.target` |
| A2 | Build materializes research + narrative | FR-003, US1-2 | `graph build --json` exit 0; `status.state.graph.available == true`, `entities`/`triples` present |
| A3 | First `status` deterministic facts | FR-008 | every row of data-model § 2.1 holds, identifiers/counts read from the oracle (never hard-coded) |
| A4 | First `status` enumerated actions | FR-008 | `next_actions` == 3 entries; skills/order == oracle `next_actions.skills`; each has `skill`+`reason`+`prompt`; `research_queue.prompt` contains both open ids |
| A5 | Resolution closes exactly one question | FR-005 | after `_apply_resolution` + rebuild: `status.state.open_questions.count == 1`, remaining id `q-origen-telares`, resolved id absent |
| A6 | Second `status` convergence | FR-009 | `research_queue.prompt` drops the resolved id; `reason` reflects new count; **invariant set (data-model § 4) byte-identical**; `len(next_actions) == 3` unchanged |
| A7 | `state.graph` carve-out | FR-008, FR-009 (D2) | `state.graph.available == true` and counts present in **both** runs; `state.graph` excluded from the byte-identity comparison |
| A8 | Determinism across repeats | FR-010, SC-002 | a repeated `status` (no corpus change) yields a byte-identical document; no asserted field carries a timestamp / minted URI |

### Group B — inertness when orchestration is unused (`tiny-novel`)

| ID | Obligation | FR | Assertion |
|---|---|---|---|
| B1 | Focus-free / research-free is inert | FR-011 | `status --json` on `tiny-novel` exit 0; `focus == null`; `next_actions == []`; no open questions / anchors / low-reliability findings |
| B2 | `build`/`validate` unchanged | FR-011, SC-003 | `graph build` and `validate` exit/behavior match pre-M5 (no orchestration output, no new required input) |

### Group C — the degraded path

| ID | Obligation | FR | Assertion |
|---|---|---|---|
| C1 | Unbuildable corpus degrades, not fails | FR-012, SC-003 | on a `tmp_path` copy with build prerequisites absent, `status --json` exit 0; `state.graph.available == false`; report present, not an error |

### Group D — committed-tree invariants (extends 016 Group D)

| ID | Obligation | FR | Assertion |
|---|---|---|---|
| D1 | Extended fixture stays source-only | FR-006 | committed `tiny-historical` ships no `graph.ttl`, no `.claude/`, no `SKILL.md`; `_resolution/` and `expected-status.md` present but inert |
| D2 | M4 research test still green | FR-006 | `tests/e2e/test_research_workflow.py` passes unchanged (`factual_anchor` still `{error:1, warning:1}`; `expected-findings.md` byte-stable) |
| D3 | Resolution file absent from corpus #1 | FR-005 | `_resolution/` is outside `bible/`/`manuscript/`/`outline/`; first `status` reports `open_questions.count == 2` (proves it was not read) |

## Documentation & release contract

| ID | Obligation | FR | Check |
|---|---|---|---|
| E1 | Orchestration page exists & reachable | FR-013, FR-014 | `docs/orchestration.md` covers the 3-layer model, `status`/`next_actions`, the loop, skill consumption; `mkdocs.yml` nav references it |
| E2 | Command reference current | FR-015 | `docs/commands/status.md`, `focus-set/show/clear.md` verified accurate vs. live CLI (verify-and-finalize, not duplicated) |
| E3 | Changelog v0.3.0 | FR-016 | `docs/changelog.md` **and** root `CHANGELOG.md` gain a v0.3.0 entry consolidating 019–023 |
| E4 | Version bumped | FR-022 | `bookwright.__version__ == "0.3.0"`; `version --json` reports it; smoke/version tests green |
| E5 | Docs build clean | FR-019, SC-006 | `mkdocs build` under `strict: true` → zero warnings |

## Quality gates (the release bar)

| ID | Obligation | FR |
|---|---|---|
| G1 | Coverage ≥ 80 % overall (single enforced gate) | FR-017 |
| G2 | new M5 code ≥ 85 % (report-only, verified at review) | FR-017, SC-005 |
| G3 | `ruff check`, `ruff format --check`, `mypy --strict`, pre-commit, CI green | FR-018, SC-006 |
| G4 | No new product mechanism / no post-v0.3 capability | FR-020, FR-021, SC-007 |

## Out of contract (explicitly NOT asserted)

- Any LLM/judgment output (the resolve step is pre-baked content; FR-010).
- A `next_actions` **length** drop on resolution (contradicts the engine's
  per-workstream aggregation — D2; FR-009 forbids requiring it).
- Exact `state.graph` entity/triple **values** across the two runs (D2 carve-out).
- Tagging/publishing the v0.3.0 release (Out of Scope — release readiness only).
