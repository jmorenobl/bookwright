"""Built-in validator modules.

This package is the auto-discovery root: :func:`bookwright.validation.registry.
discover_validators` iterates its modules with ``pkgutil.iter_modules`` and
collects every module-level object satisfying the ``Validator`` protocol. Adding
a built-in is dropping a new module here — no hand-registration (FR-004).
"""

from __future__ import annotations
