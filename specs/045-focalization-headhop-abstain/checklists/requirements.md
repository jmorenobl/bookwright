# Specification Quality Checklist: `focalization` head-hopping abstains as a permanent capability-gap

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-06-23
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

- The spec deliberately names internal identifiers the user fixed by name
  (`NotEvaluatedKind.pending_capability`, `_PENDING_ONLY`, `_head_hopping`,
  `not_evaluated[]`, `triples=()`) because they are load-bearing contract anchors
  carried over verbatim from iterations 037/040/043/044 — they are referenced as
  fixed contract points, not as proposed implementation. This mirrors the 044
  spec's accepted style for this codebase.
- The single ambiguity (does the limited-third abstention also suppress the
  first-person-break check?) was resolved from the user's explicit statement that
  partial evaluation is out of scope: yes, the whole validator abstains. Per the
  zero-debt doctrine the resulting loss is **not** silently accepted but recorded
  as a tracked debt — **DEBT-019** (FR-015, SC-008) — in addition to the
  Assumptions and partial-evaluation edge case, since dropping a working
  deterministic check is a genuine, if currently-invisible, coverage regression.
- Items marked incomplete require spec updates before `/speckit-clarify` or
  `/speckit-plan`.
