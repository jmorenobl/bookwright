"""The deferral registry: which GOLEM concepts are modelled but not yet fed.

Two of the thirteen :data:`bookwright.golem.CONCEPTS` have no authored-text
ingestion path today — they are *modelled* (a frozen class, a ``CLASS_IRI``
entry) but never *materialized* by any builder over the ingested source trees
(``bible/*.md`` and, since iteration 028, ``outline/units/*.md`` — which also
assembles ``NarrativeSequence`` (G7) since iteration 029). This module names them
explicitly so the gap is a written contract rather than silent.

It is consumed **solely** by the ingestion-parity test
(``tests/golem/test_ingestion_parity.py``), which asserts that the orphan set it
derives from a real graph build equals exactly :data:`DEFERRED_CONCEPTS`'s keys.
The single edit that wires a concept later (iteration 025+) is **removing its
entry here** — once a builder feeds it, the parity test stays green only if the
registry no longer claims it deferred (FR-002, FR-012, SC-002, research D4).

Pure data: imports only ``typing``, no I/O, no ``CONCEPTS`` import (the test
imports both and reconciles them, keeping this module dependency-free).
"""

from __future__ import annotations

from typing import NamedTuple


class DeferralNote(NamedTuple):
    """Why a modelled concept is not yet fed, and when it is expected to be.

    ``target_version`` is either a concrete shipped version label **or** the
    ``"demand-pulled"`` sentinel — a disciplined "no version until an activation
    trigger" state mirroring ``bookwright-roadmap.md`` § 4, used when the roadmap
    genuinely assigns a concept no version (it ships only when a real need pulls
    it). It is **never** the banned ``"undecided"`` placeholder: every deferred
    concept carries a firm target, even if that target is "on demand". The
    concept→version mapping is pinned by the parity test, so the value is a
    contract, not a comment (FR-002, FR-011).
    """

    reason: str
    target_version: str


DEFERRED_CONCEPTS: dict[str, DeferralNote] = {
    "RelationshipRole": DeferralNote(
        reason="requires a typed roles/states model with attributes and an authoring surface (G6)",
        target_version="demand-pulled",
    ),
    "PsychologicalState": DeferralNote(
        reason="requires a typed roles/states model with attributes and an authoring surface (G3)",
        target_version="demand-pulled",
    ),
}
"""Concept name → deferral note. Exactly two entries, each key a ``CONCEPTS``
member; the orphan set the parity test derives must equal this dict's keys."""
