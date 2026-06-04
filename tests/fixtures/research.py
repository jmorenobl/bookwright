"""The single shared ``bible/research/`` fixture (iteration 13 + 14).

One source of truth for every research test. It hosts two tiers, consumed
through the ``research`` knob on ``tests.commands.graph.conftest.scaffold_project``:

* ``"minimal"`` — the iteration-13 constants (``RESEARCH_SOURCES_MD`` /
  ``RESEARCH_TOPIC_MD`` / ``RESEARCH_INDEX_MD``), relocated here **byte-identical**
  from ``graph/conftest.py`` and re-imported there. The 10-E13 count and every
  iteration-13 ``test_research_build.py`` assertion stay stable.
* ``"rich"`` — :func:`write_research_fixture`, a fuller tree that additionally
  exercises iteration-14 success criteria against the tiny-novel bible
  (the ``Manuel de Aparici`` character / ``Destilerías Ayelo`` setting):

  - **SC-004** — a foreign-language source (``de``/``fr``, ≠ book ``es``) carries a
    ``translation``; every source carries an ``original_quote``.
  - **SC-005** — a conflicting-account pair maps to **two** findings, each with its
    own source; no silent collapse.
  - **SC-006** — a ``baja``-reliability finding is left **un-anchored** alongside a
    promoted ``alta`` finding whose anchor ``constrains`` a real bible entity.
  - plus ≥1 **open** finding.

Both the io-level conformance test (``tests/io/test_research_format.py``) and the
graph-build test (``tests/commands/graph/test_research_build.py``) read from this
module so the asserted claims/sources never drift between them.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

# --- "minimal" tier — relocated byte-identical from graph/conftest.py --------
# One `oficial`/`alta` Spanish source — book language is "es", so no translation
# (SC-004). See contracts/research-format.md and quickstart §0.
RESEARCH_SOURCES_MD = textwrap.dedent(
    """\
    ---
    sources:
      - name: "Registro TIP"
        reference: "https://www.interior.gob.es/tip"
        author: "Ministerio del Interior (España)"
        original_language: es
        type: oficial
        reliability: alta
        reliability_justification: "Fuente oficial primaria del organismo regulador."
        access_date: 2026-05-30
        original_quote: "El detective privado requiere la TIP expedida por el Ministerio."
    ---
    Notas sobre el registro de detectives.
    """
)

# One finding citing the source and bearing on the character, plus an anchor that
# promotes it, constrains the character, and carries a time-span.
RESEARCH_TOPIC_MD = textwrap.dedent(
    """\
    ---
    findings:
      - id: tip-required
        claim: "Un detective privado en España necesita la licencia TIP."
        asserted_by: agent
        bears_on: "Manuel de Aparici"
        sources: ["Registro TIP"]
    anchors:
      - promotes: tip-required
        constrains: "Manuel de Aparici"
        begin: 1995
        end: 2026
    ---
    Prosa legible sobre el tema de la licencia.
    """
)

# A single global open question (no claim/source — a truly open finding).
RESEARCH_INDEX_MD = textwrap.dedent(
    """\
    ---
    open_questions:
      - id: q-archivo-tip
    ---
    Mapa de temas y preguntas abiertas globales.
    """
)


# --- "rich" tier — iteration-14 SC-004/005/006 against the tiny-novel bible ---
#
# Named so both the io- and graph-level tests assert against the same strings
# (no drift). The constrained entity exists in the tiny-novel bible, so the
# promoted anchor resolves to a real triple rather than a soft warning.
CONSTRAINED_ENTITY = "Manuel de Aparici"
"""The bible character the promoted anchor ``constrains`` (SC-003)."""

PROMOTED_CLAIM = "Destilerías Ayelo fue fundada por Manuel de Aparici en 1871."
"""The ``alta``-source finding promoted to a binding anchor (SC-003)."""

CONFLICT_CLAIM_A = "La destilería cerró en el invierno de 1944 por falta de carbón."
CONFLICT_CLAIM_B = "La destilería siguió operando en 1944 pese a la escasez de carbón."
"""The two conflicting accounts of the same event — each its own source (SC-005)."""

BAJA_CLAIM = "Se rumoreaba que Aparici escondía oro en la bodega."
"""A ``baja``-reliability finding deliberately left un-anchored (SC-006)."""

OPEN_QUESTION_ID = "q-libro-de-cuentas"
"""The ``_index.md`` open question (an open finding with no claim/source)."""

FOREIGN_SOURCE_NAMES = ("Kriegstagebuch Ayelo", "Chronique de Lyon")
"""Sources whose ``original_language`` (``de``/``fr``) differs from book ``es`` —
each MUST carry a ``translation`` (SC-004)."""

RICH_TOPIC_FILENAME = "historia-destilerias.md"
"""The single rich-tier ``<topic>.md`` filename."""

_RICH_SOURCES_MD = textwrap.dedent(
    """\
    ---
    sources:
      - name: "Registro Mercantil de Valencia"
        reference: "AHPV, Registro Mercantil, t. IV, ff. 88-90"
        author: "Archivo Histórico Provincial de Valencia"
        original_language: es
        type: oficial
        reliability: alta
        reliability_justification: "Inscripción registral contemporánea de la sociedad."
        access_date: 2026-05-30
        original_quote: "Destilerías Ayelo queda inscrita, fundada por Manuel de Aparici en 1871."
      - name: "Kriegstagebuch Ayelo"
        reference: "BA-MA RH 2/1234, ff. 5-7"
        author: "Verwaltung Ayelo"
        original_language: de
        type: primaria
        reliability: alta
        reliability_justification: "Registro administrativo contemporáneo del invierno de 1944."
        access_date: 2026-05-31
        original_quote: "Die Brennerei wurde im Winter 1944 wegen Kohlemangels geschlossen."
        translation: "La destilería fue cerrada en el invierno de 1944 por falta de carbón."
      - name: "Chronique de Lyon"
        reference: "Bibliothèque municipale de Lyon, Fonds local, ms. 207"
        author: "Société d'histoire locale"
        original_language: fr
        type: secundaria
        reliability: media
        reliability_justification: "Crónica local redactada algunos años después de los hechos."
        access_date: 2026-05-31
        original_quote: "La distillerie fonctionna en 1944 malgré la pénurie de charbon."
        translation: "La destilería siguió funcionando en 1944 pese a la escasez de carbón."
      - name: "Panfleto Anónimo"
        reference: "Hemeroteca municipal, hoja suelta sin firma"
        author: "Anónimo"
        original_language: es
        type: periodística
        reliability: baja
        reliability_justification: "Hoja suelta sin firma ni contraste; rumor de la época."
        access_date: 2026-06-01
        original_quote: "Dicen que el viejo Aparici guardaba oro escondido en la bodega."
    ---
    Registro de fuentes para la historia de Destilerías Ayelo.
    """
)

_RICH_TOPIC_MD = textwrap.dedent(
    f"""\
    ---
    findings:
      - id: fundacion
        claim: "{PROMOTED_CLAIM}"
        asserted_by: author
        bears_on: "{CONSTRAINED_ENTITY}"
        sources: ["Registro Mercantil de Valencia"]
      - id: cierre-1944-de
        claim: "{CONFLICT_CLAIM_A}"
        bears_on: "{CONSTRAINED_ENTITY}"
        sources: ["Kriegstagebuch Ayelo"]
      - id: cierre-1944-fr
        claim: "{CONFLICT_CLAIM_B}"
        bears_on: "{CONSTRAINED_ENTITY}"
        sources: ["Chronique de Lyon"]
      - id: rumor-oro
        claim: "{BAJA_CLAIM}"
        sources: ["Panfleto Anónimo"]
      - id: q-proveedor-carbon
        open: true
    anchors:
      - promotes: fundacion
        constrains: "{CONSTRAINED_ENTITY}"
        begin: 1871
        end: 1871
    ---
    Historia de Destilerías Ayelo: fundación, cierre de 1944 (versiones en
    conflicto) y rumores sin contrastar.
    """
)

_RICH_INDEX_MD = textwrap.dedent(
    f"""\
    ---
    open_questions:
      - id: {OPEN_QUESTION_ID}
    ---
    # Índice de investigación

    ## Temas

    - [Historia de Destilerías Ayelo]({RICH_TOPIC_FILENAME})

    ## Preguntas abiertas globales

    - ¿Se conserva el libro de cuentas de la destilería?
    """
)


def write_research_fixture(research_dir: Path) -> None:
    """Write the **rich** ``bible/research/`` tree into ``research_dir``.

    Produces ``sources.md`` (4 sources, two foreign), one ``<topic>.md`` (the
    promoted finding, the conflicting pair, the un-anchored ``baja`` finding and an
    open finding, plus the single anchor) and ``_index.md`` (one open question).
    Every file is conformant — ``map_research()`` raises zero ``ResearchError``.
    """

    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "sources.md").write_text(_RICH_SOURCES_MD, encoding="utf-8")
    (research_dir / RICH_TOPIC_FILENAME).write_text(_RICH_TOPIC_MD, encoding="utf-8")
    (research_dir / "_index.md").write_text(_RICH_INDEX_MD, encoding="utf-8")
