"""registry lookup, listing, and conflict detection (FR-001..FR-005)."""

from __future__ import annotations

import importlib
from typing import cast

import pytest

import bookwright.integrations.claude as claude_module
from bookwright.integrations import (
    INTEGRATION_REGISTRY,
    ClaudeIntegration,
    DuplicateRegistrationError,
    GenericIntegration,
    InvalidIntegrationError,
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
    payload = exc_info.value.to_json()
    assert payload["code"] == "unknown_integration"
    assert payload["details"]["value"] == bad_key
    assert payload["details"]["valid"] == ["claude", "generic"]


def test_get_none_raises_structured_error_with_none_value() -> None:
    """Non-string input is "not in dict" — payload faithfully carries None (FR-035)."""

    with pytest.raises(UnknownIntegrationError) as exc_info:
        get(cast(str, None))
    details = exc_info.value.to_json()["details"]
    assert details["value"] is None
    assert details["valid"] == ["claude", "generic"]


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
    payload = exc_info.value.to_json()
    assert payload["code"] == "duplicate_registration"
    assert payload["details"]["value"] == "claude"
    # `existing` names the original Claude class; `new` names the conflicting one.
    existing = payload["details"]["existing"]
    new_name = payload["details"]["new"]
    assert isinstance(existing, str) and existing.endswith("ClaudeIntegration")
    assert isinstance(new_name, str) and new_name.endswith("ConflictingClaude")


def test_register_reloaded_submodule_is_idempotent(
    registry_snapshot: dict[str, type[SkillsIntegration]],
) -> None:
    """R12 — `_register` MUST be idempotent across `importlib.reload`
    even though the reloaded module produces a fresh class object with
    different identity. Pre-R12 the `existing is cls` check raised
    DuplicateRegistrationError spuriously, contradicting FR-002.
    """

    del registry_snapshot

    reloaded = importlib.reload(claude_module)

    # Identity differs from the previously-registered class…
    assert reloaded.ClaudeIntegration is not INTEGRATION_REGISTRY["claude"]
    # …but FQCN matches, so _register treats it as a re-registration and
    # rebinds the registry to the reloaded class with no exception.
    _register(reloaded.ClaudeIntegration)
    assert INTEGRATION_REGISTRY["claude"] is reloaded.ClaudeIntegration


def test_register_base_class_raises_invalid_integration() -> None:
    """R13 — registering ``SkillsIntegration`` itself (or any subclass that
    forgot to override ``key``) raises ``InvalidIntegrationError`` instead of
    silently binding to the empty-string sentinel.
    """

    with pytest.raises(InvalidIntegrationError) as exc_info:
        _register(SkillsIntegration)
    payload = exc_info.value.to_json()
    assert payload["code"] == "invalid_integration"
    assert payload["details"]["rule"] == "empty_key"
    assert "SkillsIntegration" in str(payload["details"]["value"])
    # Nothing was inserted — the empty key sentinel never lands in the
    # registry.
    assert "" not in INTEGRATION_REGISTRY


def test_register_forgetful_subclass_raises_invalid_integration(
    registry_snapshot: dict[str, type[SkillsIntegration]],
) -> None:
    """R13 — a concrete subclass that forgets ``key`` is also rejected."""

    del registry_snapshot

    class ForgetfulIntegration(SkillsIntegration):
        # `key` deliberately not overridden — inherits the empty sentinel.
        default_skills_dir = ".forgetful/skills"

    with pytest.raises(InvalidIntegrationError) as exc_info:
        _register(ForgetfulIntegration)
    assert exc_info.value.to_json()["details"]["rule"] == "empty_key"


def test_register_subclass_without_default_skills_dir_raises_invalid_integration(
    registry_snapshot: dict[str, type[SkillsIntegration]],
) -> None:
    """R25 — a subclass that overrides ``key`` but inherits the empty
    ``default_skills_dir`` sentinel is rejected at registration time,
    instead of surfacing as a misleading ``resolves_to_project_root``
    error in ``setup()`` because ``Path("") == Path(".")`` collapses
    to the project root.
    """

    del registry_snapshot

    class HalfForgetfulIntegration(SkillsIntegration):
        key = "half-forgetful"
        # `default_skills_dir` deliberately not overridden — inherits the
        # empty sentinel from `SkillsIntegration`.

    with pytest.raises(InvalidIntegrationError) as exc_info:
        _register(HalfForgetfulIntegration)
    payload = exc_info.value.to_json()
    assert payload["code"] == "invalid_integration"
    assert payload["details"]["rule"] == "empty_default_skills_dir"
    assert "HalfForgetfulIntegration" in str(payload["details"]["value"])
    # Nothing was inserted under the would-be key.
    assert "half-forgetful" not in INTEGRATION_REGISTRY
