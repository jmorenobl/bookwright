"""Shared path constants and enumerators for the iteration-7 template +
iteration-8 command-source suites.

Not a test module (no ``test_`` prefix → not collected). Locates the packaged
resource trees on disk, classifies the authored documents the validation tests
sweep, and exposes thin frontmatter accessors. Imports only the shipped
``bookwright`` package.
"""

from __future__ import annotations

from math import ceil
from pathlib import Path
from typing import Any

import bookwright
from bookwright.io.frontmatter import parse_frontmatter

_pkg_init = bookwright.__file__
assert _pkg_init is not None, "bookwright package has no __file__"
_PKG_ROOT = Path(_pkg_init).resolve().parent

#: Stamped-once skeleton singletons (rendered/byte-copied by ``init``).
PROJECT_DIR = _PKG_ROOT / "resources" / "project"
#: Re-instanceable molds + the verify-only manifest template.
TEMPLATES_DIR = _PKG_ROOT / "resources" / "templates"
#: Command sources (the 12 ``*.md``) + their tier-3 references subtree.
COMMANDS_DIR = _PKG_ROOT / "resources" / "commands"
REFERENCES_DIR = COMMANDS_DIR / "references"

#: The 12 command source basenames: the 10 fixed by FR-001 (design § 10.4 order),
#: iteration-14's ``bookwright-research`` and iteration-15's ``bookwright-verify``.
EXPECTED_COMMANDS: tuple[str, ...] = (
    "bookwright-constitution",
    "bookwright-bible",
    "bookwright-outline",
    "bookwright-scenes",
    "bookwright-draft",
    "bookwright-synopsis",
    "bookwright-clarify",
    "bookwright-analyze",
    "bookwright-continuity",
    "bookwright-checklist",
    "bookwright-research",
    "bookwright-verify",
)

#: Command classification — single executable source of truth (spec "Command
#: classification"). Generative commands write project files and carry the marker
#: + update-in-place rules; report-only commands write nothing.
GENERATIVE_COMMANDS: tuple[str, ...] = (
    "bookwright-constitution",
    "bookwright-bible",
    "bookwright-outline",
    "bookwright-scenes",
    "bookwright-draft",
    "bookwright-synopsis",
    # iteration 14 — writes bible/research/* files and merges them in place.
    "bookwright-research",
)
REPORT_ONLY_COMMANDS: tuple[str, ...] = (
    "bookwright-clarify",
    "bookwright-analyze",
    "bookwright-continuity",
    "bookwright-checklist",
    # iteration 15 — verifies the manuscript against research anchors; writes nothing.
    "bookwright-verify",
)

#: Scaffolding markers that must never survive into an authored or stamped file.
SENTINELS: tuple[str, ...] = (
    "Placeholder — iteration 7 lands the full template",
    "Placeholder — iteration 7",
    "{{TODO}}",
    "{{ TODO }}",
    "TODO: iteration 7",
)


def read_text(path: Path) -> str:
    """Read ``path`` as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def project_prose_files() -> list[Path]:
    """Authored skeleton prose: every ``.md`` / ``.j2`` under bible/ + outline/, plus README."""
    found: list[Path] = []
    for sub in ("bible", "outline"):
        root = PROJECT_DIR / sub
        found += [p for p in root.rglob("*") if p.is_file() and p.suffix in {".md", ".j2"}]
    readme = PROJECT_DIR / "README.md.j2"
    if readme.is_file():
        found.append(readme)
    return sorted(found)


def mold_files() -> list[Path]:
    """Every re-instanceable mold (``*.tmpl``) under ``resources/templates/``."""
    return sorted(p for p in TEMPLATES_DIR.rglob("*.tmpl") if p.is_file())


def authored_templates() -> list[Path]:
    """All human-authored prose deliverables (skeleton prose + molds)."""
    return project_prose_files() + mold_files()


def resource_text_files() -> list[Path]:
    """Every non-cache file under all three packaged resource trees (for the sentinel sweep)."""
    found: list[Path] = []
    for root in (PROJECT_DIR, TEMPLATES_DIR, COMMANDS_DIR):
        found += [
            p
            for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        ]
    return sorted(found)


def looks_spanish(text: str) -> bool:
    """Cheap heuristic: at least three Spanish function words appear in ``text``."""
    haystack = f" {text.lower()} "
    markers = (
        " de ",
        " la ",
        " el ",
        " que ",
        " los ",
        " las ",
        " con ",
        " para ",
        " en ",
        " del ",
    )
    return sum(marker in haystack for marker in markers) >= 3


def command_files() -> list[Path]:
    """The 12 command source ``*.md`` directly under ``commands/`` (excludes references/)."""
    if not COMMANDS_DIR.is_dir():
        return []
    return sorted(p for p in COMMANDS_DIR.glob("*.md") if p.is_file())


def reference_files() -> list[Path]:
    """Every tier-3 reference ``*.md`` under ``commands/references/``."""
    if not REFERENCES_DIR.is_dir():
        return []
    return sorted(p for p in REFERENCES_DIR.glob("*.md") if p.is_file())


def command_body(path: Path) -> str:
    """Frontmatter-stripped body of the command source at ``path``."""
    return parse_frontmatter(read_text(path)).body


def command_metadata(path: Path) -> dict[str, Any]:
    """Parsed frontmatter metadata of the command source at ``path``."""
    return parse_frontmatter(read_text(path)).metadata


def approx_tokens(text: str) -> int:
    """Token estimate for the < 5000-token body budget (FR-015, R1).

    Deterministic ``ceil(len / 4)`` char heuristic — the same definition of
    "token" used by ``integrations.lint.approx_tokens`` so the source-side gate
    and the materialized-side lint stay in lock-step (a source that passes here
    passes lint), and the verdict never depends on installed packages.
    """
    return ceil(len(text) / 4)
