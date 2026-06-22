"""``focalization`` — prose vs. the declared narrative voice (FR-018, research D5).

Reads the constitution's narrative-voice declaration (Spanish "Voz narrativa" or
English "Narrative voice", case-insensitive) for the declared grammatical person and,
if a bible character is named there, the focal character. Then flags two heuristic
breaks, LLM-free, defaulting to ``warning``:

* first-person pronouns outside dialogue when **third person** is declared,
* interiority verbs attached to a **non-focal** bible character (head-hopping) under
  **third-person-limited**.

When there is no usable narrative voice to read, the validator raises
``NotEvaluated`` (iteration 040) rather than returning ``[]`` — so a silently dormant
focalization (DEBT-004) can no longer read as green. There are four distinct causes,
each with its own reason: (i) no constitution, (ii) a constitution that declares no
voice, (iii) an unanswered ``[PENDING]`` placeholder, (iv) a declaration that names no
grammatical person. A usable first/third person stays **evaluated** (FR-008).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from bookwright.indexers import Indexer
from bookwright.io.prose import ProseView, is_placeholder
from bookwright.validation.base import NotEvaluated, Severity, ValidationContext, Violation

_LABEL = r"(?:voz narrativa|narrative voice)"
# The declaration, recognized on a line whose leading block prefix the seam already
# stripped. Optional emphasis runs (`**`/`*`/`_`) are tolerated around the label —
# `**` precedes `*` in the alternation so the longest run is consumed; the label
# carries no `*`/`_`, so the emphasis groups cannot bleed into the label or body
# (contract C4). The `(?P<body>.+)$` capture is unchanged, so the parsed body is
# byte-identical to the bare `Voz narrativa: …` form (C4.1).
_DECLARATION = re.compile(
    r"(?i)^\s*(?:\*\*|\*|_)*\s*(?:voz narrativa|narrative voice)"
    r"(?:\*\*|\*|_)*\s*:\s*(?P<body>.+)$"
)
_THIRD = re.compile(r"(?i)\b(tercera|third)\b")
_FIRST = re.compile(r"(?i)\b(primera|first)\b")
_LIMITED = re.compile(r"(?i)\b(limitada|limitado|limited)\b")

# First-person markers we treat as a voice break outside dialogue (conservative).
_FIRST_PERSON = re.compile(r"(?i)(?<![\wáéíóúñ])(yo|nosotros|nosotras|i|we)(?![\wáéíóúñ])")
# Lines that are dialogue (Spanish em-dash openers or quotation marks) are exempt.
# Spanish typography (en/em dashes, angle + curly quotes) is intentional here.
_DIALOGUE_PREFIX = ("—", "–", "-", '"', "«", "“", "'", "‘")  # noqa: RUF001
# Interiority verbs — third-person reports of a character's inner life.
_INTERIORITY = re.compile(
    r"(?i)(?<![\wáéíóúñ])"
    r"(pensó|sintió|supo|recordó|creyó|temió|imaginó|comprendió|deseó|"
    r"thought|felt|knew|remembered|believed|feared|wondered|realized|realised|wished)"
    r"(?![\wáéíóúñ])"
)


@dataclass(frozen=True)
class _Declaration:
    person: str | None  # "first" | "third" | None
    limited: bool
    focal: str | None  # bible character named in the declaration, if any


class Focalization:
    """Flags prose that breaks the declared narrative person / focal character."""

    name: ClassVar[str] = "focalization"
    severity_default: ClassVar[Severity] = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        constitution = project.constitution_view()
        if not constitution:  # (i) no constitution file to read at all
            raise NotEvaluated("there is no constitution to read the narrative voice from")
        character_names = [name for name, _ in project.character_names()]
        # (ii) no declaration / (iii) a [PENDING] placeholder both raise inside the parse.
        declaration = _parse_declaration(constitution, character_names)
        if declaration.person is None:  # (iv) a declaration that names no grammatical person
            raise NotEvaluated(
                "the narrative-voice declaration names no grammatical person "
                "(neither first nor third)"
            )

        view = project.manuscript_view()
        out: list[Violation] = []
        if declaration.person == "third":
            out.extend(self._first_person_breaks(view))
            if declaration.limited:
                out.extend(self._head_hopping(view, character_names, declaration.focal))
        return out

    def _first_person_breaks(self, view: tuple[tuple[str, ProseView], ...]) -> list[Violation]:
        out: list[Violation] = []
        for relpath, prose in view:
            for line in prose:
                # Dialogue / first-person scans read RAW so the dialogue-prefix
                # exemption is byte-for-byte unchanged from the original line form (C6.2).
                if _is_dialogue(line.raw):
                    continue
                match = _FIRST_PERSON.search(line.raw)
                if match:
                    out.append(
                        Violation(
                            validator=self.name,
                            severity=Severity.warning,
                            message=(
                                f"first-person marker '{match.group(1)}' outside dialogue, but "
                                "the constitution declares a third-person narrative voice"
                            ),
                            source=f"{relpath}:{line.number}",
                            triples=(),
                        )
                    )
                    break  # one finding per file (citing the first break)
        return out

    def _head_hopping(
        self,
        view: tuple[tuple[str, ProseView], ...],
        character_names: list[str],
        focal: str | None,
    ) -> list[Violation]:
        non_focal = sorted(n for n in character_names if n != focal)
        seen: set[str] = set()
        out: list[Violation] = []
        for relpath, prose in view:
            for line in prose:
                if not _INTERIORITY.search(line.raw):
                    continue
                for name in non_focal:
                    if name in seen:
                        continue
                    if re.search(rf"\b{re.escape(name)}\b", line.raw):
                        seen.add(name)
                        out.append(
                            Violation(
                                validator=self.name,
                                severity=Severity.warning,
                                message=(
                                    f"interiority attributed to '{name}', a non-focal character, "
                                    "under a third-person-limited narrative voice (head-hopping)"
                                ),
                                source=f"{relpath}:{line.number}",
                                triples=(),
                            )
                        )
        return out


def _parse_declaration(view: ProseView, character_names: list[str]) -> _Declaration:
    """Parse the constitution's narrative-voice declaration.

    Raises :class:`NotEvaluated` for the two "could not read a voice" causes the
    constitution is present for: (ii) no line declares a voice, and (iii) the
    declaration is still an unanswered ``[PENDING: …]`` placeholder (FR-008). A parsed
    declaration is returned even when it names no grammatical person — the caller routes
    that (iv) case, since it can also carry a focal character.
    """
    match = next(
        (m for prose_line in view if (m := _DECLARATION.match(prose_line.normalized)) is not None),
        None,
    )
    if match is None:  # (ii) a constitution present, but it declares no narrative voice
        raise NotEvaluated("the constitution does not declare a narrative voice")
    body = match.group("body")
    if is_placeholder(body):  # (iii) an unanswered `[PENDING: …]` placeholder (FR-008b)
        raise NotEvaluated("the narrative-voice declaration is still unanswered ([PENDING])")
    person: str | None = None
    if _THIRD.search(body):
        person = "third"
    elif _FIRST.search(body):
        person = "first"
    focal = next(
        (
            name
            for name in sorted(character_names, key=len, reverse=True)
            if re.search(rf"\b{re.escape(name)}\b", body)
        ),
        None,
    )
    return _Declaration(person=person, limited=bool(_LIMITED.search(body)), focal=focal)


def _is_dialogue(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith(_DIALOGUE_PREFIX)
