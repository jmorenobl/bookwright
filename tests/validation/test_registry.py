"""Discovery + configuration resolution (FR-004..007, D2/D7)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from bookwright.core.manifest import ValidatorsBlock
from bookwright.validation.base import UnknownValidatorError
from bookwright.validation.registry import discover_validators, resolve_active

_BUILTINS = {
    "character_presence",
    "factual_anchor",
    "focalization",
    "setting_continuity",
    "temporal",
}

_GOOD = """
from bookwright.validation import Severity, Violation

class NoTodo:
    name = "no_todo"
    severity_default = Severity.warning
    def validate(self, project, indexer):
        return []
"""

_COLLIDE = """
from bookwright.validation import Severity

class Shadow:
    name = "temporal"
    severity_default = Severity.error
    def validate(self, project, indexer):
        return []
"""

_BROKEN = "def : this is not valid python\n"
_NO_CONFORM = "x = 1\ny = 2\n"


def _custom_dir(tmp_path: Path) -> Path:
    target = tmp_path / ".bookwright" / "validators"
    target.mkdir(parents=True)
    return target


def _write(target: Path, name: str, body: str) -> None:
    (target / name).write_text(textwrap.dedent(body), encoding="utf-8")


def test_builtins_auto_discovered(tmp_path: Path) -> None:
    builtins, customs, errors = discover_validators(tmp_path / "absent")
    assert set(builtins) == _BUILTINS
    assert customs == {}
    assert errors == []


def test_conforming_custom_is_discovered(tmp_path: Path) -> None:
    target = _custom_dir(tmp_path)
    _write(target, "no_todo.py", _GOOD)
    _builtins, customs, errors = discover_validators(target)
    assert set(customs) == {"no_todo"}
    assert errors == []


def test_broken_custom_skipped_with_attributed_error(tmp_path: Path) -> None:
    target = _custom_dir(tmp_path)
    _write(target, "broken.py", _BROKEN)
    _b, customs, errors = discover_validators(target)
    assert customs == {}
    assert len(errors) == 1
    assert errors[0].phase == "load"
    assert errors[0].validator == ".bookwright/validators/broken.py"


def test_no_conforming_object_is_a_load_error(tmp_path: Path) -> None:
    target = _custom_dir(tmp_path)
    _write(target, "nope.py", _NO_CONFORM)
    _b, customs, errors = discover_validators(target)
    assert customs == {}
    assert "no conforming validator" in errors[0].message


def test_custom_colliding_with_builtin_is_skipped_builtin_wins(tmp_path: Path) -> None:
    target = _custom_dir(tmp_path)
    _write(target, "shadow.py", _COLLIDE)
    builtins, customs, errors = discover_validators(target)
    assert "temporal" in builtins  # the built-in still runs
    assert customs == {}  # the shadow is dropped
    assert any("collides with a built-in" in e.message for e in errors)


def test_resolve_active_defaults_to_all_builtins(tmp_path: Path) -> None:
    builtins, customs, _e = discover_validators(tmp_path / "absent")
    active = resolve_active(builtins, customs, ValidatorsBlock())
    assert [v.name for v in active] == sorted(_BUILTINS)


def test_resolve_active_enabled_intersects(tmp_path: Path) -> None:
    builtins, customs, _e = discover_validators(tmp_path / "absent")
    active = resolve_active(builtins, customs, ValidatorsBlock(enabled=["temporal"]))
    assert [v.name for v in active] == ["temporal"]


def test_resolve_active_disabled_subtracts(tmp_path: Path) -> None:
    builtins, customs, _e = discover_validators(tmp_path / "absent")
    active = resolve_active(builtins, customs, ValidatorsBlock(disabled=["temporal"]))
    assert "temporal" not in {v.name for v in active}
    assert len(active) == len(_BUILTINS) - 1


def test_resolve_active_custom_allow_list(tmp_path: Path) -> None:
    target = _custom_dir(tmp_path)
    _write(target, "no_todo.py", _GOOD)
    builtins, customs, _e = discover_validators(target)
    # empty custom = all discovered customs run alongside builtins.
    all_active = resolve_active(builtins, customs, ValidatorsBlock())
    assert "no_todo" in {v.name for v in all_active}
    # non-empty custom allow-lists; an enabled set can still narrow.
    just_custom = resolve_active(
        builtins, customs, ValidatorsBlock(enabled=["no_todo"], custom=["no_todo"])
    )
    assert [v.name for v in just_custom] == ["no_todo"]


def test_resolve_active_unknown_name_raises(tmp_path: Path) -> None:
    builtins, customs, _e = discover_validators(tmp_path / "absent")
    with pytest.raises(UnknownValidatorError) as excinfo:
        resolve_active(builtins, customs, ValidatorsBlock(enabled=["does_not_exist"]))
    assert excinfo.value.names == ("does_not_exist",)
    assert excinfo.value.to_json()["code"] == "unknown_validator"
