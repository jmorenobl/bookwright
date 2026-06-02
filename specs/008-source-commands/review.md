# Quality Audit — 008-source-commands

**Scope:** iteration-8 deliverables (commit `7d071cf`): 10 command sources + 6 references + the `tests/resources/` validation suite. The 007 artifacts in `main...HEAD` are inherited from the merge and were audited under `specs/007-project-templates/review.md`; they are out of scope here.
**Commit range:** `main`..`7d071cf`
**Date:** 2026-06-02
**Conventions discovered:** `CLAUDE.md`, `CONTRIBUTING.md`, `.specify/memory/constitution.md` (v1.2.0), `specs/008-source-commands/contracts/command-source.md`, `specs/008-source-commands/contracts/validation.md`

## 1. Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 2 |
| **Total** | 3 |

Coverage gate: **PASS** (full suite `uv run pytest` → 97.01%, threshold = 80%; 709 passed, 1 skipped). The 008 validation suite (`tests/resources/`) is green: 191 passed. Iteration 8 ships **no production Python**, so there is no coverage delta to defend.

CI gates (Constitution VIII / Technical Constraints): `ruff check` ✅, `ruff format --check` ✅ (14 files), `mypy --strict src tests` ✅ (145 files, no issues).

## 2. Conventions Compliance Matrix

One row per extracted rule. Grouped by source file.

| Rule (verbatim ≤120 chars) | Source | Kind | Status | Evidence |
|---|---|---|---|---|
| "Every artifact … MUST be Markdown, TOML, or Turtle (RDF). Binary stores … are forbidden" | constitution.md:47 | layout | PASS | All 16 deliverables are `.md`; test_command_frontmatter `test_commands_tree_ships_only_markdown` guards `commands/` ships only `.md` |
| "Introducing an additional runtime dependency requires an amendment to the dependency list" | constitution.md:64 | dependency | PASS | No `pyproject.toml` dep change in diff; `tiktoken` imported optionally test-side only (helpers.py:147–151), never added as a dep |
| "All production code MUST live under `src/bookwright/`. All automated tests MUST live under `tests/`" | constitution.md:72 | layout | PASS | Sources under `src/bookwright/resources/commands/`; tests under `tests/resources/` |
| "No source file (production or test) may exceed 500 lines" | constitution.md:84 | module-size | PASS | Largest changed file is `test_command_body.py` (90 lines); helpers.py 152 lines |
| "Integrations MUST be implemented as subclasses of `SkillsIntegration` registered in `INTEGRATION_REGISTRY`" | constitution.md:94 | plugin-shape | N/A | No integration code touched this iteration (sources are integration-agnostic) |
| "Bookwright MUST emit Agent Skills … Writing to `.claude/commands/` … or any analogous … directory is prohibited" | constitution.md:107 | directory-ban | PASS | No `SKILL.md` and nothing under any `skills_dir` in diff; `src/bookwright/resources/commands/` is internal source material, not an emitted skill dir (see note below) |
| "`name` < 64 characters and exactly matching the parent directory name; `description` < 1024 characters" | constitution.md:120 | frontmatter-constraint | PASS | test_command_frontmatter asserts `name==basename`, `<64`; max `description` measured 590 chars (synopsis 475, bible 590) |
| "Long reference material MUST be offloaded to `references/`" | constitution.md:124 | frontmatter-constraint | PASS | 6 `references/*.md` carry GOLEM/Propp/Greimas/pending depth; bodies link, don't inline |
| "v0 MUST hold a minimum of 80% line coverage across `src/bookwright/`" | constitution.md:135 | coverage-threshold | PASS | Full suite 97.01% (no src code added this iteration) |
| "Any CLI command … meant to be consumed by an AI agent MUST accept a `--json` flag" | constitution.md:148 | io-contract | PASS | Bodies invoke `bookwright graph build --json` literally (constitution.md:43, continuity.md:30); test_command_body `test_graph_build_is_inline` enforces it |
| "Section 16 … decisions that are closed … MUST NOT be reopened" | constitution.md:159 | scope-ban | PASS | No axiom reopened; plain-text/Agent-Skills/no-shell honored |
| "Preset system / GrafeoIndexer / multi-integration / extensions / export … MUST NOT be pulled into v0 scope" | constitution.md:197 | scope-ban | PASS | No deferred-capability plumbing introduced |
| "FORBIDDEN keys: `scripts:` (FR-005), `handoffs:` and any other agent-specific key (FR-006)" | contracts/command-source.md:17 | frontmatter-constraint | PASS | grep finds no `scripts:`/`handoffs:`; test_frontmatter_contract asserts both absent |
| "Eight required sections — presence required" | contracts/command-source.md:23 | io-contract | PASS | test_body_required_sections_and_language asserts all 8 ES heading-keywords on all 10 |
| "source MUST NOT hard-code an agent-specific token such as `$ARGUMENTS`; … `{ARGS}` (single brace)" | contracts/command-source.md:69 | io-contract | PASS | grep: no `$ARGUMENTS`, no `{{ }}` Jinja delims; all 10 use `{ARGS}` |
| "Every `references/…` path a body cites MUST resolve to a shipped file" | contracts/command-source.md:53 | io-contract | PASS | test_every_cited_reference_resolves: 0 dangling; test_no_orphan_references: 0 orphans |
| "Every read path named is a real project path (`bible/…`, `outline/…`, `manuscript/…`)" | contracts/command-source.md:80 | io-contract | **FAIL** | `bookwright-bible.md:63` names `resources/templates/bible/` — a packaged-wheel path, not reachable in an initialized project → **R1** |
| "`draft`/`checklist` MUST define behavior for an unknown `<scene_id>`/`<artifact>` (report and ask, never fabricate)" | contracts/command-source.md:61 | io-contract | PASS | draft.md:28–29 + draft.md:62; checklist.md:27–29 + checklist.md:56 |
| "Checking commands run on an empty project MUST report 'prerequisite missing', not error opaquely" | contracts/command-source.md:62 | io-contract | PASS | analyze.md:35, continuity.md:38, clarify.md:30 each report "prerrequisito ausente" |
| "No `SKILL.md` anywhere in the diff; no helper `.py` under `resources/commands/`" | contracts/validation.md:61 | directory-ban | PASS | test_commands_tree_ships_only_markdown; diff confirms |

