"""Structured-error canonical-envelope shape + JSON round-trip (FR-036, SC-008).

Since iteration 018 the integrations hierarchy emits the unified error envelope
owned by ``BookwrightError.to_json()`` — ``{status, code, message[, details]}`` —
instead of the former hand-rolled ``to_dict()`` (now deleted). The public
attributes move under ``details``.
"""

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
    payload = err.to_json()
    assert payload == {
        "status": "error",
        "code": "unknown_integration",
        "message": err.message,
        "details": {"value": "copilot", "valid": ["claude", "generic"]},
    }
    assert err.code == UnknownIntegrationError.code
    assert err.message
    json.dumps(payload)  # no custom encoder needed


def test_unknown_integration_error_with_none_value() -> None:
    err = UnknownIntegrationError(value=None, valid=["claude", "generic"])
    payload = err.to_json()
    assert payload["details"]["value"] is None
    assert json.loads(json.dumps(payload))["details"]["value"] is None


def test_unknown_option_error_payload() -> None:
    err = UnknownOptionError(integration="generic", value="--bogus", valid=["--skills-dir"])
    payload = err.to_json()
    assert payload == {
        "status": "error",
        "code": "unknown_option",
        "message": err.message,
        "details": {
            "integration": "generic",
            "value": "--bogus",
            "valid": ["--skills-dir"],
        },
    }
    json.dumps(payload)


def test_malformed_option_error_payload() -> None:
    err = MalformedOptionError(rule="missing_value", value="--skills-dir")
    payload = err.to_json()
    assert payload == {
        "status": "error",
        "code": "malformed_option",
        "message": err.message,
        "details": {"rule": "missing_value", "value": "--skills-dir"},
    }
    json.dumps(payload)


def test_duplicate_registration_error_payload() -> None:
    err = DuplicateRegistrationError(
        value="claude",
        existing="bookwright.integrations.claude.ClaudeIntegration",
        new="other.module.OtherClaude",
    )
    payload = err.to_json()
    assert payload == {
        "status": "error",
        "code": "duplicate_registration",
        "message": err.message,
        "details": {
            "value": "claude",
            "existing": "bookwright.integrations.claude.ClaudeIntegration",
            "new": "other.module.OtherClaude",
        },
    }
    json.dumps(payload)


def test_invalid_option_declaration_error_payload() -> None:
    err = InvalidOptionDeclarationError(rule="bad_flag_prefix", value="skills-dir")
    payload = err.to_json()
    assert payload == {
        "status": "error",
        "code": "invalid_option_declaration",
        "message": err.message,
        "details": {"rule": "bad_flag_prefix", "value": "skills-dir"},
    }
    json.dumps(payload)


def test_invalid_integration_error_payload() -> None:
    err = InvalidIntegrationError(
        rule="empty_key",
        value="bookwright.integrations.base.SkillsIntegration",
    )
    payload = err.to_json()
    assert payload == {
        "status": "error",
        "code": "invalid_integration",
        "message": err.message,
        "details": {
            "rule": "empty_key",
            "value": "bookwright.integrations.base.SkillsIntegration",
        },
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


def test_subclass_without_serialiser_inherits_base() -> None:
    """A subclass that defines no serialiser inherits the one canonical
    ``BookwrightError.to_json()`` — its public attributes, passed as
    ``details`` to ``super().__init__``, surface under the ``details`` key.

    Confirms INV-1/SC-001: no integration error owns its own envelope
    serializer; the shared base is the single source of truth.
    """

    class CustomError(_IntegrationError):
        code = "custom"

        def __init__(self, *, foo: str, bar: int) -> None:
            self.foo = foo
            self.bar = bar
            super().__init__(
                f"custom error: foo={foo} bar={bar}",
                {"foo": foo, "bar": bar},
            )

    err = CustomError(foo="alpha", bar=42)
    # Neither this subclass nor the base defines a per-class serializer.
    assert "to_json" not in CustomError.__dict__
    assert "to_dict" not in CustomError.__dict__
    payload = err.to_json()
    assert payload == {
        "status": "error",
        "code": "custom",
        "message": err.message,
        "details": {"foo": "alpha", "bar": 42},
    }
    # Survives a json.dumps round-trip identically to the hand-rolled subclasses.
    assert json.loads(json.dumps(payload)) == payload


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
        payload = err.to_json()
        roundtripped = json.loads(json.dumps(payload))
        assert roundtripped == payload
