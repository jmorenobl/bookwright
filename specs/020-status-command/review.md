# Quality Audit — 020-status-command

**Scope:** 32 changed files vs main
**Commit range:** main..b234c2a
**Date:** 2026-06-12
**Conventions discovered:** `.specify/memory/constitution.md` (v1.4.0), `CLAUDE.md`, `CONTRIBUTING.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 2 |
| **Total** | 4 |

Coverage gate: PASS (0 modules below threshold, threshold = 80%). Global coverage 96.97%; all four CI gates (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest`) green locally — 1175 passed, 1 skipped.

## 2. Conventions Compliance Matrix

### `.specify/memory/constitution.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle … Binary stores … forbidden as canonical storage" | constitution.md:62-66 | layout | PASS | Only writes are two derived, gitignored caches: `bible/graph.ttl` (Turtle) and `.bookwright/cache/status.json` (JSON, write-only, never read back — pinned by `test_failure_leaves_the_previous_cache_untouched`) |
| "Introducing an additional runtime dependency requires an amendment" | constitution.md:78-80 | dependency | PASS | `pyproject.toml` / `uv.lock` not in the diff; new code imports only the locked set |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | constitution.md:86-89 | layout | PASS | All 11 source files under `src/bookwright/`, all 9 test files under `tests/` |
| "Each CLI subcommand MUST live in its own module … No source file (production or test) may exceed 500 lines" | constitution.md:97-100 | module-size | PASS | One verb, one module (`commands/status.py`, 268 lines); max changed file is `io/research.py` at 492 — no file exceeds 500 |
| "a file approaching the limit MUST be decomposed before the limit is reached, not after" | constitution.md:99-100 | module-size | **FAIL** | `io/research.py` at 492/500 (+67 on this branch) and `tests/io/test_research.py` at 483/500 (+54) — both now "approaching"; see R1 |
| "Integrations MUST be … `SkillsIntegration` registered in `INTEGRATION_REGISTRY`" | constitution.md:108-110 | plugin-shape | N/A | No integration surface touched by this branch |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" | constitution.md:121-124 | directory-ban | PASS | No skill or command-directory writes anywhere in the diff (021–022 consume status; out of 020 scope per spec) |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" | constitution.md:133-141 | frontmatter-constraint | N/A | No SKILL.md generated in this iteration |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | constitution.md:149-150 | coverage-threshold | PASS | 96.97% global; new modules: `status/model.py` 100%, `status/queries.py` 97.59%, `status/rules.py` 98.31%, `commands/status.py` 94.57%, `commands/_graph.py` 100% |
| "CI MUST run pytest, ruff, and mypy strict on every push" | constitution.md:163-164 | workflow-step | PASS | All four gates run green locally (CI config untouched) |
| "MUST accept a `--json` flag and … emit a single well-formed JSON document on stdout and nothing else" | constitution.md:171-173 | io-contract | PASS | `test_json_stdout_is_one_document_with_the_contract_keys`; human prose via `rich.Console` to stdout only in human mode; errors exit 2/3/4 with the iteration-018 envelope (`test_status_errors.py` covers every contract row with `graph build` as parity oracle) |
| "Exit codes MUST be non-zero on error even when `--json` is set" | constitution.md:175-176 | io-contract | PASS | Exit 2/3/4 asserted alongside envelope codes in `test_status_errors.py` |
| "Section 16 … decisions that are closed … MUST NOT be reopened" | constitution.md:184-192 | scope-ban | PASS | rdflib via the `Indexer` seam only (`status/queries.py` imports no rdflib); ontology untouched — authored ids deliberately stay out of the graph (research.md D2) |
| "deferred … MUST NOT be pulled into the current line … cancelled … MUST NOT be implemented at all" | constitution.md:222-231 | scope-ban | PASS | No vector-search, export, preset, Grafeo, or extension plumbing; every refactor (`_graph.py` extraction, predicate extraction, identity records) is consumed by 020's own code |

