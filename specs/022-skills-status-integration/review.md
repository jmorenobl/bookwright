# Quality Audit — 022-skills-status-integration

**Scope:** 11 changed source/test files (of 47 total changed; the rest are Spec Kit infra + specs artifacts) vs `main`
**Commit range:** main..060e2e7
**Date:** 2026-06-12
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `AGENTS.md`

> Re-audit superseding the `a44f6e6` run. The three MEDIUM findings from that pass
> are resolved: R2 (CLAUDE.md Spec Kit pin drift) and R4 (AGENTS.md skills path) by
> commit `a9c1e46`; R3 (untested FR-003 focus handoff) by `060e2e7`, which adds
> `test_phase_transition_skills_carry_focus_handoff` and
> `test_only_phase_transition_skills_carry_focus_handoff`. R1 (scope bundling of
> Spec Kit tooling into the feature branch) is now explained in §6, not re-flagged.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 2 |
| **Total** | 2 |

Coverage gate: **PASS** (0 changed modules below threshold, threshold = 80%). Both changed source modules at 100% line+branch coverage. Full integrations suite: 159 passed. `ruff check`, `ruff format --check` clean; both modules well under the 500-line cap (constants 86, materialize 220).

The iteration is clean. The design choice to inject the status-orientation and next-steps blocks **at materialization time** (`_transform_body`) rather than hand-editing all 12 source `.md` files is the DRY-correct approach: FR-001/FR-002 are satisfied for the whole roster by one code path, the FR-003 focus handoff is the only thing hardcoded into source `.md` (exactly bible + outline, pinned by test), and idempotency is enforced two ways (skill-dir skip in `generate_skill_md`, heading-sentinel guard in `_transform_body`).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden" | `constitution.md:59` | layout | PASS | Diff is `.py` + `.md` only; no binary artifacts |
| "The implementation language is Python 3.11+ … additional runtime dependency requires an amendment" | `constitution.md:74` | dependency | N/A | No `pyproject.toml`/dependency change in diff |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`." | `constitution.md:86` | layout | PASS | Source under `src/bookwright/integrations/` + `resources/commands/`; tests under `tests/integrations/` |
| "Each CLI subcommand … its own module … No source file … may exceed 500 lines" | `constitution.md:97` | module-size | PASS | constants.py 86, materialize.py 220; no new CLI verb added |
| "Integrations MUST be … subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`" | `constitution.md:108` | plugin-shape | PASS | No new dispatcher; injection keyed on `integration.supports_dynamic_context` bool, no name ladder |
| "A monolithic `AGENT_CONFIG`-style dispatcher is explicitly forbidden" | `constitution.md:111` | plugin-shape | PASS | `_transform_body` branches on a capability bool, not integration names |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" | `constitution.md:121` | directory-ban | PASS | Materializer writes `<skills_dir>/<name>/SKILL.md`; `resources/commands/` is packaged *source* input, not an emitted legacy dir |
| "name < 64 characters and exactly matching the parent directory name; description < 1024 characters" | `constitution.md:133` | frontmatter-constraint | PASS | `_render_frontmatter` sets name=stem; `name_frontmatter_mismatch` guard + `lint_skill_md` re-enforce; all 12 sources lint-pass in tests |
| "Skill generation MUST fail loudly … silent truncation or auto-fixing is forbidden" | `constitution.md:139` | io-contract | PASS | `residual_token`/`dangling_reference`/`name_frontmatter_mismatch` raise pre-write; lint failure rolls back dir |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:149` | coverage-threshold | PASS | Both changed modules 100%; 159 integration tests green |
| "Any CLI command … consumed by an AI agent MUST accept a `--json` flag … single … JSON document on stdout" | `constitution.md:170` | io-contract | N/A | No CLI command changed; injected text invokes the iter-020 `bookwright status --json`, unchanged here |
| "preset / genre-package system … MUST NOT be implemented at all" | `constitution.md:229` | scope-ban | PASS | No preset/genre plumbing in diff |
| "any integration beyond `claude` and `generic` … MUST NOT be implemented" | `constitution.md:230` | scope-ban | PASS | Only claude/generic variants; `.specify/integrations/agy.manifest.json` is Spec Kit's own config, not a bookwright integration |
| "introduces … plumbing whose only justification is 'future X', MUST be rejected" | `constitution.md:235` | scope-ban | PASS | No deferred-feature plumbing; E2E fixture/docs/release correctly deferred to iter 023 per spec Out-of-Scope |
| Workflow `/speckit-specify → clarify → plan → tasks → analyze → implement` | `CLAUDE.md` (How work is done) | workflow-step | PASS | spec.md (+ Clarifications §), plan.md, tasks.md, analysis report (commit cb2e80f), checklists/requirements.md, source all present |
| "Agent Skills must trigger on both ES and EN author prompts" | `CLAUDE.md` (Language conventions) | other | PASS | `test_preserves_bilingual_triggers` pins trigger preservation; injection prose ES, consistent with existing skill bodies |
| Source code/identifiers/commits in English; design prose in Spanish | `CLAUDE.md` (Language conventions) | other | PASS | Python identifiers + docstrings English; injected author-facing prose Spanish (matches command `.md` bodies) |

Track integrity (A.3): all `specs/022-…/` artifacts and changed source appear in `git diff main...HEAD`; working tree clean (no uncommitted/untracked governance files). **OK.**

Workflow trail (A.4): walked in reverse — implement (source ✅) ← analyze (report commit cb2e80f ✅) ← tasks.md ✅ ← plan.md ✅ ← clarify (spec Clarifications §, 2 Q&A ✅) ← specify (spec.md ✅). No gap. **OK.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | LOW | src/bookwright/integrations/constants.py:1 | File-wide `# ruff: noqa: E501` disables line-length for the whole module, not just the long Spanish prose constants | Acceptable given the prose strings; if future executable code lands here, scope the noqa to the offending lines instead |
| R2 | B | LOW | src/bookwright/integrations/materialize.py:86-90 | Idempotency gates on the literal headings `## Orientación inicial` / `## Próximos pasos`; an author who writes either heading as real content in a source body would silently suppress injection | Author-controlled and very low risk; if it ever matters, gate on a dedicated HTML-comment sentinel rather than a visible heading |

## 4. Remediation Detail

No CRITICAL or HIGH findings — nothing requires remediation before merge. The two LOW items above are notes, not blockers.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/integrations/constants.py | 100.00% (14/14 stmts, 0 branches) | 80% | PASS |
| src/bookwright/integrations/materialize.py | 100.00% (80/80 stmts, 22/22 branches) | 80% | PASS |

(Whole-repo `fail_under` is single-sourced in `[tool.coverage.report]`; CI's full-suite run enforces the 80% gate — not re-measured here since the audit ran the `tests/integrations/` subset.)

## 6. Inability-to-verify notes

- Whole-repo coverage gate not re-measured (audit scoped to `tests/integrations/`); the changed modules are the only source delta and both hit 100%, so the gate cannot regress from this diff. CI runs the full suite.
- `mypy --strict` not re-run in this audit; the modules use explicit `Final[...]` annotations and typed signatures consistent with the strict-mode house style (see the stub note at `test_status_injection.py:21`).
- The 36 non-code changed files (`.claude/skills/speckit-*`, `.specify/` scripts/manifests, specs artifacts) are out of audit scope: per CLAUDE.md, Spec Kit *core* is not hand-modified and these reflect the pinned-version upgrade (0.10.1→0.10.2) + the agy→claude integration switch, both already landed in commits a44f6e6 / a9c1e46 / 1e78132. This is the prior R1 "scope bundling" observation — noted, not re-flagged.
