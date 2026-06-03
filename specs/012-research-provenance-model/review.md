# Quality Audit — 012-research-provenance-model

**Scope:** 13 changed source/test/config files vs `main` (25 total incl. specs)
**Commit range:** `main..2a0f59a`
**Date:** 2026-06-03
**Conventions discovered:** `CLAUDE.md`, `CONTRIBUTING.md`, `.specify/memory/constitution.md` (v1.3.0)

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 1 |
| **Total** | 4 |

Coverage gate: **PASS** (0 changed modules below threshold, threshold = 80%). Suite: 920 passed, 1 skipped; total coverage 95.92%. `ruff check` + `mypy` clean on the new modules.

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … forbidden as canonical storage" | `constitution.md:59` | layout | PASS | Diff adds only `.py`/`.ttl`/`.md`/`.json`; `graph.ttl` is the documented derived cache |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | `constitution.md:76` | dependency | PASS | `pyproject.toml` not in diff; new code reuses `uuid_utils`, `pydantic`, `rdflib`, `pyyaml` |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | `constitution.md:84` | layout | PASS | All src under `src/bookwright/`, all tests under `tests/` |
| "No source file (production or test) may exceed 500 lines" | `constitution.md:97` | module-size | PASS | Largest changed file `io/research.py` = 404; all others < 332 |
| "Integrations MUST be implemented as subclasses of `SkillsIntegration`…" | `constitution.md:106` | plugin-shape | N/A | No integration code touched on this branch |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … is prohibited" | `constitution.md:119` | directory-ban | PASS | No skill/command directories written (research skill is deferred to iter 14) |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | `constitution.md:147` | coverage-threshold | PASS | 95.92% total; `research.py` 87.63%, `provenance.py` 98.31% (see §5) |
| "Any CLI command … MUST accept a `--json` flag and … emit a single … JSON document on stdout and nothing else" | `constitution.md:169` | io-contract | PASS | `graph build` adds research metrics to `BuildReport.to_json`; prose goes to `Console(stderr=True)` |
| "GOLEM as the ontology … These MUST NOT be reopened" (frozen 17-class closure) | `constitution.md:182` | scope-ban | PASS | `Source`→`crm:E55_Type`, `Finding`/`Anchor`→`crm:E13`; `bw:` terms live in `sources.ttl`, not `golem.ttl`; none added to `CLASS_IRI` |
| "A pull request that … adds plumbing whose only justification is 'future …' MUST be rejected" | `constitution.md:227` | scope-ban | PASS | `factual_anchor` validator + `bookwright-research` skill correctly NOT implemented; warnings emitted, enforcement deferred to iter 15 |
| "CI MUST run pytest, ruff, and mypy strict on every push" | `constitution.md:161` | workflow-step | PASS | Suite green; ruff + mypy clean on new files |
| "FR-0xx / SC-0xx / D-x / `bookwright-design.md § N.M` — allowed [traceability tags] in source/tests" | `CONTRIBUTING.md:51` | other | PASS | New code uses `FR-0xx`, `research D-x`, `§ 20` refs throughout |
| "Forbidden in source/tests: US-x / +USx … T0xx — task IDs from tasks.md" | `CONTRIBUTING.md:58` | other | **FAIL** | `T016` in `provenance.py:136`, `T008` in `test_research_build.py:43` → see R1 |
| Spec-Kit workflow trail: specify→clarify→plan→tasks→analyze→implement | `CLAUDE.md` | workflow-step | PASS | `spec.md`, `plan.md`, `tasks.md`, `checklists/requirements.md`, source all present (A.4) |
| Track integrity of `specs/012-…/` governance dir | `CLAUDE.md` | track-integrity | PASS | All 10 spec files in `git diff main...HEAD`; working tree clean (A.3) |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | HIGH | src/bookwright/golem/modules/provenance.py:136; tests/commands/graph/test_research_build.py:43 | Forbidden `T0xx` task-ID tags (`T016`, `T008`) in source/tests — CONTRIBUTING.md bans these as non-durable planning bookkeeping | Drop the `T016`/`T008` tokens (keep the `research D9` ref); use a plain section label in the test |
| R2 | B | MEDIUM | src/bookwright/golem/modules/provenance.py:148-155,193-200 | uuid7 identity-token boilerplate now triplicated (`Finding`, `Anchor`, plus pre-existing `AttributeAssignment`) — 3rd occurrence | Hoist the uuid7 default into a base seam so the three subclasses carry no token code |
| R3 | D | MEDIUM | src/bookwright/io/research.py:164,247,324,361,372 | Several strict-fault-model branches (structural type-guards, anchor `date`↔`begin/end` exclusivity, non-int year) have no negative test | Add focused `pytest.raises(ResearchError)` cases for the untested guards |
| R4 | B | LOW | src/bookwright/io/research.py:183 | `Source(uri_base=…, **{k: raw[k] for k in raw})` — the dict comprehension is an identity copy | Replace with `**raw` |

