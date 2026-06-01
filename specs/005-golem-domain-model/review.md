# Quality Audit — 005-golem-domain-model

**Scope:** 4 changed source files + 8 changed test files + 3 docs vs `main`
**Commit range:** `main`..`a433439` (merge-base `22bed02`; this branch's 4 newest commits = the iter-5 character-attribute *fix*)
**Date:** 2026-05-31
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.1.0), `CONTRIBUTING.md`, `pyproject.toml`
**Invocation lens:** "verify the GOLEM domain model was implemented correctly and that the previously-detected problems were fixed."

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 1 (resolved) |
| **Total** | 1 |

Coverage gate: **PASS** — full suite 98.08%, **golem module 100%** (every file under `src/bookwright/golem/` at 100% line + branch), threshold = 80%. `431 passed`. `ruff check`, `ruff format --check`, `mypy --strict` all clean on the golem subtree.

**Headline:** The character-attribute extension that iteration-5 was under-scoped for (the [HANDOFF.md](../../HANDOFF.md) fix) is implemented correctly, additively, and within the frozen vocabulary. **All three findings from the prior audit (R1, R2, R3) are resolved.** The one new LOW finding (slug-collision in feature URIs) has also been **resolved structurally** — biographical features moved to a disjoint `feature/bio/{kind}` subspace, making the collision impossible by construction (see §4 R1).

### Prior-audit regression check (the "detected problems")

| Prior ID | Was | Now | Evidence |
|---|---|---|---|
| R1 (HIGH) | `test_us1_worked_examples` carried user-story jargon | **FIXED** | `grep test_us[0-9] tests/` → none |
| R2 (HIGH) | `+US5`/`US5-x`/`T0xx` tags in golem docstrings/comments | **FIXED** | `grep 'US[0-9]\|+US\|T0[0-9][0-9]' src/bookwright/golem tests/golem` → none |
| R3 (decided) | Trace-tag policy (`FR`/`SC`/`D`/`§`) needed sanctioning in docs | **FIXED** | `CONTRIBUTING.md:45-75` "Traceability tags in code" — allowed/forbidden classes, relative resolution, freeze-on-merge |

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "frozen terms only — drop nothing, mint nothing" / SC-001 zero terms outside frozen vocab | HANDOFF.md:18 / spec | scope-ban | PASS | `test_all_emitted_terms_are_frozen`, `test_class_iris_are_in_frozen_terms`, `test_term_closure_over_frozen_ontology` all green; G17/E54/E55 present in `golem.ttl` |
| "Adding a runtime dependency requires an amendment" — pyyaml deferred to iter-6 | constitution II / HANDOFF.md:82 | dependency | PASS | `pyproject.toml` NOT in branch diff; no new dep added |
| "No source file may exceed 500 lines" | constitution IV:94 | module-size | PASS | character.py 89, feature.py 133, namespaces.py 160, base.py 118 |
| "All production code under `src/bookwright/`, tests under `tests/`" | constitution III:81 | layout | PASS | golem code under `src/bookwright/golem/`; tests under `tests/golem/` |
| "Plain text source of truth — no binary under src/" | constitution I:54 | layout | PASS | only `.py`/`.ttl`/`.md` in diff |
| "v0 MUST hold ≥80% line coverage across src/bookwright/" | constitution VIII:144 | coverage-threshold | PASS | 98.08% total; golem 100% |
| "Source code, identifiers, commit messages in English" | CLAUDE.md:143 | layout | PASS | all identifiers English (Spanish only in test *fixture data* strings, allowed) |
| "Each CLI subcommand in own file ≤500 lines" | constitution IV:92 | module-size | N/A | no `commands/` files in this branch's diff |
| "Emit Agent Skills only; no `.claude/commands/`" | constitution VI:114 | directory-ban | N/A | no skills/commands emitted by golem (pure domain model) |
| "`--json` single JSON doc on stdout" | constitution IX:155 | io-contract | N/A | golem is a library layer, no CLI surface on this branch |
| Names/identifiers must not carry planning jargon (`usN`) | prior-audit lens | naming | PASS | R1/R2 remediated (see §1 regression table) |
| Allowed trace tags `FR`/`SC`/`D`/`§`; `US`/`T0xx` forbidden in code | CONTRIBUTING.md:45 | other | PASS | golem uses only `FR`/`SC`/`D`/`§`; no `US`/`T0xx` |

