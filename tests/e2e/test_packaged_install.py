"""Manual packaged-build smoke (D7, MAN-1) — opt-in, coverage-exempt (R3).

Deselected by default (`-m 'not manual'` in pyproject) because it shells out to
``uv build`` and is slow/network-adjacent. Run it explicitly with::

    uv run pytest -m manual

It guards the packaging regression the spec cares about (SC-007): the built wheel
must bundle ``bookwright/resources/`` — without the packaged templates/commands a
fresh ``bookwright init`` would fail at first use. The full pipx-install + quickstart
walkthrough (MAN-2/MAN-3) is documented in ``specs/011-release-prep/quickstart.md``
and run by a human against an external environment.
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.manual
def test_built_wheel_bundles_resources(tmp_path: Path) -> None:
    """`uv build` produces a wheel that contains the packaged ``resources/`` tree."""
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    wheels = list(tmp_path.glob("bookwright_cli-*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, got {wheels}"
    names = zipfile.ZipFile(wheels[0]).namelist()
    assert any(n.startswith("bookwright/resources/") for n in names), (
        "wheel does not bundle bookwright/resources/ — a fresh `init` would fail"
    )
    assert any(n.startswith("bookwright/resources/commands/") for n in names)
