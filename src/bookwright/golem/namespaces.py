"""Namespaces, class/predicate IRIs, prefix binding and the frozen ontology.

All IRIs are hard-coded (confirmed against the vendored ``golem.ttl`` @
``f666128a…``); the Turtle is never parsed at import time, keeping construction
cheap and side-effect-free (research D5). The frozen ontology is loaded only by
:func:`load_frozen_ontology` / :func:`frozen_terms`, which back the term-closure
test (SC-003).
"""

from __future__ import annotations

from importlib import resources
from typing import NamedTuple

from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, XSD
from rdflib.term import URIRef

from bookwright.resources.schemas import SCHEMA_DIR

__all__ = [
    "ASSIGNED",
    "ASSIGNED_ATTRIBUTE_TO",
    "BEGIN_OF_BEGIN",
    "BW",
    "BW_ACCESS_DATE",
    "BW_ASSERTED_BY",
    "BW_AUTHOR",
    "BW_CLAIM",
    "BW_CONSTRAINS",
    "BW_OPEN",
    "BW_ORIGINAL_LANGUAGE",
    "BW_ORIGINAL_QUOTE",
    "BW_PROMOTES",
    "BW_REFERENCE",
    "BW_RELIABILITY",
    "BW_RELIABILITY_JUSTIFICATION",
    "BW_SEQUENCE_ORDINAL",
    "BW_SUPPORTED_BY",
    "BW_TRANSLATION",
    "CLASS_IRI",
    "CRM",
    "CSM",
    "DLP",
    "DURATION",
    "E52_TIME_SPAN",
    "EDNS",
    "END_OF_END",
    "FOLLOWS",
    "GENERICALLY_DEPENDENT_ON",
    "GENERIC_LOCATION",
    "GOLEM",
    "HAS_DIMENSION",
    "HAS_FEATURE",
    "HAS_TIME_SPAN",
    "HAS_TYPE",
    "HAS_VALUE",
    "PARTICIPANT",
    "PLAYS",
    "PRECEDES",
    "PROPER_PART",
    "RDF",
    "RDFS",
    "REFERS_TO",
    "RELIABILITY_IRI",
    "SOURCE_TYPE_IRI",
    "TEMPORALLY_INCLUDED_IN",
    "TEMPORALLY_INCLUDES",
    "TEMPORALLY_OVERLAPS",
    "TEMPORAL_LOCATION",
    "TEMPORAL_RELATIONS",
    "TR",
    "USED_SPECIFIC_OBJECT",
    "XSD",
    "TemporalRelation",
    "bind_prefixes",
    "frozen_terms",
    "load_frozen_ontology",
    "timeline_uri",
]

# --- Namespaces -------------------------------------------------------------

GOLEM = Namespace("https://w3id.org/golem/ontology#")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
# The DOLCE-Lite-Plus layer the frozen GOLEM ontology actually emits its
# participation / part / dependence / location predicates from (research D5).
DLP = Namespace("http://www.ontologydesignpatterns.org/ont/dlp/DOLCE-Lite.owl#")
# The DOLCE ExtendedDnS layer that supplies ``plays`` (character →
# narrative role) — a *different* file from the DOLCE-Lite ``DLP`` above, kept
# bound to its own ``edns`` prefix so the distinction stays visible (FR-018).
EDNS = Namespace("http://www.ontologydesignpatterns.org/ont/dlp/ExtendedDnS.owl#")
# The DOLCE TemporalRelations layer: the five qualitative event relations plus
# ``temporal-location`` (interval → boundary). All five relations are frozen
# (research D11, verified against ``golem.ttl``).
TR = Namespace("http://www.ontologydesignpatterns.org/ont/dlp/TemporalRelations.owl#")
# The DOLCE CommonSenseMapping layer supplying ``duration`` (event → its
# time-interval, ⊑ ``temporal-location``).
CSM = Namespace("http://www.ontologydesignpatterns.org/ont/dlp/CommonSenseMapping.owl#")
# Bookwright's own vocabulary — the research/provenance terms (``bw:reference``,
# ``bw:claim``, ``bw:constrains``, the source-type / reliability E55 individuals).
# Declared in ``resources/vocabularies/sources.ttl``, **never** in the frozen
# ``golem.ttl``; intentionally outside the ``CLASS_IRI`` closure (Constitution X;
# research D3).
BW = Namespace("https://bookwright.dev/vocab/bw#")

