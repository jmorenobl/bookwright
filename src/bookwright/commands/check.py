"""`bookwright check` — verify the running interpreter and runtime dependencies."""

import importlib
import json
import sys
from typing import TypedDict

import typer
from rich.console import Console

RUNTIME_MODULES: tuple[str, ...] = (
    "typer",
    "rich",
    "rdflib",
    "pydantic",
    "tomlkit",
    "jinja2",
    "slugify",
    "platformdirs",
    "uuid_utils",
    "yaml",
    "packaging",
)


class CheckResult(TypedDict, total=False):
    name: str
    status: str
    detail: str


def _python_version_check() -> CheckResult:
    found = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 11):  # noqa: UP036
        return {"name": "python_version", "status": "ok", "detail": found}
    return {
        "name": "python_version",
        "status": "fail",
        "detail": f"found {found}, requires >=3.11",
    }


def _dependency_check(module_name: str) -> CheckResult:
    try:
        importlib.import_module(module_name)
    except ImportError as exc:
        return {
            "name": f"dependency:{module_name}",
            "status": "fail",
            "detail": str(exc),
        }
    return {"name": f"dependency:{module_name}", "status": "ok"}


def run(
    json_output: bool = typer.Option(
        False, "--json", help="Emit a single JSON document on stdout."
    ),
) -> None:
    """Verify Python version (>=3.11) and that all declared deps are importable."""
    checks: list[CheckResult] = [_python_version_check()]
    for module_name in RUNTIME_MODULES:
        checks.append(_dependency_check(module_name))
    ok = all(c["status"] == "ok" for c in checks)
    payload = {"ok": ok, "checks": checks}
    if json_output:
        sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    else:
        console = Console()
        for check in checks:
            tag = "OK  " if check["status"] == "ok" else "FAIL"
            detail = check.get("detail", "")
            suffix = f" — {detail}" if detail else ""
            console.print(f"{tag}  {check['name']}{suffix}")
    raise typer.Exit(code=0 if ok else 1)
