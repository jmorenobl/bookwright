"""No-regression gate for the traceability-tag policy (FR-010, SC-004).

Re-runs the deterministic sweep that CONTRIBUTING.md § "Traceability tags in
code" forbids and fails on any forbidden tag under ``src/`` or ``tests/``,
pinning the cleaned-up count at zero forever. The gate rides ``uv run pytest``
and therefore CI on every push/PR.

Stdlib only (``re`` + ``pathlib``); no new dependency.
"""

from __future__ import annotations

import re
from pathlib import Path

# Single source of truth — identical to the sweep in spec/research/plan:
#   ``T`` + exactly 3 digits | ``US`` + optional ``-`` + digits | ``+US`` + digits.
FORBIDDEN = re.compile(r"\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCAN_ROOTS = ("src", "tests")
_THIS_FILE = Path(__file__).resolve()


def _iter_in_scope_files() -> list[Path]:
    """Every text file under ``src/`` and ``tests/``, minus this gate itself."""
    files: list[Path] = []
    for root in _SCAN_ROOTS:
        for path in sorted((_REPO_ROOT / root).rglob("*")):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            if path.resolve() == _THIS_FILE:
                continue
            files.append(path)
    return files


def _scan(path: Path) -> list[tuple[int, str]]:
    """Return ``(line_number, matched_token)`` pairs; skip undecodable binaries."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in FORBIDDEN.finditer(line):
            hits.append((lineno, match.group(0)))
    return hits


def test_no_forbidden_traceability_tags() -> None:
    """No ``T0xx`` / ``US-x`` / ``USx`` / ``+USx`` tag survives under src/+tests/."""
    offenders: list[str] = []
    for path in _iter_in_scope_files():
        rel = path.relative_to(_REPO_ROOT)
        for lineno, token in _scan(path):
            offenders.append(f"  {rel}:{lineno}: {token}")

    header = (
        'Forbidden traceability tags found (see CONTRIBUTING.md § "Traceability tags in code"):'
    )
    footer = "Convert to a durable FR/SC/D ref or rewrite to neutral prose."
    message = "\n".join([header, *offenders, footer])
    assert not offenders, message
