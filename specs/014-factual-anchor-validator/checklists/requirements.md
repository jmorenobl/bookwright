# Specification Quality Checklist: `factual_anchor` Validator

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-06-04
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`.
- The spec names graph predicates (`bw:promotes`, `crm:P4_has_time-span`) and the
  reliability vocabulary only inside Assumptions/Dependencies to anchor testability;
  these are domain facts fixed by iteration 012, not new implementation choices, so
  the "no implementation details" item is treated as satisfied.
- A few requirements (FR-004/005/011) reference *reuse* of named iteration-10/12
  seams. This is intentional and required by the user's brief ("reutilizando la
  lógica del validator temporal", "se autodescubre por el registry existente"); it
  expresses a behavioral constraint (one source of truth, no parallel mechanism)
  rather than a fresh design.
- Candidate probes for `/speckit-clarify` (not blockers): (a) exact anachronism
  semantics when an anchor constrains the timeline as a whole vs. a single event;
  (b) whether a time-spanned anchor on a temporal target lacking any interval should
  be a silent skip (current default) or a structural warning.
```
