"""FR-028 / FR-029 / SC-005 — progressive-disclosure references resolve.

``references/`` exists and is non-empty; every ``references/<file>.md`` path
cited across the 10 command bodies resolves to a shipped file (hard gate, FR-029);
and every shipped reference is cited by at least one body (soft, no orphans).
"""

from __future__ import annotations

import re

from .helpers import REFERENCES_DIR, command_files, read_text, reference_files

_CITATION = re.compile(r"references/([A-Za-z0-9_-]+\.md)")


def _cited_reference_names() -> set[str]:
    cited: set[str] = set()
    for path in command_files():
        cited |= set(_CITATION.findall(read_text(path)))
    return cited


def test_references_dir_exists_and_non_empty() -> None:
    assert REFERENCES_DIR.is_dir(), "references/ directory is missing"
    assert reference_files(), "references/ ships no .md files"


def test_every_cited_reference_resolves() -> None:
    # FR-029 hard gate: no dangling reference.
    shipped = {p.name for p in reference_files()}
    dangling = _cited_reference_names() - shipped
    assert not dangling, f"dangling references cited but not shipped: {sorted(dangling)}"


def test_no_orphan_references() -> None:
    # Soft: every shipped reference is cited by >= 1 body.
    shipped = {p.name for p in reference_files()}
    orphans = shipped - _cited_reference_names()
    assert not orphans, f"orphan references shipped but never cited: {sorted(orphans)}"
