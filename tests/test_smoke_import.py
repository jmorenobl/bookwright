"""Smoke test: the bookwright package imports and exposes a sane __version__."""

import re

import bookwright

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def test_version_is_semver() -> None:
    assert isinstance(bookwright.__version__, str)
    assert bookwright.__version__, "bookwright.__version__ must be non-empty"
    assert SEMVER_RE.match(bookwright.__version__), (
        f"bookwright.__version__ ({bookwright.__version__!r}) is not semver-like"
    )
