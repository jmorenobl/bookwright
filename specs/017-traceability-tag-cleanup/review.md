# Quality Audit — 017-traceability-tag-cleanup

**Scope:** 60 changed files vs `main` (1 new source file `tests/meta/test_no_traceability_tags.py`; 49 comment/docstring edits across `src/`+`tests/`; 10 spec-kit artifacts under `specs/017-*`)
**Commit range:** `main`..`9f7b04b`
**Date:** 2026-06-05
**Conventions discovered:** `CLAUDE.md`, `CONTRIBUTING.md`, `.specify/memory/constitution.md` (v1.3.0), plus this iteration's `spec.md` FR/SC set

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 0 (R3 withdrawn — false positive) |
| **Total** | 2 |

Coverage gate: **PASS** (0 modules below threshold, threshold = 80%; total 96.78%). Suite: 1046 passed, 1 skipped. `ruff check`, `ruff format --check`, `mypy --strict` (on new gate) all green. The no-regression gate was verified to bite (injected `# T013` probe → red, naming `tests/conftest.py:61: T013`, then reverted).

This is a clean, well-executed maintenance iteration. The headline outcome (zero forbidden tags) holds, the gate works, durable refs were preserved. The two surviving findings are an accuracy gap between the "comment-only" claim and one necessary non-comment edit (R1), and a narrowing of the gate's pattern vs. the literal FR wording (R2) — neither blocks merge, but both are worth recording before they mislead a future reader.

**Update (post-audit, R1/R2 fixed in a follow-up session; R3 withdrawn):** R2 has been corrected — the regex is now `\bT[0-9]{3}\b|\bUS-?[0-9]+\b|\+US[0-9]+`. R3 was withdrawn as a false positive (see §6).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "`US-x` / `+USx` … `T0xx` — task IDs from `tasks.md`" Forbidden in source/tests | `CONTRIBUTING.md:58-61` | scope-ban | PASS | `grep -rnIE '\bT0[0-9]{2}\b\|\bUS-?[0-9]+\b\|\+US[0-9]+' src/ tests/` → 0 matches |
| "`FR-0xx`/`SC-0xx` … `D-x` … Allowed in source/tests" | `CONTRIBUTING.md:51-56` | io-contract | PASS | Strip-token edits froze co-located `FR-011..FR-016`, `SC-001`, `D1/D2` byte-for-byte (verified in diff) |
| "Numbers freeze on merge … never renumbered" | `CONTRIBUTING.md:68-69` | scope-ban | PASS | Diff shows no `FR`/`SC`/`D`/`§` token value changed; only forbidden tokens removed |
| "Adding [a runtime dependency] requires a MINOR amendment" | `.specify/memory/constitution.md:204-205` | dependency | PASS | No change to `pyproject.toml`/`uv.lock`; gate uses stdlib `re`+`pathlib` |
| "All automated tests MUST live under `tests/`" | `.specify/memory/constitution.md:84` | layout | PASS | New gate at `tests/meta/test_no_traceability_tags.py` |
| "No source file … may exceed 500 lines" | `.specify/memory/constitution.md:97-98` | module-size | PASS | Gate = 66 lines; no other file grew materially |
| "v0 MUST hold a minimum of 80% line coverage" | `.specify/memory/constitution.md:147` | coverage-threshold | PASS | 96.78% total; 0 modules below 80% |
| "CI MUST run pytest, ruff, and mypy strict … red bar blocks merge" | `.specify/memory/constitution.md:161-162` | workflow-step | PASS | All four gates run green locally; gate rides `uv run pytest` → CI |
| "Writing to `.claude/commands/` … is prohibited" | `.specify/memory/constitution.md:119-121` | directory-ban | N/A | No skill/integration files in diff |
| "single JSON document on stdout and nothing else" (`--json`) | `.specify/memory/constitution.md:169-171` | io-contract | N/A | No CLI command added/changed |
| "adds plumbing whose only justification is 'future …' MUST be rejected" | `.specify/memory/constitution.md:227-230` | scope-ban | PASS | Gate enforces an already-stated CONTRIBUTING rule; no deferred-capability plumbing |
| FR-001: "`T` followed by exactly three digits MUST return zero occurrences" | `spec.md:157-159` | io-contract | FAIL | Gate regex `\bT0[0-9]{2}\b` matches only T000–T099, not T100–T999 (R2) |
| FR-008: "Changes MUST be confined to comments and docstrings" | `spec.md:181-183` | scope-ban | FAIL | One non-comment edit: pinned hash literal `tests/integrations/test_plugin_contract.py:44` (R1) |
| FR-007: existing refs "MUST NOT be renumbered, reworded" | `spec.md:178-180` | scope-ban | PASS | Verified byte-for-byte across all strip-token rows |
| FR-012: "Artifacts under `specs/` MUST NOT be modified … MUST NOT be scanned" | `spec.md:194-196` | scope-ban | PASS | Only `specs/017-*` artifacts changed; gate `_SCAN_ROOTS = ("src","tests")` excludes `specs/` |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A/D | MEDIUM | tests/integrations/test_plugin_contract.py:44 | FR-008 "comment-only" claim is contradicted by a necessary non-comment edit: the pinned sha256 of `integrations/base.py` was updated because the comment edit changed that file's content | Acknowledge the cascade in plan.md/spec.md (or exclude pinned hashes from the comment-only claim); behaviour is preserved so no code action needed |
| R2 | A | MEDIUM | tests/meta/test_no_traceability_tags.py:18 | Gate regex `\bT0[0-9]{2}\b` under-enforces FR-001 ("T + exactly three digits") — task IDs `T100`–`T999` would regress undetected | Widen to `\bT[0-9]{3}\b` to match FR-001/SC-001, or reconcile FR-001 wording with the `T0xx` Assumption |
| ~~R3~~ | B/C | ~~LOW~~ WITHDRAWN | tests/meta/test_no_traceability_tags.py:18 | **False positive.** Claimed `\+US[0-9]+` is redundant — it is not: it catches `+US<n>` followed by a word char (e.g. `+US3foo`), which the `\b`-terminated `\bUS-?[0-9]+\b` misses, and preserves the `+` in the reported token | No change — the alternative is load-bearing; verified empirically (see note below) |

