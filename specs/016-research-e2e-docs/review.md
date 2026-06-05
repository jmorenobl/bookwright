# Quality Audit — 016-research-e2e-docs

**Scope:** 35 changed files vs `main` (0 under `src/` — 1 test module, docs/config, fixture, governance artifacts)
**Commit range:** `main`..`9d917b4`
**Date:** 2026-06-05
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.3.0), `CONTRIBUTING.md`, `README.md` (dev sections)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 3 |
| **Total** | 3 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; full-suite total **96.78%**, `1045 passed, 1 skipped, 1 deselected`). New E2E module `tests/e2e/test_research_workflow.py`: **10 passed**. `mkdocs build --strict`: **PASS** (built clean — the red banner is mkdocs-material's vendor 2.0 notice, not a build warning; FR-021 zero-warnings gate holds).

This is the closing M4/v0.2.0 consolidation iteration: it ships **no new product mechanism** — a worked `tiny-historical` fixture, one E2E regression, and the v0.2.0 docs set. It already received a quality-audit pass (committed at `9d917b4`). This re-audit confirms the branch is merge-ready; all three findings are cosmetic LOW nits (two doc-accuracy, one test maintainability) with no behavioral impact.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle … Binary stores … forbidden as canonical storage" | `constitution.md:57` | layout | PASS | Fixture is `.md`/`.toml`; `test_committed_fixture_is_source_only` asserts no committed `graph.ttl`/`.claude`/`SKILL.md` |
| "Introducing an additional runtime dependency requires an amendment" | `constitution.md:76` | dependency | N/A | `pyproject.toml` not in diff — no dependency change |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:84` | layout | PASS | New code is `tests/e2e/…` + `tests/fixtures/…`; docs under `docs/` |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:96` | module-size | PASS | `test_research_workflow.py` = 306 lines |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`" | `constitution.md:95` | module-size | N/A | No CLI subcommand added/changed |
| Integrations MUST subclass `SkillsIntegration` registered in `INTEGRATION_REGISTRY` | `constitution.md:106` | plugin-shape | N/A | No integration added; test *uses* `integration use claude` |
| "Writing to `.claude/commands/`, `.agents/commands/`, or any analogous … directory is prohibited" | `constitution.md:120` | directory-ban | PASS | No `commands/` path written; skills documented in `docs/authoring.md` + research page, not `docs/commands/` |
| Every `SKILL.md` MUST satisfy the agentskills.io spec (name<64 == dir, description<1024) | `constitution.md:131` | frontmatter-constraint | N/A | No `SKILL.md` authored or modified |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:147` | coverage-threshold | PASS | Full suite = 96.78%; `fail_under = 80` reached |
| Commands consumed by an agent MUST accept `--json` and emit one JSON doc on stdout only | `constitution.md:169` | io-contract | PASS | Test consumes existing `--json`; no new command/contract |
| Section-16 design axioms MUST NOT be reopened (rdflib / no-vectors / Agent-Skills-only) | `constitution.md:182` | scope-ban | PASS | Verification reads research Markdown via existing graph; no Grafeo/vectors (FR-022) |
| Deferred capabilities (presets, GrafeoIndexer/vectors, …) MUST NOT be pulled into v0 scope | `constitution.md:216` | scope-ban | PASS | Pure consolidation; no "future X" plumbing — grep clean |
| "no production module may be imported from outside `src/bookwright/`" | `constitution.md:84` | layout | PASS | Test imports `bookwright.cli`, `bookwright.io.frontmatter`, `tests.conftest` only |
| docs/ site is Spanish — keep edits in Spanish; code/identifiers/spec artifacts English | `CLAUDE.md` (Language) | other | PASS | `docs/research.md`/`changelog.md` Spanish; test module + spec artifacts English |
| "do NOT add `--cov-fail-under` anywhere; one source, no drift" | `CLAUDE.md` (Common cmds) | coverage-threshold | PASS | No second `fail_under`; FR-019 keeps the single 80% gate (D10) |
| Fixed workflow `specify→clarify→plan→tasks→analyze→implement` (do not skip steps) | `CLAUDE.md` (How work) | workflow-step | PASS | A.4 below — full trail present |

**A.3 — Track integrity:** `git status --porcelain` clean; every `specs/016-research-e2e-docs/*`, `docs/*`, `mkdocs.yml`, fixture, and test file appears in `git diff main...HEAD`. No uncommitted/untracked/`.gitignore`-shadowed governance artifact. **PASS.**

**A.4 — Workflow-trail integrity:** `spec.md` (has `## Clarifications` → clarify ran) → `plan.md` → `tasks.md` → analyze (commit `2726739` "resolve /speckit-analyze cross-artifact findings") → implement (code/fixtures/docs). Every downstream artifact has its upstream. **PASS.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | LOW | `mkdocs.yml:13` | Comment cites "(D5, FR-014)" for the strict zero-warnings gate; the gate is **FR-021** and the docs-strict decision is **D7** (`research.md:165`). D5 is "What E2E test means"; FR-014 is disabled-block inertness. | Change the comment to `(D7, FR-021)`. |
| R2 | A | LOW | `plan.md:133` | Plan lists `docs/validation.md` as `# EDIT — add factual_anchor (FR-016)`, but the file is **unchanged vs main** — `factual_anchor` was already documented there in iteration 014, so the planned edit was a no-op. FR-016 is satisfied regardless. | Optionally note in the plan that validation.md was already compliant; no code change. |
| R3 | D | LOW | `test_research_workflow.py:133-135` | Entity counts `sources == 4`, `findings == 6`, `anchors == 4` are inline magic numbers; only the `factual_anchor` counts + anchor IDs come from the oracle, so the docstring's "never hard-coded" framing doesn't cover them. | Optional: lift the three structural counts into `expected-findings.md` front-matter, or annotate them as structural (non-oracle) assertions. |

## 4. Remediation Detail

*No CRITICAL or HIGH findings. All three are LOW (cosmetic/informational); none blocks merge.*

### R1 — mkdocs.yml comment cites the wrong decision/FR anchors

- **Where:** `mkdocs.yml:13`
- **Why it matters:** A comment-as-documentation pointing at the wrong governance anchors misleads the next reader who follows the cross-reference. The strict-build gate is FR-021 ("docs build with no warnings", `spec.md:290`); its rationale is D7 ("Documentation placement and the docs-match gate", `research.md:165`). The cited D5/FR-014 are the E2E-test-meaning decision and the disabled-block inertness requirement — unrelated to `strict: true`.
- **Suggested change:** replace `(D5, FR-014)` with `(D7, FR-021)` in the `strict: true` comment block.

### R2 — plan.md describes a validation.md edit that didn't happen

- **Where:** `plan.md:133` (and the prose at `plan.md:66`)
- **Why it matters:** The plan's Project Structure lists `docs/validation.md` under "# EDIT" for FR-016, but `git diff main...HEAD -- docs/validation.md` is empty — the `factual_anchor` row already shipped in iteration 014. The requirement is met; the plan just over-describes the work. Harmless, but a reader auditing FR-016 against the diff will find a phantom edit.
- **Suggested change:** drop validation.md from the EDIT list (or annotate "already present since iter 014"). No source change.

### R3 — Structural entity counts are hard-coded outside the oracle

- **Where:** `tests/e2e/test_research_workflow.py:133-135`
- **Why it matters:** The module docstring states the planted-defect expectations load from the oracle and are "NEVER hard-coded" — accurate for the `factual_anchor` counts and anchor slugs, but the build's entity tallies (4/6/4) sit as bare literals with only an inline comment. Defensible as *structural* (not planted-defect) assertions, so this is a maintainability nit, not a correctness issue: a future fixture growth needs a manual edit the docstring doesn't lead you to.
- **Suggested change:** either move the three counts into `expected-findings.md` front-matter (single source for all fixture expectations) or annotate them explicitly as structural assertions distinct from the oracle.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| (whole `src/bookwright/`, full suite) | 96.78% | 80% (enforced) | PASS |
| `validation/validators/factual_anchor.py` (M4 surface) | 83.11% | 85% (report-only, FR-019) | OK — above the global gate; the 85% M4 target is verified-at-review, not a CI gate |
| `io/research.py` (M4 surface) | 77.45% | 85% (report-only) | Note — below the report-only M4 target; pre-existing (iter 012), unchanged this branch |

\* Per-module figures are not gated (the project single-sources one global `fail_under = 80`; "one source, no drift"). This iteration adds **no `src/` code**, so no changed module regressed.

## 6. Inability-to-verify notes

- **Defect #3 (prose anachronism)** is verified only at the *precondition* level (the contradicted anchor is queryable, `bookwright-verify` materializes). Correct and intentional: the LLM skill's judgment rotates and can't be asserted in CI (FR-012, D4). The planted text (`sonó el teléfono … 1851`) was confirmed present at `manuscript/01-el-telar-nuevo.md:15`.
- **A.4 `analyze` step** has no standalone artifact; completion is evidenced by commit `2726739`. Trail treated as intact.
- `ruff`/`mypy` gates were not re-run in this pass (no `src/` change; the prior audit at `2dd0fc9` recorded all four green). The enforced gate exercised here is the full `pytest` run + `mkdocs --strict`.
