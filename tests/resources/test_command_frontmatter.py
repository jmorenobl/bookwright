"""FR-001..FR-006 / FR-031 — the 12 command sources' frontmatter contract.

Asserts the inventory (exactly the 11 expected names), that each frontmatter
parses through the shipped ``parse_frontmatter``, the ``name``/``description``
rules, the forbidden keys (``scripts``/``handoffs``), and the out-of-scope guard
(``commands/`` ships only ``.md`` — no ``SKILL.md``, no helper ``.py``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import COMMANDS_DIR, EXPECTED_COMMANDS, command_files, command_metadata


def test_exactly_the_expected_commands_exist() -> None:
    # FR-001: no extras, no missing.
    found = {p.stem for p in command_files()}
    assert found == set(EXPECTED_COMMANDS), (
        f"missing={set(EXPECTED_COMMANDS) - found}, extra={found - set(EXPECTED_COMMANDS)}"
    )


@pytest.mark.parametrize("path", command_files(), ids=lambda p: p.name)
def test_frontmatter_contract(path: Path) -> None:
    meta = command_metadata(path)  # FR-003: parses, no raise.

    name = meta.get("name")
    assert isinstance(name, str) and name, f"{path.name}: missing/empty name"
    assert name == path.stem, f"{path.name}: name {name!r} != basename {path.stem!r}"  # FR-002
    assert len(name) < 64, f"{path.name}: name >= 64 chars"  # Constitution VII

    description = meta.get("description")
    assert isinstance(description, str) and description.strip(), (
        f"{path.name}: missing/empty description"
    )
    assert len(description) < 1024, f"{path.name}: description >= 1024 chars"  # FR-004

    assert "scripts" not in meta, f"{path.name}: forbidden 'scripts' key"  # FR-005
    assert "handoffs" not in meta, f"{path.name}: forbidden 'handoffs' key"  # FR-006


def test_commands_tree_ships_only_markdown() -> None:
    # FR-031 / SC-007: no SKILL.md, no helper .py anywhere under commands/.
    offenders = [
        p.relative_to(COMMANDS_DIR).as_posix()
        for p in COMMANDS_DIR.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".md"
    ]
    assert offenders == [], f"non-.md artifacts under commands/: {offenders}"
    assert not list(COMMANDS_DIR.rglob("SKILL.md")), "a SKILL.md leaked into commands/"
