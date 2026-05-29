"""Structured-error ``to_dict()`` shape + JSON round-trip (FR-036, SC-008)."""

from __future__ import annotations

import json

import pytest

from bookwright.integrations import (
    DuplicateRegistrationError,
    InvalidIntegrationError,
    InvalidOptionDeclarationError,
    MalformedOptionError,
    UnknownIntegrationError,
    UnknownOptionError,
)
from bookwright.integrations.errors import _IntegrationError


def test_unknown_integration_error_payload() -> None:
    err = UnknownIntegrationError(value="copilot", valid=["claude", "generic"])
    payload = err.to_dict()
    assert payload == {
        "code": "unknown_integration",
        "value": "copilot",
        "valid": ["claude", "generic"],
        "message": err.message,
    }
    assert err.code == UnknownIntegrationError.code
    assert err.message
    json.dumps(payload)  # no custom encoder needed


def test_unknown_integration_error_with_none_value() -> None:
    err = UnknownIntegrationError(value=None, valid=["claude", "generic"])
    payload = err.to_dict()
    assert payload["value"] is None
    assert json.loads(json.dumps(payload))["value"] is None


def test_unknown_option_error_payload() -> None:
    err = UnknownOptionError(integration="generic", value="--bogus", valid=["--skills-dir"])
    payload = err.to_dict()
    assert payload == {
        "code": "unknown_option",
        "integration": "generic",
        "value": "--bogus",
        "valid": ["--skills-dir"],
        "message": err.message,
    }
    json.dumps(payload)


def test_malformed_option_error_payload() -> None:
    err = MalformedOptionError(rule="missing_value", value="--skills-dir")
    payload = err.to_dict()
    assert payload == {
        "code": "malformed_option",
        "rule": "missing_value",
        "value": "--skills-dir",
        "message": err.message,
    }
    json.dumps(payload)


def test_duplicate_registration_error_payload() -> None:
    err = DuplicateRegistrationError(
        value="claude",
        existing="bookwright.integrations.claude.ClaudeIntegration",
        new="other.module.OtherClaude",
    )
    payload = err.to_dict()
    assert payload == {
        "code": "duplicate_registration",
        "value": "claude",
        "existing": "bookwright.integrations.claude.ClaudeIntegration",
        "new": "other.module.OtherClaude",
        "message": err.message,
    }
    json.dumps(payload)


def test_invalid_option_declaration_error_payload() -> None:
    err = InvalidOptionDeclarationError(rule="bad_flag_prefix", value="skills-dir")
    payload = err.to_dict()
    assert payload == {
        "code": "invalid_option_declaration",
        "rule": "bad_flag_prefix",
        "value": "skills-dir",
        "message": err.message,
    }
    json.dumps(payload)


def test_invalid_integration_error_payload() -> None:
    err = InvalidIntegrationError(
        rule="empty_key",
        value="bookwright.integrations.base.SkillsIntegration",
    )
    payload = err.to_dict()
    assert payload == {
        "code": "invalid_integration",
        "rule": "empty_key",
        "value": "bookwright.integrations.base.SkillsIntegration",
        "message": err.message,
    }
    json.dumps(payload)


# ---------- class-level code attribute is the source of truth ----------


@pytest.mark.parametrize(
    "cls,expected_code",
    [
        (UnknownIntegrationError, "unknown_integration"),
        (UnknownOptionError, "unknown_option"),
        (MalformedOptionError, "malformed_option"),
        (DuplicateRegistrationError, "duplicate_registration"),
        (InvalidOptionDeclarationError, "invalid_option_declaration"),
        (InvalidIntegrationError, "invalid_integration"),
    ],
)
def test_class_level_code_is_pinned(
    cls: type[_IntegrationError],
    expected_code: str,
) -> None:
    assert cls.code == expected_code


def test_forgetful_subclass_fails_at_class_definition() -> None:
    """R18 — `_IntegrationError.__init_subclass__` rejects subclasses that
    don't override `to_dict` at class-definition time (i.e., at import),
    not at production --json serialisation time.

    `__init_subclass__` is used instead of `abc.ABC` because
    `BaseException.__new__` (C-level) bypasses `__abstractmethods__`,
    making `class Foo(Exception, ABC)` enforcement a no-op.
    """

    with pytest.raises(TypeError) as exc_info:

        class ForgetfulError(_IntegrationError):
            code = "forgetful"
            # `to_dict` deliberately not overridden.

    msg = str(exc_info.value)
    assert "to_dict" in msg
    assert "ForgetfulError" in msg


def test_all_error_types_round_trip_through_json_dumps() -> None:
    """SC-008 — every payload survives a json.dumps/loads cycle unchanged."""

    instances = [
        UnknownIntegrationError(value="x", valid=["a", "b"]),
        UnknownOptionError(integration="g", value="--y", valid=["--z"]),
        MalformedOptionError(rule="missing_value", value="--z"),
        DuplicateRegistrationError(value="k", existing="a.A", new="b.B"),
        InvalidOptionDeclarationError(rule="bad_type", value="weird"),
        InvalidIntegrationError(rule="empty_key", value="some.module.Cls"),
    ]
    for err in instances:
        payload = err.to_dict()
        roundtripped = json.loads(json.dumps(payload))
        assert roundtripped == payload
