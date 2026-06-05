"""Resolution helpers consumed by ``init.run`` (research §R1, §R2, §R3, §R7).

Each helper is one source of truth so the orchestrator never needs to
re-derive the values. Tests monkeypatch a single symbol per behaviour.
"""

from __future__ import annotations

import locale
import os
import subprocess
import sys
from pathlib import Path

from slugify import slugify

from bookwright import integrations as _integrations
from bookwright.core.iso639_1 import ISO_639_1_CODES

from .envelope import emit_error
from .validate import (
    InvalidProjectNameError,
    check_slug_not_reserved,
)

AUTHOR_SENTINEL = "Unknown Author"
DEFAULT_LANGUAGE = "es"

AUTHOR_FALLBACK_WARNING = (
    "bookwright: warning: author could not be resolved from git config or $USER; "
    "using 'Unknown Author'"
)


def _git_config_user_name(cwd: Path) -> str | None:
    """Read ``git config --get user.name`` scoped to ``cwd``.

    Returns the trimmed value, or ``None`` if git is missing, the lookup
    failed, or the value is empty.
    """

    try:
        completed = subprocess.run(
            ["git", "config", "--get", "user.name"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None
    if completed.returncode != 0:
        return None
    candidate = completed.stdout.strip()
    return candidate or None


def resolve_authors(project_root: Path) -> tuple[list[str], bool]:
    """Resolve ``book.authors`` per FR-016 / research §R1.

    Returns ``(authors, fellback_to_sentinel)``. ``project_root`` is the
    directory used as ``cwd`` for the ``git config`` probe (the project
    parent in ``named`` mode is fine — git walks upward). Always returns
    a non-empty list.
    """

    candidate = _git_config_user_name(project_root)
    if candidate:
        return [candidate], False

    env_user = os.environ.get("USER", "").strip()
    if env_user:
        return [env_user], False

    return [AUTHOR_SENTINEL], True


def resolve_language() -> str:
    """Resolve ``book.language`` per FR-018 / research §R2.

    Reads ``locale.getlocale()`` (no ``setlocale`` mutation), takes the
    two-letter prefix, lower-cases it, and validates against
    ``ISO_639_1_CODES``. Falls back silently to ``"es"`` on any failure.
    """

    try:
        lang, _encoding = locale.getlocale()
    except (ValueError, TypeError):
        return DEFAULT_LANGUAGE
    if not lang:
        return DEFAULT_LANGUAGE
    prefix = lang[:2].lower()
    if prefix in ISO_639_1_CODES:
        return prefix
    return DEFAULT_LANGUAGE


def derive_slug(raw_name: str) -> str:
    """Slugify ``raw_name`` per FR-021 / research §R3.

    Uses ``python-slugify`` with the documented settings. Re-checks the
    slug against the FR-021a reserved-name list so a name that slugifies
    to ``"con"`` still trips.
    """

    slug = slugify(
        raw_name,
        lowercase=True,
        separator="-",
        allow_unicode=False,
        regex_pattern=r"[^A-Za-z0-9]+",
    )
    if not slug:
        raise InvalidProjectNameError(value=raw_name, rule="empty")
    return check_slug_not_reserved(slug)


def is_interactive() -> bool:
    """``True`` when stdin AND stdout are both TTYs (research §R7)."""

    return sys.stdin.isatty() and sys.stdout.isatty()


def parse_named_slug(name: str, json_output: bool) -> str:
    """Run ``derive_slug`` and translate failures to an envelope."""

    try:
        return derive_slug(name)
    except InvalidProjectNameError as exc:
        emit_error(
            code=exc.code,
            message=str(exc),
            details=exc.details or {},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )


def resolve_authors_or_warn(
    project_root: Path,
    warnings: list[str],
) -> list[str]:
    """Resolve authors and emit the FR-016 fallback warning on stderr if used.

    Per contract §5 the warning goes to stderr regardless of ``--json``; the
    JSON envelope mirrors it via the ``warnings`` list on the success path.
    """

    authors, fellback = resolve_authors(project_root)
    if fellback:
        warnings.append(AUTHOR_FALLBACK_WARNING)
        sys.stderr.write(AUTHOR_FALLBACK_WARNING + "\n")
    return authors


def resolve_integration(
    key: str,
    raw_options: str,
    *,
    json_output: bool,
) -> tuple[type[_integrations.SkillsIntegration], dict[str, str | bool]]:
    """Look up the integration class and parse its options, emitting on failure."""

    try:
        integration_cls = _integrations.get(key)
    except _integrations.UnknownIntegrationError as exc:
        emit_error(
            code=exc.code,
            message=exc.message,
            details=exc.details or {},
            exit_code=5,
            json_output=json_output,
            rolled_back=False,
        )

    try:
        parsed_options = _integrations.parse_options(raw_options, integration_cls)
    except (
        _integrations.UnknownOptionError,
        _integrations.MalformedOptionError,
        _integrations.InvalidOptionDeclarationError,
    ) as exc:
        emit_error(
            code=exc.code,
            message=exc.message,
            details=exc.details or {},
            exit_code=5,
            json_output=json_output,
            rolled_back=False,
        )

    return integration_cls, parsed_options
