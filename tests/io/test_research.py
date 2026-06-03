"""Reader tests for ``io/research.py`` — ``map_research`` (iteration 012).

Exercises the parsing contract (contracts/research-format.md, research-io.md): the
Source registry and its translation rule, findings + open questions, anchors and
their time-spans, the strict hard-error fault model, and the one soft case — an
unresolved narrative ``bears_on``/``constrains`` target (research D12).
"""

from __future__ import annotations

import textwrap
from collections.abc import Mapping
from pathlib import Path

import pytest
from rdflib.term import URIRef

from bookwright.golem.namespaces import timeline_uri
from bookwright.io.errors import ResearchError
from bookwright.io.research import ResearchResult, map_research

URI_BASE = "https://example.org/n/"
CHARACTER_URI = URIRef(f"{URI_BASE}character/manuel-de-aparici")
BIBLE_INDEX: dict[str, URIRef] = {"manuel-de-aparici": CHARACTER_URI}

SOURCES_OK = textwrap.dedent(
    """\
    ---
    sources:
      - name: "Registro TIP"
        reference: "https://www.interior.gob.es/tip"
        author: "Ministerio del Interior"
        original_language: es
        type: oficial
        reliability: alta
        reliability_justification: "Fuente oficial primaria."
        access_date: 2026-05-30
        original_quote: "El detective privado requiere la TIP."
    ---
    """
)


def _run(  # noqa: PLR0913 — a test helper mirroring map_research's own parameters
    tmp_path: Path,
    *,
    sources: str | None = None,
    topic: str | None = None,
    index: str | None = None,
    book_language: str = "es",
    bible_index: Mapping[str, URIRef] | None = None,
) -> ResearchResult:
    research = tmp_path / "bible" / "research"
    research.mkdir(parents=True, exist_ok=True)
    if sources is not None:
        (research / "sources.md").write_text(sources, encoding="utf-8")
    if topic is not None:
        (research / "detective-licencia.md").write_text(topic, encoding="utf-8")
    if index is not None:
        (research / "_index.md").write_text(index, encoding="utf-8")
    return map_research(
        tmp_path,
        research,
        URI_BASE,
        book_language,
        dict(BIBLE_INDEX if bible_index is None else bible_index),
        timeline_uri(URI_BASE),
    )


# --- Empty / absent (foundational) ------------------------------------------


def test_absent_research_dir_yields_empty_result(tmp_path: Path) -> None:
    result = map_research(tmp_path, tmp_path / "nope", URI_BASE, "es", {}, timeline_uri(URI_BASE))
    assert result.entities == ()
    assert result.files_processed == 0


