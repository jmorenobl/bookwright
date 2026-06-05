"""Direct coverage for the shared error base (``src/bookwright/errors.py``).

These tests exercise ``BookwrightError`` itself — independent of any migrated
subclass — plus the import-isolation invariant (FR-010/INV-4) and the
cross-origin single-source-of-truth proof (SC-002/SC-006).
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any

import pytest

from bookwright.commands.init.validate import InvalidProjectNameError
from bookwright.commands.validate import _UsageError
from bookwright.core.errors import ManifestNotFoundError
from bookwright.errors import BookwrightError
from bookwright.golem.errors import EmptySlugError
from bookwright.indexers.errors import GraphNotBuiltError
from bookwright.integrations.errors import UnknownIntegrationError
from bookwright.io.errors import ProjectNotFoundError
from bookwright.validation.base import UnknownValidatorError

# --------------------------------------------------------------------------- #
# The base's own envelope contract.
# --------------------------------------------------------------------------- #


class _Concrete(BookwrightError):
    """A minimal class-level-``code`` subclass for the base tests."""

    code = "example_code"


def test_details_present_when_populated() -> None:
    """A truthy ``details`` dict is carried through into the envelope."""
    exc = _Concrete("boom", {"field": "value"})
    assert exc.to_json() == {
        "status": "error",
        "code": "example_code",
        "message": "boom",
        "details": {"field": "value"},
    }


def test_details_key_absent_when_none() -> None:
    """``details=None`` omits the key entirely — not ``null``, not ``{}``."""
    exc = _Concrete("boom")
    body = exc.to_json()
    assert "details" not in body
    assert body == {"status": "error", "code": "example_code", "message": "boom"}


def test_details_key_absent_when_empty_dict() -> None:
    """An empty ``details`` dict is falsy ⇒ the key is omitted (uniform rule)."""
    exc = _Concrete("boom", {})
    assert "details" not in exc.to_json()


def test_key_order_is_status_code_message_details() -> None:
    """Insertion order is exactly ``status, code, message, details``."""
    exc = _Concrete("boom", {"k": "v"})
    assert list(exc.to_json().keys()) == ["status", "code", "message", "details"]


def test_per_instance_code_overrides_class_default() -> None:
    """A subclass that sets ``self.code`` in ``__init__`` wins over the class default."""

    class _PerInstance(BookwrightError):
        code = "class_default"

        def __init__(self, code: str) -> None:
            self.code = code
            super().__init__("msg")

    assert _PerInstance("runtime_code").to_json()["code"] == "runtime_code"


def test_str_is_the_message() -> None:
    """``super().__init__(message)`` keeps ``str(exc)`` equal to the message."""
    assert str(_Concrete("a human message")) == "a human message"


# --------------------------------------------------------------------------- #
# Import isolation (FR-010 / INV-4).
# --------------------------------------------------------------------------- #

_FORBIDDEN = (
    "bookwright.core",
    "bookwright.golem",
    "bookwright.io",
    "bookwright.indexers",
    "bookwright.validation",
    "bookwright.integrations",
    "bookwright.commands",
)


def test_errors_module_imports_no_sibling_package() -> None:
    """Importing ``bookwright.errors`` pulls in none of the higher layers.

    Run in a fresh interpreter (a subprocess) because the test suite has already
    imported the whole package — only a cold ``import`` proves the base does not
    structurally depend on its siblings, so no new import cycle is possible.
    """
    program = (
        "import sys\n"
        "import bookwright.errors\n"
        f"forbidden = {_FORBIDDEN!r}\n"
        "leaked = [m for m in forbidden if m in sys.modules]\n"
        "print(','.join(leaked))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )
    leaked = completed.stdout.strip()
    assert leaked == "", f"bookwright.errors leaked sibling imports: {leaked}"


# --------------------------------------------------------------------------- #
# Single source of truth across all eight origins (SC-002 / SC-006).
# --------------------------------------------------------------------------- #


def _one_error_per_origin() -> list[BookwrightError]:
    """Construct one representative error from each of the eight serialized origins."""
    return [
        ManifestNotFoundError("/p/manifest.toml"),
        EmptySlugError("!!!"),
        ProjectNotFoundError("/p"),
        GraphNotBuiltError("/p/graph.ttl"),
        UnknownValidatorError(("a", "b")),
        _UsageError("no_project", "no project here", {"start": "/p"}),
        UnknownIntegrationError(value="copilot", valid=["claude", "generic"]),
        InvalidProjectNameError(value="", rule="empty"),
    ]


def test_all_eight_origins_serialize_through_the_one_base() -> None:
    """SC-002/SC-006 — every origin is a ``BookwrightError`` that inherits the
    single ``to_json()``; none defines its own ``to_json``/``to_dict``."""
    errors = _one_error_per_origin()
    assert len(errors) == 8

    for exc in errors:
        cls = type(exc)
        # (a) instance of the shared base.
        assert isinstance(exc, BookwrightError), cls
        # (b) no per-class envelope serializer — neither to_json nor to_dict
        # anywhere in the MRO below BookwrightError.
        for klass in cls.__mro__:
            if klass is BookwrightError:
                break
            assert "to_json" not in klass.__dict__, f"{klass.__name__} redefines to_json"
            assert "to_dict" not in klass.__dict__, f"{klass.__name__} defines to_dict"
        # The single serializer is the base's.
        assert cls.to_json is BookwrightError.to_json
        # (c) serializes to a well-formed canonical body.
        body = exc.to_json()
        assert body["status"] == "error"
        assert isinstance(body["code"], str) and body["code"]
        assert isinstance(body["message"], str) and body["message"]
        assert list(body.keys())[:3] == ["status", "code", "message"]
        if "details" in body:
            assert isinstance(body["details"], dict) and body["details"]


def test_one_edit_to_base_changes_every_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    """SC-006 — a single edit to ``BookwrightError.to_json`` re-shapes the
    envelope for all eight origins at once (they share the one method)."""
    sentinel: dict[str, Any] = {"patched": True}
    monkeypatch.setattr(BookwrightError, "to_json", lambda self: sentinel)
    for exc in _one_error_per_origin():
        assert exc.to_json() is sentinel
