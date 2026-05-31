"""`bookwright version` — report the package and GOLEM schema versions."""

import json
import sys

import typer
from rich.console import Console

from bookwright import __version__
from bookwright.resources.schemas import load_schema_version


def _read_golem_schema_version() -> str:
    try:
        return load_schema_version()
    except FileNotFoundError:
        return "unknown"


def run(
    json_output: bool = typer.Option(
        False, "--json", help="Emit a single JSON document on stdout."
    ),
) -> None:
    """Print the bookwright package version and the bundled GOLEM schema version."""
    payload = {
        "package_version": __version__,
        "golem_schema_version": _read_golem_schema_version(),
    }
    if json_output:
        sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
        return
    console = Console()
    console.print(f"bookwright {payload['package_version']}")
    console.print(f"GOLEM schema: {payload['golem_schema_version']}")