_PREFIXES: tuple[tuple[str, Namespace], ...] = (
    ("golem", GOLEM),
    ("crm", CRM),
    ("dlp", DLP),
    ("edns", EDNS),
    ("tr", TR),
    ("csm", CSM),
    ("bw", BW),
    ("rdf", Namespace(str(RDF))),
    ("rdfs", Namespace(str(RDFS))),
    ("xsd", Namespace(str(XSD))),
)


def bind_prefixes(graph: Graph) -> None:
    """Bind exactly one short prefix per namespace, deterministically (FR-010).

    ``replace=True`` overrides rdflib's auto-bound aliases so serialized Turtle
    is byte-stable across runs.
    """
    for prefix, namespace in _PREFIXES:
        graph.bind(prefix, namespace, replace=True, override=True)


# --- Concept class IRIs (FR-004 local names) --------------------------------

CLASS_IRI: dict[str, URIRef] = {
    "Character": GOLEM["G1_Character"],
    "Object": GOLEM["G16_Object"],
    "SocialRelationship": GOLEM["G4_Social_Relationship"],
    "RelationshipRole": GOLEM["G6_Relationship_Role"],
    "NarrativeEvent": GOLEM["G5_Narrative_Event"],
    "PsychologicalState": GOLEM["G3_Psychological_State"],
    "Setting": GOLEM["G12_Setting"],
    "NarrativeLocation": GOLEM["G13_Narrative_Location"],
    "NarrativeUnit": GOLEM["G9_Narrative_Unit"],
    "NarrativeFunction": GOLEM["G10_Narrative_Function"],
    "NarrativeRole": GOLEM["G11_Narrative_Role"],
    "NarrativeSequence": GOLEM["G7_Narrative_Sequence"],
    "AttributeAssignment": CRM["E13_Attribute_Assignment"],
    # Character-scoped attribute-carrier classes (FR-020). These are NOT
    # narrative concepts — they are excluded from the CONCEPTS registry — but
    # their rdf:type IRIs live here so the closure test (SC-003) covers them too.
    "CharacterFeature": GOLEM["G17_Character_Feature"],
    "Dimension": CRM["E54_Dimension"],
    "Type": CRM["E55_Type"],
    # The DOLCE-Lite time-interval carrying an event's begin/end boundaries
    # (research D11). Closure-safe — emitted by NarrativeEvent's interval triples.
    "TimeInterval": DLP["time-interval"],
}
"""Class name → rdf:type IRI. Every value is asserted ∈ frozen_terms() (SC-003)."""

# --- Cross-reference predicate IRIs (FR-015) -------------------------------

PARTICIPANT = DLP["participant"]
"""Perdurant → endurant participation (relationship / event participants)."""
PROPER_PART = DLP["proper-part"]
"""Whole → ordered part (narrative sequence → its units)."""
GENERICALLY_DEPENDENT_ON = DLP["generically-dependent-on"]
"""Dependent → bearer (psychological state → its character)."""
GENERIC_LOCATION = DLP["generic-location"]
"""Located → locus (narrative location → its setting)."""
REFERS_TO = CRM["P67_refers_to"]
"""Generic cross-reference (role → relationship, unit → function/role, premise)."""
ASSIGNED_ATTRIBUTE_TO = CRM["P140_assigned_attribute_to"]
"""Attribute assignment → the entity it makes an attribution about."""
ASSIGNED = CRM["P141_assigned"]
"""Attribute assignment → the attribute it asserts."""
USED_SPECIFIC_OBJECT = CRM["P16_used_specific_object"]
"""Attribute assignment → the source used in the inference (carries the path)."""

# --- Character-attribute predicates (FR-017/018/019, D14) -------------------

