"""JSON success/error envelopes for the ``graph`` sub-commands (Principle IX).

Single-line ``json.dumps(payload, separators=(",", ":")) + "\\n"`` to stdout,
mirroring the pattern in :mod:`bookwright.commands.version`. Human prose and
progress go to stderr via a ``Console(stderr=True)`` owned by each command.
"""

from __future__ import annotations

import json
import sys
from typing import Any


def emit_json(payload: dict[str, Any]) -> None:
    """Write exactly one JSON document to stdout (the only thing on stdout)."""
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")


def error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the contract error envelope (cli-graph.md)."""
    payload: dict[str, Any] = {"status": "error", "code": code, "message": message}
    if details:
        payload["details"] = details
    return payload


def emit_error(payload: dict[str, Any], json_output: bool) -> None:
    """Surface an error envelope: one JSON doc on stdout under ``--json``, else a
    single ``bookwright: error: <message>`` line on stderr (Principle IX)."""
    if json_output:
        emit_json(payload)
    else:
        sys.stderr.write(f"bookwright: error: {payload['message']}\n")
