# Quality Audit — 005-golem-domain-model

**Scope:** 4 changed source files + 5 changed test files vs `main` (focused lens: planning jargon in identifiers/names)
**Commit range:** main..dbc901f
**Date:** 2026-05-31
**Conventions discovered:** `CLAUDE.md`, `.specify/memory/constitution.md`, `CONTRIBUTING.md`, `pyproject.toml`
**Audit lens (from invocation):** "que los nombres de tests, funciones, clases, métodos y cualquier cosa no contengan jerga de planificación (p.ej. `us5`) que no dice nada una vez terminada la planificación." This user instruction is treated as the governing rule for this run; severity is raised accordingly even though the constitution does not (yet) codify it as a MUST.

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 0 |
| **Total** | 3 |

Coverage gate: UNKNOWN (not measured — this run is a targeted naming sweep, not a coverage pass).

**Headline:** Exactly **one** identifier carries planning jargon — `test_us1_worked_examples` (R1). Everything else (`Character`, `CharacterFeature`, `Dimension`, `bind_prefixes`, `test_born_year_modeled_through_dimension_chain`, …) is descriptive and clean. The bulk of the jargon lives in **docstrings and comments** as user-story tags (`+US5`, `US5-1..6`, `US1`, `US2-4`) and requirement-trace tags (`FR-0xx`, `SC-00x`, `T021`, `D5/D14`).

## 2. Conventions Compliance Matrix

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Names of tests/functions/classes/methods must not contain planning jargon like `us5`" | invocation arg | naming (audit lens) | FAIL | `test_us1_worked_examples` at `tests/golem/test_uri.py:60` (R1) |
| "Source code, identifiers … in English" | `CLAUDE.md:143` | layout | PASS | All identifiers English; no Spanish leaked into code |
| "Each CLI subcommand in its own file ≤500 lines" | constitution | module-size | N/A | No `commands/` files on this branch |
| Test discipline ≥80% coverage | constitution (VIII) | coverage-threshold | N/A | Not measured this run (naming-focused) |
| Plain-text source of truth, no binary under src/ | constitution (I) | layout | PASS | No binaries in diff |

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | B | HIGH | tests/golem/test_uri.py:60 | Test function name `test_us1_worked_examples` embeds "us1" (User Story 1) planning jargon | Rename to describe the behavior, e.g. `test_canonical_uri_for_worked_examples` |
| R2 | B | HIGH | character.py:20,26 · feature.py:1 · __init__.py:3 · namespaces.py:54,96,124 · test_character_attributes.py:1,3,34,45,55,73,146,150 · test_namespaces.py:17,42 · test_triples.py:46 · test_turtle_roundtrip.py:3 · test_uri.py:3,83 | User-story planning tags (`+US5`, `US5-1..6`, `US1`, `US2-4`, `pre-US5`) sprinkled through docstrings/comments | Strip the `USx`/`+USx` tags; keep the descriptive remainder of each docstring (most already read well without the tag) |
| R3 | B | MEDIUM | namespaces.py:5,7,98,103,105,124,155 · feature.py:7 · (and pervasively in already-merged core/, integrations/, commands/) | Requirement/decision/task trace tags (`FR-0xx`, `SC-00x`, `T021`, `D5`, `D14`) used as inline shorthand in comments | Decide project-wide policy: keep `FR-xxx` as deliberate traceability, or strip. If kept, document it in CONTRIBUTING.md so it is intentional, not jargon-leak. Out of this branch's reach where it touches merged code. |

## 4. Remediation Detail

### R1 — Test identifier carries user-story jargon (`us1`)

- **Where:** `tests/golem/test_uri.py:60`
- **Why it matters:** This is the single place where planning jargon escaped a docstring and became a **public identifier**. `us1` is the exact failure mode the audit targets: it names a backlog item, not a behavior. A reader running `pytest -k` or scanning a failure report learns nothing from "us1". The body already tests "canonical URI for the design's worked examples" — the name should say that.
- **Suggested change:** rename the function to `test_canonical_uri_for_worked_examples` (or `test_worked_example_uris`). Also drop the `US1` reference on the module docstring at `test_uri.py:3` ("US1 worked examples" → "worked examples"). No other call site references the name.

### R2 — User-story tags throughout golem docstrings/comments

- **Where:** 4 source files + 5 test files; full site list in the table above. Representative cases:
  - `src/bookwright/golem/modules/feature.py:1` — `"""Feature module (+US5): character-scoped attribute carriers.`
  - `src/bookwright/golem/modules/character.py:26` — `... emits only its rdf:type assertion (US5-6).`
  - `tests/golem/test_character_attributes.py:1` — `"""US5 acceptance matrix: a Character carries born/died/...`
  - `tests/golem/test_character_attributes.py:34` — `"""US5-1, FR-017: free text → G17 feature linked by golem:GP0_has_feature ...`
- **Why it matters:** `+US5` ("added in User Story 5") and `US5-3` say nothing once the story is delivered — they're commit-time bookkeeping frozen into the file. The good news: the surrounding prose is already descriptive (e.g. "free text → G17 feature linked by `golem:GP0_has_feature`"), so the tags are pure prefix noise that can be deleted without losing meaning.
- **Suggested change:** delete the `USx` / `+USx` / `pre-USx` tokens. For test docstrings, keep the behavioral description: `"""US5-1, FR-017: free text → ..."""` becomes `"""Free text feature is linked by golem:GP0_has_feature with rdfs:label."""` (the test name `test_free_text_feature_linked_by_has_feature_with_label` already carries that). This is a mechanical, file-local edit — a good fit for `/simplify`.

### R3 — Requirement/task/decision trace tags in comments

- **Where:** `src/bookwright/golem/namespaces.py:105` (`recorded in data-model.md T021`), `:124` (`recorded T021/D14`), `:5,7` (`research D5`, `SC-003`), `feature.py:7` (`SC-001`), and pervasively across already-merged modules (`core/manifest.py`, `integrations/options.py`, `commands/init/*`).
- **Why it matters:** `FR-0xx`/`SC-00x`/`T021`/`Dxx` are the same class of planning jargon as `us5`, but they arguably serve as deliberate requirement traceability. The problem is it's **undocumented**, so it reads as leak rather than policy — and it's so widespread (including merged code) that a blanket rename here would be inconsistent and out of this branch's scope.
- **Suggested change:** make a deliberate call, don't fix piecemeal. Either (a) adopt `FR-xxx` as sanctioned traceability and write one line in `CONTRIBUTING.md` legitimizing it (then it's policy, not jargon), or (b) plan a separate sweep to strip it everywhere. This is a planning decision, not an implementation fix — see Next Actions.

## 5. Coverage Detail

Not measured this run (the invocation scoped the audit to naming/jargon, not coverage). Run `uv run pytest --cov=src/bookwright/golem --cov-report=term-missing` for the gate.

## 6. Inability-to-verify notes

- Coverage gate not evaluated (out of this run's lens).
- R3's full extent reaches already-merged code on `main`; only the golem-branch occurrences are in diff scope. The cross-codebase count (`FR-xxx` in `core/`, `integrations/`, `commands/`) is reported as context, not as branch findings.
- The constitution does not codify a "no planning jargon in names" rule; R1/R2 severity derives from the explicit audit instruction, not a discovered MUST. If you want this enforced going forward, it belongs in CONTRIBUTING.md or the constitution.