HAS_FEATURE = GOLEM["GP0_has_feature"]
"""Character → one of its character features (biographical or free-text)."""
PLAYS = EDNS["plays"]
"""Character → a narrative role it plays (DOLCE ExtendedDnS, distinct from dlp)."""
HAS_TYPE = CRM["P2_has_type"]
"""Biographical feature → its E55_Type (the birth / death individual)."""
HAS_DIMENSION = CRM["P43_has_dimension"]
"""Biographical feature → its E54_Dimension (carrying the year value)."""
HAS_VALUE = CRM["P90_has_value"]
"""Dimension → its primitive value (the year as an xsd:gYear literal)."""

# --- Temporal-interval predicates (FR-015, research D11) --------------------

DURATION = CSM["duration"]
"""Event → its time-interval (⊑ ``temporal-location``); carries the begin/end span."""
TEMPORAL_LOCATION = TR["temporal-location"]
"""Interval → one of its begin/end boundary intervals."""
FOLLOWS = TR["follows"]
"""Event strictly after another (the canonical strict-order relation)."""
PRECEDES = TR["precedes"]
"""Event strictly before another (inverse direction of ``follows``)."""
TEMPORALLY_OVERLAPS = TR["temporally-overlaps"]
"""Two events share part of their extent (symmetric)."""
TEMPORALLY_INCLUDES = TR["temporally-includes"]
"""Event whose extent contains another's (containment)."""
TEMPORALLY_INCLUDED_IN = TR["temporally-included-in"]
"""Event whose extent is contained within another's (inverse containment)."""

# --- Research / provenance predicates (iteration 012, research D3) -----------
# Bookwright's own ``bw:`` terms. Declared in ``sources.ttl``, referenced from
# ``golem/modules/provenance.py``; NONE are added to ``CLASS_IRI`` or the
# closure-checked lists in ``test_namespaces.py`` — they sit outside the frozen
# GOLEM ontology by design (Constitution X).

BW_REFERENCE = BW["reference"]
"""Source → its bibliographic reference or URL (``xsd:string``)."""
BW_AUTHOR = BW["author"]
"""Source → its author (``xsd:string``)."""
BW_ORIGINAL_LANGUAGE = BW["originalLanguage"]
"""Source → the ISO 639-1 code of its original language (``xsd:string``)."""
BW_RELIABILITY = BW["reliability"]
"""Source → its reliability E55_Type individual (``alta``/``media``/``baja``)."""
BW_RELIABILITY_JUSTIFICATION = BW["reliabilityJustification"]
"""Source → the prose justifying its reliability rating (``xsd:string``)."""
BW_ACCESS_DATE = BW["accessDate"]
"""Source → the date it was consulted (``xsd:date``)."""
BW_ORIGINAL_QUOTE = BW["originalQuote"]
"""Source → the verbatim quote in its original language (``xsd:string``)."""
BW_TRANSLATION = BW["translation"]
"""Source → the quote's translation; emitted iff source language ≠ book language."""
BW_CLAIM = BW["claim"]
"""Finding → the real-world assertion it records (``xsd:string``)."""
BW_ASSERTED_BY = BW["assertedBy"]
"""Finding → who asserts the claim — agent or author (``xsd:string``)."""
BW_SUPPORTED_BY = BW["supportedBy"]
"""Finding → one supporting Source (one triple per source)."""
BW_OPEN = BW["open"]
"""Finding → ``true`` when it is an unresolved open question (``xsd:boolean``)."""
BW_PROMOTES = BW["promotes"]
"""Anchor → the Finding it promotes into a binding constraint."""
BW_CONSTRAINS = BW["constrains"]
"""Anchor → the narrative entity (or the timeline) the constraint bears on."""
BW_SEQUENCE_ORDINAL = BW["sequenceOrdinal"]
"""A narrative unit's 1-based position within its sequence; ``xsd:integer`` (iteration 035)."""

