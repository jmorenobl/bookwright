"""``focalization`` — prose vs. the declared narrative voice (FR-018, research D5).

Reads the constitution's narrative-voice declaration (Spanish "Voz narrativa" or
English "Narrative voice", case-insensitive) for the declared grammatical person.
Under a declared **third-person** voice it flags one heuristic break, LLM-free,
defaulting to ``warning``: first-person pronouns outside dialogue.

Head-hopping (interiority verbs attributed to a non-focal bible character) under
**third-person-limited / focalized** is irreducibly a semantic-judgment task (move 3):
the deterministic heuristic was measured nearly dormant on real prose (DEBT-014). So,
exactly as iteration 043 did with the open-set unknown-mention rule, the validator
**stops faking** the head-hopping check — but the deterministic first-person-break
check still works. Under a parseable limited-third voice the validator therefore returns
a **partial** result (``EvalResult``, form (c), iteration 050): it **runs**
``_first_person_breaks`` **and** declares the head-hopping abstention
(``Abstention``, ``kind=pending_capability``) in the **same** run. Iteration 045's
all-or-nothing ``raise NotEvaluated`` suppressed the still-working break check under a
focalized voice (a recorded coverage regression, DEBT-019); the partial-evaluation
contract closes it. The break check runs under third-person **limited and non-limited**.

The break check itself only matches the CLOSED explicit-subject-pronoun set
(``yo``/``nosotros``/``nosotras``/``i``/``we``); it is silent about Spanish pro-drop
verbal morphology (``Caminé``, ``Me senté``), an OPEN set no regex captures (DEBT-021).
That silence was the ``[]``-means-clean lie at the sub-check level. So under **both**
third-person branches the validator now also declares a ``first_person_recall``
``pending_capability`` abstention (``code="first_person_recall"``, iteration 053 — the
honesty half) so the recall ceiling is honestly visible; the move-3 **judgment** half
(its nudge, closing DEBT-021) is iteration 054.

When there is no usable narrative voice to read, the validator raises
``NotEvaluated`` (iteration 040) rather than returning ``[]`` — so a silently dormant
focalization (DEBT-004) can no longer read as green. There are four distinct causes,
each ``missing_input``: (i) no constitution, (ii) a constitution that declares no
voice, (iii) an unanswered ``[PENDING]`` placeholder, (iv) a declaration that names no
grammatical person. A usable first / non-limited-third person stays **evaluated**
(FR-008).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from bookwright.indexers import Indexer
from bookwright.io.prose import ProseView, is_placeholder
from bookwright.validation.base import (
    Abstention,
    EvalResult,
    NotEvaluated,
    NotEvaluatedKind,
    Severity,
    ValidationContext,
    Violation,
)

_HEAD_HOPPING_PENDING = (
    "head-hopping / interiority attribution requires semantic judgment (move 3); "
    "the deterministic heuristic was measured nearly dormant on real prose"
)
_FIRST_PERSON_RECALL_PENDING = (
    "full first-person recall requires semantic judgment (move 3); "
    "the deterministic check only covers the explicit subject pronoun"
)

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


@dataclass(frozen=True)
class _Declaration:
    person: str | None  # "first" | "third" | None
    limited: bool


class Focalization:
    """Flags prose that breaks the declared narrative person; abstains on head-hopping."""

    name: ClassVar[str] = "focalization"
    severity_default: ClassVar[Severity] = Severity.warning

    def validate(
        self, project: ValidationContext, indexer: Indexer
    ) -> list[Violation] | EvalResult:
        if project.constitution_text() is None:  # (i) no constitution file to read at all
            raise NotEvaluated("there is no constitution to read the narrative voice from")
        # A present-but-empty constitution is NOT cause (i): it has a file, it just
        # declares nothing — so it falls through to cause (ii) inside the parse, where
        # the empty view yields no declaration. (iii) a [PENDING] placeholder also raises
        # there.
        declaration = _parse_declaration(project.constitution_view())
        if declaration.person is None:  # (iv) a declaration that names no grammatical person
            raise NotEvaluated(
                "the narrative-voice declaration names no grammatical person "
                "(neither first nor third)"
            )

        if declaration.person == "third":
            # The deterministic first-person-break check (`_first_person_breaks`) only
            # covers the CLOSED explicit-subject-pronoun set (`yo`/`nosotros`/…/`i`/`we`);
            # it is blind to Spanish pro-drop verbal morphology (`Caminé`, `Me senté`), an
            # OPEN set no regex captures without reopening issue #1's whack-a-mole. So under
            # ANY third-person voice the validator declares that recall ceiling honestly
            # with a `pending_capability` abstention (DEBT-021 honesty half, iteration 053)
            # — the move-3 judgment half (the nudge) is iteration 054.
            recall = Abstention(
                _FIRST_PERSON_RECALL_PENDING,
                NotEvaluatedKind.pending_capability,
                code="first_person_recall",
            )
            if declaration.limited:
                # Head-hopping under a focalized voice is a move-3 semantic judgment; the
                # deterministic heuristic was measured nearly dormant on real prose, so the
                # validator abstains on it (iteration 045). But the deterministic
                # first-person-break check still works — so under limited-third the
                # validator RUNS that check AND declares BOTH the head-hopping and the
                # first-person-recall abstentions in the SAME run via a partial EvalResult
                # (form (c), iteration 050). The all-or-nothing suppression that hid the
                # break check under focalized voice (DEBT-019) is gone.
                return EvalResult(
                    self._first_person_breaks(project.manuscript_view()),
                    [
                        Abstention(
                            _HEAD_HOPPING_PENDING,
                            NotEvaluatedKind.pending_capability,
                            code="head_hopping",
                        ),
                        recall,
                    ],
                )
            # Third-person non-limited: the break check still runs, and the recall ceiling
            # is declared in the same partial result (was a bare list before iteration 053).
            return EvalResult(self._first_person_breaks(project.manuscript_view()), [recall])
        return []  # first person: nothing third-person to flag

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


def _parse_declaration(view: ProseView) -> _Declaration:
    """Parse the constitution's narrative-voice declaration.

    Raises :class:`NotEvaluated` for the two "could not read a voice" causes the
    constitution is present for: (ii) no line declares a voice, and (iii) the
    declaration is still an unanswered ``[PENDING: …]`` placeholder (FR-008). A parsed
    declaration is returned even when it names no grammatical person — the caller routes
    that (iv) case.
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
    return _Declaration(person=person, limited=bool(_LIMITED.search(body)))


def _is_dialogue(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith(_DIALOGUE_PREFIX)
