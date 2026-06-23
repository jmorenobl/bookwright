"""Build-time loader for the bundled controlled vocabularies (iteration 030).

Reads the packaged ``resources/vocabularies/{name}.ttl`` — Propp's 31 functions,
Greimas' 6 actants, each term a ``crm:E55_Type`` individual carrying ES+EN
``rdfs:label``s — and builds a ``make_slug(label) → term-URI`` index so an
authored narrative-function / character-role name can be resolved to its
canonical term (research D2/D6).

The TTL is the single source of truth: Python hardcodes no term URI and no
alias. The loader depends only on ``golem.slug`` + ``golem.namespaces`` +
``rdflib`` + ``importlib.resources`` — it does no ``golem`` → ``io`` coupling
and never reads the manifest, so the domain model stays pure and the activation
gating lives entirely in the pipeline that calls :func:`load_active_vocabularies`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from importlib import resources

from rdflib import Graph
from rdflib.namespace import RDF, RDFS
from rdflib.term import URIRef

from bookwright.errors import BookwrightError
from bookwright.golem.errors import EmptySlugError
from bookwright.golem.namespaces import CLASS_IRI
from bookwright.golem.slug import make_slug

_VOCAB_PACKAGE = "bookwright.resources.vocabularies"

#: The vocabularies this feature knows how to type against. Any other name in a
#: project's ``[vocabularies] active`` list is ignored silently (research D7).
KNOWN_VOCABULARIES: frozenset[str] = frozenset({"propp", "greimas"})


class VocabularyDataError(BookwrightError):
    """A bundled vocabulary TTL is malformed — two terms collide on one slug (FR-011).

    A vocabulary-data bug surfaced at load time, never a runtime tie-break: the
    fix is to correct the offending label, not to add disambiguation logic.
    Subclasses the shared base and defines no per-class serializer (Principle IX).
    """

    code = "vocabulary_data"


@dataclass(frozen=True)
class VocabularyIndex:
    """An immutable ``make_slug(label) → term-URI`` lookup over one vocabulary.

    Built once per vocabulary from every term's ``rdfs:label``s; ``resolve`` is a
    pure normalize-then-lookup, so the same name always yields the same term
    (determinism, SC-004).

    ``terms`` is the sorted, deduplicated set of every ``rdfs:label`` (ES + EN) — the
    human-facing valid-term enumeration the ``graph build`` warning render derives
    from a warning's ``vocabulary`` (iteration 047, FR-002). Sorting makes it
    byte-stable regardless of the label store's incidental order (FR-016).
    """

    _by_slug: dict[str, URIRef]
    terms: tuple[str, ...]

    def resolve(self, name: str) -> URIRef | None:
        """The term URI an authored name maps to, or ``None`` (no-match / unsluggable).

        ``make_slug`` gives case/accent/ES-EN tolerance (FR-010); a name that
        slugs to nothing (:class:`EmptySlugError`) resolves to ``None`` — untyped,
        silent (FR-006).
        """
        try:
            slug = make_slug(name)
        except EmptySlugError:
            return None
        return self._by_slug.get(slug)


def _index_turtle(data: str, name: str) -> VocabularyIndex:
    """Build a :class:`VocabularyIndex` from Turtle source.

    Indexes every ``?t a crm:E55_Type ; rdfs:label ?l`` by ``make_slug(?l)``.
    Raises :class:`VocabularyDataError` if two distinct terms slug to one alias
    (FR-011). Split out from :func:`load_vocabulary` so the disjointness guard is
    testable against a constructed TTL without a packaged resource.
    """
    graph = Graph()
    graph.parse(data=data, format="turtle")
    by_slug: dict[str, URIRef] = {}
    labels: set[str] = set()
    for term in graph.subjects(RDF.type, CLASS_IRI["Type"]):
        if not isinstance(term, URIRef):
            continue
        for label in graph.objects(term, RDFS.label):
            labels.add(str(label))
            slug = make_slug(str(label))
            existing = by_slug.get(slug)
            if existing is not None and existing != term:
                raise VocabularyDataError(
                    f"vocabulary {name!r}: terms <{existing}> and <{term}> both "
                    f"slug to {slug!r}; fix the colliding label"
                )
            by_slug[slug] = term
    return VocabularyIndex(_by_slug=by_slug, terms=tuple(sorted(labels)))


@cache
def load_vocabulary(name: str) -> VocabularyIndex:
    """Parse ``resources/vocabularies/{name}.ttl`` into a :class:`VocabularyIndex`.

    Cached by ``name`` — the bundled resources are static for a process.
    """
    data = resources.files(_VOCAB_PACKAGE).joinpath(f"{name}.ttl").read_text(encoding="utf-8")
    return _index_turtle(data, name)


@dataclass(frozen=True)
class ActiveVocabularies:
    """The vocabulary indices a build activates — only the active ones populated.

    The pipeline passes :attr:`propp` to ``map_outline`` (function typing) and
    :attr:`greimas` to ``map_bible`` (role typing); a ``None`` slot means that
    vocabulary is inactive, so the corresponding pass types nothing (FR-009).
    """

    propp: VocabularyIndex | None = None
    greimas: VocabularyIndex | None = None


def load_active_vocabularies(active: list[str]) -> ActiveVocabularies:
    """Load the indices for the ``active`` names that are known vocabularies (D7).

    Names outside :data:`KNOWN_VOCABULARIES` are ignored silently; an empty (or
    all-unknown) list yields an all-``None`` record, so the graph is byte-for-byte
    the pre-feature output (FR-008/SC-003).
    """
    selected = {name for name in active if name in KNOWN_VOCABULARIES}
    return ActiveVocabularies(
        propp=load_vocabulary("propp") if "propp" in selected else None,
        greimas=load_vocabulary("greimas") if "greimas" in selected else None,
    )
