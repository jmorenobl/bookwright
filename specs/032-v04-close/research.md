# Phase 0 — Research & Decisions: v0.4 close (032)

All NEEDS CLARIFICATION are resolved. No new technology is introduced; the
"research" here is **reconciling this iteration's shape with the merged 028–031
mechanism and the M4/M5 closing precedents**, so each decision cites the existing
code it mirrors.

## D1 — A new dedicated fixture, not an extension of an existing one

- **Decision**: ship a **new** `tests/fixtures/tiny-quest/`, source-only, with its own
  co-located oracle, rather than extend `parity-exercise` or `tiny-historical`.
- **Rationale**: `parity-exercise` is single-purpose and pinned byte-for-byte by
  `test_ingestion_parity.py` (its `EXPECTED_REACHABLE` set + the orphan/version
  pins); adding a deliberate orphan beat or an unresolved role there would change the
  reachable/observed sets and break that guard (FR-006). `tiny-historical` carries the
  M4/M5 oracles (`expected-findings.md`, `expected-status.md`) and has **no**
  `[vocabularies]` block by design (its manifest comment says so) — activating Propp
  there would perturb the research/orchestration oracles. A fresh fixture isolates the
  v0.4 demonstration. This matches how M4 added `tiny-historical` and M5 extended it
  rather than overloading `tiny-novel`.
- **Alternatives rejected**: (a) extend `parity-exercise` — breaks the parity guard;
  (b) extend `tiny-historical` — pollutes the M4/M5 oracles and forces a
  `[vocabularies]` block onto a fixture deliberately without one.
- **Name**: `tiny-quest` — Propp's morphology is the grammar of the folktale/quest, so
  a quest narrative makes the function names (`interdiction`, `departure`, `villainy`,
  `victory`, `return`) read naturally and the oracle self-documenting.

## D2 — The fixture's exact, unambiguous outcome (the oracle)

- **Decision**: a co-located `expected-narrative.md` whose **YAML front-matter is the
  single source of truth** for every asserted fact — loaded once via
  `bookwright.io.frontmatter.parse_frontmatter(...).metadata`, never hard-coded in the
  test. Mirrors `tiny-historical/expected-status.md` (loaded by
  `test_orchestration_workflow.py::_load_oracle`).
- **Contents** (schema fixed in `contracts/fixture-oracle.md`): the G9 unit count, the
  G10 function count, the G7 sequence name(s) + their ordered member unit slugs, the
  resolved role cross-refs (unit → character-role), the Propp `P2_has_type` typings
  (function slug → matched Propp term), and the **exact** `narrative_structure`
  findings (the orphan beat unit slug(s) and the unresolved role(s), each with
  validator name, `warning` severity, and an oracle `source` file or `file:line`).
- **Why front-matter, not prose**: the test asserts machine facts; the Markdown body
  explains the planted structure to a human reader (the `tiny-historical` precedent
  keeps the body as Spanish narrative explanation).

## D3 — Producing the two validator findings deliberately

The `narrative_structure` validator (031) has exactly two rules; the fixture must
trip each exactly the planned number of times (FR-004, FR-005):

- **Rule a — orphan beat** (`_orphan_beats` → `queries.load_orphan_units`, SPARQL
  `NOT EXISTS` over `dlp:proper-part`): include **one** unit card that carries
  `functions`/`roles` but **no** `sequence` key. With no `sequence` it contributes no
  `_SeqMember`, so `_assemble_sequences` never makes it a `dlp:proper-part` of any G7
  → it is an orphan beat. Every other unit *does* carry `sequence`, so the orphan set
  is exactly that one card (asserted exact, not a lower bound).
- **Rule c — unresolved role** (`_unresolved_roles` → re-surfaced
  `UnresolvedReference` records filtered to `outline/units/`): include **one**
  `roles:` slug on a unit that **no** character's `narrative_roles` declares (e.g.
  `roles: [dragon]` while characters declare only `protagonist`/`villain`/`helper`).
  `_resolve_roles` finds no match in `roles_index` and appends one
  `UnresolvedReference(path=<unit card>, entity=<unit name>, name="dragon")`; the
  validator filters by the `outline/units/` path prefix and emits one warning.
- **Determinism of the source locator**: the validator resolves each finding's
  `source` through the existing `E13` provenance path
  (`queries.resolve_source(indexer, unit_uri)`), falling back to the card relpath.
  Because the fixture is rebuilt fresh in `tmp_path`, the provenance is present, so the
  `source` is a stable `outline/units/<card>.md:<line>` — pinned in the oracle.
- **No false positives elsewhere**: every other unit is sequenced and every other
  `roles:` slug resolves, so the *only* findings are the planted ones. The oracle
  asserts the **exact set** (FR-005, edge case "exact, unambiguous set").

