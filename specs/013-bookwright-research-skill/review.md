# Quality Audit — 013-bookwright-research-skill

**Scope:** 41 changed files vs `main` (10 source/test/config files in audit scope; 12 spec artifacts)
**Commit range:** `main`..`77a9f9c`
**Date:** 2026-06-04
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.3.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 0 |
| LOW | 1 |
| **Total** | 2 |

Coverage gate: **PASS** (0 changed modules below threshold, threshold = 80%). Suite: 992 passed, 1 skipped; total line coverage 96.51%. New production modules — `core/_research_block.py` 100%, `integrations/descriptions.py` 100%, `core/manifest.py` 100%; `io/research.py` 96.73% (on `main`, exercised by the new rich-fixture tests).

This is a high-quality, low-debt branch. The feature is almost entirely **data** (Markdown source command, packaged templates, scaffold, one TOML block) consumed by machinery already on `main`; the only new production Python is a 56-line Pydantic block plus two wiring lines. The single material finding is a **pre-existing** module-size violation that this branch touched (and marginally grew) rather than fixed.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle … Binary stores … forbidden as canonical storage" | `constitution.md:57-64` | layout | PASS | All new artifacts are .md / .toml / .tmpl; graph stays a derived cache |
| "Introducing an additional runtime dependency requires an amendment" | `constitution.md:70-78` | dependency | PASS | `git diff main…HEAD -- pyproject.toml uv.lock` empty — no dep change |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:82-87` | layout | PASS | New prod code under `src/bookwright/core/`, `…/integrations/`; tests under `tests/` |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:94-99` | module-size | **FAIL** | `core/manifest.py` = 537 lines (R1). New `_research_block.py` = 56 ✓ |
| "Each CLI subcommand MUST live in its own module … No new CLI verb" implied | `constitution.md:94-99` | layout | PASS | No change under `cli.py` / `commands/`; feature adds no verb |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY` … exactly two entries" | `constitution.md:104-111` | plugin-shape | PASS | Reuses iter-9 materializer; no new integration, no dispatcher ladder |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/`, `.agents/commands/` … is prohibited" | `constitution.md:117-122` | directory-ban | PASS | No write/reference to `*/commands/` (skills `commands/` dir is the source roster, not output) |
| "`name` < 64 characters and exactly matching the parent directory name; `description` < 1024" | `constitution.md:129-139` | frontmatter-constraint | PASS | name `bookwright-research` = 19 chars == stem; description 747 chars; `lint_skill_md` green (both integrations) |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:145-162` | coverage-threshold | PASS | 96.51% total; every changed module ≥ 96.73% |
| "CI MUST run pytest, ruff, and mypy strict … a red bar blocks merge" | `constitution.md:161-162` | workflow-step | PASS | pytest green; mypy `# type: ignore` accounted (see R2) |
| "Any CLI command … MUST accept a `--json` flag and … emit a single well-formed JSON document on stdout" | `constitution.md:167-178` | io-contract | PASS | No CLI output path changed; skill's final step calls existing `graph build --json` |
| "Section 16 axioms … MUST NOT be reopened … ontology frozen" | `constitution.md:180-193` | scope-ban | PASS | No new GOLEM class; `bw:` provenance vocab lives in `sources.ttl`, outside `CLASS_IRI` |
| "Preset system … MUST NOT be pulled into v0 scope … plumbing whose only justification is 'future'" | `constitution.md:214-230` | scope-ban | PASS | `factual_anchor` validator, `bookwright-verify`, vector search all absent; template layering reuses iter-7 resolver |
| Workflow `specify → clarify → plan → tasks → analyze → implement` | `CLAUDE.md` | track-integrity / workflow-step | PASS | spec.md, plan.md, tasks.md, contracts/, data-model.md, research.md, quickstart.md, checklists/requirements.md all present & tracked; git log shows analyze-remediation commit; tree clean |

**A.3 Track-integrity** — every file under `specs/013-bookwright-research-skill/` appears in the branch diff; `git status` clean; no untracked/staged-only governance artifact. PASS.

