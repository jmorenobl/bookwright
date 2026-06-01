"""SC-005 / FR-017-019 / F6-F7 - the cross-cutting authoring bar + CHANGELOG.

Per authored template: ≥1 HTML-comment guidance block, a `[PENDING:` prompt in
author-fill sections, valid YAML where a fence is present, and Spanish prose.
Plus: ``CHANGELOG.md`` records the preset credit and the design § 6 supersession.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.io.frontmatter import parse_frontmatter

from .helpers import authored_templates, looks_spanish, read_text

# README is generated wayfinding prose, not an author-fill template: it carries
# guidance + Spanish prose but is exempt from the `[PENDING:` requirement.
_PENDING_EXEMPT = {"README.md.j2"}

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("path", authored_templates(), ids=lambda p: p.name)
def test_template_has_html_comment_block(path: Path) -> None:
    text = read_text(path)
    start = text.find("<!--")
    assert start != -1 and text.find("-->", start) != -1, (
        f"{path.name} has no closed HTML-comment guidance block"
    )


@pytest.mark.parametrize("path", authored_templates(), ids=lambda p: p.name)
def test_template_has_pending_prompt(path: Path) -> None:
    if path.name in _PENDING_EXEMPT:
        pytest.skip(f"{path.name} is exempt from [PENDING] prompts")
    assert "[PENDING:" in read_text(path), f"{path.name} has no [PENDING: …] prompt"


@pytest.mark.parametrize("path", authored_templates(), ids=lambda p: p.name)
def test_template_frontmatter_is_valid_yaml(path: Path) -> None:
    # parse_frontmatter raises yaml.YAMLError on a malformed fence; a clean
    # return (even empty metadata for the no-fence files) is the pass condition.
    parse_frontmatter(read_text(path))


@pytest.mark.parametrize("path", authored_templates(), ids=lambda p: p.name)
def test_template_prose_is_spanish(path: Path) -> None:
    assert looks_spanish(read_text(path)), f"{path.name} does not read as Spanish prose"


def test_changelog_records_credit_and_supersession() -> None:
    changelog = _REPO_ROOT / "CHANGELOG.md"
    assert changelog.is_file(), "CHANGELOG.md is missing at the repo root"
    text = changelog.read_text(encoding="utf-8")
    for needle in ("fiction-book-writing", "adaumann", "MIT", "Apache-2.0", "GOLEM"):
        assert needle in text, f"CHANGELOG.md is missing the credit token {needle!r}"
    assert "§ 6" in text, "CHANGELOG.md does not record the design § 6 supersession"
    assert "supersede" in text.lower(), "CHANGELOG.md does not state the § 6 supersession"