def test_empty_research_dir_yields_empty_result(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.entities == ()
    assert result.files_processed == 0


# --- sources.md (US1) -------------------------------------------------------


def test_valid_source_parses(tmp_path: Path) -> None:
    result = _run(tmp_path, sources=SOURCES_OK)
    assert len(result.sources) == 1
    source = result.sources[0]
    assert source.uri == URIRef(f"{URI_BASE}source/registro-tip")
    assert source.type == "oficial"
    assert source.translation is None


@pytest.mark.parametrize(
    ("field", "value"),
    [("type", "inventado"), ("reliability", "altísima")],
)
def test_out_of_vocabulary_aborts_naming_value(tmp_path: Path, field: str, value: str) -> None:
    bad = SOURCES_OK.replace(f"{field}: oficial", f"{field}: {value}").replace(
        f"{field}: alta", f"{field}: {value}"
    )
    with pytest.raises(ResearchError) as exc:
        _run(tmp_path, sources=bad)
    assert value in str(exc.value)


def test_missing_required_facet_aborts(tmp_path: Path) -> None:
    bad = "\n".join(
        line for line in SOURCES_OK.splitlines() if not line.strip().startswith("author:")
    )
    with pytest.raises(ResearchError) as exc:
        _run(tmp_path, sources=bad)
    assert "author" in str(exc.value)


def test_translation_required_when_language_differs(tmp_path: Path) -> None:
    with pytest.raises(ResearchError) as exc:
        _run(tmp_path, sources=SOURCES_OK, book_language="en")
    assert "translation" in str(exc.value)


def test_translation_present_when_language_differs(tmp_path: Path) -> None:
    with_tr = SOURCES_OK.replace(
        '    original_quote: "El detective privado requiere la TIP."',
        '    original_quote: "El detective privado requiere la TIP."\n'
        '    translation: "The private detective requires the TIP."',
    )
    result = _run(tmp_path, sources=with_tr, book_language="en")
    assert result.sources[0].translation == "The private detective requires the TIP."


def test_translation_dropped_when_language_matches(tmp_path: Path) -> None:
    with_tr = SOURCES_OK.replace(
        '    original_quote: "El detective privado requiere la TIP."',
        '    original_quote: "El detective privado requiere la TIP."\n'
        '    translation: "ignored — same language"',
    )
    result = _run(tmp_path, sources=with_tr, book_language="es")
    assert result.sources[0].translation is None


# --- findings (US2) ---------------------------------------------------------

TOPIC_FINDING = textwrap.dedent(
    """\
    ---
    findings:
      - id: tip-required
        claim: "Necesita la licencia TIP."
        asserted_by: agent
        bears_on: "Manuel de Aparici"
        sources: ["Registro TIP"]
    ---
    """
)


def test_finding_resolves_source_and_bears_on(tmp_path: Path) -> None:
    result = _run(tmp_path, sources=SOURCES_OK, topic=TOPIC_FINDING)
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.claim == "Necesita la licencia TIP."
    assert finding.bears_on == CHARACTER_URI
    assert finding.sources == (URIRef(f"{URI_BASE}source/registro-tip"),)
    assert result.warnings == ()


def test_open_question_in_index_parses(tmp_path: Path) -> None:
    index = "---\nopen_questions:\n  - id: q-archivo\n---\n"
    result = _run(tmp_path, index=index)
    assert len(result.findings) == 1
    assert result.findings[0].open is True
    assert result.findings[0].claim is None


def test_non_open_finding_missing_claim_aborts(tmp_path: Path) -> None:
    topic = '---\nfindings:\n  - id: f1\n    sources: ["Registro TIP"]\n---\n'
    with pytest.raises(ResearchError) as exc:
        _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert "f1" in str(exc.value)


def test_non_open_finding_missing_sources_aborts(tmp_path: Path) -> None:
    topic = '---\nfindings:\n  - id: f1\n    claim: "x"\n---\n'
    with pytest.raises(ResearchError):
        _run(tmp_path, sources=SOURCES_OK, topic=topic)


def test_unknown_source_name_aborts(tmp_path: Path) -> None:
    topic = TOPIC_FINDING.replace("Registro TIP", "Fuente Fantasma")
    with pytest.raises(ResearchError) as exc:
        _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert "Fuente Fantasma" in str(exc.value)


def test_unresolved_bears_on_is_soft_warning(tmp_path: Path) -> None:
    topic = TOPIC_FINDING.replace("Manuel de Aparici", "Personaje Inexistente")
    result = _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert result.findings[0].bears_on is None
    assert len(result.warnings) == 1
    assert result.warnings[0].field == "bears_on"
    assert result.warnings[0].name == "Personaje Inexistente"


# --- anchors (US3) ----------------------------------------------------------

TOPIC_ANCHOR = textwrap.dedent(
    """\
    ---
    findings:
      - id: tip-required
        claim: "Necesita la licencia TIP."
        bears_on: "Manuel de Aparici"
        sources: ["Registro TIP"]
    anchors:
      - promotes: tip-required
        constrains: "Manuel de Aparici"
        begin: 1995
        end: 2026
    ---
    """
)


def test_anchor_resolves_promotes_and_constrains(tmp_path: Path) -> None:
    result = _run(tmp_path, sources=SOURCES_OK, topic=TOPIC_ANCHOR)
    assert len(result.anchors) == 1
    anchor = result.anchors[0]
    assert anchor.promotes == result.findings[0].uri
    assert anchor.constrains == CHARACTER_URI
    assert (anchor.begin, anchor.end) == (1995, 2026)


def test_anchor_constrains_timeline_literal(tmp_path: Path) -> None:
    topic = TOPIC_ANCHOR.replace('constrains: "Manuel de Aparici"', "constrains: timeline")
    result = _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert result.anchors[0].constrains == timeline_uri(URI_BASE)


def test_anchor_unknown_promotes_aborts(tmp_path: Path) -> None:
    topic = TOPIC_ANCHOR.replace("promotes: tip-required", "promotes: no-such-finding")
    with pytest.raises(ResearchError) as exc:
        _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert "no-such-finding" in str(exc.value)


def test_anchor_unresolved_constrains_is_soft_warning(tmp_path: Path) -> None:
    topic = TOPIC_ANCHOR.replace('constrains: "Manuel de Aparici"', 'constrains: "Fantasma"')
    result = _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert result.anchors[0].constrains is None
    assert any(w.field == "constrains" and w.name == "Fantasma" for w in result.warnings)


def test_anchor_date_shorthand_sets_equal_begin_end(tmp_path: Path) -> None:
    topic = TOPIC_ANCHOR.replace("    begin: 1995\n    end: 2026", "    date: 1943")
    result = _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert (result.anchors[0].begin, result.anchors[0].end) == (1943, 1943)


def test_anchor_no_span_leaves_begin_end_none(tmp_path: Path) -> None:
    topic = TOPIC_ANCHOR.replace("    begin: 1995\n    end: 2026\n", "")
    result = _run(tmp_path, sources=SOURCES_OK, topic=topic)
    assert (result.anchors[0].begin, result.anchors[0].end) == (None, None)


def test_malformed_yaml_aborts(tmp_path: Path) -> None:
    with pytest.raises(ResearchError):
        _run(tmp_path, sources="---\nsources: [unbalanced\n---\n")
