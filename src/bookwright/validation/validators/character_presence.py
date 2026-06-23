"""``character_presence`` — bible character roster vs. manuscript mentions (FR-003).

One direction only, deterministic and sound: a bible character **never** mentioned in
the manuscript is an orphan finding at **error** (the name and the prose are both
authored, so the absence is a fact, not a guess). This rule protects the CI gate.

The opposite, open-set direction — is every capitalized proper noun in the prose backed
by a bible entry? — used to live here as a ``warning`` heuristic. It was the NER problem
without NER, measured 100 % noise on real prose, and now lives in the honest abstainer
``character_unknown_mentions`` (issue #1, track A — honestidad).
"""

from __future__ import annotations

import re
from typing import ClassVar

from bookwright.indexers import Indexer
from bookwright.validation.base import NotEvaluated, Severity, ValidationContext, Violation

_MIN_TOKEN_LEN = 3  # shortest name token worth matching as a standalone word.


class CharacterPresence:
    """Flags every bible character that the manuscript never mentions (orphan → error)."""

    name: ClassVar[str] = "character_presence"
    severity_default: ClassVar[Severity] = Severity.error

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        roster = project.character_names()
        files = project.manuscript_files()
        if not roster and not files:  # nothing to cross-check in EITHER direction (FR-004)
            raise NotEvaluated(
                "there is no manuscript prose and no bible character roster to cross-check"
            )
        # An empty manuscript with a non-empty roster STAYS evaluated and still emits its
        # error-level orphan findings byte-for-byte — the rule that protects the gate.
        return self._orphans(roster, files)

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


def _is_mentioned(name: str, files: tuple[tuple[str, str], ...]) -> bool:
    """Whether ``name`` (full phrase or any ≥3-letter token) appears as a word."""
    patterns = [re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)]
    patterns += [
        re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)
        for token in name.split()
        if len(token) >= _MIN_TOKEN_LEN
    ]
    return any(pattern.search(text) for pattern in patterns for _, text in files)
