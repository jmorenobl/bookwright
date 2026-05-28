"""Builder for fresh manifests from minimal inputs (FR-015..FR-017).

Internal helper for `bookwright.core.manifest`. `Manifest.build()` is the
public entry point and delegates here. Kept separate so the public model
module stays under the Principle IV 500-line ceiling.
See specs/002-manifest-model/contracts/manifest_api.md §`Manifest.build`.
"""

from __future__ import annotations

from importlib.resources import files as _resource_files
from typing import TYPE_CHECKING, Any

import tomlkit
from pydantic import ValidationError
from tomlkit.toml_document import TOMLDocument

from bookwright.core._translate import _translate_validation_error

if TYPE_CHECKING:
    from bookwright.core.manifest import Manifest


_BUILD_OVERRIDE_ALLOWLIST_TABLE: dict[str, tuple[str, str]] = {
    "language": ("book", "language"),
    "type": ("book", "type"),
    "subtitle": ("book", "subtitle"),
    "genre": ("book", "genre"),
    "target_length_words": ("book", "target_length_words"),
    "status": ("book", "status"),
    "book_metadata": ("book", "metadata"),
    "vocabularies_active": ("vocabularies", "active"),
    "validators_enabled": ("validators", "enabled"),
    "validators_disabled": ("validators", "disabled"),
    "validators_custom": ("validators", "custom"),
    "paths_manuscript": ("paths", "manuscript"),
    "paths_bible": ("paths", "bible"),
    "paths_outline": ("paths", "outline"),
    "paths_graph": ("paths", "graph"),
    "paths_constitution": ("paths", "constitution"),
    "integration_options": ("integration", "options"),
    "integration_skills_dir": ("integration", "skills_dir"),
    "manifest_version": ("bookwright", "manifest_version"),
    "schema_version": ("bookwright", "schema_version"),
    "cli_version_min": ("bookwright", "cli_version_min"),
    "uri_base": ("bookwright", "uri_base"),
    "indexer": ("bookwright", "indexer"),
}

_BUILD_OVERRIDE_ALLOWLIST: frozenset[str] = frozenset(_BUILD_OVERRIDE_ALLOWLIST_TABLE)


def _load_template_document() -> TOMLDocument:
    """Read the bundled manifest template as a fresh tomlkit document."""

    resource = _resource_files("bookwright.resources.templates").joinpath("manifest.template.toml")
    text = resource.read_text(encoding="utf-8")
    return tomlkit.parse(text)


def _build_manifest(  # noqa: PLR0913 — model_cls + 3 user inputs + 2 injected deps; injection breaks an import cycle with manifest.py.
    model_cls: type[Manifest],
    *,
    title: str,
    authors: list[str],
    integration_key: str,
    installed_version: str,
    default_skills_dir: dict[str, str],
    **overrides: Any,
) -> Manifest:
    """Construct a fresh manifest from minimal inputs.

    `installed_version` and `default_skills_dir` are injected by the caller
    so this helper does not need to import `bookwright.core.manifest`,
    which would close an import cycle.
    """

    unknown = set(overrides) - _BUILD_OVERRIDE_ALLOWLIST
    if unknown:
        name = sorted(unknown)[0]
        raise TypeError(f"build() got unexpected keyword argument '{name}'")

    document = _load_template_document()

    # Apply the three required positional inputs.
    document["book"]["title"] = title
    document["book"]["authors"] = list(authors)
    document["integration"]["key"] = integration_key

    # cli_version_min default = installed CLI version.
    document["bookwright"]["cli_version_min"] = installed_version

    # uri_base has no default at build time (data-model.md). If the caller
    # did not override it, surface the missing-field failure.
    if "uri_base" not in overrides:
        del document["bookwright"]["uri_base"]

    # skills_dir default depends on integration_key (FR-017).
    if "integration_skills_dir" in overrides:
        document["integration"]["skills_dir"] = overrides["integration_skills_dir"]
    else:
        try:
            document["integration"]["skills_dir"] = default_skills_dir[integration_key]
        except KeyError as exc:
            raise TypeError(
                f"build() requires explicit integration_skills_dir for unknown "
                f"integration_key={integration_key!r}"
            ) from exc

    # Overlay caller-provided overrides.
    for kwarg, value in overrides.items():
        if kwarg == "integration_skills_dir":
            continue  # already applied above
        target_block, target_key = _BUILD_OVERRIDE_ALLOWLIST_TABLE[kwarg]
        document[target_block][target_key] = value

    # Re-parse through Pydantic for end-to-end validation (FR-016).
    try:
        instance = model_cls.model_validate(document.unwrap())
    except ValidationError as exc:
        raise _translate_validation_error(exc) from exc
    instance._document = document
    return instance
