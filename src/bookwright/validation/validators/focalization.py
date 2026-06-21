"""``focalization`` — prose vs. the declared narrative voice (FR-018, research D5).

Reads the constitution's narrative-voice declaration (Spanish "Voz narrativa" or
English "Narrative voice", case-insensitive) for the declared grammatical person and,
if a bible character is named there, the focal character. Then flags two heuristic
breaks, LLM-free, defaulting to ``warning``:

* first-person pronouns outside dialogue when **third person** is declared,
* interiority verbs attached to a **non-focal** bible character (head-hopping) under
  **third-person-limited**.

No parsable declaration → zero findings (edge case).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from bookwright.indexers import Indexer
from bookwright.validation.base import Severity, ValidationContext, Violation

_LABEL = r"(?:voz narrativa|narrative voice)"
# The declaration, recognized on an already-normalized (markdown-stripped) line.
_DECLARATION = re.compile(rf"(?i)^\s*{_LABEL}\s*:\s*(?P<body>.+)$")
# One line-leading bullet/blockquote marker + trailing whitespace (the whitespace
# distinguishes a list bullet `* Voz…` from an emphasis run `*Voz…*`).
_BULLET = re.compile(r"^\s*[-*+>]\s+")
# A leading emphasis run (before the label): `**`, `*`, or `_`, repeated.
_LEAD_EMPHASIS = re.compile(r"^\s*(?:\*\*|\*|_)+")
# An emphasis run sitting between the label and its colon (anchored to the label
# so the declaration *body* is never touched, FR-006).
_CLOSE_EMPHASIS = re.compile(rf"(?i)^(?P<label>\s*{_LABEL})(?:\*\*|\*|_)+(?=\s*:)")
# An unanswered placeholder body: *solely* a `[PENDING: …]` token (case-insensitive
# keyword, optional surrounding whitespace). The full `^…$` anchor means real text
# before OR after the token keeps the body a real declaration (FR-002, contract C1-C5).
_PENDING_ONLY = re.compile(r"(?i)^\s*\[pending\b[^\]]*\]\s*$")
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
        constitution = project.constitution_text()
        if constitution is None:
            return []
        character_names = [name for name, _ in project.character_names()]
        declaration = _parse_declaration(constitution, character_names)
        if declaration is None or declaration.person is None:
            return []

        files = project.manuscript_files()
        out: list[Violation] = []
        if declaration.person == "third":
            out.extend(self._first_person_breaks(files))
            if declaration.limited:
                out.extend(self._head_hopping(files, character_names, declaration.focal))
        return out

    def _first_person_breaks(self, files: tuple[tuple[str, str], ...]) -> list[Violation]:
        out: list[Violation] = []
        for relpath, text in files:
            for lineno, line in enumerate(text.splitlines(), start=1):
                if _is_dialogue(line):
                    continue
                match = _FIRST_PERSON.search(line)
                if match:
                    out.append(
                        Violation(
                            validator=self.name,
                            severity=Severity.warning,
                            message=(
                                f"first-person marker '{match.group(1)}' outside dialogue, but "
                                "the constitution declares a third-person narrative voice"
                            ),
                            source=f"{relpath}:{lineno}",
                            triples=(),
                        )
                    )
                    break  # one finding per file (citing the first break)
        return out

    def _head_hopping(
        self,
        files: tuple[tuple[str, str], ...],
        character_names: list[str],
        focal: str | None,
    ) -> list[Violation]:
        non_focal = sorted(n for n in character_names if n != focal)
        seen: set[str] = set()
        out: list[Violation] = []
        for relpath, text in files:
            for lineno, line in enumerate(text.splitlines(), start=1):
                if not _INTERIORITY.search(line):
                    continue
                for name in non_focal:
                    if name in seen:
                        continue
                    if re.search(rf"\b{re.escape(name)}\b", line):
                        seen.add(name)
                        out.append(
                            Violation(
                                validator=self.name,
                                severity=Severity.warning,
                                message=(
                                    f"interiority attributed to '{name}', a non-focal character, "
                                    "under a third-person-limited narrative voice (head-hopping)"
                                ),
                                source=f"{relpath}:{lineno}",
                                triples=(),
                            )
                        )
        return out


def _normalize_declaration_line(line: str) -> str:
    """Strip markdown markup around the narrative-voice label (FR-001/FR-002).

    Removes one line-leading bullet/blockquote marker, then a leading emphasis
    run, then an emphasis run between the label and its colon — each independently
    (no balance guard, per spec clarification). The declaration body is never
    touched, so the parsed ``_Declaration`` is identical to the bare form (R1).
    """
    line = _BULLET.sub("", line, count=1)
    line = _LEAD_EMPHASIS.sub("", line, count=1)
    line = _CLOSE_EMPHASIS.sub(r"\g<label>", line, count=1)
    return line


def _parse_declaration(text: str, character_names: list[str]) -> _Declaration | None:
    match = next(
        (
            m
            for line in text.splitlines()
            if (m := _DECLARATION.match(_normalize_declaration_line(line))) is not None
        ),
        None,
    )
    if match is None:
        return None
    body = match.group("body")
    if _PENDING_ONLY.match(body):
        return None  # an unanswered `[PENDING: …]` placeholder is no declaration (FR-002)
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
