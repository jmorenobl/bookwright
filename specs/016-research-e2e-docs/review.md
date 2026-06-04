# Quality Audit — 016-research-e2e-docs

**Scope:** 34 changed files vs `main` (1 test module, 5 docs/config, 18 fixture files, 10 governance artifacts)
**Commit range:** `main`..`2dd0fc9`
**Date:** 2026-06-05
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.3.0), `CONTRIBUTING.md`, `specs/016-research-e2e-docs/plan.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 2 |
| **Total** | 2 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%). Full-suite line coverage **96.78%** (1045 passed, 1 skipped). This iteration adds **no `src/` production code**, so the gate measures the pre-existing surface plus the new E2E regression.

All four CI gates verified locally: `ruff check` ✓, `ruff format --check` ✓, `uv run mypy` (strict, 210 files) ✓ *no issues*, `pytest` ✓. `mkdocs build --strict` ✓ (FR-021 zero-warnings gate holds — the red "Material for MkDocs team" banner is a vendor nag, not a build warning; build exited 0).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle … Derived caches MAY exist … if … rebuildable" | `constitution.md:57` | layout | PASS | Fixture is `.md`/`.toml`; `test_committed_fixture_is_source_only` asserts no committed `graph.ttl`/`.claude`/`SKILL.md` |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | `constitution.md:76` | dependency | N/A | `pyproject.toml` not in diff — no dependency change |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:84` | layout | PASS | New code is `tests/e2e/test_research_workflow.py` + `tests/fixtures/…`; docs under `docs/` |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:96` | module-size | PASS | `test_research_workflow.py` = 306 lines |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`" | `constitution.md:95` | module-size | N/A | No CLI subcommand added/changed on this branch |
| Integrations MUST subclass `SkillsIntegration` registered in `INTEGRATION_REGISTRY` | `constitution.md:106` | plugin-shape | N/A | No integration added; test *uses* `integration use claude`, does not define one |
| "Writing to `.claude/commands/`, `.agents/commands/`, or any analogous … directory is prohibited" | `constitution.md:120` | directory-ban | PASS | No `commands/` path written; grep of diff clean |
| Every `SKILL.md` MUST satisfy the agentskills.io spec (name<64 == dir, description<1024) | `constitution.md:131` | frontmatter-constraint | N/A | No `SKILL.md` authored or modified |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:147` | coverage-threshold | PASS | Full suite = 96.78%; gate `fail_under = 80` reached |
| "CI MUST run pytest, ruff, and mypy strict on every push and pull request" | `constitution.md:161` | io-contract | PASS | All four gates green locally; CI config unchanged |
| Commands consumed by an agent MUST accept `--json` and emit one JSON doc on stdout only | `constitution.md:169` | io-contract | PASS | Test consumes existing `--json`; no new command/contract |
| Section-16 design axioms MUST NOT be reopened (rdflib/no-vectors/Agent-Skills-only) | `constitution.md:182` | scope-ban | PASS | Verification reads research Markdown via existing graph; no Grafeo/vectors |
| Deferred capabilities (presets, GrafeoIndexer/vectors, …) MUST NOT be pulled into v0 scope | `constitution.md:216` | scope-ban | PASS | Pure consolidation; no "future X" plumbing (FR-022) — grep clean |
| "no production module may be imported from outside `src/bookwright/`" | `constitution.md:84` | layout | PASS | Test imports `bookwright.cli`, `bookwright.io.frontmatter`, `tests.conftest` only |
| Fixed workflow `specify→clarify→plan→tasks→analyze→implement` (do not skip steps) | `CLAUDE.md` | workflow-step | PASS | See A.4 below — full trail present |
| Forbidden inline tags in source/tests: `US-x`, `T0xx` (task IDs) | `CONTRIBUTING.md:58` | other | PASS | Test cites `FR-008..FR-014`, `D4`, `E1`, Principle IX — all allowed refs; no `US`/`T0xx` |

**A.3 — Track integrity:** `git status --porcelain` is clean; every `specs/016-research-e2e-docs/*`, `docs/*`, `mkdocs.yml`, fixture, and test file appears in `git diff main...HEAD`. No uncommitted/untracked/`.gitignore`-shadowed governance artifact. **PASS.**

**A.4 — Workflow-trail integrity:** `spec.md` (has a `## Clarifications` section → clarify ran) → `plan.md` → `tasks.md` → analyze (commit `2726739` "resolve /speckit-analyze cross-artifact findings") → implement (code/fixtures/docs). All upstream artifacts present for every downstream one. **PASS.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | LOW | specs/016-research-e2e-docs/plan.md:133 | `plan.md` lists `docs/validation.md` as an EDIT (FR-016), but the file is unchanged vs `main` — `factual_anchor` was already documented there in iteration 014 | None needed; optionally note in the plan that the edit was a no-op. Cross-links from `research.md`/`authoring.md` resolve (strict build passed). |
| R2 | D | LOW | tests/e2e/test_research_workflow.py:257-258 | Inertness test toggles the manifest via `str.replace("enabled = true", "enabled = false")`; relies on that literal being unique to `[research]` | Acceptable — `[validators] enabled = []` differs, so the match is unambiguous. If a future `enabled = true` is added elsewhere, switch to a TOML-aware edit. |

## 4. Remediation Detail

No CRITICAL or HIGH findings — nothing to expand. Both findings are LOW (informational); neither blocks merge.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| (whole `src/bookwright/`, full suite) | 96.78% | 80% | PASS |
| `io/research.py` | 77.45%* | 80% | informational — pre-existing (iter 012), unchanged this branch |
| `validation/validators/factual_anchor.py` | 83.11%* | 80% | PASS — pre-existing (iter 014), unchanged this branch |

\* Per-module figures are not gated (the project single-sources one global `fail_under = 80`; "one source, no drift"). Listed only for context. This iteration adds **no `src/` code**, so no changed module is below the bar.

## 6. Inability-to-verify notes

- **Defect #3 (prose anachronism)** is verified only at the *precondition* level (the contradicted anchor is queryable, the `bookwright-verify` skill materializes). This is correct and intentional: the LLM skill's judgment output rotates and cannot be asserted in CI (FR-012, plan §Summary). The planted text (`sonó el teléfono … 1851`) was confirmed present in `manuscript/01-el-telar-nuevo.md:15`.
- Single-file `mypy` invocation reports spurious `import-untyped` errors; the project's configured run (`uv run mypy`, `files = src + tests`) is the authority and reports **no issues in 210 files**.
