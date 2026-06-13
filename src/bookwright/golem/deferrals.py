"""The deferral registry: which GOLEM concepts are modelled but not yet fed.

Six of the thirteen :data:`bookwright.golem.CONCEPTS` have no authored-text
ingestion path today — they are *modelled* (a frozen class, a ``CLASS_IRI``
entry) but never *materialized* by any builder over ``bible/*.md``. This module
names them explicitly so the gap is a written contract rather than silent.

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

    ``target_version`` is one of ``"v0.3.x"``, ``"v0.4"``, or the single
    canonical literal ``"undecided"``; the concept→version mapping is pinned by
    the parity test, so the value is a contract, not a comment (FR-002).
    """

    reason: str
    target_version: str


DEFERRED_CONCEPTS: dict[str, DeferralNote] = {
    "Object": DeferralNote(
        reason="no builder, no bible/objects/, no skill (G16)",
        target_version="v0.3.x",
    ),
    "NarrativeUnit": DeferralNote(
        reason="narrative structural layer, no ingestion (G9)",
        target_version="v0.4",
    ),
    "NarrativeFunction": DeferralNote(
        reason="narrative structural layer, no ingestion (G10)",
        target_version="v0.4",
    ),
    "NarrativeSequence": DeferralNote(
        reason="narrative structural layer, no ingestion (G7)",
        target_version="v0.4",
    ),
    "RelationshipRole": DeferralNote(
        reason="relationships are identity + participants, no typed roles (G6)",
        target_version="undecided",
    ),
    "PsychologicalState": DeferralNote(
        reason="no builder (G3)",
        target_version="undecided",
    ),
}
"""Concept name → deferral note. Exactly six entries, each key a ``CONCEPTS``
member; the orphan set the parity test derives must equal this dict's keys."""
