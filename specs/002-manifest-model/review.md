# Quality Audit — 002-manifest-model

**Scope:** 17 changed files on disk (4 modified + 13 new across `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`) vs `main`
**Commit range:** `main` → `a3db7f1` (3 commits, all spec/docs)
**Date:** 2026-05-28
**Conventions discovered:** `.specify/memory/constitution.md` v1.1.0 (binding), `CLAUDE.md` (project), `specs/002-manifest-model/{spec,plan,tasks,research,data-model,quickstart}.md`, `specs/002-manifest-model/contracts/manifest_api.md`
**Frame from user:** "esta spec no se puede cerrar con deuda técnica. Hay que cancelarla toda." — strict no-debt close.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 3 |
| HIGH | 2 |
| MEDIUM | 5 |
| LOW | 3 |
| **Total** | 13 |

Coverage gate: **PASS** when measured by the configured CI gate (`uv run pytest` → 93.91 % total, `bookwright.core/manifest.py` 94 %, `errors.py` 96 %, threshold = 80 %). Constitution Principle VIII is met *at the artefact level*, but see R1: none of this state is on the branch yet.

**Headline:** every functional acceptance criterion from `spec.md` is satisfied in the working tree, the CI gates (pytest, ruff, ruff format, mypy --strict) are all green locally — **but the entire iteration's work product is uncommitted**. `git diff main...HEAD` shows only spec/plan/tasks/analyze documents; the 13 implementation and test files exist only in the working tree, and 4 governance-relevant files (`constitution.md` amendment, `pyproject.toml` dep bump, `uv.lock`, `tasks.md` checkbox flips) are modified but unstaged. Combined with R2 (`manifest.py` = 562 lines, breaking the 500-line MUST in Principle IV), the iteration cannot close under the user's no-debt frame.

## 2. Conventions Compliance Matrix

Rules extracted in A.1 from the discovered convention files. Every MUST is checked positively; `PASS` here is as load-bearing as `FAIL`.

### `.specify/memory/constitution.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden as canonical storage." | constitution.md §I | layout | PASS | All new artefacts are `.py`, `.toml`, `.md`. No binary checked in. |
| "The implementation language is Python 3.11+." | constitution.md §II | language | PASS | `requires-python = ">=3.11"`, all `from __future__ import annotations`. |
| "Introducing an additional runtime dependency requires an amendment to the dependency list." | constitution.md §II | dependency | FAIL → R4 | Amendment text is correct in working tree (`packaging>=23.0` added, version 1.0.0 → 1.1.0, Sync Impact updated) but **uncommitted**; the implementation that consumes the dep was already produced. Per plan.md "implementation MUST NOT begin until the amendment lands". |
| "All production code MUST live under `src/bookwright/`. All tests under `tests/`. No exceptions." | constitution.md §III | layout | PASS | All new files under `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`. |
| "No source file (production or test) may exceed 500 lines." | constitution.md §IV | module-size | FAIL → R2 | `src/bookwright/core/manifest.py` = 562 lines. All other new files ≤200 lines. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | constitution.md §IV | layout | N/A | Iteration 2 adds no CLI subcommand. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. AGENT_CONFIG-style dispatcher forbidden." | constitution.md §V | plugin-shape | PASS | `[integration]` block is read as opaque data only (FR-022). `DEFAULT_SKILLS_DIR` is a 2-key default-table, not a dispatcher. |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/`, `.agents/commands/` is prohibited." | constitution.md §VI | directory-ban | PASS | No writes to skill/command directories in this iteration. |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification." | constitution.md §VII | frontmatter-constraint | N/A | No skills emitted in this iteration. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`. CI MUST run pytest, ruff, mypy strict on every push." | constitution.md §VIII | coverage-threshold | PASS (in WT) | `uv run pytest` → 93.91 % total, `ruff check` clean, `ruff format --check` clean, `mypy --strict` clean. **But:** CI never ran on this state because the code is uncommitted (R1). |
| "Any CLI command meant for an agent MUST accept `--json` and emit a single JSON doc on stdout, nothing else." | constitution.md §IX | io-contract | N/A | No CLI command added. FR-024 only requires shapes ready; `to_json()` shapes verified in `tests/core/test_json_shapes.py`. |
| "Section 16 design axioms MUST NOT be reopened in spec, plan, or task discussions." | constitution.md §X | scope-ban | PASS | Pydantic v2, rdflib, TOML, Agent Skills — all honoured; nothing reopened. |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | constitution.md Tech Constraints | dependency | FAIL → R4 | Set is content-correct in working tree but the change is uncommitted; alphabetical order respected. |
| "v0 deliberately defers: Preset / GrafeoIndexer / integrations beyond claude+generic / Extension system / EPUB-PDF export." | constitution.md Scope & Release | scope-ban | PASS | None pulled forward. The `cursor` test in `test_build.py:122` only exercises the `unknown integration_key` failure path, not a new integration. |
| "Amendments MUST be a dedicated PR that updates constitution.md, bumps the version, updates Sync Impact, and propagates changes." | constitution.md Governance | workflow-step | FAIL → R4 | Amendment text well-formed; the "dedicated PR" half has not happened — nothing is committed. |

