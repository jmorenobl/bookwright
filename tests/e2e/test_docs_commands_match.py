"""D4 / FR-015 / VR-11 — the docs ``commands/`` set must equal the live CLI.

Introspects ``bookwright.cli:app`` for its registered **leaf** command paths
(descending into the ``graph`` / ``integration`` sub-``Typer`` groups so the
inventory holds ``graph build`` / ``integration use``, not the bare groups) and
asserts:

* **(a)** the documented command set under ``docs/commands/`` equals that leaf set
  — neither a missing nor an extra command;
* **(b)** every option each leaf command exposes (introspected from its params,
  excluding the auto-generated ``--help`` and hidden/deprecated flags) appears on
  that command's documentation page.

Neither the command list nor the flag list is hard-coded — both are derived from
the live Typer command objects, so a new command or a renamed flag fails CI rather
than silently shipping undocumented (closing the FR-015 drift gap, DOC-2).
"""

from __future__ import annotations

from pathlib import Path

from typer.main import get_command

from bookwright.cli import app

COMMANDS_DIR = Path(__file__).resolve().parents[2] / "docs" / "commands"
_BOOKWRIGHT = "bookwright "


def _leaf_commands() -> dict[str, list[str]]:
    """Map every CLI leaf-command path → its documented option names (sorted)."""
    root = get_command(app)
    leaves: dict[str, list[str]] = {}

    def walk(command: object, prefix: str) -> None:
        for name, sub in getattr(command, "commands", {}).items():
            path = f"{prefix}{name}".strip()
            if getattr(sub, "commands", None):
                walk(sub, f"{path} ")
                continue
            opts = sorted(
                {
                    opt
                    for param in sub.params
                    for opt in getattr(param, "opts", [])
                    if opt.startswith("--")
                    and not getattr(param, "hidden", False)
                    and getattr(param, "name", None) != "help"
                }
            )
            leaves[path] = opts

    walk(root, "")
    return leaves


def _documented_commands() -> dict[str, str]:
    """Map each documented command (from a page's H1 ``# `bookwright <cmd>` ``) → text."""
    docs: dict[str, str] = {}
    for path in sorted(COMMANDS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        command: str | None = None
        for line in text.splitlines():
            if line.startswith("# "):
                heading = line[2:].strip().strip("`").strip()
                if heading.startswith(_BOOKWRIGHT):
                    command = heading[len(_BOOKWRIGHT) :].strip()
                break  # only the H1 identifies the page's command
        assert command is not None, f"{path.name}: H1 must be '# `bookwright <cmd>`'"
        docs[command] = text
    return docs


def test_documented_command_set_equals_cli() -> None:
    """No documented command is missing and none is extra (VR-11)."""
    assert set(_documented_commands()) == set(_leaf_commands())


def test_each_command_documents_its_flags() -> None:
    """Every CLI flag a command exposes appears on its documentation page (FR-015)."""
    docs = _documented_commands()
    for path, options in _leaf_commands().items():
        text = docs[path]
        missing = [opt for opt in options if opt not in text]
        assert not missing, f"{path}: undocumented flags {missing}"
