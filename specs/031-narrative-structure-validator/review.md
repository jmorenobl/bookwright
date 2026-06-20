# Quality Audit — 031-narrative-structure-validator

**Scope:** 8 changed files vs main (validator + accessor + query + tests)
**Commit range:** main..ec69ce3 (+ uncommitted working tree)
**Date:** 2026-06-20
**Conventions discovered:** CLAUDE.md, .specify/memory/constitution.md (v1.4.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 0 |
| **Total** | 3 |

Coverage gate: PASS (narrative_structure.py 100% line; threshold = 80%). NOTE: a
reachable conditional-expression branch is unmeasured (R2) — line coverage hides it.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "The graph is ALWAYS a derived cache … never the source" | constitution Principle I | io-contract | PASS | Validator + `outline()` are read-only; `test_deterministic_and_read_only` asserts `indexer.count()` unchanged |
| "Agent Skills only — never write to `.claude/commands/`" | constitution Principle VI | directory-ban | PASS | No skill/commands writes in diff |
| "≥80% coverage, single-sourced `fail_under`" | constitution Principle VIII | coverage-threshold | PASS | 97.31% total; no `--cov-fail-under` added |
| "Every source file ≤ 500 lines" | constitution Principle IV | module-size | PASS | max changed src 256 (base.py); validator 102 |
| "one CLI subcommand per module" | constitution Principle IV | layout | N/A | No new CLI verb (validator is registry-discovered) |
| "any agent-consumed subcommand … single JSON document on stdout" | constitution Principle IX | io-contract | PASS | Findings flow through existing `validate --json` envelope; `test_…_json_envelope` asserts no new top-level key, no stderr JSON leak |
| "ontology is frozen — `golem.ttl` must not gain classes" | constitution Principle X | scope-ban | PASS | No ontology change; reuses `G7`/`G9`/`dlp:proper-part` |
| "auto-discovered by `pkgutil` scan, no hand-registration" | CLAUDE.md / plan | plugin-shape | PASS | `test_in_default_active_set` confirms discovery |
| "do NOT implement ahead of the plan" | CLAUDE.md scope discipline | scope-ban | PASS | Two rules only (a, c); rule b deliberately omitted per spec |

Track-integrity (A.3): the two new untracked files
(`src/bookwright/validation/validators/narrative_structure.py`,
`tests/validation/test_narrative_structure.py`) are working-tree-only and will be
committed by this review step's final commit — expected mid-iteration state, not a
governance leak. Workflow trail (A.4): spec.md → plan.md → tasks.md → code all present.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | D | HIGH | narrative_structure.py:89 | Reachable `else ref.path` fallback (stale/absent `graph.ttl` → `resolve_source`→None) has no test; 100% line coverage hides it | Add a Rule-c test driving an empty `RdflibIndexer`, asserting `source == card relpath` |
| R2 | B | MEDIUM | narrative_structure.py:79-80 | Dead guard: `unit_uris.get(ref.entity)` cannot be None (index + refs share one `MapResult`) — `if unit_uri is not None else None` is unreachable | Subscript `unit_uris[ref.entity]` and drop the guard; trust the invariant |
| R3 | B | MEDIUM | conftest.py:225-253 | DRY: `build_outline_indexer`/`build_and_save_outline_graph` duplicate `build_indexer`/`build_and_save_graph` byte-for-byte but one `map_outline` line | Parameterize `build_indexer(root, *, outline=False)` + `build_and_save_graph(root, *, outline=False)` |

## 4. Remediation Detail

### R1 — Untested reachable stale-graph fallback
- **Where:** `src/bookwright/validation/validators/narrative_structure.py:89`
- **Why it matters:** `validate` loads on-disk `graph.ttl` (`commands/validate.py:_load_indexer`); when it is stale or absent, `resolve_source` returns None and the finding falls back to `ref.path`. That branch is the validator's only degraded-location path and no test exercises it — and `coverage.py` reports 100% because the branch lives in a conditional *expression*, not an `if`.
- **Suggested change:** add `test_unresolved_role_stale_graph_falls_back_to_card_path` running `NarrativeStructure().validate(load_context(root), RdflibIndexer())` and asserting `finding.source == "outline/units/opening.md"`.

### R2 — Unreachable None-guard on the unit URI
- **Where:** `src/bookwright/validation/validators/narrative_structure.py:79-80`
- **Why it matters:** `_unit_uri_index` and `outline.unresolved_references` derive from the *same* cached `MapResult`; every outline-units `UnresolvedReference` carries `entity=<unit name>` for a unit that is in `outline.mapped` (`io/outline.py:_build_unit` appends the unit after `_resolve_roles`). So `unit_uris.get(ref.entity)` is never None — the guard is dead code that the doctrine treats as debt (a guard with no reachable cause).
- **Suggested change:** `unit_uri = unit_uris[ref.entity]` then `source = queries.resolve_source(indexer, unit_uri)`; the legitimate None handling stays at line 89.

### R3 — Duplicated test-graph builders
- **Where:** `tests/validation/conftest.py:225-253`
- **Why it matters:** the reify loop (map → `to_triples` → `build_provenance`) is copied verbatim into the new `build_outline_indexer`; the only delta is one `map_outline` call. Third copy of a shared shape → DRY.
- **Suggested change:** collapse to `build_indexer(root, *, outline=False)` and `build_and_save_graph(root, *, outline=False)`; update the new call sites in `test_narrative_structure.py` and `test_command.py`.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| validation/validators/narrative_structure.py | 100% line (1 expr-branch unmeasured, R1) | 80% | PASS* |
| validation/base.py | 95% | 80% | PASS |
| validation/queries.py | 93% | 80% | PASS |

## 6. Inability-to-verify notes

None — all four gates ran green locally.
