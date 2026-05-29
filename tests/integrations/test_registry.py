"""US1 — registry lookup, listing, and conflict detection (FR-001..FR-005)."""

from __future__ import annotations

from typing import cast

import pytest

from bookwright.integrations import (
    INTEGRATION_REGISTRY,
    ClaudeIntegration,
    DuplicateRegistrationError,
    GenericIntegration,
    SkillsIntegration,
    UnknownIntegrationError,
    _register,
    _register_builtins,
    get,
    list_keys,
)


def test_get_claude_returns_claude_class() -> None:
    assert get("claude") is ClaudeIntegration


def test_get_generic_returns_generic_class() -> None:
    assert get("generic") is GenericIntegration


def test_list_keys_alphabetic_order() -> None:
    """FR-004 — order is alphabetic, not insertion order."""

    assert list_keys() == ["claude", "generic"]


def test_list_keys_returns_fresh_list() -> None:
    """Callers may mutate the returned list without affecting the registry."""

    keys = list_keys()
    keys.append("synthetic")
    assert list_keys() == ["claude", "generic"]


@pytest.mark.parametrize("bad_key", ["", "copilot", "Claude", "CLAUDE"])
def test_get_unknown_key_raises_structured_error(bad_key: str) -> None:
    with pytest.raises(UnknownIntegrationError) as exc_info:
        get(bad_key)
    payload = exc_info.value.to_dict()
    assert payload["code"] == "unknown_integration"
    assert payload["value"] == bad_key
    assert payload["valid"] == ["claude", "generic"]


def test_get_none_raises_structured_error_with_none_value() -> None:
    """Non-string input is "not in dict" — payload faithfully carries None (FR-035)."""

    with pytest.raises(UnknownIntegrationError) as exc_info:
        get(cast(str, None))
    payload = exc_info.value.to_dict()
    assert payload["value"] is None
    assert payload["valid"] == ["claude", "generic"]


def test_reregistering_builtins_is_noop() -> None:
    """FR-002 — re-running ``_register_builtins`` MUST be safe and idempotent."""

    snapshot = dict(INTEGRATION_REGISTRY)
    _register_builtins()
    assert snapshot == INTEGRATION_REGISTRY
    # Same classes, same identity — no replacement happened.
    assert INTEGRATION_REGISTRY["claude"] is ClaudeIntegration
    assert INTEGRATION_REGISTRY["generic"] is GenericIntegration


def test_register_same_class_is_noop() -> None:
    """Re-registering the *exact same class* under its own key is a no-op."""

    _register(ClaudeIntegration)
    assert INTEGRATION_REGISTRY["claude"] is ClaudeIntegration


def test_register_different_class_under_existing_key_raises(
    registry_snapshot: dict[str, type[SkillsIntegration]],
) -> None:
    """FR-005 — colliding registration MUST raise with both classes named."""

    del registry_snapshot  # fixture restores teardown

    class ConflictingClaude(SkillsIntegration):
        key = "claude"
        default_skills_dir = ".elsewhere/skills"

    with pytest.raises(DuplicateRegistrationError) as exc_info:
        _register(ConflictingClaude)
    payload = exc_info.value.to_dict()
    assert payload["code"] == "duplicate_registration"
    assert payload["value"] == "claude"
    # `existing` names the original Claude class; `new` names the conflicting one.
    existing = payload["existing"]
    new_name = payload["new"]
    assert isinstance(existing, str) and existing.endswith("ClaudeIntegration")
    assert isinstance(new_name, str) and new_name.endswith("ConflictingClaude")
