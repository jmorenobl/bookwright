"""The prose/structure seam — a Markdown-aware line view for prose validators.

Modelled on :mod:`bookwright.io.frontmatter`'s line-tracking. Splits prose text
into 1-based :class:`ProseLine` records whose ``normalized`` form has had leading
*structural block prefixes* (ATX headings, bullets, blockquotes) stripped, so a
validator's surface heuristics never see the Markdown the scaffold itself emits.

This is the single place that "sees past" block markup. The three prose validators
consume it instead of each re-implementing a private stripper (closing the surface
class behind DEBT-004/007/008). Inline emphasis (``**``/``*``/``_``) is **never** a
block prefix — that is ``focalization``'s own vocabulary, not the seam's (C2.2/C4).

Stdlib only — ``re`` + ``dataclasses``, no Markdown parser/AST (FR-012).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["ProseLine", "ProseView", "is_placeholder", "prose_view"]

# An ATX heading marker, strict at column 0 (mirrors the deleted
# ``character_presence._HEADING_MARKER`` — no leading whitespace tolerated).
_HEADING_MARKER = re.compile(r"^#{1,6}\s+")
# A bullet/blockquote marker, tolerant of leading whitespace (mirrors the deleted
# ``focalization._BULLET``). The trailing ``\s+`` distinguishes a list bullet
# ``* text`` from an inline emphasis run ``*text*`` (never a block prefix — C2.2).
_BULLET_MARKER = re.compile(r"^\s*[-*+>]\s+")
# A declaration body that is *solely* an unanswered ``[PENDING: …]`` token
# (mirrors the deleted ``focalization._PENDING_ONLY``). The ``^…$`` anchor is
# load-bearing: real text before *or* after the token keeps it a real body (C3).
_PENDING_ONLY = re.compile(r"(?i)^\s*\[pending\b[^\]]*\]\s*$")


@dataclass(frozen=True)
class ProseLine:
    """One source line: its 1-based number, original text, and normalized text."""

    number: int
    raw: str
    normalized: str


ProseView = tuple[ProseLine, ...]


def _normalize(line: str) -> str:
    """Strip leading block prefix(es) iteratively, one per pass (contract C2).

    Each pass removes a single heading marker (preferred) or bullet/blockquote
    marker via ``sub(count=1)``, left-to-right, until neither matches — so a nested
    ``> - text`` reduces to ``text``. Every stripping pass deletes ≥ 1 character, so
    the loop terminates (C2.1).
    """
    while True:
        if _HEADING_MARKER.match(line):
            line = _HEADING_MARKER.sub("", line, count=1)
        elif _BULLET_MARKER.match(line):
            line = _BULLET_MARKER.sub("", line, count=1)
        else:
            return line


def prose_view(text: str) -> ProseView:
    """Split ``text`` into a tuple of :class:`ProseLine`, one per source line.

    ``number`` is the 1-based source index (never a regex match offset, C1.4);
    ``raw`` is the exact ``splitlines()`` element; ``normalized`` is its
    block-prefix-stripped form. ``prose_view("") == ()`` (C1.2).
    """
    return tuple(
        ProseLine(number=number, raw=raw, normalized=_normalize(raw))
        for number, raw in enumerate(text.splitlines(), start=1)
    )


def is_placeholder(body: str) -> bool:
    """Whether ``body`` is *solely* an unanswered ``[PENDING: …]`` token (C3)."""
    return _PENDING_ONLY.match(body) is not None
