"""The bundled ontology exists, parses, and records its exact provenance.

FR-011, SC-005.
"""

from __future__ import annotations

import json
from importlib import resources

from rdflib import Graph

_SCHEMA_PACKAGE = "bookwright.resources.schemas"
_DIR = "golem-1.1"


def _read(relpath: str) -> str:
    return resources.files(_SCHEMA_PACKAGE).joinpath(f"{_DIR}/{relpath}").read_text("utf-8")


def test_golem_ttl_exists_and_parses() -> None:
    graph = Graph()
    graph.parse(data=_read("golem.ttl"), format="turtle")
    assert len(graph) > 0


def test_version_json_names_repository_and_exact_commit() -> None:
    provenance = json.loads(_read("version.json"))
    assert provenance["repository"] == "https://github.com/GOLEM-lab/golem-ontology"
    assert provenance["commit"] == "f666128a9a29f39c9f23c96ae1c48023cc8e7898"
    assert provenance["file"] == "golem/golem_v1-1.ttl"
    assert provenance["version_iri"] == "https://w3id.org/golem/ontology/v1.1"
    assert provenance["version_info"] == "1.1"


def test_version_label_file() -> None:
    assert _read("VERSION").strip() == "golem-1.1"
