# Quality Audit — 007-project-templates

**Scope:** 45 changed files vs `main` (spec artifacts + template resources + tests)
**Commit range:** main..a86a995
**Date:** 2026-06-01
**Conventions discovered:** `CLAUDE.md`, `CONTRIBUTING.md`, `.specify/memory/constitution.md` (v1.2.0)
**Audit focus (user-supplied):** fidelity of the implementation to `bookwright-design.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 1 |
| **Total** | 1 |

Coverage gate: **PASS** (full suite `650 passed, 1 skipped`, total coverage **97.01%** ≥ 80%). Per SC-007 the coverage gate does not even apply to this iteration's prose deliverables; it passes anyway because no production Python was added or removed.

> This is a **re-audit**. The two findings from the prior pass (`main..959dee1`) — a forbidden `US3` user-story tag in `test_mold_structure.py` and the optional `!.env.example` negation — are both remediated in commit a86a995 and verified clear below.

**Verdict on the user's question — is the implementation faithful to `bookwright-design.md`?** Yes, with one documented and ratified divergence. The iteration delivers exactly the document inventory the design calls for (§ 6.1, § 17.2), the constitution template carries all seven § 9.2 sections, and the one structural divergence from § 6 (the lifecycle split replacing the 4-layer `resolve_template()`) is deliberate, owner-confirmed, and recorded in the CHANGELOG per FR-021 — not a drift. § 6 is structural guidance, not a § 16 axiom, so no constitutional amendment is required.

## 2. Conventions Compliance Matrix

### `.specify/memory/constitution.md` (v1.2.0)

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle … Binary stores … forbidden as canonical storage" | constitution.md:47 | layout | PASS | All authored artifacts are `.md`/`.j2`/`.tmpl`; no binary in diff |
| "Introducing an additional runtime dependency requires an amendment" | constitution.md:64 | dependency | N/A | No `pyproject.toml` dependency change in diff |
| "All production code MUST live under `src/bookwright/`; all tests under `tests/`" | constitution.md:72 | layout | PASS | Resources under `src/bookwright/resources/`; tests under `tests/resources/` |
| "No source file (production or test) may exceed 500 lines" | constitution.md:84 | module-size | PASS | All changed test files < 200 lines; templates are prose, not source modules |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … prohibited" | constitution.md:107 | directory-ban | N/A | No skill/command emission in this iteration |
| "every generated SKILL.md MUST satisfy the agentskills.io specification" | constitution.md:119 | frontmatter-constraint | N/A | No SKILL.md generated here (iter 8–9) |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | constitution.md:135 | coverage-threshold | PASS | 97.01% full-suite; SC-007 exempts prose deliverables regardless |
| "Any CLI command … MUST accept a `--json` flag … single JSON document on stdout" | constitution.md:148 | io-contract | N/A | No CLI command added/modified (FR-023) |
| "Section 16 … decisions that are closed … MUST NOT be reopened" | constitution.md:159 | scope-ban | PASS | § 6 divergence is not a § 16 axiom; plain-text/GOLEM/skills-only all upheld |
| "Preset system … MUST NOT be pulled into v0 … plumbing whose only justification is 'future preset support' MUST be rejected" | constitution.md:199 | scope-ban | PASS | No `resolve_template()`/preset/extension plumbing built (FR-024); `resolve_template` appears only in spec/plan prose explaining its deliberate absence |

### `CLAUDE.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "only `claude` … and `generic` … ship in v0" | CLAUDE.md | scope-ban | N/A | No integration code touched |
| "design docs … written in Spanish. Keep edits to them in Spanish" | CLAUDE.md | other | PASS | CHANGELOG/spec in English; template prose in Spanish per FR-017 |
| "GrafeoIndexer, vector search → v0.3 … MUST NOT pull forward" | CLAUDE.md | scope-ban | PASS | No Grafeo/vector references introduced |
| Iteration order: iter 7 depends on iter 4, milestone M2 | CLAUDE.md | workflow-step | PASS | Builds on merged iter-4 walker + iter-6 reader; conforms, doesn't modify (FR-023) |

### `CONTRIBUTING.md`

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Forbidden in source/tests: `US-x`/`+USx`, `T0xx` task IDs" | CONTRIBUTING.md:58 | other | PASS | grep of changed tests shows no `US-`/`T0xx` tags (prior `US3` finding remediated) |
| "Allowed: `FR-0xx`/`SC-0xx`/`D-x`/`bookwright-design.md § N.M`" | CONTRIBUTING.md:51 | other | PASS | Tests reference FR/SC and contract files, resolving to this iteration's spec |

### Design fidelity (`bookwright-design.md` — user-requested focus)