### `CLAUDE.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "do **not** add `--cov-fail-under` anywhere; one source, no drift" | CLAUDE.md (Common commands) | coverage-threshold | PASS | String absent from the diff |
| "Every source file ≤ 500 lines, one CLI subcommand per module" | CLAUDE.md (Stack) | module-size | PASS | Duplicate of constitution IV hard limit — same evidence |
| "Every serializable error … subclasses it and defines **no** per-class serializer" | CLAUDE.md (Architecture, errors.py) | plugin-shape | PASS | `_NoProjectError` / `_SkippedSourcesError` subclass `BookwrightError`, both rely on the inherited `to_json()` |
| "docs/ site are **Spanish** … Source code, identifiers, commit messages … are **English**" | CLAUDE.md (Language conventions) | other | PASS | `docs/commands/status.md` is Spanish; all code/comments/specs English |
| "Don't modify Spec Kit *core* (templates, scripts, manifests)" | CLAUDE.md (Spec Kit specifics) | directory-ban | PASS | Only `.specify/feature.json` changed — workflow state, not core; templates/scripts untouched |
| "Every iteration runs this fixed sequence — do not skip steps" | CLAUDE.md (How work is done) | workflow-step | PASS | See workflow trail below |

### `CONTRIBUTING.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Forbidden in source/tests … `US-x` / `+USx` … `T0xx`" | CONTRIBUTING.md:58-61 | directory-ban | PASS | Grep over all 14 changed source/test files: zero matches |
| "Allowed in source/tests: `FR-0xx` / `SC-0xx` … `D-x` … prefer pairing the ref with the reason" | CONTRIBUTING.md:51-73 | other | PASS | Spot-checked: refs consistently paired with the reason (e.g. `status.py:141`, `rules.py` docstrings) |

### Track integrity (Pass A.3)

`git status --porcelain` is empty: no untracked, unstaged, or staged-only files anywhere. All 8 files in `specs/020-status-command/` (spec, plan, tasks, research, data-model, quickstart, contracts/cli-status, checklists/requirements) appear in the branch diff. `.claude/skills/` and `.specify/` carry no orphaned files. **PASS.**

### Workflow trail (Pass A.4)

specify → `spec.md` ✅; clarify → `## Clarifications / Session 2026-06-11` with 5 resolved questions ✅; plan → `plan.md` + research/data-model/contracts/quickstart ✅; tasks → `tasks.md`, 29/29 checked ✅; analyze → two remediation commits (`156013c`, `047d868`) ✅; implement → source + tests (`b234c2a`) ✅. **PASS — no step skipped.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | HIGH | src/bookwright/io/research.py:1 (492 lines), tests/io/test_research.py:1 (483 lines) | Both files now sit within 2% of the 500-line ceiling; Constitution IV requires decomposition *before* the limit is reached, and this branch added the lines that put them there (+67/+54) | Extract `FindingIdentity`/`AnchorIdentity`/`_constrains_identity` into `io/_research_identity.py` (mirrors the 019 `_focus_block.py` precedent); move the identity-record tests into `tests/io/test_research_identity.py` |
| R2 | B | MEDIUM | src/bookwright/commands/status.py:164, src/bookwright/status/rules.py:150 | Degraded path builds `ValidationSummary(counts={})`; rule ④'s predicate `counts["error"] > 0` would `KeyError` on it — safe today only because `bootstrap_graph` short-circuits first (rules.py:173-174), an implicit ordering invariant | Zero-fill the degraded summary at construction (`{level.value: 0 for level in Severity}`) or make the predicate `counts.get("error", 0) > 0`, so rule correctness no longer depends on table position |
| R3 | B | LOW | src/bookwright/commands/status.py:156, src/bookwright/commands/_graph.py:58-61 | The build-prerequisite predicate (bible dir present ∧ manuscript present) is spelled twice; if the pipeline ever gains a prerequisite, `status`'s degrade check silently diverges (exit 2 instead of degraded exit 0) | Two occurrences — below the DRY threshold, note only. If touched again, expose `prerequisites_present(root, manifest)` from `_graph.py` and use it in both places |
| R4 | D | LOW | src/bookwright/status/queries.py:154 | The `continue` for an anchor URI with no authored identity is the only uncovered line in the new subpackage | One test passing an empty `identities` tuple to `anchor_gaps` over a non-empty graph pins it |