**A.4 Workflow-trail** — no downstream artifact exists ahead of a missing upstream one. PASS.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | HIGH | src/bookwright/core/manifest.py:1-537 | File is 537 lines, over the Principle IV 500-line MUST ceiling; this branch added 2 lines (import + `research` field) to an already-over file (535 on `main`) instead of decomposing it | Extract a cohesive slice (block models → `core/_blocks.py`, or the version helpers → `core/_version.py`) to bring it well under 500 |
| R2 | D | LOW | tests/commands/graph/conftest.py:155-156 | `project_factory` takes `**kwargs: object` then `# type: ignore[arg-type]` to splat into `scaffold_project`, defeating mypy at the one call that varies fixtures | Type the factory with a `TypedDict`/`Unpack` or an explicit keyword signature so the `type: ignore` can drop |

## 4. Remediation Detail

### R1 — `core/manifest.py` exceeds the 500-line module ceiling

- **Where:** `src/bookwright/core/manifest.py` (537 lines).
- **Why it matters:** Principle IV (`constitution.md:94-99`) is a binding MUST: "No source file (production or test) may exceed 500 lines; a file approaching the limit MUST be decomposed **before** the limit is reached, not after." The file was already at 535 on `main`, so the limit was breached before this iteration — but this branch *edited* the file (adding the `_research_block` import and the `research: ResearchBlock` field) and left it non-compliant. The plan was aware ("manifest.py is already 535 lines") and correctly put the new class in a separate 56-line module; the robust completion of that instinct is to also relieve the host file, not nudge it further over. Leaving it is exactly the "carry the debt forward" pattern the audit guards against — every future edit to this module starts already in violation.
- **Suggested change:** the module has two clean, low-risk extraction seams that need no behavior change:
  - **Block models** (`BookwrightBlock`, `BookBlock`, `VocabulariesBlock`, `ValidatorsBlock`, `IntegrationBlock`, `PathsBlock`, lines ~132-319, ≈190 lines) → `core/_blocks.py`, imported by `manifest.py` exactly as `_research_block.ResearchBlock` already is. This drops `manifest.py` to ≈350 lines and matches the established "extract to `_*.py`, re-export from `__init__`" pattern (`_build.py`, `_translate.py`, `_research_block.py`).
  - Alternatively the `manifest_version` helpers (`_parse_manifest_version`, `_classify_manifest_version`, `_classify_manifest_version_warnings`, lines ~81-129, ≈50 lines) → `core/_version.py`. Smaller, but only buys ~10 lines of headroom — prefer the block-model extraction.
  Keep the public surface (`bookwright.core` re-exports) byte-identical so no caller or test changes.

### R2 — `project_factory` erases its own type contract

- **Where:** `tests/commands/graph/conftest.py:155-156`.
- **Why it matters:** the factory accepts `**kwargs: object` and then `scaffold_project(tmp_path / "my-novel", **kwargs)  # type: ignore[arg-type]`. mypy `--strict` is a CI gate (Principle VIII); the `type: ignore` is a local hole that lets a mis-typed `research="rich"` typo or a wrong `with_bible` value through unchecked at the most-varied test entry point. Low severity (test infra, not shipped behavior), but it is avoidable debt.
- **Suggested change:** declare a `class _ScaffoldKwargs(TypedDict, total=False)` mirroring `scaffold_project`'s keyword params and type the factory `Callable[[Unpack[_ScaffoldKwargs]], Path]` (or just give `_make` the same explicit keyword signature as `scaffold_project`). The `# type: ignore` then drops and mypy checks the call sites.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/core/_research_block.py | 100.00% | 80% | PASS |
| src/bookwright/core/manifest.py | 100.00% | 80% | PASS |
| src/bookwright/integrations/descriptions.py | 100.00% | 80% | PASS |
| src/bookwright/io/research.py (on `main`, re-exercised) | 96.73% | 80% | PASS |
| **Whole package** | **96.51%** | 80% | PASS |

## 6. Inability-to-verify notes

- `ruff check` / `ruff format --check` / `mypy --strict` were not re-run inside this audit (read-only pass); the suite (`pytest`) passed clean and CI runs all four on push. The R2 `type: ignore` is the only mypy-relevant item spotted by reading.
- Skill *runtime* behavior (the agent actually searching, quoting in original language, leaving open questions) is LLM-driven and not unit-testable; it is verified structurally — `test_research_skill.py` proves materialization + `lint_skill_md` for both integrations and that `bookwright graph build --json` survives into the body, and `test_research_format.py` proves the documented contract is exactly what `map_research()` parses. This is the constitutionally-sanctioned verification split for authoring skills (Principle VIII, v1.3.0).
