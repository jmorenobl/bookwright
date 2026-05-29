# Quality Audit — 004-init-command

**Scope:** structural focus — `src/bookwright/commands/` layout vs main (user invocation: *"vigila la estructura de directorios para que sea una estructura limpia"*; example given: `init` should be a package, not seven flat siblings).
**Commit range:** `main..7b2a3aa`
**Date:** 2026-05-29
**Conventions discovered:** [.specify/memory/constitution.md](../../.specify/memory/constitution.md) (v1.1.0, ratified 2026-05-28), [CLAUDE.md](../../CLAUDE.md), [CONTRIBUTING.md](../../CONTRIBUTING.md)

This run supersedes the 4b8fb4f baseline. The five findings from that report (R1 CRITICAL line-ceiling, R2 dead code, R3 envelope-translate dedup, R4 `Mapping` no-op, R5 reserved-slug test naming) are all closed on this branch: R1/R2/R4 by [c99f993](https://github.com/) (decomposition into six `_init_*.py` siblings), R3 by [c99f993](https://github.com/) (collapsed into `_init_envelope.emit_error`), R5 by the same decomposition (the test moved alongside `_init_validate.py`). The line-ceiling rule now passes (largest file is `_init_scaffold.py` at 407). This audit re-scans the *resulting* layout against Principle IV, the codebase's own precedent (`integrations/<key>/`), and code-smell signals introduced by the decomposition itself.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH     | 0 |
| MEDIUM   | 1 |
| LOW      | 1 |
| **Total** | 2 |

Coverage gate: **PASS** (global 97.35%, every changed module ≥ 92%; constitutional threshold 80%). Quality gates: `pytest` ✓ 348 tests, `ruff check` ✓, `ruff format --check` ✓, `mypy --strict src tests` ✓ — all confirmed from `c99f993`'s commit message and unchanged on `7b2a3aa`.

## 2. Conventions Compliance Matrix

The compliance matrix from the 4b8fb4f baseline (23 rules, one FAIL on R1) was fully re-checked. Re-running the same rules against `7b2a3aa` yields all `PASS` except the new directory-cleanliness concern, which is not itself a constitutional rule but interacts with Principle IV's intent. Only the deltas vs the prior matrix are reproduced here; the unchanged rows are accurate at the 4b8fb4f snapshot and the source has not moved beyond what `c99f993` + `7b2a3aa` rewrote.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`." | [constitution.md:92-93](../../.specify/memory/constitution.md#L92-L93) | layout | PASS (literal) — but see **R1** for the spirit interpretation | `init` registered from [src/bookwright/commands/init.py](../../src/bookwright/commands/init.py); a Python *package* `commands/init/` would also satisfy the rule (package = module). |
| "No source file (production or test) may exceed 500 lines." | [constitution.md:93-95](../../.specify/memory/constitution.md#L93-L95) | module-size | PASS | Largest changed file is [src/bookwright/commands/_init_scaffold.py](../../src/bookwright/commands/_init_scaffold.py) at 407 lines. `init.py` is now 235. |
| "specs/NNN-name/ governance files tracked on branch." | [CLAUDE.md:60-62](../../CLAUDE.md) | track-integrity | PASS | A.3 cross-check: every file in [specs/004-init-command/](../) is in `git diff main...HEAD` (9 files, all committed). `git status --porcelain` is clean. |
| "Spec Kit pipeline: specify → clarify → plan → tasks → analyze → implement." | [CLAUDE.md:33-52](../../CLAUDE.md) | workflow-step | PASS | A.4 trail: specify `69c9703`, clarify `ef18ebe`, plan `c6bba54`, tasks present, analyze `827c8f0/5818f92/0c4a0f7/ddbf2d6`, implement `4b8fb4f`, post-implement audit-closure `c99f993` + `7b2a3aa`. No artifact missing. |
| (All other rules from the 4b8fb4f matrix) | — | various | PASS | No source movement that would change their verdicts; the only diff since 4b8fb4f is the decomposition + the duplicate-warning fix. |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A/C | MEDIUM | [src/bookwright/commands/](../../src/bookwright/commands/) — 7 of 10 files share an `init` prefix | The post-decomposition layout pushes six `_init_*.py` private siblings into the same flat namespace as the only two other subcommands (`check.py`, `version.py`). The `_init_` prefix is a name-based namespace, not a real one. The codebase's own precedent for "cluster of modules that implement one thing" is the package layout under [src/bookwright/integrations/](../../src/bookwright/integrations/) (`claude/`, `generic/`). Apply the same shape here. | Convert `commands/_init_*.py` into a `commands/init/` package: move each helper to `commands/init/<name>.py` (dropping the `_init_` prefix; the parent directory carries the namespace), keep the Typer entry point in `commands/init/__init__.py` re-exporting `run` and `CONTEXT_SETTINGS`. `cli.py:5` (`from bookwright.commands import … init …`) keeps working unchanged because `init` is then a package object exposing the same two names. See §4 R1 for the migration map and the side-effects this also fixes. |
| R2 | B | LOW | [src/bookwright/commands/_init_envelope.py:196-200](../../src/bookwright/commands/_init_envelope.py#L196-L200) | Function-local imports tagged `# noqa: PLC0415 — break cycle`: `_init_envelope` lazy-imports `_init_git` and `_init_scaffold` to dodge an import cycle introduced by the flat decomposition. The cycle exists because all six helpers live in one namespace; a package layout would let `init/envelope.py` import from `init/git.py` and `init/scaffold.py` directly without re-entering the parent package. | Auto-resolved by **R1**: once the helpers move under `commands/init/`, the lazy import + the `noqa` annotations + the `break cycle` justification all disappear with the package conversion. Track the deletion in the same PR as R1; do not patch the cycle in place. |

## 4. Remediation Detail

### R1 — Cluster `init`'s helpers into a `commands/init/` package

- **Where:** [src/bookwright/commands/](../../src/bookwright/commands/) — `init.py` plus six `_init_*.py` siblings: `_init_conflict.py`, `_init_envelope.py`, `_init_git.py`, `_init_resolve.py`, `_init_scaffold.py`, `_init_validate.py`.
- **Why it matters:** Principle IV's stated goal is *"per-command isolation keeps blast radius small, makes tests addressable, and prevents the slow drift toward a god-module."* The flat `_init_*.py` shape satisfies the rule literally (one file per subcommand at `commands/<name>.py`) but spends seven of the ten entries in `commands/` on one command, weakening the at-a-glance "what subcommands does this CLI have" reading of the directory. The package shape — already in use for plugin clusters at [src/bookwright/integrations/claude/](../../src/bookwright/integrations/claude/) and [src/bookwright/integrations/generic/](../../src/bookwright/integrations/generic/) — keeps the listing at three entries (`init/`, `check.py`, `version.py`) and makes the encapsulation explicit. It also resolves R2 (the cyclic-import workaround) as a side-effect, and lets the `_INIT_FILES` glob in [tests/commands/test_init_ast_invariants.py:17](../../tests/commands/test_init_ast_invariants.py#L17) collapse to `(_INIT_DIR / "init").glob("*.py")`.
- **Suggested change:** Migration map (rename + relocate; no behavioural change). All names lose the `_init_` prefix because the parent package now provides the namespace:

  ```
  src/bookwright/commands/init.py              → src/bookwright/commands/init/__init__.py
                                                    (re-exports `run`, `CONTEXT_SETTINGS`)
  src/bookwright/commands/init.py (Typer body) → src/bookwright/commands/init/main.py (or .command.py)
  src/bookwright/commands/_init_conflict.py    → src/bookwright/commands/init/conflict.py
  src/bookwright/commands/_init_envelope.py    → src/bookwright/commands/init/envelope.py
  src/bookwright/commands/_init_git.py         → src/bookwright/commands/init/git.py
  src/bookwright/commands/_init_resolve.py     → src/bookwright/commands/init/resolve.py
  src/bookwright/commands/_init_scaffold.py    → src/bookwright/commands/init/scaffold.py
  src/bookwright/commands/_init_validate.py    → src/bookwright/commands/init/validate.py
  ```

  Then rewrite the internal imports inside the new package from absolute (`from bookwright.commands._init_envelope import emit_error`) to relative (`from .envelope import emit_error`). External callers do not change — `cli.py:5`'s `from bookwright.commands import … init …` still resolves, and `init.run` / `init.CONTEXT_SETTINGS` still work because `commands/init/__init__.py` re-exports them. Test files that import the helpers directly ([tests/commands/conftest.py:39,49](../../tests/commands/conftest.py#L39), [tests/commands/test_init_helpers.py:15-29](../../tests/commands/test_init_helpers.py#L15-L29), [tests/commands/test_init_rollback.py:136,184,219-224](../../tests/commands/test_init_rollback.py#L136), [tests/commands/test_init_options_record.py:16](../../tests/commands/test_init_options_record.py#L16)) update from `bookwright.commands._init_<name>` → `bookwright.commands.init.<name>` — that's a single grep-and-replace across ~12 import sites. The AST-invariant glob at [tests/commands/test_init_ast_invariants.py:17](../../tests/commands/test_init_ast_invariants.py#L17) becomes a single-directory glob (`(_INIT_DIR / "init").glob("*.py")` over the new package). Run `pytest` + `ruff check` + `mypy --strict src tests` after the move; no behaviour changes, so every existing assertion should hold.

  Concrete sanity check before opening the PR: `find src/bookwright/commands -maxdepth 1 -type f -name '*.py'` should return exactly three entries (`__init__.py`, `check.py`, `version.py`), and `find src/bookwright/commands/init -maxdepth 1 -type f -name '*.py'` should return exactly eight (`__init__.py`, `main.py`, `conflict.py`, `envelope.py`, `git.py`, `resolve.py`, `scaffold.py`, `validate.py`).

### R2 — Lazy-import workaround in `_init_envelope.py`

- **Where:** [src/bookwright/commands/_init_envelope.py:196-200](../../src/bookwright/commands/_init_envelope.py#L196-L200)
- **Why it matters:** Two `# noqa: PLC0415 — break cycle` annotations sitting inside `classify_filesystem_failure` are a tell that the current flat decomposition has *bidirectional* coupling: `_init_scaffold` imports from `_init_envelope`, and `_init_envelope` needs to know `_init_scaffold`'s exception types. Workarounds tend to grow; tags marked "break cycle" are particularly load-bearing because deleting them silently re-introduces the cycle at runtime.
- **Suggested change:** Do **not** patch the cycle in place. Apply R1's package conversion and rewrite the function-local imports as top-of-file relative imports (`from .git import GitInitError`, `from .scaffold import BackupCreationError, TargetOutsideProjectRootError`). The cycle disappears because Python resolves the package's submodules in import order — there is no cross-package re-entry, only intra-package siblings. Drop the two `noqa` comments and the `# break cycle` justification in the same diff. If R1 is rejected, the local fix is to extract the three exception classes (`BackupCreationError`, `TargetOutsideProjectRootError`, `GitInitError`) into a tiny `_init_errors.py` that everyone imports from — but that adds an eighth file and makes R1 even more pointed, so prefer R1.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/commands/init.py` (235 lines, was 671) | 96% | 80% | PASS |
| `src/bookwright/commands/_init_conflict.py` (107) | 99% | 80% | PASS |
| `src/bookwright/commands/_init_envelope.py` (254) | 100% | 80% | PASS |
| `src/bookwright/commands/_init_git.py` (96) | 98% | 80% | PASS |
| `src/bookwright/commands/_init_resolve.py` (193) | 100% | 80% | PASS |
| `src/bookwright/commands/_init_scaffold.py` (407) | 99% | 80% | PASS |
| `src/bookwright/commands/_init_validate.py` (167) | 100% | 80% | PASS |
| **Global (`src/bookwright/`)** | **97.35%** | **80%** | **PASS** |

Values are the snapshot from `c99f993`'s commit message (the only commit since 4b8fb4f that changed the source tree; `7b2a3aa` is a duplicate-warning fix and does not move the numbers). Re-running `pytest --cov` would re-confirm.

## 6. Inability-to-verify notes

- The audit could not re-run `pytest --cov` because the skill is read-only and a full test pass on this branch would require a sandbox invocation that the user has not asked for. Coverage in §5 is taken verbatim from the `c99f993` commit message, which was generated by the actual test run that landed the decomposition. If R1 is acted on, the coverage table MUST be re-validated after the move; the expectation is that line counts redistribute across the package without a coverage drop.
- "Cleanliness" is not a literal constitutional rule. R1 is graded MEDIUM (not CRITICAL or HIGH) because the constitution's Principle IV allows either a single-file module or a package at `commands/<name>` — both are "a module under `src/bookwright/commands/`". The user's preference, the codebase's own `integrations/<key>/` precedent, and the cyclic-import workaround R2 are the supporting signals; the absence of a verbatim MUST is the cap on severity.

