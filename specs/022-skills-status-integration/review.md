# Quality Audit — 022-skills-status-integration

**Scope:** 47 changed files vs `main` (feature code: 4 source/resource files + 4 test files; remainder is Spec Kit tooling, specs, and agent-context docs)
**Commit range:** `main`..`a44f6e6`
**Date:** 2026-06-12
**Conventions discovered:** `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.specify/memory/constitution.md` (v1.4.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
| LOW | 1 |
| **Total** | 4 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; total line coverage 97.03%, `materialize.py` 100%, `descriptions.py` 100%). 1177 passed, 1 skipped, 1 deselected.

The feature itself is clean: the injection logic in `materialize.py` and the
constants in `constants.py` are well-factored (a single shared
`_STATUS_INJECTION_TEMPLATE` keeps the Claude/Generic variants in sync by
construction), idempotency gates on stable heading sentinels, the FR-013
injection allowlist is respected (the materialized `!`bookwright status --json``
passes `lint_skill_md`), `yaml.safe_dump` is used (no unsafe deserialization),
and every write stays inside `target_dir` (containment-tested). No
CRITICAL/HIGH findings. All four MEDIUM/LOW items concern scope hygiene and
documentation consistency around tooling changes bundled into this branch, plus
one untested MUST.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Bookwright MUST emit Agent Skills (`<skills_dir>/<name>/SKILL.md`) and nothing else." | `.specify/memory/constitution.md:121` (VI) | directory-ban | PASS | `generate_skill_md` writes only `<target>/<name>/SKILL.md` + `references/`; no `commands/` write in diff |
| "name < 64 characters and exactly matching the parent directory name; description < 1024 characters" | `.specify/memory/constitution.md:134` (VII) | frontmatter-constraint | PASS | `name==stem` enforced (materialize.py:184-190); injection touches body only; all 12 sources lint-pass |
| "Long reference material MUST be offloaded to references/ … keep the SKILL.md body within the standard's working budget" | `.specify/memory/constitution.md:138` (VII) | frontmatter-constraint | PASS | `SKILL_BODY_MAX_TOKENS=5000` re-checked by lint; all 12 materialize green incl. the injected blocks |
| "Skill generation MUST fail loudly … silent truncation or auto-fixing is forbidden." | `.specify/memory/constitution.md:139` (VII) | io-contract | PASS | `_transform_body` raises `SkillMaterializationError(residual_token)` instead of asserting (materialize.py:92-98) |
| "Integrations MUST be implemented as subclasses of SkillsIntegration registered in INTEGRATION_REGISTRY … monolithic dispatcher forbidden" | `.specify/memory/constitution.md:108` (V) | plugin-shape | PASS | Capability driven by `supports_dynamic_context` ClassVar on base (base.py:45); no if/elif over integration keys |
| "v0 MUST hold a minimum of 80% line coverage across src/bookwright/" | `.specify/memory/constitution.md:149` (VIII) | coverage-threshold | PASS | 97.03% total; changed modules at 100% |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST accept a --json flag … single well-formed JSON document on stdout" | `.specify/memory/constitution.md:171` (IX) | io-contract | N/A | No CLI command changed; iteration injects skill content, does not alter `status`/`focus` |
| "All production code MUST live under src/bookwright/ … No test may live alongside production code." | `.specify/memory/constitution.md:86` (III) | layout | PASS | New code under `src/bookwright/integrations/`; tests under `tests/integrations/` |
| "No source file (production or test) may exceed 500 lines" | `.specify/memory/constitution.md:99` (IV) | module-size | PASS | Largest changed file `constants.py` 87 lines; `materialize.py` 221 |
| "Runtime dependencies (minimum set): jinja2, packaging … Adding to this list requires a MINOR amendment" | `.specify/memory/constitution.md:204` (II) | dependency | PASS | No dependency added; `pyyaml` already in the set |
| "A PR that introduces … plumbing whose only justification is 'future X' MUST be rejected." | `.specify/memory/constitution.md:235` | scope-ban | PASS | No vector/Grafeo/preset/export plumbing; injection serves the shipped `status` command |
| "Pinned at v0.10.1 … Don't upgrade without a reason worth chasing template churn." | `CLAUDE.md:252` | workflow-step | FAIL | Branch upgraded Spec Kit 0.10.1 → 0.10.2 (`.specify/integration.json`) with no stated reason and without updating the pin line → see R1, R2 |
| "Don't modify Spec Kit core (templates, scripts, manifests). Per-project copies … are editable." | `CLAUDE.md:253-254` | scope-ban | PASS | `.specify/scripts/bash/*.sh` show 0 line changes; manifest/integration JSON changes are the per-project upgrade/switch, not hand edits |
| Fixed workflow `/speckit-specify → clarify → plan → tasks → analyze → implement` | `CLAUDE.md` "How work is done here" | workflow-step | PASS | spec.md, Clarifications §, plan.md, tasks.md, analysis commit (cb2e80f), source all present; A.4 below |
| Governance artifacts committed (track integrity) | derived | track-integrity | PASS | `git status` clean; all `specs/022-*` files in branch diff; A.3 below |

### A.3 Track-integrity

`git status --porcelain` is empty and every `specs/022-skills-status-integration/`
artifact appears in `git diff main...HEAD --name-only`. No uncommitted or
untracked governance file. **PASS.**

### A.4 Workflow-trail integrity

