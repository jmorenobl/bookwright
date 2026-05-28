"""Allow `python -m bookwright` to invoke the CLI."""

from bookwright.cli import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
