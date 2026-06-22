"""``setting_continuity`` — contradicting descriptors for one setting (FR-017, D4).

A small built-in **contradiction lexicon** of antonym groups (e.g. *coastal* /
*inland*). When the same setting is described with two terms from one group in
**different files**, that is a continuity warning citing both locations. Heuristic
and LLM-free, so it defaults to ``warning`` — it never gates CI.
"""

from __future__ import annotations

import re
from typing import ClassVar

from bookwright.indexers import Indexer
from bookwright.io.prose import ProseView
from bookwright.validation.base import Severity, ValidationContext, Violation

# Antonym groups: two terms from one group on one setting, in different files, clash.
_LEXICON: tuple[tuple[str, ...], ...] = (
    ("coastal", "inland"),
    ("costera", "costero", "interior"),
    ("urban", "rural"),
    ("urbana", "urbano", "rural"),
    ("mountainous", "flat"),
    ("montañosa", "montañoso", "llana", "llano"),
    ("tropical", "arctic"),
    ("desert", "forest"),
    ("desierto", "bosque"),
)
# Word-boundary matcher per lexicon term, compiled once at import (not per line).
_TERM_PATTERNS: dict[str, re.Pattern[str]] = {
    term: re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    for group in _LEXICON
    for term in group
}


class SettingContinuity:
    """Flags a setting tagged with mutually-exclusive descriptors across files."""

    name: ClassVar[str] = "setting_continuity"
    severity_default: ClassVar[Severity] = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        # The whole-file gate stays over the full text (FR-009); built once and shared
        # across every setting (the mapping is loop-invariant).
        texts = dict(project.manuscript_files())
        view = project.manuscript_view()
        out: list[Violation] = []
        for setting_name, _ in project.setting_names():
            out.extend(self._check_setting(setting_name, texts, view))
        return out

    def _check_setting(
        self,
        setting_name: str,
        texts: dict[str, str],
        view: tuple[tuple[str, ProseView], ...],
    ) -> list[Violation]:
        name_re = re.compile(rf"\b{re.escape(setting_name)}\b", re.IGNORECASE)
        # term → (relpath, line) of its first occurrence in a file mentioning the setting.
        occurrences: dict[str, tuple[str, int]] = {}
        for relpath, prose in view:
            if not name_re.search(texts[relpath]):
                continue
            # Per-line scan reads RAW: block-prefix stripping is inert for the
            # `\bterm\b` lexicon, so findings + line numbers are identical (D7).
            for line in prose:
                for term, pattern in _TERM_PATTERNS.items():
                    if term in occurrences:
                        continue
                    if pattern.search(line.raw):
                        occurrences[term] = (relpath, line.number)

        out: list[Violation] = []
        for group in _LEXICON:
            present = [term for term in group if term in occurrences]
            clash = _first_cross_file_pair(present, occurrences)
            if clash is None:
                continue
            (term_a, loc_a), (term_b, loc_b) = clash
            src_a, line_a = loc_a
            src_b, line_b = loc_b
            out.append(
                Violation(
                    validator=self.name,
                    severity=Severity.warning,
                    message=(
                        f"setting '{setting_name}' is described as '{term_a}' "
                        f"({src_a}:{line_a}) and '{term_b}' ({src_b}:{line_b}) — "
                        "contradicting descriptors across files"
                    ),
                    source=f"{src_a}:{line_a}",
                    triples=(),
                )
            )
        return out


def _first_cross_file_pair(
    present: list[str], occurrences: dict[str, tuple[str, int]]
) -> tuple[tuple[str, tuple[str, int]], tuple[str, tuple[str, int]]] | None:
    """The first pair of present terms whose recorded files differ (sorted, D8)."""
    for i in range(len(present)):
        for j in range(i + 1, len(present)):
            a, b = present[i], present[j]
            if occurrences[a][0] != occurrences[b][0]:
                return (a, occurrences[a]), (b, occurrences[b])
    return None
