import pytest

from bookwright.integrations import ClaudeIntegration, GenericIntegration
from bookwright.integrations.constants import (
    NEXT_STEPS_BOILERPLATE,
    STATUS_INJECTION_CLAUDE,
    STATUS_INJECTION_GENERIC,
)
from bookwright.integrations.errors import SkillMaterializationError
from bookwright.integrations.materialize import _transform_body

# ``_transform_body`` branches only on ``supports_dynamic_context``; the two real
# integrations already differ on exactly that flag (claude=True, generic=False),
# so they stand in for the dynamic/static cases without a bespoke stub.


def test_status_injection_claude_contains_required_sections() -> None:
    integration = ClaudeIntegration()
    body = "## Existing Content\n\nSome body text."
    result = _transform_body("test-skill", body, integration)

    assert result.startswith(STATUS_INJECTION_CLAUDE)
    assert result.endswith(NEXT_STEPS_BOILERPLATE)
    assert "!`bookwright status --json`" in result
    assert "halt" in result.lower() or "detente" in result.lower()
    assert "## Existing Content" in result


def test_status_injection_generic_contains_required_sections() -> None:
    integration = GenericIntegration()
    body = "## Existing Content\n\nSome body text."
    result = _transform_body("test-skill", body, integration)

    assert result.startswith(STATUS_INJECTION_GENERIC)
    assert result.endswith(NEXT_STEPS_BOILERPLATE)
    assert "```bash\nbookwright status --json\n```" in result
    assert "halt" in result.lower() or "detente" in result.lower()
    assert "## Existing Content" in result


def test_idempotency() -> None:
    integration = ClaudeIntegration()
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
    integration = ClaudeIntegration()
    body = "Triggers: english and español\n\n## Content"
    result = _transform_body("test-skill", body, integration)
    assert "Triggers: english and español" in result


def test_residual_script_token_rejected() -> None:
    """A ``{SCRIPT}`` token left in the body fails loud (SC-003, materialize.py:89).

    Only ``{ARGS}`` is substituted, so any other ``_RESIDUAL_TOKENS`` member that
    survives the transform must raise rather than ship a broken skill body.
    """

    integration = ClaudeIntegration()
    body = "## Content\n\nRun {SCRIPT} to continue."
    with pytest.raises(SkillMaterializationError) as excinfo:
        _transform_body("test-skill", body, integration)

    assert excinfo.value.rule == "residual_token"
    assert "{SCRIPT}" in excinfo.value.detail
