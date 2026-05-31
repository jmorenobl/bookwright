"""Namespaces, class/predicate IRIs, prefix binding and the frozen ontology.

All IRIs are hard-coded (confirmed against the vendored ``golem.ttl`` @
``f666128a…``); the Turtle is never parsed at import time, keeping construction
cheap and side-effect-free (research D5). The frozen ontology is loaded only by
:func:`load_frozen_ontology` / :func:`frozen_terms`, which back the term-closure
test (SC-003).
"""

from __future__ import annotations

from importlib import resources

from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, XSD
from rdflib.term import URIRef

from bookwright.resources.schemas import SCHEMA_DIR

__all__ = [
    "ASSIGNED",
    "ASSIGNED_ATTRIBUTE_TO",
    "CLASS_IRI",
    "CRM",
    "DLP",
    "GENERICALLY_DEPENDENT_ON",
    "GENERIC_LOCATION",
    "GOLEM",
    "PARTICIPANT",
    "PROPER_PART",
    "RDF",
    "RDFS",
    "REFERS_TO",
    "USED_SPECIFIC_OBJECT",
    "XSD",
    "bind_prefixes",
    "frozen_terms",
    "load_frozen_ontology",
]

# --- Namespaces -------------------------------------------------------------

GOLEM = Namespace("https://w3id.org/golem/ontology#")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
# The DOLCE-Lite-Plus layer the frozen GOLEM ontology actually emits its
# participation / part / dependence / location predicates from (research D5).
DLP = Namespace("http://www.ontologydesignpatterns.org/ont/dlp/DOLCE-Lite.owl#")

_PREFIXES: tuple[tuple[str, Namespace], ...] = (
    ("golem", GOLEM),
    ("crm", CRM),
    ("dlp", DLP),
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
}
"""Concept name → rdf:type IRI. Every value is asserted ∈ frozen_terms() (SC-003)."""

# --- Cross-reference predicate IRIs (FR-015, recorded in data-model.md T021) -

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
