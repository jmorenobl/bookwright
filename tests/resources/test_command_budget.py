"""FR-015 / SC-002 — every command body stays under the tier-2 token budget.

Measured with ``helpers.approx_tokens`` (tiktoken if importable, else the
deterministic ``ceil(len/4)`` char heuristic).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import approx_tokens, command_body, command_files

_BUDGET = 5000


@pytest.mark.parametrize("path", command_files(), ids=lambda p: p.name)
def test_body_within_token_budget(path: Path) -> None:
    tokens = approx_tokens(command_body(path))
    assert tokens < _BUDGET, f"{path.name}: body ~{tokens} tokens >= {_BUDGET}"
