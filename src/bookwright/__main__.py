"""Allow `python -m bookwright` to invoke the CLI."""

from bookwright.cli import app

if __name__ == "__main__":
    app()
