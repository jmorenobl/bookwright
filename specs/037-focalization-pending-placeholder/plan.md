# Implementation Plan: `focalization` treats an unanswered `[PENDING]` voice placeholder as no declaration

**Branch**: `037-focalization-pending-placeholder` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/037-focalization-pending-placeholder/spec.md`

## Summary

A project freshly created by `bookwright init` carries a constitution whose
narrative-voice line is still the scaffold placeholder
`- **Voz narrativa**: [PENDING: ¿Quién narra y desde qué distancia (primera/tercera
persona, omnisciente/limitada)?]`. Because that placeholder *text* literally
contains "tercera persona" and "limitada", `_parse_declaration` parses it as a
real declaration (`person="third", limited=True, focal=None`); with `focal=None`
every named character counts as non-focal, so the first interiority verb in the
manuscript floods the author with head-hopping warnings against *every* character —
exactly contradicting the validator's own docstring ("No parsable declaration →
zero findings"). This is DEBT-007.

**Technical approach** (per spec clarification — parser-level suppression, the
cause class, not the symptom): add a single guard inside `_parse_declaration`. After
the already-normalized body is extracted (`match.group("body")`, post iteration-034
markdown stripping), if the body is *solely* an unanswered `[PENDING: …]` token,
return `None` — identical to the "no declaration" path. One compiled regex, one
guard line. No other rule (first-person pronoun, interiority/head-hopping, markdown
tolerance, focal resolution) is touched. Two tests bind the live scaffold template
to the parser so placeholder and parser can never silently diverge again, and the
existing `test_template_binding` assertion is flipped (the live placeholder line now
parses to `None`, by design). DEBT-007 is deleted from `DEBT.md`. Ships as `v0.4.5`.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: stdlib `re` only — no new runtime dependency. The change
lives entirely in `src/bookwright/validation/validators/focalization.py`.

**Storage**: N/A — this is a prose-level validator. It reads the constitution text
and manuscript files through `ValidationContext`; it does **not** touch the GOLEM
graph and emits **no** triples (`Violation.triples == ()`), so the frozen ontology
(Constitution X) is untouched.

**Testing**: `pytest` (`tests/validation/test_focalization.py`), four gates
(`ruff check`, `ruff format --check`, `mypy --strict`, `pytest` ≥ 80 % coverage).

**Target Platform**: CLI toolkit (cross-platform).

**Project Type**: Single project (src-layout, Constitution III).

**Performance Goals**: N/A — one extra regex match per declaration parse (one per
validate run). Negligible.

**Constraints**: `focalization.py` MUST stay ≤ 500 lines (Constitution IV; 183
lines today, the change adds ~3). The `--json` envelope is unaffected (this
validator returns `Violation` objects to the runner, which owns serialization).

**Scale/Scope**: One module + one test file. Two new tests, one assertion flip,
one DEBT entry deletion.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ PASS | No new stores. Validator reads plain text, emits no graph. DEBT.md edit is plain text. |
| II. Modern Python stack | ✅ PASS | stdlib `re` only; no dependency added. |
| III. src-layout | ✅ PASS | Change confined to `src/bookwright/validation/validators/`; tests under `tests/`. |
| IV. Modular command surface (≤ 500 lines) | ✅ PASS | `focalization.py` 183 → ~186 lines; no new module. |
| V. Plugin-based integrations | ✅ N/A | No integration touched. |
| VI. Agent Skills only | ✅ N/A | No skill / command directory touched. |
| VII. agentskills.io compliance | ✅ N/A | No SKILL.md touched. |
| VIII. Test discipline (≥ 80 %) | ✅ PASS | Two new tests + one updated assertion; the guard branch is covered by the scaffold-binding test. |
| IX. JSON-over-stdout | ✅ N/A | Validator returns `Violation`s; serialization is the runner's, unchanged. |
| X. Design-document axioms | ✅ PASS | Prose validator; no ontology change, no `§ 16` axiom reopened. |

**Scope & Release Discipline**: this is a one-delta defect fix (DEBT-007), not
speculative plumbing. The clarifications explicitly reject (a) a shared repo-wide
`[PENDING]` token utility (speculative plumbing for validators this iteration does
not touch — `references/pending-protocol.md` stays the single prose source of truth
the local recognizer mirrors) and (b) generalizing the recognizer beyond the
narrative-voice declaration. **No violations. No Complexity Tracking entries.**

## Project Structure

### Documentation (this feature)

```text
specs/037-focalization-pending-placeholder/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── parse-declaration.md   # the _parse_declaration recognition contract
├── spec.md              # /speckit-specify output
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/validation/validators/
└── focalization.py      # ONLY production file touched:
                         #   + _PENDING_ONLY compiled regex (module-level constant)
                         #   + one guard line in _parse_declaration (return None)

src/bookwright/resources/project/bible/
└── constitution.md.j2   # READ-ONLY in this iteration (the template is the bug's
                         #   source text but is NOT reworded — clarification:
                         #   parser-level suppression, the prompt stays useful)

tests/validation/
└── test_focalization.py # + scaffold-zero-findings test (FR-007)
                         # + scaffold-wakes-on-real-voice test (FR-008)
                         # ~ flip test_template_binding assertion (now parses None)

DEBT.md                  # − remove the DEBT-007 entry (FR-009)
```

**Structure Decision**: Single project, existing src-layout. The fix is a localized
guard in one validator module plus its dedicated test file — no new modules, no new
directories. The constitution template is the bug's *origin* but is deliberately
**not edited** (the clarification chose parser-level suppression precisely so the
placeholder prompt keeps naming the person/distance options for the author).

## Complexity Tracking

> No Constitution Check violations. This section is intentionally empty.
