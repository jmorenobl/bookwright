"""SC-001 / FR-022 / F5 — no stub sentinel survives in any authored or stamped file.

Sweeps both packaged resource trees and a freshly-stamped temp project, asserting
none of the iteration-scaffolding markers remain.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import SENTINELS, resource_text_files


def _decode(path: Path) -> str:
    # Decode leniently: a stray binary byte must not crash the sweep, and a
    # sentinel is always plain ASCII/UTF-8 text anyway.
    return path.read_bytes().decode("utf-8", errors="ignore")


@pytest.mark.parametrize("path", resource_text_files(), ids=lambda p: p.name)
def test_packaged_resources_have_no_sentinel(path: Path) -> None:
    text = _decode(path)
    for sentinel in SENTINELS:
        assert sentinel not in text, f"{path} still contains sentinel {sentinel!r}"


def test_stamped_project_has_no_sentinel(stamped_project: Path) -> None:
    offenders: list[str] = []
    for path in sorted(stamped_project.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        text = _decode(path)
        for sentinel in SENTINELS:
            if sentinel in text:
                offenders.append(f"{path.relative_to(stamped_project)}: {sentinel!r}")
    assert not offenders, f"sentinels survived into a stamped project: {offenders}"
