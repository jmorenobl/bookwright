"""`bookwright init` — scaffold a new book project.

Owns the Typer signature, the success-path orchestration, and the
top-level ``try/except/ledger.rollback()`` wrapper. Delegates validation,
resolution, conflict checks, scaffolding, envelope serialization, and the
git step to the ``_init_*.py`` private siblings.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal

import typer
from rich.console import Console

from bookwright.commands import (
    _init_conflict,
    _init_envelope,
    _init_git,
    _init_resolve,
    _init_scaffold,
    _init_validate,
)
from bookwright.commands._init_envelope import ResolvedInvocation

_REMOVED_FLAGS: dict[str, str] = {
    "--ai-skills": ("--ai-skills is no longer accepted; Agent Skills is now the only output mode"),
    "--ai-commands-dir": (
        "--ai-commands-dir is no longer accepted; "
        'for generic, use --integration-options="--skills-dir <path>"'
    ),
}

_REMOVED_FLAG_MODERN: dict[str, str] = {
    "--ai-skills": "(drop the flag; Agent Skills is the only output mode)",
    "--ai-commands-dir": '--integration-options="--skills-dir <path>"',
}

_DEPRECATED_AI_WARNING = "bookwright: warning: --ai is deprecated; use --integration instead"


def _check_removed_flags(args: list[str], json_output: bool) -> None:
    """Inspect raw click args for ``--ai-skills`` / ``--ai-commands-dir`` (FR-004)."""

    for raw in args:
        bare = raw.partition("=")[0] if raw.startswith("--") else raw
        if bare in _REMOVED_FLAGS:
            _init_envelope.emit_error(
                code="removed_flag",
                message=_REMOVED_FLAGS[bare],
                details={"flag": bare, "modern": _REMOVED_FLAG_MODERN[bare]},
                exit_code=2,
                json_output=json_output,
                rolled_back=False,
            )


def run(  # noqa: PLR0913, PLR0912, PLR0915 — single Typer entry point; surface is the CLI contract
    ctx: typer.Context,
    project_name: str | None = typer.Argument(
        None, metavar="[PROJECT_NAME]", help="New project directory name (mutex with --here)."
    ),
    here: bool = typer.Option(False, "--here", help="Initialise in the current directory."),
    force: bool = typer.Option(
        False, "--force", help="Overwrite name collisions under the project root."
    ),
    no_git: bool = typer.Option(False, "--no-git", help="Skip the automatic git init + commit."),
    integration: str = typer.Option(
        "claude",
        "--integration",
        help="Agent integration key (default: claude).",
    ),
    integration_options: str = typer.Option(
        "",
        "--integration-options",
        help=(
            "Quoted POSIX-tokenised options forwarded to the integration "
            '(e.g., "--skills-dir .cursor/skills").'
        ),
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a single JSON document on stdout."
    ),
    ai: str | None = typer.Option(
        None,
        "--ai",
        hidden=True,
        help="Deprecated alias for --integration.",
    ),
) -> None:
    """Scaffold a new Bookwright project."""

    raw_args = list(ctx.args) if ctx.args else []
    _check_removed_flags(raw_args, json_output=json_output)
    _init_validate.check_mutex(project_name, here, json_output=json_output)

    # Reconcile --ai with --integration.
    deprecated_seen: list[str] = []
    warnings: list[str] = []
    integration_source = ctx.get_parameter_source("integration")
    integration_supplied = (
        integration_source is not None and integration_source.name == "COMMANDLINE"
    )
    if ai is not None:
        deprecated_seen.append("--ai")
        sys.stderr.write(_DEPRECATED_AI_WARNING + "\n")
        warnings.append(_DEPRECATED_AI_WARNING)
        if not integration_supplied:
            integration = ai

    mode: Literal["named", "here"]
    if here:
        project_root = Path.cwd().resolve()
        basename = project_root.name
        _init_validate.parse_here_basename(basename, json_output)
        title = basename
        project_slug = _init_resolve.parse_named_slug(basename, json_output)
        mode = "here"
        cleanup_project_root = False
    else:
        assert project_name is not None  # narrowed by mutex check
        title = _init_validate.parse_named_name(project_name, json_output)
        project_slug = _init_resolve.parse_named_slug(title, json_output)
        project_root = (Path.cwd() / project_slug).resolve()
        mode = "named"
        cleanup_project_root = not project_root.exists()

    # Conflict matrix BEFORE author/integration resolution (which would touch git).
    if here:
        _init_conflict.apply_here_conflict_matrix(project_root, force, json_output=json_output)
    else:
        _init_conflict.apply_named_conflict_matrix(project_root, force, json_output=json_output)

    if not project_root.exists():
        try:
            project_root.mkdir(parents=True, exist_ok=False)
        except PermissionError as exc:
            _init_envelope.emit_error(
                code="permission_denied",
                message=f"could not create {project_root}: {exc}",
                details={"path": str(project_root), "errno": exc.errno or 0},
                exit_code=6,
                json_output=json_output,
                rolled_back=False,
            )
        except OSError as exc:
            _init_envelope.emit_error(
                code="filesystem_error",
                message=f"could not create {project_root}: {exc}",
                details={"path": str(project_root), "errno": exc.errno or 0},
                exit_code=6,
                json_output=json_output,
                rolled_back=False,
            )

    authors = _init_resolve.resolve_authors_or_warn(project_root, warnings, json_output=json_output)
    language = _init_resolve.resolve_language()
    integration_cls, parsed_options = _init_resolve.resolve_integration(
        integration, integration_options, json_output=json_output
    )
    skills_dir = integration_cls().resolve_skills_dir(parsed_options).as_posix()

    use_git = _init_git.git_available() and not no_git

    resolved = ResolvedInvocation(
        mode=mode,
        project_name=title if mode == "named" else None,
        project_slug=project_slug,
        project_root=project_root.as_posix(),
        title=title,
        authors=list(authors),
        language=language,
        integration_key=integration,
        integration_skills_dir=skills_dir,
        integration_options=dict(parsed_options),
        no_git=no_git,
        force=force,
        json_output=json_output,
        deprecated_flags_seen=list(deprecated_seen),
    )

    ledger = _init_conflict.seed_backup_ledger(project_root, cleanup_project_root)

    try:
        resolved = _init_scaffold.run_scaffold_steps(
            resolved=resolved,
            integration_cls=integration_cls,
            parsed_options=parsed_options,
            ledger=ledger,
            json_output=json_output,
            warnings=warnings,
            no_git=no_git,
            author_name=authors[0],
            use_git=use_git,
        )
    except BaseException as exc:
        ledger.rollback()
        if cleanup_project_root and project_root.exists():
            import shutil  # noqa: PLC0415 — local cleanup only

            shutil.rmtree(project_root, ignore_errors=True)
        if isinstance(exc, typer.Exit):
            raise
        code, exit_code, details = _init_envelope.classify_filesystem_failure(exc)
        _init_envelope.emit_error(
            code=code,
            message=str(exc) or code,
            details=details,
            exit_code=exit_code,
            json_output=json_output,
            rolled_back=True,
        )

    ledger.commit()

    if json_output:
        envelope = _init_envelope.success_envelope(resolved, warnings)
        _init_envelope.dump_success_to_stdout(envelope)
    else:
        Console(stderr=True, highlight=False, soft_wrap=True).print(
            f"bookwright: created [bold]{project_root}[/bold] "
            f"(integration={resolved.integration_key}, "
            f"git={resolved.git_status})"
        )

    raise typer.Exit(0)


CONTEXT_SETTINGS: dict[str, Any] = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
}
"""Click context settings expected by ``cli.py`` when wiring the command."""
