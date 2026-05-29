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

from bookwright.commands._init_validate import (
    InvalidProjectNameError,
    check_slug_not_reserved,
)
from bookwright.core.iso639_1 import ISO_639_1_CODES

AUTHOR_SENTINEL = "Unknown Author"
DEFAULT_LANGUAGE = "es"


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
