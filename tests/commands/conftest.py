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
def outside_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A directory with no ``manifest.toml`` in it or any ancestor under tmp."""
    here = tmp_path / "nowhere"
    here.mkdir()
    monkeypatch.chdir(here)
    yield here


@pytest.fixture()
def git_available() -> None:
    """Skip the test when ``git`` is not on PATH."""

    if shutil.which("git") is None:
        pytest.skip("git binary not on PATH")


@pytest.fixture()
def non_interactive_io(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force ``is_interactive()`` to return ``False`` for ``--here`` refusal tests."""

    monkeypatch.setattr(
        "bookwright.commands.init.resolve.is_interactive",
        lambda: False,
    )


@pytest.fixture()
def fake_git_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force ``git_available()`` to return ``False`` regardless of PATH."""

    monkeypatch.setattr(
        "bookwright.commands.init.git.git_available",
        lambda: False,
    )


def dirhash(path: Path) -> list[tuple[str, str]]:
    """Sorted ``(relative_posix, sha256_or_dir_sentinel)`` snapshot under ``path``.

    Captures directories too (as a ``<DIR>`` sentinel) so the FR-030 / SC-005
    atomic-or-nothing assertions detect orphan directories left by a failed
    scaffold; files-only snapshots gave false negatives for `unknown_integration`
    and absolute `--skills-dir` regressions (round-4 audit).
    """

    if not path.exists():
        return []
    entries: list[tuple[str, str]] = []
    for child in sorted(path.rglob("*")):
        rel = child.relative_to(path).as_posix()
        if child.is_symlink() or child.is_file():
            try:
                digest = hashlib.sha256(child.read_bytes()).hexdigest()
            except OSError:
                digest = "<unreadable>"
            entries.append((rel, digest))
        elif child.is_dir():
            entries.append((rel, "<DIR>"))
    return entries
