"""C5 / SC-004 — a filled character/setting mold maps to exactly one GOLEM entity.

Stamps the real ``character.md.tmpl`` / ``setting.md.tmpl`` into the stamped
project's ``bible/characters`` and ``bible/settings``, fills the frontmatter with
concrete (correctly-typed) values reusing each mold's authored body, indexes via
``map_bible`` and asserts exactly one ``Character`` (carrying the declared
attributes) and exactly one ``Setting``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from bookwright.golem import Character, Setting
from bookwright.io.bible import MapResult
from bookwright.io.frontmatter import parse_frontmatter

from .helpers import TEMPLATES_DIR, read_text

_CHARACTER_FRONTMATTER = (
    "---\n"
    'name: "Ana Soler"\n'
    "born: 1990\n"
    "died: 2061\n"
    "features:\n"
    '  - "cicatriz en la ceja"\n'
    '  - "zurda"\n'
    "narrative_roles:\n"
    '  - "protagonista"\n'
    "---\n"
)
_SETTING_FRONTMATTER = '---\nname: "Las Ciudades-Puente del Vel"\n---\n'


def _fill(mold: Path, frontmatter: str) -> str:
    # Reuse the mold's authored prose body, swapping in a concrete frontmatter.
    body = parse_frontmatter(read_text(mold)).body
    return frontmatter + "\n" + body


def test_filled_molds_map_to_one_entity_each(
    stamped_project: Path,
    map_stamped_bible: Callable[[], MapResult],
) -> None:
    char_mold = TEMPLATES_DIR / "bible" / "character.md.tmpl"
    setting_mold = TEMPLATES_DIR / "bible" / "setting.md.tmpl"

    characters_dir = stamped_project / "bible" / "characters"
    settings_dir = stamped_project / "bible" / "settings"
    characters_dir.mkdir(parents=True, exist_ok=True)
    settings_dir.mkdir(parents=True, exist_ok=True)

    (characters_dir / "ana-soler.md").write_text(
        _fill(char_mold, _CHARACTER_FRONTMATTER), encoding="utf-8"
    )
    (settings_dir / "ciudades-puente.md").write_text(
        _fill(setting_mold, _SETTING_FRONTMATTER), encoding="utf-8"
    )

    result = map_stamped_bible()
    assert result.skipped == [], f"unexpected skips: {result.skipped}"
    assert result.unknown_keys == [], f"unexpected unknown keys: {result.unknown_keys}"

    characters = [e for e in result.entities if isinstance(e, Character)]
    settings = [e for e in result.entities if isinstance(e, Setting)]

    assert len(characters) == 1, f"expected one Character, got {len(characters)}"
    assert len(settings) == 1, f"expected one Setting, got {len(settings)}"

    character = characters[0]
    assert character.name == "Ana Soler"
    assert character.born == 1990
    assert character.died == 2061
    assert "cicatriz en la ceja" in character.features
    assert "protagonista" in character.narrative_roles

    assert settings[0].name == "Las Ciudades-Puente del Vel"
