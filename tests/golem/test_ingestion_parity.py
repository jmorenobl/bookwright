"""Ingestion-parity guard: the *modelled* set minus the *fed* set must equal the
deferral registry, observed against a real graph build (iteration 024).

Eight of the thirteen :data:`~bookwright.golem.CONCEPTS` materialize from authored
text today; the other five are orphans — modelled but unfed. This module builds
the GOLEM graph from the dedicated ``parity-exercise`` fixture through the real
pipeline (:func:`build_project_graph`), reads back the concept-level ``rdf:type``
IRIs the engine actually produced, derives the orphan set, and asserts it equals
exactly the keys of :data:`DEFERRED_CONCEPTS` (FR-005, SC-001). The "alive" set is
observed from the graph, never hand-listed (FR-003): when iteration 025+ wires a
concept, the test stays green only once both a builder feeds it *and* its registry
entry is removed.

The pure :func:`parity_diff` helper names the offending concept(s) under drift;
the three drift-simulation tests drive it on perturbed *local copies* of the two
sets, never mutating the production registry.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.commands._graph import BuildOutcome, build_project_graph
from bookwright.core.manifest import Manifest
from bookwright.golem import CONCEPTS
from bookwright.golem.deferrals import DEFERRED_CONCEPTS
from bookwright.golem.namespaces import CLASS_IRI
from tests.conftest import copy_fixture

PARITY_FIXTURE = "parity-exercise"

#: The eight concepts the fixture's authored text materializes (FR-004 reachable-set pin).
EXPECTED_REACHABLE: set[str] = {
    "Character",
    "Setting",
    "NarrativeLocation",
    "Object",
    "NarrativeEvent",
    "SocialRelationship",
    "NarrativeRole",
    "AttributeAssignment",
}

#: The five orphan concept names — must equal the registry keys and never appear reachable.
ORPHAN_NAMES: set[str] = {
    "PsychologicalState",
    "RelationshipRole",
    "NarrativeUnit",
    "NarrativeFunction",
    "NarrativeSequence",
}

#: The full concept→target_version mapping, pinned as a contract (FR-002, SC-002).
EXPECTED_VERSIONS: dict[str, str] = {
    "NarrativeUnit": "v0.4",
    "NarrativeFunction": "v0.4",
    "NarrativeSequence": "v0.4",
    "RelationshipRole": "v0.4",
    "PsychologicalState": "v0.4",
}

#: Carrier IRIs in ``CLASS_IRI`` but deliberately outside ``CONCEPTS`` (FR-010).
CARRIER_NAMES: set[str] = {"CharacterFeature", "Dimension", "Type", "TimeInterval"}


# --- liveness probe (FR-003, research D2/D3) --------------------------------


def _observed_types(outcome: BuildOutcome) -> set[str]:
    """The set of ``rdf:type`` IRIs (as strings) the built graph actually holds."""
    return {row["t"] for row in outcome.engine.query("SELECT DISTINCT ?t WHERE { ?s a ?t }")}


def _reachable(types: set[str]) -> set[str]:
    """``CONCEPTS`` names whose ``CLASS_IRI`` appears in the observed types (scoped)."""
    return {name for name in CONCEPTS if str(CLASS_IRI[name]) in types}


def parity_diff(reachable: set[str], deferred: set[str]) -> tuple[set[str], set[str]]:
    """Name the concepts that break parity (FR-006/007/008, data-model §Failure-message).

    Returns ``(fed_but_deferred, undeclared_orphans)`` where
    ``fed_but_deferred = reachable ∩ deferred`` (a concept the graph feeds yet the
    registry still declares deferred — FR-006/FR-007) and
    ``undeclared_orphans = (CONCEPTS - reachable) - deferred`` (a real orphan the
    registry forgot to declare — FR-008). On correct inputs both are empty; under
    drift the non-empty set names every offending concept (SC-003). Pure: no I/O,
    no mutation of either argument.
    """
    fed_but_deferred = reachable & deferred
    undeclared_orphans = (set(CONCEPTS) - reachable) - deferred
    return fed_but_deferred, undeclared_orphans


# --- the real build, shared module-scoped so the corpus is built once -------


@pytest.fixture(scope="module")
def parity_project(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Manifest]:
    """A throwaway copy of the ``parity-exercise`` fixture + its loaded manifest.

    Copied so the build's derived ``bible/graph.ttl`` never mutates the committed
    source tree (Principle I); module-scoped so the corpus is copied once.
    """
    root = copy_fixture(PARITY_FIXTURE, tmp_path_factory.mktemp("parity"))
    return root, Manifest.load(root / "manifest.toml")


@pytest.fixture(scope="module")
def parity_outcome(parity_project: tuple[Path, Manifest]) -> BuildOutcome:
    """One real pipeline build of the parity corpus (the liveness source of truth)."""
    root, manifest = parity_project
    return build_project_graph(root, manifest)


# --- reachable-set pin (FR-004) ---------------------------------------------


def test_reachable_set_pin(parity_outcome: BuildOutcome) -> None:
    """Exactly the eight reachable concepts materialize; no orphan IRI appears (FR-004)."""
    types = _observed_types(parity_outcome)
    assert _reachable(types) == EXPECTED_REACHABLE
    orphan_iris = {str(CLASS_IRI[name]) for name in ORPHAN_NAMES}
    assert orphan_iris.isdisjoint(types), (
        f"orphan rdf:type IRIs leaked into the build: {sorted(orphan_iris & types)}"
    )


# --- registry well-formedness (FR-002, FR-010, SC-002) ----------------------


def test_registry_well_formed() -> None:
    """The registry's shape and the full version mapping are a contract (FR-002, SC-002)."""
    assert set(DEFERRED_CONCEPTS) <= set(CONCEPTS)
    assert len(DEFERRED_CONCEPTS) == 5
    assert set(DEFERRED_CONCEPTS) == ORPHAN_NAMES
    assert all(note.reason for note in DEFERRED_CONCEPTS.values())
    assert CARRIER_NAMES.isdisjoint(DEFERRED_CONCEPTS), "a non-concept carrier was deferred"
    assert {
        name: note.target_version for name, note in DEFERRED_CONCEPTS.items()
    } == EXPECTED_VERSIONS
    # No entry may carry the eliminated "undecided" verdict (FR-011, SC-003) — so
    # the literal can never silently return to the registry.
    assert all(note.target_version != "undecided" for note in DEFERRED_CONCEPTS.values())


