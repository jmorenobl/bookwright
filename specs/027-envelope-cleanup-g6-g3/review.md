# Quality Audit — 027-envelope-cleanup-g6-g3

**Scope:** 17 changed source/test/doc files vs `main` (31 total incl. spec artifacts)
**Commit range:** main..3d86ade
**Date:** 2026-06-15
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 2 |
| **Total** | 3 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; measured 97.17% full-suite). All four CI gates green: `ruff check`, `ruff format --check`, `mypy --strict` (250 files, no issues), `pytest` (1226 passed, 1 skipped).

This is a clean closing patch. The byte-identity guarantee (US1) is machine-checked, the rename (US3) is complete in `src/` and `docs/`, and the G6/G3 deferral (US2) is recorded with a concrete `v0.4` target and a non-empty reason. The three findings are all documentation/naming drift left *behind* the rename — no behavioral, security, or convention violation.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Plain Text as Source of Truth … Binary stores … forbidden as canonical storage" | `constitution.md:59` | layout | PASS | No binary store touched; `bible/graph.ttl` stays a derived Turtle cache |
| "Introducing an additional runtime dependency requires an amendment" | `constitution.md:78` | dependency | PASS | No dep added; diff touches no `pyproject.toml` runtime deps |
| "All production code MUST live under `src/bookwright/` … tests under `tests/`" | `constitution.md:86` | layout | PASS | All prod edits under `src/bookwright/`; all test edits under `tests/` |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:99` | module-size | PASS | Largest touched: `_bible_builders.py` 268, new test 166 — all well under |
| "Each CLI subcommand MUST live in its own module" | `constitution.md:97` | layout | PASS | No verb added/merged; one module per verb unchanged |
| "Bookwright MUST emit Agent Skills … nothing else" | `constitution.md:121` | directory-ban | N/A | No skill/command-dir writes in this diff |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification" | `constitution.md:133` | frontmatter-constraint | N/A | No `SKILL.md` emitted or changed |
| "v0 MUST hold a minimum of 80% line coverage" | `constitution.md:149` | coverage-threshold | PASS | Full-suite coverage 97.17% ≥ 80% |
| "any agent-consumed subcommand … emit a single JSON document on stdout and only that" | `constitution.md:169` / `CLAUDE.md` | io-contract | PASS | `focus`/`graph query` now route through `ok_payload`+`emit_json`; byte pins in `test_success_envelopes.py` confirm one compact doc + single `\n` |
| "Exit codes MUST be non-zero on error even when --json is set" | `constitution.md:176` | io-contract | PASS | Migrated commands' exit codes unchanged; `unresolved_references` stays a soft warning (exit unchanged) |
| "Section 16 axioms … MUST NOT be reopened … frozen 17-class closure" | `constitution.md:184` / `CLAUDE.md` | scope-ban | PASS | No GOLEM class/property added; G6/G3 reused from existing `CLASS_IRI`, **not** wired (`deferrals.py` keeps both as orphans) |
| "A PR that introduces a deferred-but-not-yet-due capability … MUST be rejected" | `constitution.md:235` | scope-ban | PASS | v0.4 narrative-structure layer only *confirmed* deferred (`EXPECTED_VERSIONS` all `v0.4`); no plumbing pulled forward |
| "no `--cov-fail-under` anywhere; one source" | `CLAUDE.md` | coverage-threshold | PASS | Threshold single-sourced in `[tool.coverage.report]`; not touched |
| Spec Kit workflow: specify→clarify→plan→tasks→analyze→implement | `CLAUDE.md` | workflow-step | PASS | All artifacts present: spec/plan/tasks/research/data-model + 3 contracts + checklist |
| Track integrity (governance dirs committed) | `CLAUDE.md` | track-integrity | PASS | `git status` clean; every `specs/027…` file in branch diff vs `main` |

No `FAIL` rows — Section 3 lists smell/hygiene findings only (Passes B/D), none tied to a binding MUST.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | MEDIUM | src/bookwright/commands/_envelope.py:44-47 | `ok_payload` docstring still says check/focus/graph "keep their hand-built dicts for now; migrating them is out of 020's scope" — stale after this iteration migrated them | Update the docstring to record the debt as closed (focus + graph query now route through `ok_payload`; `check` keeps its `status`-less envelope by design) |
| R2 | D | LOW | src/bookwright/io/_bible_builders.py:264 | Comment reads "stray unresolved-participant warning" — old warning name after the `UnresolvedReference` rename | Change "unresolved-participant" → "unresolved-reference" in the comment |
| R3 | D | LOW | tests/io/test_bible.py:88 | Test function `test_unresolved_participant_omits_edge_but_keeps_event` keeps old "participant" naming; US3 aimed for "zero naming debt" | Rename to `test_unresolved_reference_omits_edge_but_keeps_event` (the assertions inside were already migrated) |

## 4. Remediation Detail

### R1 — `ok_payload` docstring describes a debt this iteration closed

- **Where:** `src/bookwright/commands/_envelope.py:44-47`
- **Why it matters:** The spec's own framing (US1, SC-002) is that the "out of 020's scope" note is the debt iteration 027 *closes*. `_envelope.py` is not in this branch's diff, so the docstring still asserts `focus`/`graph` "keep their hand-built dicts for now" — directly contradicting `focus/{show,set_,clear}.py` and `graph/query.py`, which now call `ok_payload(**fields)`. A future reader (or agent) trusting this docstring would believe the migration is still pending. This is comment-as-deodorant: the prose now hides the real state rather than describing it.
- **Suggested change:** Replace the last sentence with something like: "The `focus` and `graph query` success documents route through this helper (iteration 027); `check` deliberately keeps its `{"ok","checks"}` envelope with no top-level `status` key, and `graph build` serializes through `BuildReport.to_json()`." No behavior change — docstring only, so it carries no acceptance criterion and is safe to fold into this branch before release.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| (full suite) | 97.17% | 80% | PASS |
| src/bookwright/io/report.py | 100% | 80% | PASS |
| src/bookwright/golem/deferrals.py | 100% | 80% | PASS |
| src/bookwright/commands/focus/* | 100% | 80% | PASS |
| src/bookwright/commands/graph/{build,query}.py | ≥95% | 80% | PASS |
| tests/commands/test_success_envelopes.py (new) | exercised | — | 59 targeted tests pass |

No changed module dropped below threshold.

## 6. Inability-to-verify notes

- **CHANGELOG entry for the FR-016 key rename (pending at release, not a defect).** FR-016 requires the `unresolved_participants` → `unresolved_references` public-key rename be "recorded in the CHANGELOG". `CHANGELOG.md` has no `[0.3.4]`/iteration-027 section yet; per `plan.md` (Scale/Scope: "CHANGELOG entry at release") and the `bookwright-release` flow, the changelog is written when the patch is cut, not during implementation. The surviving `unresolved_participants` mention at `CHANGELOG.md:64` is the historical `[0.3.2]` entry and is correct as a record of what iteration 025 shipped. Re-verify when the release is cut that the new CHANGELOG section names the renamed key.
