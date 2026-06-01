# Quality Audit — 006-graph-indexer

**Scope:** 18 in-scope source/test/config files vs `main` (graph commands, indexers, io package, `check.py`, `cli.py`)
**Commit range:** `main`..`08538fc`
**Date:** 2026-06-01
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.2.0), `pyproject.toml`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 4 |
| LOW | 2 |
| **Total** | 6 |

Coverage gate: **PASS** (aggregate 96.75% ≥ 80%; one in-scope module, `graph/envelope.py`, sits at 79% per-module — see R1).
Lint / format / type gates: **PASS** (`ruff check`, `ruff format --check`, `mypy --strict` all clean on the 15 in-scope source files).
Test suite: **515 passed**.

This is a re-audit. The prior pass (`7424f23`) raised one finding (forbidden `US-x`/`T0xx` tags), resolved in `13df4f3`. No CRITICAL or HIGH findings remain; the implementation respects every NON-NEGOTIABLE principle.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden as canonical storage" | `constitution.md:47` | layout | PASS | Graph serialized to `bible/graph.ttl` (Turtle); reports are JSON-on-stdout. No binary canonical store. |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | `constitution.md:64` | dependency | PASS | `pyyaml` added to both `pyproject.toml` and the constitution's list (v1.1.0→1.2.0 amendment, Sync Impact Report). 11 deps match 1-to-1. |
| "Runtime dependencies (minimum set): jinja2, packaging, … pyyaml, rdflib, rich, tomlkit, typer, uuid-utils" | `constitution.md:181` | dependency | PASS | `pyproject.toml [project].dependencies` is exactly this set, alphabetical. No extras. |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:72` | layout | PASS | All new modules under `src/bookwright/{commands/graph,indexers,io}`; all new tests under `tests/`. |
| "Each CLI subcommand MUST live in its own module … No source file … may exceed 500 lines" | `constitution.md:83` | module-size | PASS | `graph build`/`query` in separate modules; largest in-scope file `io/bible.py` = 367 lines. All ≤500. |
| "Integrations MUST be implemented as subclasses … A monolithic `AGENT_CONFIG`-style dispatcher is … forbidden" | `constitution.md:94` | plugin-shape | PASS | Engine seam uses the same shape: `INDEXER_REGISTRY` + `resolve_indexer`, no if/elif ladder (`indexers/__init__.py:20-33`). |
| "Writing to `.claude/commands/`, `.agents/commands/`, or any analogous … directory is prohibited" | `constitution.md:107` | directory-ban | N/A | Iteration 6 emits no skills/commands. No writes to any banned directory in scope. |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:135` | coverage-threshold | PASS | Aggregate 96.75%. (Rule is aggregate "across src/bookwright/", which passes; see R1 for the one sub-80% module.) |
| "CI MUST run pytest, ruff, and mypy strict on every push … a red bar blocks merge" | `constitution.md:140` | coverage-threshold | PASS | All four gates green locally on the in-scope files. |
| "Any CLI command … MUST accept a `--json` flag and … emit a single well-formed JSON document on stdout and nothing else" | `constitution.md:148` | io-contract | PASS | `graph build`/`query` honor it; `emit_json` writes one separator-compact line to stdout, all prose to `Console(stderr=True)`. Asserted by `test_json_contract.py`. |
| "Exit codes MUST be non-zero on error even when `--json` is set" | `constitution.md:153` | io-contract | PASS | Both verbs raise `typer.Exit(2/3/4)` while still emitting the JSON error envelope; `test_query_error_json_only_on_stdout` checks exit 2 + error doc. |
| "GrafeoIndexer and vector search — v0.3 … MUST NOT be pulled into v0 scope" | `constitution.md:200` | scope-ban | PASS | `GrafeoIndexer` appears only as a comment stating it is *intentionally not registered* (`indexers/__init__.py:4`). No plumbing for it. |
| "These [§16 axioms] MUST NOT be reopened … rdflib over Grafeo in v0" | `constitution.md:159` | scope-ban | PASS | `RdflibIndexer` is the sole registry entry; no Grafeo code path. |
| Spec Kit ordered workflow: specify → clarify → plan → tasks → analyze → implement | `CLAUDE.md` | workflow-step | PASS | spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/, checklists/ all present and committed on branch (A.4). |
| Governance / feature dir tracked in git | `CLAUDE.md` | track-integrity | PASS | All `specs/006-graph-indexer/*` and `src`/`tests` files appear in `git diff main...HEAD`; working tree clean (A.3). |

Every `FAIL` would have a Section 3 row; there are none. The single sub-threshold module is recorded as MEDIUM (R1), not a convention FAIL, because the binding rule is aggregate.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | D | MEDIUM | src/bookwright/commands/graph/envelope.py:24,34 | Module at 79% line coverage; the `details` branch of `error_payload` and the human-stderr branch of `emit_error` are unexercised | Add one test for `--json` off (stderr `bookwright: error:` line) and one passing `details=` to `error_payload`. |
| R2 | B/C | MEDIUM | src/bookwright/indexers/base.py:49 | `Indexer.construct()` + its `RdflibIndexer` impl have no v0 caller (only a unit test); expands the "stable seam" every future engine must implement for zero current consumers | Drop `construct()` from the protocol until a command needs it (YAGNI), or document the consumer that justifies it. |
| R3 | B | MEDIUM | src/bookwright/io/bible.py:211,250,285 | Data clump: `(project_root, result, collisions, slug_index)` threads through three helpers with 8–9 params each (3× `# noqa: PLR0913`) | Introduce a small `_MapContext` dataclass holding the shared mapping state; pass one object instead of re-threading four args. |
| R4 | B | MEDIUM | src/bookwright/io/errors.py:31 | `to_json()` is hand-rolled identically across `io/errors.py` + `indexers/errors.py` (and the pre-existing `core`/`golem` error modules) — 4 parallel hierarchies | Extract a shared base (e.g. `BookwrightError` with `code`/`message`/`details` → templated `to_json`). Cross-iteration refactor — see Next Actions, not this PR. |
| R5 | B | LOW | src/bookwright/commands/graph/build.py:37 | `--force` is a documented no-op in v0 (dead parameter) | Acceptable as forward-compat (contract-documented, idempotency-tested). No action required; listed for visibility. |
| R6 | B | LOW | src/bookwright/io/bible.py:218,259,294 | `builder`/`factory`/`frontmatter` params typed `Any`, silently disabling `mypy --strict` at those call seams | Type as `Callable[[dict[str, Any], str], GolemEntity]` / `Callable[..., GolemEntity]` / `Frontmatter` for real strictness. |

