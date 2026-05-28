"""Pydantic `ValidationError` → public `ManifestValidationError` translation.

Internal helper for `bookwright.core.manifest`. Kept separate so the
public model module stays under the Principle IV 500-line ceiling.
See specs/002-manifest-model/contracts/manifest_api.md.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from bookwright.core.errors import ManifestValidationError, _FieldFailure

_PYDANTIC_TYPE_TO_KIND: dict[str, str] = {
    "missing": "missing",
    "string_type": "not_a_string",
    "int_type": "not_an_integer",
    "list_type": "not_a_list",
    "dict_type": "not_a_dict",
    "bool_type": "not_a_bool",
    "literal_error": "not_in_enum",
    "extra_forbidden": "unknown_key",
}

# Model-level errors (raised from `@model_validator`) carry no field location.
# Remap them to the field they conceptually belong to.
_ROOT_ERROR_REMAP: dict[str, str] = {
    "installed_too_old": "bookwright.cli_version_min",
    "installed_not_pep440": "bookwright.cli_version_min",
}


def _format_loc(loc: tuple[Any, ...]) -> str:
    """Render a Pydantic location tuple as a dotted path with `[N]` indices."""

    parts: list[str] = []
    for piece in loc:
        if isinstance(piece, int):
            assert parts, "Pydantic loc never starts with an int"
            parts[-1] = f"{parts[-1]}[{piece}]"
        else:
            parts.append(str(piece))
    return ".".join(parts)


def _translate_validation_error(exc: ValidationError) -> ManifestValidationError:
    """Convert a `pydantic.ValidationError` to the public `ManifestValidationError` shape."""

    failures: list[_FieldFailure] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field_path = _format_loc(loc)
        rejected = err.get("input")
        message = err.get("msg", "")
        err_type = err.get("type", "")
        ctx = err.get("ctx") or {}

        if not field_path and err_type in _ROOT_ERROR_REMAP:
            field_path = _ROOT_ERROR_REMAP[err_type]

        # Pydantic built-in error types map to short kinds; custom errors
        # (PydanticCustomError) carry their `error_type` here verbatim.
        kind = _PYDANTIC_TYPE_TO_KIND.get(err_type, err_type or "validation")

        # Prefer the offending value the validator named in `ctx["value"]`
        # (e.g. authors[N] entry) over the validator's whole input.
        if "value" in ctx:
            rejected = ctx["value"]

        rule_id = f"{field_path}.{kind}" if field_path else kind

        # A field-level validator (e.g. `_check_authors`) that walks a list
        # cannot embed the offending index in Pydantic's loc. When it surfaces
        # `ctx["index"]` we splice the `[N]` suffix here so the public
        # `field_path` matches the published contract (book.authors[N]) while
        # `rule_id` stays index-free.
        if "index" in ctx and isinstance(ctx["index"], int):
            field_path = f"{field_path}[{ctx['index']}]"

        failures.append(
            _FieldFailure(
                field_path=field_path,
                rejected_value=rejected,
                rule_id=rule_id,
                message=message,
            )
        )
    return ManifestValidationError(tuple(failures))
