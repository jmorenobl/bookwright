"""Read a Markdown file's leading YAML frontmatter fence (data-model § 2, R3).

A thin split-then-``yaml.safe_load`` reader. It records each top-level key's
1-based source line so the bible mapper can resolve a ``file:line`` provenance
locator (R6). Malformed YAML surfaces as ``yaml.YAMLError`` for the caller to
wrap in :class:`~bookwright.io.errors.InvalidFrontmatterError`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml

_FENCE = "---"
_TOP_LEVEL_KEY = re.compile(r"^([A-Za-z_][\w-]*)\s*:")


@dataclass(frozen=True)
class Frontmatter:
    """The parsed result of one Markdown file's frontmatter fence."""

    metadata: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    key_lines: dict[str, int] = field(default_factory=dict)


def parse_frontmatter(text: str) -> Frontmatter:
    """Split a leading ``---`` … ``---`` fence and parse the YAML block.

    A file with no opening fence (or no closing fence) yields ``{}`` metadata and
    the whole text as the body. Each top-level YAML key maps to its 1-based line
    in the original file via :attr:`Frontmatter.key_lines`.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FENCE:
        return Frontmatter(metadata={}, body=text, key_lines={})

    closing: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == _FENCE:
            closing = index
            break
    if closing is None:
        return Frontmatter(metadata={}, body=text, key_lines={})

    block_lines = lines[1:closing]
    loaded = yaml.safe_load("\n".join(block_lines))
    metadata: dict[str, Any] = loaded if isinstance(loaded, dict) else {}

    key_lines: dict[str, int] = {}
    for offset, line in enumerate(block_lines):
        match = _TOP_LEVEL_KEY.match(line)
        if match:
            # block_lines[0] is the file's second line (line 1 is the fence).
            key_lines.setdefault(match.group(1), offset + 2)

    body = "\n".join(lines[closing + 1 :])
    return Frontmatter(metadata=metadata, body=body, key_lines=key_lines)
