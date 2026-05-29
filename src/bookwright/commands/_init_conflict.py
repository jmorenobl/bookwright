"""Pre-scaffold conflict checks and ledger seeding for ``bookwright init``.

Owns FR-026 / FR-027 / FR-028 / FR-029 — the name-collision matrices for
``named`` and ``here`` modes — plus the tiny ``BackupLedger`` seeder that
records the project root if ``init`` created it.
"""

from __future__ import annotations

from pathlib import Path

import typer

from bookwright.commands import _init_resolve
from bookwright.commands._init_envelope import emit_error
from bookwright.commands._init_scaffold import BackupLedger


def apply_named_conflict_matrix(
    target: Path,
    force: bool,
    *,
    json_output: bool,
) -> None:
    """FR-026 / FR-027 / FR-028 — refuse with structured codes when conflicting."""

    if (target / ".bookwright").exists():
        emit_error(
            code="already_initialized",
            message=(
                f"directory {str(target)!r} is already a Bookwright project (found .bookwright/)"
            ),
            details={"target": str(target)},
            exit_code=3,
            json_output=json_output,
            rolled_back=False,
        )
    if not target.exists():
        return
    if any(target.iterdir()) and not force:
        emit_error(
            code="target_not_empty",
            message=(
                f"directory {target.name!r} is not empty; "
                "use --force to overwrite or --here to initialise in place"
            ),
            details={"target": str(target)},
            exit_code=4,
            json_output=json_output,
            rolled_back=False,
        )


def apply_here_conflict_matrix(
    target: Path,
    force: bool,
    *,
    json_output: bool,
) -> None:
    """FR-028 / FR-029 / interactive prompt for ``--here``."""

    if (target / ".bookwright").exists():
        emit_error(
            code="already_initialized",
            message=(
                f"directory {str(target)!r} is already a Bookwright project (found .bookwright/)"
            ),
            details={"target": str(target)},
            exit_code=3,
            json_output=json_output,
            rolled_back=False,
        )
    if not any(target.iterdir()):
        return
    if force:
        return
    if not _init_resolve.is_interactive() or json_output:
        emit_error(
            code="non_interactive_here",
            message="--here in a non-empty directory requires --force in non-interactive runs",
            details={"target": str(target), "modern": "--force"},
            exit_code=4,
            json_output=json_output,
            rolled_back=False,
        )
    confirmed = typer.confirm(
        f"bookwright: directory {str(target)!r} is not empty. Overwrite name collisions?",
        default=False,
    )
    if not confirmed:
        emit_error(
            code="user_declined_overwrite",
            message="aborted by user",
            details={"target": str(target)},
            exit_code=4,
            json_output=json_output,
            rolled_back=False,
        )


def seed_backup_ledger(project_root: Path, cleanup_project_root: bool) -> BackupLedger:
    """Return a ledger; record the project root itself if we created it."""

    ledger = BackupLedger(project_root)
    if cleanup_project_root:
        ledger.record_new_directory(project_root)
    return ledger
