# Quality Audit — 019-focus-state

**Scope:** 77 changed files vs main (35 source/test — all read in full; remainder are spec artifacts, docs, and the sanctioned Spec Kit v0.10.1 upgrade)
**Commit range:** main..b8953f5
**Date:** 2026-06-11
**Conventions discovered:** `.specify/memory/constitution.md` (v1.4.0), `CLAUDE.md`, `CONTRIBUTING.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 2 |
| **Total** | 3 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%). Total 96.94%; every changed module ≥ 90% (focus package: 97–100%).

All four CI gates verified locally at b8953f5: `pytest` (1109 passed, 1 skipped), `ruff check` clean, `ruff format --check` clean (231 files), `mypy --strict` clean (230 files).

## 2. Conventions Compliance Matrix

### `.specify/memory/constitution.md` (v1.4.0)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle" (Principle I, NON-NEGOTIABLE) | constitution.md:59-66 | io-contract | PASS | `[focus]` lives in `manifest.toml`; `updated_at` stored as a string, TOML-native dates normalized to string (`_focus_block.py:54-71`), never coerced to an opaque form |
| "Introducing an additional runtime dependency requires an amendment" (Principle II) | constitution.md:78-80 | dependency | PASS | `pyproject.toml` / `uv.lock` untouched on this branch |
| "All production code MUST live under `src/bookwright/` … tests under `tests/`" (Principle III, no exceptions) | constitution.md:86-89 | layout | PASS | All 21 source files under `src/bookwright/`, all 14 test files under `tests/` |
| "Each CLI subcommand MUST live in its own module … No source file … may exceed 500 lines" (Principle IV) | constitution.md:97-101 | module-size | PASS | `focus/{show,set,clear}.py` one module each (graph-style sub-app); largest changed file `manifest.py` = 396 lines, largest test 185 |
| "Integrations MUST be … registered in `INTEGRATION_REGISTRY` … monolithic dispatcher forbidden" (Principle V) | constitution.md:108-113 | plugin-shape | PASS | `integration/use.py` change is envelope consolidation only; registry shape untouched |
| "Bookwright MUST emit Agent Skills … and nothing else" (Principle VI, NON-NEGOTIABLE) | constitution.md:121-124 | directory-ban | PASS | No writes/references to `.claude/commands/` or analogues anywhere in the diff; `.claude/skills/speckit-*` changes are the pinned Spec Kit v0.10.1 upgrade |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification" (Principle VII) | constitution.md:133-141 | frontmatter-constraint | N/A | Iteration 019 generates no skills; skill-consuming work comes in later 019–023 iterations |
| "v0 MUST hold a minimum of 80% line coverage" (Principle VIII, NON-NEGOTIABLE) | constitution.md:149-150 | coverage-threshold | PASS | 96.94% total; per changed module see §5 |
| "CI MUST run pytest, ruff, and mypy strict on every push" (Principle VIII) | constitution.md:163-164 | workflow-step | PASS | All four gates run locally on b8953f5, all green |
| "`--json` … MUST emit a single well-formed JSON document on stdout and nothing else" (Principle IX) | constitution.md:171-177 | io-contract | PASS | Single-sourced `emit_json` (`_envelope.py:33`); pinned by tests (`test_set.py:51`, `test_show.py:42` asserts empty stderr, `test_query.py:111+` stderr discipline); exit 2 with JSON error body verified |
| "Section 16 … decisions that are closed … MUST NOT be reopened" (Principle X) | constitution.md:184-192 | scope-ban | PASS | Sync Impact Report explicitly states "reopens no § 16 axiom"; no Grafeo/preset/extension symbols in diff |
| "Runtime dependencies (minimum set): jinja2, packaging, … uuid-utils" | constitution.md:204-207 | dependency | PASS | `check.py:12-24` RUNTIME_MODULES matches the 11-entry list exactly; no additions |
| "deferred … MUST NOT be pulled into the current line": vector search v0.4, export v1.0 | constitution.md:222-226 | scope-ban | PASS | No chromadb/pandoc/export symbols in diff |
| "cancelled … MUST NOT be implemented at all": presets, Grafeo, extra integrations, extensions | constitution.md:228-233 | scope-ban | PASS | No matching symbols/imports in diff |
| "plumbing whose only justification is 'future X' MUST be rejected" | constitution.md:235-238 | scope-ban | PASS | `_project.py` mentions iteration 020 but is load-bearing now (all three focus commands route through it) |
| "Amendments are proposed in a dedicated pull request" (Governance) | constitution.md:247-252 | workflow-step | FAIL | Amendment 1.3.0→1.4.0 landed in commit d1e5aaf on this feature branch, not a dedicated PR → R1 |

### `CLAUDE.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Don't modify Spec Kit *core* (templates, scripts, manifests)" | CLAUDE.md (Spec Kit specifics) | directory-ban | PASS | `.specify/` script/manifest changes are the documented v0.8.16→v0.10.1 upgrade (commit 97a9d79), recorded in CLAUDE.md as deliberate; per-project copies remain editable |
| "do **not** add `--cov-fail-under` anywhere; one source, no drift" | CLAUDE.md (Common commands) | other | PASS | No pyproject/CI change on branch; threshold still single-sourced in `[tool.coverage.report]` |
| "the README, and the `docs/` site are **Spanish**" | CLAUDE.md (Language conventions) | other | PASS | `docs/commands/focus-{set,show,clear}.md` written in Spanish |
| "Source code, identifiers, commit messages … are **English**" | CLAUDE.md (Language conventions) | other | PASS | All branch commits and identifiers English |
| Fixed iteration sequence "specify → clarify → plan → tasks → analyze → implement; do not skip steps" | CLAUDE.md (How work is done) | workflow-step | PASS | See A.4 trail below |
| "Every feature lands through a numbered iteration, not as a freehand commit" | CLAUDE.md (Repository state) | workflow-step | PASS | Branch `019-focus-state` + `specs/019-focus-state/` per plan iteration 019 |

