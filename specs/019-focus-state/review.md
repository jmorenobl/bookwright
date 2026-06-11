# Quality Audit — main (iteration 019-focus-state, post-merge)

**Scope:** 99 changed files vs `v0.2.0` (33 source/test files, 1 project config, the rest specs/docs/assets)
**Commit range:** v0.2.0..4cac153
**Date:** 2026-06-11
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0)

Note: `main` is the current branch; the `019-focus-state` branch tip equals
`main` HEAD (fast-forward merge), so the audit range is the last release tag →
HEAD. This report supersedes the pre-merge review previously at this path
(compare via `git diff`).

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
| LOW | 2 |
| **Total** | 5 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%). Total
96.94%; lowest changed module 90.00% (`commands/version.py`). All four CI gates
verified locally: `ruff check`, `ruff format --check`, `mypy --strict` (230
files), `pytest` (1109 passed, 1 skipped).

## 2. Conventions Compliance Matrix

### `.specify/memory/constitution.md` (v1.4.0)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle … Binary stores … forbidden as canonical storage" | constitution.md:60-66 | layout | PASS | New `assets/banner.png` / `loop.png` are README/PyPI render assets, regenerable from committed SVGs via `scripts/banner-png.sh` — not canonical storage. `[focus]` persists as TOML strings (`updated_at` never coerced to a date type). |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | constitution.md:78-80 | dependency | PASS | `pyproject.toml` diff adds only packaging metadata (`readme`, `[project.urls]`, NOTICE in `license-files`); `[project.dependencies]` untouched. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | constitution.md:86-89 | layout | PASS | Every new module under `src/bookwright/` (focus package, `_project.py`, `_focus_block.py`) or `tests/`. |
| "Each CLI subcommand MUST live in its own module … No source file … may exceed 500 lines" | constitution.md:97-100 | module-size | PASS | `focus` split into `set.py`/`show.py`/`clear.py`/`errors.py`. Largest changed file: `core/manifest.py` at 396 lines. |
| "Integrations MUST be … registered in `INTEGRATION_REGISTRY` … monolithic dispatcher … forbidden" | constitution.md:108-113 | plugin-shape | PASS | `integration/use.py` resolves via `get(key)` against the registry; no type ladders introduced anywhere in the diff. |
| "Writing to `.claude/commands/`, `.agents/commands/`, or any analogous … directory is prohibited" | constitution.md:122-124 | directory-ban | PASS | Diff grep: zero references to legacy command directories. |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification" | constitution.md:133-141 | frontmatter-constraint | PASS | The only new SKILL.md (`speckit-agent-context-update`, both trees) has `name` matching its parent dir, description ≪1024 chars, valid frontmatter. It is Spec Kit–managed, not bookwright-generated; the generator and `lint_skill_md` gate are untouched. |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | constitution.md:149-150 | coverage-threshold | PASS | 96.94% total; per-module detail in §5. |
| "CI MUST run pytest, ruff, and mypy strict on every push and pull request; a red bar blocks merge" | constitution.md:163-164 | workflow-step | PASS | All four gates re-run locally for this audit: green. |
| "a `--json` flag and, when set, emit a single well-formed JSON document on stdout and nothing else" | constitution.md:170-173 | io-contract | PASS | All three focus verbs route through the single-sourced `emit_json`/`emit_error` (`commands/_envelope.py`); tests pin stdout emptiness in human mode and stderr emptiness under `--json` (e.g. `test_show.py:42`, `test_set.py:47`). `check`/`version`/`graph` were consolidated onto the same helper (net deletion of `graph/envelope.py`). |
| "Section 16 … axioms … MUST NOT be reopened in spec, plan, or task discussions" | constitution.md:184-192 | scope-ban | PASS | No axiom reopened; rdflib remains the only engine; skills-only delivery intact. See R3 for a scope ambiguity around design § 16.6 ("Sin scripts shell") and the two new `scripts/*.sh` — dev tooling, not toolkit surface, hence PASS here. |
| "deferred … MUST NOT be pulled into the current line ahead of their milestone" / cancelled list | constitution.md:222-238 | scope-ban | PASS | `[focus]` + `bookwright focus` is iteration 019, the sanctioned M5/v0.3 work. Diff grep for `chromadb`/`Grafeo`/preset plumbing: zero hits. `_project.py` is justified today by three concrete callers, not "future X". |
| "Amendments are proposed in a dedicated pull request that updates … constitution.md, bumps the version line" | constitution.md:247-253 | workflow-step | FAIL | The 1.3.0→1.4.0 amendment landed inside `d1e5aaf` ("chore: housekeeping after Spec Kit upgrade + constitution scope refresh"), bundled with the Spec Kit pin bump — not a dedicated change. See R1. |

