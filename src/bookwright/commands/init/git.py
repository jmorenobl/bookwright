"""Thin git subprocess wrapper for ``bookwright init`` (research §R8).

Three helpers: ``git_available()`` (PATH probe), ``is_inside_existing_repo()``
(walks parents for ``.git/``), and ``init_and_commit(...)`` (runs ``git
init`` + ``git add .`` + ``git commit -m <message>`` with author env vars
filled in, and registers the partial ``.git/`` directory with the backup
ledger so a failed commit rolls back cleanly).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scaffold import BackupLedger

_FALLBACK_EMAIL = "author@bookwright.local"


class GitInitError(Exception):
    """Raised when ``git init`` or ``git commit`` failed (FR-022)."""

    code = "git_error"

    def __init__(self, *, stderr: str) -> None:
        self.stderr = stderr
        super().__init__(stderr.strip() or "git command failed")


def git_available() -> bool:
    """``True`` when a ``git`` binary is on PATH."""

    return shutil.which("git") is not None


def is_inside_existing_repo(root: Path) -> bool:
    """``True`` when ``root`` or any ancestor contains a ``.git`` entry."""

    candidate = root.resolve()
    while True:
        if (candidate / ".git").exists():
            return True
        if candidate.parent == candidate:
            return False
        candidate = candidate.parent


def _augmented_env(author_name: str) -> dict[str, str]:
    """Build an env that forces an identity for the initial commit."""

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author_name
    env["GIT_COMMITTER_NAME"] = author_name
    env.setdefault("GIT_AUTHOR_EMAIL", _FALLBACK_EMAIL)
    env.setdefault("GIT_COMMITTER_EMAIL", _FALLBACK_EMAIL)
    return env


def init_and_commit(
    root: Path,
    message: str,
    author_name: str,
    ledger: BackupLedger,
) -> None:
    """Run ``git init`` + ``git add .`` + ``git commit`` inside ``root``.

    Registers ``<root>/.git`` with the ledger before ``git init`` so a
    commit failure unwinds the partial repository on rollback. Raises
    ``GitInitError`` on subprocess failure.
    """

    git_dir = root / ".git"
    if not git_dir.exists():
        ledger.record_new_directory(git_dir)

    env = _augmented_env(author_name)

    for argv in (
        ["git", "init"],
        ["git", "add", "."],
        ["git", "commit", "-m", message],
    ):
        completed = subprocess.run(
            argv,
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        if completed.returncode != 0:
            raise GitInitError(stderr=completed.stderr or completed.stdout)
