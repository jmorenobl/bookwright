"""`bookwright version` — report the package and GOLEM schema versions."""

import typer
from rich.console import Console

from bookwright import __version__
from bookwright.resources.schemas import load_schema_version

from ._envelope import emit_json


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
        emit_json(payload)
        return
    console = Console()
    console.print(f"bookwright {payload['package_version']}")
    console.print(f"GOLEM schema: {payload['golem_schema_version']}")
