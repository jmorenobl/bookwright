"""Unit tests for :func:`find_project_root` (R8)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.io.errors import ProjectNotFoundError
from bookwright.io.project import find_project_root


def test_found_from_nested_cwd(tmp_path: Path) -> None:
    (tmp_path / "manifest.toml").write_text("", encoding="utf-8")
    nested = tmp_path / "bible" / "characters"
    nested.mkdir(parents=True)
    assert find_project_root(nested) == tmp_path.resolve()


def test_found_at_root_itself(tmp_path: Path) -> None:
    (tmp_path / "manifest.toml").write_text("", encoding="utf-8")
    assert find_project_root(tmp_path) == tmp_path.resolve()


def test_not_a_project_raises(tmp_path: Path) -> None:
    with pytest.raises(ProjectNotFoundError):
        find_project_root(tmp_path)
