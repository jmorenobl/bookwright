"""US4 - Acceptance Scenarios 2-4 + round-trip (FR-018, FR-019, FR-020, FR-021, SC-005)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from bookwright.core import Manifest, ManifestOverwriteError

from .conftest import load_fixture


def test_dump_writes_human_readable_with_comments(tmp_path: Path) -> None:
    """FR-018: built manifests are human-readable; template comments survive."""

    m = Manifest.build(
        title="Readable",
        authors=["Alice"],
        integration_key="claude",
        uri_base="https://example.org/r/",
    )
    target = tmp_path / "manifest.toml"
    result = m.dump(target)
    assert result == target.resolve()

    body = target.read_text(encoding="utf-8")
    # Comments from the template are preserved.
    assert "# Bookwright project manifest." in body
    assert "[bookwright]" in body
    assert "[book]" in body
    # Section order is preserved (bookwright before book before integration).
    assert body.index("[bookwright]") < body.index("[book]") < body.index("[integration]")


def test_refuse_overwrite_by_default(tmp_path: Path) -> None:
    """FR-019 + AS2: a second dump to the same path raises `ManifestOverwriteError`."""

    m = Manifest.build(
        title="X",
        authors=["A"],
        integration_key="claude",
        uri_base="https://example.org/x/",
    )
    target = tmp_path / "manifest.toml"
    m.dump(target)
    with pytest.raises(ManifestOverwriteError) as exc_info:
        m.dump(target)
    assert exc_info.value.path == target.resolve()


def test_overwrite_true_succeeds(tmp_path: Path) -> None:
    """AS3: `overwrite=True` overwrites the existing file."""

    m = Manifest.build(
        title="X",
        authors=["A"],
        integration_key="claude",
        uri_base="https://example.org/x/",
    )
    target = tmp_path / "manifest.toml"
    m.dump(target)
    # second write with overwrite=True is allowed.
    m.dump(target, overwrite=True)
    assert target.read_text(encoding="utf-8").count("[bookwright]") == 1


@pytest.mark.parametrize("fixture", ["valid_full.toml", "valid_minimal.toml"])
def test_round_trip_is_byte_identical(fixture: str, tmp_path: Path) -> None:
    """FR-020 + SC-005: load → dump produces a byte-identical file."""

    source = load_fixture(fixture)
    target = tmp_path / fixture
    Manifest.load(source).dump(target, overwrite=True)
    assert source.read_bytes() == target.read_bytes()


def test_dump_ignores_post_load_mutation(tmp_path: Path) -> None:
    """Contract: `dump()` writes the captured tomlkit document, not the model.

    Pins the v0 mutation-semantics limit documented in
    `contracts/manifest_api.md` §`Manifest.dump`: assignments to model
    fields after `load()` are syntactically legal (the models are not
    `frozen=True`) but are NOT reflected in the dumped output.
    """

    source = load_fixture("valid_minimal.toml")
    target = tmp_path / "manifest.toml"

    m = Manifest.load(source)
    assert m.book.title == "Minimal Book"

    m.book.title = "Mutated Title"
    m.validators.enabled.append("never-persisted")

    m.dump(target, overwrite=False)

    # The dumped file matches the original source byte-for-byte; the
    # post-load mutations are silently dropped.
    assert target.read_bytes() == source.read_bytes()
    body = target.read_text(encoding="utf-8")
    assert "Mutated Title" not in body
    assert "never-persisted" not in body


def test_dump_atomicity_failure_preserves_prior_contents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-021: a mid-write failure leaves the destination's prior contents intact."""

    target = tmp_path / "manifest.toml"
    target.write_text("# prior contents — do not touch\n", encoding="utf-8")
    prior_body = target.read_bytes()

    m = Manifest.build(
        title="X",
        authors=["A"],
        integration_key="claude",
        uri_base="https://example.org/x/",
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(os, "replace", _boom)

    with pytest.raises(OSError, match="simulated rename failure"):
        m.dump(target, overwrite=True)

    # Prior contents preserved.
    assert target.read_bytes() == prior_body
    # Temp file cleaned up.
    leftovers = [p for p in tmp_path.iterdir() if p.name.startswith(".manifest.toml.")]
    assert leftovers == []