### `CLAUDE.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every feature lands through a numbered iteration from the implementation plan, not as a freehand commit." | CLAUDE.md | workflow-step | PASS | iteration 002 has the full spec/plan/tasks/analyze trail; not freehand. |
| "/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement; do not skip steps." | CLAUDE.md | workflow-step | FAIL → R3 | Steps 1–5 are committed (3 spec commits). Step 6 (implement) produced source code that is **not** committed: `?? src/bookwright/core/`, `?? src/bookwright/resources/`, `?? tests/core/`. tasks.md is flipped to all-`[X]` in the working tree without that proof on the branch. |
| "Per-command modules: each CLI subcommand in its own file under `src/bookwright/commands/<name>.py`, ≤500 lines." | CLAUDE.md | module-size | FAIL → R2 | Restates Principle IV. `manifest.py` = 562 lines. |
| "`uuid-utils`, NOT `uuid7`." | CLAUDE.md | dependency | PASS | pyproject.toml still uses `uuid-utils>=0.16`; no `uuid7` introduced. |
| "Merge to `main` only when tests are green and `/speckit-analyze` reports no issues." | CLAUDE.md | workflow-step | PASS (forward-looking) | Tests are green; analyse report is committed at 017f40b. Merge-time gate, not yet exercised. |
| "Spec Kit pinned at `v0.8.16` stable (commit `ffa1a45`). Don't upgrade without reason." | CLAUDE.md | scope-ban | PASS | No spec-kit / `.specify/` template churn in this branch. |

### `specs/002-manifest-model/plan.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The 500-line ceiling (Principle IV) is comfortably respected — `manifest.py` is one model + load/dump/build; helpers split out." | plan.md §Project Structure | module-size | FAIL → R2 | Post-implementation reality contradicts: `manifest.py` = 562 lines. The post-design re-check ("Module count, test layout, JSON shapes … all consistent") is therefore false on this sub-claim. |
| "The implementation iteration MUST NOT begin until the amendment lands (or until the team agrees on the hand-rolled alternative)." | plan.md §Constitution Check | workflow-step | FAIL → R4 | Implementation produced; amendment uncommitted. |

### Track-integrity check (A.3)

For each governance / feature-owned directory the conventions identify:

| Path | On disk | In branch diff | In default history | In status | Verdict |
|---|---|---|---|---|---|
| `specs/002-manifest-model/{spec,plan,research,data-model,quickstart}.md` | Yes | Yes | No | Clean | OK |
| `specs/002-manifest-model/contracts/manifest_api.md` | Yes | Yes | No | Clean | OK |
| `specs/002-manifest-model/checklists/requirements.md` | Yes | Yes | No | Clean | OK |
| `specs/002-manifest-model/tasks.md` | Yes | Yes (initial) | No | **Modified** (all `[X]` flips) | **HIGH** → R3 — completion markers staged on disk but not committed |
| `.specify/memory/constitution.md` | Yes | No | Yes | **Modified** (1.0.0 → 1.1.0 amendment) | **CRITICAL** → R1 — governance file changed in WT only |
| `pyproject.toml` | Yes | No | Yes | **Modified** (packaging dep + wheel force-include) | **CRITICAL** → R1 — build manifest changed in WT only |
| `uv.lock` | Yes | No | Yes | **Modified** (packaging resolution) | **CRITICAL** → R1 — lockfile out-of-sync with branch |
| `src/bookwright/core/` (manifest.py, errors.py, iso639_1.py, __init__.py) | Yes | No | No (`git log --all` empty for `manifest.py`) | **Untracked** | **CRITICAL** → R1 — production code git is unaware of |
| `src/bookwright/resources/` (templates/manifest.template.toml, __init__.py × 2) | Yes | No | No | **Untracked** | **CRITICAL** → R1 — package data git is unaware of |
| `tests/core/` (8 test files + conftest + 19 fixture .toml) | Yes | No | No | **Untracked** | **CRITICAL** → R1 — test suite git is unaware of |

