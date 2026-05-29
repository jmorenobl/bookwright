"""Shared fixtures for ``tests/commands/`` (iteration 4)."""

from __future__ import annotations

import hashlib
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture()
def scaffold_in_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Chdir into ``tmp_path`` for the test body, restore cwd after."""

    original = Path.cwd()
    monkeypatch.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(original)


@pytest.fixture()
def git_available() -> None:
    """Skip the test when ``git`` is not on PATH."""

    if shutil.which("git") is None:
        pytest.skip("git binary not on PATH")


@pytest.fixture()
def non_interactive_io(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force ``is_interactive()`` to return ``False`` for ``--here`` refusal tests."""

    monkeypatch.setattr(
        "bookwright.commands._init_resolve.is_interactive",
        lambda: False,
    )


@pytest.fixture()
def fake_git_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force ``git_available()`` to return ``False`` regardless of PATH."""

    monkeypatch.setattr(
        "bookwright.commands._init_git.git_available",
        lambda: False,
    )


def dirhash(path: Path) -> list[tuple[str, str]]:
    """Sorted ``(relative_posix, sha256)`` snapshot of every file under ``path``."""

    if not path.exists():
        return []
    entries: list[tuple[str, str]] = []
    for child in sorted(path.rglob("*")):
        if child.is_file() or child.is_symlink():
            rel = child.relative_to(path).as_posix()
            try:
                digest = hashlib.sha256(child.read_bytes()).hexdigest()
            except OSError:
                digest = "<unreadable>"
            entries.append((rel, digest))
    return entries
