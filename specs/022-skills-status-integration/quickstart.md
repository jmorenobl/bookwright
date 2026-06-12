# Quickstart: Validation Guide for 022

This guide validates the materializer logic that automatically injects project status instructions into skills.

## Prerequisites
- A valid local Bookwright setup using `uv run`.

## Validation Scenario 1: Materialization (Claude)
1. Run materialization for the Claude integration:
   ```bash
   uv run python -c "from bookwright.integrations.claude import ClaudeIntegration; from bookwright.core.manifest import Manifest; from pathlib import Path; ClaudeIntegration().setup(Path('.'), Manifest.default())"
   ```
2. Verify the generated skill `cat .claude/skills/bookwright-research/SKILL.md`.
3. **Expected Outcome**: The beginning of the instruction body contains `!bookwright status --json`. The end contains the "Próximos pasos" boilerplate.

## Validation Scenario 2: Materialization (Generic)
1. Run materialization for the Generic integration:
   ```bash
   uv run python -c "from bookwright.integrations.generic import GenericIntegration; from bookwright.core.manifest import Manifest; from pathlib import Path; GenericIntegration().setup(Path('.'), Manifest.default())"
   ```
2. Verify the generated skill `cat .agents/skills/bookwright-research/SKILL.md`.
3. **Expected Outcome**: The beginning of the instruction body contains an explicit instruction to run `bookwright status --json`. The end contains the "Próximos pasos" boilerplate.

## Validation Scenario 3: Tests
1. Run the test suite for the materializer to ensure skill integrity and size limits.
   ```bash
   uv run pytest tests/integrations/
   ```
2. **Expected Outcome**: All tests pass, confirming the modifications do not exceed the agentskills.io token limit and preserve bilingual triggers.
