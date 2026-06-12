# Quality Audit — 020-status-command

**Scope:** 37 changed files vs main
**Commit range:** main..1759b10
**Date:** 2026-06-12
**Conventions discovered:** `.specify/memory/constitution.md` (v1.4.0), `CLAUDE.md`, `CONTRIBUTING.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 4 |
| **Total** | 5 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%). Total: 96.98%, 1175 passed / 0 failed. All four CI gates verified locally: `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` — green.

The HIGH finding from the previous audit (b234c2a) — `io/research.py` at 492/500 lines — was remediated by extracting `io/_research_identity.py` (research.py now 457 lines) and is confirmed closed.

## 2. Conventions Compliance Matrix

### `.specify/memory/constitution.md` (v1.4.0)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle … Derived caches MAY exist … deterministically rebuildable" | constitution.md:59-66 | layout | PASS | `.bookwright/cache/status.json` is plain JSON, write-only, regenerated per run; byte-determinism pinned by `test_double_run_is_byte_identical_and_stdout_equals_cache` |
| "Introducing an additional runtime dependency requires an amendment" | constitution.md:78-80 | dependency | PASS | `pyproject.toml` not in diff; no new imports outside the locked stack |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | constitution.md:86-89 | layout | PASS | All 16 source/test files in diff under the two roots |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`" | constitution.md:97-98 | layout | PASS | `commands/status.py` registered in `cli.py:17`; domain logic split into `status/{model,queries,rules}.py` |
| "No source file (production or test) may exceed 500 lines" | constitution.md:99-100 | module-size | PASS | Largest changed: `io/research.py` 457, `tests/validation/test_factual_anchor.py` 474 — both under; prior-audit HIGH remediated |
| "Integrations MUST be … registered in `INTEGRATION_REGISTRY` … monolithic dispatcher … forbidden" | constitution.md:108-113 | plugin-shape | N/A | No integration code in this diff |
| "Writing to `.claude/commands/` … or any analogous … directory is prohibited" | constitution.md:121-124 | directory-ban | PASS | Grep over diff: no writes/references to banned directories |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" | constitution.md:133-141 | frontmatter-constraint | N/A | No SKILL.md generated in this iteration (skills consuming `status` are 021–022) |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | constitution.md:149-150 | coverage-threshold | PASS | 96.98% total; lowest changed module `commands/graph/build.py` 85.07% (see § 5) |
| "CI MUST run pytest, ruff, and mypy strict on every push" | constitution.md:163-164 | workflow-step | PASS | All four gates run locally during this audit: green |
| "MUST … emit a single well-formed JSON document on stdout and nothing else … prose … to stderr … non-zero on error" | constitution.md:171-177 | io-contract | PASS | `test_json_stdout_is_one_document_with_the_contract_keys`, `test_not_a_project_human_mode_keeps_stdout_empty`; error exits 2/3/4 with envelope |
| "Section 16 … decisions that are closed … MUST NOT be reopened" | constitution.md:184-192 | scope-ban | PASS | rdflib via the `Indexer` protocol only; no Grafeo/preset/extension symbols in diff |
| "Vector search … v0.4 / Export … v1.0 … MUST NOT be pulled into the current line" | constitution.md:222-226 | scope-ban | PASS | Grep over diff for chroma/epub/pandoc/grafeo/preset: no hits |
| "plumbing whose only justification is 'future X' MUST be rejected" | constitution.md:235-238 | scope-ban | PASS | `ok_payload` docstring explicitly *defers* migrating existing call sites rather than pulling them in — the right direction |

### `CLAUDE.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "do **not** add `--cov-fail-under` anywhere; one source, no drift" | CLAUDE.md (Common commands) | coverage-threshold | PASS | Single `fail_under = 80` at pyproject.toml:122; no `--cov-fail-under` in repo |
| "Don't modify Spec Kit *core* (templates, scripts, manifests)" | CLAUDE.md (Spec Kit specifics) | directory-ban | PASS | Only `.specify/feature.json` (workflow state pointer) changed — per-project state, not core |
| Fixed iteration sequence `/speckit-specify → clarify → plan → tasks → analyze → implement` | CLAUDE.md (How work is done) | workflow-step | PASS | Trail complete: spec.md (with `## Clarifications`, session 2026-06-11), plan.md, tasks.md, analyze-remediation commits (047d868, aadeba9), implementation |
| "docs/ site are **Spanish** … Source code, identifiers, commit messages … **English**" | CLAUDE.md (Language conventions) | other | PASS | `docs/commands/status.md` in Spanish; all code/comments/commits English |
| "Every source file ≤ 500 lines, one CLI subcommand per module" | CLAUDE.md (Stack) | module-size | PASS | Duplicate of Constitution IV row — same evidence |

### `CONTRIBUTING.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Forbidden in source/tests … `US-x` / `+USx` … `T0xx` — task IDs" | CONTRIBUTING.md:58-61 | other | PASS | Grep over diff: no forbidden tags; FR/SC/D refs used correctly with reasons attached |
| "The `validate` method MUST be deterministic and MUST NOT write to disk or mutate the graph" | CONTRIBUTING.md:120-122 | io-contract | N/A | No custom validator authored; `status` consumes the runner read-only |

**Track integrity (A.3):** working tree clean; every file in `specs/020-status-command/`, `docs/`, and `.specify/` on disk is either in the branch diff or inherited from main. The only ignored file in governance directories is `.claude/settings.local.json` (intentionally local). No uncommitted/untracked governance artifacts.

