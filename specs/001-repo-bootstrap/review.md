# Quality Audit — 001-repo-bootstrap

**Scope:** 8 changed files vs main (3 tracked diffs + 5 untracked new files)
**Commit range:** main..3486bf2
**Date:** 2026-05-28
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 1 |
| **Total** | **4** |

Coverage gate: UNKNOWN — no source tree exists yet and no test runner is available. The coverage threshold (≥ 80 %, Constitution Principle VIII) cannot be measured until `src/bookwright/` and `tests/` are created in the implementation phase.

**Bootstrap case note:** the diff contains only Spec Kit scaffolding artifacts — `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `checklists/`, and `.specify/feature.json`. No Python source code is present. Per skill protocol, **Passes B (code smells) and C (design patterns) are skipped** — there is no production code to analyse. Pass A (conventions) runs in full. Pass D (tests + security) is limited to structural observations.

---

## 2. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | HIGH | `specs/001-repo-bootstrap/` (branch state) | `tasks.md` has not been generated — the branch is mid-workflow between `/speckit-plan` and `/speckit-tasks`, so `/speckit-implement` cannot legally run yet | Run `/speckit-tasks` then `/speckit-analyze` before proceeding to implementation |
| R2 | A | MEDIUM | `specs/001-repo-bootstrap/plan.md:108-112` | Constitution Principle VIII (test discipline, ≥ 80 % coverage — NON-NEGOTIABLE) is explicitly downgraded to non-blocking for this PR with a "surface too small" justification; the constitution's MUST language is binding and the exemption is not backed by a constitutional amendment | Either accept the coverage gate in CI from day one (low cost at bootstrap scale), or open a PATCH amendment to the constitution that explicitly names the M0 bootstrap as an allowed exception |
| R3 | A | MEDIUM | `specs/001-repo-bootstrap/plan.md:157-214` (Project Structure section) | `quickstart.md` appears in the spec directory but is not listed in the "Documentation (this feature)" file tree declared in `plan.md` — the plan's own structure table omits it, creating a minor inconsistency between the declared and actual directory shape | Add `quickstart.md` to the documentation tree in `plan.md § Project Structure`, or note it explicitly in the "Directorios explícitamente NO creados" rationale |
| R4 | D | LOW | `specs/001-repo-bootstrap/contracts/check.schema.json:28` | The `name` field regex `^[a-z][a-z0-9_]*(?::[a-z][a-z0-9_]*)?$` uses only a single `?` optional group after `:` — this means a check name can only have one colon-delimited segment after the prefix (e.g., `dependency:typer` is fine, but a hypothetical `dependency:pydantic:v2` would fail). The constraint is undocumented as intentional | Add a comment or `description` field to the schema clarifying this is a deliberate two-segment limit, or adjust the pattern if deeper namespacing is anticipated |

---

## 3. Remediation Detail

### R1 — tasks.md missing: branch is mid-workflow

- **Where:** `specs/001-repo-bootstrap/` — the directory lacks `tasks.md`
- **Why it matters:** CLAUDE.md mandates the fixed Spec Kit sequence `/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement`. Skipping `/speckit-tasks` means there are no task definitions for the implementation to consume; running `/speckit-implement` in this state would bypass the governance workflow that CLAUDE.md treats as required. The checklist in `quickstart.md` also references task completion as a "done" gate.
- **Suggested change:** invoke `/speckit-tasks` immediately (no code changes needed), then run `/speckit-analyze` for the cross-artifact consistency check, then proceed to `/speckit-implement`.

### R2 — Coverage gate downgraded without constitutional amendment

- **Where:** `specs/001-repo-bootstrap/plan.md:108-112` (Principle VIII row in Constitution Check table); `specs/001-repo-bootstrap/spec.md:172` (Assumptions section)
- **Why it matters:** Constitution Principle VIII is tagged NON-NEGOTIABLE and CLAUDE.md reiterates this. The plan's "⚠️ Parcial justificado" verdict and the spec's Assumption ("no se exige el umbral como gate bloqueante para esta PR") are technically a constitutional override — and the amendment procedure in the constitution (`.specify/memory/constitution.md:228-242`) requires a dedicated PR with a version bump and Sync Impact Report. Proceeding without that amendment leaves the coverage gate in an ambiguous state for future audits.
- **Suggested change:** the lowest-friction path is to include `--cov-fail-under=80` in the pytest configuration from day one, since the bootstrap surface (`__init__.py`, `cli.py`, `commands/version.py`, `commands/check.py`) is small enough that the smoke tests described in the spec would naturally exceed 80 % coverage. If the threshold genuinely cannot be met, open a PATCH amendment to constitution.md naming the M0 bootstrap as a documented exception before merging.

---

## 4. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/` (all) | N/A — not yet created | 80 % | UNKNOWN |

---

## 5. Inability-to-verify notes

- **No Python source code:** `src/bookwright/` does not exist. Passes B (code smells), C (design patterns), and the implementation-level portion of Pass D cannot run. This is expected at iteration 1 pre-implementation state.
- **No `pyproject.toml` / test runner:** `pytest`, `ruff`, and `mypy` cannot be invoked. Coverage measurement is deferred to post-implementation.
- **`tasks.md` absent:** the skill cannot verify that all planned tasks are covered by implementation artifacts, since the task list has not been generated yet.
- **`quickstart.md` plan discrepancy (R3):** the file `specs/001-repo-bootstrap/quickstart.md` exists on disk and is clearly intentional, but the plan.md documentation tree does not enumerate it. The content is sound; this is a documentation consistency nit.
