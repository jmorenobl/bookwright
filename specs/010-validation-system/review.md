# Quality Audit — 010-validation-system

**Scope:** changed files vs `main` (30 under `src/` + `tests/`)
**Commit range:** main..d619f7c
**Date:** 2026-06-03
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.2.0), `CONTRIBUTING.md`, `README.md`

> **Update (post-`/simplify`, commit `d619f7c`):** the two LOW findings R1 and R2
> below were resolved — a single `split_source` parser now owns the `relpath:line`
> grammar, and a single `TEMPORAL_RELATIONS` table is the source of truth for the five
> relations (the `included_in`/`included-in` key fork is gone). R3 remains open by
> design (contract-conformant). Gates re-verified green: 829 passed, coverage 96.30%,
> `mypy --strict` + `ruff` clean.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 1 (was 3; R1, R2 resolved in `d619f7c`) |
| **Total** | 1 open |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%). Total line coverage 96.30%; every changed module ≥ 89%.
CI gates (read-only re-run): `ruff check` ✓, `ruff format --check` ✓, `mypy --strict` ✓ (180 files), `pytest` ✓ (829 passed, 1 skipped).

This branch is in excellent shape. No CRITICAL or HIGH findings. The three LOW items are micro-DRY / cosmetic observations, not blockers.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Plain Text as Source of Truth … Binary stores, opaque caches, … forbidden as canonical storage" | `constitution.md:45` | layout | PASS | Validation is in-memory only (FR-020); `base.py:3` "subsystem persists nothing". No binary artifacts in diff. |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | `constitution.md:64` | dependency | PASS | `pyproject.toml` not in diff; subsystem reuses `rdflib`/`typer`/`rich` only. No new deps. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:72` | layout | PASS | All 16 changed source files under `src/bookwright/`; all 14 test files under `tests/`. |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`" | `constitution.md:83` | layout | PASS | `commands/validate.py` is the sole subcommand module; `cli.py` only registers it. |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:84` | module-size | PASS | Largest changed file `io/bible.py` = 483; all others ≤ 281. |
| "Monolithic `cli.py` files that inline subcommand bodies are prohibited" | `constitution.md:87` | plugin-shape | PASS | `cli.py:18` only wires `validate.run`; body lives in the module. |
| "Integrations MUST be implemented as subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`" | `constitution.md:94` | plugin-shape | N/A | No integration code touched on this branch. |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" | `constitution.md:106` | directory-ban | PASS | No writes to any `*/commands/` directory in the diff. |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" | `constitution.md:119` | frontmatter-constraint | N/A | No `SKILL.md` generated on this branch. |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:135` | coverage-threshold | PASS | 96.30% total; all changed modules ≥ 89% (see §5). |
| "Any CLI command … MUST accept a `--json` flag and … emit a single well-formed JSON document on stdout and nothing else" | `constitution.md:148` | io-contract | PASS | `validate.py:78-83` — JSON path calls only `_emit_json` (stdout); human render only in the non-JSON branch; prose/errors to stderr (`_emit_error:157`). |
| "Exit codes MUST be non-zero on error even when `--json` is set" | `constitution.md:153` | io-contract | PASS | `validate.py:83` exit 1 on gate; `:76` exit 2 on usage error, independent of `--json`. |
| "rdflib over Grafeo in v0; GOLEM as the ontology; no shell scripts; Agent Skills only" | `constitution.md:159` | scope-ban | PASS | Temporal queries go through the `Indexer`/rdflib seam (`queries.py`); GOLEM TR/CSM namespaces added; no shell scripts. |
| "Extension system (distributable validators, pre-commit hooks) — v0.5 … MUST NOT be pulled into v0 scope" | `constitution.md:203` | scope-ban | PASS | Custom validators are **project-local** file discovery (FR-005, in scope); the *distribution* mechanism is explicitly avoided — `registry.py:6` "no `entry_points` (research D2)". Sandboxing/trust is explicitly out of scope per `spec.md:405`. |
| "v0 line ships exactly the M0–M3 milestones … Speculative generality is treated as a violation" | `constitution.md:195` | scope-ban | PASS | Iteration 11 (M3); every type maps to an FR/SC/D reference. No speculative plumbing. |
| Traceability tags allowed (`FR-0xx`/`SC-0xx`/`D-x`/`design §`); `US-x`/`T0xx` forbidden in source | `CONTRIBUTING.md:51-62` | other | PASS | grep of changed source shows only allowed tags (`FR-0xx`, `D8`/`D11`/`D12`, `SC-003`). No `US-`/`T0` tags. |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| ~~R1~~ | B | LOW | base.py, report.py, queries.py | ~~The `source` `:line`-suffix split is hand-rolled in 4 places~~ | **Resolved in `d619f7c`** — `base.split_source()` is now the single parser; `Violation.source_file/source_line`, `ScopeFilter.matches`, and `resolve_source` route through it; `_has_line` deleted. |
| ~~R2~~ | A/C | LOW | namespaces.py, event.py, queries.py, temporal.py, bible.py | ~~The five `TR:*` relations are enumerated in 4 representations across modules~~ | **Resolved in `d619f7c`** — `TEMPORAL_RELATIONS` in `golem.namespaces` is now the single source of truth; `cross_refs`, `RELATION_KEYS`, `load_relations`, and `_PRED` all derive from it; the `included_in`/`included-in` key fork is eliminated. |
| R3 | D | LOW | validate.py:118-131 | A corrupt/unparseable `graph.ttl` is surfaced with `code:"invalid_manifest"`, which can mislead (the manifest may be fine) | **Open (by design)** — contract-conformant: `cli-validate.md:92` allows exactly four codes, so reuse is forced. Optionally clarify the *message* to name the graph file. |

