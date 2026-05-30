"""Deterministic, ASCII-only slug generation (design § 4.5, FR-005/006)."""

from __future__ import annotations

from slugify import slugify

from bookwright.golem.errors import EmptySlugError


def make_slug(name: str) -> str:
    """Return the canonical slug for ``name``.

    Uses ``python-slugify`` in its default mode: lowercase, ASCII
    transliteration (``José Peña`` → ``jose-pena``), single-hyphen separators,
    edges trimmed. The rule is pure, so the same name always yields the same
    slug (FR-005). A name that reduces to the empty string (e.g. punctuation
    only) is rejected loudly with :class:`EmptySlugError` (FR-006).
    """
    slug = slugify(name)
    if not slug:
        raise EmptySlugError(name)
    return slug