| Design requirement | Source | Status | Evidence |
|---|---|---|---|
| Constitution covers all § 9.2 sections (voz/registro, pacto lector, pacto histórico-ficcional, líneas rojas, invariantes, vocabularios, notas agente) | design § 9.2 | PASS (1 LOW nuance) | 7 `##` sections present in `constitution.md.j2`; `Tono` bullet folded into voice/register → see R1 |
| Document inventory adopted from preset (synopsis short+long, themes+motif, locations sensory, glossary, research, subplots, pov-structure) | design § 6.1, § 17.2 | PASS | All present under `bible/` + `outline/`; synopsis has `## Sinopsis corta (250–350)` + `## Sinopsis larga (1000–2000)` |
| Layout follows § 6 unified `templates/` + `resolve_template()` | design § 6 | SUPERSEDED (ratified) | Lifecycle split (`project/` vs `templates/`) recorded in CHANGELOG per FR-021; § 6 not a § 16 axiom; owner-confirmed |
| Preset credited, no verbatim copy, Apache-2.0 original | design § 17.2 | PASS | CHANGELOG "Attribution" block credits adaumann/MIT, states original Spanish redaction adapted to GOLEM |
| § 16 axioms not reopened (plain text, GOLEM, rdflib, skills-only, `.agents/skills/` default) | design § 16 | PASS | None touched; iteration is prose authoring only |

### Track integrity (A.3)

| Directory | On disk | In branch diff | In status | Verdict |
|---|---|---|---|---|
| `specs/007-project-templates/` | Yes | Yes | clean | OK — properly tracked |
| `src/bookwright/resources/project/` & `templates/` | Yes | Yes | clean | OK — properly tracked |
| `tests/resources/` | Yes | Yes | clean | OK — properly tracked |
| `CHANGELOG.md` | Yes | Yes | clean | OK — properly tracked |

No untracked or staged-but-uncommitted governance/feature files. `git status` is clean.

### Workflow trail integrity (A.4)

`specify → spec.md` ✓ · `clarify → ## Clarifications (Session 2026-06-01)` ✓ · `plan → plan.md` ✓ · `tasks → tasks.md` ✓ · `analyze → checklists/{requirements,quality}.md` ✓ · `implement → resources/ + tests/resources/` ✓. Trail complete; no step skipped.

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | LOW | src/bookwright/resources/project/bible/constitution.md.j2:13-22 | Design § 9.2 lists **Tono** (neutral/coloquial/lírico/técnico) as its own bullet under *Voz y registro*; the template surfaces *Voz narrativa*, *Tiempo verbal dominante*, *Registro* but no explicit tone prompt — tone is only implied by the `Registro` prompt's "textura léxica". | Optionally add a `- **Tono**: [PENDING: …]` prompt under *Voz y registro* to mirror § 9.2. FR-001 only mandates "narrative voice, register" (both present), so this is a fidelity nicety, not a requirement gap. |

## 4. Remediation Detail

### R1 — Constitution template omits the explicit "Tono" prompt from design § 9.2

- **Where:** [constitution.md.j2:13-22](src/bookwright/resources/project/bible/constitution.md.j2#L13-L22)
- **Why it matters:** Design § 9.2's *Voz y registro* block enumerates four bullets — Persona narrativa, **Tono**, Registro, Tiempos verbales. The authored template covers persona (*Voz narrativa*), tense (*Tiempo verbal dominante*), and register (*Registro*) but folds tone into register rather than eliciting it explicitly. An author following only the template's prompts is never directly asked to name the book's tone, which downstream `bookwright-constitution`/draft commands may want as a discrete field. The consequence is minor: tone is recoverable from the register and voice answers, and FR-001's normative list ("narrative voice, register, reader pact, …") is fully satisfied — it does not name tone separately.
- **Suggested change:** add one line under *Voz y registro*: `- **Tono**: [PENDING: ¿Qué tono domina (neutral, lírico, coloquial, técnico…)?]`. Low effort, no contract impact; it brings the template to a 1:1 match with § 9.2. Defer or skip if the owner considers register sufficient.

## 5. Coverage Detail

| Module | Coverage | Threshold | Status |
|---|---|---|---|
| Full suite (`src/bookwright/`) | 97.01% | 80% | PASS |
| (No production module added/changed this iteration — prose-only per SC-007) | — | — | N/A |

## 6. Inability-to-verify notes

- **Manual sign-off items (by design):** SC-005's "reads sensibly as plain Markdown" half and SC-001's editorial quality of the Spanish prose are manual inspection items, not pytest gates — the automated half (HTML-comment presence, valid YAML, no stub sentinels, frontmatter round-trip) is green via `tests/resources/`.
- **Preset non-copying (FR-021):** the audit confirms attribution exists in the CHANGELOG and the prose is Spanish/original in structure, but a byte-level diff against adaumann's MIT repo was not performed (the repo is not vendored); the tests assert structural originality, not verbatim-absence against the live upstream.