### `CLAUDE.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "do **not** add `--cov-fail-under` anywhere; one source, no drift" | CLAUDE.md (Common commands) | coverage-threshold | PASS | Threshold still single-sourced in `[tool.coverage.report]`; no flag added anywhere in the diff. |
| "Each iteration is a branch `NNN-<short-name>` … Merge to `main` only when tests are green" | CLAUDE.md (How work is done) | workflow-step | PASS | Branch `019-focus-state` exists; its tip equals `main` HEAD (fast-forward). Gates green, `tasks.md` fully checked, `/speckit-analyze` evidenced (constitution Sync Impact Report cites its finding C1). |
| "Don't modify Spec Kit *core* (templates, scripts, manifests)" | CLAUDE.md (Spec Kit specifics) | scope-ban | PASS | `.specify/scripts/`, templates, and `speckit-*` SKILL.md files changed only via the documented v0.8.16→v0.10.1 upgrade (97a9d79); per-project copies (`extensions.yml`) edited as permitted. |
| "bookwright-design.md, bookwright-implementation-plan.md … are **Spanish** … code, identifiers, commit messages … **English**" | CLAUDE.md (Language conventions) | other | PASS | § 21 design additions are Spanish; all new identifiers/docstrings/commits English. |
| Repository-state section: "no iteration branch exists for it yet" / iterations table ends at 018 | CLAUDE.md (Repository state) | track-integrity | FAIL | CLAUDE.md still describes 019 as not started while its implementation is merged on `main`. Stale convention file — see R2. |

**Track integrity (A.3):** `git status` is clean; every file under
`specs/019-focus-state/`, `.claude/skills/`, and `.specify/` is tracked and
committed on `main`. No uncommitted or `.gitignore`-shadowed governance
artifacts. PASS.

**Workflow trail (A.4):** spec (846f32d) → clarify (e469be2) → plan/research/
tasks (192aaac) → analyze (finding C1 recorded in the constitution Sync Impact
Report and `checklists/`) → implement (ad454b9..4cac153). No step skipped. PASS.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | MEDIUM | .specify/memory/constitution.md:247 (commit d1e5aaf) | Constitution amendment 1.3.0→1.4.0 bundled into a housekeeping commit; Governance requires a dedicated change | Already merged — not retroactively fixable. For the next amendment, isolate it in its own commit/PR whose description states the bump type, per the Governance procedure. |
| R2 | A | MEDIUM | CLAUDE.md (Repository state + iterations table) | CLAUDE.md still says 019 has no branch and its table ends at 018, while 019 is implemented and merged | Refresh the repository-state paragraph and the iterations table to record 019 ✅ merged and name 020 (`bookwright status`) as the next planned iteration. |
| R3 | A | MEDIUM | scripts/publish.sh, scripts/banner-png.sh | First first-party bash outside `.specify/`; design § 16.6 axiom reads "Sin scripts shell. Todo Python, vía Typer" | The axiom's context (design lines 1404, 2039) governs the toolkit surface, not repo tooling — but the boundary is undocumented. Either port `publish.sh` to a `uv run` Python script or add one clause to design § 16.6 scoping the axiom to shipped functionality. |
| R4 | D | LOW | scripts/publish.sh:50 | Echoes the first 9 chars of the PyPI token (4 real chars past the `pypi-` prefix) to the terminal | Drop the preview line or print only `pypi-…[hidden]`. |
| R5 | B | LOW | src/bookwright/commands/focus/set.py:1, focus/__init__.py:23 | Module named `set` shadows the builtin (`from . import set as set`) | Cosmetic and contained (nothing imports the module by bare name). Optionally rename the module `set_.py` while keeping the CLI verb `set`; fine to leave as-is. |

No CRITICAL or HIGH findings. Overflow: none (5 total).

## 4. Remediation Detail

No CRITICAL or HIGH findings — this section is intentionally empty. The three
MEDIUMs are governance/documentation items, detailed in the table above; none
touches shipped code behavior.

## 5. Coverage Detail

Changed source modules only (threshold 80%):

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
| **TOTAL (src/)** | **96.94%** | **80%** | **PASS** |

**Test quality (Pass D):** strong. Byte-for-byte manifest preservation is
asserted directly (`test_set.py:105`, `test_clear.py:52`); the shared fault
boundary is parametrized once across all three verbs
(`test_project_boundary.py`); channel discipline (stdout/stderr) is pinned per
mode; rich-markup injection via author text is covered (`test_show.py:64`); the
clock is a monkeypatched seam, not a frozen library. No assertion-free tests, no
mock-count-only assertions, no interdependence. TDD-order heuristic is
inconclusive (Spec Kit batches commits as "Implementation progress").

**Security (Pass D):** no `yaml.load`/`pickle`/`eval`/`shell=True` in the diff;
no hardcoded secrets (R4 is a terminal echo of a token *prefix* read from
`~/.pypirc`, not a committed secret). `validate --scope` containment uses
`resolve()` + `relative_to(root)` correctly. All file input crosses a Pydantic
boundary (`FocusBlock` with `extra="forbid", strict=True`; the TOML-native-date
normalizer keeps strictness without bricking hand-edits).

**Positives worth keeping:** the envelope consolidation (net deletion of
`graph/envelope.py`, `check`/`version` rerouted through `emit_json`) reduced
duplication while widening the contract's test coverage; `_project.py` extracts
the load-or-exit boundary exactly at the third caller, not before.

## 6. Inability-to-verify notes

- `pytest -m manual` (packaged-install / networked smoke) was not run — slow,
  networked, opt-in by design; CI history is the evidence for it.
- The TDD-order signal cannot be derived from this branch's commit granularity
  (Spec Kit auto-commits batch tests and implementation together).
- agentskills.io compliance of *generated* skills was verified indirectly (the
  generator and its `lint_skill_md` gate are untouched and their tests pass);
  no skill was re-materialized during this read-only audit.
