"""Map ``outline/units/*.md`` cards to ``NarrativeUnit`` / ``NarrativeFunction`` (G9/G10)
and assemble ``NarrativeSequence`` (G7) from their ``sequence``/``order`` keys.

The outline sibling of :mod:`._bible_builders`: it reuses the generic
dir-walking engine (``_DirSpec`` / ``_map_single_dir``) and the value coercers
verbatim, turning each well-formed unit card into a :class:`NarrativeUnit` (G9)
whose named ``functions`` become slug-deduplicated :class:`NarrativeFunction`
(G10) entities and whose ``roles`` resolve by slug against the character-scoped
role nodes the character pass already materialized (``result.roles_index``).

Each card may additionally declare two optional keys — ``sequence`` (the plot
line the unit joins) and ``order`` (its position in that line). These are **not**
attributes of the ``NarrativeUnit`` entity; instead each surviving, sequence-naming
card contributes a transient :class:`_SeqMember` record to a side-channel
accumulator, and a single assembly step — run **after** every card is built (the
"second step", research D1) — groups those records by sequence slug and mints one
:class:`NarrativeSequence` (G7) per group whose ``dlp:proper-part`` members are the
units, ordered ascending by ``order`` (research D1/D2/D3).

The dependency is **one-way**: this module imports from :mod:`.bible` and
:mod:`._bible_builders`; neither imports this one (no cycle — Principle IX). It
mints no role entity, grows no ontology (G7/G9/G10/``dlp:proper-part``/
``crm:P67_refers_to`` already exist), and appends every entity/warning into the
single ``MapResult`` the ``_graph`` pipeline already iterates (research D1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple

from rdflib.term import URIRef

from bookwright.golem import (
    EmptySlugError,
    NarrativeFunction,
    NarrativeSequence,
    NarrativeUnit,
)
from bookwright.golem.slug import make_slug

from ._bible_builders import (
    MappedEntity,
    MapResult,
    _coerce_str_list,
    _Collisions,
    _MapContext,
    _require_name,
)
from .bible import _DirSpec, _map_single_dir
from .errors import InvalidFrontmatterError
from .report import UnknownKey, UnresolvedReference
from .vocabularies import VocabularyIndex

#: The keys a unit card recognises; anything else is a soft ``unknown_keys`` warning.
#: ``sequence``/``order`` drive ``NarrativeSequence`` assembly only and are never
#: serialized onto the unit (iteration 029, data-model § Recognised keys).
UNIT_KEYS = frozenset({"name", "functions", "roles", "sequence", "order"})


class _SeqMember(NamedTuple):
    """One unit card's contribution to a narrative sequence — internal, never serialized.

    Collected during the per-file pass and consumed by the assembly step
    (data-model § Transient record). It exists only because ``sequence``/``order``
    are not attributes of the ``NarrativeUnit`` entity and so cannot be recovered
    from ``result.mapped`` after the pass.
    """

    seq_slug: str  # ``make_slug(sequence)`` — the grouping/dedup key (FR-002)
    seq_name: str  # the raw ``sequence`` value — display-name candidate (D4)
    order: int | None  # the ``order`` value; ``None`` when omitted (FR-005)
    unit_slug: str  # ``make_slug(unit name)`` — the tie-break key (FR-006)
    unit: NarrativeUnit  # the built member entity (becomes a ``units`` tuple item)
    relpath: str  # the card's project-relative path — provenance carrier (D5)


def map_outline(
    project_root: Path,
    outline_dir: Path,
    uri_base: str,
    result: MapResult,
    *,
    propp: VocabularyIndex | None = None,
) -> None:
    """Append the ``outline/units/`` pass into ``result`` (data-model § Entities).

    Walks ``outline_dir / "units"`` with the generic one-entity-per-file engine,
    minting/deduping ``NarrativeFunction`` entities and resolving ``roles`` against
    ``result.roles_index`` (populated by the character pass). Each card's
    ``sequence``/``order`` keys are collected into a closure-local accumulator
    during the pass and, **after** it returns, assembled into one
    ``NarrativeSequence`` (G7) per distinct sequence slug (the "second step",
    research D1). A no-op when the directory is absent, so a project without unit
    cards builds an identical graph (FR-009 / FR-011 / SC-006).

    When ``propp`` is supplied (the Propp vocabulary is active, iteration 030),
    each minted ``NarrativeFunction`` whose name matches a canonical Propp term
    carries a ``crm:P2_has_type`` link to it; with ``propp=None`` (the default,
    no vocabulary active) the graph is unchanged (FR-008/SC-003).
    """
    ctx = _MapContext(
        project_root=project_root,
        result=result,
        collisions=_Collisions(),
        slug_index={},
        roles_index=result.roles_index,
        functions_index={},
        propp=propp,
    )
    # The sequence-member side-channel: a list local to this call, captured by the
    # builder closure (research D1). Kept off the shared ``_MapContext`` so no
    # outline-only field leaks into the bible/outline context.
    members: list[_SeqMember] = []
    _map_single_dir(
        ctx,
        _DirSpec(
            directory=outline_dir / "units",
            concept="NarrativeUnit",
            builder=lambda meta, rp: _build_unit(uri_base, ctx, meta, rp, members),
            allowed_keys=UNIT_KEYS,
            index=False,
            into_entity_index=False,
        ),
    )
    _assemble_sequences(uri_base, members, result)


def _assemble_sequences(uri_base: str, members: list[_SeqMember], result: MapResult) -> None:
    """Group the collected members by sequence slug and mint one G7 per group (D1/D4/D5).

    Insertion-ordered grouping (insertion = sorted-glob order, so deterministic):
    each group's display ``name`` is the first card in glob order to name the slug
    (``group[0].seq_name``), its members are ordered by :func:`_member_sort_key` (a
    total order → byte-for-byte-stable tuple across builds), and the
    ``NarrativeSequence`` is appended with file-level provenance keyed to the first
    assembled member's card (``key_lines={}`` → no ``:line``, the minted-function
    precedent). An empty accumulator appends nothing, so an unsequenced project
    builds an identical graph (FR-002/003/010/011, research D5).
    """
    groups: dict[str, list[_SeqMember]] = {}
    for member in members:
        groups.setdefault(member.seq_slug, []).append(member)
    for group in groups.values():
        ordered = sorted(group, key=_member_sort_key)
        sequence = NarrativeSequence(
            uri_base=uri_base,
            name=group[0].seq_name,
            units=tuple(m.unit for m in ordered),
        )
        result.mapped.append(
            MappedEntity(entity=sequence, relpath=ordered[0].relpath, key_lines={})
        )


def _member_sort_key(member: _SeqMember) -> tuple[int, int, str]:
    """A total order over a sequence's members (FR-005/FR-006, data-model § Member ordering).

    Explicit-``order`` members sort first (group flag ``0``) by ``order`` then unit
    slug; order-less members sort last (group flag ``1``) by unit slug (D2/D3). The
    middle element is a fixed ``int`` in both branches so the keys stay mutually
    comparable under ``mypy --strict``; the slug tie-break makes the order total,
    so the assembled tuple is identical across builds (SC-003/SC-004).
    """
    if member.order is None:
        return (1, 0, member.unit_slug)
    return (0, member.order, member.unit_slug)


def _build_unit(
    uri_base: str,
    ctx: _MapContext,
    metadata: dict[str, Any],
    relpath: str,
    members: list[_SeqMember],
) -> NarrativeUnit:
    """Build one ``NarrativeUnit`` from ``name`` / ``functions`` / ``roles``, recording
    its sequence membership into ``members``.

    All operations that can raise — and so skip the card — happen **before** any
    state mutation: identity/sequence slugging, the ``functions``/``roles`` list
    coercion, and the ``sequence``/``order`` coercion. So a card with unusable
    front-matter (a non-string ``sequence``, a non-int ``order``) contributes
    nothing but its ``skipped`` entry with no partial sequence membership and no
    stray soft note (R2, the skip-invariant of research D7).

    The ``_SeqMember`` is appended **last**, after the unit is built, and only when
    a usable ``sequence`` is present; a usable ``order`` with no ``sequence`` to
    position it is a soft ``UnknownKey "order"`` note (FR-008, research D8).
    """
    name = _require_name(metadata)
    unit_slug = make_slug(name)  # validate the identity slug before committing any state
    function_slugs = _distinct_slugs(_coerce_str_list(metadata.get("functions"), "functions"))
    role_slugs = _distinct_slugs(_coerce_str_list(metadata.get("roles"), "roles"))
    sequence = _coerce_sequence(metadata.get("sequence"))
    order = _coerce_order(metadata.get("order"))
    # The sequence-name slug is an identity slug (a G7 is minted from it), validated
    # up front like the unit's own name: an unsluggable name raises EmptySlugError →
    # the card is skipped, never half-recorded.
    seq_slug = make_slug(sequence) if sequence is not None else None

    functions = _mint_functions(uri_base, ctx, function_slugs, relpath)
    roles = _resolve_roles(ctx, role_slugs, name, relpath)
    unit = NarrativeUnit(uri_base=uri_base, name=name, functions=functions, roles=roles)

    if sequence is not None and seq_slug is not None:
        members.append(
            _SeqMember(
                seq_slug=seq_slug,
                seq_name=sequence,
                order=order,
                unit_slug=unit_slug,
                unit=unit,
                relpath=relpath,
            )
        )
    elif order is not None:
        # ``order`` with nothing to position is a soft authoring nicety, never fatal
        # — mirrors ``_resolve_interval``'s redundant-``date`` handling (research D8).
        ctx.result.unknown_keys.append(UnknownKey(path=relpath, key="order"))
    return unit


def _coerce_sequence(value: Any) -> str | None:
    """Coerce a card's ``sequence`` value (mirrors ``_resolve_setting``'s contract).

    ``None`` / blank / whitespace-only → ``None`` (no membership, FR-004); a
    non-string is unusable front-matter (``InvalidFrontmatterError`` → the card is
    skipped, FR-007); else the raw string (its slug is the grouping key).
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidFrontmatterError("", "`sequence` must be a string")
    if not value.strip():
        return None
    return value


