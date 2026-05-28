# Quality Audit — 001-repo-bootstrap (round 2)

**Scope:** 33 changed files vs `main`
**Commit range:** `987824f`..`beb3390`
**Date:** 2026-05-28
**Run motivation:** user invoked `/quality-audit` with `no quiero deuda técnica. Antes de pasar a la siguiente spec, la deuda técnica debe cancelarse.` — re-audit after applying R1–R5 from round 1, looking for any residual debt before iteration 2 starts.
**Conventions discovered:**

- `CLAUDE.md` (project-level)
- `.specify/memory/constitution.md` v1.0.0 (10 principles, 3 non-negotiable)
- `specs/001-repo-bootstrap/spec.md` (FR-001 … FR-022)
- `specs/001-repo-bootstrap/plan.md` (Project Structure, forbidden dirs)
- `specs/001-repo-bootstrap/contracts/{version,check}.schema.json`
- `bookwright-design.md` (referenced by plan/research)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH     | 1 |
| MEDIUM   | 1 |
| LOW      | 0 |
| **Total**| **2** |

**Round-1 findings (R1–R5): all CLOSED** — verified against current source. See § 7 below for the verification trail.

Coverage gate: **PASS** (91.03% over `src/bookwright`, threshold = 80%; gate `--cov-fail-under=80` is active in [pyproject.toml:72](pyproject.toml#L72)). Test suite: 8 passed in 0.36s. `ruff check`, `ruff format --check`, and `mypy --strict` all green locally.

The **code** is clean. The two findings below are **governance-document drift**: two artifacts under [specs/001-repo-bootstrap/](specs/001-repo-bootstrap/) describe an earlier state of this iteration and now contradict the shipped code and the tightened spec. Per the user's intent ("cancelar deuda técnica antes de pasar a la siguiente spec"), both should be reconciled before iteration 2 opens.

## 2. Conventions Compliance Matrix

Only the rules where the verdict has **changed** from round 1 or where the rule was previously `N/A`. The bulk of the matrix (Principles I–V, VII, X; spec FR-001 through FR-022; plan directory bans; CLAUDE.md module size) is unchanged from round 1's matrix and still `PASS`. Re-evaluated here:

### Constitution (`.specify/memory/constitution.md`)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Tests are mandatory ... CI MUST run pytest, ruff, and mypy strict" (Principle VIII, NON-NEGOTIABLE) | constitution.md §VIII | coverage-threshold | PASS | All four gates in [`.github/workflows/tests.yml`](.github/workflows/tests.yml); 8 tests passing locally |
| "v0 MUST hold minimum 80% line coverage across src/bookwright/" | constitution.md §VIII | coverage-threshold | PASS (code) / **FAIL (governance)** | Code: 91.03% measured locally; gate active in [pyproject.toml:72](pyproject.toml#L72). **Governance: [checklists/requirements.md:35](specs/001-repo-bootstrap/checklists/requirements.md#L35) still says the gate is "deliberately treated as a non-blocking target for this iteration" — directly contradicts a NON-NEGOTIABLE rule and the tightened spec.** See R6. |
| "Any CLI command ... MUST accept a `--json` flag and emit a single JSON document on stdout and nothing else" (Principle IX) | constitution.md §IX | io-contract | PASS | Subprocess byte-exact tests cover both `version --json` and `check --json` ([tests/test_cli_subprocess.py:16-55](tests/test_cli_subprocess.py#L16-L55)) — R5 closed. |

### Spec (`specs/001-repo-bootstrap/`)

| Rule | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "--cov-fail-under=80 desde día uno sin excepciones" | spec.md FR-020 | coverage-threshold | PASS (code) / **FAIL (governance)** | Gate active in pyproject; **the requirements.md Note (line 35) still asserts the opposite**. See R6. |
| "T029 Walk through quickstart.md § Definición de 'done' checklist by hand and tick every box" | tasks.md T029 | workflow-step | **FAIL** | T029 marked `[X]` in [tasks.md:167](specs/001-repo-bootstrap/tasks.md#L167) but the eight boxes it references are still `- [ ]` in [quickstart.md:151-162](specs/001-repo-bootstrap/quickstart.md#L151-L162). See R7. |

### Workflow trail (A.4) — Spec Kit sequence

CLAUDE.md mandates `/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement`. Re-walked since round 1:

| Step | Artifact | Present? | Status |
|---|---|---|---|
| specify | `spec.md` | ✓ | PASS |
| clarify | "Clarifications" section in spec | ✓ (4 Q&A) | PASS |
| plan | `plan.md` + `research.md` + `data-model.md` + `contracts/` + `quickstart.md` | All five | PASS |
| tasks | `tasks.md` (30/30 marked `[X]`) | ✓ | PASS |
| analyze | analysis report or checklist entry | ✓ — round-1 `review.md` + `checklists/quality.md` (this file will overwrite review.md) | PASS |
| implement | source code under `src/bookwright/` | ✓ — package skeleton + 2 commands + tests + CI + pre-commit; refactor commit `beb3390` applied R1–R5 | PASS |

No broken trail.

### Track integrity (A.3) — governance directories

| Directory | Files on disk | All committed on branch? | Status |
|---|---|---|---|
| `specs/001-repo-bootstrap/` | 7 .md, 2 schema JSON, 2 checklists | Yes — all in branch diff or already on main | OK |
| `.specify/` | constitution, templates, extensions.yml, per-project configs | All tracked | OK |
| `.claude/skills/` | 14 speckit skills + `uv` skill | Inherited from `main` via commits `987824f`, prior | OK |
| Repo root | `pyproject.toml`, `uv.lock`, `LICENSE`, `README.md`, `CLAUDE.md`, configs, `skills-lock.json` | All tracked, working tree clean | OK |

`git status --porcelain` is clean — no uncommitted governance artifacts. `skills-lock.json` is inherited from `main` (commit `987824f`), not new on this branch.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R6 | A | HIGH | [specs/001-repo-bootstrap/checklists/requirements.md:35](specs/001-repo-bootstrap/checklists/requirements.md#L35) | "The 80 % coverage threshold ... is deliberately treated as a non-blocking target for this iteration only" contradicts (a) Constitución §VIII (NON-NEGOTIABLE), (b) the tightened spec FR-020, and (c) the active `--cov-fail-under=80` gate in `pyproject.toml` | Delete the bullet, or replace it with an affirmative note that the gate IS active from day one and was tightened mid-iteration (commit `f2e2dcf`). Governance docs that contradict NON-NEGOTIABLE rules erode the rule. |
| R7 | A | MEDIUM | [specs/001-repo-bootstrap/quickstart.md:151-162](specs/001-repo-bootstrap/quickstart.md#L151-L162) | The "Definición de 'done'" checklist still has 8 unticked `- [ ]` boxes even though tasks.md T029 (which mandates ticking them) is marked `[X]` | Either tick the 8 boxes now (the work landed and was validated — running `uv sync`, `bookwright --help`, the gates, etc. all passed in this audit) or rewrite the section as a *recipe for new developers* and remove the iteration-specific checkboxes. Stale checkboxes signal incomplete work to anyone scanning the dir before iteration 2 starts. |

## 4. Remediation Detail

### R6 — Governance contradicts the NON-NEGOTIABLE coverage gate

- **Where:** [specs/001-repo-bootstrap/checklists/requirements.md:35](specs/001-repo-bootstrap/checklists/requirements.md#L35)
- **Why it matters:** the Note still reads "The 80 % coverage threshold from Constitution Principle VIII is deliberately treated as a non-blocking target for this iteration only: the surface of code introduced by the bootstrap is too small to meaningfully exercise the gate." Three documents prove this is no longer true:
  1. Constitución §VIII (NON-NEGOTIABLE) — "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`".
  2. Spec [FR-020](specs/001-repo-bootstrap/spec.md#L137) — "MUST activar el gate constitucional `--cov-fail-under=80` ... desde esta iteración sin excepciones".
  3. The gate itself in [pyproject.toml:72](pyproject.toml#L72) — `addopts = "... --cov-fail-under=80"`; measured coverage is 91.03%.
  Commit `f2e2dcf` ("docs(spec): tighten iteration 1 — activate coverage gate") tightened the spec, but `requirements.md` was not updated. A future contributor reading the requirements checklist first will form the wrong mental model. Per Pass A.5, a governance note contradicting a NON-NEGOTIABLE rule is **HIGH** severity.
- **Suggested change:** in [checklists/requirements.md](specs/001-repo-bootstrap/checklists/requirements.md), either delete the bullet, or rewrite it as:
  > "Coverage gate: `--cov-fail-under=80` is active in `pyproject.toml` from this iteration and measured at 91.03%. The earlier draft of this checklist treated the gate as deferrable; the spec was tightened (FR-020) to align with Constitución §VIII (NON-NEGOTIABLE)."

### R7 — Stale "done" checklist in quickstart.md

- **Where:** [specs/001-repo-bootstrap/quickstart.md:151-162](specs/001-repo-bootstrap/quickstart.md#L151-L162)
- **Why it matters:** T029 in [tasks.md:167](specs/001-repo-bootstrap/tasks.md#L167) — "Walk through `quickstart.md § Definición de 'done'` checklist by hand and tick every box" — is marked `[X]`. The eight boxes are still `- [ ]`. The four conditions auditable from this branch all pass: `uv run bookwright --help` lists `version` and `check`; both subcommands work in human and `--json` modes; `pytest && ruff check . && ruff format --check . && mypy` is green; the working tree matches `plan.md § Project Structure → Source Code` exactly (verified by `find src/bookwright -type d` returning only `commands/`). The four conditions requiring a fresh clone or live CI run (cold `uv sync` < 60 s, CI pipeline < 5 min, pre-commit hooks blocking malformed commits, …) are the dev-walk items the quickstart was designed for.
- **Suggested change:** two acceptable options —
  1. **Tick what is verifiable here, leave a one-line note for the rest.** Tick the four boxes covered by the gate (`--help`, version/check both modes, full gate suite passes, tree matches structure), and replace the remaining four with a single line: "Cold-clone / CI / pre-commit verifications: see § 'Definición de done' in the per-iteration runbook before merging to `main`."
  2. **Rewrite as a recipe.** Drop the checkbox syntax entirely and reframe the section as "Cómo el dev valida la iteración antes de cerrar la PR" — a numbered procedure, not a state list. Avoids the staleness problem permanently.
  Recommend option 2; checkboxes in a per-iteration governance doc invite drift every time the doc is re-read.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/__init__.py` | 100% | 80% | PASS |
| `src/bookwright/__main__.py` | 0% (3 stmts, 2 branches uncovered) | n/a (project gate) | Not a finding — exercised end-to-end by `tests/test_cli_subprocess.py` (which goes through `python -m bookwright`) but `coverage` doesn't trace subprocesses by default. Could be raised by configuring `concurrency = ["multiprocessing"]`; not required for the 80% project gate, which measures across `src/bookwright/`. |
| `src/bookwright/cli.py` | 100% | 80% | PASS |
| `src/bookwright/commands/__init__.py` | 100% (empty) | 80% | PASS |
| `src/bookwright/commands/check.py` | 96% (line 34 unhit — the < 3.11 failure branch) | 80% | PASS — the unhit branch is the "found 3.10.x" failure path, untestable without a different interpreter. |
| `src/bookwright/commands/version.py` | 100% | 80% | PASS |
| **Project total** | **91.03%** | **80%** | **PASS** |

## 6. Inability-to-verify notes

- **Pre-commit hooks** (FR-010 / FR-011) — exercised only by hand per `quickstart.md § Activar pre-commit hooks localmente`. No automated test invokes `pre-commit run --all-files`. Not a finding, just a coverage note; adding a `pre-commit run --all-files` step to CI would close it.
- **`bookwright check` < 5 s wall-clock budget (SC-004)** — not directly asserted by a test; the suite's 0.36 s total runtime is the indirect evidence.
- **Entry-point script (`[project.scripts].bookwright = "bookwright.cli:app"`)** — exercised via `uv run bookwright --help` in the quickstart but not by a subprocess test (the subprocess tests use `python -m bookwright`, which routes through `__main__.py`, not the console script). A regression in the entry-point string would not be caught by the current suite.
- **Cold `uv sync` < 60 s (SC-001/SC-006)** — depends on network and cache state of the developer's machine; not auditable from this clone.
- **CI pipeline wall-clock (SC-008)** — auditable only by inspecting Actions runs after pushing.

## 7. Round-1 (R1–R5) verification trail

Per the user's "cancelar deuda técnica" framing, all five findings from the previous review (committed at `b286bc6`, fixed in `beb3390`) were re-verified against current source:

| ID | Round-1 finding | Round-1 fix landed | Verification on current `HEAD` |
|---|---|---|---|
| R1 | Pre-commit ruff `rev: v0.5.7` drifted from pyproject `ruff>=0.5` | Hook switched to `repo: local` + `entry: uv run ruff …` | [`.pre-commit-config.yaml:6-17`](.pre-commit-config.yaml#L6-L17) — single ruff (the one in `uv.lock`) across pre-commit / CI / `uv run`. **Closed.** |
| R2 | Empty `@app.callback()` `_root` in `cli.py` was dead | Callback removed | [`src/bookwright/cli.py:7-15`](src/bookwright/cli.py#L7-L15) — only Typer app + two `app.command(…)` registrations. **Closed.** |
| R3 | Redundant `main()` wrapper in `__main__.py` | Collapsed | [`src/bookwright/__main__.py:1-6`](src/bookwright/__main__.py#L1-L6) — `from bookwright.cli import app` + `if __name__ == "__main__": app()`. **Closed.** |
| R4 | Weak `assert "OK" in result.stdout` in `test_check_human` | Strengthened to count + per-module assertion | [`tests/test_cli_check.py:14-19`](tests/test_cli_check.py#L14-L19) — `assert result.stdout.count("OK") == len(RUNTIME_MODULES) + 1` plus `assert f"dependency:{module_name}" in result.stdout` for each. **Closed.** |
| R5 | No subprocess byte-exact test for `check --json` | Added | [`tests/test_cli_subprocess.py:38-55`](tests/test_cli_subprocess.py#L38-L55) — `test_check_json_subprocess_stdout_pure()` builds the expected JSON from `RUNTIME_MODULES` + `sys.version_info` and asserts byte equality plus empty stderr. **Closed.** |

Five-for-five closed. Coverage rose 89.02% → 91.03% as a side effect.
