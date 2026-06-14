# Implementation Plan: JSON success-envelope cleanup + G6/G3 deferral decision

**Branch**: `027-envelope-cleanup-g6-g3` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/027-envelope-cleanup-g6-g3/spec.md`

## Summary

The closing iteration of the v0.3.x hardening track ties off three loose ends, all
**decided in the spec** — `/speckit-plan` only routes the wiring:

1. **Success-envelope single-sourcing (US1, P1).** Route the hand-built
   `{"status": "ok", …}` literals in `commands/focus/{show,set_,clear}.py` and
   `commands/graph/query.py` through the shared `ok_payload(**fields)` +
   `emit_json` helper (exactly as `status` already does, iteration 020), producing
   **byte-identical** stdout. `check.py` keeps its `{"ok": <bool>, "checks": […]}`
   envelope as-is (no top-level `status` key — wrapping it in `ok_payload()` would
   change bytes); `graph build` already serializes through `BuildReport.to_json()`
   — confirm, do not rewrite. A regression test pins the current stdout bytes of
   `check` / `focus` show·set·clear / `graph query` / `graph build` and asserts
   identity.

2. **G6/G3 deferral decision (US2, P1).** Edit `golem/deferrals.py`: change the
   `RelationshipRole` (G6) and `PsychologicalState` (G3) entries from
   `target_version="undecided"` to `"v0.4"` with reason "requires a typed
   roles/states model with attributes and an authoring surface". **Neither is
   wired** — both stay observed as orphans. Update `EXPECTED_VERSIONS` in
   `tests/golem/test_ingestion_parity.py` (the orphan/reachable sets do **not**
   change — only the version mapping). Eliminate the `"undecided"` literal from the
   registry contract (the `DeferralNote` docstring) and assert no entry may carry
   it.

3. **Unresolved-reference rename (US3, P2).** Rename `UnresolvedParticipant` →
   `UnresolvedReference` in `io/report.py` (fields `{path, entity, name}` intact,
   docstring generalized to any unresolved reference: `participants:` or
   `setting:`). Rename the `--json` key `unresolved_participants` →
   `unresolved_references` in `graph build`, preserving its **position** in the
   envelope; the stderr summary becomes "N unresolved reference(s)". A new golden
   baseline replaces the old **only** for that one key; every other byte stays
   identical. Update `docs/commands/graph-build.md`. Final grep: zero
   `UnresolvedParticipant` / `unresolved_participants` in `src/` or `docs/`.

The whole iteration is additive-to-neutral: no new ontology class/property
(Principle X), no new runtime dependency, no command added or removed. The only
deliberately changed observable byte is the single renamed `graph build` key.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `typer`, `rich`, `rdflib`, `pydantic` v2, `tomlkit`
(all already present; nothing added)

**Storage**: plain text — TOML manifest, Turtle graph cache (`bible/graph.ttl`);
no change to storage in this iteration

**Testing**: `pytest` (+ `pytest-cov`), ≥ 80 % line coverage gate, `mypy --strict`,
`ruff check` / `ruff format --check`

**Target Platform**: CLI (cross-platform); local author workstation

**Project Type**: single project — CLI toolkit (`src/bookwright/`, `tests/` at root)

**Performance Goals**: N/A — no hot path touched; the regression test reuses the
existing in-process CLI-invocation pattern

**Constraints**:
- **Byte-identical stdout** for every migrated success document except the single
  `graph build` key renamed by FR-016 (US1 hard guarantee, machine-checked).
- **No new ontology class/property** (Principle X / Constitution X): G6/G3 already
  exist in `CLASS_IRI` + `CONCEPTS` and are *not* wired.
- **Single JSON document on stdout, prose to stderr** (Principle IX) — preserved.
- Every source file ≤ 500 lines (Principle IV) — all touched files stay well under.

**Scale/Scope**: ~6 source files edited (4 focus/graph command modules confirmed
or migrated, `io/report.py`, `io/_bible_builders.py`, `io/bible.py`,
`commands/_graph.py`, `commands/graph/build.py`, `golem/deferrals.py`), 1 new
regression test module, edits to `tests/golem/test_ingestion_parity.py` and the
existing build/bible tests for the rename, 1 doc page, CHANGELOG entry at release.

## Constitution Check

*GATE: must pass before Phase 0 and re-checked after Phase 1.*

| Principle | Status | Notes |
|---|---|---|
| I — Plain text as source of truth | ✅ PASS | No binary store touched; graph cache stays a derived Turtle file. |
| II — Modern Python stack | ✅ PASS | No dependency added/removed. |
| III — src-layout | ✅ PASS | All prod edits under `src/bookwright/`; all tests under `tests/`. |
| IV — Modular command surface | ✅ PASS | One module per verb unchanged; every touched file stays ≤ 500 lines (`_bible_builders.py` largest, well under). |
| V — Plugin-based integrations | ✅ PASS | Integrations untouched. |
| VI — Agent Skills only | ✅ PASS | No skill/command-dir change. |
| VII — agentskills.io compliance | ✅ PASS | No SKILL.md emitted/changed. |
| VIII — Test discipline (≥ 80 %) | ✅ PASS | Adds a byte-pinning regression test and parity-mapping edits; coverage rises, not falls. |
| IX — JSON-over-stdout contract | ✅ PASS | The whole point: one JSON doc on stdout via the single `ok_payload`/`emit_json` source; prose stays on stderr. The one key rename is a documented `0.x` contract change (CHANGELOG). |
| X — Design-document axioms / frozen ontology | ✅ PASS | No GOLEM class/property added; G6/G3 reused identity-only-capable but **not** wired. The 17-class closure and `golem.ttl` are untouched. |
| Scope & Release Discipline | ✅ PASS | This is the planned closing patch of the v0.3.x track; no v0.4 work (narrative-structure layer, `outline/`) is pulled in — it is only *confirmed* deferred. No speculative plumbing. |

**Result**: PASS, no violations — Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/027-envelope-cleanup-g6-g3/
├── spec.md              # /speckit-specify (done)
├── plan.md              # This file (/speckit-plan)
├── research.md          # Phase 0 output (/speckit-plan)
├── data-model.md        # Phase 1 output (/speckit-plan)
├── quickstart.md        # Phase 1 output (/speckit-plan)
├── contracts/           # Phase 1 output (/speckit-plan)
│   ├── success-envelope.md     # US1 byte-identity contract
│   └── graph-build-json.md      # US3 renamed-key envelope contract
└── tasks.md             # /speckit-tasks (NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── commands/
│   ├── _envelope.py            # ok_payload / emit_json — the single source (unchanged API)
│   ├── check.py                # US1: confirm {"ok","checks"} envelope unchanged (no status key)
│   ├── focus/
│   │   ├── show.py             # US1: {"status":"ok",…} → ok_payload(**fields) + emit_json
│   │   ├── set_.py             # US1: same migration
│   │   └── clear.py            # US1: same migration
│   ├── graph/
│   │   ├── query.py            # US1: same migration
│   │   └── build.py            # US3: report field access + stderr "unresolved reference(s)"
│   └── _graph.py               # US3: BuildResult→BuildReport field name
├── io/
│   ├── report.py               # US3: UnresolvedParticipant → UnresolvedReference (+ key, docstring)
│   ├── _bible_builders.py      # US3: import, BuildResult field, append sites, docstrings
│   └── bible.py                # US3: docstring mention
└── golem/
    └── deferrals.py            # US2: G6/G3 → v0.4 + reason; remove "undecided" from contract docstring

tests/
├── commands/
│   └── test_success_envelopes.py   # NEW (US1, FR-005): byte-pin check/focus/graph query·build
├── golem/
│   └── test_ingestion_parity.py    # US2: EXPECTED_VERSIONS edit + "no undecided" assertion
├── commands/graph/test_build.py    # US3: assert unresolved_references key + new golden
├── io/test_bible.py                # US3: rename references
├── fixtures/test_fixtures.py       # US3: rename references (if any assert the key/type)
└── resources/{conftest.py,test_frontmatter_contract.py}  # US3: rename references

docs/commands/graph-build.md         # US3: document unresolved_references key
```

**Structure Decision**: Single-project CLI layout (the only option the
constitution permits). No new package or module *directory* is created — the
single new file is one regression-test module under the existing
`tests/commands/`. Everything else is in-place edits to files that already exist.

## Complexity Tracking

> No constitutional violations — section intentionally empty.
