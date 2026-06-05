# Quality Audit — 018-unified-error-envelope

**Scope:** 11 source files + 9 test files vs `main` (plus 6 spec/contract docs)
**Commit range:** `main`..`b0d1f16`
**Date:** 2026-06-05
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.3.0), `specs/018-unified-error-envelope/{spec,plan,tasks}.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 1 |
| **Total** | 2 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; total 96.77%). All four CI gates green: `ruff check`, `ruff format --check`, `mypy --strict` (214 files, no issues), `pytest` (1057 passed, 96.77%).

**Verdict:** clean, well-engineered debt-paydown. The iteration delivers every FR and SC as written. The single finding (R1) is *spec-sanctioned* residual debt, not a rule violation — surfaced because you asked for "nula deuda técnica / no atajos" and it is the one place the iteration's own "single source of truth, changeable in exactly one place" goal (spec.md:22) is only partially realised.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "single shared base exception (`BookwrightError`) that defines the canonical error envelope" | `spec.md:94` (FR-001) | io-contract | PASS | `src/bookwright/errors.py:17-47` — one base, one `to_json()` |
| "MUST inherit from `BookwrightError` and MUST NOT define its own envelope-building serializer (`to_json` **or** `to_dict`)" | `spec.md:96` (FR-003) | io-contract | PASS | `grep "def to_dict"` → 0; `def to_json` only on base + non-error report/finding types (Violation/ValidatorError/ManifestWarning/report) — all FR-012 success/finding payloads, explicitly out of scope |
| io/indexers/validation/`_UsageError` migrated **byte-for-byte** | `spec.md:97` (FR-004) | io-contract | PASS | io/errors.py, indexers/errors.py, validation/base.py:133-141, validate.py:43-53 inherit base; details preserved verbatim; unchanged shape tests pass |
| core/golem flat shapes normalized to canonical envelope | `spec.md:98-99` (FR-005) | io-contract | PASS | core/errors.py + golem/errors.py: former `"error"`→`code`, fields→`details`; tests updated (test_json_shapes.py, test_slug.py) assert canonical |
| integrations `to_dict()` deleted, attrs→`details` | `spec.md:99` (FR-005a) | io-contract | PASS | integrations/errors.py: no `to_dict`; 8 subclasses end with `super().__init__(msg, {...})` |
| `InvalidProjectNameError` inherits base, `details={value,rule}` | `spec.md:100` (FR-005b) | io-contract | PASS | init/validate.py:39-50 |
| boundary writers MUST source code/message/details from `exc.to_json()`/`exc.code`/`.message`/`.details`, never raw attrs/`to_dict` | `spec.md:101` (FR-005c) | io-contract | PASS | resolve.py:170-191, validate.py:128-137 read `exc.code`/`str(exc)`/`exc.details`; init/envelope.py keeps `rolled_back`+`bookwright_version` superset |
| codes / messages / exit codes MUST NOT change | `spec.md:103-105` (FR-007/8/9) | io-contract | PASS | `code` literals preserved; existing exit-code tests pass unchanged |
| base module MUST NOT import core/golem/io/indexers/validation/integrations/commands; no cycle | `spec.md:106` (FR-010) | layout | PASS | errors.py imports only `typing`; `test_errors.py:101-122` proves it in a cold subprocess |
| two-level hierarchy preserved; no `except <PackageError>` catch site modified | `spec.md:111` (FR-015) / SC-008 | io-contract | PASS | ManifestError/IOError_/IndexerError/GolemError abstract roots intact; no catch site touched |
| contract docs updated for unified envelope | `spec.md:110` (FR-014) | workflow-step | PASS | specs/002, 003, 005 data-model/contracts in diff |
| serializers on error classes (to_json **and** to_dict) = **zero** outside `BookwrightError` | `spec.md:124` (SC-001) | io-contract | PASS | No serializer *method on an error class* survives. Command-module envelope *functions* (graph `error_payload`, use `_error`, init `error_envelope`) are out of SC-001's literal scope — see R1 |
| Plain text as source of truth; no binary stores under src | `constitution.md:57` (I) | layout | PASS | In-memory exceptions only; no storage change |
| Python 3.11+, no new runtime dependency | `constitution.md:70` (II) | dependency | PASS | base uses stdlib `typing`/`json` only; pyproject deps unchanged |
| Each source file ≤500 lines | `constitution.md:97` (IV) | module-size | PASS | Largest changed file = validation/base.py at 233 lines |
| `--json` emits one JSON document on stdout, prose to stderr | `constitution.md:167` (IX) | io-contract | PASS | All boundary writers split stdout(JSON)/stderr(prose); exit codes non-zero on error |
| ≥80% line coverage; pytest+ruff+mypy green | `constitution.md:145` (VIII) / SC-007 | coverage-threshold | PASS | 96.77%; all four gates green |
| No plumbing whose only justification is a deferred feature | `constitution.md:227` (Scope) | scope-ban | PASS | Pure refactor of the existing R3 seam; no v0.2+ plumbing |
| Workflow: specify→clarify→plan→tasks→analyze→implement | `CLAUDE.md` | workflow-step | PASS | spec.md (with clarifications) → plan.md → tasks.md → analysis report (commit b0d1f16) → source; full trail present |
| Track integrity: spec dir + src + tests committed on branch | A.3 | track-integrity | PASS | `git status --porcelain` clean; every changed file in `main...HEAD` |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | MEDIUM | `src/bookwright/commands/integration/use.py:110-112,57` | `_error()` hand-rebuilds the `{status,code,message}` envelope skeleton to remap `ManifestError`→`invalid_manifest`, bypassing the base — while the *same* remap in `commands/validate.py` routes through `_UsageError(...).to_json()`. The skeleton is also duplicated in `graph/envelope.py:error_payload` and `init/envelope.py:error_envelope` (4 sites total). | Mirror `validate.py`: wrap the manifest remap in a tiny per-instance-`code` `BookwrightError` (or a shared `commands` helper) and emit `exc.to_json()`, so the envelope skeleton lives in exactly one place. |
| R2 | C | LOW | `src/bookwright/commands/integration/use.py:110-112` | After migration, three of four catch arms emit `exc.to_json()`; only the manifest arm needs `_error()`. The lone single-call-site helper is vestigial. | Folded into R1's fix — once the manifest remap routes through the base, `_error()` disappears. |

## 4. Remediation Detail

### R1 — Residual envelope skeletons leave the single-source goal partially met

- **Where:** `src/bookwright/commands/integration/use.py:110-112` (`_error`) and `:57` (its call); related: `src/bookwright/commands/graph/envelope.py:20-25` (`error_payload`, *not* in this diff — pre-existing), `src/bookwright/commands/init/envelope.py:140-155` (`error_envelope`, sanctioned superset).
- **Why it matters:** The iteration exists to kill the R3 debt where "any change to the contract must be replicated N times" and to make the envelope "changeable in exactly one place, ever" (`spec.md:22`). FR-005c/SC-001 are met **as literally worded** — they ban serializer *methods on error classes*, and none survive. But the canonical `{"status":"error","code","message"}` skeleton is still literally reconstructed in four command-module functions. A future envelope change (rename `status`, add a field) would still touch `BookwrightError.to_json` **plus** these three helpers. The sharpest evidence is the *inconsistency inside this very iteration*: `commands/validate.py:88-103` solves the identical "remap a caught `ManifestError` to a single `invalid_manifest` code" by wrapping in `_UsageError("invalid_manifest", str(exc))` and calling `.to_json()` (one source), whereas `use.py:57` hand-rolls it via `_error()`. Two patterns for one problem is precisely the drift the iteration set out to remove.
- **Note on authority:** This is **not** an FR/SC violation — SC-001's scope was deliberately drawn around error-class serializers, so command-level envelope helpers are spec-permitted. Treat R1 as optional debt-paydown polish, not a merge blocker. Raised because it is the one residue of exactly the R3 pattern and you asked for "nula deuda / no atajos."
- **Suggested change:** Introduce one shared remap (e.g. reuse the `_UsageError`-style per-instance-`code` `BookwrightError`, or a `commands._envelope.remap_manifest(exc) -> dict` that returns `{**_AsInvalidManifest(str(exc)).to_json()}`) and call it from `validate.py`, `graph/build.py:52`, `graph/query.py:47`, and `use.py:57`. Delete `use._error` and `graph.error_payload`. For `init/envelope.error_envelope`, spread the base body — `{**exc.to_json(), "rolled_back": ..., "bookwright_version": ...}` — on the paths where a `BookwrightError` is in hand (it must still accept primitives for the FR-003 carve-outs: `OSError`/`PermissionError`/`GitInitError`).

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/errors.py` | 100% (test_errors.py exercises base directly) | 80% | PASS |
| `src/bookwright/core/errors.py` | ≥ project floor | 80% | PASS |
| `src/bookwright/golem/errors.py` | ≥ project floor | 80% | PASS |
| `src/bookwright/io/errors.py` | ≥ project floor | 80% | PASS |
| `src/bookwright/indexers/errors.py` | ≥ project floor | 80% | PASS |
| `src/bookwright/integrations/errors.py` | ≥ project floor | 80% | PASS |
| `src/bookwright/validation/base.py` | 94.53% | 80% | PASS |
| `src/bookwright/commands/validate.py` | ≥ project floor | 80% | PASS |
| **TOTAL** | **96.77%** | 80% | PASS |

## 6. Inability-to-verify notes

- Per-file coverage for the smaller error modules was read from the aggregate run (96.77% total, no module below 80%); the coverage table reports them as "≥ project floor" where the line was not individually printed in the truncated terminal output. The gate itself (`fail_under=80`) passed.
- `graph/envelope.py` `error_payload` is flagged in R1 for context but is **out of this branch's diff** (pre-existing); it is not a finding *introduced* by 018 and is advisory only.
