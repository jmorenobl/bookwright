# Quality Audit — 005-golem-domain-model

**Scope:** 14 code files (5 source, 9 test) + `CONTRIBUTING.md`, vs `main`
**Commit range:** `main`..`c9edcf1`
**Date:** 2026-06-01
**Conventions discovered:** `.specify/memory/constitution.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 2 |
| **Total** | 4 |

Coverage gate: **PASS** (0 changed modules below threshold, threshold = 80%). Full suite: 437 passed, 98% total; every changed `golem` module is 98–100%. `ruff check`, `ruff format --check`, and `mypy --strict` all clean on the changed tree.

This branch adds the character-attributes layer (`born`/`died`/`features`/`narrative_roles`) on top of the already-merged identity-only GOLEM model. The work is high quality: the declarative `CrossRef` mechanism is applied uniformly across concepts, every namespace term is frozen-ontology-backed (SC-007 test asserts this), and the attribute-free `Character` is proven byte-identical to the prior identity-only output. Findings are quality nits, not correctness or governance failures.

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

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | C | MEDIUM | src/bookwright/golem/base.py:90-95 | `to_triples` docstring claims "overriding … is unnecessary for any concept … a character's owned feature / role sub-trees included" — but `CharacterFeature`, `CharacterRole`, and `Dimension` all override it | Correct the docstring: owned sub-nodes *do* override because `CrossRef` handles only URIRef refs and `xsd:string` literals, not `rdfs:label` literals, conditional sub-trees, or `xsd:gYear` |
| R2 | B | MEDIUM | src/bookwright/golem/modules/feature.py:106-107,123 | `model_post_init` runs *before* the `@model_validator(mode="after")`, so the neither-variant case is caught by `assert self.label is not None` (123) — making the validator's guard at 106-107 unreachable dead code (uncovered) and validation dependent on a `-O`-strippable assert | Move the variant check to a `mode="before"` validator (or compute URIs after validation) so 106-107 runs; under `python -O` the neither-variant case currently degrades to an opaque `TypeError` from `slugify(None)` |
| R3 | D | LOW | src/bookwright/golem/base.py:67 | `uri_base: str` is unvalidated; `conftest` documents "absolute http(s), trailing slash" but nothing enforces it, so a missing trailing slash silently yields malformed URIs | Add a Pydantic field validator asserting an `http(s)` scheme and trailing `/`; low urgency since the manifest wiring that supplies it lands in iteration 6 |
| R4 | D | LOW | tests/golem/test_character_attributes.py:191-197 | `test_character_feature_requires_exactly_one_variant` asserts only `pytest.raises(ValidationError)`; the neither-variant case passes because pydantic wraps the *AssertionError*, not the validator's intended `ValueError` — masking R2 | Assert on the error cause/message (`match=`), which would have surfaced that line 107 never runs |

## 4. Remediation Detail

### R1 — `to_triples` docstring overstates the no-override invariant

- **Where:** [base.py:90-95](../../src/bookwright/golem/base.py#L90-L95)
- **Why it matters:** The docstring tells a future maintainer that no concept needs to override `to_triples`, explicitly including "a character's owned feature / role sub-trees." That is false: [feature.py](../../src/bookwright/golem/modules/feature.py) overrides `to_triples` in `Dimension` (L65), `CharacterFeature` (L126), and `CharacterRole` (L155). A maintainer trusting the docstring could "simplify" those overrides away or misjudge how the owned sub-tree is emitted.
- **Suggested change:** Reword to state the real rule: the declarative `cross_refs` path covers URIRef references and `xsd:string` literals; concepts that emit `rdfs:label` (plain literal), a conditional sub-tree keyed on a discriminator, or a typed literal such as `xsd:gYear` (the `feature` module) override `to_triples` deliberately.

### R2 — Variant validation relies on a `model_post_init` assert that preempts the validator

- **Where:** [feature.py:95-110](../../src/bookwright/golem/modules/feature.py#L95-L110) and [feature.py:122-124](../../src/bookwright/golem/modules/feature.py#L122-L124)
- **Why it matters:** In this Pydantic version `model_post_init` executes *before* `@model_validator(mode="after")` (verified empirically). For the "neither `label` nor `kind`+`year`" case, `model_post_init` reaches `assert self.label is not None` (L123) and raises `AssertionError` before `_exactly_one_variant` ever runs its L106-107 guard. Consequences:
  1. **Dead code / coverage gap:** L107 is unreachable and shows as uncovered (the 1 missing statement in `feature.py`'s 98%).
  2. **Validation depends on `assert`:** under `python -O` the assert is stripped; the neither-variant case then falls through to `make_slug(self.label)` and raises `TypeError: decoding to str: need a bytes-like object, NoneType found` — an opaque error instead of the intended clean `ValidationError`.
  - The L132 assert (`self._dimension is not None`) is a fine type-narrowing invariant and is *not* part of this finding.
- **Suggested change:** Perform the exactly-one-variant check where it runs before identity construction — e.g. a `@model_validator(mode="before")` on the raw dict, or guard `model_post_init` itself so the URI is only built once the variant is known valid. Then L106-107 becomes the single source of truth and L123's assert can stay purely as a type-narrowing invariant.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| golem/__init__.py | 100% | 80% | PASS |
| golem/base.py | 100% | 80% | PASS |
| golem/namespaces.py | 100% | 80% | PASS |
| golem/modules/character.py | 100% | 80% | PASS |
| golem/modules/feature.py | 98% (L107 unreachable — see R2) | 80% | PASS |
| **Full suite total** | 98% | 80% | PASS |

## 6. Inability-to-verify notes

- None. All four gates ran locally and the full test suite (437 tests) passed. The single uncovered line (`feature.py:107`) is explained and attributed in R2 rather than left as an unknown.
