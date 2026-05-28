# Quality Audit — 002-manifest-model

**Scope:** 35 changed files vs `main` (4 modified + 31 new across `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`, `specs/002-manifest-model/`, plus `pyproject.toml`, `uv.lock`, `CLAUDE.md`, `constitution.md`, `.specify/feature.json`)
**Commit range:** `75e3382` (main) → `aff10b5` (HEAD)
**Date:** 2026-05-28
**Conventions discovered:** `.specify/memory/constitution.md` v1.1.0 (binding), `CLAUDE.md` (project), `specs/002-manifest-model/{spec,plan,tasks,research,data-model,quickstart}.md`, `specs/002-manifest-model/contracts/manifest_api.md`
**Frame from user:** "no puedo cerrar esta spec si hay duda técnica." — surface any technical doubt that should block close.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 4 |
| LOW | 2 |
| **Total** | 7 |

Coverage gate: **PASS**. Full suite — [tests.yml](.github/workflows/tests.yml) replica `uv run pytest` — reports 94.08 % total (threshold = 80 %, see [pyproject.toml:76](pyproject.toml#L76)). `bookwright.core` aggregate: ~95.8 % (manifest.py 95 %, errors.py 96 %, _translate.py 82 %, _build.py 100 %, iso639_1.py 100 %, __init__.py 100 %) — meets the spec's local 90 % bar (T033). `ruff check`, `ruff format --check`, `mypy --strict` all green.

**Headline:** the implementation is functionally complete and every CI gate (Principle VIII) passes locally. The prior audit's blocking items (uncommitted work, 562-line `manifest.py`, staging skew between checkbox flips and code commits, amendment-after-implementation order) have all been resolved by the 8 commits between `a685b9b` (constitutional amendment) and `aff10b5` (polish). What remains is one HIGH that the prior audit flagged and the iteration never closed (R1, `Manifest.dump` silently drops Pydantic-side mutations), plus four MEDIUM technical doubts around the v0 stable Python contract that are worth nailing down before this surface is frozen for iterations 3+ to depend on.

## 2. Conventions Compliance Matrix

Rules extracted in Pass A.1 from the discovered convention files. Every MUST is checked positively; `PASS` is as load-bearing as `FAIL`.

### `.specify/memory/constitution.md` (v1.1.0)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden as canonical storage." | constitution.md §I | layout | PASS | Diff contains only `.py`, `.toml`, `.md`, `.yml`, `.json`. No binary canonical stores. |
| "The implementation language is Python 3.11+." | constitution.md §II | language | PASS | `requires-python = ">=3.11"` ([pyproject.toml:8](pyproject.toml#L8)); CI matrix runs 3.11 + 3.12. |
| "Introducing an additional runtime dependency requires an amendment to the dependency list." | constitution.md §II | dependency | PASS | `packaging>=23.0` added to deps ([pyproject.toml:22](pyproject.toml#L22)); amendment landed first in commit `a685b9b` (versions 1.0.0 → 1.1.0, Sync Impact updated). |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | constitution.md Tech Constraints | dependency | PASS | [pyproject.toml:20-31](pyproject.toml#L20-L31) matches exactly, alphabetical. No additions beyond the amended set. |
| "Build backend: hatchling. Lockfile: uv.lock committed." | constitution.md Tech Constraints | dependency | PASS | `build-backend = "hatchling.build"` ([pyproject.toml:37](pyproject.toml#L37)); `uv.lock` tracked. |
| "All production code MUST live under `src/bookwright/`. All tests under `tests/`. No exceptions." | constitution.md §III | layout | PASS | New code only in `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | constitution.md §IV | layout | N/A | Iteration 2 adds no CLI subcommand. |
| "No source file (production or test) may exceed 500 lines." | constitution.md §IV | module-size | PASS | Largest source: [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py) at 417 lines. Largest test: [tests/core/test_load_valid.py](tests/core/test_load_valid.py) at 194 lines. All under cap. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. AGENT_CONFIG-style dispatcher forbidden." | constitution.md §V | plugin-shape | PASS | `[integration]` block read as opaque data only (FR-022). `DEFAULT_SKILLS_DIR` is a 2-entry table used only inside `Manifest.build` for the per-key default, not a runtime dispatcher. |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/`, `.agents/commands/` is prohibited." | constitution.md §VI | directory-ban | PASS | No writes to skill/command directories. `grep -r "\\.claude/commands\\|\\.agents/commands" src/ tests/` returns nothing. |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification." | constitution.md §VII | frontmatter-constraint | N/A | No SKILL.md emitted in this iteration. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`. CI MUST run pytest, ruff, mypy strict on every push." | constitution.md §VIII | coverage-threshold | PASS | `uv run pytest` → 94.08 % total. `.github/workflows/tests.yml` runs all four gates. |
| "Any CLI command meant for an agent MUST accept `--json` and emit a single JSON doc on stdout, nothing else." | constitution.md §IX | io-contract | PASS (shapes only) | No CLI subcommand added. FR-024 only requires the JSON shapes be ready; `to_json()` shapes pass [tests/core/test_json_shapes.py](tests/core/test_json_shapes.py) (5 shapes, json.dumps round-trip). |
| "Section 16 design axioms MUST NOT be reopened in spec, plan, or task discussions." | constitution.md §X | scope-ban | PASS | Pydantic v2, rdflib, TOML, Agent Skills, plain text — all honoured; no axiom reopened. |
| "v0 deliberately defers: Preset / GrafeoIndexer / integrations beyond claude+generic / Extension system / EPUB-PDF export." | constitution.md Scope & Release | scope-ban | PASS | None pulled forward. The `cursor` test in [tests/core/test_build.py:122-146](tests/core/test_build.py#L122-L146) only exercises the `unknown integration_key` failure path, not a real integration. |
| "Amendments MUST be a dedicated PR that updates constitution.md, bumps the version, updates Sync Impact, and propagates changes." | constitution.md Governance | workflow-step | PASS | Commit `a685b9b feat(constitution): amend to v1.1.0 adding packaging dep (T001–T003)` landed as the first commit on the branch, before any implementation commit. |

### `CLAUDE.md` (project instructions)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Layout: `src/bookwright/…` for production code, `tests/` at the root. No exceptions." | CLAUDE.md "Stack" | layout | PASS | Verified above. |
| "Per-command modules: each CLI subcommand in its own file under `src/bookwright/commands/<name>.py`, ≤500 lines." | CLAUDE.md "Stack" | module-size | N/A | No new subcommand in this iteration. |
| "Run iteration via `/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement`." | CLAUDE.md "How work is done" | workflow-step | PASS | See A.4 below. |
| "Monolithic `AGENT_CONFIG`-style dispatcher is forbidden — use `SkillsIntegration` + `INTEGRATION_REGISTRY`." | CLAUDE.md "Domain knobs" | plugin-shape | PASS | No dispatcher introduced. |
| "JSON-over-stdout contract: any subcommand consumed by an agent accepts `--json` …" | CLAUDE.md "Domain knobs" | io-contract | PASS (shapes only) | Same as Principle IX above. |
| "Out of v0 scope — do not implement: Preset / GrafeoIndexer / Copilot/Gemini/Cursor / Extensions / EPUB-PDF." | CLAUDE.md "Out of v0 scope" | scope-ban | PASS | None present. |
| "Source code, identifiers, commit messages, and the constitution itself are in **English**." | CLAUDE.md "Language" | other | PASS | Spot-checked: all new module docstrings, identifier names, commit messages in English; spec/plan/data-model/research/quickstart in English per Spec-Kit template. |
| "Spec Kit specifics — skill names are hyphenated; `extensions.yml` hook entries still use dot form." | CLAUDE.md "Spec Kit" | other | N/A | No skill/hook changes this iteration. |

### A.3 Track-integrity for governance / feature-owned directories

`specs/002-manifest-model/` — files on disk:

| File | In branch diff | In default history | Verdict |
|---|---|---|---|
| spec.md | yes | no | OK (branch artefact) |
| plan.md | yes | no | OK |
| tasks.md | yes | no | OK |
| research.md | yes | no | OK |
| data-model.md | yes | no | OK |
| quickstart.md | yes | no | OK |
| review.md (this file) | yes | no | OK |
| checklists/requirements.md | yes | no | OK |
| checklists/quality.md | yes | no | OK |
| contracts/manifest_api.md | yes | no | OK |

`git status` is clean; `git ls-files specs/002-manifest-model/` covers every on-disk file. **No untracked governance artefacts.** PASS.

### A.4 Workflow-trail integrity

Spec Kit sequence: `specify → clarify → plan → tasks → analyze → implement`.

| Step | Artefact | Present | Notes |
|---|---|---|---|
| specify | spec.md | yes | Comprehensive: 5 user stories, 24 FRs, 6 entities, 7 SCs, 8 assumptions. |
| clarify | "Clarifications / Session 2026-05-28" in spec.md | yes | 5 Q&A entries covering warning surfacing, URI shape, version comparison, ISO codes, builder signature. |
| plan | plan.md | yes | Includes Constitution Check (✅ all 10 principles), pre-/post-design re-check, Complexity Tracking. |
| tasks | tasks.md | yes | 35 tasks across 8 phases, all checked `[X]`. |
| analyze | (no standalone file) | partial | Commit `017f40b "[Spec Kit] Add analysis report"` packs plan/data-model/contracts/quickstart/research/tasks rather than a separate report. `checklists/requirements.md` is fully ticked, which is the actionable analyze output. Acceptable. |
| implement | `src/bookwright/core/*`, `tests/core/*`, `src/bookwright/resources/templates/manifest.template.toml` | yes | All 8 implementation commits present (`e7ebaf6` scaffold → `aff10b5` polish). |

PASS. No downstream-artefact-without-upstream-artefact case detected.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A/B | HIGH | [src/bookwright/core/manifest.py:378-411](src/bookwright/core/manifest.py#L378-L411), [specs/002-manifest-model/contracts/manifest_api.md:113-135](specs/002-manifest-model/contracts/manifest_api.md#L113-L135) | `Manifest.dump` writes from `self._document`, so any post-load mutation of the Pydantic model (e.g. `m.book.title = "new"`) is silently dropped — the dumped file keeps the old title. This is the same defect flagged R5 in the prior audit; the contract still does not document it and no regression test pins the behaviour. | Pick one: (a) set `model_config = ConfigDict(frozen=True)` on `Manifest` so mutation raises; (b) wire `validate_assignment=True` plus a per-field projection back into `_document` (heavyweight); (c) keep current behaviour but add an explicit "mutation-after-load is not part of the contract" paragraph to `contracts/manifest_api.md` §`Manifest.dump` and lock it with a `test_dump_ignores_post_load_mutation` that asserts the observed behaviour. The third is cheapest and matches the v0 "load → dump round-trip; build → dump" intent. |
| R2 | A | MEDIUM | [src/bookwright/core/manifest.py:115-118](src/bookwright/core/manifest.py#L115-L118), [tests/core/fixtures/future_manifest_version.toml](tests/core/fixtures/future_manifest_version.toml) | The US5 forward-compat contract ("future `manifest_version` loads best-effort") is partial: `BookwrightBlock` uses `extra="forbid"`, so a future manifest that adds even one new key inside `[bookwright]` raises `ManifestValidationError` *before* `_classify_manifest_version_warnings` runs. The warning would never fire. The US5 fixture only bumps `manifest_version`, so this gap is not exercised. Spec wording ("every recognised field is still populated") is technically met, but the contract's *intent* — that an older CLI degrade gracefully on a newer manifest — is narrower than readers will assume. | Either (a) document the limit explicitly in [contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md) §`Manifest.load`/Classification: "forward-compat applies only to `manifest_version`-level changes that do not introduce new keys inside known blocks; key-level forward-compat is not in v0 scope," and add a negative fixture confirming the behaviour; or (b) lift `extra` to `"allow"` on `BookwrightBlock` so unknown future keys round-trip as opaque data. Option (a) is the smaller change and keeps `extra="forbid"` doing its existing job of catching typos. |
| R3 | A | MEDIUM | [src/bookwright/core/manifest.py:121](src/bookwright/core/manifest.py#L121), [specs/002-manifest-model/data-model.md:84](specs/002-manifest-model/data-model.md#L84) | `data-model.md` documents `schema_version` as "Must be a non-empty string", but the field is declared bare `schema_version: str` with no validator, so `schema_version = ""` loads cleanly. Drift between the design artefact and the implementation. Not a spec violation (FR-010 only requires presence), but a doubt about which document is the source of truth. | Add a `field_validator("schema_version", mode="after")` mirroring `_check_title` (non-empty after `strip()`, rule id `bookwright.schema_version.empty`); add it to the rule taxonomy in `contracts/manifest_api.md`; add a fixture `invalid_bookwright_schema_version_empty.toml`. Alternatively, weaken data-model.md to "any string" if the project consciously does not want this enforced. |
| R4 | A/D | MEDIUM | [src/bookwright/core/manifest.py:163-168](src/bookwright/core/manifest.py#L163-L168), [tests/core/fixtures/](tests/core/fixtures/) | The `bookwright.uri_base.empty_host` rule is listed in the contract's stable taxonomy ([contracts/manifest_api.md:241](specs/002-manifest-model/contracts/manifest_api.md#L241)) but no fixture exercises it. Coverage shows line 164 uncovered. A reader would assume the rule is wired and tested. Examples that should trigger it (e.g. `http:///path/`, `https:///`) are absent from the invalid fixture set. | Add `tests/core/fixtures/invalid_uri_base_empty_host.toml` with `uri_base = "http:///p/"` and extend the parametrised list in [test_load_invalid.py:32-80](tests/core/test_load_invalid.py#L32-L80). One row in the table, one fixture file. |
| R5 | A/B | MEDIUM | [src/bookwright/core/manifest.py:148-155](src/bookwright/core/manifest.py#L148-L155), [specs/002-manifest-model/contracts/manifest_api.md:240](specs/002-manifest-model/contracts/manifest_api.md#L240) | The `bookwright.uri_base.invalid_uri` rule is named in the contract taxonomy but its raise site requires `urlsplit` to raise `ValueError`, which it almost never does for string inputs (it tolerates malformed schemes, missing hosts, etc., and surfaces them as empty `parts.*` fields instead). The rule is effectively unreachable in practice; the `except ValueError` block at lines 150-155 is dead code. Readers of the contract will plan for an error that cannot fire. | Either (a) drop `invalid_uri` from the rule taxonomy in `contracts/manifest_api.md:240` and remove the dead `try/except` from `_check_uri_base`; or (b) tighten the validator to actually surface this case (e.g. reject if `parts.scheme == ""` *and* `parts.netloc == ""` with `invalid_uri`, rather than always demoting to `wrong_scheme`). (a) is the smaller change and matches what the existing fixtures actually test. |
| R6 | D | LOW | [src/bookwright/core/manifest.py:305-312](src/bookwright/core/manifest.py#L305-L312) | The `installed_not_pep440` defensive branch in `_check_cli_floor` is uncovered. Triggers only when the installed CLI's own `__version__` fails PEP 440 parsing — possible during local dev where `bookwright.__version__` is hand-edited to e.g. `"0.0.1-dev"`. | Add a single line in [test_version_gate.py](tests/core/test_version_gate.py): `installed_version("v1")` then `Manifest.load(...)` → expect `ManifestValidationError` with `rule_id == "bookwright.cli_version_min.installed_not_pep440"`. Closes the coverage gap and pins the contract. |
| R7 | A | LOW | [.specify/memory/constitution.md:9-19](.specify/memory/constitution.md#L9-L19) | The Sync Impact Report for the 1.0.0 → 1.1.0 amendment reads as if all 10 principles are newly defined ("Principles defined (all new, no renames): I. Plain Text … X. Design Document Axioms"). For a MINOR amendment, the Sync Impact should describe the *delta* (added `packaging>=23.0` to Tech Constraints), not the original ratification scope. Cosmetic but confusing for the audit trail; reviewers reading the diff cannot tell what actually changed in 1.1.0 without comparing to 1.0.0. | Trim the "Principles defined / Added sections" subsections in the Sync Impact header to a single line: "MINOR change: `packaging>=23.0` added to the Technical Constraints runtime dependency list (Principle II), required by FR-012 PEP 440 ordering." Keep the rest of the constitution body unchanged. |

## 4. Remediation Detail

### R1 — `Manifest.dump` silently drops Pydantic-side mutations (HIGH)

- **Where:** [src/bookwright/core/manifest.py:378-411](src/bookwright/core/manifest.py#L378-L411) (dump uses `self._document`), [specs/002-manifest-model/contracts/manifest_api.md:113-135](specs/002-manifest-model/contracts/manifest_api.md#L113-L135) (contract is silent on mutation semantics).
- **Why it matters:** the v0 stable Python API is what iterations 3+ will build against. `Manifest(BaseModel)` is mutable by default (no `frozen=True`, no `validate_assignment=True`), so `m.book.title = "new"` is syntactically legal. But `dump()` writes `self._document`, which still carries the *pre-mutation* title. The file on disk silently disagrees with the in-memory model. This is the exact class of bug Principle I exists to prevent — diffability and round-trip honesty are load-bearing. The prior audit's R5 raised this; the iteration shipped without resolving it.
- **Suggested change:** the cheapest correct fix is option (c) — accept the current behaviour, but make it explicit. Edit `contracts/manifest_api.md` §`Manifest.dump` to add: *"`dump()` serialises the underlying `tomlkit` document captured at load/build time. Mutations applied to the Pydantic model after load are NOT reflected in the output. To change a field and persist it, prefer constructing a fresh manifest via `Manifest.build(...)` with overrides."* Then add a regression test in `tests/core/test_write.py` that loads `valid_minimal.toml`, mutates `m.book.title`, dumps, and asserts the dumped file matches the *original* — locking the behaviour as deliberate. If the team would rather enforce immutability, swap that test for `model_config = ConfigDict(frozen=True)` on `Manifest` + a `test_post_load_mutation_raises` test. Either fix closes the doubt.

### R2 — Forward-compat is only `manifest_version`-deep (MEDIUM)

- **Where:** [src/bookwright/core/manifest.py:115-118](src/bookwright/core/manifest.py#L115-L118) (`BookwrightBlock` is `extra="forbid"`), [tests/core/fixtures/future_manifest_version.toml](tests/core/fixtures/future_manifest_version.toml) (fixture only bumps `manifest_version`).
- **Why it matters:** US5 promises "best-effort load" for a future manifest version. In practice the manifest schema may evolve by adding new keys inside `[bookwright]` (e.g. `lock_file`, `default_locale`). With `extra="forbid"`, any such manifest would fail with `extra_forbidden` on the new key *before* `_classify_manifest_version_warnings` is reached — the user sees a hard validation error, not the documented forward-compat warning. The spec's literal wording is still satisfied ("every recognised field is still populated"), but the *intent* readers infer from US5 is broader. This is a gap iteration 3+ will trip on when bumping `manifest_version`.
- **Suggested change:** the spec calls it "best-effort," so document the boundary in `contracts/manifest_api.md` §`Manifest.load`/Classification, immediately after the existing `manifest_version` paragraph: *"Forward-compat applies to changes in the **value** of `manifest_version` alone. Adding new keys to known blocks (`[bookwright]`, `[book]`, `[vocabularies]`, `[validators]`, `[integration]`, `[paths]`) is still a validation error under `extra='forbid'`. Only new top-level blocks (e.g. `[experimental]`) round-trip opaquely via the root `extra='allow'`."* Add a fixture and test that constructs a future-version manifest with an unknown key inside `[bookwright]` and asserts `ManifestValidationError` (rule `bookwright.unknown_key`) — proves the limit is intentional. If iteration 3+ wants real key-level forward-compat, that's a separate scope discussion (and a `manifest_version` bump).

## 5. Coverage Detail

`uv run pytest` (full suite, matching `.github/workflows/tests.yml:35`).

| Module | Stmts | Miss | Branch | Cover | Status | Missing lines |
|---|---|---|---|---|---|---|
| `bookwright/core/__init__.py` | 3 | 0 | 0 | 100 % | PASS | — |
| `bookwright/core/_build.py` | 42 | 0 | 10 | 100 % | PASS | — |
| `bookwright/core/_translate.py` | 32 | 4 | 12 | 82 % | PASS | 41-44 (first-piece-int branch in `_format_loc`), 72 (defensive `ctx["value"]` fallback) |
| `bookwright/core/errors.py` | 55 | 1 | 2 | 96 % | PASS | 82 (`ManifestValidationError(())` empty-tuple `ValueError`) |
| `bookwright/core/iso639_1.py` | 3 | 0 | 0 | 100 % | PASS | — |
| `bookwright/core/manifest.py` | 202 | 9 | 34 | 95 % | PASS | 150-151 (urlsplit ValueError — see R5), 164 (empty_host — see R4), 305-307 + 311-312 (installed_not_pep440 — see R6), 389 + 417 (`_render_from_model` fallback for bare construction) |
| **`bookwright.core` aggregate** | **337** | **14** | **58** | **~95.8 %** | **PASS** ≥ 90 % spec target |
| Iteration-1 modules (`cli.py`, `commands/check.py`, `commands/version.py`, `__main__.py`) | 65 | 4 | 12 | ~94 % | PASS | (not in this iteration's scope) |
| **Total `bookwright/`** | **403** | **18** | **70** | **94.08 %** | **PASS** ≥ 80 % CI gate |

Every missing line corresponds to a defensive / fallback / cosmetic branch that the findings above either document (R4, R5, R6) or accept as cheap insurance.

## 6. Inability-to-verify notes

- Could not exercise the GitHub Actions matrix locally; verified each gate independently (`uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict`). Per CI `tests.yml`, these are the same four commands the matrix runs.
- `[integration].key` validity against the v0 registry (`claude` | `generic`) is explicitly NOT the model's job (FR-022, deferred to iteration 3); the model's "string, non-empty after strip is fine" stance is correct here, not a finding.
- `_render_from_model` (lines 389-417) is unreachable through `load()` / `build()` but is the documented fallback for bare `Manifest(...)` construction. Whether to keep or drop it is a stylistic call; not flagged.