## 4. Remediation Detail

No CRITICAL or HIGH findings — nothing in this section is blocking. The LOW items above are optional polish; full file-local detail is inline in the table.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| validation/runner.py | 100% | 80% | PASS |
| validation/__init__.py | 100% | 80% | PASS |
| validation/base.py | 95% | 80% | PASS |
| validation/registry.py | 92% | 80% | PASS |
| validation/report.py | 92% | 80% | PASS |
| validation/queries.py | 89% | 80% | PASS |
| validation/validators/character_presence.py | 99% | 80% | PASS |
| validation/validators/temporal.py | 94% | 80% | PASS |
| validation/validators/focalization.py | 92% | 80% | PASS |
| validation/validators/setting_continuity.py | 97% | 80% | PASS |
| golem/modules/event.py | 100% | 80% | PASS |
| golem/namespaces.py | 100% | 80% | PASS |
| io/bible.py | 92% | 80% | PASS |
| commands/validate.py | (covered by tests/validation/test_command.py, 16 tests) | 80% | PASS |
| **TOTAL** | **96.30%** | 80% | PASS |

## 6. Inability-to-verify notes

- **TDD ordering (Pass D heuristic):** this branch's history is squashed into progress commits, so per-file `git log` ordering of impl-vs-test cannot establish TDD discipline. Coverage (96%) and direct (mock-free) validator exercising are strong positive signals; the ordering itself is unverifiable.
- **`io/frontmatter.py` YAML safety:** the bible loader catches `yaml.YAMLError` and relies on `parse_frontmatter` (unchanged, outside this diff) for safe loading. Confirmed in scope here only that `bible.py` adds no unsafe `yaml.load`; the underlying parser was not re-audited.
- **Track integrity (A.3):** working tree clean; all `specs/010-validation-system/` and `src/bookwright/validation/` files are tracked and in the branch diff. PASS.
- **Workflow trail (A.4):** full Spec Kit trail present — `spec.md`, `clarify` (requirements checklist), `plan.md`, `tasks.md`, analyze (commit `4bf6b83`/`32ad5fc`), and implementation source. No broken step.
