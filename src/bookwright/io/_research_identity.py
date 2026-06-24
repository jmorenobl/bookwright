"""The authored identity records ``map_research`` carries per finding/anchor (020 research D2).

Extracted from ``research.py`` so that module stays under the Principle IV
500-line ceiling, mirroring ``core/_focus_block.py``. ``research.py`` builds the
records during its mapping passes and re-exports both dataclasses, so
``bookwright.io.research`` stays the import surface
(:mod:`bookwright.status.queries` joins graph projections back through them).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rdflib.term import URIRef


@dataclass(frozen=True)
class FindingIdentity:
    """One finding's corpus-stable identity (020 research D2).

    ``id`` is the authored YAML ``id`` (required, uniqueness-checked per file);
    ``uri`` is the minted entity URI — an **in-process join key** from graph
    projections back to authored identity, never serialized (it changes every
    build).
    """

    id: str
    relpath: str
    uri: str


@dataclass(frozen=True)
class AnchorIdentity:
    """One anchor's corpus-stable identity (020 research D2).

    ``promotes_id`` is the authored ``id`` of the promoted finding;
    ``constrains`` is the authored target name, ``"timeline"``, or ``None``
    when the anchor declared no target *or* its link was dropped as unresolved
    (D12 — the graph carries no ``bw:constrains`` triple either way). ``uri``
    is the minted in-process join key, never serialized.
    """

    promotes_id: str
    constrains: str | None
    relpath: str
    uri: str


def anchor_handle(promotes: str, constrains: str | None) -> str:
    """The author-facing handle for an anchor (048 research D2).

    The promoted finding id, plus ``-> <constrains>`` when the anchor declares a
    target (``constrains is not None``), else the promoted id alone. This is the
    **single** spelling of the handle: both :func:`bookwright.commands.status._anchor_line`
    (over an :class:`~bookwright.status.model.AnchorGap`) and the ``factual_anchor``
    validator (over an :class:`AnchorIdentity`) call it, so the two surfaces can
    never diverge in how they name the same anchor (FR-007/FR-009). Pure, total,
    no I/O.
    """
    target = f" -> {constrains}" if constrains is not None else ""
    return f"{promotes}{target}"


def is_timeline_ref(raw: object) -> bool:
    """Whether an authored ``constrains`` value names the timeline sentinel.

    The single spelling of the rule: ``research._resolve_constrains`` links the
    anchor to the timeline URI with it, and :func:`_constrains_identity`
    normalizes the authored identity with it — one predicate, no drift.
    """
    return isinstance(raw, str) and raw.strip() == "timeline"


def _constrains_identity(raw: Any, resolved: URIRef | None) -> str | None:
    """The authored ``constrains`` for an :class:`AnchorIdentity` (020 research D2).

    ``None`` both for an authored ``constrains: null`` and for a dropped link
    (the unresolved-target soft miss, D12) — in either case the graph carries no
    ``bw:constrains`` triple, so the identity mirrors what the anchor actually
    asserts. ``"timeline"`` is normalized from its stripped spelling.
    """
    if raw is None or resolved is None:
        return None
    name = str(raw)
    return "timeline" if is_timeline_ref(name) else name
