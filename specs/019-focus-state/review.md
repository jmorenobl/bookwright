# Quality Audit — 019-focus-state

**Scope:** 69 changed files vs main (24 under `src/`+`tests/`, all read in full; remainder are spec artifacts, docs, and the sanctioned Spec Kit v0.10.1 upgrade)
**Commit range:** main..ad454b9
**Date:** 2026-06-11
**Conventions discovered:** `.specify/memory/constitution.md` (v1.4.0), `CLAUDE.md`, `CONTRIBUTING.md`, `~/.claude/CLAUDE.md` (RTK, not code-relevant)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 2 |
| **Total** | 2 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; total 96.88%, every changed module ≥ 93.51%).

All four CI gates verified locally: `ruff check` ✅, `ruff format --check` ✅ (229 files), `mypy --strict` ✅ (228 files), `pytest` ✅ (1103 passed, 1 skipped).

## 2. Conventions Compliance Matrix

### `.specify/memory/constitution.md` (v1.4.0)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle" (Principle I, NON-NEGOTIABLE) | constitution.md:59-66 | io-contract | PASS | `[focus]` lives in `manifest.toml`; `updated_at` stored as string, never coerced, for byte round-trip (`_focus_block.py:55-78`) |
| "Introducing an additional runtime dependency requires an amendment" (Principle II) | constitution.md:78-80 | dependency | PASS | `pyproject.toml` / `uv.lock` untouched on this branch |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" (Principle III) | constitution.md:86-88 | layout | PASS | All 24 src/tests files under the mandated roots |
| "Each CLI subcommand MUST live in its own module … No source file … may exceed 500 lines" (Principle IV) | constitution.md:97-101 | module-size | PASS | `focus/{set,show,clear}.py` are separate modules; largest changed file is `manifest.py` at 395 lines |
| "Integrations MUST be … registered in `INTEGRATION_REGISTRY`" (Principle V) | constitution.md:108-110 | plugin-shape | N/A | No integration code touched |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" (Principle VI, NON-NEGOTIABLE) | constitution.md:121-124 | directory-ban | PASS | No writes/references to any `commands/` skills directory in the diff; `.claude/skills/speckit-*` changes are the pinned Spec Kit upgrade |
| "Every generated SKILL.md MUST satisfy the agentskills.io specification" (Principle VII) | constitution.md:133-141 | frontmatter-constraint | N/A | This iteration generates no skills; touched SKILL.md files are Spec Kit's own (upgrade commit 97a9d79) |
| "v0 MUST hold a minimum of 80% line coverage" (Principle VIII, NON-NEGOTIABLE) | constitution.md:149-150 | coverage-threshold | PASS | 96.88% total; per-module detail in §5 |
| "CI MUST run pytest, ruff, and mypy strict on every push" (Principle VIII) | constitution.md:163-164 | workflow-step | PASS | All four gates run locally, green (T026 also records this) |
| "`--json` … emit a single well-formed JSON document on stdout and nothing else … prose … MUST go to stderr" (Principle IX) | constitution.md:171-175 | io-contract | PASS | `emit_json` writes one compact doc; tests pin `stdout == ""` in human mode and `stderr == ""` under `--json` (`test_set.py:44-58`, `test_show.py:42`) |
| "Exit codes MUST be non-zero on error even when `--json` is set" (Principle IX) | constitution.md:175-177 | io-contract | PASS | All fault paths exit 2; pinned in `test_set.py:102`, `test_show.py:66-74`, `test_clear.py:64-74` |
| "Section 16 … decisions that are closed … MUST NOT be reopened" (Principle X) | constitution.md:184-192 | scope-ban | PASS | No axiom touched; rdflib/GOLEM/plain-text all untouched |
| "Runtime dependencies (minimum set) … Adding … requires a MINOR amendment" | constitution.md:204-207 | dependency | PASS | No dependency changes |
| "Deferred … MUST NOT be pulled into the current line: vector search (v0.4), export (v1.0)" | constitution.md:222-226 | scope-ban | PASS | No ChromaDB/vector/export plumbing in the diff |
| "Cancelled … MUST NOT be implemented at all: preset system, GrafeoIndexer, integrations beyond claude/generic, extensions" | constitution.md:228-233 | scope-ban | PASS | No references to any cancelled capability |
| "plumbing whose only justification is 'future X' MUST be rejected" | constitution.md:235-238 | scope-ban | PASS | `[focus]` + `bookwright focus` is exactly iteration 019 of the active M5/v0.3 line; no `status`/`next_actions` (020+) implemented ahead |

