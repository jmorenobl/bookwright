"""Public API for the ``bookwright.integrations`` layer (iteration 3).

Importing this package eagerly populates ``INTEGRATION_REGISTRY`` via
``_register_builtins()`` (FR-002). Downstream consumers (iteration 4's
``bookwright init``, iteration 9's skills materializer) need only::

    from bookwright.integrations import get, list_keys, parse_options

The public surface (re-exported in ``__all__``) is contractual; renaming
any symbol below is a breaking change for iterations 4+.
"""

from __future__ import annotations

from bookwright.integrations.base import SkillsIntegration
from bookwright.integrations.claude import ClaudeIntegration
from bookwright.integrations.constants import (
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
    SKILL_PLACEHOLDER_MARKER_NAME,
)
from bookwright.integrations.errors import (
    DuplicateRegistrationError,
    InvalidIntegrationError,
    InvalidOptionDeclarationError,
    MalformedOptionError,
    UnknownIntegrationError,
    UnknownOptionError,
)
from bookwright.integrations.generic import GenericIntegration
from bookwright.integrations.options import IntegrationOption, parse_options

INTEGRATION_REGISTRY: dict[str, type[SkillsIntegration]] = {}


def _fqcn(cls: type) -> str:
    """Fully-qualified class name, used in DuplicateRegistrationError payloads."""

    return f"{cls.__module__}.{cls.__qualname__}"


def _register(cls: type[SkillsIntegration]) -> None:
    """Register one integration class under its declared ``cls.key``.

    Re-registering the same class is a no-op (FR-002 idempotency under
    ``importlib.reload``). Registering a *different* class under an
    existing key raises ``DuplicateRegistrationError`` naming both
    classes (FR-005, research R5). Registering a class whose ``key``
    is empty (the base-class sentinel) raises ``InvalidIntegrationError``
    (R13) — subclasses MUST override ``key`` with a non-empty string.
    """

    if not cls.key:
        raise InvalidIntegrationError(rule="empty_key", value=_fqcn(cls))

    existing = INTEGRATION_REGISTRY.get(cls.key)
    if existing is cls:
        return
    if existing is not None:
        raise DuplicateRegistrationError(
            value=cls.key,
            existing=_fqcn(existing),
            new=_fqcn(cls),
        )
    INTEGRATION_REGISTRY[cls.key] = cls


def _register_builtins() -> None:
    """Populate ``INTEGRATION_REGISTRY`` with the two v0 built-ins.

    Future contributors add a single ``_register(NewIntegration)`` line
    here (per quickstart "Adding a new integration"). No edit to
    ``base.py``, ``claude/``, or ``generic/`` is permitted — this is
    enforced mechanically by ``tests/integrations/test_plugin_contract.py``
    (FR-031).
    """

    _register(ClaudeIntegration)
    _register(GenericIntegration)


def get(key: str) -> type[SkillsIntegration]:
    """Look up an integration class by its short key (FR-003)."""

    cls = INTEGRATION_REGISTRY.get(key)
    if cls is None:
        raise UnknownIntegrationError(value=key, valid=list_keys())
    return cls


def list_keys() -> list[str]:
    """Return registered integration keys, alphabetically sorted (FR-004)."""

    return sorted(INTEGRATION_REGISTRY.keys())


_register_builtins()


__all__ = [
    "INTEGRATION_REGISTRY",
    "SKILL_DESCRIPTION_MAX_LENGTH",
    "SKILL_NAME_MAX_LENGTH",
    "SKILL_PLACEHOLDER_MARKER_NAME",
    "ClaudeIntegration",
    "DuplicateRegistrationError",
    "GenericIntegration",
    "IntegrationOption",
    "InvalidIntegrationError",
    "InvalidOptionDeclarationError",
    "MalformedOptionError",
    "SkillsIntegration",
    "UnknownIntegrationError",
    "UnknownOptionError",
    "get",
    "list_keys",
    "parse_options",
]
