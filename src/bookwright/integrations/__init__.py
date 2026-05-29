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
    Registering a class whose ``default_skills_dir`` is empty raises
    ``InvalidIntegrationError`` (R25) for the same reason: an empty
    default would surface as a misleading ``resolves_to_project_root``
    error in ``setup()`` because ``Path("")`` collapses to ``Path(".")``.
    """

    new_fqcn = _fqcn(cls)
    if not cls.key:
        raise InvalidIntegrationError(rule="empty_key", value=new_fqcn)
    if not cls.default_skills_dir:
        # R25 — symmetric guard to R13. Without this, a forgetful subclass
        # that overrides `key` but leaves `default_skills_dir` at the
        # base sentinel ("") would register successfully and then fail
        # at setup() time with `resolves_to_project_root` (because
        # `Path("") == Path(".")` collapses to project_root), pointing
        # the author at the wrong layer.
        raise InvalidIntegrationError(rule="empty_default_skills_dir", value=new_fqcn)

    existing = INTEGRATION_REGISTRY.get(cls.key)
    if existing is None:
        INTEGRATION_REGISTRY[cls.key] = cls
        return

    # R12 — compare by fully-qualified class name, not by identity. After
    # `importlib.reload(bookwright.integrations.claude)` the reloaded
    # `ClaudeIntegration` is a NEW class object with different identity
    # from the one already in the registry; relying on `is` would raise
    # DuplicateRegistrationError spuriously, breaking the FR-002 reload
    # idempotency promise. FQCN equality preserves the duplicate guard
    # for genuinely different classes (different module/qualname) that
    # collide on `key`.
    # R27 — compute existing FQCN once and reuse for both the equality
    # check and the error payload, instead of recomputing on each call
    # site.
    existing_fqcn = _fqcn(existing)
    if existing is cls or existing_fqcn == new_fqcn:
        INTEGRATION_REGISTRY[cls.key] = cls  # rebind to the reloaded class
        return
    raise DuplicateRegistrationError(
        value=cls.key,
        existing=existing_fqcn,
        new=new_fqcn,
    )


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
    # NOTE: `INTEGRATION_REGISTRY` is intentionally NOT exposed in __all__
    # (R17). The dict remains importable from the module namespace for
    # the in-tree test snapshot fixture and the registry-mutation guard
    # tests, but external consumers MUST go through `get`, `list_keys`,
    # and `_register` — direct dict assignment bypasses FR-005's
    # duplicate-detection guard and the R13 empty-key guard.
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
