# Contract — the E2E workflow test (`tests/e2e/test_narrative_workflow.py`)

Walks the authored path **ingest → `graph build` → `validate`** against `tiny-quest`
on a `tmp_path` copy, in-process via `typer.testing.CliRunner`, every `--json` document
parsed off stdout (Principle IX). Harness idioms reused verbatim from
`test_orchestration_workflow.py` (023): `copy_fixture`, `monkeypatch.chdir`,
`_payload`, `_build`, the oracle loader, the Group-D source-only checks.

Four groups, mapped 1:1 to the user stories and FRs.

## Group A — build produces the oracle's graph facts (US1/US2, FR-008)

Given the `tiny-quest` copy, when `graph build --json` runs, the build succeeds
(exit 0) and the **derived graph** carries exactly the oracle's facts:

- **A1 — G9 units**: the count and slug set of `NarrativeUnit` entities equal
  `oracle.units.count` / `oracle.units.slugs`.
- **A2 — G10 functions**: the count of distinct `NarrativeFunction` entities equals
  `oracle.functions.count`.
- **A3 — Propp typings**: each `oracle.functions.typed[slug]` is present as a
  `crm:P2_has_type` edge from that function to the named `crm:E55_Type` Propp term;
  untyped functions carry no such edge.
- **A4 — G7 sequence + ordered members**: exactly one `NarrativeSequence` named
  `oracle.sequence.name`, whose `dlp:proper-part` members, **in order**, equal
  `oracle.sequence.members`.
- **A5 — role cross-refs**: each `oracle.roles_resolved[unit] = [roles…]` appears as
  unit→character-role edges; the orphan card's unresolved slug yields **no** edge.

Assertion surface: query the loaded engine directly (the
`test_ingestion_parity::_observed_types` pattern — `outcome.engine.query(...)` /
`build_project_graph`) for the triple-level facts that `graph build --json` does not
surface; use the `--json` envelope for entity/triple headline counts where it does.

## Group B — validate reports the exact findings (US1/US2, FR-009)

Given the built copy, when `validate --json` runs, it succeeds (exit 0 — the validator
is `warning`-only, so the error gate does not fire) and `violations[]` filtered to
`validator == "narrative_structure"` equals the oracle's enumerated set:

- **B1 — orphan beat(s)**: one violation per `oracle.narrative_structure.orphan_beats`,
  each `severity == "warning"`, `message` naming the unit slug + `orphan beat`,
  `source` == the oracle `source`.
- **B2 — unresolved role(s)**: one violation per
  `oracle.narrative_structure.unresolved_roles`, each `severity == "warning"`,
  `message` naming the unit + role + `resolves to no character role`, `source` == the
  oracle `source`.
- **B3 — exact count**: the `narrative_structure`-scoped warning/error counts equal
  `oracle.narrative_structure.counts` (no extra findings — exactness, FR-005).
- **B4 — no other validator regresses**: the rest of `violations[]` is whatever the
  other built-ins legitimately report on this clean fixture (assert no `error`-severity
  finding overall, i.e. `failed == false`).

## Group C — non-regression when no vocabulary is active (US2, FR-010, edge case)

Given the same copy with `[vocabularies] active` **emptied at runtime** (rewrite the
copy's `manifest.toml`, not a second committed fixture):

- **C1**: rebuild; **no** `crm:P2_has_type` edge and **no** vocabulary `crm:E55_Type`
  typing triple appear (`oracle.functions.typed` entirely absent).
- **C2**: every other graph fact (Group A1/A2/A4/A5 — units, function count, sequence +
  members, role cross-refs) is **byte-for-byte identical** to the Propp-active build.
- **C3**: `validate --json` still reports the same `narrative_structure` findings
  (the validator does not depend on vocabulary activation) — Group B unchanged.

This proves vocabulary activation is the **only** thing that adds the typings
(iteration-030 guarantee), with a single committed fixture.

## Group D — determinism + committed fixture is source-only (US2, FR-011; extends 023 D)

- **D1 — determinism**: repeating `graph build` then `validate --json` on an unchanged
  copy yields byte-identical asserted JSON / graph facts (no timestamp, minted-URI, or
  ordering nondeterminism in the asserted fields).
- **D2 — source-only committed tree**: the committed `tests/fixtures/tiny-quest/` ships
  **no** `bible/graph.ttl`, **no** `.claude/` or `.agents/`, **no** `SKILL.md`; the
  oracle `expected-narrative.md` is present-but-inert (read by the test, never by a
  build). Mirrors `test_orchestration_workflow.py::test_committed_fixture_is_source_only`.

## Non-goals (asserted nowhere)

- No LLM / judgment step is invoked (FR-011) — all assertions are on the deterministic
  graph triples and validator JSON.
- No new CLI verb, manifest field, validator, or skill is exercised — the test uses
  only the existing `graph build` / `validate` surface (FR-021).
