"""Shared command-layer envelope helper (review R1).

Several agent-facing commands catch a ``ManifestError`` at their ``--json``
boundary and remap it to the contract's single ``invalid_manifest`` code. Rather
than re-build the ``{status,code,message}`` skeleton by hand in each command
module, the remap routes through the base ``BookwrightError.to_json`` — the one
place the envelope skeleton lives — exactly as ``commands.validate._UsageError``
already does for the same case.
"""

from __future__ import annotations

from typing import Any

from bookwright.errors import BookwrightError


class _InvalidManifestError(BookwrightError):
    """A caught ``ManifestError`` re-coded to the contract's ``invalid_manifest``.

    Mirrors ``commands.validate._UsageError("invalid_manifest", ...)``: the remap
    is expressed as a ``BookwrightError`` whose canonical ``to_json()`` builds the
    envelope, never a hand-rolled dict.
    """

    code = "invalid_manifest"


def invalid_manifest_payload(exc: Exception) -> dict[str, Any]:
    """The ``invalid_manifest`` error envelope for a caught ``ManifestError``."""
    return _InvalidManifestError(str(exc)).to_json()
