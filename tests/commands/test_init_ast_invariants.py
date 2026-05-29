"""Contract §7.3 + §7.4 — AST invariants for ``commands/init*``.

`Manifest.dump` MUST be the only TOML writer (no `tomlkit.dump*/parse*/loads`
calls in init code); `bookwright.integrations.parse_options` MUST be the only
tokeniser (no `shlex.split` calls).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_INIT_DIR = Path(__file__).parent.parent.parent / "src" / "bookwright" / "commands"

_INIT_FILES = sorted(list(_INIT_DIR.glob("init.py")) + list(_INIT_DIR.glob("_init_*.py")))

_FORBIDDEN_TOMLKIT = {"dumps", "dump", "parse", "loads", "load"}


def _attr_chain(node: ast.AST) -> list[str]:
    parts: list[str] = []
    cursor: ast.AST | None = node
    while isinstance(cursor, ast.Attribute):
        parts.insert(0, cursor.attr)
        cursor = cursor.value
    if isinstance(cursor, ast.Name):
        parts.insert(0, cursor.id)
    return parts


@pytest.mark.parametrize("path", _INIT_FILES, ids=[p.name for p in _INIT_FILES])
def test_no_tomlkit_write_calls(path: Path) -> None:
    """FR-015 / contract §7.3 — `Manifest.dump` is the sole TOML writer."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    offending: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = _attr_chain(node.func)
        if not chain:
            continue
        if chain[0] == "tomlkit" and chain[-1] in _FORBIDDEN_TOMLKIT:
            offending.append((node.lineno, ".".join(chain)))
    assert not offending, f"{path}: forbidden tomlkit calls: {offending}"


@pytest.mark.parametrize("path", _INIT_FILES, ids=[p.name for p in _INIT_FILES])
def test_no_shlex_split_calls(path: Path) -> None:
    """FR-006 / contract §7.4 — `parse_options` is the sole tokeniser."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    offending: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = _attr_chain(node.func)
        if not chain:
            continue
        if chain[0] == "shlex" and chain[-1] == "split":
            offending.append((node.lineno, ".".join(chain)))
    assert not offending, f"{path}: forbidden shlex.split calls: {offending}"