Walking the Spec Kit pipeline in reverse: source code ✅ (implement),
analysis report committed at `cb2e80f` ✅ (analyze), `tasks.md` ✅ (20/20 tasks
`[X]`, 0 open), `plan.md` ✅, `spec.md` Clarifications § with two recorded
answers ✅ (clarify), `spec.md` ✅ (specify). No downstream artifact exists
ahead of a missing upstream one. **PASS.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | MEDIUM | .specify/integration.json:1 | Spec Kit upgrade 0.10.1→0.10.2 + integration switch `agy`→`claude` bundled into feature branch 022, unrelated to its scope | Land tooling bumps in a dedicated `chore` branch, not inside a feature iteration; keeps the feature diff reviewable |
| R2 | A | MEDIUM | CLAUDE.md:252 | Pin line still reads "Pinned at `v0.10.1`" while the branch shipped 0.10.2 — doc/config drift | Update the pin note to v0.10.2 with the one-line reason for the bump (CLAUDE.md requires a stated reason) |
| R3 | D | MEDIUM | tests/integrations/test_materialize.py | FR-003 (MUST) — no test asserts the materialized `bookwright-bible`/`bookwright-outline` bodies carry the hardcoded `bookwright focus set` instruction | Add a focused test asserting both source bodies (and their materialized output) contain `bookwright focus set --target` |
| R4 | A | LOW | AGENTS.md:39 | AGENTS.md points readers to `.agents/skills/speckit-*` but the active integration is now `claude`, so the speckit skills live in `.claude/skills/` | Either regenerate AGENTS.md for the current integration or note both locations |

## 4. Remediation Detail

### R1 — Spec Kit upgrade + integration switch bundled into the feature branch

- **Where:** `.specify/integration.json:1`, commits `a44f6e6` (0.10.1→0.10.2) and `1e78132` (agy→claude)
- **Why it matters:** Constitution "Scope & Release Discipline" and CLAUDE.md both push every change through its proper channel: features land via numbered iterations, tooling churn is housekeeping. Folding a Spec Kit version bump and an integration switch (which moved all 15 `speckit-*` skills `.agents/ → .claude/` and rewrote 7 `.specify/` config files) into iteration 022 inflates the diff from ~8 feature files to 47 and makes the feature hard to review in isolation. The `.specify/scripts/bash/*.sh` files show 0 content changes, so this is config/manifest churn rather than core edits — but it still doesn't belong here.
- **Suggested change:** No code edit. For future iterations, run tooling upgrades on a separate `chore(specify)` branch merged independently. This is advisory; the changes themselves are benign and reversible.

### R2 — CLAUDE.md Spec Kit pin not updated to match the shipped version

- **Where:** `CLAUDE.md:252`
- **Why it matters:** CLAUDE.md is the binding convention file and explicitly states the pin: "Pinned at `v0.10.1` … Don't upgrade without a reason worth chasing template churn." The branch upgraded to 0.10.2 (`.specify/integration.json`) but left the pin line and its rationale untouched, so the convention file now contradicts the actual tooling state. The next contributor reading CLAUDE.md will believe the project is on 0.10.1.
- **Suggested change:** Update CLAUDE.md:252 to `Pinned at v0.10.2 (upgraded from v0.10.1 on 2026-06-12)` and append the one-line reason the upgrade was worth the churn. (Editing CLAUDE.md is permitted — it is a convention file, not source.)

### R3 — FR-003 (MUST) lacks an asserting test

- **Where:** `tests/integrations/test_materialize.py` (no coverage), implemented at `src/bookwright/resources/commands/bookwright-bible.md:60-63` and `bookwright-outline.md:44-47`
- **Why it matters:** FR-003 is a MUST: "the designated phase-transition skills are exactly `bookwright-bible` and `bookwright-outline`" and they "MUST include a hardcoded instruction to update the focus using `bookwright focus set`." The instruction is present in both source bodies, but no test pins it — a future edit that drops or renames the line (e.g. during a re-materialization refactor) would pass CI silently. The existing `focus set` test references in `tests/status/` and `tests/commands/` cover the `status`/`focus` layers, not the skill content. Note this is instructional Markdown, not executable code, so the value is regression-pinning, not behavior verification.
- **Suggested change:** Add a parametrized test over `{bookwright-bible, bookwright-outline}` asserting the source body (and the `generate_skill_md` output) contains `bookwright focus set --target`, and a complementary assertion that the other 10 sources do **not** (pins the "exactly these two" half of FR-003).

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/integrations/materialize.py | 100.00% | 80% | PASS |
| src/bookwright/integrations/constants.py | 100.00% (constants; exercised via materialize/injection tests) | 80% | PASS |
| src/bookwright/integrations/descriptions.py | 100.00% | 80% | PASS |
| src/bookwright/integrations/lint.py | 97.22% | 80% | PASS |
| **TOTAL (src/bookwright)** | **97.03%** | 80% | PASS |

## 6. Inability-to-verify notes

- The Spec Kit `analyze` artifact is referenced by commit `cb2e80f` ("[Spec Kit] Add analysis report") but no standalone analysis file remains in `specs/022-skills-status-integration/`; the workflow-trail check (A.4) relied on the commit and on `tasks.md` being fully closed rather than on a persisted report file.
- R3 is content-regression risk, not a behavioral gap: skills are LLM-consumed Markdown, so "the agent actually runs `focus set`" cannot be unit-tested — only the presence of the instruction can be.
