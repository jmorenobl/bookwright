# Quality Audit — 022-skills-status-integration

**Scope:** 5 in-scope changed files (2 source modules, 1 resource pair, 4 test files) vs `main`
**Commit range:** `main`..`218e866`
**Date:** 2026-06-12
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0), `AGENTS.md`, `bookwright-design.md` (referenced)

> Supersedes the prior audit at `1e78132`. Its sole finding (R1 — `mypy --strict`
> failure on `MockIntegration`'s property/`setup` override) is **resolved**: the
> current `MockIntegration` sets `supports_dynamic_context` as a class attribute and
> overrides `setup` with the base signature; `mypy --strict` now passes on all three
> changed source files (verified this run).

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 3 |
| **Total** | 6 |

Coverage gate: PASS for changed modules (`materialize.py` 98.04%, `constants.py` 100%, threshold = 80%). Full-suite repo coverage gate (80% over all of `src/`) is enforced by CI and was not re-measured here — only `tests/integrations/` was run (its 18.17% repo-wide total is an artifact of that scoping, not a real figure).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Plain Text as Source of Truth … Binary stores … are forbidden as canonical storage" | `.specify/memory/constitution.md:59` | layout | PASS | Diff is Markdown/Python only; no binary artifacts |
| "Introducing an additional runtime dependency requires an amendment" | `.specify/memory/constitution.md:78` | dependency | PASS | No deps added; only `integrations/` + `resources/commands/` + tests edited |
| "All production code MUST live under `src/bookwright/`" / "tests MUST live under `tests/`" | `.specify/memory/constitution.md:86` | layout | PASS | `constants.py`/`materialize.py` under `src/`; new tests under `tests/integrations/` |
| "No source file (production or test) may exceed 500 lines" | `.specify/memory/constitution.md:99` | module-size | PASS | materialize.py 216, constants.py 74, test_status_injection.py 84 |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`" | `.specify/memory/constitution.md:108` | plugin-shape | PASS | Injection switch uses `integration.supports_dynamic_context`; no new dispatcher |
| "Bookwright MUST emit Agent Skills … nothing else … Writing to `.claude/commands/` … prohibited" | `.specify/memory/constitution.md:121` | directory-ban | PASS | Injection only mutates `SKILL.md` body; no command-dir writes |
| "name < 64 chars … description < 1024 … fail loudly when a generated skill would violate" | `.specify/memory/constitution.md:133` | frontmatter-constraint | PASS | `lint_skill_md` runs post-write on every materialized skill; injected `!`bookwright …`` passes Rule 5 (argv[0]=="bookwright") |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `.specify/memory/constitution.md:149` | coverage-threshold | PASS* | Changed modules ≥98%; repo-wide gate deferred to CI (not run here) |
| "Mixing JSON and human prose on stdout is a contract violation" | `.specify/memory/constitution.md:174` | io-contract | N/A | No CLI command output changed this iteration |
| "PR that introduces … plumbing whose only justification is 'future X' MUST be rejected" | `.specify/memory/constitution.md:235` | scope-ban | PASS | No vector-search/export/preset plumbing introduced |
| "Agent Skills must trigger on both ES and EN author prompts" | `CLAUDE.md` (Language conventions) | frontmatter-constraint | PASS | Injection touches body only; bilingual descriptions/triggers preserved (`test_preserves_bilingual_triggers`) |
| Spec Kit workflow: specify→clarify→plan→tasks→analyze→implement | `CLAUDE.md` (How work is done) | workflow-step | PASS | spec.md, Clarifications §, plan.md, tasks.md, research.md, data-model.md, checklists/ all present on branch |
| FR-003: phase-transition skills MUST update focus "using `bookwright focus set`" | `specs/.../spec.md:76` | io-contract | **FAIL** | bible.md:63 / outline.md:47 call `bookwright focus set "…"` (positional) but the CLI requires `--target` — see R1 |

`*` Changed-module coverage verified; repo-wide 80% gate is CI-enforced and not re-run in this read-only audit.

**Track integrity (A.3):** all `specs/022-skills-status-integration/` artifacts appear in `git diff main...HEAD`; working tree is clean (`git status --porcelain` empty). PASS — no uncommitted/untracked governance files.

**Workflow trail (A.4):** specify→spec.md ✓, clarify→Clarifications block (spec.md:11-16) ✓, plan→plan.md ✓, tasks→tasks.md ✓, analyze→checklists/ + prior review.md ✓, implement→source under `src/` ✓. No broken trail.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | CRITICAL | src/bookwright/resources/commands/bookwright-bible.md:63; bookwright-outline.md:47 | Hardcoded phase-transition command `bookwright focus set "<text>"` uses a positional arg, but `focus set` requires the `--target` option — the command always fails | Change both to `bookwright focus set --target "<text>"` |
| R2 | D | MEDIUM | tests/integrations/test_status_injection.py | tasks.md T005 (marked [X]) claims a test for inert-when-empty behavior (case d); no such assertion exists — only 4 tests present | Add a test asserting the injected text instructs inert/continue-normally behavior, or amend T005's claim |
| R3 | D | MEDIUM | tests/integrations/test_status_injection.py:65-76 | `test_idempotency` exercises a path the production entry point never reaches (`generate_skill_md` short-circuits on existing SKILL.md), feeding an already-transformed body back into `_transform_body` | Also assert idempotency at the real seam: re-running `generate_skill_md` over an existing skill is a no-op |
| R4 | B | LOW | src/bookwright/integrations/constants.py:41-74 | Multi-line Spanish content templates added to a module documented as "compliance constants (numeric caps, license, injection allowlist)"; mixes content with the compliance-constant role | Optionally split into `injection_templates.py`, or widen the module docstring to own the new responsibility |
| R5 | A | LOW | src/bookwright/integrations/constants.py:43,57 | Injected heading `## 1. Orientación inicial` adds a "1." that the rest of each command body does not continue (body sections are unnumbered) — inconsistent numbering | Drop the `1.` (`## Orientación inicial`) to match the unnumbered body style |
| R6 | A | LOW | (whole branch) .claude/skills/speckit-*, .specify/*, AGENTS.md, CLAUDE.md | Branch bundles a Spec Kit integration-switch regen (commit 1e78132) unrelated to the iteration's stated scope | Cosmetic — note in the PR description that these are the `chore(specify)` regen, not iteration-022 code |

## 4. Remediation Detail

### R1 — Phase-transition focus command uses an unsupported positional argument

- **Where:** [bookwright-bible.md:63](src/bookwright/resources/commands/bookwright-bible.md#L63), [bookwright-outline.md:47](src/bookwright/resources/commands/bookwright-outline.md#L47)
- **Why it matters:** FR-003 (a spec MUST) requires the two designated phase-transition skills to update the focus "using `bookwright focus set`". The CLI signature is `target: str = typer.Option(..., "--target", …)` ([set_.py:32](src/bookwright/commands/focus/set_.py#L32)) — `--target` is a *required option*, and there is no positional parameter. The instruction `bookwright focus set "Estructurar el outline narrativo"` fails Typer parsing every time (missing required `--target`, plus an unexpected extra argument). An author following the bible/outline skill verbatim at the end of a phase hits an error on the one command the iteration added. The spec's edge case ("focus update fails → warn, don't crash") covers *runtime* failures (e.g. no project), not a command that is syntactically incapable of succeeding. No test exercises the materialized instruction, so CI did not catch it.
- **Suggested change:** in both files, insert `--target`:
  - Bible:63 → `bookwright focus set --target "Estructurar el outline narrativo"`
  - Outline:47 → `bookwright focus set --target "Desglose de escenas a partir del outline"`
  Consider adding a test that materializes these two skills and asserts the focus line matches the real CLI grammar.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/integrations/materialize.py | 98.04% | 80% | PASS |
| src/bookwright/integrations/constants.py | 100% (constants) | 80% | PASS |
| (repo-wide src/bookwright) | not measured here | 80% | DEFERRED to CI |

## 6. Inability-to-verify notes

- Repo-wide coverage was not measured: this audit ran only `tests/integrations/` (read-only), so the 18.17% total reported by that scoped run is meaningless for the repo gate. The full `uv run pytest` gate is CI-enforced.
- R1's failure mode is asserted from the CLI signature, not by executing the materialized skill (skills are LLM-consumed Markdown, not run by the test suite). The Typer required-option behavior is standard and deterministic.
