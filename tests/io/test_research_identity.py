"""Reader tests for the authored identity records (020 research D2).

Split from ``test_research.py`` so that file stays under the Principle IV
500-line ceiling, mirroring the ``io/_research_identity.py`` decomposition.
``finding_identities`` / ``anchor_identities`` are the corpus-stable carriers
the status report joins graph projections back to: authored ids + relpaths,
with the minted URI as an in-process join key only. The mapping behavior they
piggyback on is pinned by ``test_research.py`` — these guards cover the records.
"""

from __future__ import annotations

from pathlib import Path

from tests.io.test_research import SOURCES_OK, TOPIC_ANCHOR, TOPIC_FINDING, TOPIC_RELPATH, _run


def test_finding_identity_captured_for_every_finding(tmp_path: Path) -> None:
    result = _run(tmp_path, sources=SOURCES_OK, topic=TOPIC_FINDING)
    assert len(result.finding_identities) == len(result.findings) == 1
    identity = result.finding_identities[0]
    assert identity.id == "tip-required"
    assert identity.relpath == TOPIC_RELPATH
    assert identity.uri == str(result.findings[0].uri)  # in-process join key


def test_open_question_identity_captured_from_index(tmp_path: Path) -> None:
    index = "---\nopen_questions:\n  - id: q-archivo\n---\n"
    result = _run(tmp_path, index=index)
    assert [identity.id for identity in result.finding_identities] == ["q-archivo"]
    assert result.finding_identities[0].relpath == "bible/research/_index.md"


def test_anchor_identity_carries_authored_names(tmp_path: Path) -> None:
    result = _run(tmp_path, sources=SOURCES_OK, topic=TOPIC_ANCHOR)
    assert len(result.anchor_identities) == len(result.anchors) == 1
    identity = result.anchor_identities[0]
    assert identity.promotes_id == "tip-required"
    assert identity.constrains == "Manuel de Aparici"
    assert identity.relpath == TOPIC_RELPATH
    assert identity.uri == str(result.anchors[0].uri)


def test_anchor_identity_normalizes_timeline(tmp_path: Path) -> None:
    topic = TOPIC_ANCHOR.replace('constrains: "Manuel de Aparici"', "constrains: timeline")
    result = _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert result.anchor_identities[0].constrains == "timeline"


def test_anchor_identity_dropped_link_normalizes_to_none(tmp_path: Path) -> None:
    # The unresolved-target soft miss (D12): no constrains triple in the graph,
    # so the identity mirrors that with None rather than echoing a dead name.
    topic = TOPIC_ANCHOR.replace('constrains: "Manuel de Aparici"', 'constrains: "Fantasma"')
    result = _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert result.anchor_identities[0].constrains is None


def test_anchor_identity_null_constrains_is_none(tmp_path: Path) -> None:
    topic = TOPIC_ANCHOR.replace('constrains: "Manuel de Aparici"', "constrains: null")
    result = _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert result.anchor_identities[0].constrains is None
