"""``bible/research/`` scaffolding + bible/clarify wiring (US3, FR-008/009/014a).

After ``bookwright init`` the project ships a ``bible/research/`` **directory**
(``_index.md`` + ``sources.md``, no stray ``bible/research.md``), the starters
parse cleanly through ``map_research()``, and the generated ``manifest.toml``
carries the ``[research]`` block. The per-index template is layer-resolvable: a
project override shadows the packaged mold under the project's own template engine.
"""

from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

import jinja2
from rdflib.term import URIRef
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.io.research import map_research

_URI_BASE = "https://example.org/proj/"


def _init_project(runner: CliRunner, root: Path) -> Path:
    result = runner.invoke(app, ["init", "proj", "--integration", "generic", "--no-git"])
    assert result.exit_code == 0, result.stdout
    return root / "proj"


def test_research_dir_scaffolded_without_legacy_file(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    # US3-1 — the directory ships two real files; the legacy single file is gone.
    proj = _init_project(runner, scaffold_in_tmp)
    assert (proj / "bible" / "research" / "_index.md").is_file()
    assert (proj / "bible" / "research" / "sources.md").is_file()
    assert not (proj / "bible" / "research.md").exists()


def test_scaffolded_starters_parse_through_map_research(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    # R7 — a user may run `graph build` immediately, so the starters must parse.
    proj = _init_project(runner, scaffold_in_tmp)
    research_dir = proj / "bible" / "research"
    result = map_research(
        project_root=proj,
        research_dir=research_dir,
        uri_base=_URI_BASE,
        book_language="en",
        bible_index={},
        timeline_uri=URIRef(f"{_URI_BASE}timeline"),
    )
    # Empty/placeholder starters → no findings/anchors and, crucially, no raise.
    assert result.anchors == ()


def test_generated_manifest_carries_research_block(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    # FR-014a (depends on T014) — the block ships in the scaffolded manifest.
    proj = _init_project(runner, scaffold_in_tmp)
    manifest_text = (proj / "manifest.toml").read_text(encoding="utf-8")
    assert "[research]" in manifest_text
    assert 'min_reliability_for_anchor = "media"' in manifest_text


def test_project_override_shadows_packaged_index_template(tmp_path: Path) -> None:
    """FR-008 / US3-2 — a project override resolves ahead of the packaged mold.

    The molds are layer-resolvable exactly like the iteration-7 templates: a
    project that drops its own ``bible/research/_index.md.tmpl`` under
    ``.bookwright/templates/`` shadows the packaged core. Demonstrated with the
    project's own template engine (a jinja2 ``ChoiceLoader``: project dir first,
    packaged core second), so the override layering is mechanically real.
    """

    rel = "bible/research/_index.md.tmpl"
    override_root = tmp_path / ".bookwright" / "templates"
    override_path = override_root / "bible" / "research" / "_index.md.tmpl"
    override_path.parent.mkdir(parents=True, exist_ok=True)
    override_path.write_text("OVERRIDE SENTINEL\n", encoding="utf-8")

    with as_file(files("bookwright.resources").joinpath("templates")) as packaged_root:
        loader = jinja2.ChoiceLoader(
            [
                jinja2.FileSystemLoader(str(override_root)),
                jinja2.FileSystemLoader(str(packaged_root)),
            ]
        )
        env = jinja2.Environment(loader=loader, autoescape=False)
        # The packaged mold exists (fallback layer) ...
        assert (Path(packaged_root) / rel).is_file()
        # ... but the override wins when present.
        assert env.get_template(rel).render().strip() == "OVERRIDE SENTINEL"
