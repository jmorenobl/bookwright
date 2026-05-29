"""FR-037 / SC-009 — no stdout/stderr writes from the integrations layer.

AST-walks every ``.py`` under ``src/bookwright/integrations/`` and rejects:
    - bare ``print(...)`` calls,
    - attribute access of ``sys.stdout`` or ``sys.stderr``,
    - ``from sys import stdout`` / ``from sys import stderr`` imports.

A static check catches dormant call paths (FR-037 is a class-level
invariant, not a happy-path one).
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_INTEGRATIONS_ROOT = (
    pathlib.Path(__file__).resolve().parents[2] / "src" / "bookwright" / "integrations"
)


def _iter_python_sources() -> list[pathlib.Path]:
    return [path for path in _INTEGRATIONS_ROOT.rglob("*.py") if "__pycache__" not in path.parts]


def _is_stdio_attribute(node: ast.Attribute) -> bool:
    if node.attr not in {"stdout", "stderr"}:
        return False
    value = node.value
    return isinstance(value, ast.Name) and value.id == "sys"


def test_no_print_no_sys_stdio() -> None:
    offenders: list[str] = []
    for path in _iter_python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            # `print(...)` calls
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                offenders.append(f"{path}:{node.lineno} — print() call")
                continue
            # `sys.stdout` / `sys.stderr` attribute access
            if isinstance(node, ast.Attribute) and _is_stdio_attribute(node):
                offenders.append(f"{path}:{node.lineno} — sys.{node.attr} access")
                continue
            # `from sys import stdout/stderr`
            if isinstance(node, ast.ImportFrom) and node.module == "sys":
                for alias in node.names:
                    if alias.name in {"stdout", "stderr"}:
                        offenders.append(f"{path}:{node.lineno} — from sys import {alias.name}")

    if offenders:
        pytest.fail(
            "FR-037 violation: the integrations layer MUST NOT write to "
            "stdout/stderr. Offending sites:\n  " + "\n  ".join(offenders)
        )
