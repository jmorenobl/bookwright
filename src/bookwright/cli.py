"""Bookwright CLI entry point."""

import typer

from bookwright.commands import check, focus, graph, init, integration, status, validate, version

app = typer.Typer(
    name="bookwright",
    help="Bookwright — Spec-driven authoring toolkit.",
    no_args_is_help=True,
    add_completion=False,
)

app.command("version")(version.run)
app.command("check")(check.run)
app.command("init", context_settings=init.CONTEXT_SETTINGS)(init.run)
app.command("status")(status.run)
app.command("validate")(validate.run)
app.add_typer(graph.app, name="graph")
app.add_typer(integration.app, name="integration")
app.add_typer(focus.app, name="focus")
