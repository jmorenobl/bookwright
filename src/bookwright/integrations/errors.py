"""Structured exception family for the integrations layer (FR-035, FR-036).

Every public error inherits from the private `_IntegrationError` base — which now
inherits the shared `BookwrightError` — and exposes:
    - a class-level ``code: str`` (immutable identifier),
    - a ``message: str`` attribute (human-readable, also passed to
      ``Exception.__init__``),
    - the structured fields under the canonical envelope's ``details`` (the
      single ``to_json()`` is owned by `BookwrightError`; see
      ``specs/018-unified-error-envelope/contracts/error-envelope.md``).

The ``init --json`` / ``integration use --json`` consumers read the canonical
``to_json()`` body; renaming any ``details`` field below is a breaking change.
"""

from __future__ import annotations

from bookwright.errors import BookwrightError


class _IntegrationError(BookwrightError):
    """Private base for all structured errors raised by the integrations layer.

    Subclasses MUST set a non-empty class-level ``code`` and assign their
    structured fields on ``self`` in ``__init__`` (e.g., ``self.rule``,
    ``self.value``), then end ``__init__`` with
    ``super().__init__(message, {<public attrs>})`` so the inherited
    ``BookwrightError.to_json()`` emits the canonical envelope. The base is
    abstract: it declares no ``code`` and is never serialized directly.
    """


class UnknownIntegrationError(_IntegrationError):
    """Raised by ``get(key)`` when ``key`` is not in ``INTEGRATION_REGISTRY``."""

    code = "unknown_integration"

    def __init__(self, *, value: str | None, valid: list[str]) -> None:
        self.value = value
        self.valid = list(valid)
        message = f"unknown integration: {value!r}; valid: [{', '.join(self.valid)}]"
        super().__init__(message, {"value": value, "valid": self.valid})


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
        super().__init__(
            message,
            {"integration": integration, "value": value, "valid": self.valid},
        )


class MalformedOptionError(_IntegrationError):
    """Raised by ``parse_options`` on a structural rule violation in user input."""

    code = "malformed_option"

    def __init__(self, *, rule: str, value: str) -> None:
        self.rule = rule
        self.value = value
        message = f"malformed option {value!r}: {rule}"
        super().__init__(message, {"rule": rule, "value": value})


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
        super().__init__(message, {"value": value, "existing": existing, "new": new})


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
        super().__init__(message, {"rule": rule, "value": value})


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
        super().__init__(message, {"rule": rule, "value": value})


class SkillLintError(_IntegrationError):
    """Raised by ``lint_skill_md`` on the first agentskills.io violation (FR-015).

    Post-write: a freshly generated skill is linted right after it is written, and
    ``generate_skill_md`` deletes the offending skill dir before this error escapes
    (FR-016 — "no invalid SKILL.md on disk"). Note that ``generate_skill_md`` does
    NOT re-lint a *pre-existing* ``SKILL.md``: idempotency (FR-014) skips it
    untouched, so re-validation of hand-edited skills is the job of the standalone
    ``lint_skill_md`` call (and the iteration-11 validation system that reuses it),
    not of ``setup()``.
    """

    code = "skill_lint_failed"

    def __init__(self, *, skill: str, rule: str, detail: str) -> None:
        self.skill = skill
        self.rule = rule
        self.detail = detail
        message = f"skill {skill!r} failed lint rule {rule!r}: {detail}"
        super().__init__(message, {"skill": skill, "rule": rule, "detail": detail})


class SkillMaterializationError(_IntegrationError):
    """Raised by ``generate_skill_md`` on a pre-write authoring error (FR-010/FR-020).

    ``rule`` ∈ {``dangling_reference``, ``name_frontmatter_mismatch``,
    ``residual_token``}. All are detected *before* the first filesystem write, so a
    rejected source leaves **zero** on-disk state (nothing to clean up).
    """

    code = "skill_materialization_failed"

    def __init__(self, *, skill: str, rule: str, detail: str) -> None:
        self.skill = skill
        self.rule = rule
        self.detail = detail
        message = f"skill {skill!r} materialization failed ({rule}): {detail}"
        super().__init__(message, {"skill": skill, "rule": rule, "detail": detail})