## 4. Remediation Detail

### R1 — "comment-only" claim vs. the pinned-hash cascade

- **Where:** `tests/integrations/test_plugin_contract.py:44` (and the claims in `specs/017-traceability-tag-cleanup/plan.md:60-62`, `spec.md:181-183` FR-008, `tasks.md:208-212` T021).
- **Why it matters:** FR-008 and plan.md state the diff is "confined to comments and docstrings" / "the only `src/` touches are two comment/docstring lines." That is *almost* true — but editing the `(T013)` comment in `src/bookwright/integrations/base.py` changed that file's content, and `test_plugin_contract.py` pins its sha256 in `_PINNED_FILE_HASHES`. So a non-comment data literal had to change too (`6335ec…` → `e8ae1c8…`). The edit is correct and behaviour-preserving (the test still asserts the same integrity invariant against the new content), but T021's checkpoint was marked `[X]` while the artifacts assert something the diff doesn't quite satisfy. A future reader trusting "comment-only" will be surprised by the hash line.
- **Suggested change:** No source change required. Add one sentence to plan.md's "Scale/Scope" note (and/or FR-008) acknowledging that a pinned-hash constant tracking a comment-edited source file is an expected, behaviour-preserving exception. This keeps the governance narrative honest. The auditing pin comment at `test_plugin_contract.py:38-39` already documents the recompute protocol, so the edit itself is well-formed.

### R2 — Gate pattern is narrower than FR-001

- **Where:** `tests/meta/test_no_traceability_tags.py:18` — `FORBIDDEN = re.compile(r"\bT0[0-9]{2}\b|...")`.
- **Why it matters:** FR-001 and SC-001 say "`T` followed by **exactly three digits**." The implemented `\bT0[0-9]{2}\b` requires the first digit to be `0`, so it matches only `T000`–`T099`. Today every `tasks.md` ID is in `T001`–`T023`, so the gate is correct *now*, but a future iteration whose `tasks.md` reaches `T100`+ could leak a `T1xx` tag into `src/`/`tests/` and the gate would stay green — silently defeating the permanence guarantee (US3) the gate exists to provide. The spec is internally inconsistent: FR-001/SC-001 say "three digits" while `spec.md:245` Assumptions and `plan.md:15` use the `T0xx` form. The gate followed the narrower form.
- **Suggested change:** change the first alternative to `\bT[0-9]{3}\b` (matches FR-001 literally), or, if `T0xx` is genuinely the intended contract, amend FR-001/SC-001 to say "`T0` followed by two digits" so the spec and the gate agree. Verify the wider pattern still produces zero matches on the current tree (it does — the stricter sweep `\bT[0-9]{3}\b` over `src/`+`tests/` returns none today).

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| (whole `src/bookwright/`) | 96.78% | 80% | PASS |
| `tests/meta/test_no_traceability_tags.py` (new) | n/a (test module; exercised by the run) | — | PASS |

No changed source module dropped below threshold; the cleanup edited only comments/docstrings (plus one pinned-hash literal, R1), leaving executed lines and coverage unchanged (SC-003 holds).

## 6. Inability-to-verify notes

- Full-repo `mypy --strict` over `src` + `tests` was not re-run end-to-end in this audit (it is a CI gate and was claimed green in T023); `mypy --strict` was run on the only new file and passed. `ruff check` and `ruff format --check` were re-run on the full tree and passed.
- R1's "behaviour-preserving" verdict rests on the test still passing against the new hash, which it does (1046 passed); the audit did not independently re-derive the sha256.
- **R3 withdrawn — false positive.** The audit claimed `\+US[0-9]+` was redundant with `\bUS-?[0-9]+\b`. An empirical check (10 cases over both patterns) disproved it: for `x+US3y` the full regex matches `+US3` while the second alternative matches **nothing** (its trailing `\b` fails before the word char `y`), and for `+US12`/`(+US42)` the third alternative preserves the leading `+` in the reported token. Removing it would shrink the gate's coverage and degrade its failure messages — a behaviour change, not a simplification. The regex is correct as written.
