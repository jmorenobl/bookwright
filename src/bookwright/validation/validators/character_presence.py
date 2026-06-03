"""``character_presence`` — bible roster vs. manuscript mentions (FR-016, research D3).

Two directions, split by severity so a heuristic false positive can never fail CI:

* a bible character **never** mentioned in the manuscript → orphan finding at
  **error** (deterministic — the name and the prose are both authored),
* a proper-noun candidate in the prose with **no** bible entry → unknown-mention at
  **warning** (a pinned, conservative heuristic — no NER).

Unknown mentions are collapsed per distinct name (one finding citing the first
occurrence), never multiplied per mention (edge case).
"""

from __future__ import annotations

import re
from typing import ClassVar

from bookwright.golem.slug import make_slug
from bookwright.indexers import Indexer
from bookwright.validation.base import Severity, ValidationContext, Violation

# Pinned proper-noun candidate: a capitalized word of ≥3 letters (D3). Accent-aware
# for Spanish prose; matches single tokens (multi-word names are caught token-wise).
_CANDIDATE = re.compile(r"[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]{2,}")
# Sentence-ending punctuation: a capital right after one of these (or at line start)
# is grammatical, not necessarily a proper noun — excluded (conservative, D3).
_SENTENCE_END = frozenset(".!?¿¡")
_MIN_TOKEN_LEN = 3  # shortest name token worth matching as a standalone word.
# Common capitalized non-names we never treat as a character mention (pinned stop-set).
_STOP_WORDS = frozenset(
    {
        # Spanish weekdays / months / frequent sentence openers.
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
        "entonces",
        "cuando",
        "aunque",
        "pero",
        "porque",
        "tambien",
        "despues",
        "antes",
        "ahora",
        "nunca",
        "siempre",
        "quiza",
        "quizas",
        "acaso",
        # English weekdays / months / openers.
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
        "then",
        "when",
        "although",
        "because",
        "after",
        "before",
        "however",
        "perhaps",
    }
)


class CharacterPresence:
    """Cross-checks the bible character roster against manuscript proper nouns."""

    name: ClassVar[str] = "character_presence"
    severity_default: ClassVar[Severity] = Severity.error

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        roster = project.character_names()
        files = project.manuscript_files()
        roster_slugs = _roster_slugs(roster)

        out: list[Violation] = []
        out.extend(self._orphans(roster, files))
        out.extend(self._unknown_mentions(files, roster_slugs))
        return out

    def _orphans(
        self,
        roster: tuple[tuple[str, str], ...],
        files: tuple[tuple[str, str], ...],
    ) -> list[Violation]:
        out: list[Violation] = []
        for name, relpath in roster:
            if not _is_mentioned(name, files):
                out.append(
                    Violation(
                        validator=self.name,
                        severity=Severity.error,
                        message=(
                            f"character '{name}' is defined in the bible but never "
                            "mentioned in the manuscript"
                        ),
                        source=relpath,
                        triples=(),
                    )
                )
        return out

    def _unknown_mentions(
        self,
        files: tuple[tuple[str, str], ...],
        roster_slugs: frozenset[str],
    ) -> list[Violation]:
        # slug → (display name, first "relpath:line"); first occurrence wins.
        first_seen: dict[str, tuple[str, str]] = {}
        for relpath, text in files:
            for lineno, line in enumerate(text.splitlines(), start=1):
                for match in _CANDIDATE.finditer(line):
                    token = match.group(0)
                    slug = make_slug(token)
                    if (
                        slug in roster_slugs
                        or slug in first_seen
                        or slug in _STOP_WORDS
                        or _is_sentence_initial(line, match.start())
                    ):
                        continue
                    first_seen[slug] = (token, f"{relpath}:{lineno}")
        out: list[Violation] = []
        for _, (token, source) in sorted(first_seen.items()):
            out.append(
                Violation(
                    validator=self.name,
                    severity=Severity.warning,
                    message=(
                        f"proper noun '{token}' appears in the manuscript but has no "
                        "bible entry (heuristic — may be a place or organization)"
                    ),
                    source=source,
                    triples=(),
                )
            )
        return out


def _roster_slugs(roster: tuple[tuple[str, str], ...]) -> frozenset[str]:
    """Slugs for every roster name and each of its tokens (so a surname matches)."""
    slugs: set[str] = set()
    for name, _ in roster:
        slugs.add(make_slug(name))
        for token in name.split():
            candidate = make_slug(token)
            if candidate:
                slugs.add(candidate)
    return frozenset(slugs)


def _is_mentioned(name: str, files: tuple[tuple[str, str], ...]) -> bool:
    """Whether ``name`` (full phrase or any ≥3-letter token) appears as a word."""
    patterns = [re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)]
    patterns += [
        re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)
        for token in name.split()
        if len(token) >= _MIN_TOKEN_LEN
    ]
    return any(pattern.search(text) for pattern in patterns for _, text in files)


def _is_sentence_initial(line: str, start: int) -> bool:
    """Whether the match at ``start`` opens a sentence (capitalization is grammatical)."""
    prefix = line[:start].rstrip()
    if not prefix:
        return True
    return prefix[-1] in _SENTENCE_END
