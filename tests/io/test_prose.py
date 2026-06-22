"""``io/prose`` — the prose/structure seam (contracts/prose-seam.md tables)."""

from __future__ import annotations

import pytest

from bookwright.io.prose import ProseLine, is_placeholder, prose_view

# --- C1: prose_view splitting ------------------------------------------------


def test_empty_text_yields_empty_view() -> None:
    # C1.2: prose_view("") → ().
    assert prose_view("") == ()


def test_one_proseline_per_splitlines_entry_with_1_based_number() -> None:
    # C1.1 / C1.3: one ProseLine per splitlines() element, 1-based number, raw exact.
    text = "uno\ndos\ntres"
    view = prose_view(text)
    assert [pl.number for pl in view] == [1, 2, 3]
    assert [pl.raw for pl in view] == text.splitlines()


def test_blank_lines_are_not_dropped() -> None:
    # C1.2: whitespace/blank lines are preserved exactly as splitlines() yields.
    view = prose_view("a\n\n  \nb")
    assert [pl.raw for pl in view] == ["a", "", "  ", "b"]
    assert [pl.number for pl in view] == [1, 2, 3, 4]


# --- C2: normalized block-prefix stripping -----------------------------------


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("# Capítulo 1", "Capítulo 1"),  # heading stripped (count=1)
        ("### Escena", "Escena"),  # 3 # + space
        ("####### x", "####### x"),  # 7 # not a heading (out of {1,6})
        ("#Capítulo", "#Capítulo"),  # no space after # — not a heading
        ("   # text", "   # text"),  # heading strict col 0; indented unchanged
        ("- Pedro", "Pedro"),  # bullet stripped
        ("   - text", "text"),  # indented bullet stripped (bullet tolerates \s*)
        ("> cita", "cita"),  # blockquote stripped
        ("> - text", "text"),  # iterative: pass 1 `> `, pass 2 `- `
        ("* Pedro", "Pedro"),  # bullet (* + space)
        ("*Pedro*", "*Pedro*"),  # emphasis run, no following space — never stripped
        ("**Voz narrativa**:", "**Voz narrativa**:"),  # inline emphasis not a prefix
        # C2-D: leading Spanish dialogue dash (contracts/dialogue-marker.md).
        ("—Esto es el porvenir", "Esto es el porvenir"),  # D1 em dash glued (\s*)
        ("— Claro", "Claro"),  # D2 em dash + space → same result
        ("–Esto", "Esto"),  # D3 en dash (U+2013) recognized identically  # noqa: RUF001
        ("  —Esto", "Esto"),  # D4 leading whitespace tolerated (^\s*)
        ("—dijo Arnela—, y se fue", "dijo Arnela—, y se fue"),  # D5 only leading stripped
        ("—", ""),  # D6 dash-only line → empty
        ("> —Esto", "Esto"),  # D7 composes with blockquote across two passes
        ("Pregúntale a Quirón —dijo.", "Pregúntale a Quirón —dijo."),  # D8 no leading dash
        ("- Pedro", "Pedro"),  # D9 ASCII hyphen bullet stays owned by _BULLET_MARKER
        ("―Esto", "Esto"),  # D10 horizontal bar (U+2015) — same dash class
        ("― Claro", "Claro"),  # D11 horizontal bar + space → same result
    ],
)
def test_normalized_block_prefix_table(raw: str, normalized: str) -> None:
    # C2: one ProseLine row at a time; normalized matches the contract table.
    assert prose_view(raw) == (ProseLine(number=1, raw=raw, normalized=normalized),)


def test_empty_line_normalizes_to_empty() -> None:
    # C2 (empty → empty): a blank line (splitlines yields one "" element) has no
    # block prefix, so its normalized form is itself. `prose_view("")` is () per C1.2,
    # so the empty-content case is exercised through a single blank line ("\n").
    assert prose_view("\n") == (ProseLine(number=1, raw="", normalized=""),)


def test_emphasis_never_triggers_a_pass() -> None:
    # C2.2: a bare emphasis run is left intact (that is focalization's job, not the seam's).
    assert prose_view("__init__")[0].normalized == "__init__"
    assert prose_view("*highlight*")[0].normalized == "*highlight*"


# --- C3: is_placeholder ------------------------------------------------------


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("[PENDING: …]", True),
        ("  [pending algo]  ", True),  # case-insensitive, surrounding whitespace ok
        ("[PENDING: x] tercera persona", False),  # text after the token
        ("tercera persona [PENDING: x]", False),  # text before the token
        ("tercera persona", False),
        ("", False),
    ],
)
def test_is_placeholder_table(body: str, expected: bool) -> None:
    assert is_placeholder(body) is expected
