"""`bookwright init` — scaffold a new book project.

Owns flag parsing, deprecation handling, JSON envelope serialization, and
the top-level orchestration `validate → resolve → scaffold → setup
integration → git init+commit → emit`. Delegates the heavy lifting to
the `_init_*.py` private siblings.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

import typer
from rich.console import Console

from bookwright import integrations as _integrations
from bookwright.commands import _init_envelope, _init_git, _init_resolve, _init_scaffold
from bookwright.commands._init_envelope import ResolvedInvocation
from bookwright.commands._init_scaffold import (
    BackupCreationError,
    BackupLedger,
    TargetOutsideProjectRootError,
)
from bookwright.commands._init_validate import (
    InvalidProjectNameError,
    check_slug_not_reserved,
    validate_project_name,
)
from bookwright.core.manifest import Manifest

_COMMIT_MESSAGE = "Initial commit from bookwright init"

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
_GIT_MISSING_WARNING = (
    "bookwright: warning: git not found on PATH; project created without a repository"
)
_GIT_EXISTING_WARNING = "bookwright: warning: existing .git/ detected; skipped git init and commit"
_AUTHOR_FALLBACK_WARNING = (
    "bookwright: warning: author could not be resolved from git config or $USER; "
    "using 'Unknown Author'"
)


def _stderr() -> Console:
    return Console(stderr=True, highlight=False, soft_wrap=True)


def _emit_error(  # noqa: PLR0913 — structured-error envelope demands all six fields
    *,
    code: str,
    message: str,
    details: dict[str, Any],
    exit_code: int,
    json_output: bool,
    rolled_back: bool,
) -> None:
    """Emit the error envelope (stdout JSON or stderr line) and exit."""

    if json_output:
        envelope = _init_envelope.error_envelope(
            code=code, message=message, details=details, rolled_back=rolled_back
        )
        _init_envelope.dump_error_to_stdout(envelope)
    else:
        sys.stderr.write(f"bookwright: error: {message}\n")
    raise typer.Exit(exit_code)


def _check_removed_flags(args: list[str], json_output: bool) -> None:
    """Inspect raw click args for ``--ai-skills`` / ``--ai-commands-dir`` (FR-004)."""

    for raw in args:
        bare = raw.partition("=")[0] if raw.startswith("--") else raw
        if bare in _REMOVED_FLAGS:
            _emit_error(
                code="removed_flag",
                message=_REMOVED_FLAGS[bare],
                details={"flag": bare, "modern": _REMOVED_FLAG_MODERN[bare]},
                exit_code=2,
                json_output=json_output,
                rolled_back=False,
            )


def _check_mutex(project_name: str | None, here: bool, *, json_output: bool) -> None:
    """FR-002 — exactly one of ``PROJECT_NAME`` / ``--here`` is required."""

    if project_name is not None and here:
        _emit_error(
            code="mutually_exclusive",
            message="PROJECT_NAME and --here are mutually exclusive",
            details={},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    if project_name is None and not here:
        _emit_error(
            code="mutually_exclusive",
            message="must specify PROJECT_NAME or --here",
            details={},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )


def _validate_named_name(value: str, json_output: bool) -> str:
    try:
        return validate_project_name(value)
    except InvalidProjectNameError as exc:
        _emit_error(
            code=exc.code,
            message=str(exc),
            details={"value": exc.value, "rule": exc.rule},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    raise AssertionError("unreachable")  # pragma: no cover — _emit_error raises


def _derive_named_slug(name: str, json_output: bool) -> str:
    try:
        return _init_resolve.derive_slug(name)
    except InvalidProjectNameError as exc:
        _emit_error(
            code=exc.code,
            message=str(exc),
            details={"value": exc.value, "rule": exc.rule},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    raise AssertionError("unreachable")  # pragma: no cover — _emit_error raises


def _validate_here_basename(basename: str, json_output: bool) -> str:
    """Reduced FR-021a check for ``--here``: empty / path-separator / reserved only."""

    if not basename.strip():
        _emit_error(
            code="invalid_project_name",
            message="current directory basename is empty",
            details={"value": basename, "rule": "empty"},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    if "/" in basename or "\\" in basename:
        _emit_error(
            code="invalid_project_name",
            message=f"current directory basename {basename!r} contains a path separator",
            details={"value": basename, "rule": "path_separator"},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    try:
        check_slug_not_reserved(basename)
    except InvalidProjectNameError as exc:
        _emit_error(
            code=exc.code,
            message=str(exc),
            details={"value": exc.value, "rule": exc.rule},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    return basename


def _resolve_authors_with_warning(
    project_root: Path,
    warnings: list[str],
    *,
    json_output: bool,
) -> list[str]:
    authors, fellback = _init_resolve.resolve_authors(project_root)
    if fellback:
        warnings.append(_AUTHOR_FALLBACK_WARNING)
        if not json_output:
            sys.stderr.write(_AUTHOR_FALLBACK_WARNING + "\n")
    return authors


def _resolve_integration(
    key: str,
    raw_options: str,
    *,
    json_output: bool,
) -> tuple[type[_integrations.SkillsIntegration], dict[str, str | bool]]:
    try:
        integration_cls = _integrations.get(key)
    except _integrations.UnknownIntegrationError as exc:
        details = {k: v for k, v in exc.to_dict().items() if k not in {"code", "message"}}
        _emit_error(
            code=exc.code,
            message=exc.message,
            details=details,
            exit_code=5,
            json_output=json_output,
            rolled_back=False,
        )
        raise AssertionError("unreachable") from None  # pragma: no cover

    try:
        parsed_options = _integrations.parse_options(raw_options, integration_cls)
    except (
        _integrations.UnknownOptionError,
        _integrations.MalformedOptionError,
        _integrations.InvalidOptionDeclarationError,
    ) as exc:
        details = {k: v for k, v in exc.to_dict().items() if k not in {"code", "message"}}
        _emit_error(
            code=exc.code,
            message=exc.message,
            details=details,
            exit_code=5,
            json_output=json_output,
            rolled_back=False,
        )
        raise AssertionError("unreachable") from None  # pragma: no cover

    return integration_cls, parsed_options


def _apply_named_conflict_matrix(
    target: Path,
    force: bool,
    *,
    json_output: bool,
) -> None:
    """FR-026 / FR-027 / FR-028 — refuse with structured codes when conflicting."""

    if (target / ".bookwright").exists():
        _emit_error(
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
        _emit_error(
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


def _apply_here_conflict_matrix(
    target: Path,
    force: bool,
    *,
    json_output: bool,
) -> None:
    """FR-028 / FR-029 / interactive prompt for ``--here``."""

    if (target / ".bookwright").exists():
        _emit_error(
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
        _emit_error(
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
        _emit_error(
            code="user_declined_overwrite",
            message="aborted by user",
            details={"target": str(target)},
            exit_code=4,
            json_output=json_output,
            rolled_back=False,
        )


def _ledger_or_panic(
    project_root: Path,
    cleanup_project_root: bool,
) -> BackupLedger:
    """Return a ledger; record the project root itself if we created it."""

    ledger = BackupLedger(project_root)
    if cleanup_project_root:
        ledger.record_new_directory(project_root)
    return ledger


def _emit_warnings_stderr(warnings: list[str]) -> None:
    for line in warnings:
        sys.stderr.write(line + "\n")


def _attach_integration_options_to_manifest(
    parsed_options: Mapping[str, str | bool],
) -> dict[str, Any]:
    """Convert ``parse_options`` output to a Manifest-friendly options dict."""

    return {k: v for k, v in parsed_options.items()}


def _run_scaffold(  # noqa: PLR0913 — orchestrator: gathers every previously-resolved input in one call
    *,
    resolved: ResolvedInvocation,
    integration_cls: type[_integrations.SkillsIntegration],
    parsed_options: dict[str, str | bool],
    ledger: BackupLedger,
    json_output: bool,
    warnings: list[str],
    no_git: bool,
    author_name: str,
    use_git: bool,
) -> ResolvedInvocation:
    """All filesystem mutations + integration setup + git step."""

    project_root = Path(resolved.project_root)

    template_context = {
        "title": resolved.title,
        "project_slug": resolved.project_slug,
        "author": resolved.authors[0],
        "language": resolved.language,
        "integration_key": resolved.integration_key,
    }

    # 1) Render the packaged template tree.
    _init_scaffold.render_resource_tree(project_root, template_context, ledger)

    # 2) Build and dump the manifest.
    manifest = Manifest.build(
        title=resolved.title,
        authors=list(resolved.authors),
        integration_key=resolved.integration_key,
        integration_skills_dir=resolved.integration_skills_dir,
        integration_options=_attach_integration_options_to_manifest(parsed_options),
        language=resolved.language,
        type="novel",
        status="idea",
        uri_base=f"https://example.org/{resolved.project_slug}/",
    )
    _init_scaffold.dump_manifest_tracked(manifest, project_root / "manifest.toml", ledger)

    # 3) Copy bundled vocabularies into .bookwright/vocabularies/.
    vocab_target = project_root / ".bookwright" / "vocabularies"
    _init_scaffold.mkdir_tracked(vocab_target, ledger)
    for vocab in ("propp.ttl", "greimas.ttl"):
        _init_scaffold.copy_resource_file(
            "bookwright.resources.vocabularies",
            vocab,
            vocab_target / vocab,
            ledger,
        )

    # 4) Wire the integration's setup() through the ledger.
    skills_target = project_root / integration_cls().resolve_skills_dir(parsed_options)
    _init_scaffold.mkdir_tracked(skills_target, ledger)
    marker = skills_target / _integrations.SKILL_PLACEHOLDER_MARKER_NAME
    if not marker.exists():
        ledger.record_new_file(marker)
    integration_cls().setup(project_root, manifest, parsed_options)

    # 5) Write the init-options record. The git_status is filled in below.
    if no_git:
        resolved = resolved.model_copy(update={"git_status": "skipped_by_flag"})
    elif not use_git:
        resolved = resolved.model_copy(update={"git_status": "skipped_no_binary"})
    elif _init_git.is_inside_existing_repo(project_root):
        resolved = resolved.model_copy(update={"git_status": "skipped_existing_repo"})
    else:
        resolved = resolved.model_copy(update={"git_status": "initialized"})

    record = _init_envelope.build_options_record(resolved)
    options_payload = _init_envelope.serialize_options_record(record)
    _init_scaffold.write_bytes_atomic(
        project_root / ".bookwright" / "init-options.json",
        options_payload,
        ledger,
    )

    # 6) Run git init + commit if applicable.
    if resolved.git_status == "initialized":
        try:
            _init_git.init_and_commit(project_root, _COMMIT_MESSAGE, author_name, ledger)
        except _init_git.GitInitError:
            raise
    elif resolved.git_status == "skipped_existing_repo":
        warnings.append(_GIT_EXISTING_WARNING)
        if not json_output:
            sys.stderr.write(_GIT_EXISTING_WARNING + "\n")
    elif resolved.git_status == "skipped_no_binary":
        warnings.append(_GIT_MISSING_WARNING)
        if not json_output:
            sys.stderr.write(_GIT_MISSING_WARNING + "\n")

    return resolved


def _exit_code_for_filesystem_failure(exc: BaseException) -> tuple[str, int, dict[str, Any]]:
    """Map a scaffold-time exception to (code, exit_code, details)."""

    if isinstance(exc, BackupCreationError):
        return (
            "backup_creation_error",
            6,
            {"target": str(exc.target), "reason": exc.reason},
        )
    if isinstance(exc, PermissionError):
        return (
            "permission_denied",
            6,
            {"path": str(getattr(exc, "filename", "") or ""), "errno": exc.errno or 0},
        )
    if isinstance(exc, _init_git.GitInitError):
        return (
            "git_error",
            7,
            {"stderr": exc.stderr},
        )
    if isinstance(exc, TargetOutsideProjectRootError):
        return (
            "filesystem_error",
            6,
            {"path": str(exc.target), "errno": 0},
        )
    if isinstance(exc, OSError):
        return (
            "filesystem_error",
            6,
            {"path": str(getattr(exc, "filename", "") or ""), "errno": exc.errno or 0},
        )
    return (
        "filesystem_error",
        6,
        {"path": "", "errno": 0},
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
    _check_mutex(project_name, here, json_output=json_output)

    # Reconcile --ai with --integration.
    deprecated_seen: list[str] = []
    integration_source = ctx.get_parameter_source("integration")
    integration_supplied = (
        integration_source is not None and integration_source.name == "COMMANDLINE"
    )
    if ai is not None:
        deprecated_seen.append("--ai")
        sys.stderr.write(_DEPRECATED_AI_WARNING + "\n")
        if not integration_supplied:
            integration = ai

    warnings: list[str] = []
    if deprecated_seen:
        warnings.append(_DEPRECATED_AI_WARNING)

    mode: Literal["named", "here"]
    if here:
        project_root = Path.cwd().resolve()
        basename = project_root.name
        _validate_here_basename(basename, json_output)
        title = basename
        project_slug = _derive_named_slug(basename, json_output)
        mode = "here"
        cleanup_project_root = False
    else:
        assert project_name is not None  # narrowed by mutex check
        title = _validate_named_name(project_name, json_output)
        project_slug = _derive_named_slug(title, json_output)
        project_root = (Path.cwd() / project_slug).resolve()
        mode = "named"
        cleanup_project_root = not project_root.exists()

    # Conflict matrix BEFORE author/integration resolution (which would touch git).
    if here:
        _apply_here_conflict_matrix(project_root, force, json_output=json_output)
    else:
        _apply_named_conflict_matrix(project_root, force, json_output=json_output)

    if not project_root.exists():
        try:
            project_root.mkdir(parents=True, exist_ok=False)
        except PermissionError as exc:
            _emit_error(
                code="permission_denied",
                message=f"could not create {project_root}: {exc}",
                details={"path": str(project_root), "errno": exc.errno or 0},
                exit_code=6,
                json_output=json_output,
                rolled_back=False,
            )
        except OSError as exc:
            _emit_error(
                code="filesystem_error",
                message=f"could not create {project_root}: {exc}",
                details={"path": str(project_root), "errno": exc.errno or 0},
                exit_code=6,
                json_output=json_output,
                rolled_back=False,
            )

    authors = _resolve_authors_with_warning(project_root, warnings, json_output=json_output)
    language = _init_resolve.resolve_language()
    integration_cls, parsed_options = _resolve_integration(
        integration, integration_options, json_output=json_output
    )
    skills_dir = integration_cls().resolve_skills_dir(parsed_options).as_posix()

    git_binary_available = _init_git.git_available()
    use_git = git_binary_available and not no_git
    if not no_git and not git_binary_available:
        warnings.append(_GIT_MISSING_WARNING)
        if not json_output:
            sys.stderr.write(_GIT_MISSING_WARNING + "\n")

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

    ledger = _ledger_or_panic(project_root, cleanup_project_root)

    try:
        resolved = _run_scaffold(
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
        code, exit_code, details = _exit_code_for_filesystem_failure(exc)
        _emit_error(
            code=code,
            message=str(exc) or code,
            details=details,
            exit_code=exit_code,
            json_output=json_output,
            rolled_back=True,
        )
        raise AssertionError("unreachable") from None  # pragma: no cover

    ledger.commit()

    if json_output:
        envelope = _init_envelope.success_envelope(resolved, warnings)
        _init_envelope.dump_success_to_stdout(envelope)
    else:
        console = _stderr()
        console.print(
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
