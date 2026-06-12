# Feature Specification: Skills Status Integration

**Feature Branch**: `022-skills-status-integration`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Necesidad: el hilo conductor solo funciona si las skills lo usan. Cada skill debería orientarse al empezar (foco actual + qué falta) consultando `bookwright status`, y terminar proponiendo el siguiente paso concreto, en vez de dejar al autor sin saber qué hacer después. Hoy las skills no consultan estado ni recomiendan continuación. Comportamiento esperado: - Cada command source de la suite (los 10 de v0.1 + bookwright-research y bookwright-verify de v0.2) gana: (al inicio) un paso para consultar `bookwright status --json` y orientarse con el foco y los elementos abiertos; (al final) una sección 'Próximos pasos' que muestra las next_actions relevantes con sus prompts listos para pegar. - Donde tenga sentido tras una transición de fase (p. ej. terminar la biblia), la skill actualiza el foco con `bookwright focus set` (iteración 019). Es opcional y solo donde aporte. - La integración claude, con contexto dinámico, puede inyectar el estado vía !`bookwright status --json`; la generic lo instruye como paso explícito a ejecutar (respetando las convenciones de la iteración 9). - La re-materialización es idempotente y aplica a ambas integraciones. Los triggers bilingües se preservan. - El sistema es inerte si status no aporta nada: las skills siguen funcionando igual que hoy en un proyecto sin foco ni investigación. Fuera de scope: - El fixture E2E, los tests de flujo, la documentación y el release (iteración 023). - Cambiar la lógica de `status` o `focus`."

## Clarifications

### Session 2026-06-12

- Q: How should the skill handle `bookwright status --json` failures? → A: Halt execution and ask the user to fix the error (guarantees the workflow is not broken).
- Q: How should "phase transitions" be handled for `bookwright focus set`? → A: Hardcode the `bookwright focus set` instruction only in specific, pre-determined skills (safer, deterministic).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Skill Orientation and Next Steps (Priority: P1)

As an author, when I invoke any of the bookwright skills, the skill should first orient itself to my current project focus and open tasks, and at the end of its execution, provide me with actionable next steps so I know exactly how to continue the development workflow.

**Why this priority**: Without orientation, skills operate in a vacuum. Without next steps, the user is left hanging, breaking the flow of the bookwright workflow. This represents the core "hilo conductor" (golden thread).

**Independent Test**: Can be tested independently by running any modified skill and observing its initial status check and its final output containing next actions.

**Acceptance Scenarios**:

1. **Given** a bookwright project with an active focus, **When** a user invokes a skill (e.g., `bookwright-research`), **Then** the skill should consult `bookwright status --json` at the start to adapt its context.
2. **Given** the skill has finished its primary task, **When** the skill completes, **Then** it must output a "Próximos pasos" (Next steps) section containing relevant `next_actions` with copy-pasteable prompts.
3. **Given** a project without any active focus or research, **When** a skill is invoked, **Then** the skill continues operating normally without disruption (system remains inert to status).

---

### User Story 2 - Automatic Focus Updates on Phase Transition (Priority: P2)

As an author, when a skill completes a major phase of the project (e.g., finishing the bible), the skill should automatically update the project focus to the next logical phase.

**Why this priority**: Automating focus transitions reduces friction for the user and enforces the project workflow without requiring manual focus commands.

**Independent Test**: Can be tested independently by running a skill that triggers a phase transition and verifying the focus was updated.

**Acceptance Scenarios**:

1. **Given** a specific, pre-determined skill that concludes a phase (e.g., finishing the project bible), **When** the skill concludes, **Then** its hardcoded instructions should run `bookwright focus set` to update the project focus appropriately.

---

### User Story 3 - Integration-Specific Status Injections (Priority: P1)

As an integration user (Claude or Generic), I should receive the project status context with minimal token overhead (respecting agentskills.io token budget limits) based on my integration's capabilities.

**Why this priority**: Different agents/integrations have different capabilities. Optimizing context delivery per integration is key for performance, keeping within token limits, and ensuring correct execution.

**Independent Test**: Can be tested by materializing the skills for both integrations and checking the generated instructions.

**Acceptance Scenarios**:

1. **Given** the `claude` integration, **When** skills are materialized, **Then** the dynamic context should be injected via `!bookwright status --json`.
2. **Given** the `generic` integration, **When** skills are materialized, **Then** the status check must be instructed as an explicit step to execute, respecting iteration 9 conventions.
3. **Given** existing bilingual triggers in the skills, **When** re-materialization occurs, **Then** the triggers are preserved and the process is idempotent.

### Edge Cases

- What happens if the `bookwright status --json` command fails or returns invalid JSON? The skill MUST halt execution and inform the user to fix the error to guarantee the workflow is strictly enforced without operating blindly.
- What happens if the focus update `bookwright focus set` fails during phase transition? The skill should warn the user but not crash, as focus updates are optional.
- How does the system handle materializing a skill that has custom manual edits? The materialization process should ideally overwrite it according to templates, but custom non-templated content might be lost. This is a known constraint.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All 12 command sources (10 from v0.1 + bookwright-research and bookwright-verify) MUST include an initial step to consult the project status.
- **FR-002**: All 12 command sources MUST include a final step to propose next actions ("Próximos pasos") using prompts ready to copy and paste.
- **FR-003**: Specific, pre-determined skills that officially conclude a phase MUST include a hardcoded instruction to update the focus using `bookwright focus set` (this is not evaluated dynamically by all skills).
- **FR-004**: For the `claude` integration, the status check MUST be implemented via the dynamic context feature (`!bookwright status --json`).
- **FR-005**: For the `generic` integration, the status check MUST be included as an explicit command step.
- **FR-006**: The materialization process MUST be idempotent, allowing repeated generation without duplicating instructions.
- **FR-007**: Bilingual triggers in the skills MUST be preserved during materialization.
- **FR-008**: The execution of skills MUST remain unaffected (inert) if `bookwright status` returns no actionable context.

### Key Entities

- **Skill (Command Source)**: The agent instructions for a specific task.
- **Project Status**: The current state of the project, including focus and next actions.
- **Integration**: The target platform (e.g., `claude`, `generic`) dictating how context is injected.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the 12 specified skills successfully fetch project status upon initiation.
- **SC-002**: 100% of the 12 specified skills output a "Próximos pasos" section upon completion.
- **SC-003**: Re-running the materialization script produces no changes on an already updated skill set (idempotency verified).
- **SC-004**: No regressions in existing skill functionality or triggers.

## Assumptions

- The `bookwright status` and `bookwright focus` command logic remains unchanged (out of scope).
- Automated tests, documentation, and release processes for this specific integration are deferred to iteration 023.
- The `bookwright status --json` output structure is stable and parseable by the skills.