### `CLAUDE.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "do **not** add `--cov-fail-under` anywhere; one source, no drift" | CLAUDE.md (Common commands) | coverage-threshold | PASS | No occurrence in the diff |
| "Every feature lands through a numbered iteration … fixed sequence — do not skip steps" | CLAUDE.md (How work is done) | workflow-step | PASS | See workflow-trail check below |
| "Don't modify Spec Kit *core* (templates, scripts, manifests)" | CLAUDE.md (Spec Kit specifics) | directory-ban | PASS | `.specify/` changes come from the sanctioned v0.8.16→v0.10.1 upgrade (97a9d79); CLAUDE.md pin updated in the same change |
| "design docs, README, docs/ site are **Spanish** … Source code, identifiers, commits are **English**" | CLAUDE.md (Language conventions) | other | PASS | `docs/commands/focus-*.md` and `bookwright-design.md §8.1` additions in Spanish; code/commits English |
| "Merge to `main` only when tests are green and `/speckit-analyze` reports no issues" | CLAUDE.md (How work is done) | workflow-step | PASS | Gates green; analyze ran (constitution v1.4.0 Sync Impact Report cites its finding C1 on this iteration) |

### `CONTRIBUTING.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Forbidden in source/tests … `US-x` / `+USx` … `T0xx`" | CONTRIBUTING.md:58-61 | other | PASS | grep over all changed src/tests files: zero hits (US tags appear only in `tasks.md`, where they belong) |
| "Prefer pairing the ref with the reason, not a bare pointer" | CONTRIBUTING.md:71-74 | other | PASS | All FR/SC/D refs in the new code carry the reason (e.g. `_focus_block.py:43`, `set.py:53`) |

### Track integrity (Pass A.3)

Working tree is clean (`git status --porcelain` empty). Every file in `specs/019-focus-state/` (spec, plan, tasks, research, data-model, quickstart, contracts/, checklists/requirements.md) appears in the branch diff — properly tracked. No uncommitted or untracked governance artifacts. **PASS.**

### Workflow trail (Pass A.4)

`specify→spec.md` ✅ (commit 846f32d) → `clarify` ✅ (e469be2) → `plan→plan.md` ✅ (192aaac) → `tasks→tasks.md` ✅ (192aaac) → `analyze` ✅ (evidenced by constitution v1.4.0 Sync Impact Report: "Surfaced by /speckit-analyze on iteration 019-focus-state (finding C1)") → `implement` ✅ (ad454b9; T001–T026 all checked in tasks.md). Trail intact, in order. **PASS.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | LOW | src/bookwright/commands/focus/set.py:25 | `EXIT_CONFIG = 2` re-declared though `focus/_project.py:23` (same package, already imported) defines it; sixth repo-wide copy of the literal | `from ._project import EXIT_CONFIG` in `set.py`; optionally hoist the shared exit code into `commands/_envelope.py` in a later cleanup |
| R2 | B | LOW | src/bookwright/commands/_envelope.py:40-43 | Docstring claims the `INVALID_MANIFEST_CODE` constant covers "the two remap sites … cannot drift", but `commands/validate.py:126,133` (pre-existing on main, outside this diff) still hand-code `"invalid_manifest"` | Replace the two literals in `validate.py` with `INVALID_MANIFEST_CODE`, or soften the docstring claim; either is a one-line follow-up |

No CRITICAL, HIGH, or MEDIUM findings. No security findings: the diff contains no subprocess/eval/pickle/yaml.load, no path joins from user input outside the project root (paths derive from `find_project_root()`), and all external input (`--target`, `--notes`, manifest bytes) crosses the boundary through strict Pydantic validation with a pre-write CLI guard (`set.py:46-49`).

## 4. Remediation Detail

No CRITICAL or HIGH findings — nothing blocks merge.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/cli.py | 100.00% | 80% | PASS |
| src/bookwright/commands/_envelope.py | 100.00% | 80% | PASS |
| src/bookwright/commands/focus/__init__.py | 100.00% | 80% | PASS |
| src/bookwright/commands/focus/_project.py | 100.00% | 80% | PASS |
| src/bookwright/commands/focus/clear.py | 100.00% | 80% | PASS |
| src/bookwright/commands/focus/errors.py | 100.00% | 80% | PASS |
| src/bookwright/commands/focus/set.py | 96.77% | 80% | PASS |
| src/bookwright/commands/focus/show.py | 100.00% | 80% | PASS |
| src/bookwright/commands/graph/build.py | 93.51% | 80% | PASS |
| src/bookwright/commands/graph/query.py | 96.30% | 80% | PASS |
| src/bookwright/core/__init__.py | 100.00% | 80% | PASS |
| src/bookwright/core/_focus_block.py | 100.00% | 80% | PASS |
| src/bookwright/core/manifest.py | 97.16% | 80% | PASS |
| **TOTAL (suite)** | **96.88%** | **80%** | **PASS** |

The single missed line in `focus/set.py` is line 30 — the real-clock body of `_today()`, the documented test seam (research D5) that tests monkey-patch for determinism. Expected and acceptable.

## 6. Inability-to-verify notes

- **TDD signal (heuristic):** the implementation landed as a single commit (ad454b9 "[Spec Kit] Implementation progress"), so the tests-before-implementation git-history heuristic cannot distinguish ordering. tasks.md sequences tests before implementation per story (T010/T011 before T012-T014, etc.), consistent with the intended order.
- **`/speckit-analyze` output:** the analyze artifact itself is not persisted as a file; its execution is evidenced indirectly through the constitution v1.4.0 Sync Impact Report citing finding C1 from this iteration.