### Workflow-trail integrity (A.4)

| Step | Expected artefact | Present on branch? | Present in WT? |
|---|---|---|---|
| `/speckit-specify` | `spec.md` | ✅ committed | ✅ |
| `/speckit-clarify` | clarification block in `spec.md` | ✅ committed | ✅ |
| `/speckit-plan` | `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/manifest_api.md` | ✅ committed | ✅ |
| `/speckit-tasks` | `tasks.md` | ✅ committed (with `[ ]` boxes) | ⚠️ flipped to all `[X]` only in WT |
| `/speckit-analyze` | analysis report (commit `017f40b`) | ✅ committed | ✅ |
| `/speckit-implement` | source code under `src/bookwright/core/` + tests under `tests/core/` | ❌ **MISSING** | ✅ produced but uncommitted |

The downstream artefact (`tasks.md` with all `[X]`) exists while the upstream artefact (committed source) does not — **workflow trail broken → R3**.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A.3 | CRITICAL | working tree (10 untracked files + 4 modified files) | All iteration-2 implementation is uncommitted; CI never observed this state. | Stop and commit (or revert) before any close-claim. See remediation §4. |
| R2 | A.2 | CRITICAL | `src/bookwright/core/manifest.py:1-562` | 562 lines > 500-line cap mandated by Principle IV (MUST). | Split out the build-table (`_BUILD_OVERRIDE_ALLOWLIST_TABLE` + `Manifest.build`) into `src/bookwright/core/_build.py` (~140 LoC) and the Pydantic→`_FieldFailure` translator (`_translate_validation_error`, `_format_loc`, `_PYDANTIC_TYPE_TO_KIND`, `_ROOT_ERROR_REMAP`) into `src/bookwright/core/_translate.py` (~70 LoC). That brings `manifest.py` under 350. |
| R3 | A.4 | CRITICAL | `specs/002-manifest-model/tasks.md` (modified, not committed) | tasks.md flips all 35 `[ ]` → `[X]` in WT while the proof artefact (source code) is uncommitted. Workflow trail broken. | Either revert the checkbox flip or commit the implementation it claims is done. The checklist must reflect committed state, not local "I did this." |
| R4 | A.2 | HIGH | `.specify/memory/constitution.md` (modified, not committed) + `pyproject.toml` (modified, not committed) | Amendment text is correct (1.0.0 → 1.1.0 adding `packaging>=23.0`, Sync Impact updated, alphabetical order) — but unstaged. The plan's own gate says "implementation MUST NOT begin until the amendment lands." Implementation began. | Commit the amendment as the first commit of the implementation push (constitution.md + pyproject.toml + uv.lock together, single commit). Tasks T001, T002, T003 already describe this; the work just needs to be on the branch. |
| R5 | B | HIGH | `src/bookwright/core/manifest.py:416-449` (`Manifest.dump`) | Latent footgun: `dump()` writes `tomlkit.dumps(self._document)`, not a re-render from `self`. If a caller mutates the Pydantic model (`m.book.title = "X"`) and then calls `m.dump(q)`, the mutation is silently lost. No test covers this; round-trip test reads then writes unmodified. | Either (a) document the constraint loudly in the contract (`dump()` reflects the *loaded/built* document, not Python-side mutations) and reject the inconsistency in iteration 4, or (b) fix by rebuilding `_document` from `self.model_dump(...)` and overlaying onto the template before each dump. Iteration 4's `init` won't trigger this, so (a) is acceptable for now if explicitly written. |
| R6 | B | MEDIUM | `src/bookwright/core/manifest.py:425-427, 460-463` | Dead/speculative code: `Manifest.dump`'s `if document is None` branch and `_render_from_model` helper handle "bare-construction" instances that the documented public API never produces. Both are uncovered (lines 427 and 463 in the coverage miss list). Pure YAGNI. | Delete both. The public surface is `load()` and `build()`, both of which set `_document`. If a future need arises, write it then. |
| R7 | B | MEDIUM | `src/bookwright/resources/templates/manifest.template.toml:35-36` vs `src/bookwright/core/manifest.py:202` | Template comment claims `target_length_words` is a "positive integer". The model accepts any `int | None`; `target_length_words=-5` validates clean. Comment overstates the constraint. | Either tighten the validator (`PositiveInt` from pydantic) — but no FR mandates it — or rewrite the comment to "non-negative integer or omitted". I'd rewrite the comment; the rule isn't in the spec. |
| R8 | A | MEDIUM | `src/bookwright/core/manifest.py:393-399`, `specs/002-manifest-model/contracts/manifest_api.md:182-196` | Contract enumerates three causes for `TypeError`: unknown override kwarg, missing required, wrong-type required. The implementation adds a fourth: unknown `integration_key` without explicit `integration_skills_dir`. `test_build.py:122` asserts this `TypeError` shape. Contract drift. | Decide and align: either add the fourth case to the contract under `Manifest.build` §Exceptions, or convert it to `ManifestValidationError` citing `integration.key`. The latter matches the user-visible error model more cleanly (it's a value error, not a programming error). |
| R9 | C | MEDIUM | `src/bookwright/core/errors.py:67-74` (`ManifestSyntaxError.to_json`) | The `field` key in `ManifestSyntaxError.to_json()` is `f"bookwright.{self.path.name}"`, producing values like `"bookwright.broken.toml"`. The contract example says `"bookwright.<file>"` literally, so the implementation matches the contract text — but the `field` slot is meant for offending field paths elsewhere in the JSON shapes. Semantic overload. | Either drop the `field` key for syntax errors (TOML parse failure has no field) or rename it to `location` / `source`. Keep the contract honest. |
| R10 | A | LOW | `specs/002-manifest-model/plan.md` Post-design re-check | The re-check claims "Module count, test layout, JSON shapes, and atomic-write strategy are all consistent with the pre-design table." Module-size sub-claim is false (R2). | When the split lands (R2), update the plan's re-check note. The plan is otherwise sound. |
| R11 | D | LOW | `src/bookwright/core/manifest.py:306-313` (`_check_cli_floor` defensive branches) | `InvalidVersion` paths for the *installed* CLI version are defensive only — `bookwright.__version__ == "0.0.1"` is hard-coded valid PEP 440 in iteration 1. Uncovered (lines 306-308, 312-313 in coverage miss list). | Acceptable as defence-in-depth, but pair with a one-line unit test that monkey-patches `_installed_version` to return `"not-a-version"` and asserts `ManifestValidationError` with `installed_not_pep440`. Closes the only uncovered model-validator branch. |
| R12 | B | LOW | `src/bookwright/core/errors.py:16-27` (`_FieldFailure`), `tests/core/test_load_invalid.py:16` | `_FieldFailure` is underscore-prefixed (signalling private) yet imported by tests directly. The `ManifestValidationError.failures` attribute is part of the public contract; the dataclass holding each failure is therefore effectively public. | Rename to `FieldFailure` and add to `errors.py`'s public surface (re-export via `bookwright.core.errors`). Either privacy or it's a real public type — pick one. |
| R13 | C | LOW | `src/bookwright/core/manifest.py:466-490` (`_BUILD_OVERRIDE_ALLOWLIST_TABLE`) | The override allowlist is hand-maintained. Adding a Pydantic field requires updating two places (the block model + this table) with no compile-time link. | Acceptable for v0 with 23 entries. Add a unit test that asserts every key in `_BUILD_OVERRIDE_ALLOWLIST_TABLE` resolves to a real attribute on the targeted block, so a typo or drift fails CI immediately. |

## 4. Remediation Detail

### R1 — All iteration-2 work product is uncommitted (CRITICAL)

- **Where:** working tree only — 10 untracked files (under `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`) and 4 modified files (`.specify/memory/constitution.md`, `pyproject.toml`, `uv.lock`, `specs/002-manifest-model/tasks.md`).
- **Why it matters:** `git diff main...HEAD` reports zero implementation; `git log --all --oneline -- src/bookwright/core/manifest.py` returns empty. CI has never observed this state. From the branch's perspective, iteration 2 produced only spec/plan/tasks/analyze documents. Claiming "iteration 002 is done" while the code is invisible to git, to CI, and to any reviewer is exactly the technical debt the user wants gated. Under the no-debt frame ("hay que cancelarla toda" if there is debt), R1 alone closes the question: either commit the work, run CI on the committed state, and re-audit; or revert the working tree and re-open the iteration.
- **Suggested change:** Group commits along the task-phase boundary already in `tasks.md`:
  1. `feat(core): amend constitution + add packaging dep` — `.specify/memory/constitution.md`, `pyproject.toml`, `uv.lock` (covers T001–T003).
  2. `feat(core): scaffold manifest module + ISO-639-1 + errors` — `src/bookwright/core/{__init__,errors,iso639_1}.py`, `src/bookwright/resources/{__init__,templates/__init__,templates/manifest.template.toml}.py(.toml)`, `tests/core/{__init__,conftest}.py` (T004–T011).
  3. One commit per user story for the Pydantic blocks, validators, builder, dump, future-version warning + their tests (T012–T031), or bundle US1–US5 if PR-size is acceptable.
  4. `test(core): json shapes + coverage` — `tests/core/test_json_shapes.py` and any coverage tightening (T032–T035).
  5. `chore(spec): mark tasks.md complete` — `specs/002-manifest-model/tasks.md` checkbox flips. **Do this last**, after the commits whose work each `[X]` represents.

  Then re-run the full CI gate (`uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy --strict src tests`) on the committed branch and re-audit before merge.

### R2 — `manifest.py` exceeds the 500-line cap (CRITICAL)

- **Where:** `src/bookwright/core/manifest.py:1-562` (562 LoC total).
- **Why it matters:** Constitution Principle IV says "No source file (production or test) may exceed 500 lines; a file approaching the limit MUST be decomposed before the limit is reached, not after." This is a MUST. The plan.md predicted "comfortably respected" and is wrong by 62 lines. Leaving this for "later" violates the explicit "before the limit, not after" clause.
- **Suggested change:** Two extractions, both internal (do not change `bookwright.core.__init__`'s `__all__`):
  - `src/bookwright/core/_translate.py` (~70 LoC): move `_PYDANTIC_TYPE_TO_KIND`, `_ROOT_ERROR_REMAP`, `_format_loc`, `_translate_validation_error`. Import them back into `manifest.py` (`from bookwright.core._translate import _translate_validation_error`).
  - `src/bookwright/core/_build.py` (~140 LoC): move `_BUILD_OVERRIDE_ALLOWLIST_TABLE`, `_BUILD_OVERRIDE_ALLOWLIST`, the body of `Manifest.build` (as a free function `_build_manifest(cls, *, title, authors, integration_key, **overrides)`), and `_load_template_document`. `Manifest.build` then becomes a 3-line thin classmethod that delegates.

  Net effect: `manifest.py` ≈ 340 LoC; both new modules well below the cap; public surface unchanged.

### R3 — Workflow trail broken: tasks marked done with no committed proof (CRITICAL)

- **Where:** `specs/002-manifest-model/tasks.md` (modified, not committed) vs the missing commits for T001–T035.
- **Why it matters:** Once R1 is resolved, R3 dissolves naturally: each commit from §R1 covers a contiguous range of tasks; the final `chore(spec)` commit flips the corresponding boxes. The current state — boxes flipped, code missing — is the literal definition of premature task completion.
- **Suggested change:** Do the `[X]` flip in the **last** commit of the implementation push, scoped to only the tasks whose work is in earlier commits of the same push. If a task is genuinely not done (per the audit, T033 was claimed against a narrow per-subpackage coverage run, not the CI gate — clarify with a one-line note in tasks.md or run the full-gate command exactly as configured in pyproject.toml), do not flip its box.

### R4 — Constitutional amendment uncommitted alongside the change it justifies (HIGH)

- **Where:** `.specify/memory/constitution.md` (modified), `pyproject.toml` (modified), `uv.lock` (modified).
- **Why it matters:** The constitution's Governance section requires "a dedicated pull request that updates `.specify/memory/constitution.md`, bumps the version line, updates the Sync Impact Report, and propagates any required changes". The plan.md §Constitution Check explicitly gates this iteration: "The implementation iteration MUST NOT begin until the amendment lands." It began.
- **Suggested change:** The amendment text is correct as-is (1.0.0 → 1.1.0, Sync Impact updated, alphabetical dep list). Stage and commit `.specify/memory/constitution.md` + `pyproject.toml` + `uv.lock` as the **first** commit of the implementation push (per R1's commit plan). This satisfies the Governance procedure on this branch even though it's bundled with the code that consumes the dep.

### R5 — `Manifest.dump` silently drops Pydantic-side mutations (HIGH)

- **Where:** `src/bookwright/core/manifest.py:416-449`, `src/bookwright/core/manifest.py:423` (`document = self._document`).
- **Why it matters:** A future caller writing `m = Manifest.load(p); m.book.title = "New"; m.dump(q)` will end up with `q` carrying the *old* title, because `dump` writes `tomlkit.dumps(self._document)` — i.e., the parsed-on-load tomlkit document, untouched. No assertion currently fails because the round-trip test reads then writes unmodified. The iteration-2 spec (FR-018) says "serialize a manifest object", which the implementation arguably doesn't honour: it serialises the *loaded document*, not the *model state*. Iteration 4 (`init`) goes through `build → dump` (where `_document` is freshly built from the template + overrides, so consistent), so this won't bite immediately — but the contract drift is a footgun the moment any later iteration loads-then-mutates.
- **Suggested change:** Either:
  - (a) **Document the constraint.** Add to `contracts/manifest_api.md` §`Manifest.dump` Behaviour: "`dump()` writes the underlying tomlkit document captured at load/build time. Mutations to attributes on the Pydantic model after load are not reflected in dump output. Use `Manifest.build(...)` with overrides for fresh state." Then add a one-line negative test in `test_write.py` that documents the behaviour (`m.book.title = "edited"; m.dump(q); assert "edited" not in q.read_text()`) so the constraint is regression-locked.
  - (b) **Fix it.** Before each `dump`, rebuild `_document` by overlaying `self.model_dump(mode="python", exclude={"warnings"})` onto a fresh template parse, then dump. This breaks the FR-020 byte-for-byte round-trip guarantee for files whose layout doesn't match the template, so it's the more invasive choice.

  Recommend (a) for v0; reopen for v0.1 if/when a mutation use case appears.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/__main__.py` | 0 % | 80 % | PASS (only exercised by `python -m bookwright`; iteration 1 acceptable) |
| `src/bookwright/cli.py` | 100 % | 80 % | PASS |
| `src/bookwright/commands/check.py` | 96 % | 80 % | PASS |
| `src/bookwright/commands/version.py` | 100 % | 80 % | PASS |
| `src/bookwright/core/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/core/errors.py` | 96 % | 80 % | PASS (uncovered: line 82, an unreachable empty-failures branch) |
| `src/bookwright/core/iso639_1.py` | 100 % | 80 % | PASS |
| `src/bookwright/core/manifest.py` | 94 % | 80 % | PASS (uncovered: 151-152, 165, 306-308, 312-313, 427, 463, 520-523, 551 — see R6, R11) |
| `src/bookwright/resources/__init__.py` | 100 % | 80 % | PASS |
| `src/bookwright/resources/templates/__init__.py` | 100 % | 80 % | PASS |
| **Total** | **93.91 %** | **80 %** | **PASS** |

`bookwright.core` package subtotal: ~95 %, comfortably above the spec's own ≥90 % bar.

## 6. Inability-to-verify notes

- **CI never observed the working-tree state.** All locally-run gates (pytest, ruff, mypy) pass on the WT, but the CI matrix configured in the project (per Principle VIII Technical Constraints) has not run against this code. Once R1 is resolved and a push lands, GitHub Actions becomes the authoritative verifier.
- **`packaging>=23.0` runtime resolution** was verified locally via `uv.lock` (entry present); the constitutional amendment that authorises this dep is itself uncommitted, so the runtime stack and the governance document disagree on the branch (R4).
- **`tomlkit` round-trip determinism** was sample-tested via `test_round_trip_is_byte_identical` for `valid_full.toml` and `valid_minimal.toml` only. Iteration 2 does not certify the round-trip property over arbitrary user manifests; that is the spec's intent (FR-020 says "loaded from disk and written back without modification") and acceptable.