def _coerce_order(value: Any) -> int | None:
    """Coerce a card's ``order`` value (mirrors ``_coerce_year``: rejects ``bool``).

    Absent / ``None`` → ``None`` (member placed last, FR-005). A non-integer —
    including ``bool``, ``float``, ``str`` or ``list`` — is unusable front-matter
    (``InvalidFrontmatterError`` → the card is skipped, FR-007); else the int.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidFrontmatterError("", "`order` must be an integer")
    return value


def _distinct_slugs(names: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """Ordered ``(slug, original-name)`` pairs, deduplicated by slug within the card.

    An unsluggable name (empty / punctuation-only) contributes no slug — it is
    dropped here rather than aborting the card, so a stray blank function/role name
    never minted/warned. Computed up front so no minting precedes a possible skip.
    """
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in names:
        try:
            slug = make_slug(raw)
        except EmptySlugError:
            continue
        if slug not in seen:
            seen.add(slug)
            pairs.append((slug, raw))
    return tuple(pairs)


def _mint_functions(
    uri_base: str,
    ctx: _MapContext,
    slugs: tuple[tuple[str, str], ...],
    relpath: str,
) -> tuple[NarrativeFunction, ...]:
    """Mint-or-reuse one ``NarrativeFunction`` per distinct function slug (C2/C3).

    Deduplicated across **all** units via ``ctx.functions_index``: the first card to
    introduce a slug appends the function's ``MappedEntity`` (so its ``rdf:type``
    triple is emitted once); later cards reuse the stored entity.

    When ``ctx.propp`` is active, the first card to introduce a slug also fixes the
    function's ``type_uri`` (the matched Propp term, or ``None`` on no-match), so
    the typing is deterministic and shared by every later card that reuses the
    slug (iteration 030, FR-004/FR-006).
    """
    functions: list[NarrativeFunction] = []
    for slug, raw in slugs:
        function = ctx.functions_index.get(slug)
        if function is None:
            type_uri = ctx.propp.resolve(raw) if ctx.propp is not None else None
            function = NarrativeFunction(uri_base=uri_base, name=raw, type_uri=type_uri)
            ctx.functions_index[slug] = function
            ctx.result.mapped.append(MappedEntity(entity=function, relpath=relpath, key_lines={}))
        functions.append(function)
    return tuple(functions)


def _resolve_roles(
    ctx: _MapContext,
    slugs: tuple[tuple[str, str], ...],
    entity_name: str,
    relpath: str,
) -> tuple[URIRef, ...]:
    """Resolve role slugs against the character-scoped role index — never mint (C4/C5).

    One unit→role edge per matching character role node; a slug matching no character
    role is a single soft :class:`UnresolvedReference` (no edge, the unit still built).
    """
    resolved: list[URIRef] = []
    for slug, raw in slugs:
        matches = ctx.roles_index.get(slug, [])
        if matches:
            resolved.extend(matches)
        else:
            ctx.result.unresolved_references.append(
                UnresolvedReference(path=relpath, entity=entity_name, name=raw)
            )
    return tuple(resolved)