## 4. Remediation Detail

### R1 — `io/research.py` and its test file are 8/17 lines from the 500-line ceiling

- **Where:** `src/bookwright/io/research.py` (492 lines), `tests/io/test_research.py` (483 lines)
- **Why it matters:** Constitution IV is explicit: "a file approaching the limit MUST be decomposed before the limit is reached, not after." The hard limit is not yet violated, but this branch added 67/54 lines to files that were already large; the *next* touch of either file (iteration 021 consumes the identity records) will almost certainly breach the hard limit mid-iteration, forcing an unplanned refactor under worse conditions.
- **Suggested change:** Move `FindingIdentity`, `AnchorIdentity`, and `_constrains_identity` into a new `src/bookwright/io/_research_identity.py` and re-export from `io/research.py` — the exact pattern iteration 019 used when `manifest.py` approached the ceiling (`core/_focus_block.py`). Split the six identity-record tests (the "Authored identity records" section) into `tests/io/test_research_identity.py`. Pure file moves; no behavior change, no envelope or contract impact.

### R2 — Degraded-path `ValidationSummary` relies on the rule table's short-circuit to avoid a `KeyError`

- **Where:** `src/bookwright/commands/status.py:164` (constructs `ValidationSummary(counts={}, ran=())`), `src/bookwright/status/rules.py:150` (`s.validation.counts["error"] > 0`)
- **Why it matters:** Today `next_actions` never evaluates rule ④ on the degraded state because `bootstrap_graph` returns early. But that makes rule ④'s predicate correct only *by table position* — reordering `RULES`, evaluating a predicate directly (as `test_every_rule_is_exercised_by_a_synthetic_state` does, just never with empty counts), or constructing a degraded-shaped state elsewhere raises `KeyError` instead of `False`. `ValidationSummary.to_payload()` already zero-fills defensively, which shows the model knows the dict can be incomplete — the predicate is the one consumer that doesn't.
- **Suggested change:** In `_aggregate`'s degraded branch, build `ValidationSummary(counts={level.value: 0 for level in Severity}, ran=())` (one import already available in `queries.py`'s pattern). Alternatively change the rule ④ lambda to `s.validation.counts.get("error", 0) > 0`. Either is a two-line, test-neutral fix; the first also lets `to_payload`'s zero-fill compensation become a pure ordering guarantee.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/commands/status.py | 94.57% | 80% | PASS |
| src/bookwright/commands/_graph.py | 100.00% | 80% | PASS |
| src/bookwright/commands/_envelope.py | 100.00% | 80% | PASS |
| src/bookwright/commands/graph/build.py | 85.07% | 80% | PASS |
| src/bookwright/status/model.py | 100.00% | 80% | PASS |
| src/bookwright/status/queries.py | 97.59% | 80% | PASS |
| src/bookwright/status/rules.py | 98.31% | 80% | PASS |
| src/bookwright/io/research.py | 96.99% | 80% | PASS |
| src/bookwright/validation/validators/factual_anchor.py | 100.00% | 80% | PASS |
| **Global** | **96.97%** | 80% | **PASS** |

## 6. Inability-to-verify notes

- **TDD signal:** implementation and tests landed in the same commit (`b234c2a`, the Spec Kit implementation commit), so commit-order analysis cannot distinguish test-first from test-after. Neutral — the spec-driven flow defines tests in `tasks.md` before implementation.
- **Security pass:** no shell, `eval`/`exec`, pickle, unsafe `yaml.load`, subprocess, or secret-shaped strings anywhere in the changed source (grep-verified). The only filesystem writes use fixed, manifest-derived paths under the project root; no user-controlled path joins were introduced. Nothing to flag.
- **Patterns pass:** no findings — the registry-style `RULES` table, the `Indexer` seam, and the extracted pure predicates are all exactly the shapes the conventions mandate; no singleton/factory/observer misuse observed.
