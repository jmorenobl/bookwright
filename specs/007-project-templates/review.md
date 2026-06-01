# Quality Audit — 007-project-templates

**Scope:** 41 changed files vs `main`
**Commit range:** main..959dee1
**Date:** 2026-06-01
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.2.0), `CONTRIBUTING.md`, `README.md`, plus feature contracts (`specs/007-project-templates/contracts/{frontmatter,skeleton-walker,template-format}.md`)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 1 |
| **Total** | 2 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%). Full suite: 650 passed, 1 skipped, **97.01%** line coverage on `src/bookwright/`. This iteration adds zero production Python, so the global figure is unchanged from `main` (Constitution VIII recorded N/A in plan.md; the suite still runs green in CI).

> Note: running only `tests/resources/` reports 59.71% and "fails" the gate — that is an artifact of the project-wide `--cov-fail-under=80` in `pyproject.toml` applied to a subset, **not** a regression. The full suite is the gate of record.

## 2. Conventions Compliance Matrix

One row per extracted rule. Grouped by source.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … are forbidden as canonical storage" | `constitution.md:47` | layout | PASS | Diff is `.md`/`.j2`/`.tmpl`/`.toml`/`.py` only; no binary store |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | `constitution.md:64` | dependency | PASS | `pyproject.toml:20-32` deps == constitution's allowed set exactly; no additions |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:72` | layout | PASS | Resources under `src/bookwright/resources/`; suite under `tests/resources/` |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:85` | module-size | PASS | Largest changed code file `tests/resources/helpers.py` = 87 lines |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`" | `constitution.md:83` | module-size | N/A | No CLI subcommand added or modified (FR-023) |
| "Integrations MUST be … subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`" | `constitution.md:94` | plugin-shape | N/A | No integration code touched |
| "Writing to `.claude/commands/`, `.agents/commands/`, or any analogous … directory is prohibited" | `constitution.md:108` | directory-ban | PASS | No `commands/` dir written; molds target `bible/`/`manuscript/` |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" | `constitution.md:119` | frontmatter-constraint | N/A | No `SKILL.md` generated this iteration (skills land in iter 9) |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:135` | coverage-threshold | PASS | Full suite = 97.01% |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a `--json` flag" | `constitution.md:148` | io-contract | N/A | No CLI output contract changed |
| "Section 16 … decisions that are closed … MUST NOT be reopened in spec, plan, or task" | `constitution.md:161` | scope-ban | PASS | § 6 layout split is structural, not a § 16 axiom; recorded in CHANGELOG (plan.md:88) |
| "A pull request that introduces any of the deferred capabilities … MUST be rejected" (presets/extensions) | `constitution.md:206` | scope-ban | PASS | No `resolve_template()`, preset, or extension plumbing (FR-024); confirmed in plan + CHANGELOG |
| "Build backend: `hatchling`. Lockfile: `uv.lock` committed" | `constitution.md:185` | dependency | PASS | `pyproject.toml:37-39` unchanged; `uv.lock` present |
| "Forbidden in source/tests … `US-x` / `+USx` — user-story / backlog tags" | `CONTRIBUTING.md:59` | other | **FAIL** | `tests/resources/test_mold_structure.py:1` docstring opens with `US3` → see R1 |
| "Forbidden in source/tests … `T0xx` — task IDs from `tasks.md`" | `CONTRIBUTING.md:60` | other | PASS | No `T0xx` in this branch's new files (`tests/resources/`, `resources/`) |
| Indexed frontmatter uses only mapper-recognized keys (Character/Setting/Timeline/Relationships) | `contracts/frontmatter-contract.md:C2` | frontmatter-constraint | PASS | `test_mold_structure` + `test_frontmatter_contract` green; `unknown_keys == []` |
| timeline.md / relationships.md ship frontmatter exactly `events: []` / `relationships: []` | `contracts/frontmatter-contract.md:C4` | frontmatter-constraint | PASS | `timeline.md:1-3`, `relationships.md:1-3`; asserted by `test_indexed_collections_have_exactly_one_top_key` |
| `character` `name` is a quoted non-empty string (bare `[PENDING]` parses as YAML list) | `contracts/frontmatter-contract.md:C3` | frontmatter-constraint | PASS | `character.md.tmpl:2` `name: "[PENDING: …]"`; `test_character_name_is_quoted_non_empty_string` green |
| Skeleton singletons use `.md` or `.j2` — never `.tmpl` under `project/` | `contracts/skeleton-walker-contract.md:W1` | layout | PASS | `project/` tree contains no `.tmpl`; molds isolated under `templates/` |
| `.j2` files reference only the 5 scaffold context keys | `contracts/skeleton-walker-contract.md:W2` | io-contract | PASS | `test_skeleton_renders` renders under `StrictUndefined` with no `UndefinedError` |
| Spanish human prose; English frontmatter keys + `[PENDING]` token | `contracts/template-format.md:F2` | other | PASS | `test_template_prose_is_spanish` green across all authored templates |
| No stub / scaffolding sentinels survive (FR-022) | `contracts/template-format.md:F5` | other | PASS | `test_no_stub_sentinels` sweeps both trees + a stamped temp project |
| `CHANGELOG.md` credits the preset + records the § 6 supersession (FR-021) | `contracts/template-format.md:F6` | other | PASS | `CHANGELOG.md:28-49`; `test_changelog_records_credit_and_supersession` green |
| `manifest.template.toml` is verify-only, not re-authored (FR-025) | `plan.md:139` | other | PASS | File present, not in branch diff |

