"""Structured exception family for the integrations layer (FR-035, FR-036).

Every public error inherits from the private `_IntegrationError` base and
exposes:
    - a class-level ``code: str`` (immutable identifier),
    - a ``message: str`` attribute (human-readable, also passed to
      ``Exception.__init__``),
    - a ``to_dict()`` method returning a ``json.dumps``-compatible dict
      whose shape is pinned in
      ``specs/003-integration-architecture/data-model.md § 6``.

The iteration-4 ``init --json`` consumer reads ``to_dict()`` directly to
populate its error envelope; renaming any field below is a breaking change.
"""

from __future__ import annotations


class _IntegrationError(Exception):
    """Private base for all structured errors raised by the integrations layer.

    Subclasses MUST set a non-empty class-level ``code`` and assign their
    structured fields on ``self`` in ``__init__`` (e.g., ``self.rule``,
    ``self.value``). The base ``to_dict()`` (R20) returns
    ``{'code': self.code, 'message': self.message, **<public instance attrs>}``
    — derived from ``vars(self)`` minus dunder/underscore-prefixed names
    and the ``message`` key (which is hoisted up). Subclasses do NOT need
    to override ``to_dict`` for the standard payload shape; the field
    order in the returned dict is ``code, message, <attrs in insertion
    order>`` because the iteration-4 ``--json`` envelope compares by
    value, not by serialised string.
    """

    code: str = ""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            **{k: v for k, v in vars(self).items() if not k.startswith("_") and k != "message"},
        }


class UnknownIntegrationError(_IntegrationError):
    """Raised by ``get(key)`` when ``key`` is not in ``INTEGRATION_REGISTRY``."""

    code = "unknown_integration"

    def __init__(self, *, value: str | None, valid: list[str]) -> None:
        self.value = value
        self.valid = list(valid)
        message = f"unknown integration: {value!r}; valid: [{', '.join(self.valid)}]"
        super().__init__(message)


class UnknownOptionError(_IntegrationError):
    """Raised by ``parse_options`` for a flag the integration does not declare."""

    code = "unknown_option"

    def __init__(self, *, integration: str, value: str, valid: list[str]) -> None:
        self.integration = integration
        self.value = value
        self.valid = list(valid)
        message = (
            f"unknown option {value} for integration {integration!r}; "
            f"valid: [{', '.join(self.valid)}]"
        )
        super().__init__(message)


class MalformedOptionError(_IntegrationError):
    """Raised by ``parse_options`` on a structural rule violation in user input."""

    code = "malformed_option"

    def __init__(self, *, rule: str, value: str) -> None:
        self.rule = rule
        self.value = value
        message = f"malformed option {value!r}: {rule}"
        super().__init__(message)


class DuplicateRegistrationError(_IntegrationError):
    """Raised by ``_register`` when a *different* class is bound to an existing key."""

    code = "duplicate_registration"

    def __init__(self, *, value: str, existing: str, new: str) -> None:
        self.value = value
        self.existing = existing
        self.new = new
        message = (
            f"duplicate integration registration for key {value!r}: "
            f"already registered as {existing}, refusing to replace with {new}"
        )
        super().__init__(message)


class InvalidOptionDeclarationError(_IntegrationError):
    """Raised when an ``IntegrationOption`` descriptor itself is malformed.

    Programming-error guard for FR-015: surfaced the first time
    ``parse_options`` introspects an integration's ``options()``. Never
    user-facing — the offending integration class needs to be fixed.
    """

    code = "invalid_option_declaration"

    def __init__(self, *, rule: str, value: str) -> None:
        self.rule = rule
        self.value = value
        message = (
            f"invalid option declaration ({rule}): {value!r}; "
            "this is a programming error in the integration's options()"
        )
        super().__init__(message)


class InvalidIntegrationError(_IntegrationError):
    """Raised by ``_register`` when an integration class is malformed.

    Programming-error guard (R13): catches integrations that forgot to
    override the base ``SkillsIntegration`` sentinel defaults
    (e.g., ``cls.key = ""``). Never user-facing — the offending
    integration class needs to be fixed.
    """

    code = "invalid_integration"

    def __init__(self, *, rule: str, value: str) -> None:
        self.rule = rule
        self.value = value
        message = (
            f"invalid integration ({rule}): {value!r}; "
            "this is a programming error in the integration class"
        )
        super().__init__(message)
