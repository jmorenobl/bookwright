# Quality Audit — 022-skills-status-integration

**Scope:** 8 in-scope source/test files (of 41 changed; remainder is Spec Kit `.agents`→`.claude` migration churn + governance docs)
**Commit range:** bd47ca4..1e78132
**Date:** 2026-06-12
**Conventions discovered:** `CLAUDE.md`, `AGENTS.md`, `.specify/memory/constitution.md` (v1.4.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 1 |
| **Total** | 3 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; full-suite total = 96.99%).
Other CI gates: `ruff check` PASS, `ruff format --check` PASS, `pytest` PASS (1176 passed, 1 skipped), **`mypy --strict` FAIL (2 errors)** → see R1.

## 2. Conventions Compliance Matrix

Rules extracted from the constitution (binding) and CLAUDE.md/AGENTS.md, checked 1-to-1 against the diff.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "CI MUST run pytest, ruff, and mypy strict on every push and pull request; a red bar blocks merge" | `.specify/memory/constitution.md:163` | io-contract | **FAIL** | `mypy --strict` reports 2 errors in `tests/integrations/test_status_injection.py` (R1). |
| "All four [pytest, ruff check, ruff format --check, mypy --strict] MUST pass before merge" | `.specify/memory/constitution.md:214` | workflow-step | **FAIL** | mypy red (R1); other three green. |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `.specify/memory/constitution.md:149` | coverage-threshold | PASS | Full suite total 96.99%; changed `materialize.py` 98.04%, `constants.py` 100%. |
| "No source file (production or test) may exceed 500 lines" | `.specify/memory/constitution.md:99` | module-size | PASS | `materialize.py` 216, `constants.py` 75, `test_status_injection.py` 72 lines. |
| "Writing to `.claude/commands/`, `.agents/commands/` ... is prohibited" | `.specify/memory/constitution.md:122` | directory-ban | PASS | Injection writes only into `SKILL.md` bodies; no `commands/` writes in diff. |
| "name < 64 chars and exactly matching the parent directory name; description < 1024 chars" | `.specify/memory/constitution.md:134` | frontmatter-constraint | PASS | Frontmatter logic unchanged; `name == filename stem` guard intact (materialize.py:179). |
| "Skill generation MUST fail loudly ... silent truncation or auto-fixing is forbidden" | `.specify/memory/constitution.md:138` | io-contract | PASS | `_transform_body` raises `SkillMaterializationError` on residual tokens; lint still runs post-write. |
| "Any CLI command ... MUST accept a `--json` flag and ... emit a single ... JSON document on stdout" | `.specify/memory/constitution.md:171` | io-contract | PASS | Injected instructions call `bookwright status --json`; no CLI surface changed here. |
| "Integrations MUST be implemented as subclasses of SkillsIntegration ... monolithic dispatcher explicitly forbidden" | `.specify/memory/constitution.md:108` | plugin-shape | PASS | New branch reads `integration.supports_dynamic_context` (a capability flag), not a type-switch ladder. |
| "Adding [a runtime dependency] requires a MINOR amendment" | `.specify/memory/constitution.md:206` | dependency | PASS | No dependency changes; `yaml`, `re`, `shutil` already in use. |
| "A PR that adds plumbing whose only justification is 'future X' MUST be rejected" | `.specify/memory/constitution.md:235` | scope-ban | PASS | All code serves iteration 022 FR-001..FR-008; no deferred/cancelled-feature plumbing. |
| "Agent Skills must trigger on both ES and EN author prompts" | `CLAUDE.md` (Language conventions) | other | PASS | Bilingual triggers preserved (test_preserves_bilingual_triggers); injection text is Spanish, consistent with Spanish command sources. |
| Spec Kit pipeline specify→clarify→plan→tasks→analyze→implement | `CLAUDE.md` (How work is done) | workflow-step | PASS | spec.md, plan.md, tasks.md, research.md, data-model.md, quickstart.md, checklists/ all present on branch. |
| Governance artifacts tracked by git (A.3) | derived | track-integrity | PASS | Working tree clean; all `specs/022-*` files appear in branch diff; no untracked/staged governance files. |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A/D | CRITICAL | tests/integrations/test_status_injection.py:18,25 | `mypy --strict` fails: `MockIntegration` overrides `supports_dynamic_context` (a `ClassVar[bool]`) with a read-only `@property`, and its `setup` signature is incompatible with the base — a red CI gate that blocks merge | Make `MockIntegration` match the `SkillsIntegration` contract: declare `supports_dynamic_context` as a class attribute and align `setup` to the base signature. |
| R2 | A | MEDIUM | specs/022-skills-status-integration/review.md; checklists/quality.md | The previously-committed audit declared "No CRITICAL or HIGH findings" while `mypy --strict` is in fact red — a stale governance artifact giving false assurance (it never ran mypy) | This run overwrites both files with the corrected verdict; run all four gates as part of the audit, not a coverage spot-check. |
| R3 | B | LOW | src/bookwright/integrations/materialize.py:81-85 | `_transform_body` idempotency is enforced by a substring `not in` guard, partially redundant with `generate_skill_md`'s SKILL.md-exists early return (line 172) | Acceptable as defense-in-depth; no change required. Noted for clarity. |

## 4. Remediation Detail

### R1 — mypy --strict fails on the new test's MockIntegration

- **Where:** `tests/integrations/test_status_injection.py:18` and `:25`
- **Why it matters:** The constitution makes `mypy --strict` one of four CI gates that **MUST pass before merge** (Technical Constraints, `.specify/memory/constitution.md:214`; Principle VIII, `:163`). The branch as committed (HEAD `1e78132`) is red:
  - `:18` — `Cannot override writeable attribute with read-only property [override]`: the base declares `supports_dynamic_context: ClassVar[bool] = False` (base.py:45), but `MockIntegration` re-declares it as a `@property`.
  - `:25` — `Signature of "setup" incompatible with supertype`: base is `setup(self, project_root: Path, manifest: Manifest, parsed_options=..., *, ledger=...) -> None`; the mock is `setup(self, repo_root: Path, manifest: Any) -> None`.
- **Suggested change:** In `MockIntegration`, drop the `@property` and the `__init__`/`_dynamic` indirection — define two tiny module-level subclasses (one with `supports_dynamic_context = True`, one `False`) or assign the class attribute, and widen `setup` to `def setup(self, project_root: Path, manifest: Any, parsed_options: Any = None, *, ledger: Any = None) -> None`. The test only needs the flag value and a no-op `setup`; matching the supertype signature clears both errors.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/integrations/constants.py | 100.00% | 80% | PASS |
| src/bookwright/integrations/materialize.py | 98.04% | 80% | PASS |
| **Full suite total** | 96.99% | 80% | PASS |

## 6. Inability-to-verify notes

- None. All four CI gates were executed locally: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest` (full suite with coverage).
- Deleted test blocks (`test_no_branching_on_capability_flags`, `test_claude_and_generic_bodies_are_identical`, `test_no_generated_body_contains_injection_syntax`) asserted the iteration-9 FR-011 invariant ("capability flags are pure metadata; no `!`…` injection"). Iteration 022 intentionally reverses that invariant (FR-004/FR-005), so the removals are correct — **not** a finding. FR-011 was an iteration-level requirement, not a § 16 design axiom, so reversing it does not trip Principle X.
