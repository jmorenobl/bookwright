"""Vocabulary TTLs are well-formed and agree with their references (iteration 030).

C1/C3: ``propp.ttl`` / ``greimas.ttl`` parse and carry exactly 31 / 6 ``E55_Type``
terms, each with ≥ 1 ``@en`` and ≥ 1 ``@es`` label. C14 / SC-005: each reference's
"Canonical match-names" section enumerates exactly the EN/ES names of its
vocabulary's terms — set-equality by ``make_slug`` in both directions, so no name
is present in one side and absent from the other. See contracts/vocabulary-typing.md.
"""

from __future__ import annotations

from importlib import resources

import pytest
from rdflib import Graph
from rdflib.namespace import RDF, RDFS
from rdflib.term import Literal, URIRef

from bookwright.golem.namespaces import CLASS_IRI
from bookwright.golem.slug import make_slug
from bookwright.io.vocabularies import load_vocabulary

from .helpers import REFERENCES_DIR, read_text

_VOCAB_PACKAGE = "bookwright.resources.vocabularies"

# (vocabulary name, reference filename, expected term count).
_VOCABS = [
    ("propp", "propp-functions.md", 31),
    ("greimas", "greimas-actants.md", 6),
]


def _graph(name: str) -> Graph:
    data = resources.files(_VOCAB_PACKAGE).joinpath(f"{name}.ttl").read_text(encoding="utf-8")
    graph = Graph()
    graph.parse(data=data, format="turtle")
    return graph


def _terms(graph: Graph) -> list[URIRef]:
    return [t for t in graph.subjects(RDF.type, CLASS_IRI["Type"]) if isinstance(t, URIRef)]


def _match_name_slugs(markdown: str) -> set[str]:
    """The slug set of every name in a reference's 'Canonical match-names' section.

    Each bullet lists equivalent names separated by ``/``; every name is slugged so
    the set is directly comparable with the loader's derived index keys."""
    slugs: set[str] = set()
    in_section = False
    for line in markdown.splitlines():
        if line.startswith("## "):
            in_section = "Canonical match-names" in line
            continue
        if in_section and line.strip().startswith("- "):
            for name in line.strip()[2:].split("/"):
                token = name.strip()
                if token:
                    slugs.add(make_slug(token))
    return slugs


@pytest.mark.parametrize(("name", "_ref", "count"), _VOCABS)
def test_vocabulary_term_count(name: str, _ref: str, count: int) -> None:
    """C1: each TTL parses and carries exactly the expected number of E55_Type terms."""
    assert len(_terms(_graph(name))) == count


@pytest.mark.parametrize(("name", "_ref", "_count"), _VOCABS)
def test_each_term_has_en_and_es_labels(name: str, _ref: str, _count: int) -> None:
    """C3: every term carries at least one @en and one @es label."""
    graph = _graph(name)
    for term in _terms(graph):
        labels = [o for o in graph.objects(term, RDFS.label) if isinstance(o, Literal)]
        langs = {label.language for label in labels}
        assert "en" in langs and "es" in langs, f"{term} missing an en/es label"


@pytest.mark.parametrize(("name", "ref", "_count"), _VOCABS)
def test_reference_matches_vocabulary_both_directions(name: str, ref: str, _count: int) -> None:
    """C14 / SC-005: the reference's canonical match-names slug-equal the loader's
    index keys — no orphan on either side."""
    reference_slugs = _match_name_slugs(read_text(REFERENCES_DIR / ref))
    vocabulary_slugs = set(load_vocabulary(name)._by_slug.keys())
    assert reference_slugs == vocabulary_slugs
