"""Mold structure — every ``*.tmpl`` mold is well-formed (FR-012..016, SC-004).

For each mold: (a) ``parse_frontmatter`` raises no ``yaml.YAMLError``,
(b) its required Spanish section headings are present, (c) the indexed molds
(`character`/`setting`) carry only mapper-recognized frontmatter keys, and
(d) ``character``'s ``name`` parses to a non-empty ``str`` (the C3 quoting trap:
a bare-bracket ``[PENDING: …]`` would parse as a YAML list, not a string).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bookwright.io.bible import CHARACTER_KEYS, SETTING_KEYS
from bookwright.io.frontmatter import parse_frontmatter

from .helpers import TEMPLATES_DIR, mold_files, read_text

_REQUIRED_HEADINGS: dict[str, tuple[str, ...]] = {
    "character.md.tmpl": (
        "Rasgos biográficos",
        "Rasgos psicológicos",
        "Rasgos físicos",
        "Rol narrativo",
        "Diálogo de muestra",
        "Patrones de lenguaje corporal",
    ),
    "setting.md.tmpl": ("Cultura", "Sistema / era", "Geografía amplia"),
    "location.md.tmpl": (
        "Qué se ve",
        "Qué se oye",
        "Qué se huele",
        "Qué se toca",
        "Atmósfera dominante",
    ),
    "chapter.md.tmpl": ("Propósito del capítulo", "Escenas", "Borrador"),
    "scene.md.tmpl": ("Objetivo del POV", "Conflicto", "Cambio de estado"),
}


def test_every_mold_has_required_headings_listed() -> None:
    # Guard: a newly added mold must declare its expected headings here.
    on_disk = {p.name for p in mold_files()}
    assert on_disk == set(_REQUIRED_HEADINGS), f"mold set drifted: {on_disk}"


@pytest.mark.parametrize("path", mold_files(), ids=lambda p: p.name)
def test_mold_parses_and_has_headings(path: Path) -> None:
    text = read_text(path)
    try:
        parse_frontmatter(text)
    except yaml.YAMLError as exc:  # pragma: no cover - failure path
        pytest.fail(f"{path.name} has invalid YAML frontmatter: {exc}")
    for heading in _REQUIRED_HEADINGS[path.name]:
        assert heading in text, f"{path.name} is missing required heading {heading!r}"


def test_indexed_molds_carry_only_recognized_keys() -> None:
    character = parse_frontmatter(read_text(TEMPLATES_DIR / "bible" / "character.md.tmpl"))
    setting = parse_frontmatter(read_text(TEMPLATES_DIR / "bible" / "setting.md.tmpl"))

    assert set(character.metadata) <= CHARACTER_KEYS, set(character.metadata)
    assert set(setting.metadata) <= SETTING_KEYS, set(setting.metadata)


def test_character_name_is_quoted_non_empty_string() -> None:
    metadata = parse_frontmatter(read_text(TEMPLATES_DIR / "bible" / "character.md.tmpl")).metadata
    name = metadata.get("name")
    assert isinstance(name, str) and name.strip(), (
        f"character `name` must be a non-empty str (quote the [PENDING] prompt); got {name!r}"
    )
