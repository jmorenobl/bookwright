"""``narrative_structure`` — structural-continuity checks over the v0.4 layer.

The first consumer of the Propp/Greimas narrative-structure layer (iterations
028-030). Two rules, both LLM-free and advisory (``warning``, never gates CI):

- **Rule a — orphan beat**: a ``G9_Narrative_Unit`` that is a member of no
  ``G7_Narrative_Sequence``, answered purely by SPARQL ``NOT EXISTS`` over the
  derived graph (``queries.load_orphan_units``). The clean demonstration that the
  structural layer is SPARQL-citable.
- **Rule c — unresolved role**: a unit card whose ``roles:`` names a slug
  resolving to no character role. The graph carries no edge for this soft miss, so
  the finding is re-surfaced from the structured ``UnresolvedReference`` records the
  outline ingestion already emits, reached through ``ValidationContext.outline()``.

Auto-discovered by the registry's ``pkgutil`` scan (no hand-registration, FR-002),
read-only and deterministic (FR-008), and it adds no class or property to the frozen
ontology (FR-012).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from bookwright.golem import NarrativeUnit
from bookwright.indexers import Indexer
from bookwright.validation import queries
from bookwright.validation.base import Severity, ValidationContext, Violation

if TYPE_CHECKING:
    from bookwright.io.bible import MapResult


class NarrativeStructure:
    """Flags orphan beats (Rule a) and unresolved role references (Rule c)."""

    name: ClassVar[str] = "narrative_structure"
    severity_default: ClassVar[Severity] = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        return self._orphan_beats(indexer) + self._unresolved_roles(project, indexer)

    def _orphan_beats(self, indexer: Indexer) -> list[Violation]:
        """Rule a: one finding per ``G9`` unit belonging to no ``G7`` sequence (FR-005).

        Names the unit by its human authored ``rdfs:label`` (carried alongside the URI
        by the widened query, FR-003), falling back to the URI slug only when the graph
        carries no label — the impossible-by-construction floor (FR-004).
        """
        out: list[Violation] = []
        for unit_uri, label in queries.load_orphan_units(indexer):
            slug = unit_uri.rsplit("/", 1)[-1]
            identifier = _unit_identifier(label, slug)
            out.append(
                Violation(
                    validator=self.name,
                    severity=Severity.warning,
                    message=(
                        f"narrative unit '{identifier}' belongs to no narrative sequence "
                        "(orphan beat)"
                    ),
                    source=queries.resolve_source(indexer, unit_uri),
                    triples=(),
                )
            )
        return out

    def _unresolved_roles(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        """Rule c: one finding per unresolved ``roles:`` reference in a unit card (FR-006).

        Re-surfaces the structured ``UnresolvedReference`` records the outline pass
        already emitted (the single source of truth for role resolution), filtered to
        the ``outline/units/`` cards so bible-level misses (``participants:`` /
        ``setting:``) never leak in (research D6). The card locator is recovered via
        the existing ``E13`` provenance path from the unit's URI, falling back to the
        card relpath when the loaded graph carries no provenance for it — a stale or
        unbuilt ``graph.ttl`` (research D7).
        """
        outline = project.outline()
        prefix = f"{project.manifest.paths.outline.rstrip('/')}/units/"
        unit_uris = _unit_uri_index(outline)
        out: list[Violation] = []
        references = sorted(
            (ref for ref in outline.unresolved_references if ref.path.startswith(prefix)),
            key=lambda ref: (ref.path, ref.entity, ref.name),
        )
        for ref in references:
            # Every outline-units ``UnresolvedReference`` carries ``entity=<unit name>``
            # for a unit ``map_outline`` also appended to ``outline.mapped`` — both come
            # from the one cached ``MapResult`` — so the unit URI is always indexed (D7).
            unit_uri = unit_uris[ref.entity]
            source = queries.resolve_source(indexer, unit_uri)
            slug = unit_uri.rsplit("/", 1)[-1]
            identifier = _unit_identifier(ref.entity, slug)
            out.append(
                Violation(
                    validator=self.name,
                    severity=Severity.warning,
                    message=(
                        f"narrative unit '{identifier}' references role '{ref.name}' "
                        "which resolves to no character role"
                    ),
                    source=source if source is not None else ref.path,
                    triples=(),
                )
            )
        return out


def _unit_identifier(name: str | None, slug: str) -> str:
    """The one place a ``G9`` unit is named in a finding message (FR-005, the 048
    ``anchor_handle`` precedent).

    Returns the human authored ``name`` when present, else the URI ``slug`` — the
    impossible-by-construction floor (FR-004). An empty-string label counts as missing
    (so a defensive ``""`` never prints an empty identifier). Both rules render through
    this single point, so the two surfaces cannot drift (SC-006).
    """
    return name if name else slug


def _unit_uri_index(outline: MapResult) -> dict[str, str]:
    """``unit name → URI`` for every ``NarrativeUnit`` in the outline ``MapResult`` (D7)."""
    return {
        mapped.entity.name: str(mapped.entity.uri)
        for mapped in outline.mapped
        if isinstance(mapped.entity, NarrativeUnit)
    }