## 4. Remediation Detail

No CRITICAL or HIGH findings require pre-merge remediation. The MEDIUM items below are quality improvements; none block merge.

### R1 — `graph/envelope.py` two uncovered branches

- **Where:** `src/bookwright/commands/graph/envelope.py:24` (`payload["details"] = details`) and `:34` (the `sys.stderr.write("bookwright: error: …")` non-`--json` branch).
- **Why it matters:** Principle VIII's gate is aggregate (96.75%, passes), but the *human-mode* error path is the one a developer sees at the terminal and it currently has no test. A regression that broke the stderr formatting would ship green.
- **Suggested change:** in `tests/commands/graph/`, invoke a failing command **without** `--json` and assert `result.stderr.startswith("bookwright: error:")`; add a direct unit test `error_payload("x", "y", {"k": 1})["details"] == {"k": 1}`.

### R2 — `Indexer.construct()` is speculative seam

- **Where:** `src/bookwright/indexers/base.py:49` (protocol) and `src/bookwright/indexers/rdflib_indexer.py:89-98` (impl, with a `# pragma: no cover` defensive branch).
- **Why it matters:** the `Indexer` protocol is explicitly "the stable engine seam build/query depend on." Neither `graph build` nor `graph query` calls `construct()`; only `test_rdflib_indexer.py` does. Every future engine (the deferred Grafeo) is now contractually obliged to implement a method nothing consumes — the exact "speculative generality" the constitution's Scope section warns against.
- **Suggested change:** remove `construct()` from `base.Indexer` and `RdflibIndexer` until a command (likely iteration 10 validation) actually needs CONSTRUCT, then re-add it with its consumer. If it must stay, add a one-line comment naming the iteration that will use it.

### R3 — `io/bible.py` mapping helpers share a data clump

- **Where:** `src/bookwright/io/bible.py:211` (`_map_single_dir`), `:250` (`_map_collection`), `:285` (`_map_collection_item`).
- **Why it matters:** the same four values — `project_root`, `result`, `collisions`, and the `slug_index` — travel together through every helper, forcing 8–9-parameter signatures the author had to silence with `# noqa: PLR0913` three times. That is the textbook data-clump / long-parameter-list smell; the suppressions document the tension rather than resolving it.
- **Suggested change:** add `@dataclass class _MapContext: project_root: Path; result: MapResult; collisions: _Collisions; slug_index: dict[str, URIRef] | None`, build it once in `map_bible`, and pass it as a single argument. The per-call `concept`/`allowed_keys`/`factory` stay as explicit params. This removes all three `noqa`s.

### R4 — `to_json()` duplicated across error hierarchies

- **Where:** `src/bookwright/io/errors.py:31` and `src/bookwright/indexers/errors.py:33` (plus the pre-existing `core/errors.py`, `golem/errors.py`). Each error class repeats `{"status":"error","code":self.code,"message":self.message,"details":{…}}`.
- **Why it matters:** four parallel hierarchies hand-roll the identical envelope shape (the module docstrings even say they "mirror" one another). A change to the error contract is shotgun surgery across four files. Crossed the 3-occurrence DRY threshold.
- **Suggested change:** a shared `BookwrightError(Exception)` base with `code: ClassVar[str]`, `message: str`, optional `details: dict`, and one `to_json()` built from those. **This touches pre-existing `core`/`golem` code, so it belongs in a dedicated refactor PR, not iteration 6** — see Next Actions §3.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| commands/check.py | 96% | 80% | PASS |
| commands/graph/build.py | 89% | 80% | PASS |
| commands/graph/envelope.py | 79% | 80% (aggregate) | sub-module (R1) |
| commands/graph/query.py | 94% | 80% | PASS |
| indexers/base.py | 100% | 80% | PASS |
| indexers/errors.py | 100% | 80% | PASS |
| indexers/rdflib_indexer.py | 94% | 80% | PASS |
| io/bible.py | 91% | 80% | PASS |
| io/errors.py | 98% | 80% | PASS |
| io/frontmatter.py | 100% | 80% | PASS |
| io/manuscript.py | 100% | 80% | PASS |
| io/project.py | 100% | 80% | PASS |
| io/report.py | 100% | 80% | PASS |
| **Aggregate (src/bookwright)** | **96.75%** | **80%** | **PASS** |

## 6. Inability-to-verify notes

- **TDD ordering (Pass D heuristic):** implementation and tests for each graph/indexer module landed in the same commit (`7424f23`), so the impl-before-test heuristic cannot be evaluated — no signal either way.
- **Boundary security:** no path-traversal, injection, unsafe-deserialization, or hardcoded-secret risk found. `frontmatter.py` uses `yaml.safe_load`; no `shell=True`/`eval`/`exec`/`pickle` anywhere in scope. SPARQL passed to `graph query` is intentional read-only user input (mutation-free, asserted by `test_query_does_not_mutate_the_graph`); not a finding.
