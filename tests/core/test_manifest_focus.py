"""The ``[focus]`` block attachment to ``Manifest`` (load + mutation).

This file covers the load path (backward compatibility, valid/invalid block) and
the ``set_focus`` / ``clear_focus`` round-trip preservation added per story. See
specs/019-focus-state/data-model.md.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from bookwright.core import FocusBlock, Manifest, ManifestValidationError

_BASE = """\
[bookwright]
cli_version_min = "0.0.1"
schema_version = "golem-1.1"
manifest_version = "1"
uri_base = "https://example.org/focus/"

[book]
title = "Focus Book"
type = "novel"
language = "es"
authors = ["Solo Author"]

[integration]
key = "generic"
skills_dir = ".agents/skills"
"""


def _with_focus(block: str) -> str:
    return f"{_BASE}\n[focus]\n{block}"


# --- load: backward compatibility (FR-002, SC-004) ---------------------------


def test_absent_block_loads_as_none(tmp_manifest: Callable[[str], Path]) -> None:
    manifest = Manifest.load(tmp_manifest(_BASE))
    assert manifest.focus is None
    # other fields intact
    assert manifest.book.title == "Focus Book"
    assert manifest.integration.key == "generic"


# --- load: valid block (FR-001) ----------------------------------------------


def test_present_valid_block_populates_focus(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(
        _with_focus('target = "cap-04"\nnotes = "cerrar timeline"\nupdated_at = "2026-06-11"\n')
    )
    manifest = Manifest.load(path)
    assert isinstance(manifest.focus, FocusBlock)
    assert manifest.focus.target == "cap-04"
    assert manifest.focus.notes == "cerrar timeline"
    assert manifest.focus.updated_at == "2026-06-11"


# --- load: invalid updated_at surfaces as manifest_validation (FR-011, SC-005) -


def test_bad_updated_at_names_the_field(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_with_focus('target = "cap-04"\nupdated_at = "nope"\n'))
    with pytest.raises(ManifestValidationError) as exc:
        Manifest.load(path)
    fields = {f.field_path for f in exc.value.failures}
    assert "focus.updated_at" in fields
    # SC-005: a normal validation failure, never a stack trace escaping.
    assert exc.value.code == "manifest_validation"


# --- set_focus round-trip (FR-006, FR-009, SC-002) ---------------------------

_AUTHORED = """\
# top-of-file comment
[bookwright]
cli_version_min = "0.0.1"
schema_version = "golem-1.1"
manifest_version = "1"
uri_base = "https://example.org/focus/"

[book]
title = "Focus Book"  # inline comment
type = "novel"
language = "es"
authors = ["Solo Author"]

[integration]
key = "generic"
skills_dir = ".agents/skills"

# trailing block keeps its comment
[paths]
bible = "bible"
"""


def test_set_focus_creates_block_when_absent(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_BASE)
    manifest = Manifest.load(path)
    assert manifest.focus is None
    manifest.set_focus(target="cap-04", notes="x", updated_at="2026-06-11")
    assert manifest.focus == FocusBlock(target="cap-04", notes="x", updated_at="2026-06-11")
    manifest.dump(path, overwrite=True)
    reloaded = Manifest.load(path)
    assert reloaded.focus == FocusBlock(target="cap-04", notes="x", updated_at="2026-06-11")


def test_set_focus_updates_block_when_present(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_with_focus('target = "old"\nnotes = "n"\nupdated_at = "2026-01-01"\n'))
    manifest = Manifest.load(path)
    manifest.set_focus(target="new", notes="n2", updated_at="2026-06-11")
    manifest.dump(path, overwrite=True)
    reloaded = Manifest.load(path)
    assert reloaded.focus == FocusBlock(target="new", notes="n2", updated_at="2026-06-11")


def test_set_focus_preserves_comments_and_ordering(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_AUTHORED)
    before = path.read_text(encoding="utf-8")
    manifest = Manifest.load(path)
    manifest.set_focus(target="cap-04", notes="", updated_at="2026-06-11")
    manifest.dump(path, overwrite=True)
    after_lines = path.read_text(encoding="utf-8").splitlines()
    # Every original (non-[focus]) line is preserved byte-identically and in order.
    assert before.splitlines() == after_lines[: len(before.splitlines())]
    assert "[focus]" in after_lines


def test_set_focus_on_bare_manifest_raises(tmp_manifest: Callable[[str], Path]) -> None:
    bare = Manifest.load(tmp_manifest(_BASE)).model_copy()
    object.__setattr__(bare, "_document", None)
    with pytest.raises(RuntimeError):
        bare.set_focus(target="cap-04", notes="", updated_at="2026-06-11")


# --- clear_focus round-trip (FR-010, SC-002) ---------------------------------


def test_clear_focus_removes_present_block(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_with_focus('target = "cap-04"\nnotes = "n"\nupdated_at = "2026-06-11"\n'))
    manifest = Manifest.load(path)
    assert manifest.focus is not None
    manifest.clear_focus()
    assert manifest.focus is None
    manifest.dump(path, overwrite=True)
    assert "[focus]" not in path.read_text(encoding="utf-8")
    assert Manifest.load(path).focus is None


def test_clear_focus_preserves_rest_of_manifest(tmp_manifest: Callable[[str], Path]) -> None:
    # Author the base, then append a [focus] block to the otherwise-pristine body.
    base_body = _AUTHORED
    path = tmp_manifest(base_body + '\n[focus]\ntarget = "cap-04"\nupdated_at = "2026-06-11"\n')
    manifest = Manifest.load(path)
    manifest.clear_focus()
    manifest.dump(path, overwrite=True)
    after = path.read_text(encoding="utf-8")
    # Every original authored line survives byte-identically; only [focus] is gone.
    for line in base_body.splitlines():
        assert line in after.splitlines()
    assert "[focus]" not in after


def test_clear_focus_absent_is_noop(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_BASE)
    manifest = Manifest.load(path)
    manifest.clear_focus()  # no error
    assert manifest.focus is None


def test_clear_focus_on_bare_manifest_raises(tmp_manifest: Callable[[str], Path]) -> None:
    bare = Manifest.load(tmp_manifest(_BASE)).model_copy()
    object.__setattr__(bare, "_document", None)
    with pytest.raises(RuntimeError):
        bare.clear_focus()
