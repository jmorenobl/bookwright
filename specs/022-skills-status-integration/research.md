# Research: Skills Status Integration

## Decision 1: Shared Editing Pattern & Boilerplate Injection

**Decision**: Modify the existing `_transform_body` function in `src/bookwright/integrations/materialize.py` to inject the status check at the top and the "Próximos pasos" boilerplate at the bottom, rather than hardcoding them into the 12 `resources/commands/*.md` files.

**Rationale**: 
1. **Token Limit**: The agentskills.io standard strongly encourages keeping bodies small. Duplicating the boilerplate 12 times increases the risk of hitting token limits and complicates maintenance.
2. **Integration Specificity**: The `claude` integration requires `!bookwright status --json` (dynamic context), whereas the `generic` integration needs explicit instructions. The materializer (`generate_skill_md`) has access to the `integration` object and its `supports_dynamic_context` flag. Passing the integration down to `_transform_body` allows us to resolve this seamlessly per-integration.
3. **Idempotency & Triggers**: The materializer already ensures idempotency and does not touch the trigger frontmatter/metadata.

**Alternatives considered**: 
- Using a shared `references/status.md` file: Ruled out because `references/` are read lazily by the agent and the initial orientation step must be the very first thing the agent processes, which requires it to be directly in the `SKILL.md` body.

## Decision 2: Phase Transitions (`bookwright focus set`)

**Decision**: Hardcode the `bookwright focus set` instruction only in the specific, pre-determined command source markdown files that logically conclude a phase (e.g., `bookwright-bible.md`, `bookwright-outline.md`). 

**Rationale**: Phase transitions only happen at very specific junctures. Hardcoding the instruction (e.g. 2-3 lines of text) inside the specific skill's body does not significantly bloat the token count and avoids complex materializer logic to conditionally inject phase transitions.

**Alternatives considered**:
- Injecting `{FOCUS_TRANSITION}` tags during materialization. Ruled out as it over-engineers what is essentially a static string unique to 2-3 files.

## Summary of Implementation Steps
- Update `src/bookwright/integrations/materialize.py`:
  - Modify `_transform_body` to accept `integration: SkillsIntegration`.
  - Inject the integration-specific status check string at the beginning of the body.
  - Append the "Próximos pasos" standardized string at the end of the body.
- Update `src/bookwright/resources/commands/*.md` files to include phase transitions where appropriate.
- Update tests to ensure the materialized output conforms to agentskills.io and is under the limits.
