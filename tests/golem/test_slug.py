"""Slug rule: determinism, ASCII transliteration, empty-name rejection.

FR-005/006, design § 4.5, SC-002 edge case.
"""

from __future__ import annotations

import pytest

from bookwright.golem.errors import EmptySlugError
from bookwright.golem.slug import make_slug


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("José Peña", "jose-pena"),
        ("La caída", "la-caida"),
        ("Aparici", "aparici"),
        ("El faro", "el-faro"),
        ("La caída del puente", "la-caida-del-puente"),
    ],
)
def test_worked_examples(name: str, expected: str) -> None:
    assert make_slug(name) == expected


def test_lowercase_and_ascii() -> None:
    slug = make_slug("ÉÀÇ Ñoño")
    assert slug == slug.lower()
    assert slug.isascii()


def test_collapses_separators_and_trims() -> None:
    assert make_slug("  Hola   ---  Mundo  ") == "hola-mundo"


def test_determinism_and_idempotence() -> None:
    once = make_slug("José Peña")
    assert make_slug("José Peña") == once
    assert make_slug(once) == once


@pytest.mark.parametrize("name", ["!!!", "   ", "-", "...", "@#$%"])
def test_empty_result_rejected(name: str) -> None:
    with pytest.raises(EmptySlugError) as excinfo:
        make_slug(name)
    assert excinfo.value.name == name
    payload = excinfo.value.to_json()
    assert payload["status"] == "error"
    assert payload["code"] == "golem_empty_slug"
    assert payload["details"]["name"] == name
