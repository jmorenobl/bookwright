"""Map ``outline/units/*.md`` cards to ``NarrativeUnit`` / ``NarrativeFunction`` (G9/G10).

The outline sibling of :mod:`._bible_builders`: it reuses the generic
dir-walking engine (``_DirSpec`` / ``_map_single_dir``) and the value coercers
verbatim, turning each well-formed unit card into a :class:`NarrativeUnit` (G9)
whose named ``functions`` become slug-deduplicated :class:`NarrativeFunction`
(G10) entities and whose ``roles`` resolve by slug against the character-scoped
role nodes the character pass already materialized (``result.roles_index``).

The dependency is **one-way**: this module imports from :mod:`.bible` and
:mod:`._bible_builders`; neither imports this one (no cycle — Principle IX). It
mints no role entity, grows no ontology (G9/G10/``crm:P67_refers_to`` already
exist), and appends every entity/warning into the single ``MapResult`` the
``_graph`` pipeline already iterates (research D1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib.term import URIRef

from bookwright.golem import EmptySlugError, NarrativeFunction, NarrativeUnit
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
from .report import UnresolvedReference

#: The keys a unit card recognises; anything else is a soft ``unknown_keys`` warning.
UNIT_KEYS = frozenset({"name", "functions", "roles"})


def map_outline(
    project_root: Path,
    outline_dir: Path,
    uri_base: str,
    result: MapResult,
) -> None:
    """Append the ``outline/units/`` pass into ``result`` (data-model § Entities).

    Walks ``outline_dir / "units"`` with the generic one-entity-per-file engine,
    minting/deduping ``NarrativeFunction`` entities and resolving ``roles`` against
    ``result.roles_index`` (populated by the character pass). A no-op when the
    directory is absent, so a project without unit cards builds an identical graph
    (FR-009 / SC-006).
    """
    ctx = _MapContext(
        project_root=project_root,
        result=result,
        collisions=_Collisions(),
        slug_index={},
        roles_index=result.roles_index,
        functions_index={},
    )
    _map_single_dir(
        ctx,
        _DirSpec(
            directory=outline_dir / "units",
            concept="NarrativeUnit",
            builder=lambda meta, rp: _build_unit(uri_base, ctx, meta, rp),
            allowed_keys=UNIT_KEYS,
            index=False,
            into_entity_index=False,
        ),
    )


def _build_unit(
    uri_base: str, ctx: _MapContext, metadata: dict[str, Any], relpath: str
) -> NarrativeUnit:
    """Build one ``NarrativeUnit`` from a card's ``name`` / ``functions`` / ``roles``.

    All slugging (the only operations that can raise and so skip the card) happens
    **before** any function is minted or any role warning recorded, so a card with
    unusable front-matter contributes nothing but its ``skipped`` entry (R2, the
    ordering invariant of research D3).
    """
    name = _require_name(metadata)
    make_slug(name)  # validate the identity slugs before committing any state
    function_slugs = _distinct_slugs(_coerce_str_list(metadata.get("functions"), "functions"))
    role_slugs = _distinct_slugs(_coerce_str_list(metadata.get("roles"), "roles"))

    functions = _mint_functions(uri_base, ctx, function_slugs, relpath)
    roles = _resolve_roles(ctx, role_slugs, name, relpath)
    return NarrativeUnit(uri_base=uri_base, name=name, functions=functions, roles=roles)


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
    """
    functions: list[NarrativeFunction] = []
    for slug, raw in slugs:
        function = ctx.functions_index.get(slug)
        if function is None:
            function = NarrativeFunction(uri_base=uri_base, name=raw)
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
