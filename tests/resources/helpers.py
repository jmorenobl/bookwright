"""Shared path constants and enumerators for the iteration-7 template suite.

Not a test module (no ``test_`` prefix → not collected). Locates the two
packaged resource trees on disk and classifies the authored documents the
validation tests sweep. Imports only the shipped ``bookwright`` package.
"""

from __future__ import annotations

from pathlib import Path

import bookwright

_pkg_init = bookwright.__file__
assert _pkg_init is not None, "bookwright package has no __file__"
_PKG_ROOT = Path(_pkg_init).resolve().parent

#: Stamped-once skeleton singletons (rendered/byte-copied by ``init``).
PROJECT_DIR = _PKG_ROOT / "resources" / "project"
#: Re-instanceable molds + the verify-only manifest template.
TEMPLATES_DIR = _PKG_ROOT / "resources" / "templates"

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
    """Every non-cache file under both packaged resource trees (for the sentinel sweep)."""
    found: list[Path] = []
    for root in (PROJECT_DIR, TEMPLATES_DIR):
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
