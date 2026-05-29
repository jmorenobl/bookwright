"""Agent Skills compliance constants (FR-033, FR-034, SC-010)."""

from __future__ import annotations

import ast
import pathlib

import pytest

from bookwright.integrations import (
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
    SKILL_PLACEHOLDER_MARKER_NAME,
)


def test_skill_name_max_length() -> None:
    assert SKILL_NAME_MAX_LENGTH == 64


def test_skill_description_max_length() -> None:
    assert SKILL_DESCRIPTION_MAX_LENGTH == 1024


def test_skill_placeholder_marker_name() -> None:
    assert SKILL_PLACEHOLDER_MARKER_NAME == ".bookwright-skills-placeholder"


# ---------- single-source-of-truth pin ----------


_SRC_ROOT = pathlib.Path(__file__).resolve().parents[2] / "src" / "bookwright"
_CONSTANTS_FILE = _SRC_ROOT / "integrations" / "constants.py"


def _iter_python_sources_outside_constants() -> list[pathlib.Path]:
    return [
        path
        for path in _SRC_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts and path != _CONSTANTS_FILE
    ]


@pytest.mark.parametrize(
    "name,expected_value",
    [
        ("SKILL_NAME_MAX_LENGTH", 64),
        ("SKILL_DESCRIPTION_MAX_LENGTH", 1024),
    ],
)
def test_constant_is_not_redeclared_elsewhere(name: str, expected_value: int) -> None:
    """No other module re-declares the same SKILL_*_MAX_LENGTH literal."""

    offenders: list[str] = []
    for path in _iter_python_sources_outside_constants():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        offenders.append(f"{path}:{node.lineno}")
            elif isinstance(node, ast.AnnAssign):
                target = node.target
                if isinstance(target, ast.Name) and target.id == name:
                    offenders.append(f"{path}:{node.lineno}")

    assert not offenders, (
        f"{name} (={expected_value}) is re-declared outside constants.py at: "
        f"{offenders}. Constants live in one place — import them."
    )
