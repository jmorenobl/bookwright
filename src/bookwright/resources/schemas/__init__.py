"""Vendored, frozen schema resources (GOLEM ontology Turtle + provenance)."""

from __future__ import annotations

from importlib import resources

SCHEMA_DIR = "golem-1.1"
"""Vendored schema directory name — the single source of truth for the stamp."""


def load_schema_version() -> str:
    """Read the vendored schema's short version label (e.g. ``golem-1.1``).

    Routed through this package's own anchor so the directory name lives in
    exactly one place; both ``bookwright version`` and the ontology loader in
    ``golem.namespaces`` resolve the schema location from here (D11).
    """
    resource = resources.files(__name__).joinpath(f"{SCHEMA_DIR}/VERSION")
    return resource.read_text(encoding="utf-8").strip()
