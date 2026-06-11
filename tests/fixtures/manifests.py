"""The single shared minimal-manifest TOML literal (iteration 019 review).

One source of truth for the "smallest valid manifest" used by both the
``focus`` command suite (``tests/commands/focus/conftest.py``) and the core
``[focus]`` attachment suite (``tests/core/test_manifest_focus.py``). When a
future iteration grows the required manifest surface, this literal is the one
place to update — the two suites can no longer drift apart.
"""

from __future__ import annotations

#: A minimal valid manifest: the three required blocks plus one authored
#: comment, so byte-preservation assertions exercise comment round-tripping.
MINIMAL_MANIFEST = """\
# authored comment
[bookwright]
cli_version_min = "0.0.1"
schema_version = "golem-1.1"
manifest_version = "1"
uri_base = "https://example.org/focus/"

[book]
title = "Focus Book"
type = "novel"
language = "es"
authors = ["Solo Author"]

[integration]
key = "generic"
skills_dir = ".agents/skills"
"""


def with_focus(block: str, *, base: str = MINIMAL_MANIFEST) -> str:
    """Append a ``[focus]`` block holding ``block``'s key/value lines to ``base``."""
    return f"{base}\n[focus]\n{block}"