### `CONTRIBUTING.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Allowed in source/tests: FR-0xx / SC-0xx … D-x … bookwright-design.md § N.M" | CONTRIBUTING.md:51-56 | other | PASS | New code's FR/SC/D refs all resolve to `specs/019-focus-state/` artifacts; refs paired with reasons per the stated preference |
| "Forbidden in source/tests … US-x / +USx … T0xx" | CONTRIBUTING.md:58-61 | directory-ban | PASS | grep over every changed src/tests file: zero hits; the iteration-017 meta gate (`tests/meta/test_no_traceability_tags.py`) also passed in the suite |
| "Run before pushing: ruff check, ruff format --check, mypy, pytest" | CONTRIBUTING.md:32-43 | workflow-step | PASS | All four executed in this audit, all green |

### Track integrity (A.3)

`git status` is clean and `git ls-files --others --ignored` over `specs/`, `.claude/`, `docs/`, `.specify/`, `src/`, `tests/` returns only `__pycache__`/`.pyc` files and `.claude/settings.local.json`. Every governance artifact in `specs/019-focus-state/` appears in the branch diff. **No git-invisible governance files.**

### Workflow trail (A.4)

`spec.md` (commit 846f32d) → clarify (e469332f, clarifications encoded in spec) → `plan.md`/`research.md`/`data-model.md`/`contracts/`/`quickstart.md` (192aaac) → `tasks.md` (27/27 tasks `[X]`) → analyze (evidenced: constitution Sync Impact Report cites "/speckit-analyze on iteration 019-focus-state (finding C1)") → implement (source + tests, gates green). **Trail complete, no step skipped.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | MEDIUM | .specify/memory/constitution.md:269 (commit d1e5aaf) | Constitution amendment 1.3.0→1.4.0 bundled into the 019 feature branch; Governance prescribes "a dedicated pull request" | State the amendment (bump type + rationale) explicitly in the 019 PR description, or split d1e5aaf's constitution hunk into its own PR before merging |
| R2 | B | LOW | src/bookwright/commands/_envelope.py:1, src/bookwright/core/manifest.py:228-241, tests/fixtures/manifests.py:1 | Review-ID comments ("review R1", "R10", "R23", "iteration 019 review") cite review artifacts that are overwritten on each re-audit — outside CONTRIBUTING.md's allowed FR/SC/D tag set, and their referents decay | On next touch, keep the *why* (the contract being protected) and drop the review-ID citation; git blame preserves lineage |
| R3 | D | LOW | src/bookwright/commands/focus/set.py:25-27 | `_today()` is monkeypatched in every test, so its real one-line body is the focus package's only uncovered statement — intentional test seam (research D5), recorded for transparency | Nothing to do; not worth a clock-freezing E2E |

