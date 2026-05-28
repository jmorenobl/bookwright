# Quality Audit — 002-manifest-model

**Scope:** 51 changed files vs `main` (4 modified + 47 new across `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`, `specs/002-manifest-model/`, plus `pyproject.toml`, `uv.lock`)
**Commit range:** `75e3382` (main) → `0429b09` (HEAD)
**Date:** 2026-05-28
**Conventions discovered:** [.specify/memory/constitution.md](.specify/memory/constitution.md) v1.1.0 (binding), [CLAUDE.md](CLAUDE.md), [specs/002-manifest-model/{spec,plan,tasks,research,data-model,quickstart}.md](specs/002-manifest-model/), [specs/002-manifest-model/contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md)
**Prior audit:** the same `review.md` at `aff10b5` flagged R1 (dump mutation) HIGH and R2 (forward-compat boundary) MEDIUM. Both are closed by `cc59389` (contract paragraphs + regression tests). The 7-item `/simplify`-driven cleanup in `0429b09` closed the JSON-value-leak / authors-index / warnings-PrivateAttr / TOCTOU items as well.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 4 |
| LOW | 2 |
| **Total** | 6 |

Coverage gate: **PASS**. `uv run pytest` → 94.82 % total (threshold = 80 %, [pyproject.toml:76](pyproject.toml#L76)); `bookwright.core` aggregate ≈ 95.7 % (manifest.py 96 %, errors.py 96 %, _translate.py 88 %, _build.py 100 %, iso639_1.py 100 %, __init__.py 100 %) — meets the spec's 90 % local bar. `ruff check`, `ruff format --check`, `mypy --strict` all green. 71 tests pass.

**Headline:** the iteration is functionally complete and every Principle-VIII gate is green. The prior HIGH (`Manifest.dump` mutation semantics) and the prior MEDIUM forward-compat boundary are now both documented in [contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md) and pinned by regression tests — see R1/R2 in §4 of the previous review. What remains are the same four MEDIUM and two LOW items that the iteration consciously chose not to land in this PR: three are doc-vs-code drift inside the published rule taxonomy, one is a small contract gap introduced by `0429b09`, and two are coverage / cosmetic notes. None of the remaining findings are spec violations or constitutional MUST failures, so the branch is mergeable.

## 2. Conventions Compliance Matrix

Rules extracted in Pass A.1 from the discovered convention files. Every MUST is checked positively; `PASS` is as load-bearing as `FAIL`.

### `.specify/memory/constitution.md` (v1.1.0)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden as canonical storage." | constitution.md §I | layout | PASS | Diff contains only `.py`, `.toml`, `.md`, `.lock`. No binary canonical stores. |
| "The implementation language is Python 3.11+." | constitution.md §II | language | PASS | `requires-python = ">=3.11"` ([pyproject.toml:8](pyproject.toml#L8)). |
| "Introducing an additional runtime dependency requires an amendment to the dependency list." | constitution.md §II | dependency | PASS | `packaging>=23.0` added ([pyproject.toml:22](pyproject.toml#L22)); amendment `a685b9b` (1.0.0 → 1.1.0) lands first on the branch. |
| "Runtime dependencies (minimum set): jinja2, packaging, platformdirs, pydantic, python-slugify, rdflib, rich, tomlkit, typer, uuid-utils." | constitution.md Tech Constraints | dependency | PASS | [pyproject.toml:20-31](pyproject.toml#L20-L31) matches exactly. No additions beyond the amended set. |
| "Build backend: hatchling. Lockfile: uv.lock committed." | constitution.md Tech Constraints | dependency | PASS | `build-backend = "hatchling.build"` ([pyproject.toml:37](pyproject.toml#L37)); `uv.lock` tracked. |
| "All production code MUST live under `src/bookwright/`. All tests under `tests/`." | constitution.md §III | layout | PASS | New code only in `src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | constitution.md §IV | layout | N/A | Iteration 2 adds no CLI subcommand. |
| "No source file (production or test) may exceed 500 lines." | constitution.md §IV | module-size | PASS | Largest source: [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py) at 441 lines. Largest test: [tests/core/test_load_valid.py](tests/core/test_load_valid.py) at 194 lines. All under cap. |
| "Integrations MUST be subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`. AGENT_CONFIG-style dispatcher forbidden." | constitution.md §V | plugin-shape | PASS | `[integration]` block read as opaque data (FR-022). `DEFAULT_SKILLS_DIR` is a 2-entry default-table used only inside `Manifest.build`, not a runtime dispatcher. |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/`, `.agents/commands/` is prohibited." | constitution.md §VI | directory-ban | PASS | `grep -r "\.claude/commands\|\.agents/commands" src/ tests/` returns nothing. |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification." | constitution.md §VII | frontmatter-constraint | N/A | No SKILL.md emitted in this iteration. |
| "v0 MUST hold a minimum of 80 % line coverage across `src/bookwright/`. CI MUST run pytest, ruff, mypy strict on every push." | constitution.md §VIII | coverage-threshold | PASS | `uv run pytest` → 94.82 %. CI gate is `--cov-fail-under=80`. |
| "Any CLI command meant for an agent MUST accept `--json` and emit a single JSON doc on stdout, nothing else." | constitution.md §IX | io-contract | PASS (shapes only) | No CLI subcommand added. FR-024 only requires the JSON shapes be ready; `to_json()` shapes pass [tests/core/test_json_shapes.py](tests/core/test_json_shapes.py) (5 shapes, json.dumps round-trip). Model layer never writes to stdout/stderr (verified by `test_future_manifest_version_attaches_one_warning`'s `capsys` assertion). |
| "Section 16 design axioms MUST NOT be reopened in spec, plan, or task discussions." | constitution.md §X | scope-ban | PASS | Pydantic v2, rdflib (deferred), TOML, Agent Skills, plain text — all honoured; no axiom reopened. |
| "v0 deliberately defers: Preset / GrafeoIndexer / integrations beyond claude+generic / Extension system / EPUB-PDF export." | constitution.md Scope & Release | scope-ban | PASS | None pulled forward. The `cursor` test in [tests/core/test_build.py:122-146](tests/core/test_build.py#L122-L146) only exercises the *unknown integration_key* failure path. |
| "Amendments MUST be a dedicated PR that updates constitution.md, bumps the version, updates Sync Impact, and propagates changes." | constitution.md Governance | workflow-step | PASS (cosmetic gap → R5) | Commit `a685b9b` lands the 1.0.0 → 1.1.0 amendment first. Sync Impact wording overstates the delta — see R5. |

### `CLAUDE.md` (project instructions)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Layout: `src/bookwright/…` for production code, `tests/` at the root. No exceptions." | CLAUDE.md "Stack" | layout | PASS | Verified above. |
| "Per-command modules: each CLI subcommand in its own file under `src/bookwright/commands/<name>.py`, ≤500 lines." | CLAUDE.md "Stack" | module-size | N/A | No new subcommand. |
| "Run iteration via `/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement`." | CLAUDE.md "How work is done" | workflow-step | PASS | See A.4. |
| "Monolithic `AGENT_CONFIG`-style dispatcher is forbidden." | CLAUDE.md "Domain knobs" | plugin-shape | PASS | No dispatcher introduced. |
| "Out of v0 scope — do not implement: Preset / GrafeoIndexer / Copilot/Gemini/Cursor / Extensions / EPUB-PDF." | CLAUDE.md "Out of v0 scope" | scope-ban | PASS | None present. |
| "Source code, identifiers, commit messages, and the constitution itself are in **English**." | CLAUDE.md "Language" | other | PASS | All new module docstrings, identifiers, commit messages in English. |
| "Spec Kit specifics — skill names are hyphenated; `extensions.yml` hook entries use dot form." | CLAUDE.md "Spec Kit" | other | N/A | No skill/hook changes this iteration. |

### A.3 Track-integrity for governance / feature-owned directories

`specs/002-manifest-model/` — `find specs/002-manifest-model -type f | wc -l` = `git ls-files specs/002-manifest-model/ | wc -l` = 10. No untracked or `.gitignore`-orphaned governance files. PASS.

### A.4 Workflow-trail integrity

Spec Kit sequence: `specify → clarify → plan → tasks → analyze → implement`.

| Step | Artefact | Present | Notes |
|---|---|---|---|
| specify | spec.md | yes | 5 user stories, 24 FRs, 6 entities, 7 SCs. |
| clarify | "Clarifications / Session 2026-05-28" in spec.md | yes | 5 Q&A entries. |
| plan | plan.md | yes | Constitution Check ✅ all 10, Complexity Tracking, post-design re-check. |
| tasks | tasks.md | yes | 35 tasks across 8 phases, all `[X]`. |
| analyze | (no standalone file) | partial | Bundled in commit `017f40b`; `checklists/requirements.md` fully ticked as the actionable output. Acceptable. |
| implement | `src/bookwright/core/*`, `tests/core/*`, `src/bookwright/resources/templates/manifest.template.toml` | yes | 11 implementation commits (`e7ebaf6` → `0429b09`). |

PASS. No downstream-artefact-without-upstream-artefact case detected.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | MEDIUM | [src/bookwright/core/manifest.py:126](src/bookwright/core/manifest.py#L126), [specs/002-manifest-model/data-model.md:84](specs/002-manifest-model/data-model.md#L84) | `data-model.md` documents `schema_version` as "Must be a non-empty string", but the field is declared bare `schema_version: str` with no validator, so `schema_version = ""` loads cleanly. Drift between the design artefact and the implementation; not an FR-010 violation (FR-010 only requires presence). | Add a `field_validator("schema_version", mode="after")` mirroring `_check_title` (non-empty after `strip()`, rule id `bookwright.schema_version.empty`); register it in the rule taxonomy in `contracts/manifest_api.md`; add an `invalid_bookwright_schema_version_empty.toml` fixture. Alternatively weaken `data-model.md:84` to "any string" if the project consciously does not want this enforced. |
| R2 | A/D | MEDIUM | [src/bookwright/core/manifest.py:153-160](src/bookwright/core/manifest.py#L153-L160), [specs/002-manifest-model/contracts/manifest_api.md:270-275](specs/002-manifest-model/contracts/manifest_api.md#L270-L275) | The `bookwright.uri_base.invalid_uri` rule is named in the published rule taxonomy but no fixture exercises it. Coverage shows lines 155-156 uncovered. *Note*: contrary to the previous audit's "dead code" reading, the branch IS reachable — `urlsplit("http://[invalid")` raises `ValueError("Invalid IPv6 URL")` — but the test suite never demonstrates it. Readers of the contract will plan for an error that the test suite does not pin. | Add `tests/core/fixtures/invalid_uri_base_malformed_ipv6.toml` with `uri_base = "http://[invalid"`; extend the parametrised list in [tests/core/test_load_invalid.py:32-80](tests/core/test_load_invalid.py#L32-L80). One row + one fixture file closes both the contract-promise gap and the coverage gap. |
| R3 | A/D | MEDIUM | [src/bookwright/core/manifest.py:168-173](src/bookwright/core/manifest.py#L168-L173), [tests/core/fixtures/](tests/core/fixtures/) | The `bookwright.uri_base.empty_host` rule is listed in the contract's stable taxonomy ([contracts/manifest_api.md:270-275](specs/002-manifest-model/contracts/manifest_api.md#L270-L275)) but no fixture exercises it. Coverage shows line 169 uncovered. Sample inputs that should trigger it (e.g. `http:///path/`, `https:///`) are absent. | Add `tests/core/fixtures/invalid_uri_base_empty_host.toml` with `uri_base = "http:///p/"` and a row in the [test_load_invalid.py:32-80](tests/core/test_load_invalid.py#L32-L80) parametrisation. Same minimal-change shape as R2. |
| R4 | A | MEDIUM | [src/bookwright/core/manifest.py:404-409](src/bookwright/core/manifest.py#L404-L409), [specs/002-manifest-model/contracts/manifest_api.md:139-143](specs/002-manifest-model/contracts/manifest_api.md#L139-L143) | `Manifest.dump` now raises `RuntimeError` when `self._document is None` (introduced by `0429b09` after removing the `_render_from_model` fallback). The contract's *Exceptions* list for `dump()` does not mention `RuntimeError` — it only documents `ManifestOverwriteError` and `OSError` subclasses. A caller who instantiates `Manifest` directly (or via `model_construct`) will hit an undocumented exception. The `_document=None` path is unreachable through the supported `load()` / `build()` entry points, but `Manifest` is re-exported via `bookwright.core.__init__.py` and therefore part of the public surface. | Either (a) add a one-paragraph note to `contracts/manifest_api.md` §`Manifest.dump`/Exceptions: *"`RuntimeError` if called on a `Manifest` instance not produced by `Manifest.load(...)` or `Manifest.build(...)` — bare construction is not part of the v0 contract."* — and (optionally) lock the behaviour with a one-line test; or (b) mark `Manifest.__init__` private by routing public construction exclusively through `load`/`build` (heavier; not worth the churn for v0). Option (a) is the cheapest correct close. |
| R5 | D | LOW | [src/bookwright/core/manifest.py:325-326](src/bookwright/core/manifest.py#L325-L326) | The `installed_not_pep440` defensive branch in `_check_cli_floor` is uncovered. Fires only when the installed CLI's own `__version__` fails PEP 440 parsing — possible during local dev where `bookwright.__version__` is hand-edited to e.g. `"0.0.1-dev"`. Rule id is in the published taxonomy. | Add a single test in [test_version_gate.py](tests/core/test_version_gate.py): `installed_version("v1")` then `Manifest.load(load_fixture("valid_minimal.toml"))` → expect `ManifestValidationError` with `rule_id == "bookwright.cli_version_min.installed_not_pep440"`. Closes the coverage gap and pins the contract. |
| R6 | A | LOW | [.specify/memory/constitution.md:9-19](.specify/memory/constitution.md#L9-L19) | The Sync Impact Report for the 1.0.0 → 1.1.0 amendment reads as if all 10 principles are newly defined ("Principles defined (all new, no renames): I. Plain Text … X. Design Document Axioms"). For a MINOR amendment, the Sync Impact should describe the *delta* (added `packaging>=23.0` to Tech Constraints), not the original ratification scope. Cosmetic but confusing for the audit trail. | Trim the "Principles defined / Added sections" subsections in the Sync Impact header to a single line: *"MINOR change: `packaging>=23.0` added to the Technical Constraints runtime dependency list (Principle II), required by FR-012 PEP 440 ordering."* Keep the rest of the constitution body unchanged. |

## 4. Remediation Detail

No CRITICAL or HIGH findings. The four MEDIUM items above are all small, file-local edits. None block merge of the iteration; they are the residue of doc-vs-code drift inside the *published* rule taxonomy and one small contract gap introduced by the `0429b09` cleanup. The two LOW items are a coverage gap and a constitution-housekeeping note.

If the team wants to ship a tidy v0 stable surface, R1–R4 are worth doing in the *current* PR because they all touch artefacts that go on disk as part of this iteration (the rule taxonomy in `contracts/manifest_api.md` and the fixture/test set under `tests/core/`). R5 and R6 can comfortably wait.

## 5. Coverage Detail

`uv run pytest --cov=bookwright --cov-report=term-missing` (matches CI gate at [pyproject.toml:76](pyproject.toml#L76)).

| Module | Stmts | Miss | Branch | Cover | Status | Missing lines |
|---|---|---|---|---|---|---|
| `bookwright/core/__init__.py` | 3 | 0 | 0 | 100 % | PASS | — |
| `bookwright/core/_build.py` | 42 | 0 | 10 | 100 % | PASS | — |
| `bookwright/core/_translate.py` | 34 | 3 | 14 | 88 % | PASS | 41-44 (first-piece-int branch in `_format_loc`, unreachable through current call sites) |
| `bookwright/core/errors.py` | 55 | 1 | 2 | 96 % | PASS | 82 (`ManifestValidationError(())` empty-tuple `ValueError`; defensive) |
| `bookwright/core/iso639_1.py` | 3 | 0 | 0 | 100 % | PASS | — |
| `bookwright/core/manifest.py` | 206 | 8 | 36 | 96 % | PASS | 155-156 (R2 `invalid_uri`), 169 (R3 `empty_host`), 325-326 (R5 `installed_not_pep440`), 405 + 433-434 (`dump` RuntimeError + os.link-EEXIST refusal; both reachable only from unsupported call paths) |
| **`bookwright.core` aggregate** | **343** | **12** | **62** | **~95.7 %** | **PASS** ≥ 90 % spec target |
| Iteration-1 modules (`cli.py`, `commands/check.py`, `commands/version.py`, `__main__.py`) | 65 | 4 | 12 | ~94 % | PASS | (out of this iteration's scope) |
| **Total `bookwright/`** | **409** | **16** | **74** | **94.82 %** | **PASS** ≥ 80 % CI gate |

Every remaining miss is either covered by a finding above (R2, R3, R5) or a defensive / unsupported-call-path branch.

## 6. Inability-to-verify notes

- Could not run the GitHub Actions matrix locally; verified each gate independently (`uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict`). Per CI `tests.yml`, these are the same four commands the matrix runs.
- `[integration].key` validity against the future v0 registry (`claude` | `generic`) is intentionally NOT the model's job (FR-022, deferred to iteration 3). The model's "non-empty string is fine" stance is correct here, not a finding.
- The `RuntimeError` raise site in `Manifest.dump` (line 405) covers an unsupported call path; verifying it is unreachable from `load()` / `build()` is a reading of the code, not a test result.
