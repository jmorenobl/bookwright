from pathlib import Path
from typing import Any

from bookwright.integrations.base import SkillsIntegration
from bookwright.integrations.constants import (
    NEXT_STEPS_BOILERPLATE,
    STATUS_INJECTION_CLAUDE,
    STATUS_INJECTION_GENERIC,
)
from bookwright.integrations.materialize import _transform_body


class MockIntegration(SkillsIntegration):
    """Minimal ``SkillsIntegration`` stub for body-injection tests.

    Only ``supports_dynamic_context`` (a ``ClassVar[bool]`` on the base) drives
    ``_transform_body``, so the two subclasses below set it as a class attribute
    rather than overriding it with a property. ``setup`` is a no-op that matches
    the base signature so ``mypy --strict`` accepts the override.
    """

    def setup(
        self,
        project_root: Path,
        manifest: Any,
        parsed_options: Any = None,
        *,
        ledger: Any = None,
    ) -> None:
        pass


class DynamicMockIntegration(MockIntegration):
    supports_dynamic_context = True


class StaticMockIntegration(MockIntegration):
    supports_dynamic_context = False


def test_status_injection_claude_contains_required_sections() -> None:
    integration = DynamicMockIntegration()
    body = "## Existing Content\n\nSome body text."
    result = _transform_body("test-skill", body, integration)

    assert result.startswith(STATUS_INJECTION_CLAUDE)
    assert result.endswith(NEXT_STEPS_BOILERPLATE)
    assert "!`bookwright status --json`" in result
    assert "halt" in result.lower() or "detente" in result.lower()
    assert "## Existing Content" in result


def test_status_injection_generic_contains_required_sections() -> None:
    integration = StaticMockIntegration()
    body = "## Existing Content\n\nSome body text."
    result = _transform_body("test-skill", body, integration)

    assert result.startswith(STATUS_INJECTION_GENERIC)
    assert result.endswith(NEXT_STEPS_BOILERPLATE)
    assert "```bash\nbookwright status --json\n```" in result
    assert "halt" in result.lower() or "detente" in result.lower()
    assert "## Existing Content" in result


def test_idempotency() -> None:
    integration = DynamicMockIntegration()
    body = "## Existing Content"
    # First materialization
    result1 = _transform_body("test-skill", body, integration)
    # Second materialization (simulating reading the already materialized body)
    result2 = _transform_body("test-skill", result1, integration)

    # It should not duplicate the injection
    assert result2 == result1
    assert result2.count(STATUS_INJECTION_CLAUDE) == 1
    assert result2.count(NEXT_STEPS_BOILERPLATE) == 1


def test_preserves_bilingual_triggers() -> None:
    integration = DynamicMockIntegration()
    body = "Triggers: english and español\n\n## Content"
    result = _transform_body("test-skill", body, integration)
    assert "Triggers: english and español" in result
