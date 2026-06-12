"""Shared command-layer envelope helpers.

Several agent-facing commands catch a ``ManifestError`` at their ``--json``
boundary and remap it to the contract's single ``invalid_manifest`` code. Rather
than re-build the ``{status,code,message}`` skeleton by hand in each command
module, the remap routes through the base ``BookwrightError.to_json`` — the one
place the envelope skeleton lives — exactly as ``commands.validate._UsageError``
already does for the same case.

The :func:`emit_json` / :func:`emit_error` pair is single-sourced here too: a
single-line ``json.dumps(payload, separators=(",", ":")) + "\\n"`` to stdout,
with human prose / progress going to stderr via a ``Console(stderr=True)`` owned
by each command. Every ``--json`` command (``check``, ``focus``, ``graph``,
``init``, ``integration``, ``validate``, ``version``) routes its stdout encoding
through :func:`emit_json` instead of hand-rolling a per-group copy.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from bookwright.errors import BookwrightError

#: The CLI-wide "configuration fault" exit status (missing project, unparseable
#: manifest, unknown engine/integration, bad scope, …). Single-sourced here so
#: the command groups cannot drift to different statuses for the same fault class.
EXIT_CONFIG = 2


def ok_payload(**fields: Any) -> dict[str, Any]:
    """The success-envelope skeleton: ``{"status": "ok", **fields}`` (Principle IX).

    The success-side complement of ``BookwrightError.to_json()`` — the one place
    the ``"status": "ok"`` literal lives for new success documents (020 research
    D6). Existing ``check``/``focus``/``graph`` call sites keep their hand-built
    dicts for now; migrating them is out of 020's scope.
    """
    return {"status": "ok", **fields}


def emit_json(payload: dict[str, Any]) -> None:
    """Write exactly one JSON document to stdout (the only thing on stdout)."""
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")


def emit_error(payload: dict[str, Any], json_output: bool) -> None:
    """Surface an error envelope: one JSON doc on stdout under ``--json``, else a
    single ``bookwright: error: <message>`` line on stderr (Principle IX)."""
    if json_output:
        emit_json(payload)
    else:
        sys.stderr.write(f"bookwright: error: {payload['message']}\n")


#: The contract code every caught ``ManifestError`` collapses to at a ``--json``
#: boundary. Single-sourced here so the two remap sites — this module and
#: ``commands.validate._UsageError`` — cannot drift to different literals.
INVALID_MANIFEST_CODE = "invalid_manifest"


class _InvalidManifestError(BookwrightError):
    """A caught ``ManifestError`` re-coded to the contract's ``invalid_manifest``.

    Mirrors ``commands.validate._UsageError(INVALID_MANIFEST_CODE, ...)``: the
    remap is expressed as a ``BookwrightError`` whose canonical ``to_json()``
    builds the envelope, never a hand-rolled dict.
    """

    code = INVALID_MANIFEST_CODE


def invalid_manifest_payload(exc: Exception) -> dict[str, Any]:
    """The ``invalid_manifest`` error envelope for a caught ``ManifestError``."""
    return _InvalidManifestError(str(exc)).to_json()
