"""Validator discovery and configuration resolution (contracts/validator-protocol.md).

Built-ins are auto-discovered by iterating the ``bookwright.validation.validators``
package (``pkgutil``); customs are loaded from sorted ``*.py`` under
``<root>/.bookwright/validators/`` (``importlib``). No hand-registration, no
``entry_points`` (research D2). Discovery is deterministic: modules sorted by name,
objects within a module sorted by validator name (D8).
"""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from bookwright.validation import validators as _validators_pkg
from bookwright.validation.base import UnknownValidatorError, Validator, ValidatorError

if TYPE_CHECKING:
    from bookwright.core.manifest import ValidatorsBlock

__all__ = ["discover_validators", "resolve_active"]


def _looks_like_validator_class(value: object) -> bool:
    """Whether ``value`` is a concrete class shaped like a validator (not a Protocol)."""
    if not isinstance(value, type) or getattr(value, "_is_protocol", False):
        return False
    return all(hasattr(value, attr) for attr in ("name", "severity_default", "validate"))


def _as_validator(value: object) -> Validator | None:
    """Normalize a module-level object to a validator instance, or ``None``.

    A conforming class is instantiated once (data-model); an already-built
    conforming instance is used as-is. A class that raises on construction is
    treated as not-a-validator (its file then yields the "no conforming" error).
    """
    if _looks_like_validator_class(value):
        try:
            instance = value()  # type: ignore[operator]
        except Exception:  # a broken ctor is "no conforming validator", not a crash
            return None
        return instance if isinstance(instance, Validator) else None
    if isinstance(value, Validator) and not isinstance(value, type):
        return value
    return None


def _collect_from_module(module: ModuleType) -> list[Validator]:
    """Every conforming validator declared at module level, sorted by ``name``."""
    found: list[Validator] = []
    for attr, value in vars(module).items():
        if attr.startswith("_"):
            continue
        instance = _as_validator(value)
        if instance is not None:
            found.append(instance)
    return sorted(found, key=lambda v: v.name)


def _discover_builtins() -> tuple[dict[str, Validator], list[ValidatorError]]:
    builtins: dict[str, Validator] = {}
    errors: list[ValidatorError] = []
    modules = sorted(pkgutil.iter_modules(_validators_pkg.__path__), key=lambda m: m.name)
    for info in modules:
        module = importlib.import_module(f"{_validators_pkg.__name__}.{info.name}")
        for validator in _collect_from_module(module):
            if validator.name in builtins:
                errors.append(
                    ValidatorError(
                        validator.name,
                        f"duplicate built-in validator name '{validator.name}'",
                        "load",
                    )
                )
                continue
            builtins[validator.name] = validator
    return builtins, errors


def _load_custom_module(path: Path, mod_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        raise ImportError(f"cannot load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _discover_customs(
    custom_dir: Path, builtins: dict[str, Validator]
) -> tuple[dict[str, Validator], list[ValidatorError]]:
    customs: dict[str, Validator] = {}
    errors: list[ValidatorError] = []
    if not custom_dir.is_dir():
        return customs, errors
    root = custom_dir.parent.parent  # <root>/.bookwright/validators
    for index, path in enumerate(sorted(custom_dir.glob("*.py"))):
        try:
            relpath = path.relative_to(root).as_posix()
        except ValueError:  # pragma: no cover — custom_dir always under root
            relpath = path.as_posix()
        try:
            module = _load_custom_module(path, f"_bookwright_custom_{index}_{path.stem}")
        except Exception as exc:  # any import failure is a skip (FR-005), never a crash
            errors.append(ValidatorError(relpath, f"{type(exc).__name__}: {exc}", "load"))
            continue
        found = _collect_from_module(module)
        if not found:
            errors.append(ValidatorError(relpath, "no conforming validator found", "load"))
            continue
        for validator in found:
            name = validator.name
            if name in builtins:
                errors.append(
                    ValidatorError(
                        relpath,
                        f"custom validator name '{name}' collides with a built-in; rename it",
                        "load",
                    )
                )
                continue
            if name in customs:
                errors.append(
                    ValidatorError(relpath, f"duplicate custom validator name '{name}'", "load")
                )
                continue
            customs[name] = validator
    return customs, errors


def discover_validators(
    custom_dir: Path,
) -> tuple[dict[str, Validator], dict[str, Validator], list[ValidatorError]]:
    """Discover built-in and custom validators (FR-004/005).

    Returns ``(builtins, customs, load_errors)``. The built-in and custom dicts are
    **disjoint by name**: a custom colliding with a built-in is dropped with an
    attributed ``ValidatorError(phase="load")`` so a built-in coherence check is
    never silently shadowed by project code (FR-019, D2). A malformed custom file --
    import failure, no conforming object, or a duplicate name -- is skipped the same
    way; the run continues.
    """
    builtins, builtin_errors = _discover_builtins()
    customs, custom_errors = _discover_customs(custom_dir, builtins)
    return builtins, customs, builtin_errors + custom_errors


def resolve_active(
    builtins: dict[str, Validator],
    customs: dict[str, Validator],
    cfg: ValidatorsBlock,
) -> list[Validator]:
    """Apply the ``[validators]`` config to the discovered set (research D7).

    1. A non-empty ``custom`` allow-lists the discovered customs to those names.
    2. ``candidates = builtins + customs`` minus ``disabled``.
    3. A non-empty ``enabled`` intersects ``candidates`` with those names.
    4. Any ``enabled`` / ``disabled`` / ``custom`` name absent from the discovered
       ``builtins + customs`` -> :class:`UnknownValidatorError` (FR-007).

    Returns the active validators sorted by ``name`` (FR-019, D8).
    """
    discovered = {**builtins, **customs}

    unknown = tuple(
        sorted(
            name for name in (*cfg.enabled, *cfg.disabled, *cfg.custom) if name not in discovered
        )
    )
    if unknown:
        raise UnknownValidatorError(unknown)

    selected_customs = {name: customs[name] for name in cfg.custom} if cfg.custom else dict(customs)
    candidates = {**builtins, **selected_customs}
    disabled = set(cfg.disabled)
    active = {name: v for name, v in candidates.items() if name not in disabled}
    if cfg.enabled:
        enabled = set(cfg.enabled)
        active = {name: v for name, v in active.items() if name in enabled}
    return [active[name] for name in sorted(active)]