### Track-integrity (A.3) & workflow-trail (A.4)

- **Track integrity:** clean. `git status --porcelain` is empty; every golem file on disk is tracked. The 9 golem files absent from `main...HEAD` (base.py, serialize.py, slug.py, errors.py, event/inference/narrative/relationship/setting.py) are **inherited from `main`** (merge-base `22bed02`), the OK case in the decision table — they are the already-merged identity-only model, not missing artifacts.
- **Workflow trail (Spec Kit):** complete. `specs/005-golem-domain-model/` holds spec.md, research.md, plan.md, tasks.md, contracts/golem_api.md, data-model.md, quickstart.md, and checklists/. No downstream-without-upstream gap.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | LOW (resolved) | src/bookwright/golem/modules/feature.py:95 | A free-text feature whose slug equals `"birth"`/`"death"` collided with the biographical feature URI and was silently deduped away when the character also had `born`/`died` | RESOLVED — biographical features moved to the disjoint `{c}/feature/bio/{kind}` subspace; collision now impossible by construction (no guard needed). See §4. |

## 4. Remediation Detail

_No CRITICAL or HIGH findings._ The one LOW was **resolved** (structural fix, not a guard):

### R1 — Free-text feature could collide with a biographical feature URI — RESOLVED

- **Was:** biographical and free-text features shared the `{character.uri}/feature/{token}` namespace, distinguished only by whether the token happened to be `birth`/`death`. `Character(born=1828, features=("birth",))` silently dropped the free-text feature via the dedup `seen` set. Data loss on a contrived-but-legal input; flat namespace was the root cause.
- **Fix (chosen over a runtime guard):** biographical features now live under a disjoint sub-segment — `{character.uri}/feature/bio/{kind}` ([feature.py:95](../../src/bookwright/golem/modules/feature.py#L95)) — while free-text stays at `{character.uri}/feature/{slug}`. A slug can never contain `/`, so the two subspaces **cannot** collide; the collision is impossible by construction, not rejected at runtime. The dedup in [character.py](../../src/bookwright/golem/modules/character.py) reverts to deduping free-text values only. Net effect: **code removed** (no `ReservedFeatureTokenError`, no guard) rather than added.
- **Verification:** `test_free_text_birth_feature_coexists_with_born_year` asserts `features=("birth",)` + `born=1828` now yields two distinct nodes. golem coverage 100%, full suite 431 passed, contract (`golem_api.md`) and `data-model.md` updated to the `bio/` URI shape. iteration-6/10 are unaffected (queries traverse predicates, not URI string patterns), and iter-5 is unmerged so the contract change is free.

## 5. Coverage Detail

| Module | Stmts | Miss | Branch | Coverage | Threshold | Status |
|---|---|---|---|---|---|---|
| golem/__init__.py | 13 | 0 | 0 | 100% | 80% | PASS |
| golem/base.py | 50 | 0 | 10 | 100% | 80% | PASS |
| golem/errors.py | 11 | 0 | 0 | 100% | 80% | PASS |
| golem/modules/character.py | 51 | 0 | 16 | 100% | 80% | PASS |
| golem/modules/feature.py | 63 | 0 | 10 | 100% | 80% | PASS |
| golem/modules/event.py | 15 | 0 | 0 | 100% | 80% | PASS |
| golem/modules/inference.py | 21 | 0 | 0 | 100% | 80% | PASS |
| golem/modules/narrative.py | 22 | 0 | 0 | 100% | 80% | PASS |
| golem/modules/relationship.py | 15 | 0 | 0 | 100% | 80% | PASS |
| golem/modules/setting.py | 13 | 0 | 0 | 100% | 80% | PASS |
| golem/namespaces.py | 54 | 0 | 2 | 100% | 80% | PASS |
| golem/serialize.py | 12 | 0 | 4 | 100% | 80% | PASS |
| golem/slug.py | 8 | 0 | 2 | 100% | 80% | PASS |
| **Full repo** | 1628 | 21 | 352 | **98.08%** | 80% | PASS |

## 6. Inability-to-verify notes

- None. All four gates ran locally and the golem subtree is fully covered. The 21 missed statements across the full repo are entirely outside golem (untouched merged modules) and the project gate still passes at 98%.
- R1's reachability depends on iteration-6's bible-frontmatter parser (not on this branch); flagged for confirmation there rather than treated as a defect here.