SOURCE_TYPE_IRI: dict[str, URIRef] = {
    "primaria": BW["source-type/primaria"],
    "secundaria": BW["source-type/secundaria"],
    "oficial": BW["source-type/oficial"],
    "académica": BW["source-type/academica"],
    "periodística": BW["source-type/periodistica"],
    "testimonial": BW["source-type/testimonial"],
}
"""Front-matter ``type`` value → its ``a crm:E55_Type`` individual (ASCII-slugged
IRI). The accented Spanish key is the author-facing value; the IRI is slugged
(research D4). Declared in ``sources.ttl``; enforced by the ``Source`` ``Literal``."""

RELIABILITY_IRI: dict[str, URIRef] = {
    "alta": BW["reliability/alta"],
    "media": BW["reliability/media"],
    "baja": BW["reliability/baja"],
}
"""Front-matter ``reliability`` value → its ``a crm:E55_Type`` individual IRI."""

# --- Reused CIDOC-CRM time-span terms (anchor time-span, research D5) --------
# Already-bound ``crm:`` predicates/classes referenced directly; never added to
# ``CLASS_IRI`` (the frozen closure is GOLEM's, not the whole of CIDOC-CRM).

HAS_TIME_SPAN = CRM["P4_has_time-span"]
"""Anchor → its ``E52_Time-Span`` sub-node (optional, research D5)."""
E52_TIME_SPAN = CRM["E52_Time-Span"]
"""``rdf:type`` of an anchor's time-span sub-node."""
BEGIN_OF_BEGIN = CRM["P82a_begin_of_the_begin"]
"""Time-span → its begin year (``xsd:gYear``)."""
END_OF_END = CRM["P82b_end_of_the_end"]
"""Time-span → its end year (``xsd:gYear``)."""


def timeline_uri(uri_base: str) -> URIRef:
    """The well-known, **untyped** timeline IRI an anchor constrains (research D10).

    GOLEM has no single node for "the timeline" (it is a collection of events), yet
    FR-009 lets an anchor constrain it. This returns the conventional ``{uri_base}
    timeline`` IRI — referenced as the object of ``bw:constrains`` only, never typed
    — so era-level anchors resolve without introducing a new GOLEM class.
    """
    return URIRef(f"{uri_base}timeline")


class TemporalRelation(NamedTuple):
    """One qualitative event-to-event temporal relation (research D11).

    ``name`` is the single canonical key used across every layer — the bible
    frontmatter key, the :class:`NarrativeEvent` field, the SPARQL projection key,
    and the validator's predicate map — so the layers never drift apart or fork on
    spelling. ``predicate`` is the frozen ``TR:*`` IRI the relation serializes to.
    """

    name: str
    predicate: URIRef


TEMPORAL_RELATIONS: tuple[TemporalRelation, ...] = (
    TemporalRelation("follows", FOLLOWS),
    TemporalRelation("precedes", PRECEDES),
    TemporalRelation("overlaps", TEMPORALLY_OVERLAPS),
    TemporalRelation("includes", TEMPORALLY_INCLUDES),
    TemporalRelation("included_in", TEMPORALLY_INCLUDED_IN),
)
"""The five qualitative temporal relations, in canonical order — the single source
of truth every consumer derives its own view from (cross_refs, bible keys, queries,
the ``temporal`` validator)."""

# --- Frozen ontology --------------------------------------------------------

_SCHEMA_PACKAGE = "bookwright.resources.schemas"
_ONTOLOGY_RELPATH = f"{SCHEMA_DIR}/golem.ttl"


def load_frozen_ontology() -> Graph:
    """Parse the vendored frozen GOLEM ontology into a fresh rdflib graph."""
    resource = resources.files(_SCHEMA_PACKAGE).joinpath(_ONTOLOGY_RELPATH)
    data = resource.read_text(encoding="utf-8")
    graph = Graph()
    graph.parse(data=data, format="turtle")
    return graph


def frozen_terms() -> set[URIRef]:
    """Every IRI defined or referenced in the frozen ontology (closure backstop).

    Term closure (SC-003) holds iff every class/predicate emitted by any
    ``to_triples()`` is a member of this set.
    """
    graph = load_frozen_ontology()
    return {term for triple in graph for term in triple if isinstance(term, URIRef)}