## 4. Remediation Detail

### R1 — Forbidden `T0xx` task-ID tags leaked into source and tests

- **Where:** `src/bookwright/golem/modules/provenance.py:136` ("(research D9, T016)") and `tests/commands/graph/test_research_build.py:43` ("# --- Foundational regression (T008) ---").
- **Why it matters:** CONTRIBUTING.md §"Traceability tags in code" (lines 58–61) explicitly lists `T0xx` task IDs from `tasks.md` as **Forbidden in source/tests** — they are planning bookkeeping with no durable artifact (task IDs are not frozen on merge the way `FR`/`SC`/`D` numbers are, so the reference goes stale). The companion `research D9` ref on line 136 is allowed and should stay; only the `T016` token is the violation.
- **Suggested change:** in `provenance.py:136` change `(research D9, T016)` → `(research D9)`. In `test_research_build.py:43` change the section banner to a behavioural label, e.g. `# --- Foundational regression: research-free build is byte-stable ---`. No code behaviour changes.

### R2 — uuid7 identity-token boilerplate triplicated

- **Where:** `src/bookwright/golem/modules/provenance.py:148-155` (`Finding`) and `193-200` (`Anchor`), identical to the pre-existing `src/bookwright/golem/modules/inference.py:45-51` (`AttributeAssignment`).
- **Why it matters:** the same five-line block (`_token: str = PrivateAttr()`, a `model_post_init` that mints `uuid_utils.uuid7()`, and a `_build_token` returning it) now appears three times. `_build_token` is already the designed identity seam in `base.py` (`SluggedEntity` overrides it for slug identity), so the duplication is avoidable rather than incidental. A future change to token generation would now require edits in three files (shotgun surgery).
- **Suggested change:** give `GolemEntity._build_token` (or a thin `MintedEntity` subclass between `GolemEntity` and these three) a default that mints a uuid7, leaving `SluggedEntity` to override with the slug. The three concrete classes then drop their `_token`/`model_post_init`/`_build_token` blocks entirely. Verify ordering guarantees in the existing `AttributeAssignment` sort test still hold.

### R3 — Strict-fault-model branches lack negative tests

- **Where:** `src/bookwright/io/research.py` raise-branches uncovered by the suite: `:164` (`sources` not a list), `:247`/`:252` (`findings` not a list / item not a mapping), `:324` (anchor missing required `constrains`), `:361` (anchor `date` mutually exclusive with `begin`/`end`), `:372` (non-integer year).
- **Why it matters:** the module's headline contract (D7/FR-016) is that it is *stricter* than the bible mapper — malformed structure aborts the build naming the offending file. The value-level rules (out-of-vocab, missing facet, translation, unknown source) are well tested, but the structural guards and the `date`↔`begin/end` exclusivity rule (D5) are asserted only by the code, not by a test. A regression that loosened one of them would pass CI (overall coverage stays > 80%).
- **Suggested change:** add `pytest.raises(ResearchError)` cases in `tests/io/test_research.py` for: a non-list `findings:`, an anchor missing `constrains`, an anchor with both `date` and `begin`, and a non-integer `begin`. Assert the `relpath`/`value` carried on the raised error.

### (LOW — not expanded) R4

`{k: raw[k] for k in raw}` at `research.py:183` is an identity dict copy; `**raw` is equivalent and clearer. No behavioural difference.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| golem/modules/provenance.py | 98.31% | 80% | PASS |
| io/research.py | 87.63% | 80% | PASS |
| golem/namespaces.py | 100.00% | 80% | PASS |
| io/errors.py | 98.08% | 80% | PASS |
| io/report.py | 100.00% | 80% | PASS |
| io/bible.py | 92.48% | 80% | PASS |
| commands/graph/build.py | (covered via integration) | 80% | PASS |
| **Total (src/bookwright)** | **95.92%** | 80% | PASS |

## 6. Inability-to-verify notes

- None. Convention files, the full diff, and all four passes ran against every in-scope file; the test runner (`uv run pytest --cov`) executed successfully.
