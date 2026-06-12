# Tasks: Skills Status Integration (022-skills-status-integration)

**Input**: Design documents from `/specs/022-skills-status-integration/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Tests are required as per the project constitution and spec requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and pre-implementation verification

- [ ] T001 Verify project structure and load specifications in specs/022-skills-status-integration/
- [ ] T002 Run initial test suite to verify all checks pass on main branch using uv run pytest

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core constants and base typing structure to ensure maximum code quality and zero technical debt

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Remove the `del integration` guard (L151-153) in `generate_skill_md` and update `_transform_body` signature to accept `integration: SkillsIntegration` in src/bookwright/integrations/materialize.py. Thread the parameter through from `generate_skill_md` to `_transform_body`. No injection logic yet — structural plumbing only.
- [ ] T004 Run `uv run mypy --strict src/bookwright/integrations/materialize.py` to confirm T003's signature change is type-safe before proceeding.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Skill Orientation and Next Steps (Priority: P1) 🎯 MVP

**Goal**: Orient skills at initiation by calling status and end by outputting next steps to guide the development workflow.

**Independent Test**: Run materialization and verify the generated SKILL.md files for bookwright-research contain the injected sections.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] [US1] Create tests/integrations/test_status_injection.py with test cases asserting: (a) materialized skills contain the status orientation check at the top of the body, (b) materialized skills contain the "Próximos pasos" boilerplate at the end of the body, (c) when `bookwright status --json` fails the injected text instructs the agent to halt, (d) when status returns no focus or next actions the skill operates normally (inert behavior). Separate test file to avoid bloating test_materialize.py (Constitution IV).

### Implementation for User Story 1

- [ ] T006 [P] [US1] Create status injection pattern for Claude integration in src/bookwright/integrations/constants.py
- [ ] T007 [P] [US1] Create status injection pattern for Generic integration in src/bookwright/integrations/constants.py
- [ ] T008 [P] [US1] Create "Próximos pasos" (Next Steps) boilerplate in src/bookwright/integrations/constants.py
- [ ] T009 [US1] Implement status injection logic inside `_transform_body` in src/bookwright/integrations/materialize.py: use `integration.supports_dynamic_context` to select the Claude (`!bookwright status --json`) or Generic (explicit step) pattern from constants. Prepend the status check at the top of the body and append the "Próximos pasos" boilerplate at the end.
- [ ] ~~T010~~ [US1] ABSORBED into T003 — the `generate_skill_md` → `_transform_body` parameter threading is part of the foundational phase (T003).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automatic Focus Updates on Phase Transition (Priority: P2)

**Goal**: Specific command skills conclude their phase by updating the project focus via bookwright focus set.

**Independent Test**: Check that the materialized skills for bible and outline contain the focus transition instructions.

### Implementation for User Story 2

- [ ] T011 [P] [US2] Update bookwright-bible.md source command in src/bookwright/resources/commands/bookwright-bible.md to include focus transition instruction
- [ ] T012 [P] [US2] Update bookwright-outline.md source command in src/bookwright/resources/commands/bookwright-outline.md to include focus transition instruction

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Integration-Specific Status Injections (Priority: P1)

**Goal**: Correct status check formatting per integration (dynamic context vs explicit run) with preserved triggers and idempotency.

### Tests for User Story 3

- [ ] T013 [US3] Add test case to tests/integrations/test_status_injection.py verifying idempotency: materializing the same skill source twice produces identical output with status injection for both claude and generic integrations.
- [ ] T014 [US3] Add test case to tests/integrations/test_status_injection.py verifying bilingual triggers are preserved verbatim after body transformation with status injection.
- [ ] ~~T014b~~ ABSORBED into T005 — halt-on-failure and inert-when-empty test cases are consolidated in T005 to avoid duplication.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Quality verification, formatting, type checking, and zero technical debt validation

- [ ] T015 Run mypy strict on all modified modules: src/bookwright/integrations/materialize.py and src/bookwright/integrations/constants.py
- [ ] T016 Run ruff check and ruff format on all modified files to eliminate formatting issues
- [ ] T017 Run pytest tests/integrations/ to ensure 100% test success and verify code coverage is above 80%
- [ ] T018 Execute the three validation scenarios in specs/022-skills-status-integration/quickstart.md to verify integration functionality
- [ ] T019 Run quality-audit checks on modified code to guarantee zero technical debt and clean refactoring

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Constants before services/logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks can run in parallel
- All Foundational tasks can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch constants and patterns definition together:
Task: "Create status injection pattern for Claude integration in src/bookwright/integrations/constants.py"
Task: "Create status injection pattern for Generic integration in src/bookwright/integrations/constants.py"
Task: "Create "Próximos pasos" (Next Steps) boilerplate in src/bookwright/integrations/constants.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories
