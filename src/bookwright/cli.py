"""Bookwright CLI entry point."""

import typer

from bookwright.commands import check, version

app = typer.Typer(
    name="bookwright",
    help="Bookwright — Spec-driven authoring toolkit.",
    no_args_is_help=True,
    add_completion=False,
)

app.command("version")(version.run)
app.command("check")(check.run)