# --- the live guard (FR-005, SC-001) ----------------------------------------


def test_ingestion_parity_holds(parity_outcome: BuildOutcome) -> None:
    """The real orphan set equals exactly the deferral registry's keys (FR-005, SC-001)."""
    reachable = _reachable(_observed_types(parity_outcome))
    orphans = set(CONCEPTS) - reachable
    fed_but_deferred, undeclared_orphans = parity_diff(reachable, set(DEFERRED_CONCEPTS))
    assert orphans == set(DEFERRED_CONCEPTS), (
        "ingestion parity drifted — "
        f"fed-but-still-deferred: {sorted(fed_but_deferred)}; "
        f"undeclared orphans: {sorted(undeclared_orphans)}. "
        "Wire a builder and remove the entry from DEFERRED_CONCEPTS, or add the entry."
    )


# --- drift simulations: FR-006/007/008 (perturbed copies, never the registry) ---


def test_drift_fed_but_deferred_from_corpus(parity_outcome: BuildOutcome) -> None:
    """A reachable concept added to the deferred copy is named by ``fed_but_deferred`` (FR-006)."""
    reachable = _reachable(_observed_types(parity_outcome))
    deferred = set(DEFERRED_CONCEPTS) | {"Character"}
    fed_but_deferred, _ = parity_diff(reachable, deferred)
    assert "Character" in fed_but_deferred


def test_drift_declaring_an_already_fed_concept(parity_outcome: BuildOutcome) -> None:
    """Declaring an already-fed concept deferred trips the same set condition (FR-007)."""
    reachable = _reachable(_observed_types(parity_outcome))
    deferred = set(DEFERRED_CONCEPTS) | {"NarrativeEvent"}
    fed_but_deferred, _ = parity_diff(reachable, deferred)
    assert "NarrativeEvent" in fed_but_deferred


def test_drift_undeclared_orphan(parity_outcome: BuildOutcome) -> None:
    """A real orphan dropped from the deferred copy is named by ``undeclared_orphans`` (FR-008)."""
    reachable = _reachable(_observed_types(parity_outcome))
    deferred = set(DEFERRED_CONCEPTS) - {"PsychologicalState"}
    _, undeclared_orphans = parity_diff(reachable, deferred)
    assert "PsychologicalState" in undeclared_orphans


# --- determinism: a second, independent build (FR-009, SC-004) --------------


def test_verdict_is_deterministic(parity_project: tuple[Path, Manifest]) -> None:
    """A fresh, independent build yields an identical verdict (FR-009, SC-004)."""
    root, manifest = parity_project
    first = build_project_graph(root, manifest)
    second = build_project_graph(root, manifest)
    first_reachable = _reachable(_observed_types(first))
    second_reachable = _reachable(_observed_types(second))
    assert first_reachable == second_reachable
    assert (set(CONCEPTS) - first_reachable) == (set(CONCEPTS) - second_reachable)
