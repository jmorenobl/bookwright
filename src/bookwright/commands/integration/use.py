"""``bookwright integration use <key>`` — switch the project's agent integration.

Re-materializes one ``SKILL.md`` per source command under the chosen integration's
skills directory (reusing the shared materializer + the plugin registry —
Principles V/VI/VII), updates the manifest's ``[integration]`` block, and leaves
any previously-materialized skills directory **untouched** (the swap-residue
policy: no cleanup in v0). The operation is atomic — a materialization or lint
failure rolls the whole change back through a ``BackupLedger``.

This is the supported integration-swap mechanism. ``init`` deliberately refuses to
re-initialize an existing project (the ``.bookwright/`` guard), so switching the
*integration* of a live book is its own intention-revealing command rather than a
re-init flag. Principle IX: under ``--json`` exactly one JSON document on stdout;
all human prose goes to stderr.

Fault model: missing project / unparseable manifest / unknown integration key →
exit 2; a skill materialization or lint failure → exit 3 (fully rolled back).
"""

from __future__ import annotations

import json
import sys
from typing import Any

import typer
from rich.console import Console

from bookwright.core.errors import ManifestError
from bookwright.core.manifest import Manifest
from bookwright.integrations import UnknownIntegrationError, get
from bookwright.integrations.errors import SkillLintError, SkillMaterializationError
from bookwright.io.errors import ProjectNotFoundError
from bookwright.io.fs import BackupLedger
from bookwright.io.project import find_project_root

from . import app

EXIT_CONFIG = 2
EXIT_MATERIALIZE = 3


@app.command("use")
def run(
    key: str = typer.Argument(..., help="Integration key to switch to (e.g. 'claude', 'generic')."),
    json_output: bool = typer.Option(
        False, "--json", help="Emit the result as one JSON document on stdout."
    ),
) -> None:
    """Switch the project to integration ``key`` and re-materialize its skills."""
    try:
        payload = _use(key)
    except ProjectNotFoundError as exc:
        _emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except ManifestError as exc:
        _emit_error(_error("invalid_manifest", str(exc)), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except UnknownIntegrationError as exc:
        _emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_CONFIG) from exc
    except (SkillLintError, SkillMaterializationError) as exc:
        _emit_error(exc.to_json(), json_output)
        raise typer.Exit(EXIT_MATERIALIZE) from exc

    if json_output:
        _emit_json(payload)
    else:
        Console(stderr=True, highlight=False).print(
            f"bookwright: switched integration to '{payload['integration']}' "
            f"({payload['count']} skills → {payload['skills_dir']})"
        )


def _use(key: str) -> dict[str, Any]:
    """Materialize the new integration, update the manifest, and return the report.

    Resolves the integration *before* any filesystem mutation (an unknown key is a
    no-op exit-2). All writes — the skills and the manifest overwrite — go through a
    single ``BackupLedger`` so a failure leaves the project byte-identical.
    """
    root = find_project_root()
    manifest_path = root / "manifest.toml"
    manifest = Manifest.load(manifest_path)

    integration = get(key)()  # raises UnknownIntegrationError on an unknown key
    skills_dir = integration.resolve_skills_dir().as_posix()

    ledger = BackupLedger(root)
    try:
        integration.setup(root, manifest, ledger=ledger)
        ledger.record_overwrite(manifest_path)
        manifest.set_integration(key=key, skills_dir=skills_dir)
        manifest.dump(manifest_path, overwrite=True)
    except BaseException:
        ledger.rollback()
        raise
    ledger.commit()

    materialized = sorted(p.parent.name for p in (root / skills_dir).rglob("SKILL.md"))
    return {
        "status": "ok",
        "integration": key,
        "skills_dir": skills_dir,
        "materialized": materialized,
        "count": len(materialized),
    }


def _error(code: str, message: str) -> dict[str, Any]:
    """Build a Principle-IX error envelope."""
    return {"status": "error", "code": code, "message": message}


def _emit_json(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")


def _emit_error(payload: dict[str, Any], json_output: bool) -> None:
    if json_output:
        _emit_json(payload)
    else:
        message = payload.get("message", payload.get("code", "error"))
        sys.stderr.write(f"bookwright: error: {message}\n")
