# Quickstart: Index locations (G13) + `bible.py` split

Runnable validation that the feature works end-to-end. Assumes `uv sync` has run.
See [contracts/location-frontmatter.md](contracts/location-frontmatter.md) for the
full input/output contract and [data-model.md](data-model.md) for the module-split
map.

## Prerequisites

```bash
uv sync
```

## Scenario 1 — A location becomes a G13 node with a resolved setting (FR-001/003, SC-001/002)

In a `tmp_path` bible (or the `parity-exercise` fixture), with
`bible/settings/the-old-crossing.md` present, add:

```yaml
# bible/locations/harbor.md
---
name: "The Harbor"
setting: "The Old Crossing"
---
```

Map it and assert:

```python
from bookwright.io.bible import map_bible
from bookwright.golem import NarrativeLocation

result = map_bible(root, root / "bible", "https://example.org/n/")
loc = next(e for e in result.entities if isinstance(e, NarrativeLocation))
assert loc.slug == "the-harbor"
assert loc.setting is not None              # dlp:generic-location edge will be emitted
assert "the-harbor" in result.entity_index  # research targets resolve to it (FR-005)
assert result.unresolved_participants == []
```

Build the full graph and confirm the type + edge appear:

```python
# rdf:type golem:G13_Narrative_Location present; dlp:generic-location → the setting node
```

## Scenario 2 — A location with no `setting:` (FR-002, SC-002)

```yaml
# bible/locations/lonely-rock.md
---
name: "Lonely Rock"
---
```

```python
assert any(e.slug == "lonely-rock" for e in result.entities if isinstance(e, NarrativeLocation))
# exactly one G13 node, zero dlp:generic-location edges for it, no warning
```

## Scenario 3 — Unresolvable `setting:` is a soft-miss, not a crash (FR-004, SC-002)

```yaml
# bible/locations/nowhere-place.md
---
name: "Nowhere Place"
setting: "Nowhere"        # no sibling setting
---
```

```python
assert any(e.slug == "nowhere-place" for e in result.entities if isinstance(e, NarrativeLocation))
miss = [(u.entity, u.name) for u in result.unresolved_participants]
assert ("Nowhere Place", "Nowhere") in miss   # node still built; build did not abort
```

## Scenario 4 — Research link to a location resolves (FR-005, SC-003)

With `harbor.md` (Scenario 1) present and a research finding whose `bears_on:`
names "The Harbor", build the project graph and assert **no** soft-miss warning is
produced for that target (it resolves to the location node via `entity_index`).

## Scenario 5 — Skip & absent cases (FR-007/008/009, SC-005)

```python
# frontmatter-less / non-string-setting / missing-name file → recorded under result.skipped, no node, no crash
assert any(s.path.endswith("old-place.md") for s in result.skipped)
# a project with no bible/locations/ directory builds identically to before (no error, no location nodes)
```

## Scenario 6 — Slug collision (FR-006)

Two location files whose `name:` slugs collide:

```python
import pytest
from bookwright.io.errors import SlugCollisionError
with pytest.raises(SlugCollisionError):
    map_bible(root, root / "bible", "https://example.org/n/")
```

## Scenario 7 — Authoring command re-materializes (FR-010/011)

```bash
# The source command now prescribes name:/setting: front-matter and no longer says "no se indexa en v0".
grep -n "setting" src/bookwright/resources/commands/bookwright-bible.md
# The materialization tests regenerate + lint the bookwright-bible SKILL.md for claude and generic:
uv run pytest tests/integrations/ -q
```

## Scenario 8 — Parity guard green with G13 alive (FR-012, SC-004)

```bash
uv run pytest tests/golem/test_ingestion_parity.py -q
# DEFERRED_CONCEPTS has 6 entries; reachable set has 7 concepts incl. NarrativeLocation.
```

## Scenario 9 — Module under the ceiling + all gates (FR-013, SC-006)

```bash
test "$(grep -c '' src/bookwright/io/bible.py)" -le 500 && echo "bible.py ≤ 500 lines"
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest          # ≥ 80% coverage; every pre-existing bible test passes unchanged
```

All nine green ⇒ the feature is complete: locations are first-class G13 nodes, the
setting cross-ref resolves (with a graceful soft-miss), research links resolve, the
authoring command teaches the front-matter, the parity guard holds with G13 fed,
and `bible.py` is back under the size limit with no behavior change.
