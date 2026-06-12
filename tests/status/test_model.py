"""Unit coverage for the status state model (020, data-model § 2).

Pins the payload shapes the CLI contract serializes: the ``{"count", "items"}``
invariant (FR-011a), order preservation, the fixed ``counts`` key order, and
the determinism rule that no minted URI / timestamp / environment data ever
reaches a serialized shape (research D2).
"""

from __future__ import annotations

import json
import re

from bookwright.status.model import (
    AnchorGap,
    GraphFacts,
    LowReliabilityFinding,
    OpenQuestion,
    StatusState,
    ValidationSummary,
)


def _state() -> StatusState:
    """A representative fully-populated state (items pre-ordered, as produced)."""
    return StatusState(
        phase="drafting",
        focus_defined=True,
        graph=GraphFacts(available=True, entities=12, triples=240),
        open_questions=(
            OpenQuestion(id="q-archivo", text=None, file="bible/research/_index.md"),
            OpenQuestion(id="q-mercurio", text="¿Cómo?", file="bible/research/_index.md"),
        ),
        unresolved_anchors=(
            AnchorGap(
                promotes="rel-001",
                constrains="timeline",
                file="bible/research/medicina.md",
                problems=("under_reliable",),
            ),
        ),
        low_reliability_findings=(
            LowReliabilityFinding(
                id="rel-001", best_reliability="baja", file="bible/research/medicina.md"
            ),
        ),
        validation=ValidationSummary(
            counts={"error": 1, "warning": 3, "info": 0}, ran=("temporal",)
        ),
    )


def test_state_payload_has_exactly_the_contract_keys() -> None:
    payload = _state().to_payload()
    assert list(payload) == [
        "phase",
        "graph",
        "open_questions",
        "unresolved_anchors",
        "low_reliability_findings",
        "validation",
    ]
    # focus_defined is predicate input only — the focus content is top-level
    # in the report, never duplicated inside state.
    assert "focus_defined" not in payload


def test_every_item_list_fact_carries_count_equal_to_items() -> None:
    payload = _state().to_payload()
    for key in ("open_questions", "unresolved_anchors", "low_reliability_findings"):
        fact = payload[key]
        assert list(fact) == ["count", "items"]
        assert fact["count"] == len(fact["items"])


def test_item_shapes_match_the_contract() -> None:
    payload = _state().to_payload()
    assert payload["graph"] == {"available": True, "entities": 12, "triples": 240}
    assert payload["open_questions"]["items"][0] == {
        "id": "q-archivo",
        "text": None,
        "file": "bible/research/_index.md",
    }
    assert payload["unresolved_anchors"]["items"][0] == {
        "promotes": "rel-001",
        "constrains": "timeline",
        "file": "bible/research/medicina.md",
        "problems": ["under_reliable"],
    }
    assert payload["low_reliability_findings"]["items"][0] == {
        "id": "rel-001",
        "best_reliability": "baja",
        "file": "bible/research/medicina.md",
    }


def test_payload_preserves_the_producer_ordering() -> None:
    # Ordering is established once, at construction (queries sort by the
    # corpus-stable keys); the payload must echo stored order untouched.
    ids = [item["id"] for item in _state().to_payload()["open_questions"]["items"]]
    assert ids == ["q-archivo", "q-mercurio"]


def test_validation_counts_serialize_in_fixed_key_order_zero_filled() -> None:
    # Construction order scrambled + a missing key: the payload still emits
    # error/warning/info, zero-filled (byte-identity, SC-002).
    summary = ValidationSummary(counts={"info": 2, "error": 1}, ran=("a", "b"))
    payload = summary.to_payload()
    assert list(payload["counts"]) == ["error", "warning", "info"]
    assert payload["counts"] == {"error": 1, "warning": 0, "info": 2}
    assert payload["ran"] == ["a", "b"]


def test_serialized_state_carries_no_uri_timestamp_or_environment_data() -> None:
    document = json.dumps(_state().to_payload())
    assert "://" not in document  # no minted (or any) URIs (research D2)
    assert "uri" not in json.dumps(list(_state().to_payload())).lower()
    assert not re.search(r"\d{4}-\d{2}-\d{2}T", document)  # no timestamps
    assert "/Users/" not in document and "tmp" not in document  # no paths beyond relpaths
