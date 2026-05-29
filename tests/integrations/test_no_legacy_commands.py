"""FR-032 (Constitution Principle VI, NON-NEGOTIABLE) — no legacy commands path.

AST-walks every ``.py`` under ``src/bookwright/integrations/`` and rejects:
    (a) any ``ClassDef`` whose name ends in ``MarkdownIntegration`` or whose
        bases include a name other than ``SkillsIntegration`` / ``object``,
    (b) any string literal matching the pattern ``*commands/*`` (catches
        ``.claude/commands/``, ``.agents/commands/``, etc.) outside of
        comments / docstrings,
    (c) any path-building call (``Path(...)``, ``os.path.join(...)``) whose
        joined segments include ``"commands"``.

Constitution Principle VI is NON-NEGOTIABLE; this guard fails loudly the
moment any iteration tries to introduce a legacy commands path.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_INTEGRATIONS_ROOT = (
    pathlib.Path(__file__).resolve().parents[2] / "src" / "bookwright" / "integrations"
)

_ALLOWED_BASES: frozenset[str] = frozenset({"SkillsIntegration", "object"})


def _iter_python_sources() -> list[pathlib.Path]:
    return [path for path in _INTEGRATIONS_ROOT.rglob("*.py") if "__pycache__" not in path.parts]


def _is_docstring(node: ast.AST, parent_body: list[ast.stmt] | None) -> bool:
    """Return True if `node` is the first-statement docstring of its parent."""

    if parent_body is None:
        return False
    if not parent_body:
        return False
    first = parent_body[0]
    if not isinstance(first, ast.Expr):
        return False
    if first is not node:
        return False
    value = first.value
    return isinstance(value, ast.Constant) and isinstance(value.value, str)


def _collect_docstring_node_ids(tree: ast.Module) -> set[int]:
    """Collect the id() of every docstring expression node in the module."""

    docstring_ids: set[int] = set()
    for parent in ast.walk(tree):
        body = getattr(parent, "body", None)
        if isinstance(body, list) and body:
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                docstring_ids.add(id(first.value))
    return docstring_ids


def _base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def test_no_legacy_markdown_integration_classes() -> None:
    """(a) reject ``*MarkdownIntegration`` class names + non-SkillsIntegration bases."""

    offenders: list[str] = []
    for path in _iter_python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name.endswith("MarkdownIntegration"):
                offenders.append(f"{path}:{node.lineno} — class {node.name!r} (FR-032)")
                continue
            # Base-class check applies only to integration classes (those
            # whose name ends in `Integration`). Internal helper classes
            # (errors, options descriptors) are out of scope.
            if not node.name.endswith("Integration"):
                continue
            for base in node.bases:
                name = _base_name(base)
                if name and name not in _ALLOWED_BASES:
                    offenders.append(
                        f"{path}:{node.lineno} — class {node.name} inherits from {name!r} "
                        f"(only SkillsIntegration / object allowed)"
                    )
    if offenders:
        pytest.fail(
            "FR-032 violation: legacy command-style integration detected:\n  "
            + "\n  ".join(offenders)
        )


def test_no_commands_path_literals() -> None:
    """(b) reject any non-docstring string literal containing ``commands/``."""

    offenders: list[str] = []
    for path in _iter_python_sources():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        docstring_ids = _collect_docstring_node_ids(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            if not isinstance(node.value, str):
                continue
            if id(node) in docstring_ids:
                continue
            if "commands/" in node.value or "/commands" in node.value:
                offenders.append(f"{path}:{node.lineno} — literal {node.value!r} (FR-032)")
    if offenders:
        pytest.fail(
            "FR-032 violation: a legacy `commands/` path literal was found "
            "in the integrations layer:\n  " + "\n  ".join(offenders)
        )


def test_no_commands_path_joining() -> None:
    """(c) reject ``Path(...)`` / ``os.path.join(...)`` with a ``commands`` segment."""

    offenders: list[str] = []
    for path in _iter_python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            func_name = ""
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                # os.path.join — match on the attribute name.
                func_name = func.attr
            if func_name not in {"Path", "join"}:
                continue
            for arg in node.args:
                if (
                    isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)
                    and arg.value == "commands"
                ):
                    offenders.append(
                        f"{path}:{node.lineno} — {func_name}() joins 'commands' segment"
                    )
    if offenders:
        pytest.fail(
            "FR-032 violation: a path-building call joins a 'commands' "
            "segment:\n  " + "\n  ".join(offenders)
        )