## D4 — Propp activation and the `P2_has_type` typings

- **Decision**: the manifest declares `[vocabularies] active = ["propp"]`. The
  `_graph` pipeline calls `load_active_vocabularies(["propp"])`, passing the resulting
  `VocabularyIndex` to `map_outline(..., propp=index)`; `_mint_functions` then sets each
  function's `type_uri` to `propp.resolve(name)` (the matched `crm:E55_Type` term, or
  `None`). So function cards whose names are canonical Propp terms gain a
  `crm:P2_has_type` → `crm:E55_Type` edge (031/030 mechanism, verbatim).
- **Function names must be canonical Propp labels** so they resolve (the loader indexes
  `make_slug(label)` over `propp.ttl`'s ES+EN labels). The oracle records, per
  function, whether it is typed (matched) — the test asserts those typings appear.
- **Greimas (role typing) is documented but the fixture leads with Propp**: Greimas
  types `narrative_roles` via `map_bible(..., greimas=index)` (the
  `_bible_builders.py` path). The fixture activates **Propp only** (the functions
  vocabulary, FR-003); the docs page still explains Greimas/actant activation (edge
  case "Greimas as well as Propp"). Optionally the oracle may also assert role typings
  if the fixture additionally activates Greimas — but the spec's worked example is
  Propp-led, so the default is Propp-only and the non-regression test (D5) toggles
  exactly that one vocabulary off.

## D5 — The non-regression assertion (toggle vocab off at runtime)

- **Decision**: assert the iteration-030 guarantee by **emptying `[vocabularies]
  active` on the `tmp_path` copy at runtime** (rewrite the manifest in the copy, not a
  second committed fixture, FR-010). Rebuild; assert **no** `crm:P2_has_type` edge and
  **no** vocabulary `crm:E55_Type` typing triple appear, and **every other graph fact**
  (G9/G10/G7 entities, members, role cross-refs) is byte-for-byte identical to the
  Propp-active build.
- **Rationale**: `load_active_vocabularies([])` returns an all-`None` record, so
  `map_outline(propp=None)` types nothing — the byte-for-byte pre-feature output
  (FR-008/SC-003 of iteration 030). Toggling at runtime proves activation is the *only*
  thing adding the typings, with one fixture (avoids a near-duplicate committed tree).
- **Mechanic**: load the copy's `manifest.toml` via `tomlkit`, set
  `vocabularies.active = []`, write it back, rebuild — or, simpler and equally valid,
  use `Manifest.load` + the same `build_project_graph` entry the parity test uses, with
  the active list cleared. The test will pick whichever keeps the assertion on the
  derived graph triples (the deterministic surface).

## D6 — The workflow test harness (mirror 023, not 016)

- **Decision**: model `tests/e2e/test_narrative_workflow.py` on
  `test_orchestration_workflow.py` (023): in-process `CliRunner`, a `tmp_path` copy via
  `tests.conftest.copy_fixture`, `monkeypatch.chdir`, every `--json` document parsed off
  stdout with a `_payload` helper, the oracle loaded once. Reuse the 023 idioms
  (`_build`, `_payload`, Group D source-only assertions).
- **Groups** (1:1 with `contracts/e2e-narrative-workflow.md`):
  - **A** — build produces the oracle's G9/G10/G7 entities, ordered members, role
    cross-refs, and Propp typings (assert against the derived graph via the engine's
    SPARQL, like `test_ingestion_parity::_observed_types`, or by re-reading
    `graph build --json` counts where the envelope exposes them).
  - **B** — `validate --json` reports the exact `narrative_structure` findings
    (orphan beat + unresolved role), each `warning`, with validator name and a
    `file:line` source, oracle-sourced.
  - **C** — non-regression: empty `[vocabularies] active` on the copy → no typings, all
    else unchanged (D5).
  - **D** — determinism + committed fixture is source-only (no `graph.ttl`, no
    `.claude/`, no `SKILL.md`; the oracle file is present-but-inert), extending the
    023 Group D invariants.
- **Assertion surface**: the **derived graph triples** and the **validator JSON** only
  — both deterministic; no LLM/judgment step (FR-011). Where the `graph build --json`
  envelope does not expose a needed fact (e.g. per-typing edges), the test queries the
  loaded engine directly, exactly as `test_ingestion_parity.py` does (`_observed_types`
  via `outcome.engine.query`).

## D7 — The honest deferral re-target (`"v0.4"` → `"demand-pulled"`)

- **Decision** (resolved in Clarifications 2026-06-21): re-point G6/G3
  `target_version` to the first-class sentinel **`"demand-pulled"`**, swept across
  **every** holder of the string:
  1. `deferrals.py` — both `DEFERRED_CONCEPTS` entries (`RelationshipRole`,
     `PsychologicalState`).
  2. `deferrals.py` — the `DeferralNote` docstring, which today says *"always a
     concrete version label such as `"v0.4"`"*. Extend it to admit `"demand-pulled"`
     as a documented first-class state ("a concrete version label **or** the
     `"demand-pulled"` sentinel — a disciplined 'no version until an activation
     trigger' state mirroring roadmap § 4; never the banned `"undecided"`
     placeholder").
  3. `test_ingestion_parity.py` — `EXPECTED_VERSIONS` from
     `{"RelationshipRole": "v0.4", "PsychologicalState": "v0.4"}` to
     `{"RelationshipRole": "demand-pulled", "PsychologicalState": "demand-pulled"}`.
- **Why the sentinel and not a fabricated version**: the roadmap genuinely assigns
  G6/G3 **no** version (iteration 027 left them "diferidos a posterior"; § 4's
  demand-pulled horizon assigns a version only at activation). Inventing `"v0.5"`/`"v1.0"`
  would fabricate a commitment the owner never made (zero-debt doctrine §3 — eliminate
  the cause, don't fake a target). `"demand-pulled"` is the truthful, disciplined
  state. It is **not** `"undecided"`: the parity test's existing
  `note.target_version != "undecided"` assertion still holds.
- **Why the set of orphans does not change**: G7/G9/G10 left the orphan set when
  028–029 wired them, so the live orphan set stays exactly `{RelationshipRole,
  PsychologicalState}` and the orphan-set assertion is unaffected. Only the *version
  map* assertion would go red without the `EXPECTED_VERSIONS` sweep — hence FR-019.
- **No new placeholder semantics**: `"demand-pulled"` is a literal string value, not a
  new `DeferralNote` field or enum; the registry stays "pure data" (no import churn).

## D8 — The `DEBT.md` stale-target sweep (FR-019b)

- **Decision**: the same honesty sweep extends to the two open `DEBT.md` entries that
  carry `Target: v0.4` while **not** being resolved in v0.4:
  - **DEBT-001** (`NarrativeRole` dead concept) → re-point its target to a **concrete
    later structural iteration** (e.g. "una iteración estructural posterior, sin
    versión asignada — horizonte demand-pulled"), since deciding to remove/wire the
    top-level G11 concept is a separate structural debt class, forbidden here by
    FR-021/Out of Scope.
  - **DEBT-002** (constitution Scope & Release Discipline drift) → re-point its target
    to the **manual `v0.4.0` release/amendment step** that owns it (the MINOR
    constitution amendment rides the release, per CLAUDE.md, not this branch).
- **Both entries otherwise stay deferred** (Out of Scope) — only the stale `Target:`
  string is corrected, so the ledger never claims a shipped version as a future target.

## D9 — Division of labour: branch work vs. the `bookwright-release` step

- **Decision**: the **branch** (`/speckit-implement`) ships the fixture+oracle, the
  test, the docs page + nav + README, the deferral re-target, the DEBT corrections, and
  the roadmap §1/§2 edits. The **release metadata** — `__version__ = "0.4.0"`, the
  `v0.4.0` CHANGELOG section, the `CLAUDE.md` status-table flip + milestone prose, the
  `bookwright-design.md` status edits, the release commit, and the annotated `v0.4.0`
  tag — is executed by the **`bookwright-release` skill** at the closing manual step.
- **Rationale**: CLAUDE.md is explicit that the iteration branch "does **not** push,
  merge, bump the version, or tag — merging to `main` stays a separate, manual step,"
  and the plan hint assigns the version/CHANGELOG/CLAUDE.md/design/tag chain to
  `bookwright-release`. Bumping `__version__` inside the branch and again in the release
  step would double-handle and risk drift. Keeping the version single-sourced *and* the
  bump in one place (the release skill) honours FR-020's "no second version string may
  drift" most cleanly.
- **Consequence for tasks**: the `/speckit-tasks` output marks FR-015/016/020 tasks as
  **[release-skill]** — verified at the release step, not committed on the branch.
  `quickstart.md` documents the handoff so the maintainer runs `bookwright-release`
  after the branch is green and merged.

## D10 — Quality gates unchanged

Coverage ≥ 80 % stays the single enforced gate (`fail_under` in
`[tool.coverage.report]`; no `--cov-fail-under` is added anywhere). The new E2E test
*raises* covered lines (it exercises the build + validate paths over a Propp-active
project, a path no current fixture covers). `ruff check`, `ruff format --check`,
`mypy --strict`, pre-commit, and the strict `mkdocs build` all must pass (FR-024).
