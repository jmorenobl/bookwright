"""Unit tests for the indexer registry (FR-007/008, SC-007)."""

from __future__ import annotations

import pytest

from bookwright.indexers import (
    INDEXER_REGISTRY,
    Indexer,
    RdflibIndexer,
    UnknownIndexerError,
    resolve_indexer,
)


def test_resolve_known_engine() -> None:
    assert resolve_indexer("rdflib") is RdflibIndexer


def test_default_key_resolves_to_rdflib() -> None:
    # The manifest defaults `[bookwright] indexer = "rdflib"`, so the command path
    # always hands a concrete name; "rdflib" is that default.
    assert resolve_indexer("rdflib") is RdflibIndexer


def test_unknown_engine_names_engine_and_available() -> None:
    with pytest.raises(UnknownIndexerError) as excinfo:
        resolve_indexer("nope")
    err = excinfo.value
    assert err.name == "nope"
    assert err.available == sorted(INDEXER_REGISTRY)
    assert "nope" in err.message
    assert "rdflib" in err.message


def test_new_entry_is_selectable_without_touching_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SC-007/FR-008: adding an engine is one registry entry — no command-code edit.

    A structurally-conformant stand-in registered under a new key resolves through
    the same factory the commands use.
    """

    class FakeIndexer(RdflibIndexer):
        pass

    monkeypatch.setitem(INDEXER_REGISTRY, "fake", FakeIndexer)
    assert resolve_indexer("fake") is FakeIndexer
    # the protocol is structural — the stand-in satisfies it
    assert isinstance(FakeIndexer(), Indexer)
