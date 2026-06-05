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

# Single source of truth for the forbidden patterns (FR-001/FR-002):
#   ``T`` + exactly 3 digits | ``US`` + optional ``-`` + digits | ``+US`` + digits.
# ``\bT[0-9]{3}\b`` matches FR-001 literally (T000-T999), so a future ``tasks.md``
# reaching ``T100``+ cannot leak a tag past the gate.
FORBIDDEN = re.compile(r"\bT[0-9]{3}\b|\bUS-?[0-9]+\b|\+US[0-9]+")

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


# The sweep above only proves the tree is *currently* clean; on its own it would
# pass vacuously if the detector ever broke. These two guard the detector itself
# so a future refactor of ``FORBIDDEN`` cannot silently neuter the gate.


def test_detector_catches_each_forbidden_pattern(tmp_path: Path) -> None:
    """Every forbidden shape (FR-001/FR-002) is detected by ``_scan``."""
    sample = tmp_path / "sample.py"
    sample.write_text(
        "\n".join(
            [
                "tag T013 here",  # FR-001: T + exactly 3 digits
                "story US1 here",  # FR-002: USx
                "story US-3 here",  # FR-002: US-x
                "story +US2 here",  # FR-002: +USx
                "future T100 here",  # FR-001: T100+ must not leak
            ]
        ),
        encoding="utf-8",
    )
    tokens = {token for _, token in _scan(sample)}
    # ``+US2`` is consumed whole by the ``\+US[0-9]+`` alternative, so the bare
    # ``US2`` is not yielded as a separate (overlapping) match.
    assert tokens == {"T013", "US1", "US-3", "+US2", "T100"}


def test_detector_ignores_permitted_refs(tmp_path: Path) -> None:
    """Durable refs and the gate's own vocabulary do not false-positive (FR-011)."""
    sample = tmp_path / "permitted.py"
    sample.write_text(
        "dedup feature values (FR-021); SC-001 clean; decision D8; "
        "bookwright-design.md § 20.5; US English; matrix T273K and var _T013\n",
        encoding="utf-8",
    )
    assert _scan(sample) == []