## 4. Remediation Detail

### R1 — Constitution amendment rode the feature branch instead of a dedicated PR

- **Where:** `.specify/memory/constitution.md` (1.3.0 → 1.4.0), commit d1e5aaf "chore: housekeeping after Spec Kit upgrade + constitution scope refresh"
- **Why it matters:** the Governance section's amendment procedure exists so constitution changes are reviewed on their own terms, not approved implicitly inside a feature merge. The amendment is exemplary in substance — version bumped, Sync Impact Report updated, MINOR rationale stated, no principle reworded, no § 16 axiom reopened — so this is a process deviation, not a content problem. It was also *triggered by* this iteration (`/speckit-analyze` finding C1), which explains, without fully excusing, the bundling.
- **Suggested change:** lowest-cost path — state the amendment explicitly in the 019 PR description (bump type MINOR + rationale, lifted verbatim from the Sync Impact Report) so the reviewer approves it knowingly. Strict-compliance path — split d1e5aaf's constitution hunk into a dedicated PR merged ahead of 019.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/cli.py | 100.00% | 80% | PASS |
| src/bookwright/commands/_envelope.py | 100.00% | 80% | PASS |
| src/bookwright/commands/_project.py | 100.00% | 80% | PASS |
| src/bookwright/commands/check.py | 95.56% | 80% | PASS |
| src/bookwright/commands/focus/__init__.py | 100.00% | 80% | PASS |
| src/bookwright/commands/focus/clear.py | 100.00% | 80% | PASS |
| src/bookwright/commands/focus/errors.py | 100.00% | 80% | PASS |
| src/bookwright/commands/focus/set.py | 97.06% | 80% | PASS |
| src/bookwright/commands/focus/show.py | 100.00% | 80% | PASS |
| src/bookwright/commands/graph/build.py | 90.74% | 80% | PASS |
| src/bookwright/commands/graph/query.py | 94.03% | 80% | PASS |
| src/bookwright/commands/init/envelope.py | 97.40% | 80% | PASS |
| src/bookwright/commands/integration/use.py | 100.00% | 80% | PASS |
| src/bookwright/commands/validate.py | 90.36% | 80% | PASS |
| src/bookwright/commands/version.py | 90.00% | 80% | PASS |
| src/bookwright/core/_focus_block.py | 100.00% | 80% | PASS |
| src/bookwright/core/manifest.py | 98.73% | 80% | PASS |
| **Suite total** | **96.94%** | 80% | **PASS** |

## 6. Inability-to-verify notes

- **TDD signal (Pass D heuristic):** branch implementation commits are bulk "[Spec Kit] Implementation progress" snapshots, so per-file test-before-impl ordering is not recoverable from `git log`. The Spec Kit task flow orders test tasks before implementation tasks in `tasks.md`, which is the available (indirect) evidence.
- **Passes B (smells) and C (patterns) produced no findings beyond R2.** The iteration's structural moves run *against* the usual smell directions: the per-group `emit_json`/`emit_error` copies (3 occurrences — exactly the DRY threshold) were consolidated into `_envelope.py`, `graph/envelope.py` deleted, `FocusBlock` extracted to keep `manifest.py` under the Principle IV ceiling, the `outside_project` fixture hoisted to the shared conftest, and the manifest literal single-sourced in `tests/fixtures/manifests.py`. No singleton/factory/observer misuse; the focus sub-app mirrors the existing `graph` sub-app pattern; `rich` markup injection from author text is explicitly neutralized (`markup=False`) and pinned by tests.
- **Pass D security:** no user-controlled path joins beyond `find_project_root()` (upward walk from cwd; writes confined to the resolved project's `manifest.toml` via atomic tempfile-in-parent + `os.replace`/`os.link`); no `yaml.load`/pickle/eval/`shell=True`; no secrets; all file-boundary input crosses Pydantic `strict=True, extra="forbid"` validation. Nothing to flag.