**Workflow trail (A.4):** all six step artifacts present, in order. No broken trail.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | MEDIUM | src/bookwright/commands/status.py:152, src/bookwright/commands/_graph.py:58-61 | The degraded-path predicate (`bible_dir.is_dir() and manuscript_present(...)`) re-states `build_project_graph`'s raise conditions; if the pipeline gains a prerequisite, `status` exits 2 instead of degrading (D5 drift) | Extract a `prerequisites_present(root, manifest) -> bool` helper in `_graph.py` consumed by both sites |
| R2 | B | LOW | src/bookwright/status/rules.py:173 | `if rule.name == "bootstrap_graph"` — the short-circuit is keyed by a magic string; renaming the rule silently disables D5 | Add a `terminal: bool = False` field to `Rule` and check `rule.terminal` (the exact-match tests would catch drift, so LOW) |
| R3 | B | LOW | src/bookwright/commands/status.py:72-73 | `EXIT_COLLISION = 3` / `EXIT_SKIPPED = 4` re-declare literals already owned by `commands/graph/build.py:31` and `io/report.py:15` — two sites each, at the DRY threshold's edge given the per-corpus exit-parity contract (D4) | Import the literals from their owning modules (matches the `_envelope.EXIT_CONFIG` single-sourcing pattern this branch itself established) |
| R4 | D | LOW | src/bookwright/validation/registry.py:90-96 | `_load_custom_module` executes arbitrary project-local Python from `.bookwright/validators/` — flagged per the dynamic-code checklist; it is the documented extension point (CONTRIBUTING.md:117-122) with conftest.py-equivalent trust, so accepted by design | No change needed; keep the trust boundary documented where it is |
| R5 | B | LOW | src/bookwright/commands/validate.py:117 | `_load_indexer(...) -> Any` weakens typing where the `Indexer` protocol exists; `mypy --strict` passes but call sites lose checking | Annotate `-> Indexer` (pre-existing signature, touched file) |

## 4. Remediation Detail

No CRITICAL or HIGH findings. The one MEDIUM, for context:

### R1 — Degraded-path predicate can drift from the pipeline's prerequisites

- **Where:** `src/bookwright/commands/status.py:152` vs `src/bookwright/commands/_graph.py:58-61`
- **Why it matters:** research D5 defines "degraded" as *exactly* the states where `build_project_graph` would raise `MissingDirectoryError`. That equivalence is currently maintained by hand in two files. A future prerequisite added to the pipeline (e.g. a research-dir precondition) would make `status` fail with exit 2 on a corpus the spec says must degrade to exit 0 — a silent contract break that only an integration test on the new prerequisite would catch.
- **Suggested change:** add `def prerequisites_present(root: Path, manifest: Manifest) -> bool` to `_graph.py` returning `bible_dir.is_dir() and manuscript_present(manuscript_dir)`; have `build_project_graph` raise when it is false and `_aggregate` branch on it. One predicate, two consumers, no drift. Fits naturally in 021+ housekeeping; not blocking for this merge.

## 5. Coverage Detail

Changed source modules only (threshold 80%):

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/cli.py | 100.00% | 80% | PASS |
| src/bookwright/commands/_envelope.py | 100.00% | 80% | PASS |
| src/bookwright/commands/_graph.py | 100.00% | 80% | PASS |
| src/bookwright/commands/graph/build.py | 85.07% | 80% | PASS |
| src/bookwright/commands/status.py | 94.44% | 80% | PASS |
| src/bookwright/commands/validate.py | 90.36% | 80% | PASS |
| src/bookwright/io/_research_identity.py | 100.00% | 80% | PASS |
| src/bookwright/io/research.py | 96.84% | 80% | PASS |
| src/bookwright/status/__init__.py | 100.00% | 80% | PASS |
| src/bookwright/status/model.py | 100.00% | 80% | PASS |
| src/bookwright/status/queries.py | 97.65% | 80% | PASS |
| src/bookwright/status/rules.py | 98.31% | 80% | PASS |
| src/bookwright/validation/registry.py | 92.31% | 80% | PASS |
| src/bookwright/validation/validators/factual_anchor.py | 100.00% | 80% | PASS |

**Test quality:** notably strong. Exact-match pins on every rule-table prompt (test_rules.py), byte-identity and corpus-immutability proofs via sha256 (test_status.py), parity oracles cross-checking `status` against `graph build` exit codes and `validate`/`focus show` payloads, and a predicate↔validator parity matrix guarding the D3 extraction. No test smells found: assertions are on values, names describe conditions, no mock-count-only assertions, no interdependence.

**Security at boundaries:** YAML via `yaml.safe_load` only (frontmatter.py:50); `--scope` resolution validates containment under the project root (validate.py:133-145); cache writes confined to `<root>/.bookwright/cache/`; no `eval`/`exec`/`shell=True`/secrets in the diff. R4 documents the one sanctioned dynamic-import surface.

## 6. Inability-to-verify notes

- TDD ordering (Pass D heuristic) is indeterminate: tests and implementation land in the same Spec Kit progress commits (b234c2a), so commit order can't distinguish test-first from test-after. The Spec Kit flow (tasks → implement) governs ordering here; no finding.
- Pass A frontmatter-constraint and plugin-shape rules are N/A on this branch (no SKILL.md generated, no integration touched) — recorded in the matrix, not skipped.
