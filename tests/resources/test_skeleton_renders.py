"""FR-010 / W5 — every ``.j2`` skeleton renders cleanly under the real walker.

Invokes the iter-4 ``render_resource_tree`` into a temp dir with a representative
5-key W2 context and asserts it raises no Jinja ``UndefinedError`` (i.e. no
``.j2`` references a variable outside ``{title, project_slug, author, language,
integration_key}``), and that no rendered output leaks an unresolved ``{{`` tag.
"""

from __future__ import annotations

from pathlib import Path

from bookwright.commands.init.scaffold import BackupLedger, render_resource_tree

from .helpers import PROJECT_DIR

_W2_CONTEXT: dict[str, str] = {
    "title": "Qt Book",
    "project_slug": "qt-book",
    "author": "A. Author",
    "language": "es",
    "integration_key": "generic",
}


def test_render_resource_tree_strict_undefined_clean(tmp_path: Path) -> None:
    ledger = BackupLedger(tmp_path)
    # Raises UndefinedError if any `.j2` references a non-W2 variable.
    render_resource_tree(tmp_path, _W2_CONTEXT, ledger)

    # The two `.j2` files land with their suffix stripped and no residual tag.
    for rendered in (tmp_path / "README.md", tmp_path / "bible" / "constitution.md"):
        assert rendered.is_file(), f"expected rendered {rendered}"
        body = rendered.read_text(encoding="utf-8")
        assert "{{" not in body and "}}" not in body, f"unrendered Jinja tag in {rendered}"


def test_every_project_j2_is_covered() -> None:
    # Guard: if a future `.j2` is added under project/, this suite must render it.
    j2_files = sorted(p.name for p in PROJECT_DIR.rglob("*.j2") if p.is_file())
    assert "README.md.j2" in j2_files
    assert "constitution.md.j2" in j2_files
