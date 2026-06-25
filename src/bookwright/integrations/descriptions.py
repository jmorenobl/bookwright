"""Authoritative `SKILL.md` `description` table (R1/R3, FR-004).

A pure, dependency-free data module: `SKILL_DESCRIPTIONS` maps each command name
to its bilingual ES/EN trigger-bearing description, and `get_description` is the
single authoritative lookup (with source-frontmatter fallback) where the
1024-char cap is asserted in **one** place.

In v0 the table mirrors the iteration-8 source frontmatter `description` verbatim
under a CI equality gate (SC-009): the dict is the authoritative read seam (where
the cap lives and where future per-skill tuning would land), while the gate makes
any divergence from the source an explicit, reviewed change — never silent drift.
"""

from __future__ import annotations

from bookwright.integrations.constants import SKILL_DESCRIPTION_MAX_LENGTH

SKILL_DESCRIPTIONS: dict[str, str] = {
    "bookwright-constitution": 'Define la constitución narrativa del libro: voz, tono, pacto con el lector, líneas rojas e invariantes de coherencia — el paso de configuración que va ANTES de la biblia. Build the book\'s narrative constitution: voice, tone, reader pact, red lines and coherence invariants — the setup step BEFORE the bible. Úsalo cuando el autor quiera fijar el tono, la voz o las reglas de su obra ("define el tono", "set the tone/voice", "establece las bases"). NO genera fichas de personajes ni localizaciones: eso es bookwright-bible, que va después.',
    "bookwright-bible": 'Genera la biblia del proyecto en una sola pasada: fichas de personajes, escenarios y localizaciones, cronología, relaciones, temas, glosario y subtramas — DESPUÉS de tener la constitución. Build the project bible in a single pass: character, setting and location sheets, timeline, relationships, themes, glossary and subplots — AFTER the constitution exists. Úsalo cuando el autor pida "fichas de mis personajes y localizaciones" / "character and location sheets", "puebla la biblia" / "build the bible". NO sirve para definir el tono o la voz: eso es bookwright-constitution, que va antes.',
    "bookwright-outline": 'Construye el esqueleto narrativo de la obra: arcos de personaje, estructura por actos y capítulos, y una sinopsis inicial, a partir de la constitución y la biblia. Build the book\'s narrative skeleton: character arcs, act/chapter structure and an initial synopsis, from the constitution and bible. Úsalo cuando el autor quiera "estructurar la trama", "diseñar los arcos" / "outline the plot", "design the arcs and structure". Trabaja al nivel de capítulos y arcos, no de escenas concretas (eso es bookwright-scenes).',
    "bookwright-scenes": 'Desglosa la estructura en una lista de escenas concretas, cada una con su función narrativa, personajes presentes, lugar y beats. Break the structure into a concrete scene list, each carrying its narrative function, characters present, location and beats. Úsalo cuando el autor quiera "desglosar los capítulos en escenas", "preparar la lista de escenas" / "break chapters into scenes", "plan the scene list" antes de redactar. Planifica escenas; NO redacta su prosa (eso es bookwright-draft).',
    "bookwright-draft": 'Redacta la prosa de una escena concreta (indicada por su scene_id) en el capítulo correcto del manuscrito, respetando la voz, la focalización y las restricciones de la constitución y la biblia. Draft the prose of a specific scene (given by its scene_id) into the correct manuscript chapter, honoring the voice, focalization and constraints from the constitution and bible. Úsalo cuando el autor diga "escribe/redacta la escena X" / "draft/write scene X". Es el único comando que produce prosa de manuscrito.',
    "bookwright-synopsis": 'Actualiza la sinopsis del proyecto: una versión corta (250–350 palabras) y una larga (1000–2000 palabras) que reflejan el estado actual de la trama. Update the project synopsis: a short version (250–350 words) and a long one (1000–2000 words) reflecting the current state of the plot. Úsalo cuando el autor pida "actualiza/genera la sinopsis", "resume la novela" / "update/write the synopsis", "summarize the plot". Regenera ambos resúmenes en cualquier momento del proyecto.',
    "bookwright-clarify": 'Revisa los artefactos del proyecto y devuelve una lista de preguntas abiertas que el autor debería resolver antes de seguir. Review the project artifacts and return a list of open questions the author should resolve before continuing. Úsalo cuando el autor pregunte "¿qué me falta por aclarar antes de seguir?", "¿qué dudas quedan?" / "what\'s still unclear?", "what do I need to decide next?". Es de solo lectura. Pregunta por DUDAS abiertas, NO comprueba la completitud de un artefacto concreto (eso es bookwright-checklist).',
    "bookwright-analyze": 'Revisa la consistencia cruzada PRE-redacción entre constitución, biblia, outline y escenas, y reporta contradicciones antes de empezar a escribir. Check PRE-draft cross-artifact consistency among constitution, bible, outline and scenes, reporting contradictions before any prose is written. Úsalo cuando el autor pregunte "¿es coherente mi planificación antes de redactar?" / "is my planning consistent before I start drafting?". Es de solo lectura y trabaja en fase PRE-draft. NO compara el manuscrito con la biblia (eso es post-draft: bookwright-continuity).',
    "bookwright-continuity": 'Revisa la consistencia POST-redacción del manuscrito frente a la biblia: cumplimiento de la biblia, coherencia de los arcos de personaje y de la línea de tiempo, personajes mencionados en la prosa pero sin ficha en bible/characters/, y head-hopping / rupturas de voz o de persona narrativa. Check POST-draft continuity of the manuscript against the bible: bible compliance, character-arc consistency, timeline coherence, characters used in the prose but undeclared (no sheet in bible/characters/), and head-hopping / voice or narrative-person breaks. Úsalo cuando el autor pida "revisa si mi manuscrito es coherente con la biblia" / "check my manuscript against the bible", "revisa si hay personajes sin declarar / sin ficha" / "check for undeclared / unbacked characters", o "revisa head-hopping / saltos de punto de vista / focalización rota" / "check for head-hopping / POV breaks". Es de solo lectura y trabaja en fase POST-draft. NO revisa la planificación antes de redactar (eso es pre-draft: bookwright-analyze).',
    "bookwright-checklist": 'Comprueba si UN artefacto concreto está completo: todas sus secciones presentes, sin marcadores [PENDING: …] sin resolver y sin placeholders vacíos. Check whether ONE named artifact is complete: all sections present, no unresolved [PENDING: …] markers, no empty placeholders. Úsalo cuando el autor pregunte "¿está completa mi constitución / esta ficha?" / "is this artifact complete?". Es de solo lectura. Mide COMPLETITUD de un artefacto, NO recoge las dudas abiertas del proyecto (eso es bookwright-clarify).',
    "bookwright-research": 'Investiga un tema del mundo real y lo documenta como hallazgos con procedencia completa (fuentes, citas en lengua original, fiabilidad) en bible/research/, marcando qué hallazgos son anclas que restringen la ficción. Research a real-world topic and document it as findings with full provenance (sources, original-language quotes, reliability) under bible/research/, marking which findings are binding anchors on the fiction. Úsalo cuando el autor pida "investiga <tema>", "documenta <tema> con fuentes", "preséntame fuentes sobre <tema>" / "research <topic>", "find sources on <topic>". NO verifica prosa ya escrita contra sus fuentes (eso es bookwright-verify, posterior) ni puebla fichas de personajes o localizaciones (eso es bookwright-bible).',
    "bookwright-verify": 'Verifica el manuscrito ya redactado contra las anclas de investigación: detecta pasajes que contradicen lo investigado — anacronismos, errores de procedimiento (algo ilegal o imposible en la ambientación) e inexactitudes culturales o lingüísticas. Verify the drafted manuscript against the research anchors: flag passages that contradict the research — anachronisms, procedural errors (something illegal or impossible in the setting) and cultural or linguistic inaccuracies. Úsalo cuando el autor pida "verifica si mi manuscrito contradice lo investigado" / "check my manuscript against my research". Es de solo lectura y trabaja en fase POST-draft. NO compara el manuscrito con la biblia (eso es bookwright-continuity) ni audita la integridad estructural de las anclas (eso es el validator factual_anchor).',
}


def get_description(name: str, fallback: str) -> str:
    """Authoritative lookup with source-frontmatter fallback (R3, FR-004).

    Returns `SKILL_DESCRIPTIONS[name]` when present, else `fallback` (the source
    frontmatter description). The 1024-char cap is *enforced* at runtime by
    ``lint_skill_md`` Rule 3 (which survives ``python -O``); the ``assert`` below
    is only a developer-time tripwire on the static table — over-cap is a coding
    error caught by tests (the SC-009 equality gate), never a user-data case.
    """

    result = SKILL_DESCRIPTIONS.get(name, fallback)
    assert len(result) < SKILL_DESCRIPTION_MAX_LENGTH, (
        f"description for {name!r} is {len(result)} chars, >= cap {SKILL_DESCRIPTION_MAX_LENGTH}"
    )
    return result
