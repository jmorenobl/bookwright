"""The model never reads the bible/manuscript or the filesystem (FR-014).

Constructing entities and serializing them must perform no file reads. The only
resource the package ever opens is the vendored ``golem.ttl`` (via the
term-closure / frozen-ontology helpers), which these paths do not touch.
"""

from __future__ import annotations

import builtins
import io
import sys

import pytest

from bookwright.golem import Character, SocialRelationship, to_turtle
from tests.golem.conftest import B


def test_golem_package_imports_no_bible_or_manuscript_reader() -> None:
    forbidden = ("bible", "manuscript")
    leaked = [
        m
        for m in set(sys.modules)
        if m.startswith("bookwright.golem") and any(f in m for f in forbidden)
    ]
    assert leaked == []


def test_construction_and_serialization_open_no_files(monkeypatch: pytest.MonkeyPatch) -> None:
    # Warm up rdflib's lazy serializer-plugin registration before banning open().
    _ = to_turtle([Character(uri_base=B, name="Warmup")])

    real_open = builtins.open

    def _banned_open(*args: object, **kwargs: object) -> io.IOBase:
        raise AssertionError(f"unexpected file open: {args!r}")

    monkeypatch.setattr(builtins, "open", _banned_open)

    aparici = Character(uri_base=B, name="Aparici")
    pena = Character(uri_base=B, name="Peña")
    rel = SocialRelationship(uri_base=B, name="R", participants=(aparici, pena))
    list(rel.to_triples())
    ttl = to_turtle([aparici, pena, rel])

    monkeypatch.setattr(builtins, "open", real_open)
    assert "golem:G1_Character" in ttl