**Workflow-trail integrity (A.4):** PASS. `spec.md` → 2 `Clarification` annotations → `plan.md` → `tasks.md` → 2 `[Spec Kit] Add analysis report` commits → source+tests under the source root. No downstream artifact exists without its upstream predecessor.

**Track-integrity (A.3):** PASS. `git status --porcelain` is empty; every file under `specs/007-project-templates/`, `src/bookwright/resources/`, and `tests/resources/` is tracked and committed on the branch. No uncommitted or `.gitignore`-shadowed governance artifact.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | MEDIUM | tests/resources/test_mold_structure.py:1 | Docstring opens with `US3`, a user-story tag `CONTRIBUTING.md:59` lists as "Forbidden in source/tests" | Replace `US3` with the durable `SC-`/`FR-` ref the test actually validates (e.g. mold structure → SC-004/FR-012..016), or drop the tag |
| R2 | D | LOW | src/bookwright/resources/project/.gitignore:18 | `.env.*` in the stamped project's gitignore would also ignore a `.env.example` an author might commit | Optional: add `!.env.example` negation, or leave as-is (no `.env.example` convention exists for authoring projects) |

## 4. Remediation Detail

### R1 — Forbidden user-story tag in a test docstring

- **Where:** `tests/resources/test_mold_structure.py:1` — `"""US3 independent test — every \`\`*.tmpl\`\` mold is well-formed.`
- **Why it matters:** `CONTRIBUTING.md:58-60` lists `US-x` / `+USx` (user-story / backlog tags) as **Forbidden in source/tests** because they are "planning bookkeeping with no durable artifact" — once `tasks.md`/user-story numbering is gone, the tag points nowhere, exactly the staleness the rule exists to prevent. The allowed alternatives (`FR-0xx`, `SC-0xx`, `D-x`, `bookwright-design.md § N.M`) freeze on merge and stay resolvable.
- **Context (not a blocker):** the same `US`-tag pattern is pervasive in **already-merged** iterations (`tests/core/*`, `tests/integrations/*`, `tests/commands/*`) — those are out of this branch's diff scope and frozen by CONTRIBUTING's "numbers freeze on merge" rule, so they are not findings here. But it means the project has an established house habit that contradicts its own written rule. Either honor the rule going forward (fix R1) or relax CONTRIBUTING — that second option is a deliberate edit to the convention file, not something this audit should assume.
- **Suggested change:** the module already validates mold well-formedness for the molds authored under FR-012..FR-016 / SC-004; retitle the docstring to one of those durable refs, e.g. `"""Mold structure — every *.tmpl is well-formed (FR-012..016, SC-004)."""`.

## 5. Coverage Detail

| Module group | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/` (full suite) | 97.01% | 80% | PASS |
| New executable lines this iteration | 0 added | 80% | N/A — prose-only deliverable (plan.md Complexity Tracking) |

## 6. Inability-to-verify notes

- **Subset-run coverage is misleading by design.** `pyproject.toml:81` pins `--cov-fail-under=80` in `addopts`, so any `pytest <subset>` invocation (e.g. `tests/resources/` alone, 59.71%) reports a false gate failure. Verified the real number with the full suite (97.01%). Not a finding — pre-existing project config from iteration 1.
- **Spanish-prose check is heuristic.** `looks_spanish` (helpers.py:72) counts ≥3 function words; it confirms language but cannot judge prose quality. Manual read of all 12 skeleton documents + 5 molds found the prose consistent, idiomatic, and on-spec (worked examples inside HTML comments, `[PENDING]` questions in author-fill sections).
</content>
