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
| R2 | B | HIGH | character.py:20,26 · feature.py:1 · __init__.py:3 · namespaces.py:54,96,105,124 · test_character_attributes.py:1,3,34,45,55,73,146,150 · test_namespaces.py:17,42 · test_triples.py:46 · test_turtle_roundtrip.py:3 · test_uri.py:3,83 | Ephemeral planning tags — user-story (`+US5`, `US5-1..6`, `US1`, `US2-4`, `pre-US5`) and task IDs (`T021` at namespaces.py:105,124) — in docstrings/comments. These name work units, not durable artifacts. | Strip the `USx`/`+USx` and `T0xx` tokens; keep the descriptive remainder of each docstring (most already read well without the tag). The 4 other `T0xx` sites (base.py:11, two core fixtures, commands/conftest.py:60) live in merged code — out of this branch's reach. |
| R3 | B | MEDIUM | namespaces.py:5,7,98,103,124,155 · feature.py:7 · serialize.py:1,18 · slug.py:1 · (and ~300 more across merged core/, integrations/, commands/) | **DECIDED.** Durable trace tags (`FR-0xx`, `SC-00x`, `D-x`, `bookwright-design.md § N.M`) used as inline shorthand. Unlike R2 these point to versioned in-repo artifacts (spec.md / research.md / design doc) that carry the *why*. Keep them — but they are ambiguous (`FR-021` exists in 5 specs) and can drift on `/speckit-specify` re-run. | Do **not** strip. Sanction the convention in `CONTRIBUTING.md` (see §7 / Remediation R3): allowed classes = `FR`/`SC` (owning iteration's spec), `D` (research), `§ N.M` (global design); refs resolve relative to the file's iteration; FR/SC/D numbers freeze once an iteration merges. `US`/`T0xx` forbidden in code (→ R2). Zero churn on the ~300 existing refs. |

## 4. Remediation Detail

### R1 — Test identifier carries user-story jargon (`us1`)

- **Where:** `tests/golem/test_uri.py:60`
- **Why it matters:** This is the single place where planning jargon escaped a docstring and became a **public identifier**. `us1` is the exact failure mode the audit targets: it names a backlog item, not a behavior. A reader running `pytest -k` or scanning a failure report learns nothing from "us1". The body already tests "canonical URI for the design's worked examples" — the name should say that.
- **Suggested change:** rename the function to `test_canonical_uri_for_worked_examples` (or `test_worked_example_uris`). Also drop the `US1` reference on the module docstring at `test_uri.py:3` ("US1 worked examples" → "worked examples"). No other call site references the name.

### R2 — Ephemeral planning tags (user-story + task IDs) in golem docstrings/comments

- **Where:** 4 source files + 5 test files; full site list in the table above. Representative cases:
  - `src/bookwright/golem/modules/feature.py:1` — `"""Feature module (+US5): character-scoped attribute carriers.`
  - `src/bookwright/golem/modules/character.py:26` — `... emits only its rdf:type assertion (US5-6).`
  - `tests/golem/test_character_attributes.py:1` — `"""US5 acceptance matrix: a Character carries born/died/...`
  - `tests/golem/test_character_attributes.py:34` — `"""US5-1, FR-017: free text → G17 feature linked by golem:GP0_has_feature ...`
  - `src/bookwright/golem/namespaces.py:105,124` — `recorded ... T021` (task ID)
- **Why it matters:** `+US5` ("added in User Story 5"), `US5-3` and `T021` name **work units**, not durable artifacts — there is no `US5.md` or `T021.md` a future reader opens. Once the story/task is delivered they are commit-time bookkeeping frozen into the file. (Contrast R3, which points to versioned spec/research artifacts.) The surrounding prose is already descriptive (e.g. "free text → G17 feature linked by `golem:GP0_has_feature`"), so the tags are pure prefix noise that can be deleted without losing meaning. **Keep the `FR-0xx` references** that co-occur on the same lines — those are sanctioned under R3.
- **Suggested change:** delete the `USx` / `+USx` / `pre-USx` / `T0xx` tokens (keep neighbouring `FR`/`SC`/`D` refs). For test docstrings, keep the behavioral description: `"""US5-1, FR-017: free text → ..."""` becomes `"""FR-017: free text feature is linked by golem:GP0_has_feature with rdfs:label."""`. Mechanical, file-local edit — a good fit for `/simplify`. The 4 `T0xx` sites outside golem (`integrations/base.py:11`, `tests/core/fixtures/valid_{full,minimal}.toml:1`, `tests/commands/conftest.py:60`) are merged code, not this branch's scope.

### R3 — DECIDED: durable trace tags are sanctioned, not stripped

- **Where:** `src/bookwright/golem/namespaces.py:5,7,124,155`, `serialize.py:1,18`, `slug.py:1`, `feature.py:7`, and ~300 occurrences across merged `core/`, `integrations/`, `commands/`.
- **The decision (recorded 2026-05-31):** `FR-0xx`, `SC-00x`, `D-x` and `bookwright-design.md § N.M` are **kept** as deliberate, project-sanctioned traceability — they are *not* the same as `us5`. Each points to a **versioned, in-repo artifact** that carries the *why*: `FR`/`SC` → the owning iteration's `spec.md`, `D` → `research.md`, `§ N.M` → the global design doc (already declared "load-bearing" by `CLAUDE.md`). In a Spec-Kit project these IDs are the lingua franca that `/speckit-analyze` cross-references. The 261 `FR` + 45 `SC` refs are systematic, not accidental.
- **Two real risks that the policy must close:** (1) **Ambiguity** — every spec restarts at `FR-001`, so a bare `FR-021` matches 5 specs; only the file's location disambiguates. (2) **Drift** — re-running `/speckit-specify` can renumber FRs and silently stale every inline ref.
- **Resolution — sanction + close the gaps in `CONTRIBUTING.md`** (draft below, awaiting approval; nothing edited yet):
  1. **Allowed in code:** `FR`/`SC` (owning iteration's `spec.md`), `D-x` (`research.md`), `bookwright-design.md § N.M` (global). `US-x` and `T0xx` are **forbidden** in code (enforced via R2).
  2. **Relative resolution:** an inline ref resolves against the spec/research of the iteration the file belongs to (the `src/` tree maps to iterations). Documenting this once removes the ambiguity with zero edits to the ~300 refs.
  3. **Freeze on merge:** once an iteration merges, its `FR`/`SC`/`D` numbers are frozen — never renumbered. This turns inline refs from best-effort into trustworthy and kills the drift.
  - Style preference (not a rule): pair the ref with a *why* phrase (`# dedup identical features (FR-021)`) rather than a bare pointer. Most sites already do.
- **Net:** zero churn on the existing refs; the only action is ~6 lines added to `CONTRIBUTING.md`.

## 5. Coverage Detail

Not measured this run (the invocation scoped the audit to naming/jargon, not coverage). Run `uv run pytest --cov=src/bookwright/golem --cov-report=term-missing` for the gate.

## 6. Inability-to-verify notes

- Coverage gate not evaluated (out of this run's lens).
- R3 is now **decided** (keep + sanction, see §4 R3); the only remaining work is the `CONTRIBUTING.md` block, which is a docs add, not a code change. Its full extent reaches already-merged code on `main`; the policy applies repo-wide but requires no edits to the ~300 existing refs.
- The constitution does not codify a "no planning jargon in names" rule; R1/R2 severity derives from the explicit audit instruction, not a discovered MUST. If you want this enforced going forward, it belongs in CONTRIBUTING.md or the constitution.
