# Quality Audit — 005-golem-domain-model

**Scope:** 14 code files (5 source, 9 test) + `CONTRIBUTING.md`, vs `main`
**Commit range:** `main`..`c9edcf1`
**Date:** 2026-06-01
**Conventions discovered:** `.specify/memory/constitution.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`

## 1. Summary

| Severity | Open | Resolved |
|---|---|---|
| CRITICAL | 0 | — |
| HIGH | 0 | — |
| MEDIUM | 0 | 2 (R1, R2) |
| LOW | 2 | 0 |
| **Total** | 2 | 2 |

Coverage gate: **PASS** (0 changed modules below threshold, threshold = 80%). Full suite: 437 passed, 98% total; after the R2 fix every changed `golem` module is **100%**. `ruff check`, `ruff format --check`, and `mypy --strict` all clean on the changed tree.

This branch adds the character-attributes layer (`born`/`died`/`features`/`narrative_roles`) on top of the already-merged identity-only GOLEM model. The work is high quality: the declarative `CrossRef` mechanism is applied uniformly across concepts, every namespace term is frozen-ontology-backed (SC-007 test asserts this), and the attribute-free `Character` is proven byte-identical to the prior identity-only output. Both MEDIUM findings (R1, R2) have since been remediated and verified; the two remaining LOW items are non-blocking (R3 is deferred to iteration 6, R4 is a moot test-tightening once R2 is fixed).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden" | `constitution.md:56` | layout | PASS | Only RDF/Turtle emitted; frozen ontology is `.ttl`; no binary stores |
| "Runtime dependencies (minimum set): … Adding to this list requires a MINOR amendment" | `constitution.md:190` | dependency | PASS | `pyproject.toml` not modified on branch; `uuid_utils`, `rdflib`, `pydantic`, `slugify` all in allowed set |
| "All production code MUST live under `src/bookwright/`. All … tests MUST live under `tests/`" | `constitution.md:81` | layout | PASS | All 5 source files under `src/bookwright/golem/`; all 9 tests under `tests/golem/` |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:93` | module-size | PASS | Largest changed file is 213 lines (`test_character_attributes.py`) |
| "Each CLI subcommand MUST live in its own module under `src/bookwright/commands/<name>.py`" | `constitution.md:92` | module-size | N/A | No CLI command in this iteration (domain model only) |
| "Integrations MUST be … subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`" | `constitution.md:103` | plugin-shape | N/A | No integration code on this branch |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" | `constitution.md:116` | directory-ban | N/A | No skill emission on this branch |
| "Every generated `SKILL.md` MUST satisfy the agentskills.io specification" | `constitution.md:128` | frontmatter-constraint | N/A | No `SKILL.md` generated on this branch |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:144` | coverage-threshold | PASS | 98% total; changed modules 98–100% |
| "CI MUST run pytest, ruff, and mypy strict on every push … a red bar blocks merge" | `constitution.md:148` | coverage-threshold | PASS | All three pass locally on the changed tree |
| "command whose output is … consumed by an AI agent MUST accept a `--json` flag" | `constitution.md:157` | io-contract | N/A | No CLI command; `errors.py` provides `to_json()` for the future `--json` surface |
| "rdflib over Grafeo in v0 … These MUST NOT be reopened" | `constitution.md:170` | scope-ban | PASS | `rdflib` only; no `Grafeo`/`GrafeoIndexer` import or plumbing |
| "adds plumbing whose only justification is 'future preset support' MUST be rejected" | `constitution.md:215` | scope-ban | PASS | No deferred-feature plumbing; `CrossRef` flags all exercised by current concepts |
| "Forbidden in source/tests: `US-x` / `+USx` … `T0xx` task IDs" | `CONTRIBUTING.md:58` | other | PASS | grep found zero `US-`/`T0xx` tags in changed source/tests |
| "Refs resolve relative to the file's iteration" (FR/SC/D/design §) | `CONTRIBUTING.md:65` | other | PASS | Inline refs (FR-016…021, SC-007, D1/D5/D8) are this iteration's |

**Track integrity (A.3):** every file in `src/bookwright/golem/`, `tests/golem/`, and `specs/005-golem-domain-model/` is git-tracked and the working tree is clean (`git ls-files` matches disk modulo `__pycache__`). No untracked or staged-but-uncommitted governance artifacts. **Verdict: OK.**

**Workflow-trail integrity (A.4):** `spec.md` → Clarifications section present → `plan.md` → `tasks.md` → `research.md`/`data-model.md` → source under `src/bookwright/golem/`. Full Spec Kit trail intact. **Verdict: OK.**

## 3. Findings

| ID | Pass | Severity | Status | Location | Summary | Recommendation |
|---|---|---|---|---|---|---|
| R1 | C | MEDIUM | ✅ RESOLVED | src/bookwright/golem/base.py:92-98 | `to_triples` docstring claimed "overriding … is unnecessary for any concept … a character's owned feature / role sub-trees included" — but `CharacterFeature`, `CharacterRole`, and `Dimension` all override it | Done: docstring now states `cross_refs` covers only URIRef refs / `xsd:string` literals and names the three deliberate overrides |
| R2 | B | MEDIUM | ✅ RESOLVED | src/bookwright/golem/modules/feature.py:93-117 | `model_post_init` ran *before* the `@model_validator(mode="after")`, so the neither-variant case was caught by `assert self.label is not None` — making the validator's guard unreachable dead code (uncovered) and validation dependent on a `-O`-strippable assert | Done: variant check moved to `@model_validator(mode="before")`; neither-variant now raises a clean `ValidationError` (verified identical under `python -O`); `feature.py` coverage 98% → 100% |
| R3 | D | LOW | OPEN | src/bookwright/golem/base.py:67 | `uri_base: str` is unvalidated; `conftest` documents "absolute http(s), trailing slash" but nothing enforces it, so a missing trailing slash silently yields malformed URIs | Add a Pydantic field validator asserting an `http(s)` scheme and trailing `/`; low urgency since the manifest wiring that supplies it lands in iteration 6 |
| R4 | D | LOW | OPEN (moot) | tests/golem/test_character_attributes.py:191-197 | `test_character_feature_requires_exactly_one_variant` asserts only `pytest.raises(ValidationError)` without `match=` | With R2 fixed the test now passes for the right reason; tightening with `match=` remains an optional nicety |

## 4. Remediation Detail

### R1 — `to_triples` docstring overstated the no-override invariant ✅ RESOLVED

- **Where:** [base.py:92-98](../../src/bookwright/golem/base.py#L92-L98)
- **Why it mattered:** The docstring told a future maintainer that no concept needs to override `to_triples`, explicitly including "a character's owned feature / role sub-trees." That was false: [feature.py](../../src/bookwright/golem/modules/feature.py) overrides `to_triples` in `Dimension`, `CharacterFeature`, and `CharacterRole`.
- **Fix applied:** the docstring now states the real rule — `cross_refs` covers only URIRef references and `xsd:string` literals, and names the three deliberate overrides (`rdfs:label` plain literal, discriminator-keyed sub-tree, `xsd:gYear` typed literal) as cases that fall outside that path.

### R2 — Variant validation relied on a `model_post_init` assert that preempted the validator ✅ RESOLVED

- **Where:** [feature.py:93-117](../../src/bookwright/golem/modules/feature.py#L93-L117)
- **Why it mattered:** In this Pydantic version `model_post_init` executes *before* `@model_validator(mode="after")` (verified empirically). The "neither `label` nor `kind`+`year`" case hit `assert self.label is not None` in `model_post_init` before the validator ran, making the validator's guard unreachable dead code (the 1 uncovered statement) and making validation depend on an assert — under `python -O` it degraded to an opaque `TypeError` from `slugify(None)`.
- **Fix applied:** `_exactly_one_variant` is now a `@model_validator(mode="before")` that inspects the raw kwargs dict, so it runs before identity construction. Verified: the neither-variant case raises a clean `ValidationError` ("requires either `label` or (`kind` + `year`)") **identically under `python -O`**, and `feature.py` coverage rose from 98% to **100%** (no more dead branch). The remaining asserts in the class are now purely type-narrowing invariants guaranteed by the validator.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| golem/__init__.py | 100% | 80% | PASS |
| golem/base.py | 100% | 80% | PASS |
| golem/namespaces.py | 100% | 80% | PASS |
| golem/modules/character.py | 100% | 80% | PASS |
| golem/modules/feature.py | 100% (was 98%; dead branch removed by R2 fix) | 80% | PASS |
| **Full suite total** | 98% | 80% | PASS |

## 6. Inability-to-verify notes

- None. All four gates ran locally and the full test suite (437 tests) passed. After the R2 fix there are no unreachable branches in the changed modules.