**Note on the `commands/` directory ban:** Principle VI bans writing to *agent-consumed* legacy command directories (`.claude/commands/`, `.agents/commands/`). `src/bookwright/resources/commands/` is internal source material that iteration-9 materializes into `SKILL.md` files — it is explicitly permitted (plan.md Constitution Check, FR-031) and guarded by a test that forbids any `SKILL.md` or `.py` leaking into it. No violation.

### Track integrity (A.3)

Working tree clean (`git status --porcelain` → 0 entries). All 9 tracked files under `specs/008-source-commands/` are committed; the 16 source deliverables + 6 test files are in `7d071cf`. No uncommitted, staged-only, or git-invisible governance artifacts. **OK.**

### Workflow trail integrity (A.4)

Spec Kit pipeline artifacts all present and in order: `spec.md` (b63d840) → clarify annotations (8f20284) → `plan.md` + `contracts/` + `data-model.md` (a4580f8) → `tasks.md` → analyze remediation (aa8d7b1 "008 analyze I1") → implementation (7d071cf). No downstream-without-upstream gap. **OK.**

## 3. Findings

| ID | Pass | Severity | Location | Summary | Recommendation |
|---|---|---|---|---|---|
| R1 | A | MEDIUM | src/bookwright/resources/commands/bookwright-bible.md:63 | "Archivos a leer" + step 4 direct the agent to read molds at `resources/templates/bible/` and stamp `character.md.tmpl`, but `init` renders only `resources.project` — that path is absent from an initialized project | Reframe the read to rely on the field+section contract in `references/golem-character.md` (and the setting/location analogues); drop the unreachable `resources/templates/` path, or state that iteration-9 bundles the molds into the skill |
| R2 | B | LOW | tests/resources/helpers.py:1 | Module docstring still reads "for the iteration-7 template suite"; the module now also enumerates the 10 iteration-8 commands | Broaden the docstring to "iteration-7 template + iteration-8 command suites" |
| R3 | B | LOW | tests/resources/test_command_body.py:46 (+budget:22, activation:34/41, frontmatter:30) | `parse_frontmatter(read_text(path)).body` / `.metadata[...]` extraction is hand-rolled in 4 test modules | Optional: a `body(path)`/`meta(path)` helper in `helpers.py`. Borderline — idiomatic one-liners; leaving as-is is defensible |

## 4. Remediation Detail

### R1 — `bookwright-bible` names a mold path unreachable in initialized projects

- **Where:** `src/bookwright/resources/commands/bookwright-bible.md:63` ("Archivos a leer": `Los moldes en resources/templates/bible/ (character, setting, location)`) and step 4 (`bookwright-bible.md:36–40`, "estampa el molde `character.md.tmpl`").
- **Why it matters:** `init` only renders `bookwright.resources.project` into the target (`src/bookwright/commands/init/scaffold.py:225`, `_RESOURCE_PACKAGE = "bookwright.resources.project"`); `resources/templates/*.tmpl` molds are never copied into a project. An agent executing the materialized `bookwright-bible` skill in the author's project resolves `resources/templates/bible/` against the project root and finds nothing — exactly the executability failure SC-004 rubric #1 is meant to prevent. The automated suite cannot catch it: `test_command_references` only validates `references/…md` citations, not arbitrary read paths. This is the one read path among all 10 bodies that is neither a real project path nor a `references/` citation.
- **Mitigating factor:** `references/golem-character.md` already carries the authoritative frontmatter contract and a summary of the prose body sections, so the agent is not blind — but the body still directs it to read and stamp a file that isn't there.
- **Suggested change:** in `bookwright-bible.md`, change the step-4 wording from "estampa el molde `character.md.tmpl`" to "construye la ficha con la estructura de `references/golem-character.md`" (and the setting/location equivalents), and replace the `resources/templates/bible/` entry under "Archivos a leer" with the corresponding `references/golem-*.md`. Alternatively, if iteration-9 is intended to bundle the molds into the skill payload, say so explicitly in the body so the path is no longer presented as a project path. Either keeps the body honest about what exists at execution time.

## 5. Coverage Detail

No production source modules were added or changed in this iteration, so there is no per-module coverage delta to report. The aggregate gate is satisfied.

| Scope | Coverage | Threshold | Status |
|---|---|---|---|
| `src/bookwright/` (full suite) | 97.01% | 80% | PASS |

## 6. Inability-to-verify notes

- **SC-003 activation precision** is, by the spec's own design, a hand-run A/B battery (US3); only the keyword backstop (`test_command_activation.py`) is automated. This audit verified the backstop passes and the four sibling-disambiguation keyword pairs are present, but did not run the A/B battery.
- **iteration-9 materialization behavior** (how `{ARGS}` and reference/mold paths are rewritten into `SKILL.md`) is out of scope for this branch; R1's severity assumes paths are emitted as-is, which is what the 008 contracts specify (only `{ARGS}` is documented as remapped).
