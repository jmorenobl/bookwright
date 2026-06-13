# Quality Audit — 025-index-locations

**Scope:** 11 changed files in scope (3 source, 3 test, 1 fixture pair, 1 source-command, design/roadmap/plan docs) vs `main`
**Commit range:** `main`..`e4c7485`
**Date:** 2026-06-14
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md` (v1.4.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 1 |
| **Total** | 2 |

Coverage gate: **PASS** (0 modules below threshold; suite 97.13 %, changed modules `bible.py` 90.21 %, `_bible_builders.py` 96.30 %, `deferrals.py` 100 %; threshold = 80 %).

All four CI gates run clean: `ruff check` ✓, `ruff format --check` ✓ (250 files), `mypy --strict` ✓ (249 files, no issues), `pytest` ✓ (1209 passed, 1 skipped).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Everything an author can author … MUST be Markdown, TOML, or Turtle (RDF). … indices) are forbidden as canonical storage" | `.specify/memory/constitution.md:62` | layout | PASS | Locations are `bible/locations/*.md`; graph stays a derived `graph.ttl` cache |
| "The implementation language is Python 3.11+. The required toolchain is: …" (locked stack, no new deps) | `.specify/memory/constitution.md:74` | dependency | PASS | `pyproject.toml` not in diff — no runtime dep added; reuses rdflib/pydantic/pyyaml/slugify |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `.specify/memory/constitution.md:86` | layout | PASS | New module `src/bookwright/io/_bible_builders.py`; tests under `tests/io`, `tests/golem`, `tests/integrations` |
| "No source file (production or test) may exceed 500 lines; a file approaching the limit MUST be decomposed before" | `.specify/memory/constitution.md:99` | module-size | PASS | `bible.py` 384, `_bible_builders.py` 263 (was 500 at ceiling — the point of FR-013) |
| "Each CLI subcommand MUST live in its own module" | `.specify/memory/constitution.md:97` | module-size | N/A | No CLI surface touched this iteration |
| "Integrations MUST be subclasses of `SkillsIntegration` … `AGENT_CONFIG`-style dispatcher is explicitly forbidden" | `.specify/memory/constitution.md:108` | plugin-shape | N/A | No integration added; materialization rides the existing pipeline |
| "Bookwright MUST emit Agent Skills … and [not] legacy commands" (no `commands/` directory) | `.specify/memory/constitution.md:121` | directory-ban | PASS | Only edits source-command `.md`; `SKILL.md` re-materialized, no `.claude/commands/` write |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" (name ≤64, valid YAML) | `.specify/memory/constitution.md:133` | frontmatter-constraint | PASS | `test_bible_skill_teaches_location_frontmatter` asserts `name:`, `---` start, bilingual triggers; lint gate enforced |
| "v0 MUST hold a minimum of 80% line [coverage]" | `.specify/memory/constitution.md:149` | coverage-threshold | PASS | 97.13 % total; every changed module > 90 % |
| "Any CLI command whose output is meant to be consumed by an AI agent MUST [emit JSON-only on stdout]" | `.specify/memory/constitution.md:171` | io-contract | N/A | No CLI/envelope change; soft-miss reuses existing `unresolved_participants` channel |
| "[Frozen ontology axioms] MUST NOT be reopened in spec, plan, or [code]" (no class/property added) | `.specify/memory/constitution.md:190` | scope-ban | PASS | `golem/modules/setting.py` UNCHANGED; reuses `G13_Narrative_Location` + `dlp:generic-location` |
| "[deferred capabilities] MUST NOT be pulled into the [current milestone] … plumbing whose only justification is 'future X', MUST [be rejected]" | `.specify/memory/constitution.md:222` | scope-ban | PASS | Locations is the planned iteration 025; no Object/G16/narrative-structure plumbing added |
| "Every milestone lands through numbered iterations, never as freehand commits" | `.specify/memory/constitution.md:220` | workflow-step | PASS | Branch `025-index-locations`; full `specs/025-index-locations/` artifact set present |
| "`bookwright-design.md` … the README, and the `docs/` site are Spanish … Source code, identifiers, commit messages … are English" | `CLAUDE.md` (Language conventions) | other | PASS | Design § 7.2 rewritten in Spanish; source/tests/identifiers English |

No `FAIL` rows — Section 3 carries the two findings, both below convention authority (no MUST violated).

### Track integrity (A.3)

All 8 governance files under `specs/025-index-locations/` (`spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/location-frontmatter.md`, `checklists/requirements.md`) appear in `git diff main...HEAD`. `git status --porcelain` is empty — no uncommitted/untracked/staged governance artifacts. **OK — properly tracked on branch.**

### Workflow trail integrity (A.4)

Spec Kit sequence verified in reverse: `implement`→source under `src/` ✓; `tasks`→`tasks.md` (20 tasks, 0 open) ✓; `plan`→`plan.md` ✓; `clarify`→clarification annotations present (`## Clarifications` → Session 2026-06-14) ✓; `specify`→`spec.md` ✓. No downstream artifact exists while an upstream one is missing — **trail intact.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | D | MEDIUM | src/bookwright/io/_bible_builders.py:244-247 | The documented "`setting:` value that slugs to nothing → soft-miss" branch (`except EmptySlugError: slug = None`) has no test; lines 246-247 are the only uncovered new code. | Add a `test_bible.py` case with `setting: "!!!"` (non-blank, slugs empty) asserting node built + one `UnresolvedParticipant` + `loc.setting is None`. |
| R2 | B | LOW | src/bookwright/io/bible.py:59-85 | `__all__` re-exports ~16 underscore-prefixed internals (`_MapContext`, `_build_character`, …) so old imports resolve, coupling test/import sites to private names. | Acceptable as a behavior-preserving shim (documented in the docstring). Optionally migrate the few importers to `_bible_builders` in iteration 027's cleanup, then trim the re-export list. |

## 4. Remediation Detail

### R1 — Documented slugs-to-nothing `setting:` path is untested

- **Where:** `src/bookwright/io/_bible_builders.py:244-247`
- **Why it matters:** `_resolve_setting`'s docstring and the spec's Edge Cases both promise that a present `setting:` "that slugs to nothing … is a soft miss recorded as an `UnresolvedParticipant` (the location is still built, no edge, no abort)." The blank/whitespace case is tested (it returns early at line 242–243 before `make_slug`), but no test drives a non-blank value that `make_slug` rejects with `EmptySlugError`. That `except` arm is the single uncovered new branch (term-missing: `246-247`). A future refactor could silently turn this documented soft-miss into a crash with the suite still green.
- **Suggested change:** in `tests/io/test_bible.py`, add a case alongside `test_location_unresolved_setting_is_soft_miss`: write `bible/locations/odd.md` with `name: "The Quay"` and `setting: "!!!"`, build, and assert the location node exists with `setting is None` and exactly one `UnresolvedParticipant(path="bible/locations/odd.md", entity="The Quay", name="!!!")`. This is a test-only addition (read-only constraint preserved).

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| src/bookwright/io/bible.py | 90.21 % | 80 % | PASS |
| src/bookwright/io/_bible_builders.py | 96.30 % | 80 % | PASS |
| src/bookwright/golem/deferrals.py | 100 % | 80 % | PASS |
| **Total suite** | 97.13 % | 80 % | PASS |

`bible.py`'s missing lines (269→271, 285, 289–299, 314–352) are pre-existing collection-handling error paths (malformed `events:`/`relationships:` containers), not new code introduced by this iteration. `_bible_builders.py`'s 136/214 are likewise pre-existing coercer/ref error arms; only 246-247 is new (R1).

## 6. Inability-to-verify notes

None. All four gates ran locally to completion; the parity fixture (`bible/settings/the-old-crossing.md` present for `the-harbor.md`'s `setting:`) and both location fixtures resolve as designed.
